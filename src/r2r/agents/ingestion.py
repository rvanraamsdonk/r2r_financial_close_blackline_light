from __future__ import annotations
from ..state import CloseState, AuditEvent
from ..console import Console

def node_ingest(state: CloseState, *, data_repo, console: Console) -> CloseState:
    console.banner("Data Ingestion")
    snap = data_repo.snapshot()
    events = state.get("events", [])
    events.append(AuditEvent(ts="now", actor="agent:Ingestion", action="ingest.completed", details={"tables": list(snap.keys())}))
    console.line("ingestion","DataIngestion","load", det=True, details=f"tables={len(snap)}")
    return {"events": events, "entities": list(snap["entities"]["entity"]), "data": snap}
