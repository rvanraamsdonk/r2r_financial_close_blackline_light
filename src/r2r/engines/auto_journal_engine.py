"""
Auto Journal Creation Engine - Automatically creates journal entries for immaterial differences
"""

from __future__ import annotations

import json
from .. import utils
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState
from ..je.engine import JEEngine
from ..je.models import JEStatus


def _hash_bytes(data: bytes) -> str:
    return sha256(data).hexdigest()


def auto_journal_creation(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Auto Journal Creation Engine:
    - Analyze exceptions from all modules
    - Create journal entries for immaterial differences within thresholds
    - Generate AI rationale for each auto-created journal
    - Track auto-journal metrics and confidence scores
    """
    
    je_engine = JEEngine()
    auto_journals = []
    total_auto_amount = 0.0
    
    # Get materiality thresholds
    materiality_thresholds = state.metrics.get("materiality_thresholds_usd", {})
    default_threshold = 5000  # $5K default for auto-journal creation
    
    # Process FX translation differences
    fx_data = _load_fx_data_for_auto_je(state)
    for fx_item in fx_data:
        diff_usd = abs(fx_item.get("diff_usd", 0.0))
        entity = fx_item.get("entity", "")
        threshold = materiality_thresholds.get(entity, default_threshold)
        
        if 0 < diff_usd <= threshold:  # Within auto-journal threshold
            try:
                proposal = je_engine.propose_je(
                    module="FX",
                    scenario="translation_adjustment", 
                    source_data=fx_item,
                    period=state.period,
                    entity=entity,
                    user_id="AI_AUTO_JOURNAL"
                )
                
                if proposal:
                    # Auto-approve immaterial differences
                    proposal.status = JEStatus.APPROVED
                    proposal.approved_by = "AI_AUTO_JOURNAL"
                    proposal.approved_at = utils.now_iso_z()
                    proposal.comments = f"Auto-approved: ${diff_usd:,.2f} below materiality threshold (${threshold:,.2f})"
                    
                    auto_journals.append({
                        "je_id": proposal.id,
                        "module": "FX",
                        "scenario": "translation_adjustment",
                        "entity": entity,
                        "amount_usd": diff_usd,
                        "description": proposal.description,
                        "lines": [
                            {
                                "account": line.account,
                                "description": line.description,
                                "debit": line.debit,
                                "credit": line.credit,
                                "entity": line.entity,
                                "currency": line.currency
                            } for line in proposal.lines
                        ],
                        "ai_rationale": f"Auto-created journal for FX translation difference of ${diff_usd:,.2f}. Amount is below materiality threshold and represents routine currency translation adjustment.",
                        "confidence_score": 0.95,
                        "source_data": fx_item
                    })
                    total_auto_amount += diff_usd
                    
            except Exception as e:
                # Log but don't fail the entire process
                state.messages.append(f"[AUTO-JE] Failed to create FX journal for {entity}: {e}")
    
    # Process Flux variances for accrual adjustments
    flux_data = _load_flux_data_for_auto_je(state)
    for flux_item in flux_data:
        var_amount = abs(flux_item.get("var_vs_budget", 0.0))
        entity = flux_item.get("entity", "")
        threshold = materiality_thresholds.get(entity, default_threshold)
        
        if 0 < var_amount <= threshold and flux_item.get("var_vs_budget", 0.0) > 0:  # Over budget, needs accrual
            try:
                proposal = je_engine.propose_je(
                    module="Flux",
                    scenario="accrual_adjustment",
                    source_data=flux_item,
                    period=state.period,
                    entity=entity,
                    user_id="AI_AUTO_JOURNAL"
                )
                
                if proposal:
                    proposal.status = JEStatus.APPROVED
                    proposal.approved_by = "AI_AUTO_JOURNAL"
                    proposal.approved_at = utils.now_iso_z()
                    proposal.comments = f"Auto-approved: ${var_amount:,.2f} budget variance accrual below materiality"
                    
                    auto_journals.append({
                        "je_id": proposal.id,
                        "module": "Flux",
                        "scenario": "accrual_adjustment",
                        "entity": entity,
                        "amount_usd": var_amount,
                        "description": proposal.description,
                        "lines": [
                            {
                                "account": line.account,
                                "description": line.description,
                                "debit": line.debit,
                                "credit": line.credit,
                                "entity": line.entity,
                                "currency": line.currency or "USD"
                            } for line in proposal.lines
                        ],
                        "ai_rationale": f"Auto-created accrual adjustment for budget variance of ${var_amount:,.2f}. Over-budget amount requires accrual but is below materiality threshold for manual review.",
                        "confidence_score": 0.92,
                        "source_data": flux_item
                    })
                    total_auto_amount += var_amount
                    
            except Exception as e:
                state.messages.append(f"[AUTO-JE] Failed to create Flux journal for {entity}: {e}")
    
    # Build output artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"auto_journals_{run_id}.json"
    
    payload = {
        "generated_at": utils.now_iso_z(),
        "period": state.period,
        "entity_scope": state.entity,
        "auto_journals": auto_journals,
        "summary": {
            "total_count": len(auto_journals),
            "total_amount_usd": round(total_auto_amount, 2),
            "by_module": {
                "FX": len([j for j in auto_journals if j["module"] == "FX"]),
                "Flux": len([j for j in auto_journals if j["module"] == "Flux"])
            },
            "average_confidence": round(sum(j["confidence_score"] for j in auto_journals) / len(auto_journals), 3) if auto_journals else 0.0
        },
        "materiality_thresholds": materiality_thresholds,
        "auto_journal_threshold": default_threshold
    }
    
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    
    # Evidence and deterministic run
    det = DeterministicRun(function_name="auto_journal_creation")
    det.params = {"period": state.period, "entity": state.entity}
    det.output_hash = _hash_bytes(json.dumps(payload, sort_keys=True).encode("utf-8"))
    state.det_runs.append(det)
    
    audit.append({
        "type": "deterministic",
        "fn": det.function_name,
        "output_hash": det.output_hash,
        "params": det.params,
        "artifact": str(out_path),
    })
    
    # Messages, tags, metrics
    if auto_journals:
        state.messages.append(
            f"[AUTO-JE] Created {len(auto_journals)} auto-journals totaling ${total_auto_amount:,.2f} -> {out_path}"
        )
    else:
        state.messages.append("[AUTO-JE] No auto-journals created - all differences above threshold or zero")
    
    state.tags.append(
        OutputTag(method_type=MethodType.DET, rationale="Auto journal creation for immaterial differences")
    )
    
    state.metrics.update({
        "auto_journals_count": len(auto_journals),
        "auto_journals_total_usd": round(total_auto_amount, 2),
        "auto_journals_by_module": payload["summary"]["by_module"],
        "auto_journals_avg_confidence": payload["summary"]["average_confidence"],
        "auto_journals_artifact": str(out_path),
    })
    
    return state


def _load_fx_data_for_auto_je(state: R2RState) -> List[Dict[str, Any]]:
    """Load FX translation data for auto-journal analysis"""
    try:
        fx_artifact = state.metrics.get("fx_translation_artifact")
        if not fx_artifact or not Path(fx_artifact).exists():
            return []
        
        with open(fx_artifact, "r") as f:
            fx_data = json.load(f)
        
        # Return rows with non-zero differences
        return [row for row in fx_data.get("rows", []) if abs(row.get("diff_usd", 0.0)) > 0]
    
    except Exception:
        return []


def _load_flux_data_for_auto_je(state: R2RState) -> List[Dict[str, Any]]:
    """Load flux analysis data for auto-journal analysis"""
    try:
        flux_artifact = state.metrics.get("flux_analysis_artifact")
        if not flux_artifact or not Path(flux_artifact).exists():
            return []
        
        with open(flux_artifact, "r") as f:
            flux_data = json.load(f)
        
        # Return rows with significant budget variances
        return [row for row in flux_data.get("rows", []) if abs(row.get("var_vs_budget", 0.0)) > 0]
    
    except Exception:
        return []
