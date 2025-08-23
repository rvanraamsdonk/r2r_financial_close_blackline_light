"""
Custom assertion helpers for financial close testing.
"""
from __future__ import annotations

from typing import Optional

import pandas as pd
import pytest


def assert_dataframe_equals(
    actual: pd.DataFrame,
    expected: pd.DataFrame,
    check_dtype: bool = True,
    check_index: bool = True,
    tolerance: float = 1e-6,
) -> None:
    """Assert two DataFrames are equal with financial precision handling."""
    try:
        pd.testing.assert_frame_equal(
            actual,
            expected,
            check_dtype=check_dtype,
            check_index=check_index,
            atol=tolerance,
            rtol=tolerance,
        )
    except AssertionError as e:
        pytest.fail(f"DataFrames are not equal:\n{e}")


def assert_financial_balance(
    debits: float,
    credits: float,
    tolerance: float = 0.01,
    message: Optional[str] = None,
) -> None:
    """Assert that debits equal credits within financial tolerance."""
    difference = abs(debits - credits)
    if difference > tolerance:
        error_msg = f"Financial imbalance: debits={debits:.2f}, credits={credits:.2f}, diff={difference:.2f}"
        if message:
            error_msg = f"{message}: {error_msg}"
        pytest.fail(error_msg)


def assert_tb_balanced(tb_df: pd.DataFrame, tolerance: float = 0.01) -> None:
    """Assert trial balance is balanced by entity."""
    for entity in tb_df["entity"].unique():
        entity_tb = tb_df[tb_df["entity"] == entity]
        total_balance = entity_tb["balance_usd"].sum()
        if abs(total_balance) > tolerance:
            pytest.fail(f"Entity {entity} trial balance not balanced: {total_balance:.2f}")


def assert_fx_consistency(
    amount_local: float,
    amount_usd: float,
    fx_rate: float,
    tolerance: float = 0.01,
) -> None:
    """Assert FX conversion consistency."""
    expected_usd = amount_local * fx_rate
    difference = abs(amount_usd - expected_usd)
    if difference > tolerance:
        pytest.fail(
            f"FX conversion inconsistent: {amount_local} * {fx_rate} = {expected_usd:.2f}, "
            f"but got {amount_usd:.2f} (diff: {difference:.2f})"
        )
