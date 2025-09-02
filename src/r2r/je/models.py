"""
Journal Entry Data Models
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


class JEStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending" 
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"


@dataclass
class JELine:
    """Individual journal entry line (debit or credit)"""
    account: str
    description: str
    debit: float = 0.0
    credit: float = 0.0
    entity: Optional[str] = None
    currency: Optional[str] = None
    
    def __post_init__(self):
        if self.debit > 0 and self.credit > 0:
            raise ValueError("Line cannot have both debit and credit")
        if self.debit == 0 and self.credit == 0:
            raise ValueError("Line must have either debit or credit")


@dataclass 
class JEProposal:
    """Complete journal entry proposal"""
    id: str
    module: str  # "FX", "Flux", "AP", "AR", etc.
    scenario: str  # "translation_adjustment", "accrual_reversal", etc.
    period: str
    entity: str
    description: str
    lines: List[JELine]
    source_data: Dict[str, Any]  # Original data that triggered the JE
    status: JEStatus = JEStatus.DRAFT
    created_by: Optional[str] = None
    created_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    comments: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
    
    @property
    def total_debits(self) -> float:
        return sum(line.debit for line in self.lines)
    
    @property 
    def total_credits(self) -> float:
        return sum(line.credit for line in self.lines)
    
    @property
    def is_balanced(self) -> bool:
        return abs(self.total_debits - self.total_credits) < 0.01
    
    def validate(self) -> List[str]:
        """Return list of validation errors"""
        errors = []
        
        if not self.lines:
            errors.append("JE must have at least one line")
        
        if not self.is_balanced:
            errors.append(f"JE not balanced: debits={self.total_debits:.2f}, credits={self.total_credits:.2f}")
        
        for i, line in enumerate(self.lines):
            if not line.account:
                errors.append(f"Line {i+1}: Account is required")
            if not line.description:
                errors.append(f"Line {i+1}: Description is required")
        
        return errors


@dataclass
class JETemplate:
    """Template for generating JEs for a specific module/scenario"""
    module: str
    scenario: str
    description_template: str
    account_mappings: Dict[str, str]  # role -> account_code
    calculation_rules: Dict[str, Any]
    approval_required: bool = True
    materiality_threshold: float = 0.0
