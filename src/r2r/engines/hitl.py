from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState


@dataclass
class Case:
    id: str
    created_at: str
    period: str
    entity: str
    source: str
    severity: str
    title: str
    description: str
    evidence_uris: List[str]
    status: str = "open"  # open|resolved
    assignee: Optional[str] = None
    resolution_notes: Optional[str] = None
    resolved_at: Optional[str] = None


def _hash_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def _mk_case_id(period: str, source: str, idx: int) -> str:
    return f"CASE-{period.replace('-', '')}-{source.upper()}-{idx:03d}"


def open_hitl_cases(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic HITL Case Management
    - Open cases based on gatekeeping outcomes and per-category exception counts
    - Persist cases list and manifest, record provenance
    """
    m = state.metrics or {}
    run_id = Path(audit.log_path).stem.replace("audit_", "")

    # Determine which categories triggered
    categories = {
        "bank_duplicates": int(m.get("bank_duplicates_count", 0) or 0),
        "ap_exceptions": int(m.get("ap_exceptions_count", 0) or 0),
        "ar_exceptions": int(m.get("ar_exceptions_count", 0) or 0),
        "ic_mismatches": int(m.get("ic_mismatch_count", 0) or 0),
        "accruals_exceptions": int(m.get("accruals_exception_count", 0) or 0),
        "je_exceptions": int(m.get("je_exceptions_count", 0) or 0),
        "flux_exceptions": int(m.get("flux_exceptions_count", 0) or 0),
    }

    referenced_artifacts: Dict[str, str] = {
        k: str(v) for k, v in m.items() if isinstance(k, str) and k.endswith("_artifact") and isinstance(v, str)
    }

    # Severity heuristic: high if gatekeeping blocks close, else medium if any exceptions, else low
    gate_block = bool(m.get("gatekeeping_block_close", False))
    base_severity = "high" if gate_block else ("medium" if any(v > 0 for v in categories.values()) else "low")

    cases: List[Case] = []
    now = datetime.utcnow().isoformat() + "Z"

    idx = 1
    for cat, count in categories.items():
        if count <= 0:
            continue
        ev_uris = [uri for key, uri in referenced_artifacts.items() if cat.split("_")[0] in key]
        title = f"{cat.replace('_', ' ').title()}: {count} items"
        desc = f"Automated detection opened this HITL case for category '{cat}' with {count} exception items in period {state.period}."
        cases.append(
            Case(
                id=_mk_case_id(state.period, cat, idx),
                created_at=now,
                period=state.period,
                entity=state.entity,
                source=cat,
                severity=base_severity,
                title=title,
                description=desc,
                evidence_uris=ev_uris,
            )
        )
        idx += 1

    # If no specific categories but gatekeeping blocked close, open a general case
    if not cases and gate_block:
        ev_uris = list(referenced_artifacts.values())
        cases.append(
            Case(
                id=_mk_case_id(state.period, "gatekeeping", 1),
                created_at=now,
                period=state.period,
                entity=state.entity,
                source="gatekeeping",
                severity="high",
                title="Gatekeeping blocked close",
                description="Gatekeeping risk policy resulted in a block_close=True outcome.",
                evidence_uris=ev_uris,
            )
        )

    out_cases = Path(audit.out_dir) / f"cases_{run_id}.json"
    out_manifest = Path(audit.out_dir) / f"cases_manifest_{run_id}.json"

    cases_payload = [asdict(c) for c in cases]
    manifest_payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "count": len(cases),
        "cases_uri": str(out_cases),
    }

    with out_cases.open("w", encoding="utf-8") as f:
        json.dump(cases_payload, f, indent=2)
    with out_manifest.open("w", encoding="utf-8") as f:
        json.dump(manifest_payload, f, indent=2)

    # Evidence (cases file itself)
    ev = EvidenceRef(type="json", uri=str(out_cases))
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
    det = DeterministicRun(function_name="open_hitl_cases")
    det.params = {"period": state.period, "entity": state.entity}
    det.output_hash = _hash_bytes(json.dumps({"cases": cases_payload, "manifest": manifest_payload}, sort_keys=True).encode("utf-8"))
    state.det_runs.append(det)

    audit.append(
        {
            "type": "deterministic",
            "fn": det.function_name,
            "output_hash": det.output_hash,
            "params": det.params,
            "artifact": str(out_cases),
            "manifest": str(out_manifest),
        }
    )

    state.messages.append(f"[DET] HITL: opened {len(cases)} cases -> {out_cases}")
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="HITL case management"))

    state.metrics.update(
        {
            "hitl_cases_open_count": len(cases),
            "hitl_cases_artifact": str(out_cases),
            "hitl_manifest_artifact": str(out_manifest),
        }
    )

    return state
