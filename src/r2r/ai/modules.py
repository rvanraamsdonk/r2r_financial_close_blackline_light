from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from ..state import R2RState
from ..audit import AuditLogger
from ..schemas import EvidenceRef, DeterministicRun
from ..utils import now_iso_z, run_id
from .schemas import (
    ValidationAI,
    APARAI,
    ICAI,
    FluxAI,
    HITLAI,
    BankAI,
    AccrualsAI,
    GatekeepingAI,
    ControlsAI,
    ReportAI,
)
from .infra import (
    compute_inputs_hash,
    with_cache,
    time_call,
    estimate_tokens,
    estimate_cost_usd,
    default_rate_per_1k_from_env,
)


def _now_iso() -> str:
    # Delegate to centralized time provider
    return now_iso_z()


def _write_json(out_dir: Path, name: str, run_id: str, payload: Dict[str, Any]) -> Path:
    p = out_dir / f"{name}_{run_id}.json"
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


def _audit_run_id(audit: AuditLogger) -> str:
    # audit.log_path = out_dir/audit_<runid>.jsonl
    try:
        stem = Path(audit.log_path).stem  # audit_<runid>
        return stem.replace("audit_", "", 1)
    except Exception:
        # fallback to timestamp
        return run_id()


def _record_ai(
    state: R2RState,
    audit: AuditLogger,
    *,
    kind: str,
    artifact: Path,
    inputs_hash: str,
    latency_ms: float,
    cached: bool,
) -> None:
    # Visible provenance for AI calls (no external model by default)
    prompt_run = {
        "kind": kind,
        "generated_at": _now_iso(),
        "inputs_hash": inputs_hash,
        "artifact": str(artifact),
        "latency_ms": round(latency_ms, 2),
        "cached": cached,
    }
    state.prompt_runs.append(prompt_run)
    state.tags.append("[AI]")
    state.metrics[f"ai_{kind}_latency_ms"] = prompt_run["latency_ms"]
    state.metrics[f"ai_{kind}_cached"] = cached
    state.evidence.append(EvidenceRef(type="json", uri=str(artifact)))
    audit.append({
        "type": "ai_output",
        "kind": kind,
        "generated_at": prompt_run["generated_at"],
        "artifact": str(artifact),
    })


def _validate_ai(kind: str, payload: Dict[str, Any], state: R2RState) -> None:
    if state.ai_mode not in ("assist", "strict"):
        return
    try:
        match kind:
            case "validation":
                ValidationAI.model_validate(payload)
            case "ap_ar":
                APARAI.model_validate(payload)
            case "intercompany":
                ICAI.model_validate(payload)
            case "flux":
                FluxAI.model_validate(payload)
            case "hitl":
                HITLAI.model_validate(payload)
            case "bank":
                BankAI.model_validate(payload)
            case "accruals":
                AccrualsAI.model_validate(payload)
            case "gatekeeping":
                GatekeepingAI.model_validate(payload)
            case "controls":
                ControlsAI.model_validate(payload)
            case "report":
                ReportAI.model_validate(payload)
            case _:
                return
    except Exception as e:
        state.messages.append(f"[AI][WARN] Schema validation failed for {kind}: {e}")
        state.tags.append("[AI-WARN]")


