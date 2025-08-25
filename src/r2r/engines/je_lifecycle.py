from __future__ import annotations

import json
from .. import utils
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Set

import pandas as pd
from ..utils.strings import safe_str as _shared_safe_str

from ..audit.log import AuditLogger
from ..schemas import DeterministicRun, EvidenceRef, MethodType, OutputTag
from ..state import R2RState


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _truthy(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    s = str(val).strip().lower()
    return s in {"1", "true", "yes", "y", "t"}


def _safe_str(val: Any) -> str:
    """Compatibility wrapper delegating to shared util `safe_str`."""
    return _shared_safe_str(val)


def je_lifecycle(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic JE lifecycle review:
    - Load supporting/journal_entries.csv
    - Filter to current period and optional entity
    - Flag approval_status != 'Approved'
    - Flag manual entries missing supporting_doc
    - Flag reversal_flagged entries
    - Emit artifact, evidence (input_row_ids=je_id), deterministic run, messages/tags/metrics
    """
    period = state.period
    entity_scope = state.entity

    # Try enhanced journal entries first
    candidates = [
        Path(state.data_path) / "supporting" / "journal_entries_enhanced.csv",
        Path(state.data_path) / "supporting" / "journal_entries.csv",
    ]
    data_fp = None
    for c in candidates:
        if c.exists():
            data_fp = c
            break
    if data_fp is None:
        data_fp = Path(state.data_path) / "supporting" / "journal_entries.csv"  # fallback
    msgs: List[str] = []

    if not data_fp.exists():
        msgs.append("[DET] JE lifecycle: no supporting/journal_entries.csv; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="JE lifecycle (skipped)"))
        return state

    df = pd.read_csv(
        data_fp,
        dtype={
            "period": str,
            "entity": str,
            "je_id": str,
            "description": str,
            "debit_account": str,
            "credit_account": str,
            "amount": float,
            "currency": str,
            "source_system": str,
            "approval_status": str,
            "approver": str,
            "supporting_doc": str,
            "manual_flag": object,
            "reversal_flag": object,
            "linked_transaction": str,
        },
    )

    df = df[df["period"] == period]
    if entity_scope and entity_scope != "ALL":
        df = df[df["entity"] == entity_scope]

    if df.empty:
        msgs.append("[DET] JE lifecycle: no JEs in scope; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="JE lifecycle (skipped)"))
        return state

    exceptions: List[Dict[str, Any]] = []
    input_row_ids: Set[str] = set()

    # Materiality thresholds by entity for four-eyes enforcement
    materiality_map: Dict[str, float] = {}
    if isinstance(state.metrics.get("materiality_thresholds_usd"), dict):
        for k, v in state.metrics["materiality_thresholds_usd"].items():
            try:
                materiality_map[str(k)] = float(v)
            except Exception:
                continue

    for _, r in df.iterrows():
        je_id = str(r.get("je_id"))
        amount = float(r.get("amount", 0.0)) if pd.notna(r.get("amount")) else 0.0
        approval = _safe_str(r.get("approval_status"))
        supp = _safe_str(r.get("supporting_doc"))
        is_manual = _truthy(r.get("manual_flag"))
        is_reversal = _truthy(r.get("reversal_flag"))
        ent = _safe_str(r.get("entity"))
        approver = _safe_str(r.get("approver"))

        # Approval exceptions
        if approval and approval.lower() != "approved":
            reason = "approval_rejected" if approval.lower() == "rejected" else "approval_pending"
            exceptions.append(
                {
                    "je_id": je_id,
                    "entity": r.get("entity"),
                    "amount": amount,
                    "currency": r.get("currency"),
                    "source_system": r.get("source_system"),
                    "reason": reason,
                    "approval_status": approval,
                    "approver": r.get("approver"),
                }
            )
            input_row_ids.add(je_id)

        # Four-eyes enforcement for material amounts: require approved + approver present
        thr = materiality_map.get(ent)
        if thr is not None and abs(amount) > float(thr):
            if (not approval) or (approval.lower() != "approved") or (not approver):
                exceptions.append(
                    {
                        "je_id": je_id,
                        "entity": ent,
                        "amount": amount,
                        "currency": r.get("currency"),
                        "source_system": r.get("source_system"),
                        "reason": "four_eyes_breach",
                        "approval_status": approval,
                        "approver": approver,
                        "materiality_threshold_usd": float(thr),
                    }
                )
                input_row_ids.add(je_id)

        # Manual missing support
        if is_manual and (not supp):
            exceptions.append(
                {
                    "je_id": je_id,
                    "entity": r.get("entity"),
                    "amount": amount,
                    "currency": r.get("currency"),
                    "source_system": r.get("source_system"),
                    "reason": "manual_missing_support",
                }
            )
            input_row_ids.add(je_id)

        # Reversal flagged
        if is_reversal:
            exceptions.append(
                {
                    "je_id": je_id,
                    "entity": r.get("entity"),
                    "amount": amount,
                    "currency": r.get("currency"),
                    "source_system": r.get("source_system"),
                    "reason": "reversal_flagged",
                }
            )
            input_row_ids.add(je_id)

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"je_lifecycle_{run_id}.json"

    total_abs = float(sum(abs(e.get("amount", 0.0)) for e in exceptions))
    by_reason: Dict[str, int] = {}
    for e in exceptions:
        by_reason[e["reason"]] = by_reason.get(e["reason"], 0) + 1

    payload = {
        "generated_at": utils.now_iso_z(),
        "period": period,
        "entity_scope": entity_scope,
        "rules": {
            "flag_if_approval_not_approved": True,
            "flag_manual_missing_support": True,
            "flag_reversal": True,
        },
        "exceptions": exceptions,
        "summary": {
            "count": len(exceptions),
            "total_abs_amount": float(round(total_abs, 2)),
            "by_reason": by_reason,
        },
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence + deterministic
    ev = EvidenceRef(type="csv", uri=str(data_fp), input_row_ids=(sorted(input_row_ids) or None))
    state.evidence.append(ev)

    det = DeterministicRun(function_name="je_lifecycle")
    det.params = {"period": period, "entity": entity_scope}
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
            f"[DET] JE lifecycle exceptions: {len(exceptions)} items, total_abs={payload['summary']['total_abs_amount']:.2f} -> {out_path}"
        )
    else:
        msgs.append("[DET] JE lifecycle: no exceptions for period")

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="JE lifecycle review"))

    state.metrics.update(
        {
            "je_exceptions_count": len(exceptions),
            "je_exceptions_total_abs": payload["summary"]["total_abs_amount"],
            "je_exceptions_by_reason": by_reason,
            "je_lifecycle_artifact": str(out_path),
        }
    )

    return state
