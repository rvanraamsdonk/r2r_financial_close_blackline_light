from __future__ import annotations
from ..state import CloseState
from ..console import Console

def node_audit(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Audit Trail")
    console.line("governance","AuditLogger","finalize", det=True, details=f"events={len(state.get('events',[]))}")
    return {}
