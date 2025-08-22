from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from .schemas import EvidenceRef, DeterministicRun, PromptRun, OutputTag, MethodType


class R2RState(BaseModel):
    # Scope
    period: str
    prior: Optional[str] = None
    entity: str = "ALL"

    # Paths
    repo_root: Path
    data_path: Path
    out_path: Path

    # Datasets
    entities_df: Optional[Any] = None
    coa_df: Optional[Any] = None
    tb_df: Optional[Any] = None
    fx_df: Optional[Any] = None

    # Provenance
    evidence: List[EvidenceRef] = Field(default_factory=list)
    det_runs: List[DeterministicRun] = Field(default_factory=list)
    prompt_runs: List[PromptRun] = Field(default_factory=list)
    lineage: List[Dict[str, Any]] = Field(default_factory=list)

    # Outputs / tags
    tags: List[OutputTag] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    messages: List[str] = Field(default_factory=list)  # labeled lines for CLI

    # Policy
    ai_mode: str = "assist"
    show_prompts: bool = False
    save_evidence: bool = True

    class Config:
        arbitrary_types_allowed = True
