from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

import pandas as pd

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState


def _generate_resolution_suggestion(
    top_accounts: List[Dict[str, Any]], imbalance_usd: float
) -> Dict[str, str]:
    """Generates a resolution suggestion based on common accounting patterns."""
    # Rule 1: Check for suspense/clearing account usage
    for acc in top_accounts:
        acc_name = acc.get("account_name", "").lower()
        if "suspense" in acc_name or "clearing" in acc_name:
            return {
                "suggestion": "Reclassify Suspense Account Balance",
                "rationale": f"The top contributing account, {acc['account_name']}, appears to be a suspense/clearing account. Balances in these accounts should typically be zeroed out by period-end. Investigate and reclassify the remaining ${acc['balance_usd']:.2f} balance to the correct accounts.",
            }

    # Rule 2: Check if one account is the primary driver of the imbalance
    if top_accounts:
        primary_acc = top_accounts[0]
        # If one account explains >95% of the imbalance
        if abs(primary_acc["balance_usd"] - imbalance_usd) / abs(imbalance_usd) < 0.05:
            return {
                "suggestion": "Investigate Potential Misposting",
                "rationale": f"The imbalance of ${imbalance_usd:.2f} is almost entirely driven by account {primary_acc['account_name']} (${primary_acc['balance_usd']:.2f}). This could indicate a one-sided journal entry or a misposted transaction. Review recent activity in this account.",
            }

    # Default suggestion
    return {
        "suggestion": "Review Top Contributing Accounts",
        "rationale": "The imbalance is distributed across several accounts. Review the top contributing accounts to identify any potential misclassifications or errors.",
    }


def _get_entity_level_materiality_threshold(
    entity: str, entities_df: pd.DataFrame, default_threshold: float = 1000.0
) -> float:
    """Calculates a materiality threshold for an entity's total imbalance."""
    try:
        entity_info = entities_df[entities_df["entity"] == entity]
        entity_size_usd = (
            entity_info["entity_size_usd"].iloc[0]
            if not entity_info.empty
            else 1_000_000
        )
        # Entity-level threshold: 0.01% of entity size, min $1,000
        return max(entity_size_usd * 0.0001, 1000.0)
    except (IndexError, KeyError):
        return default_threshold


