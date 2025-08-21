from __future__ import annotations
from ..state import CloseState, Journal
from ..console import Console
from ..llm.azure import chat

def node_journals(state: CloseState, *, console: Console) -> CloseState:
    console.banner("Journal Entries")
    journals = state.get("journals", [])
    for ent in state["entities"]:
        prompt = [
            {"role":"system","content":"Draft one-line JE descriptions for monthly close."},
            {"role":"user","content":f"Entity {ent}. Period {state['period']}. FX revaluation journal. Keep to one sentence."}
        ]
        desc = chat(prompt, temperature=0.2, max_tokens=40)
        j = Journal(
            id=f"J-{state['period'].replace('-','')}-{ent}-0001",
            entity=ent, description=(desc or "FX revaluation"),
            amount=12430.00, currency="EUR",
            status="draft", preparer="fin.preparer"
        )
        journals.append(j)
        console.line("journals","JE","draft", ai=True, details=f"{j.id} amount {j.amount} {j.currency}")
    return {**state, "journals": journals}
