from __future__ import annotations

from typing import Any

import pandas as pd


def safe_str(val: Any) -> str:
    """Return a stripped string or empty string for NaN/None/invalid values.

    Centralized helper to avoid AttributeError when pandas values are float('nan')
    by coercing safely to string only when not NaN.
    """
    if pd.isna(val):
        return ""
    try:
        return str(val).strip()
    except Exception:
        return ""
