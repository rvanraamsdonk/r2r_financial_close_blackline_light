#!/usr/bin/env python3
"""
R2R Financial Close Demo Script - Showcasing Advanced Forensic Capabilities
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from r2r.state import CloseState
from r2r.console import Console
from r2r.data.repo import DataRepo
from r2r.agents.ingestion import node_ingest
from r2r.agents.reconciliations import node_reconcile
from r2r.agents.smart_matching import node_smart_match
from r2r.agents.forensics import node_forensics
from r2r.agents.scenario_generator import node_generate_scenarios
from r2r.agents.reporting import node_generate_reports

def main():
    """Run the comprehensive R2R demo with forensic capabilities."""
    console = Console()
    
    # Demo introduction
    console.banner("R2R FINANCIAL CLOSE - ADVANCED FORENSIC DEMO")
    print("🚀 Demonstrating AI-powered financial close automation")
    print("📊 Featuring: Root Cause Analysis, Smart Matching, Executive Dashboards")
    print("🔍 Built for Big 4 audit readiness with comprehensive forensic capabilities")
    print()
    
    # Initialize state
    state = CloseState()
    state["period"] = "2025-08"
    state["entities"] = ["ENT100", "ENT101", "ENT102"]
    
    # Step 1: Data Ingestion with Static Dataset
    console.section("🔄 STEP 1: Loading Static Dataset with Embedded Forensic Scenarios")
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from src.r2r.data.static_loader import StaticDataRepo
    data_repo = StaticDataRepo()
    updated_state = node_ingest(state, data_repo=data_repo, console=console)
    state.update(updated_state)
    
    
    data_summary = state.get("data", {})
    print(f"✅ Loaded {len(data_summary)} data sources:")
    for source, df in data_summary.items():
        if hasattr(df, '__len__'):
            print(f"   • {source.upper()}: {len(df)} records")
    print()
    
    # Step 2: Generate Additional Scenarios for Demo
    print("🎭 STEP 2: Generating Additional Forensic Scenarios")
    updated_state = node_generate_scenarios(state, console=console)
    state.update(updated_state)
    
    scenarios = state.get("scenarios_applied", [])
    if scenarios:
        print(f"✅ Applied {len(scenarios)} additional forensic scenarios:")
        scenario_types = {}
        for scenario in scenarios:
            s_type = scenario.get("type", "unknown")
            scenario_types[s_type] = scenario_types.get(s_type, 0) + 1
        
        for s_type, count in scenario_types.items():
            print(f"   • {s_type.replace('_', ' ').title()}: {count} cases")
    print()
    
    # Step 3: Account Reconciliations
    console.section("⚖️ STEP 3: Performing Account Reconciliations")
    # Add policy for reconciliation
    from src.r2r.policies import POLICY
    state["policy"] = POLICY
    updated_state = node_reconcile(state, console=console)
    state.update(updated_state)
    
    recs = state.get("recs", [])
    if recs:
        balanced = len([r for r in recs if abs(r.diff) < 100])
        material = len([r for r in recs if abs(r.diff) >= 10000])
        print(f"✅ Reconciled {len(recs)} accounts:")
        print(f"   • ✅ Balanced: {balanced} ({balanced/len(recs)*100:.1f}%)")
        print(f"   • ⚠️ Material Differences: {material}")
    print()
    
    # Step 4: Smart AI Matching
    print("🤖 STEP 4: AI-Powered Smart Transaction Matching")
    state = node_smart_match(state, console=console)
    
    matches = state.get("matches", [])
    if matches:
        high_conf = len([m for m in matches if m.confidence > 0.8])
        avg_conf = sum([m.confidence for m in matches]) / len(matches)
        print(f"✅ Matched {len(matches)} transactions:")
        print(f"   • ⭐ High Confidence: {high_conf} ({high_conf/len(matches)*100:.1f}%)")
        print(f"   • 📈 Average Confidence: {avg_conf:.1%}")
    print()
    
    # Step 5: AI Forensic Analysis
    print("🔍 STEP 5: AI-Powered Forensic Root Cause Analysis")
    state = node_forensics(state, console=console)
    
    forensic_findings = state.get("forensic_findings", [])
    console.forensic_findings_display(forensic_findings)
    
    # Step 6: Generate Executive Reports
    print("📊 STEP 6: Generating Executive Dashboards & Audit Packages")
    state = node_generate_reports(state, console=console)
    
    reports = state.get("reports", {})
    
    # Display Executive Dashboard
    if "executive_dashboard" in reports:
        console.executive_dashboard_display(reports["executive_dashboard"])
    
    # Display Matching Analysis
    if "matching_analysis" in reports:
        console.matching_analysis_display(reports["matching_analysis"])
    
    # Display Audit Package Summary
    if "audit_package" in reports:
        console.audit_package_display(reports["audit_package"])
    
    # Demo Summary
    console.banner("DEMO SUMMARY - KEY ACHIEVEMENTS")
    
    print("🎯 ADVANCED CAPABILITIES DEMONSTRATED:")
    print("   ✅ AI Root Cause Detection with confidence scoring")
    print("   ✅ 4-Stage Smart Matching Algorithm (Exact→Fuzzy→Pattern→ML)")
    print("   ✅ Executive Risk Dashboards with KPI tracking")
    print("   ✅ Big 4 Audit-Ready Exception Packages")
    print("   ✅ Configurable Forensic Scenario Generation")
    print()
    
    # Key Metrics Summary
    total_findings = len(forensic_findings)
    critical_findings = len([f for f in forensic_findings if f.get("confidence", 0) > 0.8])
    total_impact = sum([abs(f.get("amount", 0)) for f in forensic_findings])
    
    print("📈 DEMO RESULTS:")
    print(f"   🔍 Forensic Findings: {total_findings} total, {critical_findings} critical")
    print(f"   💰 Financial Impact Identified: ${total_impact:,.0f}")
    print(f"   🤖 AI Matching Performance: {len(matches)} matches, {avg_conf:.1%} avg confidence")
    print(f"   ⚖️ Reconciliation Coverage: {len(recs)} accounts, {balanced/len(recs)*100:.1f}% balanced")
    print()
    
    # Next Steps for Demo Audience
    print("🚀 NEXT STEPS FOR IMPLEMENTATION:")
    print("   1. Review forensic findings and implement recommended actions")
    print("   2. Configure scenario parameters for your specific business")
    print("   3. Integrate with your ERP systems and data sources")
    print("   4. Set up automated reporting for monthly close cycles")
    print("   5. Train your team on the AI-powered insights and dashboards")
    print()
    
    # Export Reports for Demo
    export_demo_reports(reports, console)
    
    console.banner("DEMO COMPLETE - READY FOR BIG 4 PRESENTATION")
    print("🎉 All forensic capabilities successfully demonstrated!")
    print("📁 Reports exported to /tmp/r2r_demo_reports/ for review")
    print("🔗 System ready for enterprise deployment")

def export_demo_reports(reports: dict, console: Console):
    """Export demo reports for audience review."""
    import json
    import os
    
    export_dir = "/tmp/r2r_demo_reports"
    os.makedirs(export_dir, exist_ok=True)
    
    for report_type, report_data in reports.items():
        filename = f"{export_dir}/{report_type}_demo.json"
        with open(filename, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
    
    console.line("demo", "Export", "complete", auto=True, 
                details=f"Reports saved to {export_dir}")

if __name__ == "__main__":
    main()
