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
    tb_diagnostics,
    accruals_check,
    email_evidence_analysis,
)
from .metrics import compute_metrics
from .ai import ai_narrative_for_fx


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
    s = state["obj"]
    if s.ai_mode != "off":
        facts = {
            "currencies": sorted(s.fx_df["currency"].unique().tolist()) if s.fx_df is not None else [],
            "coverage_ok": s.metrics.get("fx_coverage_ok"),
        }
        payload = ai_narrative_for_fx(
            policy={"period": s.period}, facts=facts, allow=False if s.ai_mode == "strict" and not s.show_prompts else True
        )
        s.prompt_runs.append(payload["prompt_run"])  # visible provenance
        s.tags.append(payload["tag"])  # [AI]
        s.messages.append(f"[AI] {payload['text']}")
    return {**state, "obj": s}


def _node_fx_translation(state: GraphState) -> GraphState:
    s = fx_translation(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_tb(state: GraphState) -> GraphState:
    s = tb_checks(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_tb_diag(state: GraphState) -> GraphState:
    s = tb_diagnostics(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_accruals(state: GraphState) -> GraphState:
    s = accruals_check(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_email_evidence(state: GraphState) -> GraphState:
    s = email_evidence_analysis(state["obj"], state["audit"])
    return {**state, "obj": s}


def _node_metrics(state: GraphState) -> GraphState:
    s = compute_metrics(state["obj"])
    return {**state, "obj": s}


def build_graph() -> StateGraph:
    g = StateGraph(GraphState)  # type: ignore[arg-type]
    g.add_node("period_init", _node_period_init)
    g.add_node("validate", _node_validate)
    g.add_node("fx", _node_fx)
    g.add_node("ai_fx", _node_ai_fx)
    g.add_node("fx_translation", _node_fx_translation)
    g.add_node("tb", _node_tb)
    g.add_node("tb_diag", _node_tb_diag)
    g.add_node("accruals", _node_accruals)
    g.add_node("email_evidence", _node_email_evidence)
    g.add_node("metrics", _node_metrics)

    g.set_entry_point("period_init")
    g.add_edge("period_init", "validate")
    g.add_edge("validate", "fx")
    g.add_edge("fx", "ai_fx")
    g.add_edge("ai_fx", "fx_translation")
    g.add_edge("fx_translation", "tb")
    g.add_edge("tb", "tb_diag")
    g.add_edge("tb_diag", "accruals")
    g.add_edge("accruals", "email_evidence")
    g.add_edge("email_evidence", "metrics")
    g.add_edge("metrics", END)
    return g
