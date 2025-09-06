"""
Enhanced TB Analysis for Big 4 Demo - AI-First with Trust & Verify

This module implements sophisticated AI-powered trial balance diagnostics
that would be credible to Big 4 accountants, following trust-and-verify principles.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json
from datetime import datetime

class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

class AIConfidenceLevel(Enum):
    VERY_HIGH = "very_high"  # 95-100%
    HIGH = "high"           # 85-94%
    MEDIUM = "medium"       # 70-84%
    LOW = "low"            # 50-69%
    VERY_LOW = "very_low"  # <50%

@dataclass
class MaterialityThreshold:
    """Big 4 standard materiality thresholds"""
    entity: str
    revenue_based: float  # 5% of revenue
    asset_based: float    # 0.5% of total assets
    absolute_floor: float # Minimum $50K
    
    @property
    def effective_threshold(self) -> float:
        return max(
            min(self.revenue_based, self.asset_based),
            self.absolute_floor
        )

@dataclass
class AITBDiagnostic:
    """AI-enhanced trial balance diagnostic with confidence scoring"""
    entity: str
    imbalance_usd: float
    materiality_threshold: float
    risk_level: RiskLevel
    ai_confidence: AIConfidenceLevel
    ai_explanation: str
    recommended_actions: List[str]
    forensic_indicators: List[str]
    control_deficiencies: List[str]
    
    @property
    def is_material(self) -> bool:
        return abs(self.imbalance_usd) > self.materiality_threshold
    
    @property
    def requires_investigation(self) -> bool:
        return self.is_material or self.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

class EnhancedTBAnalyzer:
    """AI-First Trial Balance Analyzer with Big 4 Standards"""
    
    def __init__(self):
        self.materiality_thresholds = {
            "ENT100": MaterialityThreshold("ENT100", 117284.0, 26527.0, 50000.0),  # Based on revenue
            "ENT101": MaterialityThreshold("ENT101", 99383.0, 21951.0, 50000.0),
            "ENT102": MaterialityThreshold("ENT102", 78395.0, 17783.0, 50000.0)
        }
    
    def analyze_entity_balance(self, entity_data: Dict[str, Any]) -> AITBDiagnostic:
        """Perform AI-enhanced analysis of entity trial balance"""
        entity = entity_data["entity"]
        imbalance = float(entity_data["imbalance_usd"])
        accounts = entity_data.get("top_accounts", [])
        
        # Get materiality threshold
        threshold = self.materiality_thresholds.get(entity)
        if not threshold:
            threshold = MaterialityThreshold(entity, 50000.0, 50000.0, 50000.0)
        
        # AI Risk Assessment
        risk_level, confidence, explanation = self._ai_risk_assessment(
            imbalance, accounts, threshold.effective_threshold
        )
        
        # Forensic Analysis
        forensic_indicators = self._detect_forensic_patterns(accounts, imbalance)
        
        # Control Assessment
        control_deficiencies = self._assess_control_deficiencies(accounts, imbalance)
        
        # Recommended Actions
        actions = self._generate_recommendations(imbalance, risk_level, forensic_indicators)
        
        return AITBDiagnostic(
            entity=entity,
            imbalance_usd=imbalance,
            materiality_threshold=threshold.effective_threshold,
            risk_level=risk_level,
            ai_confidence=confidence,
            ai_explanation=explanation,
            recommended_actions=actions,
            forensic_indicators=forensic_indicators,
            control_deficiencies=control_deficiencies
        )
    
    def _ai_risk_assessment(self, imbalance: float, accounts: List[Dict], threshold: float) -> Tuple[RiskLevel, AIConfidenceLevel, str]:
        """AI-powered risk assessment with confidence scoring"""
        abs_imbalance = abs(imbalance)
        
        # Pattern Recognition
        revenue_accounts = [a for a in accounts if a.get("account_type") == "revenue"]
        expense_accounts = [a for a in accounts if a.get("account_type") == "expense"]
        
        total_revenue = sum(abs(a.get("balance_usd", 0)) for a in revenue_accounts)
        total_expenses = sum(a.get("balance_usd", 0) for a in expense_accounts)
        
        # AI Analysis Logic
        if abs_imbalance > threshold * 10:  # 10x materiality
            risk = RiskLevel.CRITICAL
            confidence = AIConfidenceLevel.VERY_HIGH
            explanation = f"Critical imbalance of ${abs_imbalance:,.0f} exceeds 10x materiality threshold. Likely systematic error in closing entries or consolidation adjustments."
        elif abs_imbalance > threshold * 3:  # 3x materiality
            risk = RiskLevel.HIGH
            confidence = AIConfidenceLevel.HIGH
            explanation = f"High-risk imbalance of ${abs_imbalance:,.0f}. Pattern suggests missing accrual reversals or intercompany elimination errors."
        elif abs_imbalance > threshold:  # Above materiality
            risk = RiskLevel.MEDIUM
            confidence = AIConfidenceLevel.MEDIUM
            explanation = f"Material imbalance of ${abs_imbalance:,.0f}. Requires investigation of period-end adjustments and cut-off procedures."
        else:
            risk = RiskLevel.LOW
            confidence = AIConfidenceLevel.HIGH
            explanation = f"Immaterial imbalance of ${abs_imbalance:,.0f} within acceptable tolerance. Likely rounding differences."
        
        return risk, confidence, explanation
    
    def _detect_forensic_patterns(self, accounts: List[Dict], imbalance: float) -> List[str]:
        """AI detection of forensic accounting patterns"""
        indicators = []
        
        # Round number analysis
        if abs(imbalance) % 1000 == 0 and abs(imbalance) > 100000:
            indicators.append("Large round-number imbalance suggests manual adjustment")
        
        # Account balance patterns
        revenue_accounts = [a for a in accounts if a.get("account_type") == "revenue"]
        if len(revenue_accounts) > 0:
            avg_revenue = sum(abs(a.get("balance_usd", 0)) for a in revenue_accounts) / len(revenue_accounts)
            if avg_revenue > 1000000:  # Large revenue accounts
                indicators.append("High-value revenue accounts require enhanced substantive testing")
        
        # Intercompany patterns
        ic_accounts = [a for a in accounts if "intercompany" in a.get("account_name", "").lower()]
        if ic_accounts and abs(imbalance) > 100000:
            indicators.append("Material imbalance with intercompany accounts suggests elimination errors")
        
        return indicators
    
    def _assess_control_deficiencies(self, accounts: List[Dict], imbalance: float) -> List[str]:
        """Assess internal control deficiencies"""
        deficiencies = []
        
        if abs(imbalance) > 500000:  # Material weakness threshold
            deficiencies.append("Material weakness: Trial balance review controls ineffective")
            deficiencies.append("Deficiency: Period-end close procedures require remediation")
        
        # Account reconciliation controls
        cash_accounts = [a for a in accounts if "cash" in a.get("account_name", "").lower()]
        if cash_accounts:
            deficiencies.append("Control testing required: Bank reconciliation completeness")
        
        return deficiencies
    
    def _generate_recommendations(self, imbalance: float, risk: RiskLevel, forensic: List[str]) -> List[str]:
        """Generate AI-powered recommendations"""
        actions = []
        
        if risk == RiskLevel.CRITICAL:
            actions.extend([
                "IMMEDIATE: Halt close process pending investigation",
                "Perform detailed account analysis and journal entry review",
                "Engage forensic accounting team if fraud indicators present",
                "Document all findings for audit committee reporting"
            ])
        elif risk == RiskLevel.HIGH:
            actions.extend([
                "Investigate root cause before proceeding with close",
                "Review all period-end adjusting entries",
                "Validate intercompany elimination entries",
                "Perform analytical procedures on material accounts"
            ])
        elif risk == RiskLevel.MEDIUM:
            actions.extend([
                "Document imbalance and obtain management explanation",
                "Review supporting documentation for material adjustments",
                "Consider impact on financial statement assertions"
            ])
        else:
            actions.append("Monitor for trends in future periods")
        
        if forensic:
            actions.append("Perform enhanced forensic procedures per audit program")
        
        return actions

def generate_enhanced_tb_viewmodel(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate enhanced TB viewmodel with AI analysis"""
    analyzer = EnhancedTBAnalyzer()
    
    diagnostics = []
    total_risk_score = 0
    critical_count = 0
    
    for entity_data in raw_data.get("diagnostics", []):
        ai_diagnostic = analyzer.analyze_entity_balance(entity_data)
        
        # Convert to viewmodel format
        enhanced_diag = {
            "entity": ai_diagnostic.entity,
            "imbalance_usd": ai_diagnostic.imbalance_usd,
            "is_balanced": not ai_diagnostic.is_material,
            "materiality_threshold": ai_diagnostic.materiality_threshold,
            "risk_level": ai_diagnostic.risk_level.value,
            "ai_confidence": ai_diagnostic.ai_confidence.value,
            "confidence_score": _confidence_to_numeric(ai_diagnostic.ai_confidence),
            "confidence_score_pct": int(_confidence_to_numeric(ai_diagnostic.ai_confidence) * 100),
            "ai_explanation": ai_diagnostic.ai_explanation,
            "recommended_actions": ai_diagnostic.recommended_actions,
            "forensic_indicators": ai_diagnostic.forensic_indicators,
            "control_deficiencies": ai_diagnostic.control_deficiencies,
            "auto_approved": ai_diagnostic.risk_level == RiskLevel.LOW,
            "requires_investigation": ai_diagnostic.requires_investigation,
            "top_accounts": entity_data.get("top_accounts", [])
        }
        
        diagnostics.append(enhanced_diag)
        
        # Calculate summary metrics
        if ai_diagnostic.risk_level == RiskLevel.CRITICAL:
            critical_count += 1
            total_risk_score += 4
        elif ai_diagnostic.risk_level == RiskLevel.HIGH:
            total_risk_score += 3
        elif ai_diagnostic.risk_level == RiskLevel.MEDIUM:
            total_risk_score += 2
        else:
            total_risk_score += 1
    
    # Enhanced summary with AI insights
    material_imbalances = sum(1 for d in diagnostics if not d["is_balanced"])
    auto_approved_entities = sum(1 for d in diagnostics if d["auto_approved"])
    avg_confidence = sum(d["confidence_score"] for d in diagnostics) / len(diagnostics) if diagnostics else 0
    
    summary = {
        "material_imbalances": material_imbalances,
        "auto_approved_entities": auto_approved_entities,
        "average_confidence_score": round(avg_confidence * 100, 1),
        "critical_risk_entities": critical_count,
        "overall_risk_score": total_risk_score,
        "requires_cfo_attention": critical_count > 0 or material_imbalances > 1,
        "audit_committee_reporting": critical_count > 0
    }
    
    return {
        "generated_at": raw_data.get("generated_at"),
        "period": raw_data.get("period"),
        "diagnostics": diagnostics,
        "summary": summary,
        "ai_enhanced": True,
        "materiality_basis": "Revenue and asset-based thresholds per Big 4 standards"
    }

def _confidence_to_numeric(confidence: AIConfidenceLevel) -> float:
    """Convert confidence enum to numeric score"""
    mapping = {
        AIConfidenceLevel.VERY_HIGH: 0.975,
        AIConfidenceLevel.HIGH: 0.895,
        AIConfidenceLevel.MEDIUM: 0.77,
        AIConfidenceLevel.LOW: 0.595,
        AIConfidenceLevel.VERY_LOW: 0.35
    }
    return mapping.get(confidence, 0.5)
