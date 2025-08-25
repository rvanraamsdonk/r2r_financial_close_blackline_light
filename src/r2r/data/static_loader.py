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
        Path(data_path) / f"trial_balance_{period}_enhanced.csv",  # prefer enhanced
        Path(data_path) / f"trial_balance_{period}.csv",
        Path(data_path) / f"trial_balance_{period.replace('-', '_')}_enhanced.csv",  # prefer enhanced
        Path(data_path) / f"trial_balance_{period.replace('-', '_')}.csv",
        Path(data_path) / "trial_balance_aug_enhanced.csv",  # enhanced fallback
        Path(data_path) / "trial_balance_aug.csv",  # original fallback
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


def _find_ar_file(data_path: Path, period: str) -> Path:
    base = Path(data_path) / "subledgers"
    candidates = [
        base / f"ar_detail_{period}_enhanced.csv",  # prefer enhanced
        base / f"ar_detail_{period}.csv",
        base / f"ar_detail_{period.replace('-', '_')}_enhanced.csv",  # prefer enhanced
        base / f"ar_detail_{period.replace('-', '_')}.csv",
        base / "ar_detail_aug_enhanced.csv",  # enhanced fallback
        base / "ar_detail_aug.csv",  # original fallback
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"No AR detail file found for period {period} in {base}")


def load_ar_detail(
    data_path: Path, period: str, entity: Optional[str] = None, status: Optional[str] = None
) -> pd.DataFrame:
    fp = _find_ar_file(data_path, period)
    df = pd.read_csv(
        fp,
        dtype={
            "period": str,
            "entity": str,
            "invoice_id": str,
            "customer_name": str,
            "invoice_date": str,
            "currency": str,
            "status": str,
        },
    )
    df = df[df["period"] == period]
    if entity and entity != "ALL":
        df = df[df["entity"] == entity]
    if status:
        df = df[df["status"] == status]
    return df


def _find_ap_file(data_path: Path, period: str) -> Path:
    base = Path(data_path) / "subledgers"
    candidates = [
        base / f"ap_detail_{period}_enhanced.csv",  # prefer enhanced
        base / f"ap_detail_{period}.csv",
        base / f"ap_detail_{period.replace('-', '_')}_enhanced.csv",  # prefer enhanced
        base / f"ap_detail_{period.replace('-', '_')}.csv",
        base / "ap_detail_aug_enhanced.csv",  # enhanced fallback
        base / "ap_detail_aug.csv",  # original fallback
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"No AP detail file found for period {period} in {base}")


def load_ap_detail(
    data_path: Path, period: str, entity: Optional[str] = None, status: Optional[str] = None
) -> pd.DataFrame:
    fp = _find_ap_file(data_path, period)
    df = pd.read_csv(
        fp,
        dtype={
            "period": str,
            "entity": str,
            "bill_id": str,
            "vendor_name": str,
            "bill_date": str,
            "currency": str,
            "status": str,
            "notes": str,
        },
    )
    df = df[df["period"] == period]
    if entity and entity != "ALL":
        df = df[df["entity"] == entity]
    if status:
        df = df[df["status"] == status]
    return df


def _find_bank_file(data_path: Path, period: str) -> Path:
    base = Path(data_path) / "subledgers" / "bank_statements"
    candidates = [
        base / f"bank_transactions_{period}_enhanced.csv",  # prefer enhanced
        base / f"bank_transactions_{period}.csv",
        base / f"bank_transactions_{period.replace('-', '_')}_enhanced.csv",  # prefer enhanced
        base / f"bank_transactions_{period.replace('-', '_')}.csv",
        base / "bank_transactions_aug_enhanced.csv",  # enhanced fallback
        base / "bank_transactions_aug.csv",  # original fallback
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(
        f"No unified bank transactions file found for period {period} in {base}"
    )


def load_bank_transactions(
    data_path: Path, period: str, entity: Optional[str] = None
) -> pd.DataFrame:
    fp = _find_bank_file(data_path, period)
    df = pd.read_csv(
        fp,
        dtype={
            "period": str,
            "entity": str,
            "bank_txn_id": str,
            "date": str,
            "currency": str,
            "counterparty": str,
            "transaction_type": str,
            "description": str,
        },
    )
    df = df[df["period"] == period]
    if entity and entity != "ALL":
        df = df[df["entity"] == entity]
    return df


def _find_ic_file(data_path: Path, period: str) -> Path:
    base = Path(data_path) / "subledgers" / "intercompany"
    candidates = [
        base / f"ic_transactions_{period}.csv",
        base / f"ic_transactions_{period.replace('-', '_')}.csv",
        base / "ic_transactions_aug.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"No intercompany file found for period {period} in {base}")


def load_intercompany(
    data_path: Path,
    period: str,
    src_entity: Optional[str] = None,
    dst_entity: Optional[str] = None,
) -> pd.DataFrame:
    fp = _find_ic_file(data_path, period)
    df = pd.read_csv(
        fp,
        dtype={
            "period": str,
            "entity_src": str,
            "entity_dst": str,
            "doc_id": str,
            "currency": str,
            "transaction_type": str,
            "description": str,
        },
    )
    df = df[df["period"] == period]
    if src_entity and src_entity != "ALL":
        df = df[df["entity_src"] == src_entity]
    if dst_entity and dst_entity != "ALL":
        df = df[df["entity_dst"] == dst_entity]
    return df


def load_fx(data_path: Path, period: str) -> pd.DataFrame:
    # Try enhanced FX rates first
    candidates = [
        Path(data_path) / "fx_rates_enhanced.csv",
        Path(data_path) / "fx_rates.csv",
    ]
    fp = None
    for c in candidates:
        if c.exists():
            fp = c
            break
    if fp is None:
        fp = Path(data_path) / "fx_rates.csv"  # fallback
    df = pd.read_csv(fp, dtype={"period": str, "currency": str})
    df = df[df["period"] == period]
    return df


def load_budget(data_path: Path, period: str, entity: Optional[str] = None) -> pd.DataFrame:
    """
    Load budget for a given period (and optional entity) from budget.csv
    Expected schema: period, entity, account, budget_amount
    """
    fp = Path(data_path) / "budget.csv"
    df = pd.read_csv(
        fp,
        dtype={
            "period": str,
            "entity": str,
            "account": str,
            "budget_amount": float,
        },
    )
    df = df[df["period"] == period]
    if entity and entity != "ALL":
        df = df[df["entity"] == entity]
    return df
