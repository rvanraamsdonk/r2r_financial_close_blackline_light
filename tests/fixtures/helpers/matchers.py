"""
Custom matchers for financial close testing.
"""
from __future__ import annotations

from typing import Any, Union


class ApproxMatcher:
    """Approximate matcher for floating point comparisons."""
    
    def __init__(self, expected: float, tolerance: float = 1e-6):
        self.expected = expected
        self.tolerance = tolerance
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, (int, float)):
            return False
        return abs(float(other) - self.expected) <= self.tolerance
    
    def __repr__(self) -> str:
        return f"ApproxMatcher({self.expected} ± {self.tolerance})"


class FinancialMatcher:
    """Matcher for financial amounts with currency precision."""
    
    def __init__(self, expected: float, currency_precision: int = 2):
        self.expected = expected
        self.tolerance = 10 ** (-currency_precision)
    
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, (int, float)):
            return False
        return abs(float(other) - self.expected) <= self.tolerance
    
    def __repr__(self) -> str:
        return f"FinancialMatcher({self.expected:.2f} ± {self.tolerance})"


def approx(expected: float, tolerance: float = 1e-6) -> ApproxMatcher:
    """Create an approximate matcher."""
    return ApproxMatcher(expected, tolerance)


def financial_approx(expected: float, precision: int = 2) -> FinancialMatcher:
    """Create a financial precision matcher."""
    return FinancialMatcher(expected, precision)
