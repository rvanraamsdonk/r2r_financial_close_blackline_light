from __future__ import annotations

from typing import Dict, Any, List
from ..schemas import MethodType, OutputTag, PromptRun


def ai_narrative_for_fx(policy: Dict[str, Any], facts: Dict[str, Any], allow: bool) -> Dict[str, Any]:
    """Return an AI-assist narrative stub with visible metadata.

    If `allow` is False, return a deterministic-looking placeholder tagged as AI with zero cost/latency.
    """
    text = (
        "FX policy: EOM for balance sheet and average for P&L. "
        f"Period={policy.get('period')} currencies={facts.get('currencies')} coverage_ok={facts.get('coverage_ok')}"
    )

    pr = PromptRun(
        model_name=("offline" if not allow else "model"),
        model_version=(None if not allow else "v1"),
        temperature=0.0,
        tokens_in=0,
        tokens_out=0,
        latency_ms=0,
        cost=0.0,
        redaction=True,
        confidence=0.8,
        citation_row_ids=None,
    )

    tag = OutputTag(method_type=MethodType.AI, rationale="FX policy explanation narrative")
    return {"text": text, "prompt_run": pr, "tag": tag}
