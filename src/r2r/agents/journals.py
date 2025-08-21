from __future__ import annotations
from ..state import CloseState, Journal
from ..console import Console
from ..llm.azure import chat

def node_journals(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Journal Entries")
    journals = state.get("journals", [])
    for idx, ent in enumerate(state["entities"]):
        prompt = [
            {"role":"system","content":"Draft one-line JE descriptions for monthly close."},
            {"role":"user","content":f"Entity {ent}. Period {state['period']}. FX revaluation journal. Keep to one sentence."}
        ]
        desc = chat(prompt, temperature=0.2, max_tokens=40)
        j = Journal(
            id=f"J-{state['period'].replace('-','')}-{ent}-0001",
            entity=ent, description=(desc or "FX revaluation"),
            amount=12430.00, currency="EUR",
            status="draft", preparer="fin.preparer",
            links={"lines":[{"account":"6000","amount":12430.00}]}
        )
        journals.append(j)
        console.line("journals","JE","draft", ai=True, details=f"{j.id} amount {j.amount} {j.currency}")
        if idx == 0:
            fee_amt = 250.00
            j2 = Journal(
                id=f"J-{state['period'].replace('-','')}-{ent}-0002",
                entity=ent, description="Bank fee reclass to OPEX",
                amount=fee_amt, currency="USD",
                status="draft", preparer="fin.preparer",
                links={"lines":[{"account":"1000","amount":-fee_amt},{"account":"5100","amount":fee_amt}]}
            )
            journals.append(j2)
            console.line("journals","JE","draft", ai=True, details=f"{j2.id} amount {j2.amount} {j2.currency}")
    return {"journals": journals}
