from __future__ import annotations
from ..state import CloseState, HITLCase
from ..console import Console

def node_gatekeeper(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Governance and HITL")
    # Build a fresh HITL queue from current state
    new_queue: list[HITLCase] = []
    # Queue population
    for r in state.get("recs", []):
        if r.status!="certified" and r.risk in ("medium","high"):
            new_queue.append(HITLCase(id=f"H-REC-{r.entity}-{r.account_id}", type="recon_cert", risk=r.risk, payload=r.model_dump()))
    for j in state.get("journals", []):
        new_queue.append(HITLCase(id=f"H-JE-{j.id}", type="journal_post", risk=("high" if abs(j.amount)>=100000 else "medium"), payload=j.model_dump()))
    for ic in state.get("ic", []):
        if ic.status=="net_ready":
            new_queue.append(HITLCase(id=f"H-IC-{ic.doc_id}", type="ic_settlement", risk="high", payload=ic.model_dump()))
    # Approvals (produce approved copies)
    approved_queue: list[HITLCase] = []
    for c in new_queue:
        c2 = c.model_copy(update={"maker":"fin.preparer","checker":"fin.controller","status":"approved"})
        approved_queue.append(c2)
        console.line("governance","Gatekeeper","approval", hitl=True, details=f"{c2.id} {c2.type} {c2.status}")
    # Posting of approved JEs (non-destructive: copy GL and journals)
    updated: CloseState = {"hitl_queue": approved_queue}
    data = state.get("data")
    gl = None
    if data is not None:
        gl = data.get("gl")
    gl_new = None
    journals_new = list(state.get("journals", []))
    if gl is not None:
        gl_new = gl.copy()
        approved_ids = {c.id.replace("H-JE-","") for c in approved_queue if c.type=="journal_post" and c.status=="approved"}
        journals_new = []
        for j in state.get("journals", []):
            if j.id in approved_ids and j.links and "lines" in j.links and j.status=="draft":
                for ln in j.links["lines"]:
                    acct = ln["account"]; amt = float(ln["amount"])
                    mask = (gl_new.period==state["period"]) & (gl_new.entity==j.entity) & (gl_new.account==acct)
                    if mask.any():
                        gl_new.loc[mask,"balance"] = gl_new.loc[mask,"balance"] + amt
                j2 = j.model_copy(update={"status":"posted"})
                journals_new.append(j2)
                console.line("governance","Gatekeeper","post", det=True, details=f"{j2.id} posted")
            else:
                journals_new.append(j)
    if gl_new is not None and data is not None:
        new_data = dict(data)
        new_data["gl"] = gl_new
        updated["data"] = new_data
        # Only update journals if we actually modified them
        if any(j.status == "posted" for j in journals_new):
            updated["journals"] = journals_new
    # Auto-decertify certified recs impacted by GL changes (use gl_new if available)
    if gl_new is not None:
        new_recs = []
        for r in state.get("recs", []):
            if r.status=="certified" and r.gl_balance_at_cert is not None:
                acct = r.account_id
                if acct == "1000":
                    cur = float(gl_new[(gl_new.period==state["period"]) & (gl_new.entity==r.entity) & (gl_new.account.isin(["1000"]))]["balance"].sum())
                else:
                    cur = float(gl_new[(gl_new.period==state["period"]) & (gl_new.entity==r.entity) & (gl_new.account==acct)]["balance"].sum())
                if abs(cur - r.gl_balance_at_cert) > 0.01:
                    r2 = r.model_copy(update={"status":"decertified"})
                    new_recs.append(r2)
                    console.line("governance","Gatekeeper","decertify", det=True, details=f"{r.entity} acct {acct} balance changed {r.gl_balance_at_cert}->{cur}")
                else:
                    new_recs.append(r)
            else:
                new_recs.append(r)
        updated["recs"] = new_recs
    return updated
