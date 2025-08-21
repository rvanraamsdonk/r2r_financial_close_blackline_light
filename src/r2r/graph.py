from __future__ import annotations
from langgraph.graph import StateGraph, END
from .state import CloseState
from .console import Console
from .agents.orchestrator import node_orchestrate
from .agents.ingestion import node_ingest
from .agents.reconciliations import node_reconcile
from .agents.matching import node_match
from .agents.smart_matching import node_smart_match
from .agents.forensics import node_forensics
from .agents.scenario_generator import node_generate_scenarios
from .agents.reporting import node_generate_reports
from .agents.journals import node_journals
from .agents.variance import node_flux
from .agents.intercompany import node_intercompany
from .agents.gatekeeper import node_gatekeeper
from .agents.compliance import node_compliance
from .agents.audit import node_audit

def build_graph(*, data_repo, policy):
    console = Console()
    graph = StateGraph(CloseState)

    graph.add_node("orchestrate", lambda s: node_orchestrate(s, console=console))
    graph.add_node("ingest", lambda s: node_ingest(s, data_repo=data_repo, console=console))
    graph.add_node("scenarios", lambda s: node_generate_scenarios(s, console=console))
    graph.add_node("reconcile", lambda s: node_reconcile(s, console=console))
    graph.add_node("match", lambda s: node_match(s, console=console))
    graph.add_node("smart_match", lambda s: node_smart_match(s, console=console))
    graph.add_node("forensics", lambda s: node_forensics(s, console=console))
    graph.add_node("journals", lambda s: node_journals(s, console=console))
    graph.add_node("variance", lambda s: node_flux(s, console=console))
    graph.add_node("intercompany", lambda s: node_intercompany(s, console=console))
    graph.add_node("reporting", lambda s: node_generate_reports(s, console=console))
    graph.add_node("gatekeeper", lambda s: node_gatekeeper(s, console=console))
    graph.add_node("compliance", lambda s: node_compliance(s, console=console))
    graph.add_node("audit", lambda s: node_audit(s, console=console))

    graph.set_entry_point("orchestrate")
    graph.add_edge("orchestrate","ingest")
    graph.add_edge("ingest","scenarios")
    graph.add_edge("scenarios","reconcile")
    graph.add_edge("scenarios","match")
    graph.add_edge("scenarios","variance")
    graph.add_edge("scenarios","intercompany")
    graph.add_edge("reconcile","smart_match")
    graph.add_edge("match","smart_match")
    graph.add_edge("smart_match","forensics")
    graph.add_edge("forensics","journals")
    graph.add_edge("forensics","reporting")
    graph.add_edge("variance","gatekeeper")
    graph.add_edge("intercompany","gatekeeper")
    graph.add_edge("journals","gatekeeper")
    graph.add_edge("reporting","gatekeeper")
    graph.add_edge("gatekeeper","compliance")
    graph.add_edge("compliance","audit")
    graph.add_edge("audit", END)

    app = graph.compile()
    init: CloseState = {"period":"2025-08","policy":policy}
    return app, console, init
