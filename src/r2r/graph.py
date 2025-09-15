from __future__ import annotations

from typing import TypedDict
from langgraph.graph import StateGraph, END

from .state import R2RState
from .audit import AuditLogger
from .engines import (
    period_init,
    validate_ingestion,
    compute_fx_coverage,
    fx_translation,
    tb_checks,
    accruals_check,
    flux_analysis,
    email_evidence_analysis,
    bank_reconciliation,
    intercompany_reconciliation,
    ap_reconciliation,
    ar_reconciliation,
    je_lifecycle,
    gatekeeping_aggregate,
    open_hitl_cases,
    controls_mapping,
    close_reporting,
)
from .engines.auto_journal_engine import auto_journal_creation
from .metrics import compute_metrics
from .ai.comprehensive_analysis import ai_comprehensive_analysis


class GraphState(TypedDict):
    obj: R2RState
    audit: AuditLogger


def _node_period_init(state: GraphState) -> GraphState:
    s = period_init(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_validate(state: GraphState) -> GraphState:
    s = validate_ingestion(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_fx(state: GraphState) -> GraphState:
    s = compute_fx_coverage(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_fx(state: GraphState) -> GraphState:
    # Deprecated: Inline AI removed from execution graph. Kept as no-op for backward compatibility.
    return state


def _node_ai_validation(state: GraphState) -> GraphState:
    s = ai_validation_root_causes(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_fx_translation(state: GraphState) -> GraphState:
    s = fx_translation(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_tb(state: GraphState) -> GraphState:
    s = tb_checks(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_bank_recon(state: GraphState) -> GraphState:
    s = bank_reconciliation(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_bank(state: GraphState) -> GraphState:
    s = ai_bank_rationales(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ap_recon(state: GraphState) -> GraphState:
    s = ap_reconciliation(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ar_recon(state: GraphState) -> GraphState:
    s = ar_reconciliation(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_ap_ar(state: GraphState) -> GraphState:
    s = ai_ap_ar_suggestions(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ic_recon(state: GraphState) -> GraphState:
    s = intercompany_reconciliation(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_ic(state: GraphState) -> GraphState:
    s = ai_ic_match_proposals(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_accruals(state: GraphState) -> GraphState:
    s = accruals_check(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_je_lifecycle(state: GraphState) -> GraphState:
    s = je_lifecycle(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_accruals(state: GraphState) -> GraphState:
    s = ai_accruals_narratives(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_flux_analysis(state: GraphState) -> GraphState:
    s = flux_analysis(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_flux(state: GraphState) -> GraphState:
    s = ai_flux_narratives(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_email_evidence(state: GraphState) -> GraphState:
    s = email_evidence_analysis(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_gatekeeping(state: GraphState) -> GraphState:
    s = gatekeeping_aggregate(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_gatekeeping(state: GraphState) -> GraphState:
    s = ai_gatekeeping_rationales(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_hitl(state: GraphState) -> GraphState:
    s = open_hitl_cases(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_hitl(state: GraphState) -> GraphState:
    s = ai_hitl_case_summaries(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_metrics(state: GraphState) -> GraphState:
    s = compute_metrics(state["obj"])
    return {**state, "obj": s}


def _node_controls_mapping(state: GraphState) -> GraphState:
    s = controls_mapping(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_controls(state: GraphState) -> GraphState:
    s = ai_controls_owner_summaries(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_close_reporting(state: GraphState) -> GraphState:
    s = close_reporting(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_ai_comprehensive_analysis(state: GraphState) -> GraphState:
    s = ai_comprehensive_analysis(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_auto_journals(state: GraphState) -> GraphState:
    s = auto_journal_creation(state["obj"], state["audit"])
    return {**state, "obj": s}

def build_graph() -> StateGraph:
    g = StateGraph(GraphState)  # type: ignore[arg-type]
    g.add_node("period_init", _node_period_init)
    g.add_node("validate", _node_validate)
    g.add_node("fx", _node_fx)
    g.add_node("fx_translation", _node_fx_translation)
    g.add_node("tb", _node_tb)
    g.add_node("bank_recon", _node_bank_recon)
    g.add_node("ap_recon", _node_ap_recon)
    g.add_node("ar_recon", _node_ar_recon)
    g.add_node("ic_recon", _node_ic_recon)
    g.add_node("accruals", _node_accruals)
    g.add_node("je_lifecycle", _node_je_lifecycle)
    g.add_node("flux_analysis", _node_flux_analysis)
    g.add_node("email_evidence", _node_email_evidence)
    g.add_node("gatekeeping", _node_gatekeeping)
    g.add_node("hitl", _node_hitl)
    g.add_node("metrics", _node_metrics)
    g.add_node("controls_mapping", _node_controls_mapping)
    g.add_node("auto_journals", _node_auto_journals)
    g.add_node("close_reporting", _node_close_reporting)
    g.add_node("ai_comprehensive_analysis", _node_ai_comprehensive_analysis)

    g.set_entry_point("period_init")
    g.add_edge("period_init", "validate")
    g.add_edge("validate", "fx")
    g.add_edge("fx", "fx_translation")
    g.add_edge("fx_translation", "tb")
    g.add_edge("tb", "bank_recon")
    g.add_edge("bank_recon", "ap_recon")
    g.add_edge("ap_recon", "ar_recon")
    g.add_edge("ar_recon", "ic_recon")
    g.add_edge("ic_recon", "accruals")
    g.add_edge("accruals", "je_lifecycle")
    g.add_edge("je_lifecycle", "flux_analysis")
    g.add_edge("flux_analysis", "email_evidence")
    # Tactical Change: Run auto-journals BEFORE gatekeeping to allow the gatekeeper
    # to make a decision on the post-adjustment state of the books.
    g.add_edge("email_evidence", "auto_journals")
    g.add_edge("auto_journals", "gatekeeping")
    # Preliminary gatekeeping only - no AI during execution
    g.add_edge("gatekeeping", "hitl")
    g.add_edge("hitl", "metrics")
    g.add_edge("metrics", "controls_mapping")
    g.add_edge("controls_mapping", "close_reporting")
    # All AI analysis moved to post-run
    g.add_edge("close_reporting", "ai_comprehensive_analysis")
    g.add_edge("ai_comprehensive_analysis", END)
    return g
