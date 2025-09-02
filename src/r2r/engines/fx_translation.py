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

    tb = state.tb_df.copy()
    ents = state.entities_df[["entity", "home_currency"]].copy()
    fx = state.fx_df.copy()

    # Build currency map and rates for the period
    cur_map = {str(r["entity"]): str(r["home_currency"]) for _, r in ents.iterrows()}
    fx_p = fx[fx["period"].astype(str) == str(state.period)].copy()
    rates = {str(r["currency"]): float(r["usd_rate"]) for _, r in fx_p.iterrows()}

    # Compute translation
    input_row_ids: List[str] = []
    computed_rows: List[Dict[str, Any]] = []
    diff_count = 0
    total_abs_diff = 0.0

    for _, r in tb.iterrows():
        ent = str(r["entity"])
        acct = str(r["account"])
        bal_local = float(r.get("balance_local", 0.0))
        bal_usd_reported = float(r.get("balance_usd", 0.0))
        cur = cur_map.get(ent)
        rate = rates.get(cur) if cur else None
        comp_usd = bal_local * float(rate) if rate is not None else None
        diff = None
        if comp_usd is not None:
            diff = float(comp_usd) - float(bal_usd_reported)
            if abs(diff) > 0.01:
                diff_count += 1
                total_abs_diff += abs(diff)
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
            "tolerance_usd": 0.01,
        },
        "summary": {
            "rows": len(computed_rows),
            "diff_count": int(diff_count),
            "total_abs_diff_usd": float(round(total_abs_diff, 2)),
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
