from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd


def load_entities(data_path: Path) -> pd.DataFrame:
    fp = Path(data_path) / "entities.csv"
    df = pd.read_csv(fp, dtype={"entity": str, "home_currency": str})
    return df


def load_coa(data_path: Path) -> pd.DataFrame:
    fp = Path(data_path) / "chart_of_accounts.csv"
    df = pd.read_csv(fp, dtype={"account": str, "account_name": str, "account_type": str})
    return df


def _find_tb_file(data_path: Path, period: str) -> Path:
    candidates = [
        Path(data_path) / f"trial_balance_{period}.csv",
        Path(data_path) / f"trial_balance_{period.replace('-', '_')}.csv",
        Path(data_path) / "trial_balance_aug.csv",  # fallback sample
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"No trial balance file found for period {period} in {data_path}")


def load_tb(data_path: Path, period: str, entity: Optional[str] = None) -> pd.DataFrame:
    fp = _find_tb_file(data_path, period)
    df = pd.read_csv(
        fp,
        dtype={"period": str, "entity": str, "account": str},
    )
    if entity and entity != "ALL":
        df = df[df["entity"] == entity]
    return df


def load_fx(data_path: Path, period: str) -> pd.DataFrame:
    fp = Path(data_path) / "fx_rates.csv"
    df = pd.read_csv(fp, dtype={"period": str, "currency": str})
    df = df[df["period"] == period]
    return df
