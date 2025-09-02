"""
Approval Workflow Engine - Configurable routing and sign-off for JE proposals
"""

from typing import Dict, List, Optional, Callable
from enum import Enum
from dataclasses import dataclass
from datetime import datetime
from .models import JEProposal, JEStatus


class ApprovalAction(Enum):
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_CHANGES = "request_changes"
    ESCALATE = "escalate"


@dataclass
class ApprovalRule:
    """Rule for determining approval requirements"""
    module: str
    scenario: str
    min_amount: float = 0.0
    max_amount: float = float('inf')
    required_approvers: List[str] = None
    auto_approve: bool = False
    escalation_threshold: float = float('inf')
    
    def __post_init__(self):
        if self.required_approvers is None:
            self.required_approvers = []


@dataclass
class ApprovalStep:
    """Individual approval step in workflow"""
    approver_id: str
    approver_role: str
    status: str = "pending"  # pending, approved, rejected
    comments: Optional[str] = None
    timestamp: Optional[datetime] = None


class ApprovalWorkflow:
    """Manages approval workflows for JE proposals"""
    
    def __init__(self):
        self._rules: List[ApprovalRule] = []
        self._workflows: Dict[str, List[ApprovalStep]] = {}  # proposal_id -> steps
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Load default approval rules"""
        
        # FX Translation - Auto-approve small amounts
        self.add_rule(ApprovalRule(
            module="FX",
            scenario="translation_adjustment",
            min_amount=0.0,
            max_amount=1000.0,
            auto_approve=True
        ))
        
        # FX Translation - Manager approval for medium amounts
        self.add_rule(ApprovalRule(
            module="FX", 
            scenario="translation_adjustment",
            min_amount=1000.0,
            max_amount=10000.0,
            required_approvers=["accounting_manager"]
        ))
        
        # FX Translation - Controller approval for large amounts
        self.add_rule(ApprovalRule(
            module="FX",
            scenario="translation_adjustment", 
            min_amount=10000.0,
            required_approvers=["accounting_manager", "controller"]
        ))
        
        # Flux Accruals - Manager approval required
        self.add_rule(ApprovalRule(
            module="Flux",
            scenario="accrual_adjustment",
            min_amount=0.0,
            required_approvers=["accounting_manager"]
        ))
        
        # AP/AR Clearing - Auto-approve small amounts
        for module in ["AP", "AR"]:
            self.add_rule(ApprovalRule(
                module=module,
                scenario="clearing_adjustment",
                min_amount=0.0,
                max_amount=500.0,
                auto_approve=True
            ))
            
            self.add_rule(ApprovalRule(
                module=module,
                scenario="clearing_adjustment",
                min_amount=500.0,
                required_approvers=["accounting_manager"]
            ))
        
        # Intercompany - Always requires controller approval
        self.add_rule(ApprovalRule(
            module="Intercompany",
            scenario="elimination_entry",
            min_amount=0.0,
            required_approvers=["controller"]
        ))
        
        # Accrual Reversals - Auto-approve (standard reversals)
        self.add_rule(ApprovalRule(
            module="Accruals",
            scenario="reversal_entry",
            min_amount=0.0,
            auto_approve=True
        ))
    
    def add_rule(self, rule: ApprovalRule):
        """Add approval rule to workflow engine"""
        self._rules.append(rule)
    
    def get_approval_requirements(self, proposal: JEProposal) -> List[str]:
        """
        Determine required approvers for a JE proposal
        
        Returns:
            List of approver role IDs required for this proposal
        """
        amount = abs(proposal.total_debits)
        
        # Find matching rules (most specific first)
        matching_rules = [
            rule for rule in self._rules
            if (rule.module == proposal.module and 
                rule.scenario == proposal.scenario and
                rule.min_amount <= amount < rule.max_amount)
        ]
        
        if not matching_rules:
            # Default: require manager approval
            return ["accounting_manager"]
        
        # Use first matching rule
        rule = matching_rules[0]
        
        if rule.auto_approve:
            return []  # No approval needed
        
        return rule.required_approvers.copy()
    
    def initiate_approval(self, proposal: JEProposal) -> bool:
        """
        Start approval workflow for a proposal
        
        Returns:
            True if approval initiated, False if auto-approved
        """
        required_approvers = self.get_approval_requirements(proposal)
        
        if not required_approvers:
            # Auto-approve
            proposal.status = JEStatus.APPROVED
            proposal.approved_at = datetime.utcnow()
            proposal.approved_by = "system_auto_approval"
            return False
        
        # Create approval steps
        steps = []
        for approver_role in required_approvers:
            steps.append(ApprovalStep(
                approver_id=self._get_approver_for_role(approver_role, proposal.entity),
                approver_role=approver_role,
                status="pending"
            ))
        
        self._workflows[proposal.id] = steps
        proposal.status = JEStatus.PENDING
        return True
    
    def process_approval(
        self, 
        proposal_id: str, 
        approver_id: str, 
        action: ApprovalAction,
        comments: Optional[str] = None
    ) -> bool:
        """
        Process an approval action
        
        Returns:
            True if workflow completed, False if more approvals needed
        """
        if proposal_id not in self._workflows:
            raise ValueError(f"No workflow found for proposal {proposal_id}")
        
        steps = self._workflows[proposal_id]
        
        # Find the approver's step
        approver_step = None
        for step in steps:
            if step.approver_id == approver_id and step.status == "pending":
                approver_step = step
                break
        
        if not approver_step:
            raise ValueError(f"No pending approval found for approver {approver_id}")
        
        # Process the action
        approver_step.timestamp = datetime.utcnow()
        approver_step.comments = comments
        
        if action == ApprovalAction.APPROVE:
            approver_step.status = "approved"
        elif action == ApprovalAction.REJECT:
            approver_step.status = "rejected"
            # Reject entire workflow
            for step in steps:
                if step.status == "pending":
                    step.status = "cancelled"
            return True  # Workflow completed (rejected)
        elif action == ApprovalAction.REQUEST_CHANGES:
            approver_step.status = "changes_requested"
            return True  # Workflow completed (needs changes)
        
        # Check if all approvals complete
        pending_steps = [s for s in steps if s.status == "pending"]
        if not pending_steps:
            return True  # All approvals complete
        
        return False  # More approvals needed
    
    def get_workflow_status(self, proposal_id: str) -> Dict[str, any]:
        """Get current status of approval workflow"""
        if proposal_id not in self._workflows:
            return {"status": "no_workflow", "steps": []}
        
        steps = self._workflows[proposal_id]
        completed_steps = [s for s in steps if s.status != "pending"]
        pending_steps = [s for s in steps if s.status == "pending"]
        
        return {
            "status": "in_progress" if pending_steps else "completed",
            "total_steps": len(steps),
            "completed_steps": len(completed_steps),
            "pending_steps": len(pending_steps),
            "steps": [
                {
                    "approver_id": s.approver_id,
                    "approver_role": s.approver_role,
                    "status": s.status,
                    "comments": s.comments,
                    "timestamp": s.timestamp.isoformat() if s.timestamp else None
                }
                for s in steps
            ]
        }
    
    def get_pending_approvals(self, approver_id: str) -> List[str]:
        """Get list of proposal IDs pending approval by specific approver"""
        pending = []
        
        for proposal_id, steps in self._workflows.items():
            for step in steps:
                if (step.approver_id == approver_id and 
                    step.status == "pending"):
                    pending.append(proposal_id)
                    break
        
        return pending
    
    def _get_approver_for_role(self, role: str, entity: str) -> str:
        """
        Map approver role to actual user ID for entity
        
        In a real system, this would lookup from user/role database
        """
        role_mappings = {
            "accounting_manager": f"mgr_{entity.lower()}",
            "controller": "controller_global", 
            "cfo": "cfo_global"
        }
        
        return role_mappings.get(role, f"approver_{role}")
