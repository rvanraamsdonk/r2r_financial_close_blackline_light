from __future__ import annotations
from typing import Dict, Any
POLICY: Dict[str, Any] = {
    "auto_cert_rules": [
        {"name": "zero_balance_no_activity"},
        {"name": "subledger_equals_gl_within_threshold", "threshold_abs": 50.0, "threshold_pct": 0.01},
        {"name": "bankrec_match", "tolerance": 0.01},
        {"name": "ic_variance_below_tolerance", "tolerance": 25.0},
    ],
    "flux_thresholds": {
        "cash": {"pct": 10.0, "abs": 5_000.0},
        "revenue": {"pct": 5.0, "abs": 50_000.0},
        "expense": {"pct": 7.5, "abs": 25_000.0},
        "default": {"pct": 8.0, "abs": 20_000.0},
    },
    "sod": {"roles": ["preparer","approver","reviewer"], "rules": ["preparer!=approver"]},
    "risk": {"high_accounts": ["IC_PAY","IC_REC","FX_GAIN_LOSS","REV"], "high_amount_abs": 100_000.0},
    "hitl_modes": {"default": "supervised"},
    "sampling": {"low_risk_cert_sample_pct": 5.0},
}
