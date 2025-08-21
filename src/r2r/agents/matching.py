from __future__ import annotations
from ..state import CloseState, MatchResult
from ..console import Console
from datetime import datetime, timedelta

def node_match(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Transaction Matching")
    data = state["data"]; period = state["period"]; matches=[]
    bank = data["bank"][data["bank"].period==period].copy()
    bank["date"] = bank["date"].apply(lambda x: datetime.fromisoformat(x).date())
    ar = data["ar"][data["ar"].period==period].copy()
    ar["invoice_date"] = ar["invoice_date"].apply(lambda x: datetime.fromisoformat(x).date())

    # 1) 1:1 by exact amount (rounded)
    credits = bank[bank["amount"]>0].copy()
    ar["key"] = ar["amount"].round(2)
    credits["key"] = credits["amount"].round(2)
    merged = ar.merge(credits, on=["entity","key"], how="inner", suffixes=("_ar","_bnk"))
    cleared_1to1 = merged.drop_duplicates(subset=["invoice_id"])
    used_bank_ids = set(cleared_1to1["bank_txn_id"])
    residual_ids = set(ar["invoice_id"]) - set(cleared_1to1["invoice_id"])
    residual = ar[ar["invoice_id"].isin(residual_ids)].copy()

    matches.append(MatchResult(rule_hit="AR_to_Bank_amount", cleared=len(cleared_1to1), residual=int(len(residual))))
    console.line("matching","Matching","rule", det=True, details=f"AR_to_Bank_amount cleared={len(cleared_1to1)} residual={len(residual)}")

    # 2) 1:N sum within date tolerance ±5 days, up to N=3
    DATE_TOL = 5
    TOL_FRAC = 0.005  # 0.5%
    cleared_1N = 0
    credits_remaining = credits[~credits["bank_txn_id"].isin(used_bank_ids)].copy()
    credits_remaining = credits_remaining.sort_values(["entity","date"])
    by_ent = {e: df.copy() for e, df in credits_remaining.groupby("entity")}

    def try_match_sum(cands, target):
        # greedy: try single then pairs then triplets
        cand_vals = list(cands["amount"].values)
        cand_ids = list(cands["bank_txn_id"].values)
        # single
        for i,amt in enumerate(cand_vals):
            if abs(amt - target) <= max(1.0, TOL_FRAC*abs(target)):
                return [cand_ids[i]]
        # pairs
        n=len(cand_vals)
        for i in range(n):
            for j in range(i+1,n):
                s = cand_vals[i] + cand_vals[j]
                if abs(s - target) <= max(1.0, TOL_FRAC*abs(target)):
                    return [cand_ids[i], cand_ids[j]]
        # triplets
        for i in range(n):
            for j in range(i+1,n):
                for k in range(j+1,n):
                    s = cand_vals[i] + cand_vals[j] + cand_vals[k]
                    if abs(s - target) <= max(1.0, TOL_FRAC*abs(target)):
                        return [cand_ids[i], cand_ids[j], cand_ids[k]]
        return []

    used_more = set()
    for _, r in residual.iterrows():
        ent = r["entity"]; inv_dt = r["invoice_date"]; target = float(r["amount"])
        cands = by_ent.get(ent, credits_remaining.iloc[0:0])
        if len(cands)==0: continue
        window = cands[(cands["date"] >= inv_dt - timedelta(days=DATE_TOL)) &
                       (cands["date"] <= inv_dt + timedelta(days=DATE_TOL)) &
                       (~cands["bank_txn_id"].isin(used_more))]
        hit_ids = try_match_sum(window, target)
        if hit_ids:
            used_more.update(hit_ids)
            cleared_1N += 1

    residual_after = len(residual) - cleared_1N
    tags = []
    if residual_after > 0:
        # repeat-exception tagging by amount bucket and aging
        buck = (residual["amount"]//100).astype(int)
        repeats = residual.groupby(["entity", buck]).size().reset_index(name="n")
        if any(repeats["n"]>=2):
            tags.append("repeat_amount_bucket")
        if any(residual["age_days"]>=30):
            tags.append("aged_30_plus")

    matches.append(MatchResult(rule_hit="AR_1toN_date_tolerance", cleared=int(cleared_1N), residual=int(residual_after), repeat_exception_tags=tags))
    console.line("matching","Matching","rule", det=True, details=f"AR_1toN_date_tolerance cleared={cleared_1N} residual={residual_after}")
    return {"matches": matches}
