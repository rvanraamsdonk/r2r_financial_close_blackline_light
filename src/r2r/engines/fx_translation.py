from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState
from ..utils import now_iso_z, run_id


def _calculate_materiality_factor(diff: float, threshold: float) -> float:
    """
    Calculates a materiality factor based on the difference relative to the materiality threshold.
    Factor is 1.0 for zero diff, and decreases as diff approaches the threshold.
    """
    if threshold == 0:
        return 0.0 if diff != 0 else 1.0

    # Scale confidence from 1.0 (zero diff) down to 0.5 (at threshold)
    ratio = min(abs(diff) / threshold, 1.0)
    confidence = 1.0 - (0.5 * ratio)
    return round(confidence, 4)


def _get_dynamic_materiality_threshold(
    account: str,
    entity: str,
    coa_df: pd.DataFrame,
    entities_df: pd.DataFrame,
    default_threshold: float = 100.0,
) -> float:
    """
    Calculates a dynamic materiality threshold based on account type and entity size.
    """
    try:
        # Get account type from Chart of Accounts
        account_info = coa_df[coa_df["account"] == account]
        account_type = account_info["account_type"].iloc[0] if not account_info.empty else "other"

        # Get entity size from entities table (assuming 'entity_size_usd' column exists)
        entity_info = entities_df[entities_df["entity"] == entity]
        entity_size_usd = entity_info["entity_size_usd"].iloc[0] if not entity_info.empty else 1_000_000 # Default size

        # Dynamic thresholds based on context from Master Plan
        if account_type == "cash":
            return max(entity_size_usd * 0.001, 50.0)  # 0.1% of entity size, min $50
        elif account_type == "revenue":
            return max(entity_size_usd * 0.005, 250.0) # 0.5% of entity size, min $250
        elif account_type == "expense":
            return max(entity_size_usd * 0.005, 250.0) # 0.5% of entity size, min $250
        else:
            return default_threshold # Default for other accounts
    except (IndexError, KeyError):
        # Fallback to default if lookups fail
        return default_threshold


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _extract_run_id_from_audit(audit: AuditLogger) -> str:
    name = Path(audit.log_path).name  # audit_<runid>.jsonl
    if name.startswith("audit_") and name.endswith(".jsonl"):
        return name[len("audit_") : -len(".jsonl")]
    return run_id()


