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

    # Consume auto-journaling results (from auto_journal_engine)
    auto_journal_cnt = _ival("auto_journals_count")
    auto_journal_total = _fval("auto_journals_total_usd") or 0.0

    totals = {
        "ap_exceptions_total_abs": _fval("ap_exceptions_total_abs"),
        "ar_exceptions_total_abs": _fval("ar_exceptions_total_abs"),
        "ic_mismatch_total_diff_abs": _fval("ic_mismatch_total_diff_abs"),
        "accruals_exception_total_usd": _fval("accruals_exception_total_usd"),
        "je_exceptions_total_abs": _fval("je_exceptions_total_abs"),
        "auto_journals_total_amount": auto_journal_total,
    }

    categories: Dict[str, int] = {
        "bank_duplicates": bank_cnt,
        "ap_exceptions": ap_cnt,
        "ar_exceptions": ar_cnt,
        "ic_mismatches": ic_cnt,
        "accruals_exceptions": accr_cnt,
        "je_exceptions": je_cnt,
        "flux_exceptions": flux_cnt,
        "auto_journals_created": auto_journal_cnt,
    }

    sources_triggered = sum(1 for k, v in categories.items() if v > 0 and k != "auto_journals_created")

    # Enhanced AI-first risk policy: more aggressive auto-closing
    # Calculate total exception amounts for materiality assessment
    gross_exception_amount = sum([
        totals.get("ap_exceptions_total_abs", 0) or 0,
        totals.get("ar_exceptions_total_abs", 0) or 0,
        totals.get("ic_mismatch_total_diff_abs", 0) or 0,
        totals.get("accruals_exception_total_usd", 0) or 0,
        totals.get("je_exceptions_total_abs", 0) or 0,
    ])

    # Auto-journals reduce the net exception amount
    net_exception_amount = gross_exception_amount - auto_journal_total
    
    # Materiality thresholds (configurable)
    MATERIALITY_THRESHOLD = 50000  # $50K
    HIGH_RISK_THRESHOLD = 250000   # $250K
    
    # Two-stage gatekeeping: Preliminary deterministic assessment
    CRITICAL_THRESHOLD = 1000000  # $1M - extreme materiality
    
    risk_level: str
    preliminary_decision: str
    final_decision_pending = False
    
    # Stage 1: Hard stops that cannot be overridden
    if fx_ok is False or tb_bal_ok is False:
        risk_level = "high"
        preliminary_decision = "BLOCKED"
        final_decision_pending = False
    elif net_exception_amount > CRITICAL_THRESHOLD:
        risk_level = "critical" 
        preliminary_decision = "BLOCKED"
        final_decision_pending = False
    # Everything else gets conditional approval pending AI analysis
    else:
        if sources_triggered >= 3 or net_exception_amount > MATERIALITY_THRESHOLD:
            risk_level = "medium"
        elif sources_triggered <= 1 and net_exception_amount <= MATERIALITY_THRESHOLD:
            risk_level = "low"
        else:
            risk_level = "medium"
        
        preliminary_decision = "CONDITIONAL_APPROVAL"
        final_decision_pending = True
    
    # For now, block_close reflects preliminary decision
    block_close = preliminary_decision == "BLOCKED"
    auto_close_eligible = preliminary_decision == "CONDITIONAL_APPROVAL"

    # Gather referenced artifacts already produced (URIs only)
    referenced_artifacts: Dict[str, str] = {}
    for k, v in list(m.items()):
        if isinstance(k, str) and k.endswith("_artifact") and isinstance(v, str):
            referenced_artifacts[k] = v

    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"gatekeeping_{run_id}.json"

    # Generate deterministic rationale for preliminary decisions
    deterministic_rationale = ""
    
    auto_journal_text = f"{auto_journal_cnt} automated journal(s) totaling ${auto_journal_total:,.2f} were created to resolve exceptions." if auto_journal_cnt > 0 else ""

    if preliminary_decision == "BLOCKED":
        if fx_ok is False or tb_bal_ok is False:
            deterministic_rationale = f"BLOCKED: Critical control failure detected (FX: {fx_ok}, TB: {tb_bal_ok}). {auto_journal_text} Manual intervention required."
        else:
            deterministic_rationale = f"BLOCKED: Extreme materiality breach (${net_exception_amount:,.2f} > ${CRITICAL_THRESHOLD:,.0f}). {auto_journal_text} Management escalation required."
    else:  # CONDITIONAL_APPROVAL
        deterministic_rationale = f"CONDITIONAL APPROVAL: Preliminary assessment passed. Net exceptions: ${net_exception_amount:,.2f}, Sources: {sources_triggered}. {auto_journal_text} Pending comprehensive AI analysis for final decision."
    
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
        "preliminary_decision": preliminary_decision,
        "final_decision_pending": final_decision_pending,
        "block_close": block_close,
        "auto_close_eligible": auto_close_eligible,
        "gross_exception_amount": gross_exception_amount,
        "auto_journal_amount": auto_journal_total,
        "net_exception_amount": net_exception_amount,
        "materiality_threshold": MATERIALITY_THRESHOLD,
        "critical_threshold": CRITICAL_THRESHOLD,
        "deterministic_rationale": deterministic_rationale,
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

    # Simple console progress tracking
    console = getattr(state, 'console', None)
    if console:
        console.start_phase('Gatekeeping Assessment')
        
        # Progress through gatekeeping analysis
        console.progress("Analyzing exception patterns", processed=50, total=100)
        console.progress("Evaluating risk factors", processed=75, total=100)
        console.progress(f"Final decision: {('BLOCKED' if block_close else 'APPROVED')} ({risk_level} risk)", processed=sum(categories.values()), total=sum(categories.values()))
        console.complete_phase(
            status="BLOCKED" if block_close else "SUCCESS",
            summary=f"Decision: {'BLOCKED' if block_close else 'APPROVED'}, Risk: {risk_level}, Auto-approved: {auto_journal_cnt}/{sum(categories.values())}",
            artifacts=[str(out_path)]
        )

    # Redundant legacy console output removed; enhanced console used above

    state.metrics.update(
        {
            "gatekeeping_risk_level": risk_level,
            "gatekeeping_block_close": block_close,
            "gatekeeping_auto_close_eligible": auto_close_eligible,
            "gatekeeping_sources_triggered_count": sources_triggered,
            "gatekeeping_net_exception_amount": net_exception_amount,
            "gatekeeping_deterministic_rationale": deterministic_rationale,
            "gatekeeping_artifact": str(out_path),
            "gatekeeping_total_exceptions": int(sum(categories.values())),
            "gatekeeping_auto_approved_count": int(auto_journal_cnt),
        }
    )

    return state
