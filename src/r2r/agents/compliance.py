from __future__ import annotations
from ..state import CloseState, AuditEvent
from ..console import Console

def node_compliance(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Compliance Summary")
    events = state.get("events", [])
    events.append(AuditEvent(ts="now", actor="agent:Compliance", action="attestation", details={"period": state["period"]}))
    console.line("governance","Compliance","attest", auto=True, details=f"period {state['period']}")
    return {**state, "events": events}
