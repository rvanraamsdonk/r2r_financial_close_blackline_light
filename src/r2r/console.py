from __future__ import annotations
from typing import Optional

class Console:
    def __init__(self): self.step = 0
    def line(self, stage:str, agent:str, action:str, *, ai=False, hitl=False, auto=False, details:Optional[str]=None):
        self.step += 1
        markers = []
        if ai: markers.append("AI")
        if hitl: markers.append("HITL")
        if auto: markers.append("AUTO")
        m = " ".join(markers) if markers else "—"
        d = f" | details={details}" if details else ""
        print(f"STEP {self.step:02d} | {stage.upper()} | AGENT={agent} | {m} | action={action}{d}")

    def banner(self, title:str):
        print("="*80); print(title.upper()); print("="*80)
