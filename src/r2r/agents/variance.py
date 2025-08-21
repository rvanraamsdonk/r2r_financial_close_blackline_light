from __future__ import annotations
from ..state import CloseState, FluxAlert
from ..console import Console
from ..llm.azure import chat

def node_flux(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Variance Analysis")
    data = state["data"]; period = state["period"]; prev = data.get("gl_prev")
    gl = data["gl"]; thresholds = state["policy"]["flux_thresholds"]
    alerts=[]
    if prev is None:
        return state
    prev_period = prev["period"].iloc[0]
    for ent in state["entities"]:
        for acct in ["3000","5000","5100","6000"]:
            cur = float(gl[(gl.period==period)&(gl.entity==ent)&(gl.account==acct)]["balance"].sum())
            pri = float(prev[(prev.period==prev_period)&(prev.entity==ent)&(prev.account==acct)]["balance"].sum())
            delta = cur - pri
            pct = (abs(delta) / max(1.0, abs(pri))) * 100.0
            band = "revenue" if acct=="3000" else ("expense" if acct in ["5000","5100","6000"] else "default")
            material = abs(delta)>=thresholds[band]["abs"] or pct>=thresholds[band]["pct"]
            if material:
                alert = FluxAlert(entity=ent, account_id=acct, delta_abs=round(delta,2), delta_pct=round(pct,1), material=True)
                narr = chat([
                    {"role":"system","content":"Explain P&L flux succinctly for controllers."},
                    {"role":"user","content":f"Entity {ent}. Account {acct}. Δ {delta:.0f} ({pct:.1f}%). 1-2 short clauses."}
                ], temperature=0.1, max_tokens=50)
                alert.narrative = narr or ""
                alerts.append(alert)
                console.line("variance","Variance","alert", ai=True, details=f"{ent} acct {acct} Δ={delta:.0f} ({pct:.1f}%)")
    return {**state, "flux": alerts}
