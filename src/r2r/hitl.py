"""
Human-in-the-Loop (HITL) workflow for R2R financial close process.
Provides interactive review and approval of flagged items.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class HITLItem:
    """Represents an item requiring human review."""
    id: str
    type: str  # 'accrual', 'duplicate', 'timing', 'variance'
    amount: float
    description: str
    ai_recommendation: str
    supporting_evidence: List[str]
    confidence: float
    status: str = "pending"  # 'pending', 'approved', 'rejected', 'modified'
    reviewer_notes: str = ""
    reviewed_at: Optional[str] = None
    reviewer: str = ""

class HITLWorkflow:
    """Manages the Human-in-the-Loop review process."""
    
    def __init__(self, data_path: str = None):
        if data_path is None:
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_path = project_root / "data"
        else:
            self.data_path = Path(data_path)
        
        self.emails = self._load_emails()
        self.hitl_items = []
        self.review_session = None
    
    def _load_emails(self) -> Dict:
        """Load email evidence from JSON file."""
        email_file = self.data_path / "supporting" / "emails.json"
        if email_file.exists():
            with open(email_file, 'r') as f:
                return json.load(f)
        return {"emails": []}
    
    def flag_item(self, item_id: str, item_type: str, amount: float, 
                  description: str, ai_recommendation: str, 
                  confidence: float, evidence_refs: List[str] = None) -> HITLItem:
        """Flag an item for HITL review."""
        
        # Find supporting evidence
        supporting_evidence = []
        if evidence_refs:
            for ref in evidence_refs:
                email = self._find_email_by_ref(ref)
                if email:
                    supporting_evidence.append({
                        "type": "email",
                        "subject": email["subject"],
                        "from": email["from"],
                        "summary": email["ai_summary"],
                        "body": email["body"][:200] + "..." if len(email["body"]) > 200 else email["body"]
                    })
        
        hitl_item = HITLItem(
            id=item_id,
            type=item_type,
            amount=amount,
            description=description,
            ai_recommendation=ai_recommendation,
            supporting_evidence=supporting_evidence,
            confidence=confidence
        )
        
        self.hitl_items.append(hitl_item)
        return hitl_item
    
    def _find_email_by_ref(self, ref: str) -> Optional[Dict]:
        """Find email by accrual_id or other reference."""
        for email in self.emails.get("emails", []):
            if email.get("accrual_id") == ref or email.get("id") == ref:
                return email
        return None
    
    def start_review_session(self, reviewer: str = "Financial Controller") -> Dict[str, Any]:
        """Start an interactive HITL review session."""
        if not self.hitl_items:
            return {"status": "no_items", "message": "No items require HITL review"}
        
        self.review_session = {
            "started_at": datetime.now().isoformat(),
            "reviewer": reviewer,
            "items_total": len(self.hitl_items),
            "items_reviewed": 0,
            "current_item": 0
        }
        
        return {
            "status": "started",
            "session": self.review_session,
            "total_items": len(self.hitl_items)
        }
    
    def get_current_item(self) -> Optional[HITLItem]:
        """Get the current item for review."""
        if not self.review_session or self.review_session["current_item"] >= len(self.hitl_items):
            return None
        return self.hitl_items[self.review_session["current_item"]]
    
    def review_item(self, decision: str, notes: str = "") -> Dict[str, Any]:
        """Process a review decision for the current item."""
        if not self.review_session:
            return {"status": "error", "message": "No active review session"}
        
        current_idx = self.review_session["current_item"]
        if current_idx >= len(self.hitl_items):
            return {"status": "error", "message": "No more items to review"}
        
        item = self.hitl_items[current_idx]
        
        # Validate decision
        if decision.lower() not in ['approve', 'reject', 'modify']:
            return {"status": "error", "message": "Invalid decision. Use 'approve', 'reject', or 'modify'"}
        
        # Update item - fix status mapping
        if decision.lower() == "approve":
            item.status = "approved"
        elif decision.lower() == "reject":
            item.status = "rejected"
        else:
            item.status = "modified"
            
        item.reviewer_notes = notes
        item.reviewed_at = datetime.now().isoformat()
        item.reviewer = self.review_session["reviewer"]
        
        # Update session
        self.review_session["items_reviewed"] += 1
        self.review_session["current_item"] += 1
        
        # Check if session complete
        if self.review_session["current_item"] >= len(self.hitl_items):
            self.review_session["completed_at"] = datetime.now().isoformat()
            return {
                "status": "session_complete",
                "item_decision": item.status,
                "total_reviewed": self.review_session["items_reviewed"]
            }
        
        return {
            "status": "item_reviewed",
            "item_decision": item.status,
            "remaining": len(self.hitl_items) - self.review_session["current_item"]
        }
    
    def get_review_summary(self) -> Dict[str, Any]:
        """Get summary of HITL review results."""
        if not self.hitl_items:
            return {"total_items": 0}
        
        summary = {
            "total_items": len(self.hitl_items),
            "approved": len([i for i in self.hitl_items if i.status == "approved"]),
            "rejected": len([i for i in self.hitl_items if i.status == "rejected"]),
            "modified": len([i for i in self.hitl_items if i.status == "modified"]),
            "pending": len([i for i in self.hitl_items if i.status == "pending"]),
            "total_impact": sum([abs(i.amount) for i in self.hitl_items if i.status == "approved"]),
            "items": []
        }
        
        for item in self.hitl_items:
            summary["items"].append({
                "id": item.id,
                "type": item.type,
                "amount": item.amount,
                "status": item.status,
                "reviewer_notes": item.reviewer_notes
            })
        
        return summary
    
    def export_audit_trail(self) -> Dict[str, Any]:
        """Export complete audit trail for compliance."""
        return {
            "review_session": self.review_session,
            "items": [
                {
                    "id": item.id,
                    "type": item.type,
                    "amount": item.amount,
                    "description": item.description,
                    "ai_recommendation": item.ai_recommendation,
                    "confidence": item.confidence,
                    "status": item.status,
                    "reviewer": item.reviewer,
                    "reviewed_at": item.reviewed_at,
                    "reviewer_notes": item.reviewer_notes,
                    "supporting_evidence_count": len(item.supporting_evidence)
                }
                for item in self.hitl_items
            ],
            "exported_at": datetime.now().isoformat()
        }
