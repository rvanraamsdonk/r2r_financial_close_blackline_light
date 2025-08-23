from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict

from ..audit.log import AuditLogger
from ..schemas import EvidenceRef, DeterministicRun, OutputTag, MethodType
from ..state import R2RState
from ..utils import now_iso_z


def _hash_payload(payload: Dict[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def close_reporting(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic Close Reporting & Evidence Pack
    Produces a manifest of key artifacts, a summary for executives/auditors, and references the audit log.
    """
    m = state.metrics or {}
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    now = now_iso_z()

    # Collect all artifact URIs present in metrics
    artifacts: Dict[str, str] = {
        k: str(v) for k, v in m.items() if isinstance(k, str) and k.endswith("_artifact") and isinstance(v, str)
    }

    summary = {
        "period": state.period,
        "entity": state.entity,
        "risk_level": m.get("gatekeeping_risk_level"),
        "block_close": bool(m.get("gatekeeping_block_close", False)),
        "open_hitl_cases": int(m.get("hitl_cases_open_count", 0) or 0),
        "tb_balanced_by_entity": m.get("tb_balanced_by_entity"),
        "fx_coverage_ok": m.get("fx_coverage_ok"),
        "key_counts": {
            "ap_exceptions": int(m.get("ap_exceptions_count", 0) or 0),
            "ar_exceptions": int(m.get("ar_exceptions_count", 0) or 0),
            "je_exceptions": int(m.get("je_exceptions_count", 0) or 0),
            "flux_exceptions": int(m.get("flux_exceptions_count", 0) or 0),
            "accruals_exceptions": int(m.get("accruals_exception_count", 0) or 0),
        },
    }

    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "artifacts": artifacts,
        "summary": summary,
        "audit_log": str(audit.log_path),
    }

    out_path = Path(audit.out_dir) / f"close_report_{run_id}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Evidence and deterministic run
    ev = EvidenceRef(type="json", uri=str(out_path))
    state.evidence.append(ev)
    audit.append({
        "type": "evidence",
        "id": ev.id,
        "evidence_type": ev.type,
        "uri": ev.uri,
        "timestamp": ev.timestamp.isoformat() + "Z",
    })

    det = DeterministicRun(function_name="close_reporting")
    det.params = {"period": state.period, "entity": state.entity}
    det.output_hash = _hash_payload(payload)
    state.det_runs.append(det)
    audit.append({
        "type": "deterministic",
        "fn": det.function_name,
        "output_hash": det.output_hash,
        "params": det.params,
        "artifact": str(out_path),
    })

    state.messages.append(f"[DET] Close reporting: evidence pack manifest -> {out_path}")
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Close reporting & evidence pack"))

    state.metrics.update({
        "close_report_artifact": str(out_path),
    })

    return state
