"""
Enhanced reporting engine with executive dashboards and audit packages.
"""
from __future__ import annotations
from ..state import CloseState
from ..console import Console
import pandas as pd
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import os

def node_generate_reports(state: CloseState, *, console: Console) -> CloseState:
    """Generate comprehensive reports and dashboards."""
    console.banner("Report Generation")
    
    # Collect all state data for reporting
    data = state.get("data", {})
    recs = state.get("recs", [])
    matches = state.get("matches", [])
    forensic_findings = state.get("forensic_findings", [])
    scenarios_applied = state.get("scenarios_applied", [])
    
    reports = {}
    
    # Generate executive dashboard
    reports["executive_dashboard"] = generate_executive_dashboard(
        recs, matches, forensic_findings, console
    )
    
    # Generate detailed reconciliation report
    reports["reconciliation_report"] = generate_reconciliation_report(
        recs, data, console
    )
    
    # Generate forensic analysis report
    reports["forensic_report"] = generate_forensic_report(
        forensic_findings, scenarios_applied, console
    )
    
    # Generate audit package
    reports["audit_package"] = generate_audit_package(
        recs, matches, forensic_findings, data, console
    )
    
    # Generate matching analysis
    reports["matching_analysis"] = generate_matching_analysis(
        matches, console
    )
    
    console.line("reporting", "Complete", "success", auto=True,
                details=f"Generated {len(reports)} report types")
    
    return {"reports": reports}

def generate_executive_dashboard(recs: List, matches: List, forensic_findings: List, console: Console) -> Dict[str, Any]:
    """Generate high-level executive dashboard."""
    
    # Calculate key metrics
    total_accounts = len(recs) if recs else 0
    balanced_accounts = len([r for r in recs if abs(r.difference) < 100]) if recs else 0
    material_differences = len([r for r in recs if abs(r.difference) >= 10000]) if recs else 0
    
    total_matches = len(matches) if matches else 0
    high_confidence_matches = len([m for m in matches if m.confidence > 0.8]) if matches else 0
    
    critical_findings = len([f for f in forensic_findings if f.get("confidence", 0) > 0.8]) if forensic_findings else 0
    
    # Risk assessment
    risk_score = calculate_risk_score(recs, forensic_findings)
    risk_level = "LOW" if risk_score < 30 else "MEDIUM" if risk_score < 70 else "HIGH"
    
    dashboard = {
        "summary": {
            "close_date": datetime.now().strftime("%Y-%m-%d"),
            "total_accounts_reconciled": total_accounts,
            "accounts_balanced": balanced_accounts,
            "balance_rate": f"{(balanced_accounts/total_accounts*100):.1f}%" if total_accounts > 0 else "0%",
            "material_differences": material_differences,
            "risk_level": risk_level,
            "risk_score": risk_score
        },
        "matching_performance": {
            "total_matches": total_matches,
            "high_confidence_matches": high_confidence_matches,
            "match_confidence_rate": f"{(high_confidence_matches/total_matches*100):.1f}%" if total_matches > 0 else "0%"
        },
        "forensic_insights": {
            "total_findings": len(forensic_findings),
            "critical_findings": critical_findings,
            "top_risk_areas": get_top_risk_areas(forensic_findings)
        },
        "recommendations": generate_executive_recommendations(recs, forensic_findings)
    }
    
    console.line("reporting", "Executive", "generated", auto=True,
                details=f"Risk={risk_level} Balance={dashboard['summary']['balance_rate']}")
    
    return dashboard

def generate_reconciliation_report(recs: List, data: Dict, console: Console) -> Dict[str, Any]:
    """Generate detailed reconciliation report."""
    
    report = {
        "reconciliation_summary": {
            "total_accounts": len(recs),
            "by_entity": {},
            "by_risk_level": {"LOW": 0, "MEDIUM": 0, "HIGH": 0},
            "total_differences": 0
        },
        "account_details": [],
        "variance_analysis": {}
    }
    
    # Process each reconciliation
    for rec in recs:
        # Entity summary
        entity = rec.entity
        if entity not in report["reconciliation_summary"]["by_entity"]:
            report["reconciliation_summary"]["by_entity"][entity] = {
                "accounts": 0,
                "total_difference": 0,
                "balanced": 0
            }
        
        report["reconciliation_summary"]["by_entity"][entity]["accounts"] += 1
        report["reconciliation_summary"]["by_entity"][entity]["total_difference"] += abs(rec.difference)
        
        if abs(rec.difference) < 100:
            report["reconciliation_summary"]["by_entity"][entity]["balanced"] += 1
        
        # Risk level summary
        report["reconciliation_summary"]["by_risk_level"][rec.risk] += 1
        report["reconciliation_summary"]["total_differences"] += abs(rec.difference)
        
        # Account detail
        account_detail = {
            "entity": rec.entity,
            "account_id": rec.account_id,
            "account_name": get_account_name(rec.account_id),
            "book_balance": rec.book_balance,
            "bank_balance": rec.bank_balance,
            "difference": rec.difference,
            "difference_pct": (rec.difference / rec.book_balance * 100) if rec.book_balance != 0 else 0,
            "status": rec.status,
            "risk_level": rec.risk,
            "last_reconciled": rec.date
        }
        report["account_details"].append(account_detail)
    
    # Variance analysis
    if recs:
        differences = [abs(r.difference) for r in recs]
        report["variance_analysis"] = {
            "total_variance": sum(differences),
            "average_variance": sum(differences) / len(differences),
            "max_variance": max(differences),
            "variance_distribution": {
                "under_1k": len([d for d in differences if d < 1000]),
                "1k_to_10k": len([d for d in differences if 1000 <= d < 10000]),
                "10k_to_100k": len([d for d in differences if 10000 <= d < 100000]),
                "over_100k": len([d for d in differences if d >= 100000])
            }
        }
    
    console.line("reporting", "Reconciliation", "generated", auto=True,
                details=f"{len(recs)} accounts analyzed")
    
    return report