def fx_translation(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic FX translation to reporting currency (USD):
    - Map each TB row's entity to home currency (from entities.csv)
    - For state's period, use fx_rates.csv usd_rate for that currency
    - Recompute USD balances and compare to provided balance_usd
    - Persist artifact with per-row computed_usd and differences
    - Log evidence and deterministic run with input_row_ids for drill-through
    Policy (simplified): single period rate applied to all accounts (dataset has period rates only).
    """
    assert state.tb_df is not None, "tb_df missing"
    assert state.fx_df is not None, "fx_df missing"
    assert state.entities_df is not None, "entities_df missing"
    assert state.chart_of_accounts_df is not None, "chart_of_accounts_df missing"

    tb = state.tb_df.copy()
    # Assume entities_df now contains 'entity_size_usd' for dynamic materiality
    ents = state.entities_df.copy()
    fx = state.fx_df.copy()
    coa = state.chart_of_accounts_df.copy()

    # Build currency map and rates for the period
    cur_map = {str(r["entity"]): str(r["home_currency"]) for _, r in ents.iterrows()}
    fx_p = fx[fx["period"].astype(str) == str(state.period)].copy()
    rates = {str(r["currency"]): float(r["usd_rate"]) for _, r in fx_p.iterrows()}

    # Compute translation
    input_row_ids: List[str] = []
    computed_rows: List[Dict[str, Any]] = []
    diff_count = 0
    total_abs_diff = 0.0
    auto_approved_count = 0
    total_confidence = 0.0
    processed_rows = 0

    for _, r in tb.iterrows():
        ent = str(r["entity"])
        acct = str(r["account"])
        bal_local = float(r.get("balance_local", 0.0))
        bal_usd_reported = float(r.get("balance_usd", 0.0))
        cur = cur_map.get(ent)
        rate = rates.get(cur) if cur else None
        comp_usd = bal_local * float(rate) if rate is not None else None
        diff = None
        is_exception = False
        confidence = 1.0
        auto_approved = False

        if comp_usd is not None:
            diff = float(comp_usd) - float(bal_usd_reported)
            threshold = _get_dynamic_materiality_threshold(acct, ent, coa, ents)
            materiality_factor = _calculate_materiality_factor(diff, threshold)

            if abs(diff) > threshold:
                diff_count += 1
                total_abs_diff += abs(diff)
                is_exception = True
            
            if not is_exception and confidence >= 0.95:
                auto_approved = True
                auto_approved_count += 1

            total_confidence += confidence
            processed_rows += 1

        computed_rows.append(
            {
                "period": str(r["period"]),
                "entity": ent,
                "account": acct,
                "currency": cur,
                "balance_local": bal_local,
                "rate": float(rate) if rate is not None else None,
                "computed_usd": float(comp_usd) if comp_usd is not None else None,
                "reported_usd": bal_usd_reported,
                "diff_usd": float(diff) if diff is not None else None,
                "is_exception": is_exception,
                "materiality_factor": materiality_factor,
                "auto_approval_recommended": auto_approved,
            }
        )
        input_row_ids.append(f"{str(r['period'])}|{ent}|{acct}")

    run_id = _extract_run_id_from_audit(audit)
    out_path = Path(audit.out_dir) / f"fx_translation_{run_id}.json"
    artifact = {
        "generated_at": now_iso_z(),
        "period": state.period,
        "entity_scope": state.entity,
        "policy": {
            "rate_basis": "period_rate (dataset)",
            "materiality_policy": "dynamic",
            "description": "Materiality is based on account type and entity size."
        },
        "summary": {
            "rows": len(computed_rows),
            "exceptions_count": int(diff_count),
            "exceptions_total_abs_diff_usd": float(round(total_abs_diff, 2)),
            "auto_approved_count": auto_approved_count,
            "average_materiality_factor": round(total_confidence / processed_rows, 4) if processed_rows > 0 else 0,
        },
        "rows": computed_rows,
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    # Evidence & deterministic run
    period_fs = str(state.period).replace("-", "_")
    tb_path = state.data_path / f"trial_balance_{period_fs}.csv"
    ev_tb = EvidenceRef(type="csv", uri=str(tb_path) if tb_path.exists() else None, input_row_ids=input_row_ids)
    ev_fx = EvidenceRef(type="csv", uri=str(Path(state.data_path) / "fx_rates.csv"))
    state.evidence.extend([ev_tb, ev_fx])

    det = DeterministicRun(function_name="fx_translation")
    det.params = {"period": state.period, "entity": state.entity}
    det.output_hash = sha256(json.dumps(artifact, sort_keys=True).encode("utf-8")).hexdigest()
    state.det_runs.append(det)

    audit.append(
        {
            "type": "evidence",
            "id": ev_tb.id,
            "evidence_type": ev_tb.type,
            "uri": ev_tb.uri,
            "input_row_ids": ev_tb.input_row_ids,
            "timestamp": ev_tb.timestamp.isoformat() + "Z",
        }
    )
    audit.append(
        {
            "type": "evidence",
            "id": ev_fx.id,
            "evidence_type": ev_fx.type,
            "uri": ev_fx.uri,
            "input_row_ids": ev_fx.input_row_ids,
            "timestamp": ev_fx.timestamp.isoformat() + "Z",
        }
    )

    audit.append(
        {
            "type": "deterministic",
            "fn": det.function_name,
            "evidence_id": ev_tb.id,
            "output_hash": det.output_hash,
            "params": det.params,
            "artifact": str(out_path),
        }
    )

    # Messages, tags, metrics
    msg = (
        f"[DET] FX translation: recomputed USD for {len(computed_rows)} rows; diffs>1c: {diff_count} -> {out_path}"
    )
    state.messages.append(msg)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="FX translation to USD"))
    state.metrics.update(
        {
            "fx_translation_diff_count": int(diff_count),
            "fx_translation_total_abs_diff_usd": float(round(total_abs_diff, 2)),
            "fx_translation_artifact": str(out_path),
        }
    )

    return state
