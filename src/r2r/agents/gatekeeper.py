from __future__ import annotations
from ..state import CloseState, HITLCase
from ..console import Console

def node_gatekeeper(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Governance and HITL")
    queue = state.get("hitl_queue", [])
    for r in state.get("recs", []):
        if r.status!="certified" and r.risk in ("medium","high"):
            queue.append(HITLCase(id=f"H-REC-{r.entity}-{r.account_id}", type="recon_cert", risk=r.risk, payload=r.model_dump()))
    for j in state.get("journals", []):
        queue.append(HITLCase(id=f"H-JE-{j.id}", type="journal_post", risk=("high" if abs(j.amount)>=100000 else "medium"), payload=j.model_dump()))
    for ic in state.get("ic", []):
        if ic.status=="net_ready":
            queue.append(HITLCase(id=f"H-IC-{ic.doc_id}", type="ic_settlement", risk="high", payload=ic.model_dump()))
    for c in queue:
        c.maker = "fin.preparer"; c.checker = "fin.controller"
        c.status = "approved"
        console.line("governance","Gatekeeper","approval", hitl=True, details=f"{c.id} {c.type} {c.status}")
    return {**state, "hitl_queue": queue}
