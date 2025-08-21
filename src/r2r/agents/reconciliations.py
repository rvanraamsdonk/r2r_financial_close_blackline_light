from __future__ import annotations
from ..state import CloseState, ReconResult
from ..console import Console

def _auto_cert(account:str, diff:float, rules:list[dict]) -> tuple[bool,list[str]]:
    hits=[]
    for r in rules:
        if r["name"]=="zero_balance_no_activity" and abs(diff)<1e-6:
            hits.append(r["name"])
        if r["name"]=="subledger_equals_gl_within_threshold":
            th_abs=r.get("threshold_abs",50.0); th_pct=r.get("threshold_pct",0.01)
            if abs(diff)<=th_abs:
                hits.append(r["name"])
    return (len(hits)>0, hits)

def node_reconcile(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Account Reconciliations")
    data = state["data"]; policy = state["policy"]; period = state["period"]
    gl = data["gl"]; ar = data["ar"]; ap = data["ap"]; coa = data["coa"]
    recs=[]
    cash_accts = coa[coa["name"]=="Cash"]["account"].tolist()
    for ent in state["entities"]:
        gl_cash = gl[(gl.period==period)&(gl.entity==ent)&(gl.account.isin(cash_accts))]["balance"].sum()
        bank_total = data["bank"][(data["bank"].period==period)&(data["bank"].entity==ent)]["amount"].sum()
        diff = round(float(gl_cash - bank_total),2)
        ok,hits = _auto_cert("Cash", diff, policy["auto_cert_rules"])
        status = "certified" if ok else "open"
        recs.append(ReconResult(account_id="1000", entity=ent, risk="low", status=status, diff=diff, rule_hits=hits))
        console.line("reconciliations","Recs","evaluate", auto=True, details=f"{ent} Cash diff {diff}")
    for acct,name,df in [("1200","AR", ar), ("2000","AP", ap)]:
        for ent in state["entities"]:
            gl_bal = gl[(gl.period==period)&(gl.entity==ent)&(gl.account==acct)]["balance"].sum()
            sl_sum = df[(df.period==period)&(df.entity==ent)]["amount"].sum()
            diff = round(float(gl_bal - sl_sum),2)
            ok,hits = _auto_cert(name, diff, policy["auto_cert_rules"])
            risk = "medium"
            status = "certified" if ok else "open"
            recs.append(ReconResult(account_id=acct, entity=ent, risk=risk, status=status, diff=diff, rule_hits=hits))
            console.line("reconciliations","Recs","evaluate", auto=True, details=f"{ent} {name} diff {diff}")
    return {**state, "recs": recs}
