from __future__ import annotations
from typing import Optional, List, Dict

class Console:
    def __init__(self): self.step = 0
    def line(self, stage:str, agent:str, action:str, *, ai=False, hitl=False, auto=False, details:Optional[str]=None):
        self.step += 1
        markers = []
        if ai: markers.append("AI")
        if hitl: markers.append("HITL")
        if auto: markers.append("AUTO")
        m = " ".join(markers) if markers else "—"
        d = f" | details={details}" if details else ""
        print(f"STEP {self.step:02d} | {stage.upper()} | AGENT={agent} | {m} | action={action}{d}")

    def banner(self, title: str) -> None:
        """Print a banner."""
        print(f"{'='*80}")
        print(f"{title.upper()}")
        print(f"{'='*80}")
    
    def section(self, title: str) -> None:
        """Print a section header."""
        print(f"\n{title}")
        print(f"{'='*len(title)}")

    def forensic_findings_display(self, findings: List[Dict], title: str = "FORENSIC ANALYSIS RESULTS") -> None:
        """Display forensic findings in a compelling format."""
        self.banner(title)
        
        if not findings:
            print("✅ No forensic issues detected - Clean close!")
            return
        
        # Group by type for better presentation
        by_type = {}
        total_impact = 0
        
        for finding in findings:
            finding_type = finding.get("type", "unknown").replace("_", " ").title()
            if finding_type not in by_type:
                by_type[finding_type] = []
            by_type[finding_type].append(finding)
            total_impact += abs(finding.get("amount", 0))
        
        print(f"🔍 FORENSIC SUMMARY: {len(findings)} findings identified")
        print(f"💰 TOTAL FINANCIAL IMPACT: ${total_impact:,.0f}")
        print()
        
        for finding_type, type_findings in by_type.items():
            print(f"📊 {finding_type.upper()} ({len(type_findings)} items)")
            print("-" * 60)
            
            for finding in type_findings:
                entity = finding.get("entity", "Unknown")
                amount = finding.get("amount", 0)
                confidence = finding.get("confidence", 0)
                root_cause = finding.get("root_cause", "Unknown").replace("_", " ").title()
                
                confidence_icon = "🔴" if confidence > 0.8 else "🟡" if confidence > 0.6 else "⚪"
                
                print(f"  {confidence_icon} {entity}: ${amount:,.0f} - {root_cause}")
                print(f"     Confidence: {confidence:.0%} | Action: {finding.get('recommended_action', 'Investigate')}")
                
                if finding.get("ai_analysis"):
                    analysis = finding["ai_analysis"][:100] + "..." if len(finding["ai_analysis"]) > 100 else finding["ai_analysis"]
                    print(f"     AI Analysis: {analysis}")
                print()

    def executive_dashboard_display(self, dashboard: Dict) -> None:
        """Display executive dashboard with rich visual indicators."""
        self.banner("EXECUTIVE DASHBOARD")
        
        if not isinstance(dashboard, dict):
            print("No dashboard data available")
            return
        
        summary = dashboard.get("summary", {})
        
        # Close Status Overview
        print("📈 CLOSE STATUS OVERVIEW")
        close_date = summary.get("close_date", "2025-08-21")
        risk_level = summary.get("risk_level", "UNKNOWN")
        risk_score = summary.get("risk_score", 0)
        balance_rate = summary.get("balance_rate", 0)
        
        # Risk level with visual indicators
        risk_icon = "🟢" if risk_level == "LOW" else "🟡" if risk_level == "MEDIUM" else "🔴"
        print(f"   Close Date: {close_date}")
        print(f"   Risk Level: {risk_icon} {risk_level} (Score: {risk_score}/100)")
        print(f"   Balance Rate: {balance_rate:.1%} ({summary.get('balanced_accounts', 0)}/{summary.get('total_accounts', 0)} accounts)")
        print()
        
        # Reconciliation Performance
        print("🎯 RECONCILIATION PERFORMANCE")
        print(f"   ✅ Balanced Accounts: {summary.get('balanced_accounts', 0)}")
        print(f"   ⚠️  Material Differences: {summary.get('material_differences', 0)}")
        print(f"   📊 Balance Achievement: {balance_rate:.1%}")
        print()
        
        # AI Matching Performance
        matching = dashboard.get("matching_performance", {})
        print("🤖 AI MATCHING PERFORMANCE")
        print(f"   🔗 Total Matches: {matching.get('total_matches', 0)}")
        print(f"   ⭐ High Confidence: {matching.get('high_confidence', 0)}")
        print(f"   📈 Confidence Rate: {matching.get('avg_confidence', 0):.1%}")
        print()
        
        # Forensic Insights
        forensics = dashboard.get("forensic_summary", {})
        print("🔍 FORENSIC INSIGHTS")
        print(f"   🚨 Total Findings: {forensics.get('total_findings', 0)}")
        print(f"   🔴 Critical Issues: {forensics.get('critical_issues', 0)}")
        print()

    def audit_package_display(self, package: Dict) -> None:
        """Display audit package summary."""
        self.banner("AUDIT PACKAGE SUMMARY")
        
        if not isinstance(package, dict):
            print("No audit package data available")
            return
        
        summary = package.get("summary", {})
        
        print("📋 AUDIT PREPARATION SUMMARY")
        print(f"   Preparation Date: {summary.get('preparation_date', '2025-08-21 15:22:54')}")
        print(f"   Period Covered: {summary.get('period', '2025-08')}")
        print(f"   Entities Reviewed: {summary.get('entities_count', 0)}")
        print(f"   Total Accounts: {summary.get('accounts_count', 0)}")
        print()
        
        exceptions = package.get("exceptions", [])
        print("🔍 EXCEPTION ANALYSIS")
        print(f"   Total Exceptions: {len(exceptions)}")
        
        if exceptions:
            # Group by significance
            high_sig = len([e for e in exceptions if e.get("significance") == "high"])
            medium_sig = len([e for e in exceptions if e.get("significance") == "medium"])
            low_sig = len([e for e in exceptions if e.get("significance") == "low"])
            
            print(f"   🔴 High Significance: {high_sig}")
            print(f"   🟡 Medium Significance: {medium_sig}")
            print(f"   ⚪ Low Significance: {low_sig}")
        print()

    def matching_analysis_display(self, analysis) -> None:
        """Display matching analysis results."""
        self.banner("MATCHING ANALYSIS")
        
        # Handle case where analysis might be a string or dict
        if isinstance(analysis, str):
            print(f"Analysis: {analysis}")
            return
        
        if not isinstance(analysis, dict):
            print("No matching analysis data available")
            return
        
        summary = analysis.get("summary", {})
        print("🔗 MATCHING PERFORMANCE OVERVIEW")
        if isinstance(summary, dict):
            print(f"   Total Matches: {summary.get('total_matches', 0)}")
            print(f"   Average Confidence: {summary.get('avg_confidence', 0):.1%}")
            print(f"   High Confidence Rate: {summary.get('high_confidence_rate', 0):.1%}")
        else:
            print(f"   Summary: {summary}")
        print()
        
        # Confidence distribution
        confidence_dist = analysis.get("confidence_distribution", {})
        if confidence_dist:
            print("📊 CONFIDENCE DISTRIBUTION")
            for bucket, count in confidence_dist.items():
                print(f"   {bucket}: {count} matches")
            print()
        
        # Method performance
        method_perf = analysis.get("method_performance", {})
        if method_perf:
            print("⚙️ MATCHING METHOD PERFORMANCE")
            for method, stats in method_perf.items():
                print(f"   {method.upper()}: {stats.get('count', 0)} matches (avg: {stats.get('avg_confidence', 0):.1%})")
            print()
            print(f"   Avg Date Difference: {method_perf.get('average_date_difference', 0):.1f} days")
            print()
