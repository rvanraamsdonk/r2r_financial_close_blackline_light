"""
Builder utilities for creating test objects.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from src.r2r.state import R2RState


class StateBuilder:
    """Builder for R2RState objects in tests."""
    
    def __init__(self, repo_root: Path, temp_dir: Path):
        self.repo_root = repo_root
        self.temp_dir = temp_dir
        self._period = "2025-08"
        self._prior = "2025-07"
        self._entity = "TEST_ENT"
        self._ai_mode = "off"
        self._show_prompts = False
        self._save_evidence = False
        self._entities_df = None
        self._coa_df = None
        self._tb_df = None
        self._fx_df = None
        self._metrics = {}
    
    def with_period(self, period: str) -> "StateBuilder":
        self._period = period
        return self
    
    def with_prior(self, prior: str) -> "StateBuilder":
        self._prior = prior
        return self
    
    def with_entity(self, entity: str) -> "StateBuilder":
        self._entity = entity
        return self
    
    def with_ai_mode(self, ai_mode: str) -> "StateBuilder":
        self._ai_mode = ai_mode
        return self
    
    def with_show_prompts(self, show_prompts: bool = True) -> "StateBuilder":
        self._show_prompts = show_prompts
        return self
    
    def with_save_evidence(self, save_evidence: bool = True) -> "StateBuilder":
        self._save_evidence = save_evidence
        return self
    
    def with_entities_df(self, df: pd.DataFrame) -> "StateBuilder":
        self._entities_df = df
        return self
    
    def with_coa_df(self, df: pd.DataFrame) -> "StateBuilder":
        self._coa_df = df
        return self
    
    def with_tb_df(self, df: pd.DataFrame) -> "StateBuilder":
        self._tb_df = df
        return self
    
    def with_fx_df(self, df: pd.DataFrame) -> "StateBuilder":
        self._fx_df = df
        return self
    
    def with_metrics(self, metrics: Dict[str, Any]) -> "StateBuilder":
        self._metrics = metrics
        return self
    
    def build(self) -> R2RState:
        """Build the R2RState object."""
        return R2RState(
            period=self._period,
            prior=self._prior,
            entity=self._entity,
            repo_root=self.repo_root,
            data_path=self.repo_root / "tests" / "fixtures" / "data",
            out_path=self.temp_dir,
            entities_df=self._entities_df,
            coa_df=self._coa_df,
            tb_df=self._tb_df,
            fx_df=self._fx_df,
            ai_mode=self._ai_mode,
            show_prompts=self._show_prompts,
            save_evidence=self._save_evidence,
            metrics=self._metrics,
        )


class DataFrameBuilder:
    """Builder for creating test DataFrames with financial data."""
    
    @staticmethod
    def entities() -> "EntityDataFrameBuilder":
        return EntityDataFrameBuilder()
    
    @staticmethod
    def coa() -> "COADataFrameBuilder":
        return COADataFrameBuilder()
    
    @staticmethod
    def trial_balance() -> "TBDataFrameBuilder":
        return TBDataFrameBuilder()
    
    @staticmethod
    def fx_rates() -> "FXDataFrameBuilder":
        return FXDataFrameBuilder()


class EntitiesDataFrameBuilder:
    """Builder for entities DataFrame."""
    
    def __init__(self):
        self._entities = []
    
    def add_entity(self, entity_id: str, name: str, currency: str, home_currency: str = "USD") -> "EntitiesDataFrameBuilder":
        self._entities.append({
            "entity": entity_id,
            "name": name,
            "currency": currency,
            "home_currency": home_currency,
        })
        return self
    
    def build(self) -> pd.DataFrame:
        return pd.DataFrame(self._entities)


class COADataFrameBuilder:
    """Builder for chart of accounts DataFrame."""
    
    def __init__(self):
        self._accounts = []
    
    def add_account(self, account: str, name: str, type_: str, class_: str) -> "COADataFrameBuilder":
        self._accounts.append({
            "account": account,
            "name": name,
            "type": type_,
            "class": class_,
        })
        return self
    
    def build(self) -> pd.DataFrame:
        return pd.DataFrame(self._accounts)


class TBDataFrameBuilder:
    """Builder for trial balance DataFrame."""
    
    def __init__(self):
        self._balances = []
    
    def add_balance(
        self,
        period: str,
        entity: str,
        account: str,
        balance: float,
        balance_usd: Optional[float] = None,
    ) -> "TBDataFrameBuilder":
        self._balances.append({
            "period": period,
            "entity": entity,
            "account": account,
            "balance": balance,
            "balance_usd": balance_usd or balance,
        })
        return self
    
    def build(self) -> pd.DataFrame:
        return pd.DataFrame(self._balances)


class FXDataFrameBuilder:
    """Builder for FX rates DataFrame."""
    
    def __init__(self):
        self._rates = []
    
    def add_rate(self, period: str, currency: str, rate: float) -> "FXDataFrameBuilder":
        self._rates.append({
            "period": period,
            "currency": currency,
            "usd_rate": rate,
        })
        return self
    
    def build(self) -> pd.DataFrame:
        return pd.DataFrame(self._rates)
