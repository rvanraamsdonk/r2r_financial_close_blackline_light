from __future__ import annotations
import pandas as pd
from .synth import make_entities, make_coa, make_fx, make_budget, make_gl, make_subledgers, make_bank, make_ic_docs

class DataRepo:
    """In-memory synthetic datasets with deterministic generation."""
    def __init__(self, period:str, prior_period:str|None=None, seed:int=42, n_entities:int=6):
        self.period = period; self.prior_period = prior_period; self.seed = seed
        self.entities = make_entities(n_entities, seed)
        self.coa = make_coa(seed)
        self.fx = make_fx(period, seed)
        self.budget = make_budget(self.entities, self.coa, period, seed)
        self.gl = make_gl(self.entities, self.coa, period, seed)
        self.ar, self.ap = make_subledgers(self.entities, period, seed)
        self.bank = make_bank(self.entities, period, seed)
        self.ic = make_ic_docs(self.entities, period, seed)
        self.gl_prev = make_gl(self.entities, self.coa, prior_period, seed+1) if prior_period else None

    def snapshot(self) -> dict[str, pd.DataFrame]:
        return {
            "entities": self.entities, "coa": self.coa, "fx": self.fx, "budget": self.budget,
            "gl": self.gl, "ar": self.ar, "ap": self.ap, "bank": self.bank, "ic": self.ic,
            "gl_prev": self.gl_prev
        }
