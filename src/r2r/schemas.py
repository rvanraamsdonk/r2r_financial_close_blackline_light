from __future__ import annotations

from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid


class MethodType(str, Enum):
    DET = "DET"
    AI = "AI"
    HYBRID = "HYBRID"


class EvidenceRef(BaseModel):
    id: str = Field(default_factory=lambda: f"ev-{uuid.uuid4().hex}")
    type: str
    uri: Optional[str] = None
    input_row_ids: Optional[List[str]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    hash: Optional[str] = None


class DeterministicRun(BaseModel):
    id: str = Field(default_factory=lambda: f"det-{uuid.uuid4().hex}")
    function_name: str
    code_hash: str = ""
    params: Dict[str, Any] = Field(default_factory=dict)
    row_ids: Optional[List[str]] = None
    output_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class PromptRun(BaseModel):
    id: str = Field(default_factory=lambda: f"ai-{uuid.uuid4().hex}")
    prompt_id: Optional[str] = None
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    temperature: Optional[float] = None
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    cost: float = 0.0
    redaction: bool = True
    confidence: Optional[float] = None
    citation_row_ids: Optional[List[str]] = None
    prompt_hash: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class LineageLink(BaseModel):
    id: str = Field(default_factory=lambda: f"ln-{uuid.uuid4().hex}")
    output_id: str
    input_row_ids: Optional[List[str]] = None
    fx_rate_ids: Optional[List[str]] = None
    je_ids: Optional[List[str]] = None
    prompt_ids: Optional[List[str]] = None


class OutputTag(BaseModel):
    method_type: MethodType
    rationale: Optional[str] = None
    materiality_band: Optional[str] = None


__all__ = [
    "MethodType",
    "EvidenceRef",
    "DeterministicRun",
    "PromptRun",
    "LineageLink",
    "OutputTag",
]
