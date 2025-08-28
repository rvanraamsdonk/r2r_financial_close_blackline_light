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
    render_template,
    call_openai_json,
    openai_enabled,
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


def _invoke_ai(kind: str, template_name: str, context: Dict[str, Any], payload: Dict[str, Any]) -> Dict[str, Any]:
    """If OpenAI is enabled, render template and invoke model, expecting JSON.

    The returned dict is merged into payload (shallow merge for known keys per kind).
    """
    if not openai_enabled():
        return payload
    prompt = render_template(template_name, context)
    system = (
        "You are a finance assistant. Return ONLY valid JSON with the required keys for the requested analysis. "
        "Do not include markdown, prose, or explanatory text outside the JSON response."
    )
    resp = call_openai_json(prompt, system=system)
    # Shallow merge for known top-level fields
    try:
        match kind:
            case "validation":
                for k in ("root_causes", "remediations"):
                    if isinstance(resp.get(k), list):
                        payload[k] = resp[k]
            case "ap_ar":
                for k in ("matches",):
                    if isinstance(resp.get(k), list):
                        payload[k] = resp[k]
            case "intercompany":
                for k in ("candidate_pairs", "je_proposals"):
                    if isinstance(resp.get(k), list):
                        payload[k] = resp[k]
            case "flux":
                if isinstance(resp.get("narratives"), list):
                    payload["narratives"] = resp["narratives"]
            case "hitl":
                for k in ("case_summaries", "next_actions"):
                    if isinstance(resp.get(k), list):
                        payload[k] = resp[k]
            case "bank":
                if isinstance(resp.get("rationales"), list):
                    payload["rationales"] = resp["rationales"]
            case "accruals":
                for k in ("narratives", "je_rationales"):
                    if isinstance(resp.get(k), list):
                        payload[k] = resp[k]
            case "gatekeeping":
                if isinstance(resp.get("rationales"), list):
                    payload["rationales"] = resp["rationales"]
            case "controls":
                for k in ("owner_summaries", "residual_risks"):
                    if isinstance(resp.get(k), list):
                        payload[k] = resp[k]
            case "report":
                if isinstance(resp.get("executive_summary"), str):
                    payload["executive_summary"] = resp["executive_summary"]
            case _:
                pass
    except Exception:
        # Keep original payload on any merge error
        return payload
    return payload


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
    # Enrich validation context with optional gatekeeping aggregates to avoid Jinja Undefined
    categories, totals = {}, {}
    try:
        gk_path = (state.metrics or {}).get("gatekeeping_artifact")
        if gk_path and Path(gk_path).exists():
            with Path(gk_path).open("r", encoding="utf-8") as f:
                gk = json.load(f)
            categories = gk.get("categories") or {}
            totals = gk.get("totals") or {}
    except Exception:
        categories, totals = {}, {}
    # Try to populate via OpenAI
    context = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "counts": inputs["counts"],
        "categories": categories,
        "totals": totals,
    }
    payload = _invoke_ai("validation", "validation.md", context, payload)
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
    # Extract compact top-N AP/AR exception slices to enrich prompt context
    ap_slice = []
    ar_slice = []
    try:
        ap_path = m.get("ap_reconciliation_artifact")
        if ap_path and Path(ap_path).exists():
            with Path(ap_path).open("r", encoding="utf-8") as f:
                ap_json = json.load(f)
            ap_exc = ap_json.get("exceptions") or []
            # Sort by absolute amount desc; take top 8 for context compactness
            ap_exc_sorted = sorted(ap_exc, key=lambda e: abs(float(e.get("amount", 0.0))), reverse=True)[:8]
            for e in ap_exc_sorted:
                ap_slice.append(
                    {
                        "bill_id": e.get("bill_id"),
                        "entity": e.get("entity"),
                        "vendor_name": e.get("vendor_name"),
                        "bill_date": e.get("bill_date"),
                        "amount": float(e.get("amount", 0.0)),
                        "currency": e.get("currency"),
                        "age_days": int(e.get("age_days", 0) or 0),
                        "status": e.get("status"),
                        "reason": e.get("reason"),
                        "ai_rationale": e.get("ai_rationale"),
                        "candidates": e.get("candidates") or [],
                    }
                )
    except Exception:
        # Non-fatal; continue with minimal context
        ap_slice = []
    try:
        ar_path = m.get("ar_reconciliation_artifact")
        if ar_path and Path(ar_path).exists():
            with Path(ar_path).open("r", encoding="utf-8") as f:
                ar_json = json.load(f)
            ar_exc = ar_json.get("exceptions") or []
            ar_exc_sorted = sorted(ar_exc, key=lambda e: abs(float(e.get("amount", 0.0))), reverse=True)[:8]
            for e in ar_exc_sorted:
                ar_slice.append(
                    {
                        "invoice_id": e.get("invoice_id"),
                        "entity": e.get("entity"),
                        "customer_name": e.get("customer_name"),
                        "invoice_date": e.get("invoice_date"),
                        "amount": float(e.get("amount", 0.0)),
                        "currency": e.get("currency"),
                        "age_days": int(e.get("age_days", 0) or 0),
                        "status": e.get("status"),
                        "reason": e.get("reason"),
                        "ai_rationale": e.get("ai_rationale"),
                        "candidates": e.get("candidates") or [],
                    }
                )
    except Exception:
        ar_slice = []
    context = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "unresolved_summary": payload["unresolved_summary"],
        # enriched deterministic evidence slices
        "ap_exceptions": ap_slice,
        "ar_exceptions": ar_slice,
    }
    payload = _invoke_ai("ap_ar", "ap_ar.md", context, payload)
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
    # Extract compact top-N IC exception slices (schema-agnostic, safe)
    ic_slice = []
    try:
        ic_path = m.get("intercompany_reconciliation_artifact")
        if ic_path and Path(ic_path).exists():
            with Path(ic_path).open("r", encoding="utf-8") as f:
                ic_json = json.load(f)
            ic_exc = ic_json.get("exceptions") or []
            # Sorting key prefers any present difference metric; fallback to 0.0
            def diff_key(e: Dict[str, Any]) -> float:
                for k in ("diff", "amount_diff", "delta", "delta_usd"):
                    try:
                        return abs(float(e.get(k, 0.0)))
                    except Exception:
                        continue
                return 0.0
            ic_exc_sorted = sorted(ic_exc, key=diff_key, reverse=True)[:8]
            for e in ic_exc_sorted:
                compact = {k: e.get(k) for k in (
                    "pair", "src_entity", "dst_entity", "src_amount", "dst_amount", "currency",
                    "status", "reason", "ai_rationale", "je_proposal_id",
                    "diff", "amount_diff", "delta", "delta_usd",
                ) if k in e}
                ic_slice.append(compact)
    except Exception:
        ic_slice = []
    context = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "counts": inputs["counts"],
        "ic_exceptions": ic_slice,
    }
    payload = _invoke_ai("intercompany", "intercompany.md", context, payload)
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
    # Extract top variances for compact context from flux analysis rows
    flux_slice = []
    try:
        flux_path = m.get("flux_analysis_artifact")
        if flux_path and Path(flux_path).exists():
            with Path(flux_path).open("r", encoding="utf-8") as f:
                flux_json = json.load(f)
            rows = flux_json.get("rows") or []
            def variance_magnitude(r: Dict[str, Any]) -> float:
                # prefer the larger of abs var vs budget/prior when available
                vb = abs(float(r.get("var_vs_budget", 0.0) or 0.0))
                vp = abs(float(r.get("var_vs_prior", 0.0) or 0.0))
                return max(vb, vp)
            top_rows = sorted(rows, key=variance_magnitude, reverse=True)[:12]
            for r in top_rows:
                flux_slice.append({
                    "entity": r.get("entity"),
                    "account": r.get("account"),
                    "var_vs_budget": r.get("var_vs_budget"),
                    "var_vs_prior": r.get("var_vs_prior"),
                    "pct_vs_budget": r.get("pct_vs_budget"),
                    "pct_vs_prior": r.get("pct_vs_prior"),
                    "threshold_usd": r.get("threshold_usd"),
                    "band_vs_budget": r.get("band_vs_budget"),
                    "band_vs_prior": r.get("band_vs_prior"),
                    "ai_basis": r.get("ai_basis"),
                })
    except Exception:
        flux_slice = []
    context = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "counts": inputs["counts"],
        "top_variances": flux_slice,
    }
    payload = _invoke_ai("flux", "flux.md", context, payload)
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
    # Include compact open case slices
    cases_slice = []
    try:
        cases_path = m.get("hitl_cases_artifact")
        if cases_path and Path(cases_path).exists():
            with Path(cases_path).open("r", encoding="utf-8") as f:
                cases = json.load(f)
            def severity_rank(s: str) -> int:
                order = {"critical": 3, "high": 2, "medium": 1, "low": 0}
                return order.get((s or "").lower(), 0)
            open_cases = [c for c in (cases or []) if (c.get("status") or "").lower() == "open"]
            top = sorted(open_cases, key=lambda c: severity_rank(c.get("severity")), reverse=True)[:8]
            for c in top:
                cases_slice.append({
                    "id": c.get("id"),
                    "source": c.get("source"),
                    "severity": c.get("severity"),
                    "title": c.get("title"),
                })
    except Exception:
        cases_slice = []
    context = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "counts": inputs["counts"],
        "open_cases": cases_slice,
    }
    payload = _invoke_ai("hitl", "hitl.md", context, payload)
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
    # Include compact bank exception slices if present
    bank_slice = []
    try:
        bank_path = m.get("bank_reconciliation_artifact")
        if bank_path and Path(bank_path).exists():
            with Path(bank_path).open("r", encoding="utf-8") as f:
                bank_json = json.load(f)
            exc = bank_json.get("exceptions") or []
            def amt(e: Dict[str, Any]) -> float:
                try:
                    return abs(float(e.get("amount", 0.0)))
                except Exception:
                    return 0.0
            top_exc = sorted(exc, key=amt, reverse=True)[:8]
            for e in top_exc:
                compact = {k: e.get(k) for k in (
                    "entity", "date", "amount", "currency", "counterparty", "transaction_type",
                    "status", "reason", "ai_rationale",
                ) if k in e}
                bank_slice.append(compact)
    except Exception:
        bank_slice = []
    context = {"period": state.period, "entity": state.entity, "citations": payload["citations"], "bank_exceptions": bank_slice}
    payload = _invoke_ai("bank", "bank.md", context, payload)
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
    # Include compact accrual exceptions and proposals slices
    accr_exc_slice, accr_prop_slice = [], []
    try:
        accr_path = m.get("accruals_artifact")
        if accr_path and Path(accr_path).exists():
            with Path(accr_path).open("r", encoding="utf-8") as f:
                accr = json.load(f)
            exc = accr.get("exceptions") or []
            def exc_amt(e: Dict[str, Any]) -> float:
                try:
                    return abs(float(e.get("amount_usd", 0.0)))
                except Exception:
                    return 0.0
            top_exc = sorted(exc, key=exc_amt, reverse=True)[:8]
            for e in top_exc:
                accr_exc_slice.append({
                    "accrual_id": e.get("accrual_id"),
                    "entity": e.get("entity"),
                    "amount_usd": e.get("amount_usd"),
                    "status": e.get("status"),
                    "accrual_date": e.get("accrual_date"),
                    "reversal_date": e.get("reversal_date"),
                    "reason": e.get("reason"),
                })
            props = accr.get("proposals") or []
            def prop_amt(p: Dict[str, Any]) -> float:
                try:
                    return abs(float(p.get("amount_usd", 0.0)))
                except Exception:
                    return 0.0
            top_props = sorted(props, key=prop_amt, reverse=True)[:6]
            for p in top_props:
                accr_prop_slice.append({
                    "proposal_type": p.get("proposal_type"),
                    "entity": p.get("entity"),
                    "accrual_id": p.get("accrual_id"),
                    "proposed_period": p.get("proposed_period"),
                    "amount_usd": p.get("amount_usd"),
                })
    except Exception:
        accr_exc_slice, accr_prop_slice = [], []
    context = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "accruals_exceptions": accr_exc_slice,
        "accruals_proposals": accr_prop_slice,
    }
    payload = _invoke_ai("accruals", "accruals.md", context, payload)
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
    # Add gatekeeping categories and totals for richer context
    categories, totals = {}, {}
    try:
        gk_path = m.get("gatekeeping_artifact")
        if gk_path and Path(gk_path).exists():
            with Path(gk_path).open("r", encoding="utf-8") as f:
                gk = json.load(f)
            categories = gk.get("categories") or {}
            totals = gk.get("totals") or {}
    except Exception:
        categories, totals = {}, {}
    context = {
        "period": state.period,
        "entity": state.entity,
        "citations": payload["citations"],
        "risk": payload.get("risk_level"),
        "counts": {"risk_level": payload.get("risk_level")},
        "categories": categories,
        "totals": totals,
    }
    payload = _invoke_ai("gatekeeping", "validation.md", context, payload)
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
    # Include failing or notable controls as compact list
    controls_slice = []
    try:
        ctrl_path = m.get("controls_mapping_artifact")
        if ctrl_path and Path(ctrl_path).exists():
            with Path(ctrl_path).open("r", encoding="utf-8") as f:
                ctrl = json.load(f)
            mappings = (ctrl.get("mappings") or {}).items()
            for key, val in mappings:
                v = val.get("value") if isinstance(val, dict) else None
                # Select booleans that are concerning (False) and counts above zero
                if (isinstance(v, bool) and v is False) or (isinstance(v, (int, float)) and float(v) > 0):
                    controls_slice.append({
                        "key": key,
                        "control_id": val.get("control_id") if isinstance(val, dict) else None,
                        "value": v,
                        "description": val.get("description") if isinstance(val, dict) else None,
                    })
            controls_slice = controls_slice[:12]
    except Exception:
        controls_slice = []
    context = {"period": state.period, "entity": state.entity, "citations": payload["citations"], "controls_notable": controls_slice}
    payload = _invoke_ai("controls", "controls.md", context, payload)
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
    # Include key highlights for the executive summary from gatekeeping and flux
    highlights = {}
    try:
        gk_path = m.get("gatekeeping_artifact")
        if gk_path and Path(gk_path).exists():
            with Path(gk_path).open("r", encoding="utf-8") as f:
                gk = json.load(f)
            highlights["risk_level"] = gk.get("risk_level")
            highlights["block_close"] = gk.get("block_close")
            highlights["categories"] = gk.get("categories")
    except Exception:
        pass
    context = {"period": state.period, "entity": state.entity, "citations": payload["citations"], "highlights": highlights}
    payload = _invoke_ai("report", "report.md", context, payload)
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
