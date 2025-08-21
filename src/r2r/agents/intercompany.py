from __future__ import annotations
from ..state import CloseState, ICItem
from ..console import Console

def node_intercompany(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Intercompany")
    data = state["data"]; ic_df = data["ic"]; period = state["period"]
    items=[]
    for _,r in ic_df[ic_df.period==period].iterrows():
        status = "balanced" if abs(r.amount_src - r.amount_dst) < 1.0 else "open"
        items.append(ICItem(pair=(r.entity_src, r.entity_dst), doc_id=r.doc_id, amount_src=float(r.amount_src),
                            currency=r.currency, status=status, exceptions=([] if status=="balanced" else ["asymmetry"])))
    by_pair = {}
    for it in items:
        by_pair.setdefault(it.pair, []).append(it)
    for pair, lst in by_pair.items():
        if all(x.status=="balanced" for x in lst):
            for x in lst: x.status = "net_ready"
    ready = sum(1 for x in items if x.status=="net_ready")
    console.line("intercompany","IC","evaluate", auto=True, details=f"net_ready={ready} docs={len(items)}")
    return {**state, "ic": items}
