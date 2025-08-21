from __future__ import annotations
from ..state import CloseState, MatchResult
from ..console import Console

def node_match(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Transaction Matching")
    data = state["data"]; period = state["period"]; matches=[]
    bank = data["bank"][data["bank"].period==period].copy()
    ar = data["ar"][data["ar"].period==period].copy()
    credits = bank[bank["amount"]>0].copy()
    ar["key"] = ar["amount"].round(2)
    credits["key"] = credits["amount"].round(2)
    merged = ar.merge(credits, on=["entity","key"], how="inner", suffixes=("_ar","_bnk"))
    cleared = merged.drop_duplicates(subset=["invoice_id"])
    residual = len(ar) - cleared["invoice_id"].nunique()
    matches.append(MatchResult(rule_hit="AR_to_Bank_amount", cleared=len(cleared), residual=int(residual)))
    console.line("matching","Matching","rule", auto=True, details=f"AR_to_Bank_amount cleared={len(cleared)} residual={residual}")
    return {**state, "matches": matches}
