from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from .schemas import EvidenceRef, DeterministicRun, PromptRun, OutputTag, MethodType


@dataclass
class R2RState:
    # Core identifiers
    period: str
    prior: str | None = None
    entity: str | None = None
    
    # Paths
    repo_root: Path | None = None
    data_path: Path | None = None
    out_path: str | None = None
    
    # Runtime context
    run_id: str | None = None
    console: Any | None = None  # ConsoleAdapter instance
    
    # Datasets
    entities_df: Optional[Any] = None
    coa_df: Optional[Any] = None
    chart_of_accounts_df: Optional[Any] = None
    tb_df: Optional[Any] = None
    fx_df: Optional[Any] = None

    # Provenance
    evidence: List[EvidenceRef] = field(default_factory=list)
    det_runs: List[DeterministicRun] = field(default_factory=list)
    prompt_runs: List[PromptRun] = field(default_factory=list)
    lineage: List[Dict[str, Any]] = field(default_factory=list)

    # Outputs / tags
    tags: List[OutputTag] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)
    messages: List[str] = field(default_factory=list)  # labeled lines for CLI

    # Policy
    ai_mode: str = "assist"  # Always enabled
    save_evidence: bool = True
    
    # Enhanced state for new console system
    gatekeeping_rationale: str | None = None

    
