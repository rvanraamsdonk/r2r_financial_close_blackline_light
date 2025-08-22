from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from ..audit.log import AuditLogger
from ..schemas import DeterministicRun, EvidenceRef, MethodType, OutputTag
from ..state import R2RState
from ..data.static_loader import load_intercompany


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _find_ic_file(data_path: Path, period: str) -> Path:
    # Not used by loader directly; retained for provenance URI resolution
    base = Path(data_path) / "subledgers" / "intercompany"
    candidates = [
        base / f"ic_transactions_{period}.csv",
        base / f"ic_transactions_{period.replace('-', '_')}.csv",
        base / "ic_transactions_aug.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"No intercompany file found for period {period} in {base}")


def intercompany_reconciliation(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic intercompany reconciliation (mismatch detection):
    - Load intercompany transactions for period
    - Compute absolute difference |amount_src - amount_dst|
    - Flag exceptions where difference exceeds materiality threshold
      threshold = max(materiality[src], materiality[dst]) if available, else $1,000
    - Emit artifact and provenance; update messages, tags, metrics
    """
    period = state.period
    # Load via canonical loader (filters by period only; entities optional)
    df = load_intercompany(Path(state.data_path), period)
    # Resolve CSV URI for evidence
    fp = _find_ic_file(Path(state.data_path), period)

    msgs: List[str] = []

    if df.empty:
        msgs.append("[DET] Intercompany: no transactions in scope; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Intercompany reconciliation (skipped)"))
        return state

    # Materiality thresholds by entity
    materiality_map: Dict[str, float] = {}
    if isinstance(state.metrics.get("materiality_thresholds_usd"), dict):
        for k, v in state.metrics["materiality_thresholds_usd"].items():
            try:
                materiality_map[str(k)] = float(v)
            except Exception:
                continue

    def pair_threshold(src: str, dst: str) -> float:
        # Default floor if not available
        thr_src = materiality_map.get(str(src), 1000.0)
        thr_dst = materiality_map.get(str(dst), 1000.0)
        return float(max(thr_src, thr_dst))

    exceptions: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []

    for _, r in df.iterrows():
        src = str(r["entity_src"])  # e.g., ENT100
        dst = str(r["entity_dst"])  # e.g., ENT101
        diff = abs(float(r["amount_src"]) - float(r["amount_dst"]))
        thr = pair_threshold(src, dst)
        if diff > thr:
            exceptions.append(
                {
                    "doc_id": r["doc_id"],
                    "entity_src": src,
                    "entity_dst": dst,
                    "amount_src": float(r["amount_src"]),
                    "amount_dst": float(r["amount_dst"]),
                    "currency": r.get("currency"),
                    "transaction_type": r.get("transaction_type"),
                    "description": r.get("description"),
                    "diff_abs": float(round(diff, 2)),
                    "threshold": float(round(thr, 2)),
                    "reason": "ic_amount_mismatch_above_threshold",
                }
            )
            input_row_ids.append(str(r["doc_id"]))

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"intercompany_reconciliation_{run_id}.json"

    total_diff = float(sum(e.get("diff_abs", 0.0) for e in exceptions))

    by_pair: Dict[str, float] = {}
    for e in exceptions:
        key = f"{e['entity_src']}->{e['entity_dst']}"
        by_pair[key] = by_pair.get(key, 0.0) + e.get("diff_abs", 0.0)

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": period,
        "rules": {
            "mismatch_rule": "flag |amount_src-amount_dst| > max(materiality[src], materiality[dst])",
            "default_floor_usd": 1000.0,
        },
        "exceptions": exceptions,
        "summary": {
            "count": len(exceptions),
            "total_diff_abs": float(round(total_diff, 2)),
            "by_pair_diff_abs": {k: float(round(v, 2)) for k, v in by_pair.items()},
        },
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence and deterministic run
    ev = EvidenceRef(type="csv", uri=str(fp), input_row_ids=input_row_ids or None)
    state.evidence.append(ev)

    det = DeterministicRun(function_name="intercompany_reconciliation")
    det.params = {"period": period}
    det.output_hash = _hash_df(df)
    state.det_runs.append(det)

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

    # Messages, tags, metrics
    if exceptions:
        msgs.append(
            f"[DET] Intercompany mismatches: {len(exceptions)} items, total_diff_abs={payload['summary']['total_diff_abs']:.2f} -> {out_path}"
        )
    else:
        msgs.append("[DET] Intercompany: no mismatches above materiality")

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Intercompany reconciliation (mismatches)"))

    state.metrics.update(
        {
            "ic_mismatch_count": len(exceptions),
            "ic_mismatch_total_diff_abs": payload["summary"]["total_diff_abs"],
            "ic_mismatch_by_pair": payload["summary"]["by_pair_diff_abs"],
            "intercompany_reconciliation_artifact": str(out_path),
        }
    )

    return state
