from __future__ import annotations
import pandas as pd
from .synth import make_entities, make_coa, make_fx, make_budget, make_gl, make_subledgers, make_bank, make_ic_docs
from .static_loader import StaticDataRepo

class DataRepo:
    """In-memory datasets - can use static or synthetic data."""
    def __init__(self, period:str, prior_period:str|None=None, seed:int=42, n_entities:int=6, use_static:bool=True):
        self.period = period; self.prior_period = prior_period; self.seed = seed
        
        if use_static:
            # Use static forensic dataset
            static_repo = StaticDataRepo()
            snapshot = static_repo.snapshot()
            self.entities = snapshot["entities"]
            self.coa = snapshot["coa"] 
            self.fx = snapshot["fx"]
            self.budget = snapshot["budget"]
            self.gl = snapshot["gl"]
            self.ar = snapshot["ar"]
            self.ap = snapshot["ap"]
            self.bank = snapshot["bank"]
            self.ic = snapshot["ic"]
            self.gl_prev = snapshot["gl_prev"]
            self.forensic_scenarios = static_repo.get_forensic_scenarios()
        else:
            # Use synthetic data (legacy)
            self.entities = make_entities(n_entities, seed)
            self.coa = make_coa(seed)
            self.fx = make_fx(period, seed)
            self.budget = make_budget(self.entities, self.coa, period, seed)
            self.gl = make_gl(self.entities, self.coa, period, seed)
            self.ar, self.ap = make_subledgers(self.entities, period, seed)
            self.bank = make_bank(self.entities, period, seed)
            self.ic = make_ic_docs(self.entities, period, seed)
            self.gl_prev = make_gl(self.entities, self.coa, prior_period, seed+1) if prior_period else None
            self.forensic_scenarios = {}

    def snapshot(self) -> dict[str, pd.DataFrame]:
        return {
            "entities": self.entities, "coa": self.coa, "fx": self.fx, "budget": self.budget,
            "gl": self.gl, "ar": self.ar, "ap": self.ap, "bank": self.bank, "ic": self.ic,
            "gl_prev": self.gl_prev
        }