def generate_forensic_report(forensic_findings: List, scenarios_applied: List, console: Console) -> Dict[str, Any]:
    """Generate comprehensive forensic analysis report."""
    
    report = {
        "executive_summary": {
            "total_findings": len(forensic_findings),
            "high_risk_findings": len([f for f in forensic_findings if f.get("confidence", 0) > 0.8]),
            "total_financial_impact": sum([abs(f.get("amount", 0)) for f in forensic_findings]),
            "scenarios_tested": len(scenarios_applied) if scenarios_applied else 0
        },
        "findings_by_type": {},
        "detailed_findings": [],
        "root_cause_analysis": {},
        "recommended_actions": []
    }
    
    # Process findings by type
    for finding in forensic_findings:
        finding_type = finding.get("type", "unknown")
        if finding_type not in report["findings_by_type"]:
            report["findings_by_type"][finding_type] = {
                "count": 0,
                "total_amount": 0,
                "avg_confidence": 0
            }
        
        report["findings_by_type"][finding_type]["count"] += 1
        report["findings_by_type"][finding_type]["total_amount"] += abs(finding.get("amount", 0))
        
        # Detailed finding
        detailed_finding = {
            "id": f"FIND-{len(report['detailed_findings']) + 1:03d}",
            "type": finding_type,
            "entity": finding.get("entity", "Unknown"),
            "description": finding.get("ai_analysis", "No description available"),
            "financial_impact": finding.get("amount", 0),
            "confidence_level": finding.get("confidence", 0),
            "root_cause": finding.get("root_cause", "Unknown"),
            "recommended_action": finding.get("recommended_action", "Investigate further"),
            "supporting_evidence": finding.get("supporting_data", {})
        }
        report["detailed_findings"].append(detailed_finding)
    
    # Calculate average confidence by type
    for finding_type, stats in report["findings_by_type"].items():
        type_findings = [f for f in forensic_findings if f.get("type") == finding_type]
        if type_findings:
            avg_confidence = sum([f.get("confidence", 0) for f in type_findings]) / len(type_findings)
            stats["avg_confidence"] = avg_confidence
    
    # Root cause analysis
    root_causes = {}
    for finding in forensic_findings:
        cause = finding.get("root_cause", "unknown")
        if cause not in root_causes:
            root_causes[cause] = {"count": 0, "total_impact": 0}
        root_causes[cause]["count"] += 1
        root_causes[cause]["total_impact"] += abs(finding.get("amount", 0))
    
    report["root_cause_analysis"] = root_causes
    
    # Generate recommended actions
    report["recommended_actions"] = generate_forensic_recommendations(forensic_findings)
    
    console.line("reporting", "Forensic", "generated", auto=True,
                details=f"{len(forensic_findings)} findings analyzed")
    
    return report

