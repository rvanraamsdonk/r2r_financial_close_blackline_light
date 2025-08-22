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

    # Determine imbalance per entity
    by_ent = tb.groupby("entity")["balance_usd"].sum()
    off = by_ent[by_ent.round(2) != 0.0]

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
            diagnostics.append(
                {
                    "entity": ent,
                    "imbalance_usd": float(round(total, 2)),
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

    # Persist artifact
    run_id = _extract_run_id_from_audit(audit)
    out_path = Path(audit.out_dir) / f"tb_diagnostics_{run_id}.json"
    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": state.period,
        "entity_scope": state.entity,
        "diagnostics": diagnostics,
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
