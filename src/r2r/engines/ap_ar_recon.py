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
from ..data.static_loader import load_ap_detail, load_ar_detail


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _safe_str(val: Any) -> str:
    """Return a stripped string or empty string for NaN/None/invalid values.

    Prevents AttributeError when pandas values are float('nan') by coercing
    safely to string only when not NaN.
    """
    if pd.isna(val):
        return ""
    try:
        return str(val).strip()
    except Exception:
        return ""


def _resolve_ap_path(data_path: Path, period: str) -> Path:
    base = Path(data_path) / "subledgers"
    for cand in [
        base / f"ap_detail_{period}.csv",
        base / f"ap_detail_{period.replace('-', '_')}.csv",
        base / "ap_detail_aug.csv",
    ]:
        if cand.exists():
            return cand
    return base / f"ap_detail_{period}.csv"  # best-effort fallback


def _resolve_ar_path(data_path: Path, period: str) -> Path:
    base = Path(data_path) / "subledgers"
    for cand in [
        base / f"ar_detail_{period}.csv",
        base / f"ar_detail_{period.replace('-', '_')}.csv",
        base / "ar_detail_aug.csv",
    ]:
        if cand.exists():
            return cand
    return base / f"ar_detail_{period}.csv"  # best-effort fallback


def ap_reconciliation(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic AP reconciliation (aging & duplicate flags):
    - Load AP detail filtered by period/entity
    - Flag overdue (status == 'Overdue') or age_days > 60
    - Flag notes containing 'Duplicate'
    - Emit artifact, evidence with input_row_ids, deterministic run, and metrics
    """
    period = state.period
    entity_scope = state.entity

    df = load_ap_detail(Path(state.data_path), period, entity_scope)

    # Resolve file path for evidence
    fp = _resolve_ap_path(Path(state.data_path), period)

    msgs: List[str] = []
    if df.empty:
        msgs.append("[DET] AP recon: no AP bills in scope; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="AP reconciliation (skipped)"))
        return state

    exceptions: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []

    for _, r in df.iterrows():
        status = _safe_str(r.get("status"))
        # age_days may be str/int; coerce safely
        try:
            age = int(r.get("age_days")) if pd.notna(r.get("age_days")) else 0
        except Exception:
            age = 0
        notes = _safe_str(r.get("notes"))
        reason: str | None = None
        if status == "Overdue":
            reason = "overdue"
        elif age > 60:
            reason = "age_gt_60"
        if not reason and ("duplicate" in notes.lower()):
            reason = "duplicate_flag"
        if reason:
            e = {
                "subledger": "AP",
                "entity": r.get("entity"),
                "bill_id": r.get("bill_id"),
                "vendor_name": r.get("vendor_name"),
                "bill_date": r.get("bill_date"),
                "amount": float(r.get("amount", 0.0)),
                "currency": r.get("currency"),
                "age_days": age,
                "status": status,
                "reason": reason,
                "notes": notes or None,
            }
            exceptions.append(e)
            input_row_ids.append(str(r.get("bill_id")))

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"ap_reconciliation_{run_id}.json"

    total_abs = float(sum(abs(e.get("amount", 0.0)) for e in exceptions))
    by_ent: Dict[str, float] = {}
    for e in exceptions:
        ent = str(e.get("entity"))
        by_ent[ent] = by_ent.get(ent, 0.0) + abs(float(e.get("amount", 0.0)))

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": period,
        "entity_scope": entity_scope,
        "rules": {
            "overdue_status": True,
            "age_days_threshold": 60,
            "duplicate_in_notes": True,
        },
        "exceptions": exceptions,
        "summary": {
            "count": len(exceptions),
            "total_abs_amount": float(round(total_abs, 2)),
            "by_entity_abs_amount": {k: float(round(v, 2)) for k, v in by_ent.items()},
        },
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence + deterministic run
    ev = EvidenceRef(type="csv", uri=str(fp), input_row_ids=input_row_ids or None)
    state.evidence.append(ev)

    det = DeterministicRun(function_name="ap_reconciliation")
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
            f"[DET] AP recon exceptions: {len(exceptions)} items, total_abs={payload['summary']['total_abs_amount']:.2f} -> {out_path}"
        )
    else:
        msgs.append("[DET] AP recon: no exceptions for period")

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="AP reconciliation"))

    state.metrics.update(
        {
            "ap_exceptions_count": len(exceptions),
            "ap_exceptions_total_abs": payload["summary"]["total_abs_amount"],
            "ap_exceptions_by_entity": payload["summary"]["by_entity_abs_amount"],
            "ap_reconciliation_artifact": str(out_path),
        }
    )

    return state


def ar_reconciliation(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic AR reconciliation (aging):
    - Load AR detail filtered by period/entity
    - Flag overdue (status == 'Overdue') or age_days > 60
    - Emit artifact, evidence with input_row_ids, deterministic run, and metrics
    """
    period = state.period
    entity_scope = state.entity

    df = load_ar_detail(Path(state.data_path), period, entity_scope)

    # Resolve file path for evidence
    fp = _resolve_ar_path(Path(state.data_path), period)

    msgs: List[str] = []
    if df.empty:
        msgs.append("[DET] AR recon: no AR invoices in scope; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="AR reconciliation (skipped)"))
        return state

    exceptions: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []

    for _, r in df.iterrows():
        status = _safe_str(r.get("status"))
        try:
            age = int(r.get("age_days")) if pd.notna(r.get("age_days")) else 0
        except Exception:
            age = 0
        reason: str | None = None
        if status == "Overdue":
            reason = "overdue"
        elif age > 60:
            reason = "age_gt_60"
        if reason:
            e = {
                "subledger": "AR",
                "entity": r.get("entity"),
                "invoice_id": r.get("invoice_id"),
                "customer_name": r.get("customer_name"),
                "invoice_date": r.get("invoice_date"),
                "amount": float(r.get("amount", 0.0)),
                "currency": r.get("currency"),
                "age_days": age,
                "status": status,
                "reason": reason,
            }
            exceptions.append(e)
            input_row_ids.append(str(r.get("invoice_id")))

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"ar_reconciliation_{run_id}.json"

    total_abs = float(sum(abs(e.get("amount", 0.0)) for e in exceptions))
    by_ent: Dict[str, float] = {}
    for e in exceptions:
        ent = str(e.get("entity"))
        by_ent[ent] = by_ent.get(ent, 0.0) + abs(float(e.get("amount", 0.0)))

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": period,
        "entity_scope": entity_scope,
        "rules": {
            "overdue_status": True,
            "age_days_threshold": 60,
        },
        "exceptions": exceptions,
        "summary": {
            "count": len(exceptions),
            "total_abs_amount": float(round(total_abs, 2)),
            "by_entity_abs_amount": {k: float(round(v, 2)) for k, v in by_ent.items()},
        },
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence + deterministic run
    ev = EvidenceRef(type="csv", uri=str(fp), input_row_ids=input_row_ids or None)
    state.evidence.append(ev)

    det = DeterministicRun(function_name="ar_reconciliation")
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
            f"[DET] AR recon exceptions: {len(exceptions)} items, total_abs={payload['summary']['total_abs_amount']:.2f} -> {out_path}"
        )
    else:
        msgs.append("[DET] AR recon: no exceptions for period")

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="AR reconciliation"))

    state.metrics.update(
        {
            "ar_exceptions_count": len(exceptions),
            "ar_exceptions_total_abs": payload["summary"]["total_abs_amount"],
            "ar_exceptions_by_entity": payload["summary"]["by_entity_abs_amount"],
            "ar_reconciliation_artifact": str(out_path),
        }
    )

    return state
