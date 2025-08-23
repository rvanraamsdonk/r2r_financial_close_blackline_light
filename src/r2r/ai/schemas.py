from __future__ import annotations

from typing import List, Optional, Dict, Any
from pydantic import BaseModel


class BaseAI(BaseModel):
    generated_at: str
    period: str
    entity_scope: Optional[str] = None


class ValidationAI(BaseAI):
    summary: Dict[str, Any]
    root_causes: List[Dict[str, Any]]
    remediations: List[Dict[str, Any]]
    citations: List[Optional[str]]


class APARAI(BaseAI):
    matches: List[Dict[str, Any]]
    unresolved_summary: Dict[str, int]
    citations: List[Optional[str]]


class ICAI(BaseAI):
    candidate_pairs: List[Dict[str, Any]]
    je_proposals: List[Dict[str, Any]]
    citations: List[Optional[str]]


class FluxAI(BaseAI):
    narratives: List[Dict[str, Any]]
    citations: List[Optional[str]]


class HITLAI(BaseAI):
    case_summaries: List[Dict[str, Any]]
    next_actions: List[Dict[str, Any]]
    citations: List[Optional[str]]


class BankAI(BaseAI):
    rationales: List[Dict[str, Any]]
    citations: List[Optional[str]]


class AccrualsAI(BaseAI):
    narratives: List[Dict[str, Any]]
    je_rationales: List[Dict[str, Any]]
    citations: List[Optional[str]]


class GatekeepingAI(BaseAI):
    risk_level: Optional[str]
    block_close: Optional[bool]
    rationales: List[Dict[str, Any]]
    citations: List[Optional[str]]


class ControlsAI(BaseAI):
    owner_summaries: List[Dict[str, Any]]
    residual_risks: List[Dict[str, Any]]
    citations: List[Optional[str]]


class ReportAI(BaseAI):
    executive_summary: str
    citations: List[Optional[str]]
