from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, Any, List, Optional

import pandas as pd

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _read_csv_if_exists(path: Path, **read_kwargs) -> Optional[pd.DataFrame]:
    if path.exists():
        return pd.read_csv(path, **read_kwargs)
    return None


def _extract_run_id_from_audit(audit: AuditLogger) -> str:
    name = Path(audit.log_path).name  # audit_<runid>.jsonl
    if name.startswith("audit_") and name.endswith(".jsonl"):
        return name[len("audit_") : -len(".jsonl")]
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def period_init(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic Period Initialization & Governance
    - Load entities and COA if not already in state
    - Optionally load TB for current period (if present)
    - Compute basic materiality thresholds by entity (0.5% of abs TB sum, $1,000 floor)
    - Emit run snapshot artifact with dataset hashes, scope, and governance flags
    - Log evidence and deterministic run with provenance-ready structure
    """
    msgs: List[str] = []

    data_root = Path(state.data_path)
    entities_fp = data_root / "entities.csv"
    coa_fp = data_root / "chart_of_accounts.csv"

    # Load into state if missing
    if state.entities_df is None:
        state.entities_df = _read_csv_if_exists(entities_fp, dtype=str)
    if state.coa_df is None:
        state.coa_df = _read_csv_if_exists(coa_fp, dtype={"account": str, "account_name": str, "type": str})

    # Attempt to load TB for period if not already present
    if state.tb_df is None:
        period_fs = str(state.period).replace("-", "_")
        tb_fp = data_root / f"trial_balance_{period_fs}.csv"
        if tb_fp.exists():
            state.tb_df = pd.read_csv(
                tb_fp,
                dtype={
                    "period": str,
                    "entity": str,
                    "account": str,
                    "balance_usd": float,
                },
            )
        else:
            tb_fp = None
    else:
        tb_fp = None

    # Compute materiality thresholds by entity (if possible)
    materiality: Dict[str, float] = {}
    method_desc = "0.5% of absolute TB balance by entity with $1,000 floor"
    if isinstance(state.tb_df, pd.DataFrame) and not state.tb_df.empty:
        by_ent_abs = state.tb_df.groupby("entity")["balance_usd"].apply(lambda s: float(s.abs().sum()))
        for ent, total_abs in by_ent_abs.items():
            thr = max(1000.0, 0.005 * float(total_abs))
            materiality[str(ent)] = float(round(thr, 2))
    elif isinstance(state.entities_df, pd.DataFrame):
        # Fallback: default floor only for listed entities
        for ent in state.entities_df["entity"].astype(str).tolist():
            materiality[ent] = 1000.0

    # Build dataset hashes for snapshot
    dataset_hashes: Dict[str, Optional[str]] = {"entities.csv": None, "chart_of_accounts.csv": None}
    if isinstance(state.entities_df, pd.DataFrame):
        dataset_hashes["entities.csv"] = _hash_df(state.entities_df)
    if isinstance(state.coa_df, pd.DataFrame):
        dataset_hashes["chart_of_accounts.csv"] = _hash_df(state.coa_df)
    if isinstance(state.tb_df, pd.DataFrame):
        dataset_hashes[f"trial_balance_{str(state.period).replace('-', '_')}.csv"] = _hash_df(state.tb_df)

    # Persist snapshot artifact
    run_id = _extract_run_id_from_audit(audit)
    out_path = Path(audit.out_dir) / f"period_init_{run_id}.json"
    snapshot = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": state.period,
        "entity_scope": state.entity,
        "governance": {
            "locked": True,
            "policy": {
                "materiality_method": method_desc,
                "ai_mode": state.ai_mode,
            },
        },
        "datasets": {
            "entities_uri": str(entities_fp) if entities_fp.exists() else None,
            "coa_uri": str(coa_fp) if coa_fp.exists() else None,
        },
        "dataset_hashes": dataset_hashes,
        "materiality_threshold_usd": materiality,
    }
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    # Evidence logging (URIs only, no row IDs for governance snapshot)
    evs: List[EvidenceRef] = []
    if entities_fp.exists():
        evs.append(EvidenceRef(type="csv", uri=str(entities_fp)))
    if coa_fp.exists():
        evs.append(EvidenceRef(type="csv", uri=str(coa_fp)))
    if isinstance(state.tb_df, pd.DataFrame):
        period_fs = str(state.period).replace("-", "_")
        tb_uri = str(data_root / f"trial_balance_{period_fs}.csv")
        if Path(tb_uri).exists():
            evs.append(EvidenceRef(type="csv", uri=tb_uri))

    for ev in evs:
        state.evidence.append(ev)
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

    det = DeterministicRun(function_name="period_init")
    det.params = {"period": state.period, "entity": state.entity}
    # Hash snapshot content for deterministic record
    det.output_hash = sha256(json.dumps(snapshot, sort_keys=True).encode("utf-8")).hexdigest()
    state.det_runs.append(det)

    audit.append(
        {
            "type": "deterministic",
            "fn": det.function_name,
            "output_hash": det.output_hash,
            "params": det.params,
            "artifact": str(out_path),
        }
    )

    # Messages, tags, metrics
    ent_count = int(state.entities_df.shape[0]) if isinstance(state.entities_df, pd.DataFrame) else 0
    msgs.append(
        f"[DET] Period initialized for {state.period}: scope={state.entity}; entities={ent_count}; locked=True -> {out_path}"
    )
    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Period init & governance"))

    state.metrics.update(
        {
            "period_locked": True,
            "materiality_thresholds_usd": materiality,
            "period_init_artifact": str(out_path),
        }
    )

    return state
