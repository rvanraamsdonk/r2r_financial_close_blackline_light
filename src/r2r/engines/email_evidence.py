from __future__ import annotations

import json
import re
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState
from ..ai.modules import _invoke_ai


def _hash_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def email_evidence_analysis(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    AI-powered email evidence analysis:
    - Load supporting/emails.json (without hardcoded transaction links)
    - Use AI to analyze email content and semantically match to transaction data
    - Generate confidence-scored linkages between emails and transactions
    - Export enhanced evidence with AI-discovered connections
    """
    data_fp = Path(state.data_path) / "supporting" / "emails.json"
    msgs: List[str] = []

    if not data_fp.exists():
        msgs.append("[DET] Email evidence: no supporting emails.json; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Email evidence (skipped)"))
        return state

    email_data = json.loads(data_fp.read_text(encoding="utf-8"))
    emails: List[Dict[str, Any]] = email_data.get("items", [])

    period = state.period  # YYYY-MM

    def is_relevant(e: Dict[str, Any]) -> bool:
        ts = str(e.get("timestamp", ""))
        # Include emails in current period or next-day of month-end for cutoff issues
        return ts.startswith(period) or ts.startswith(_next_day_of_period(period)) or bool(e.get("requires_action"))

    relevant = [e for e in emails if is_relevant(e)]
    
    # AI-powered transaction linking
    enhanced_emails = []
    for email in relevant:
        enhanced_email = _analyze_email_with_ai(email, state, audit, data_fp)
        enhanced_emails.append(enhanced_email)

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
        "items": enhanced_emails,
        "summary": summary,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence + AI processing
    ev_ids = [str(e.get("email_id")) for e in enhanced_emails if e.get("email_id")]
    ev = EvidenceRef(type="json", uri=str(data_fp), input_row_ids=ev_ids or None)
    state.evidence.append(ev)

    det = DeterministicRun(function_name="email_evidence_ai")
    det.params = {"period": period, "entity": state.entity, "ai_enhanced": True}
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
    total_matches = sum(len(e.get("ai_transaction_matches", [])) for e in enhanced_emails)
    msgs.append(
        f"[AI] Email evidence: relevant={summary['relevant']} ai_matches={total_matches} -> {out_path}"
    )
    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.AI, rationale="AI-powered email evidence analysis"))

    return state


def _next_day_of_period(period: str) -> str:
    # period YYYY-MM -> next day after month end, approximated by next month 'YYYY-MM' + '-01'
    y, m = map(int, period.split("-"))
    if m == 12:
        return f"{y+1}-01-01"
    return f"{y}-{m+1:02d}-01"


def _analyze_email_with_ai(email: Dict[str, Any], state: R2RState, audit: AuditLogger, source_file_path: Path) -> Dict[str, Any]:
    """
    Use AI to analyze email content and find semantic matches to transaction data
    """
    # Load available transaction data from state artifacts
    transaction_data = _load_transaction_data(state)
    
    if not transaction_data:
        # No transaction data available, return email as-is
        enhanced = email.copy()
        enhanced["source_evidence"] = {"uri": str(source_file_path), "id": email.get("email_id")}
        enhanced["ai_transaction_matches"] = []
        enhanced["ai_analysis"] = {"status": "no_transaction_data", "confidence": 0.0}
        return enhanced
    
    # Prepare AI context
    template_path = Path(__file__).parent.parent / "ai" / "templates" / "email_analysis.md"
    
    try:
        context = {
            "email": email,
            "transaction_data": transaction_data,
            "period": state.period
        }
        
        # Invoke AI analysis
        ai_result = _invoke_ai(
            kind="email_analysis",
            template_name="email_analysis.md",
            context=context,
            payload={}
        )
        
        # Parse AI response - ai_result is a dict from _invoke_ai
        analysis = ai_result  # _invoke_ai returns the parsed JSON directly
        
        # Enhance email with AI findings
        enhanced = email.copy()
        enhanced["source_evidence"] = {"uri": str(source_file_path), "id": email.get("email_id")}
        enhanced["ai_transaction_matches"] = analysis.get("transaction_matches", [])
        enhanced["ai_extracted_info"] = analysis.get("extracted_info", {})
        enhanced["ai_forensic_indicators"] = analysis.get("forensic_indicators", [])
        enhanced["ai_analysis"] = {
            "status": "completed",
            "confidence": analysis.get("overall_confidence", 0.0),
            "model": "gpt-4o-mini"
        }
        
        return enhanced
        
    except Exception as e:
        # Fallback on AI failure
        enhanced = email.copy()
        enhanced["source_evidence"] = {"uri": str(source_file_path), "id": email.get("email_id")}
        enhanced["ai_transaction_matches"] = []
        enhanced["ai_analysis"] = {"status": f"ai_error: {str(e)}", "confidence": 0.0}
        return enhanced


def _load_transaction_data(state: R2RState) -> Dict[str, List[Dict[str, Any]]]:
    """
    Load transaction data from various modules for AI matching
    """
    transaction_data = {}
    
    # Check for existing artifacts in state
    out_dir = Path(state.data_path).parent / "out"
    
    # Find latest run directory
    run_dirs = [d for d in out_dir.glob("run_*") if d.is_dir()]
    if not run_dirs:
        return {}
    
    latest_run = max(run_dirs, key=lambda x: x.name)
    
    # Load transaction data from various modules
    modules = {
        "ap_reconciliation": "bill_id",
        "ar_reconciliation": "invoice_id", 
        "bank_reconciliation": "bank_txn_id",
        "intercompany_reconciliation": "doc_id"
    }
    
    for module, id_field in modules.items():
        run_timestamp = latest_run.name.replace('run_', '')
        artifact_path = latest_run / f"{module}_run_{run_timestamp}.json"
        if artifact_path.exists():
            try:
                with artifact_path.open() as f:
                    data = json.load(f)
                    
                # Extract transaction info for AI matching
                transactions = []
                items = data.get("exceptions", data.get("items", []))
                for item in items:
                    if isinstance(item, dict):
                        txn = {
                            "id": item.get(id_field, ""),
                            "amount": item.get("amount_usd", item.get("amount", "")),
                            "counterparty": item.get("vendor_name", item.get("customer_name", item.get("description", ""))),
                            "date": item.get("bill_date", item.get("invoice_date", item.get("date", item.get("transaction_date", "")))),
                            "description": item.get("notes", item.get("description", ""))
                        }
                        if txn["id"]:  # Only include if has valid ID
                            transactions.append(txn)
                
                if transactions:
                    transaction_data[module] = transactions[:10]  # Limit for AI context
                    
            except Exception:
                continue
    
    return transaction_data
