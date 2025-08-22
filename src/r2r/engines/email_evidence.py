from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, Any, List

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState


def _hash_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def email_evidence_analysis(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic extraction of actionable email evidence:
    - Load supporting/emails.json
    - Filter to items relevant to the period (simple heuristic) and/or requires_action
    - Export summary artifact and append audit/evidence with row-level input_row_ids (email_id)
    """
    data_fp = Path(state.data_path) / "supporting" / "emails.json"
    msgs: List[str] = []

    if not data_fp.exists():
        msgs.append("[DET] Email evidence: no supporting emails.json; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Email evidence (skipped)"))
        return state

    emails: List[Dict[str, Any]] = json.loads(data_fp.read_text(encoding="utf-8"))

    period = state.period  # YYYY-MM

    def is_relevant(e: Dict[str, Any]) -> bool:
        ts = str(e.get("timestamp", ""))
        # Include emails in current period or next-day of month-end for cutoff issues
        return ts.startswith(period) or ts.startswith(_next_day_of_period(period)) or bool(e.get("requires_action"))

    relevant = [e for e in emails if is_relevant(e)]

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"email_evidence_{run_id}.json"

    summary = {
        "total": len(emails),
        "relevant": len(relevant),
        "requires_action": sum(1 for e in relevant if e.get("requires_action")),
        "by_category": {},
    }

    cat_counts: Dict[str, int] = {}
    for e in relevant:
        cat = str(e.get("category") or "Uncategorized")
        cat_counts[cat] = cat_counts.get(cat, 0) + 1
    summary["by_category"] = dict(sorted(cat_counts.items(), key=lambda kv: (-kv[1], kv[0])))

    payload = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": period,
        "entity_scope": state.entity,
        "items": relevant,
        "summary": summary,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence + deterministic
    ev_ids = [str(e.get("email_id")) for e in relevant if e.get("email_id")]
    ev = EvidenceRef(type="json", uri=str(data_fp), input_row_ids=ev_ids or None)
    state.evidence.append(ev)

    det = DeterministicRun(function_name="email_evidence")
    det.params = {"period": period, "entity": state.entity}
    det.output_hash = _hash_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
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

    # Messages & tags
    msgs.append(
        f"[DET] Email evidence: relevant={summary['relevant']} requires_action={summary['requires_action']} -> {out_path}"
    )
    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Email evidence analysis"))

    return state


def _next_day_of_period(period: str) -> str:
    # period YYYY-MM -> next day after month end, approximated by next month 'YYYY-MM' + '-01'
    y, m = map(int, period.split("-"))
    if m == 12:
        return f"{y+1}-01-01"
    return f"{y}-{m+1:02d}-01"
