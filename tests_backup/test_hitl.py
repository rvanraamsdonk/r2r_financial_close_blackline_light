#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import sys

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"
sys.path.insert(0, str(ROOT / "src"))

from r2r.state import R2RState  # type: ignore
from r2r.audit import AuditLogger  # type: ignore
from r2r.engines.hitl import open_hitl_cases  # type: ignore


def build_state(metrics: dict[str, Any]) -> R2RState:
    return R2RState(
        period="2099-01",
        prior=None,
        entity="ALL",
        repo_root=ROOT,
        data_path=ROOT / "data" / "lite",
        out_path=OUT,
        entities_df=None,
        coa_df=None,
        tb_df=None,
        fx_df=None,
        ai_mode="off",
        show_prompts=False,
        save_evidence=True,
        metrics=metrics,
    )


def test_severity_and_count() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    audit = AuditLogger(OUT, "TESTHITL")

    # Case 1: gatekeeping block, but no explicit category counts -> 1 general case, high
    s1 = build_state({"gatekeeping_block_close": True})
    s1 = open_hitl_cases(s1, audit)
    assert s1.metrics.get("hitl_cases_open_count") == 1, "Expected 1 general case"

    cases_path = Path(s1.metrics["hitl_cases_artifact"])  # type: ignore[index]
    cases = json.loads(Path(cases_path).read_text())
    assert cases[0]["severity"] == "high", "Expected high severity when block_close is True"

    # Case 2: explicit categories with counts, no block -> per-category cases, medium severity
    s2 = build_state({
        "gatekeeping_block_close": False,
        "ap_exceptions_count": 2,
        "ar_exceptions_count": 1,
        "je_exceptions_count": 0,
    })
    s2 = open_hitl_cases(s2, audit)
    assert s2.metrics.get("hitl_cases_open_count") == 2, "Expected 2 cases for AP and AR"

    cases2_path = Path(s2.metrics["hitl_cases_artifact"])  # type: ignore[index]
    cases2 = json.loads(Path(cases2_path).read_text())
    severities = {c["source"]: c["severity"] for c in cases2}
    assert severities.get("ap_exceptions") == "medium", "Expected medium severity without block"
    assert severities.get("ar_exceptions") == "medium", "Expected medium severity without block"

    print("HITL tests passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(test_severity_and_count())
