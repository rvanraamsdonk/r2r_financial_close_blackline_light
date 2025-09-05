from datetime import datetime
from typing import Dict, Any, List
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class JEStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"

class JELine(BaseModel):
    account: str
    description: str
    debit: float = 0.0
    credit: float = 0.0

class JournalEntry(BaseModel):
    id: str
    module: str
    scenario: str
    entity: str
    period: str
    description: str
    lines: List[JELine] = Field(default_factory=list)
    status: JEStatus = JEStatus.DRAFT
    source_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())

    @property
    def total_debits(self) -> float:
        return sum(line.debit for line in self.lines)

    @property
    def total_credits(self) -> float:
        return sum(line.credit for line in self.lines)

    @property
    def is_balanced(self) -> bool:
        return abs(self.total_debits - self.total_credits) < 0.01

# In-memory JE storage (in production, this would be a database)
_je_store: Dict[str, JournalEntry] = {}

def _create_fx_je(entity: str, account: str, period: str, diff_usd: float, source_data: Dict[str, Any]) -> JournalEntry:
    """Create a journal entry for FX translation differences."""
    je_id = str(uuid.uuid4())[:8]
    if diff_usd > 0:
        lines = [
            JELine(account="7200", description="FX Translation Adjustment", debit=abs(diff_usd)),
            JELine(account=account, description=f"FX Revaluation - {entity}", credit=abs(diff_usd))
        ]
    else:
        lines = [
            JELine(account=account, description=f"FX Revaluation - {entity}", debit=abs(diff_usd)),
            JELine(account="7200", description="FX Translation Adjustment", credit=abs(diff_usd))
        ]
    description = f"FX translation adjustment for {entity} account {account} - ${diff_usd:.2f} difference"
    return JournalEntry(
        id=je_id,
        module="FX",
        scenario="fx_translation",
        entity=entity,
        period=period,
        description=description,
        lines=lines,
        source_data=source_data,
    )

def _create_flux_je(source_data: Dict[str, Any], period: str, entity: str) -> JournalEntry:
    """Create journal entry for flux analysis variance."""
    account = source_data.get("account", "Unknown")
    var_amount = float(source_data.get("var_vs_budget", 0.0))
    if var_amount == 0.0:
        var_amount = float(source_data.get("var_vs_prior", 0.0))
    lines: List[JELine] = []
    if var_amount != 0.0:
        if var_amount > 0:
            lines.append(JELine(f"{account}-Variance", f"Flux variance adjustment for {account}", var_amount, 0.0))
            lines.append(JELine("2100-Accrued Liabilities", "Variance accrual", 0.0, var_amount))
        else:
            lines.append(JELine("2100-Accrued Liabilities", "Variance accrual reversal", abs(var_amount), 0.0))
            lines.append(JELine(f"{account}-Variance", f"Flux variance adjustment for {account}", 0.0, abs(var_amount)))
    return JournalEntry(
        id=str(uuid.uuid4()),
        module="Flux",
        scenario="variance_analysis",
        entity=entity,
        period=period,
        description=f"Flux variance adjustment for {entity}/{account}",
        lines=lines,
        status=JEStatus.DRAFT,
        source_data=source_data,
        created_at=datetime.now(),
    )

def _create_bank_je(source_data: Dict[str, Any], period: str, entity: str) -> JournalEntry:
    """Create journal entry for bank reconciliation adjustment."""
    txn_id = source_data.get("bank_txn_id", "Unknown")
    amount = float(source_data.get("amount", 0.0))
    counterparty = source_data.get("counterparty", "Unknown")
    reason = source_data.get("reason", "adjustment")
    lines: List[JELine] = []
    if amount != 0.0:
        if reason == "unusual_counterparty" or source_data.get("classification") == "forensic_risk":
            if amount > 0:
                lines.append(JELine("1010-Cash", f"Reverse suspicious transaction {txn_id}", 0.0, amount))
                lines.append(JELine("1200-Suspense Account", f"Hold for investigation - {counterparty}", amount, 0.0))
            else:
                lines.append(JELine("1010-Cash", f"Reverse suspicious transaction {txn_id}", abs(amount), 0.0))
                lines.append(JELine("1200-Suspense Account", f"Hold for investigation - {counterparty}", 0.0, abs(amount)))
        elif reason == "timing_difference":
            if amount > 0:
                lines.append(JELine("1020-Cash in Transit", f"Outstanding deposit {txn_id}", amount, 0.0))
                lines.append(JELine("1010-Cash", "Bank reconciliation adjustment", 0.0, amount))
            else:
                lines.append(JELine("1010-Cash", "Bank reconciliation adjustment", abs(amount), 0.0))
                lines.append(JELine("2010-Outstanding Checks", f"Outstanding check {txn_id}", 0.0, abs(amount)))
        else:
            if amount > 0:
                lines.append(JELine("1010-Cash", f"Bank adjustment {txn_id}", amount, 0.0))
                lines.append(JELine("6100-Bank Charges", "Bank reconciliation adjustment", 0.0, amount))
            else:
                lines.append(JELine("6100-Bank Charges", "Bank reconciliation adjustment", abs(amount), 0.0))
                lines.append(JELine("1010-Cash", f"Bank adjustment {txn_id}", 0.0, abs(amount)))
    return JournalEntry(
        id=str(uuid.uuid4()),
        module="Bank",
        scenario="bank_reconciliation",
        entity=entity,
        period=period,
        description=f"Bank reconciliation adjustment for {entity}/{txn_id}",
        lines=lines,
        status=JEStatus.DRAFT,
        source_data=source_data,
        created_at=datetime.now(),
    )
