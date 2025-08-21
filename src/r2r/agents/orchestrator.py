from __future__ import annotations
from datetime import date, timedelta
from ..state import CloseState, Task
from ..console import Console

def node_orchestrate(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Period Close Orchestration")
    today = date.today()
    tasks = [
        Task(id="T-INGEST", stage="INGESTION", owner="system", sla=today),
        Task(id="T-RECS", stage="RECONCILIATIONS", owner="fin.preparer", sla=today+timedelta(days=2), predecessors=["T-INGEST"]),
        Task(id="T-MATCH", stage="MATCHING", owner="fin.preparer", sla=today+timedelta(days=2), predecessors=["T-INGEST"]),
        Task(id="T-SMART-MATCH", stage="SMART_MATCHING", owner="fin.preparer", sla=today+timedelta(days=2), predecessors=["T-MATCH"]),
        Task(id="T-FORENSICS", stage="FORENSICS", owner="fin.analyst", sla=today+timedelta(days=2), predecessors=["T-RECS","T-SMART-MATCH"]),
        Task(id="T-JE", stage="JOURNALS", owner="fin.preparer", sla=today+timedelta(days=3), predecessors=["T-RECS","T-SMART-MATCH"]),
        Task(id="T-FLUX", stage="VARIANCE", owner="fpna.analyst", sla=today+timedelta(days=3), predecessors=["T-INGEST"]),
        Task(id="T-IC", stage="INTERCOMPANY", owner="fin.ic", sla=today+timedelta(days=3), predecessors=["T-INGEST"]),
        Task(id="T-REPORTS", stage="REPORTING", owner="fin.controller", sla=today+timedelta(days=3), predecessors=["T-FORENSICS","T-JE"]),
        Task(id="T-COMP", stage="GOVERNANCE", owner="fin.controller", sla=today+timedelta(days=4), predecessors=["T-REPORTS","T-FLUX","T-IC"]),
    ]
    console.line("orchestration","Orchestrator","plan", det=True, details=f"{len(tasks)} tasks created")
    return {"tasks": tasks}