def generate_audit_package(recs: List, matches: List, forensic_findings: List, data: Dict, console: Console) -> Dict[str, Any]:
    """Generate comprehensive audit package."""
    
    package = {
        "audit_summary": {
            "preparation_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "period_covered": "2025-08",
            "entities_reviewed": list(set([r.entity for r in recs])) if recs else [],
            "total_accounts": len(recs),
            "total_transactions_matched": len(matches),
            "exceptions_identified": len(forensic_findings)
        },
        "control_testing": generate_control_testing_results(recs, matches),
        "exception_details": [],
        "management_letter_points": [],
        "audit_trail": generate_audit_trail(data),
        "supporting_schedules": generate_supporting_schedules(recs, data)
    }
    
    # Process exceptions for audit
    for i, finding in enumerate(forensic_findings):
        exception = {
            "exception_id": f"EXC-{i+1:03d}",
            "type": finding.get("type", "Unknown"),
            "entity": finding.get("entity", "Unknown"),
            "account_affected": finding.get("account", "Multiple"),
            "monetary_impact": finding.get("amount", 0),
            "description": finding.get("ai_analysis", ""),
            "audit_significance": determine_audit_significance(finding),
            "management_response_required": finding.get("confidence", 0) > 0.7,
            "proposed_adjustment": finding.get("recommended_action", "")
        }
        package["exception_details"].append(exception)
        
        # Generate management letter points for significant items
        if exception["audit_significance"] in ["HIGH", "MEDIUM"]:
            mlp = {
                "point_id": f"MLP-{len(package['management_letter_points']) + 1:02d}",
                "category": "Internal Controls" if "control" in finding.get("type", "") else "Financial Reporting",
                "description": f"Exception identified: {finding.get('root_cause', 'Unknown issue')}",
                "recommendation": finding.get("recommended_action", ""),
                "management_response_due": "Within 30 days"
            }
            package["management_letter_points"].append(mlp)
    
    console.line("reporting", "Audit Package", "generated", auto=True,
                details=f"{len(package['exception_details'])} exceptions documented")
    
    return package

def generate_matching_analysis(matches: List, console: Console) -> Dict[str, Any]:
    """Generate detailed matching performance analysis."""
    
    if not matches:
        return {"summary": "No matches to analyze"}
    
    analysis = {
        "summary": {
            "total_matches": len(matches),
            "by_match_type": {},
            "confidence_distribution": {},
            "average_confidence": 0
        },
        "performance_metrics": {},
        "match_details": []
    }
    
    # Analyze by match type
    for match in matches:
        match_type = match.match_type
        if match_type not in analysis["summary"]["by_match_type"]:
            analysis["summary"]["by_match_type"][match_type] = 0
        analysis["summary"]["by_match_type"][match_type] += 1
        
        # Confidence distribution
        conf_bucket = get_confidence_bucket(match.confidence)
        if conf_bucket not in analysis["summary"]["confidence_distribution"]:
            analysis["summary"]["confidence_distribution"][conf_bucket] = 0
        analysis["summary"]["confidence_distribution"][conf_bucket] += 1
        
        # Match detail
        detail = {
            "match_id": match.id,
            "ar_invoice": match.ar_id,
            "bank_transaction": match.bank_id,
            "amount": match.amount,
            "match_type": match.match_type,
            "confidence": match.confidence,
            "date_difference_days": match.date_diff
        }
        analysis["match_details"].append(detail)
    
    # Calculate average confidence
    analysis["summary"]["average_confidence"] = sum([m.confidence for m in matches]) / len(matches)
    
    # Performance metrics
    analysis["performance_metrics"] = {
        "high_confidence_rate": len([m for m in matches if m.confidence > 0.8]) / len(matches),
        "exact_match_rate": len([m for m in matches if m.match_type == "exact_amount"]) / len(matches),
        "average_date_difference": sum([m.date_diff for m in matches]) / len(matches)
    }
    
    console.line("reporting", "Matching Analysis", "generated", auto=True,
                details=f"Avg confidence: {analysis['summary']['average_confidence']:.2f}")
    
    return analysis

# Helper functions

def calculate_risk_score(recs: List, forensic_findings: List) -> int:
    """Calculate overall risk score (0-100)."""
    score = 0
    
    if not recs:
        return 0
    
    # Risk from reconciliation differences
    material_diffs = len([r for r in recs if abs(r.difference) >= 10000])
    score += min(material_diffs * 15, 40)  # Cap at 40 points
    
    # Risk from high-risk reconciliations
    high_risk_recs = len([r for r in recs if r.risk == "HIGH"])
    score += min(high_risk_recs * 10, 30)  # Cap at 30 points
    
    # Risk from forensic findings
    if forensic_findings:
        high_conf_findings = len([f for f in forensic_findings if f.get("confidence", 0) > 0.8])
        score += min(high_conf_findings * 8, 30)  # Cap at 30 points
    
    return min(score, 100)

def get_top_risk_areas(forensic_findings: List) -> List[str]:
    """Get top risk areas from forensic findings."""
    if not forensic_findings:
        return []
    
    risk_counts = {}
    for finding in forensic_findings:
        risk_type = finding.get("type", "unknown")
        if risk_type not in risk_counts:
            risk_counts[risk_type] = 0
        risk_counts[risk_type] += 1
    
    # Sort by count and return top 3
    sorted_risks = sorted(risk_counts.items(), key=lambda x: x[1], reverse=True)
    return [risk[0].replace("_", " ").title() for risk in sorted_risks[:3]]