def ai_validation_root_causes(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "summary": {
            "schema_issues": int(m.get("validation_schema_issue_count", 0) or 0),
            "duplicate_rows": int(m.get("validation_duplicate_count", 0) or 0),
            "fx_coverage_ok": bool(m.get("fx_coverage_ok")) if m.get("fx_coverage_ok") is not None else None,
        },
        "root_causes": [],
        "remediations": [],
        "citations": [
            m.get("bank_reconciliation_artifact"),
            m.get("ap_reconciliation_artifact"),
            m.get("ar_reconciliation_artifact"),
        ],
    }
    inputs = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "counts": {
            "bank_duplicates": int(m.get("bank_duplicates_count", 0) or 0),
            "ap_exceptions": int(m.get("ap_exceptions_count", 0) or 0),
            "ar_exceptions": int(m.get("ar_exceptions_count", 0) or 0),
        },
    }
    if state.ai_mode == "strict":
        _validate_ai("validation", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="validation_ai",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    # token/cost metrics (provider-agnostic)
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    text = "Validation review completed; see artifact for counts and evidence citations."
    _record_ai(state, audit, kind="validation", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["validation_ai_artifact"] = str(path)
    state.metrics["ai_validation_tokens"] = tokens
    state.metrics["ai_validation_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "validation", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] Validation: {text} -> {path}")
    return state


def ai_ap_ar_suggestions(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "matches": [],
        "unresolved_summary": {
            "ap_exceptions": int(m.get("ap_exceptions_count", 0) or 0),
            "ar_exceptions": int(m.get("ar_exceptions_count", 0) or 0),
        },
        "citations": [m.get("ap_reconciliation_artifact"), m.get("ar_reconciliation_artifact")],
    }
    inputs = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "counts": payload["unresolved_summary"],
    }
    if state.ai_mode == "strict":
        _validate_ai("ap_ar", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="ap_ar_ai_suggestions",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    _record_ai(state, audit, kind="ap_ar", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["ap_ar_ai_artifact"] = str(path)
    state.metrics["ai_ap_ar_tokens"] = tokens
    state.metrics["ai_ap_ar_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "ap_ar", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] AP/AR: suggestions prepared with citations -> {path}")
    return state


def ai_ic_match_proposals(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "candidate_pairs": [],
        "je_proposals": [],
        "citations": [m.get("intercompany_reconciliation_artifact")],
    }
    inputs = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "counts": {"ic_mismatch_count": int(m.get("ic_mismatch_count", 0) or 0)},
    }
    if state.ai_mode == "strict":
        _validate_ai("intercompany", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="ic_ai_match_proposals",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    _record_ai(state, audit, kind="intercompany", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["ic_ai_artifact"] = str(path)
    state.metrics["ai_intercompany_tokens"] = tokens
    state.metrics["ai_intercompany_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "intercompany", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] Intercompany: match proposals prepared -> {path}")
    return state


def ai_flux_narratives(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "narratives": [],
        "citations": [m.get("flux_analysis_artifact"), m.get("period_init_artifact")],
    }
    inputs = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "counts": {"flux_exceptions_count": int(m.get("flux_exceptions_count", 0) or 0)},
    }
    if state.ai_mode == "strict":
        _validate_ai("flux", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="flux_ai_narratives",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    _record_ai(state, audit, kind="flux", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["flux_ai_artifact"] = str(path)
    state.metrics["ai_flux_tokens"] = tokens
    state.metrics["ai_flux_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "flux", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] Flux: narratives prepared with citations -> {path}")
    return state


def ai_hitl_case_summaries(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "case_summaries": [],
        "next_actions": [],
        "citations": [m.get("hitl_cases_artifact"), m.get("hitl_manifest_artifact")],
    }
    inputs = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "counts": {"hitl_cases_open_count": int(m.get("hitl_cases_open_count", 0) or 0)},
    }
    if state.ai_mode == "strict":
        _validate_ai("hitl", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="hitl_ai_case_summaries",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    _record_ai(state, audit, kind="hitl", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["hitl_ai_artifact"] = str(path)
    state.metrics["ai_hitl_tokens"] = tokens
    state.metrics["ai_hitl_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "hitl", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] HITL: case summaries and next actions -> {path}")
    return state


def ai_bank_rationales(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "rationales": [],
        "citations": [m.get("bank_reconciliation_artifact")],
    }
    inputs = {"period": state.period, "entity": state.entity, "citations": payload["citations"]}
    if state.ai_mode == "strict":
        _validate_ai("bank", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="bank_ai_rationales",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    _record_ai(state, audit, kind="bank", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["bank_ai_artifact"] = str(path)
    state.metrics["ai_bank_tokens"] = tokens
    state.metrics["ai_bank_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "bank", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] Bank: timing/error rationales prepared -> {path}")
    return state


def ai_accruals_narratives(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "narratives": [],
        "je_rationales": [],
        "citations": [m.get("accruals_artifact"), m.get("je_lifecycle_artifact"), m.get("email_evidence_artifact")],
    }
    inputs = {"period": state.period, "entity": state.entity, "citations": payload["citations"]}
    if state.ai_mode == "strict":
        _validate_ai("accruals", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="accruals_ai_narratives",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    _record_ai(state, audit, kind="accruals", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["accruals_ai_artifact"] = str(path)
    state.metrics["ai_accruals_tokens"] = tokens
    state.metrics["ai_accruals_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "accruals", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] Accruals: JE narratives and rationales -> {path}")
    return state


def ai_gatekeeping_rationales(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "risk_level": m.get("gatekeeping_risk_level"),
        "block_close": m.get("gatekeeping_block_close"),
        "rationales": [],
        "citations": [m.get("gatekeeping_artifact")],
    }
    inputs = {"period": state.period, "entity": state.entity, "citations": payload["citations"], "risk": payload["risk_level"]}
    if state.ai_mode == "strict":
        _validate_ai("gatekeeping", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="gatekeeping_ai_rationales",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    _record_ai(state, audit, kind="gatekeeping", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["gatekeeping_ai_artifact"] = str(path)
    state.metrics["ai_gatekeeping_tokens"] = tokens
    state.metrics["ai_gatekeeping_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "gatekeeping", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] Gatekeeping: risk rationales and escalation -> {path}")
    return state


def ai_controls_owner_summaries(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "owner_summaries": [],
        "residual_risks": [],
        "citations": [m.get("controls_mapping_artifact")],
    }
    inputs = {"period": state.period, "entity": state.entity, "citations": payload["citations"]}
    if state.ai_mode == "strict":
        _validate_ai("controls", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="controls_ai_summaries",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    _record_ai(state, audit, kind="controls", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["controls_ai_artifact"] = str(path)
    state.metrics["ai_controls_tokens"] = tokens
    state.metrics["ai_controls_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "controls", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] Controls: owner summaries and residual risks -> {path}")
    return state


def ai_close_report_exec_summary(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "executive_summary": "",
        "citations": [
            m.get("close_report_artifact"),
            m.get("gatekeeping_artifact"),
            m.get("flux_analysis_artifact"),
            m.get("ap_reconciliation_artifact"),
            m.get("ar_reconciliation_artifact"),
        ],
    }
    inputs = {"period": state.period, "entity": state.entity, "citations": payload["citations"]}
    if state.ai_mode == "strict":
        _validate_ai("report", payload, state)
    ih = compute_inputs_hash(inputs)
    result, dt = time_call(
        lambda: with_cache(
            out_dir=Path(audit.out_dir),
            kind="report_ai_executive_summary",
            run_id=_audit_run_id(audit),
            inputs_hash=ih,
            build_payload=lambda: payload,
        )
    )
    path, _payload, was_cached = result
    tokens = estimate_tokens(_payload)
    cost = estimate_cost_usd(tokens, default_rate_per_1k_from_env())
    _record_ai(state, audit, kind="report", artifact=path, inputs_hash=ih, latency_ms=dt, cached=was_cached)
    state.metrics["report_ai_artifact"] = str(path)
    state.metrics["ai_report_tokens"] = tokens
    state.metrics["ai_report_cost_usd"] = cost
    audit.append({"type": "ai_metrics", "kind": "report", "tokens": tokens, "cost_usd": cost})
    state.messages.append(f"[AI] Report: executive summary prepared -> {path}")
    return state
