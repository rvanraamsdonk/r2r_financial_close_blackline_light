from __future__ import annotations
from typing import TypedDict, Literal, Any, Optional, Dict
from pydantic import BaseModel
from datetime import date

Risk = Literal["low","medium","high"]

class Task(BaseModel):
    id: str
    stage: str
    owner: str
    sla: date
    predecessors: list[str] = []
    status: Literal["pending","in_progress","done","blocked"] = "pending"

class AuditEvent(BaseModel):
    ts: str
    actor: str  # system|user:<id>|agent:<name>
    action: str
    entity: Optional[str] = None
    details: Dict[str, Any] = {}

class HITLCase(BaseModel):
    id: str
    type: Literal["recon_cert","journal_post","ic_settlement","flux_explanation"]
    risk: Risk
    payload: Dict[str, Any]
    status: Literal["queued","approved","rejected"] = "queued"
    maker: Optional[str] = None
    checker: Optional[str] = None

class ReconResult(BaseModel):
    account_id: str
    entity: str
    risk: Risk
    status: Literal["certified","open","decertified"]
    diff: float
    rule_hits: list[str] = []
    evidence_refs: list[str] = []
    gl_balance_at_cert: float | None = None

class MatchResult(BaseModel):
    rule_hit: str
    cleared: int
    residual: int
    repeat_exception_tags: list[str] = []

class Journal(BaseModel):
    id: str
    entity: str
    description: str
    amount: float
    currency: str
    status: Literal["draft","approved","posted","rejected"] = "draft"
    preparer: Optional[str] = None
    approver: Optional[str] = None
    links: Dict[str, Any] = {}

class FluxAlert(BaseModel):
    entity: str
    account_id: str
    delta_abs: float
    delta_pct: float
    material: bool
    narrative: Optional[str] = None

class ICItem(BaseModel):
    pair: tuple[str,str]
    doc_id: str
    amount_src: float
    currency: str
    status: Literal["open","balanced","net_ready","settled"] = "open"
    exceptions: list[str] = []

class Match(BaseModel):
    id: str
    ar_id: str
    bank_id: str
    amount: float
    match_type: str
    confidence: float
    date_diff: int

class CloseState(TypedDict, total=False):
    period: str
    entities: list[str]
    tasks: list[Task]
    events: list[AuditEvent]
    recs: list[ReconResult]
    matches: list[MatchResult]
    journals: list[Journal]
    flux: list[FluxAlert]
    ic: list[ICItem]
    hitl_queue: list[HITLCase]
    policy: dict
    data: dict
