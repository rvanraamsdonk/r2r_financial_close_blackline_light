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
        console.line("variance", "Analysis", "complete", auto=True, 
                    details="VARIANCE ANALYSIS | Status: No prior period data available | Analysis: Skipped")
        return {}
    
    prev_period = prev["period"].iloc[0]
    total_analyzed = 0
    material_variances = 0
    
    for ent in state["entities"]:
        for acct in ["3000","5000","5100","6000"]:
            cur = float(gl[(gl.period==period)&(gl.entity==ent)&(gl.account==acct)]["balance"].sum())
            pri = float(prev[(prev.period==prev_period)&(prev.entity==ent)&(prev.account==acct)]["balance"].sum())
            delta = cur - pri
            pct = (abs(delta) / max(1.0, abs(pri))) * 100.0
            band = "revenue" if acct=="3000" else ("expense" if acct in ["5000","5100","6000"] else "default")
            material = abs(delta)>=thresholds[band]["abs"] or pct>=thresholds[band]["pct"]
            
            # Enhanced console output for each account analysis
            account_name = {"3000": "Revenue", "5000": "Operating Expenses", "5100": "Personnel Costs", "6000": "Other Expenses"}.get(acct, acct)
            status_text = "MATERIAL VARIANCE" if material else "WITHIN THRESHOLD"
            
            console.line("variance", "Account Analysis", "complete", auto=True,
                        details=f"VARIANCE ANALYSIS | Entity: {ent} | Account: {acct} ({account_name}) | Current: ${cur:,.0f} | Prior: ${pri:,.0f} | Variance: ${delta:,.0f} ({pct:.1f}%) | Status: {status_text}")
            
            total_analyzed += 1
            
            if material:
                material_variances += 1
                narr = chat([
                    {"role":"system","content":"Explain P&L flux succinctly for controllers."},
                    {"role":"user","content":f"Entity {ent}. Account {acct}. Δ {delta:.0f} ({pct:.1f}%). 1-2 short clauses."}
                ], temperature=0.1, max_tokens=50)
                alerts.append(FluxAlert(entity=ent, account_id=acct, delta_abs=round(delta,2), delta_pct=round(pct,1), material=True, narrative=narr or ""))
                
                console.line("variance", "Material Variance", "detected", ai=True,
                            details=f"MATERIAL VARIANCE ALERT | Entity: {ent} | Account: {acct} ({account_name}) | Variance: ${delta:,.0f} ({pct:.1f}%) | AI Analysis: {narr or 'Analysis unavailable'}")
    
    # Summary analysis
    console.line("variance", "Analysis Summary", "complete", auto=True,
                details=f"VARIANCE ANALYSIS SUMMARY | Accounts Analyzed: {total_analyzed} | Material Variances: {material_variances} | Threshold Compliance: {((total_analyzed - material_variances) / max(1, total_analyzed) * 100):.1f}%")
    
    return {"flux": alerts}
