from __future__ import annotations

import json
from .. import utils
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState


def _hash_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def gatekeeping_aggregate(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic Gatekeeping & Risk Aggregation
    - Aggregate exception signals and key controls from prior deterministic steps
    - Compute a simple risk score and block/allow flag
    - Emit a provenance-ready artifact, log evidence and deterministic run
    """
    m = state.metrics or {}

    # Core controls/health
    fx_ok: bool | None = m.get("fx_coverage_ok")  # bool or None
    tb_bal_ok: bool | None = m.get("tb_balanced_by_entity")  # bool or None

    # Exception counts (fallback to 0 if missing)
    def _ival(key: str) -> int:
        try:
            v = m.get(key, 0)
            return int(v) if v is not None else 0
        except Exception:
            return 0

    bank_cnt = _ival("bank_duplicates_count")
    ap_cnt = _ival("ap_exceptions_count")
    ar_cnt = _ival("ar_exceptions_count")
    ic_cnt = _ival("ic_mismatch_count")
    accr_cnt = _ival("accruals_exception_count")
    je_cnt = _ival("je_exceptions_count")
    flux_cnt = _ival("flux_exceptions_count")

    # Totals where available (for contextualization only)
    def _fval(key: str) -> float | None:
        try:
            v = m.get(key)
            return float(v) if v is not None else None
        except Exception:
            return None

    totals = {
        "ap_exceptions_total_abs": _fval("ap_exceptions_total_abs"),
        "ar_exceptions_total_abs": _fval("ar_exceptions_total_abs"),
        "ic_mismatch_total_diff_abs": _fval("ic_mismatch_total_diff_abs"),
        "accruals_exception_total_usd": _fval("accruals_exception_total_usd"),
        "je_exceptions_total_abs": _fval("je_exceptions_total_abs"),
    }

    categories: Dict[str, int] = {
        "bank_duplicates": bank_cnt,
        "ap_exceptions": ap_cnt,
        "ar_exceptions": ar_cnt,
        "ic_mismatches": ic_cnt,
        "accruals_exceptions": accr_cnt,
        "je_exceptions": je_cnt,
        "flux_exceptions": flux_cnt,
    }

    sources_triggered = sum(1 for v in categories.values() if v > 0)

    # Risk policy: simple and deterministic
    risk_level: str
    if fx_ok is False or tb_bal_ok is False or sources_triggered >= 3:
        risk_level = "high"
    elif sources_triggered in (1, 2):
        risk_level = "medium"
    else:
        risk_level = "low"
    block_close = bool(risk_level == "high")

    # Gather referenced artifacts already produced (URIs only)
    referenced_artifacts: Dict[str, str] = {}
    for k, v in list(m.items()):
        if isinstance(k, str) and k.endswith("_artifact") and isinstance(v, str):
            referenced_artifacts[k] = v

    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"gatekeeping_{run_id}.json"

    payload: Dict[str, Any] = {
        "generated_at": utils.now_iso_z(),
        "period": state.period,
        "entity_scope": state.entity,
        "inputs": {
            "fx_coverage_ok": fx_ok,
            "tb_balanced_by_entity": tb_bal_ok,
            "tb_entity_sums_usd": m.get("tb_entity_sums_usd"),
        },
        "categories": categories,
        "totals": totals,
        "risk_level": risk_level,
        "block_close": block_close,
        "referenced_artifacts": referenced_artifacts,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence: reference artifacts that informed aggregation (URIs only)
    for name, uri in referenced_artifacts.items():
        ev = EvidenceRef(type="json", uri=str(uri))
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

    # Deterministic run
    det = DeterministicRun(function_name="gatekeeping_aggregate")
    det.params = {"period": state.period, "entity": state.entity}
    det.output_hash = _hash_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
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
    state.messages.append(
        f"[DET] Gatekeeping: risk_level={risk_level}, sources={sources_triggered} -> {out_path}"
    )
    state.tags.append(
        OutputTag(method_type=MethodType.DET, rationale="Gatekeeping & risk aggregation")
    )

    state.metrics.update(
        {
            "gatekeeping_risk_level": risk_level,
            "gatekeeping_block_close": block_close,
            "gatekeeping_sources_triggered_count": sources_triggered,
            "gatekeeping_artifact": str(out_path),
        }
    )

    return state