def _calculate_confidence_score(diff: float, threshold: float) -> float:
    """Calculates a confidence score based on the difference relative to the materiality threshold."""
    if threshold == 0:
        return 0.0 if diff != 0 else 1.0
    ratio = min(abs(diff) / threshold, 1.0)
    confidence = 1.0 - (0.5 * ratio)
    return round(confidence, 4)


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _extract_run_id_from_audit(audit: AuditLogger) -> str:
    name = Path(audit.log_path).name  # audit_<runid>.jsonl
    if name.startswith("audit_") and name.endswith(".jsonl"):
        return name[len("audit_") : -len(".jsonl")]
    # fallback: timestamp
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def tb_diagnostics(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic TB diagnostics: for each imbalanced entity, list top accounts contributing
    to the imbalance with account name/type, and export a drill-through JSON artifact.
    """
    assert state.tb_df is not None, "tb_df missing"

    tb = state.tb_df.copy()
    coa = state.coa_df
    ents = state.entities_df

    # Determine imbalance per entity
    by_ent = tb.groupby("entity")["balance_usd"].sum()

    # Materiality check
    materially_off = {}
    entity_confidence = {}
    entity_auto_approved = {}

    for ent, total in by_ent.items():
        threshold = _get_entity_level_materiality_threshold(ent, ents)
        confidence = _calculate_confidence_score(total, threshold)
        entity_confidence[ent] = confidence
        
        if abs(total) > threshold:
            materially_off[ent] = total
        
        entity_auto_approved[ent] = abs(total) <= threshold and confidence >= 0.95

    off = pd.Series(materially_off)

    diagnostics: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []

    if not off.empty:
        for ent, total in off.items():
            ent_rows = tb[tb["entity"] == ent]
            contrib = (
                ent_rows.groupby(["account"], as_index=False)["balance_usd"].sum()
                .sort_values(by="balance_usd", key=lambda s: s.abs(), ascending=False)
            )
            # Enrich with COA
            if coa is not None:
                contrib = contrib.merge(coa, on="account", how="left")

            top = contrib.head(10).to_dict(orient="records")
            suggestion = _generate_resolution_suggestion(top, total)
            diagnostics.append(
                {
                    "entity": ent,
                    "imbalance_usd": float(round(total, 2)),
                    "materiality_threshold_usd": _get_entity_level_materiality_threshold(ent, ents),
                    "confidence_score": entity_confidence.get(ent, 0.0),
                    "auto_approved": entity_auto_approved.get(ent, False),
                    "ai_resolution_suggestion": suggestion,
                    "top_accounts": top,
                }
            )
            # Capture row-level provenance keys for this entity
            input_row_ids.extend(
                [
                    f"{str(r['period'])}|{str(r['entity'])}|{str(r['account'])}"
                    for _, r in ent_rows.iterrows()
                ]
            )

    # Compute rollups and balance flags regardless of off state for summary
    by_entity_totals = by_ent.round(2).to_dict()
    entity_balanced = {
        ent: abs(v) <= _get_entity_level_materiality_threshold(ent, ents)
        for ent, v in by_entity_totals.items()
    }
    by_account_type: Dict[str, float] | None = None
    if coa is not None and "account_type" in coa.columns:
        tb_join = tb.merge(coa[["account", "account_type"]], on="account", how="left")
        by_account_type = (
            tb_join.groupby("account_type")["balance_usd"].sum().round(2).to_dict()
        )

    # Persist artifact
    run_id = _extract_run_id_from_audit(audit)
    out_path = Path(audit.out_dir) / f"tb_diagnostics_{run_id}.json"
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": state.period,
        "entity_scope": state.entity,
        "diagnostics": diagnostics,
        "summary": {
            "entities_in_scope": len(by_entity_totals),
            "material_imbalances": len(diagnostics),
            "auto_approved_entities": sum(entity_auto_approved.values()),
            "average_confidence_score": round(sum(entity_confidence.values()) / len(entity_confidence), 4) if entity_confidence else 0,
        },
        "rollups": {
            "by_entity_total_usd": {k: float(v) for k, v in by_entity_totals.items()},
            "entity_materially_balanced": entity_balanced,
            "entity_confidence_scores": entity_confidence,
            **({"by_account_type_total_usd": {k: float(v) for k, v in by_account_type.items()}} if by_account_type else {}),
        },
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence and deterministic run logging
    # Standardize period formatting in URI to match data files (YYYY_MM)
    period_fs = str(state.period).replace("-", "_")
    tb_path = state.data_path / f"trial_balance_{period_fs}.csv"
    ev = EvidenceRef(
        type="csv",
        uri=str(tb_path),
        input_row_ids=input_row_ids or None,
    )
    state.evidence.append(ev)

    det = DeterministicRun(function_name="tb_diagnostics")
    det.params = {"period": state.period, "entity": state.entity}
    det.output_hash = _hash_df(tb)
    state.det_runs.append(det)

    # Persist evidence with row-level provenance into audit log
    audit.append(
        {
            "type": "evidence",
            "id": ev.id,
            "evidence_type": ev.type,
            "uri": ev.uri,
            "input_row_ids": ev.input_row_ids,
            "timestamp": ev.timestamp.isoformat() + "Z",
        }
    )

    audit.append(
        {
            "type": "deterministic",
            "fn": det.function_name,
            "evidence_id": ev.id,
            "output_hash": det.output_hash,
            "params": det.params,
            "artifact": str(out_path),
        }
    )

    # Messages
    if diagnostics:
        state.messages.append(
            f"[DET] TB diagnostics exported -> {out_path} (entities: {[d['entity'] for d in diagnostics]})"
        )
    else:
        state.messages.append("[DET] TB diagnostics: all entities balanced; no drill-through created")

    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="TB diagnostics"))
    return state
