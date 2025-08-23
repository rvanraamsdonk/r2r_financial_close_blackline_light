"""
AI component mocks for testing.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from unittest.mock import Mock


class MockAIResponse:
    """Mock AI response with configurable behavior."""
    
    def __init__(
        self,
        text: str = "Mock AI response",
        tokens: int = 100,
        cost_usd: float = 0.001,
        model: str = "mock-model",
    ):
        self.text = text
        self.tokens = tokens
        self.cost_usd = cost_usd
        self.model = model
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "prompt_run": {
                "prompt": "Mock prompt",
                "response": self.text,
                "model": self.model,
                "tokens": self.tokens,
                "cost_usd": self.cost_usd,
            },
            "tag": "[AI]",
        }


class MockAIModule:
    """Mock AI module that simulates AI behavior without actual API calls."""
    
    def __init__(self, responses: Optional[Dict[str, MockAIResponse]] = None):
        self.responses = responses or {}
        self.call_count = 0
        self.last_policy = None
        self.last_facts = None
    
    def __call__(self, policy: Dict[str, Any], facts: Dict[str, Any], allow: bool = True) -> Dict[str, Any]:
        """Mock AI call that returns predictable responses."""
        self.call_count += 1
        self.last_policy = policy
        self.last_facts = facts
        
        # Return specific response if configured
        kind = policy.get("kind", "default")
        if kind in self.responses:
            return self.responses[kind].to_dict()
        
        # Default response
        return MockAIResponse(
            text=f"Mock AI response for {kind}",
            tokens=50 + self.call_count * 10,
            cost_usd=0.0005 + self.call_count * 0.0001,
        ).to_dict()
    
    def configure_response(self, kind: str, response: MockAIResponse) -> None:
        """Configure specific response for a given AI kind."""
        self.responses[kind] = response
    
    def reset(self) -> None:
        """Reset mock state."""
        self.call_count = 0
        self.last_policy = None
        self.last_facts = None


def create_ai_mock_suite() -> Dict[str, MockAIModule]:
    """Create a complete suite of AI mocks for all R2R AI modules."""
    return {
        "fx_narrative": MockAIModule({
            "fx_narrative": MockAIResponse("FX coverage analysis complete", 75, 0.0008)
        }),
        "validation_root_causes": MockAIModule({
            "validation": MockAIResponse("Data validation passed", 60, 0.0006)
        }),
        "ap_ar_suggestions": MockAIModule({
            "ap_ar": MockAIResponse("AP/AR reconciliation suggestions", 120, 0.0012)
        }),
        "ic_match_proposals": MockAIModule({
            "intercompany": MockAIResponse("Intercompany matching proposals", 90, 0.0009)
        }),
        "flux_narratives": MockAIModule({
            "flux": MockAIResponse("Variance analysis narratives", 110, 0.0011)
        }),
        "hitl_case_summaries": MockAIModule({
            "hitl": MockAIResponse("HITL case summaries", 80, 0.0008)
        }),
        "bank_rationales": MockAIModule({
            "bank": MockAIResponse("Bank reconciliation rationales", 95, 0.0010)
        }),
        "accruals_narratives": MockAIModule({
            "accruals": MockAIResponse("Accruals processing narratives", 85, 0.0009)
        }),
        "gatekeeping_rationales": MockAIModule({
            "gatekeeping": MockAIResponse("Gatekeeping analysis", 70, 0.0007)
        }),
        "controls_owner_summaries": MockAIModule({
            "controls": MockAIResponse("Controls owner summaries", 100, 0.0010)
        }),
        "close_report_exec_summary": MockAIModule({
            "report": MockAIResponse("Executive close summary", 150, 0.0015)
        }),
    }
