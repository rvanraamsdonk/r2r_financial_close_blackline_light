"""AI-powered comprehensive close analysis and synthesis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class RiskFinding:
    """Individual risk finding from analysis."""
    area: str
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW
    description: str
    financial_impact: float
    evidence_files: List[str]
    recommended_actions: List[str]


@dataclass
class CrossFunctionalPattern:
    """Pattern detected across multiple functional areas."""
    pattern_type: str
    areas_involved: List[str]
    description: str
    risk_level: str
    evidence: Dict[str, Any]


class AICloseSynthesis:
    """Comprehensive AI analysis of close execution results."""
    
    def __init__(self, output_dir: Path, period: str, entity: str):
        self.output_dir = output_dir
        self.period = period
        self.entity = entity
        self.artifacts = self._discover_artifacts()
        
    def _discover_artifacts(self) -> Dict[str, Path]:
        """Discover all JSON artifacts from the close run."""
        artifacts = {}
        for json_file in self.output_dir.glob("*.json"):
            # Extract module name from filename
            name = json_file.stem
            if name.startswith(('ap_', 'ar_', 'bank_', 'flux_', 'ic_', 'auto_', 'gatekeeping_')):
                module = name.split('_')[0]
                artifacts[module] = json_file
            elif 'reconciliation' in name:
                if 'ap' in name:
                    artifacts['ap'] = json_file
                elif 'ar' in name:
                    artifacts['ar'] = json_file
                elif 'bank' in name:
                    artifacts['bank'] = json_file
                elif 'intercompany' in name:
                    artifacts['ic'] = json_file
        return artifacts
    
    def _load_artifact(self, module: str) -> Optional[Dict[str, Any]]:
        """Load artifact data for a module."""
        if module not in self.artifacts:
            return None
        try:
            with open(self.artifacts[module], 'r') as f:
                return json.load(f)
        except Exception:
            return None
    
    def analyze_risk_concentration(self) -> List[RiskFinding]:
        """Analyze risk concentration across all modules."""
        findings = []
        
        # Load all module data
        modules_data = {}
        for module in ['ap', 'ar', 'bank', 'flux', 'ic', 'auto', 'gatekeeping']:
            data = self._load_artifact(module)
            if data:
                modules_data[module] = data
        
        # Analyze exception concentration
        total_exceptions = 0
        total_financial_impact = 0.0
        high_risk_modules = []
        
        for module, data in modules_data.items():
            exceptions = data.get('exceptions', [])
            exception_count = len(exceptions)
            total_exceptions += exception_count
            
            # Calculate financial impact
            if module == 'flux':
                impact = sum(abs(e.get('amount', 0)) for e in exceptions)
            elif module == 'ic':
                impact = data.get('summary', {}).get('total_diff_abs', 0)
            else:
                impact = data.get('summary', {}).get('total_abs_amount', 0)
            
            total_financial_impact += impact
            
            # Flag high-risk modules
            if exception_count > 10 or impact > 100000:
                high_risk_modules.append({
                    'module': module,
                    'exceptions': exception_count,
                    'impact': impact
                })
        
        # Generate risk finding
        if total_exceptions > 20 or total_financial_impact > 250000:
            severity = "CRITICAL" if total_financial_impact > 1000000 else "HIGH"
            findings.append(RiskFinding(
                area="Exception Concentration",
                severity=severity,
                description=f"High exception concentration detected: {total_exceptions} exceptions across {len(high_risk_modules)} high-risk modules",
                financial_impact=total_financial_impact,
                evidence_files=[str(f) for f in self.artifacts.values()],
                recommended_actions=[
                    "Prioritize investigation of high-impact modules",
                    "Implement enhanced controls for exception-prone areas",
                    "Consider management escalation for material items"
                ]
            ))
        
        return findings
    
    def detect_cross_functional_patterns(self) -> List[CrossFunctionalPattern]:
        """Detect patterns spanning multiple functional areas."""
        patterns = []
        
        # Load relevant data
        ap_data = self._load_artifact('ap')
        ar_data = self._load_artifact('ar')
        bank_data = self._load_artifact('bank')
        
        # Pattern 1: Duplicate payment schemes across AP and Bank
        if ap_data and bank_data:
            ap_duplicates = [e for e in ap_data.get('exceptions', []) 
                           if 'duplicate' in e.get('reason', '').lower()]
            bank_duplicates = [e for e in bank_data.get('exceptions', []) 
                             if 'duplicate' in e.get('reason', '').lower()]
            
            if len(ap_duplicates) > 3 and len(bank_duplicates) > 3:
                patterns.append(CrossFunctionalPattern(
                    pattern_type="Duplicate Payment Scheme",
                    areas_involved=["AP", "Bank"],
                    description=f"Coordinated duplicate patterns: {len(ap_duplicates)} AP duplicates correlate with {len(bank_duplicates)} bank duplicates",
                    risk_level="HIGH",
                    evidence={"ap_duplicates": len(ap_duplicates), "bank_duplicates": len(bank_duplicates)}
                ))
        
        # Pattern 2: Revenue manipulation across AR and period-end timing
        if ar_data:
            ar_exceptions = ar_data.get('exceptions', [])
            channel_stuffing = [e for e in ar_exceptions if 'channel_stuffing' in e.get('reason', '')]
            weekend_revenue = [e for e in ar_exceptions if 'weekend' in e.get('reason', '')]
            
            if len(channel_stuffing) > 2 or len(weekend_revenue) > 2:
                patterns.append(CrossFunctionalPattern(
                    pattern_type="Revenue Manipulation",
                    areas_involved=["AR", "Period-End Controls"],
                    description=f"Revenue timing manipulation detected: {len(channel_stuffing)} channel stuffing + {len(weekend_revenue)} weekend entries",
                    risk_level="CRITICAL",
                    evidence={"channel_stuffing": len(channel_stuffing), "weekend_revenue": len(weekend_revenue)}
                ))
        
        return patterns
    
    def calculate_automation_effectiveness(self) -> Dict[str, Any]:
        """Calculate overall automation effectiveness metrics."""
        total_items = 0
        auto_approved = 0
        total_value = 0.0
        auto_value = 0.0
        
        # Aggregate across all modules
        for module in ['ap', 'ar', 'bank', 'ic', 'auto']:
            data = self._load_artifact(module)
            if not data:
                continue
                
            summary = data.get('summary', {})
            
            # Count items
            exceptions = data.get('exceptions', [])
            total_items += len(exceptions)
            
            # Count auto-approved
            auto_count = summary.get('auto_approved_count', 0)
            auto_approved += auto_count
            
            # Value calculations
            if module == 'auto':
                # Auto journal engine
                auto_value += summary.get('auto_journals_total_usd', 0)
            else:
                auto_value += summary.get('auto_approved_total_abs', 0)
                total_value += summary.get('total_abs_amount', 0) or summary.get('total_diff_abs', 0)
        
        automation_rate = (auto_approved / total_items * 100) if total_items > 0 else 0.0
        value_automation = (auto_value / total_value * 100) if total_value > 0 else 0.0
        
        return {
            "total_items_processed": total_items,
            "auto_approved_count": auto_approved,
            "automation_rate_pct": f"{automation_rate:.1f}%",
            "total_financial_exposure": round(total_value, 2),
            "auto_approved_value": round(auto_value, 2),
            "value_automation_pct": f"{value_automation:.1f}%"
        }
    
    def generate_executive_summary(self) -> str:
        """Generate comprehensive executive summary."""
        risk_findings = self.analyze_risk_concentration()
        patterns = self.detect_cross_functional_patterns()
        automation = self.calculate_automation_effectiveness()
        
        # Determine overall risk level
        critical_findings = [f for f in risk_findings if f.severity == "CRITICAL"]
        critical_patterns = [p for p in patterns if p.risk_level == "CRITICAL"]
        
        if critical_findings or critical_patterns:
            overall_risk = "CRITICAL"
        elif any(f.severity == "HIGH" for f in risk_findings) or any(p.risk_level == "HIGH" for p in patterns):
            overall_risk = "HIGH"
        else:
            overall_risk = "MEDIUM"
        
        # Build summary
        summary_parts = [
            f"=== AI CLOSE ANALYSIS SUMMARY - {self.period} ===",
            f"Entity: {self.entity} | Overall Risk: {overall_risk}",
            "",
            "AUTOMATION EFFECTIVENESS:",
            f"  • Processed {automation['total_items_processed']:,} items across all modules",
            f"  • Automation rate: {automation['automation_rate_pct']}% ({automation['auto_approved_count']} auto-approved)",
            f"  • Financial automation: {automation['value_automation_pct']}% (${automation['auto_approved_value']:,.0f} of ${automation['total_financial_exposure']:,.0f})",
            "",
            "KEY RISK FINDINGS:"
        ]
        
        if not risk_findings:
            summary_parts.append("  • No significant risk concentrations detected")
        else:
            for finding in risk_findings:
                summary_parts.append(f"  • {finding.area}: {finding.severity} - ${finding.financial_impact:,.0f}")
                summary_parts.append(f"    {finding.description}")
        
        summary_parts.append("")
        summary_parts.append("CROSS-FUNCTIONAL PATTERNS:")
        
        if not patterns:
            summary_parts.append("  • No cross-functional risk patterns detected")
        else:
            for pattern in patterns:
                summary_parts.append(f"  • {pattern.pattern_type}: {pattern.risk_level}")
                summary_parts.append(f"    {pattern.description}")
        
        summary_parts.append("")
        summary_parts.append("RECOMMENDED ACTIONS:")
        
        # Consolidate all recommended actions
        all_actions = set()
        for finding in risk_findings:
            all_actions.update(finding.recommended_actions)
        
        if critical_findings or critical_patterns:
            all_actions.add("Immediate management escalation required")
            all_actions.add("Consider delaying close until critical issues resolved")
        
        if not all_actions:
            all_actions.add("Continue with standard close procedures")
            all_actions.add("Monitor automation effectiveness trends")
        
        for action in sorted(all_actions):
            summary_parts.append(f"  • {action}")
        
        return "\n".join(summary_parts)
    
    def save_analysis(self) -> Path:
        """Save comprehensive analysis to file."""
        analysis = {
            "generated_at": datetime.now().isoformat(),
            "period": self.period,
            "entity": self.entity,
            "risk_findings": [
                {
                    "area": f.area,
                    "severity": f.severity,
                    "description": f.description,
                    "financial_impact": f.financial_impact,
                    "evidence_files": f.evidence_files,
                    "recommended_actions": f.recommended_actions
                }
                for f in self.analyze_risk_concentration()
            ],
            "cross_functional_patterns": [
                {
                    "pattern_type": p.pattern_type,
                    "areas_involved": p.areas_involved,
                    "description": p.description,
                    "risk_level": p.risk_level,
                    "evidence": p.evidence
                }
                for p in self.detect_cross_functional_patterns()
            ],
            "automation_metrics": self.calculate_automation_effectiveness(),
            "executive_summary": self.generate_executive_summary()
        }
        
        output_file = self.output_dir / f"ai_close_analysis_{self.period.replace('-', '')}.json"
        with open(output_file, 'w') as f:
            json.dump(analysis, f, indent=2)
        
        return output_file
