from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from ..state import R2RState
from ..audit import AuditLogger
from ..schemas import EvidenceRef, DeterministicRun


def _now_iso() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


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
        return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _record_ai(state: R2RState, audit: AuditLogger, *, kind: str, payload: Dict[str, Any], artifact: Path) -> None:
    # Minimal visible provenance for AI calls (no external model by default)
    prompt_run = {
        "kind": kind,
        "generated_at": _now_iso(),
        "inputs_hash": hash(json.dumps(payload, sort_keys=True)),
        "artifact": str(artifact),
    }
    state.prompt_runs.append(prompt_run)  # visible provenance
    state.tags.append("[AI]")
    state.evidence.append(EvidenceRef(type="json", uri=str(artifact)))
    audit.append({
        "type": "ai_output",
        "kind": kind,
        "generated_at": prompt_run["generated_at"],
        "artifact": str(artifact),
    })


def ai_validation_root_causes(state: R2RState, audit: AuditLogger) -> R2RState:
    if state.ai_mode == "off":
        return state
    m = state.metrics or {}
    now = _now_iso()
    payload: Dict[str, Any] = {
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
    # Deterministic heuristic text for now
    text = "Validation review completed; see artifact for counts and evidence citations."
    path = _write_json(Path(audit.out_dir), "validation_ai", _audit_run_id(audit), payload)
    _record_ai(state, audit, kind="validation", payload=payload, artifact=path)
    state.metrics["validation_ai_artifact"] = str(path)
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
    path = _write_json(Path(audit.out_dir), "ap_ar_ai_suggestions", _audit_run_id(audit), payload)
    _record_ai(state, audit, kind="ap_ar", payload=payload, artifact=path)
    state.metrics["ap_ar_ai_artifact"] = str(path)
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
    path = _write_json(Path(audit.out_dir), "ic_ai_match_proposals", _audit_run_id(audit), payload)
    _record_ai(state, audit, kind="intercompany", payload=payload, artifact=path)
    state.metrics["ic_ai_artifact"] = str(path)
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
    path = _write_json(Path(audit.out_dir), "flux_ai_narratives", _audit_run_id(audit), payload)
    _record_ai(state, audit, kind="flux", payload=payload, artifact=path)
    state.metrics["flux_ai_artifact"] = str(path)
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
    path = _write_json(Path(audit.out_dir), "hitl_ai_case_summaries", _audit_run_id(audit), payload)
    _record_ai(state, audit, kind="hitl", payload=payload, artifact=path)
    state.metrics["hitl_ai_artifact"] = str(path)
    state.messages.append(f"[AI] HITL: case summaries and next actions -> {path}")
    return state