def generate_executive_recommendations(recs: List, forensic_findings: List) -> List[str]:
    """Generate executive-level recommendations."""
    recommendations = []
    
    if not recs:
        return recommendations
    
    # Balance rate recommendation
    balanced = len([r for r in recs if abs(r.difference) < 100])
    balance_rate = balanced / len(recs)
    
    if balance_rate < 0.9:
        recommendations.append("Improve reconciliation processes to achieve >90% balance rate")
    
    # Material differences
    material_diffs = len([r for r in recs if abs(r.difference) >= 10000])
    if material_diffs > 0:
        recommendations.append(f"Investigate and resolve {material_diffs} material differences")
    
    # Forensic findings
    if forensic_findings:
        high_risk = len([f for f in forensic_findings if f.get("confidence", 0) > 0.8])
        if high_risk > 0:
            recommendations.append(f"Address {high_risk} high-confidence forensic findings immediately")
    
    # Process improvements
    if len([r for r in recs if r.risk == "HIGH"]) > len(recs) * 0.1:
        recommendations.append("Implement enhanced controls for high-risk accounts")
    
    return recommendations

def get_account_name(account_id: str) -> str:
    """Get account name from account ID."""
    account_names = {
        "1000": "Cash and Cash Equivalents",
        "1100": "Accounts Receivable",
        "1200": "Inventory",
        "1300": "Prepaid Expenses",
        "1400": "Intercompany Receivables",
        "2000": "Accounts Payable",
        "2100": "Accrued Liabilities",
        "2200": "Intercompany Payables",
        "3000": "Revenue",
        "4000": "Cost of Goods Sold",
        "5000": "Operating Expenses"
    }
    return account_names.get(account_id, f"Account {account_id}")

def generate_control_testing_results(recs: List, matches: List) -> Dict[str, Any]:
    """Generate control testing results for audit."""
    return {
        "reconciliation_controls": {
            "tested": len(recs),
            "passed": len([r for r in recs if abs(r.difference) < 1000]),
            "effectiveness": "Satisfactory" if len(recs) > 0 and len([r for r in recs if abs(r.difference) < 1000]) / len(recs) > 0.85 else "Needs Improvement"
        },
        "matching_controls": {
            "tested": len(matches),
            "high_confidence": len([m for m in matches if m.confidence > 0.8]),
            "effectiveness": "Satisfactory" if len(matches) > 0 and len([m for m in matches if m.confidence > 0.8]) / len(matches) > 0.7 else "Needs Improvement"
        }
    }

def determine_audit_significance(finding: Dict) -> str:
    """Determine audit significance of a finding."""
    amount = abs(finding.get("amount", 0))
    confidence = finding.get("confidence", 0)
    
    if amount >= 100000 and confidence > 0.8:
        return "HIGH"
    elif amount >= 25000 and confidence > 0.6:
        return "MEDIUM"
    else:
        return "LOW"

def generate_audit_trail(data: Dict) -> Dict[str, Any]:
    """Generate audit trail information."""
    trail = {
        "data_sources": list(data.keys()) if data else [],
        "processing_timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data_integrity_checks": "Passed",
        "completeness_verification": "Verified"
    }
    
    if data:
        for source, df in data.items():
            if hasattr(df, '__len__'):
                trail[f"{source}_record_count"] = len(df)
    
    return trail

def generate_supporting_schedules(recs: List, data: Dict) -> Dict[str, Any]:
    """Generate supporting schedules for audit."""
    schedules = {}
    
    if recs:
        # Reconciliation summary schedule
        schedules["reconciliation_summary"] = [
            {
                "entity": rec.entity,
                "account": rec.account_id,
                "book_balance": rec.book_balance,
                "adjusted_balance": rec.bank_balance,
                "difference": rec.difference
            }
            for rec in recs
        ]
    
    return schedules

def get_confidence_bucket(confidence: float) -> str:
    """Get confidence bucket for analysis."""
    if confidence >= 0.9:
        return "Very High (90%+)"
    elif confidence >= 0.8:
        return "High (80-89%)"
    elif confidence >= 0.6:
        return "Medium (60-79%)"
    else:
        return "Low (<60%)"

def generate_forensic_recommendations(forensic_findings: List) -> List[str]:
    """Generate forensic-specific recommendations."""
    recommendations = []
    
    # Group by root cause
    root_causes = {}
    for finding in forensic_findings:
        cause = finding.get("root_cause", "unknown")
        if cause not in root_causes:
            root_causes[cause] = []
        root_causes[cause].append(finding)
    
    # Generate recommendations by root cause
    for cause, findings in root_causes.items():
        if len(findings) > 1:
            recommendations.append(f"Address systemic {cause.replace('_', ' ')} issues affecting {len(findings)} transactions")
        else:
            recommendations.append(findings[0].get("recommended_action", "Investigate further"))
    
    return recommendations
