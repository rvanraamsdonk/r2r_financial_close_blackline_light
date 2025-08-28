#!/usr/bin/env python3
"""
Evidence Coherence Testing Suite
Tests drillthrough, provenance, and evidence linking across all R2R modules.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Tuple
from collections import defaultdict

def load_artifact(run_dir: Path, artifact_name: str) -> Dict[str, Any]:
    """Load a JSON artifact from the run directory."""
    artifact_path = run_dir / f"{artifact_name}.json"
    if not artifact_path.exists():
        return {}
    return json.loads(artifact_path.read_text())

def extract_transaction_ids(data: Any, path: str = "") -> Set[str]:
    """Recursively extract all transaction IDs from data structure."""
    ids = set()
    
    if isinstance(data, dict):
        for key, value in data.items():
            # Standard transaction ID fields
            if key in ["linked_transactions", "transaction_id", "input_row_ids"]:
                if isinstance(value, list):
                    ids.update(value)
                elif isinstance(value, str):
                    ids.add(value)
            # AI-discovered transaction matches
            elif key == "ai_transaction_matches":
                if isinstance(value, list):
                    for match in value:
                        if isinstance(match, dict) and "transaction_id" in match:
                            ids.add(match["transaction_id"])
            # Module-specific transaction ID fields
            elif key in ["bill_id", "bank_txn_id", "invoice_id", "doc_id", "accrual_id", "account"]:
                if isinstance(value, str):
                    ids.add(value)
            else:
                ids.update(extract_transaction_ids(value, f"{path}.{key}"))
    elif isinstance(data, list):
        for i, item in enumerate(data):
            ids.update(extract_transaction_ids(item, f"{path}[{i}]"))
    
    return ids

def test_module_evidence_linking(run_dir: Path) -> Dict[str, Any]:
    """Test evidence linking within each module."""
    results = {}
    
    # Core reconciliation modules
    modules = [
        "ap_reconciliation",
        "ar_reconciliation", 
        "bank_reconciliation",
        "intercompany_reconciliation",
        "accruals",
        "flux_analysis",
        "email_evidence"
    ]
    
    for module in modules:
        artifact = load_artifact(run_dir, f"{module}_run_{run_dir.name.split('_', 1)[1]}")
        if not artifact:
            results[module] = {"status": "missing", "issues": ["Artifact not found"]}
            continue
            
        issues = []
        transaction_ids = extract_transaction_ids(artifact)
        
        # Check for empty transaction references
        if not transaction_ids:
            issues.append("No transaction IDs found")
        
        # Check for malformed IDs
        malformed = [tid for tid in transaction_ids if not tid or len(tid) < 3]
        if malformed:
            issues.append(f"Malformed transaction IDs: {malformed}")
            
        # Module-specific checks
        if module == "email_evidence":
            items = artifact.get("items", [])
            # Check for missing transaction linkages (either linked_transactions or ai_transaction_matches)
            for item in items:
                if "email_id" in item:
                    has_linked = "linked_transactions" in item and item["linked_transactions"]
                    has_ai_matches = "ai_transaction_matches" in item and item["ai_transaction_matches"]
                    if not has_linked and not has_ai_matches:
                        issues.append(f"Email {item['email_id']} missing transaction linkages")
        
        results[module] = {
            "status": "pass" if not issues else "fail",
            "transaction_count": len(transaction_ids),
            "issues": issues,
            "sample_ids": list(transaction_ids)[:5]
        }
    
    return results

def test_cross_module_provenance(run_dir: Path) -> Dict[str, Any]:
    """Test provenance chains between modules."""
    results = {}
    
    # Load all artifacts
    artifacts = {}
    for json_file in run_dir.glob("*.json"):
        if not json_file.name.startswith("ai_cache"):
            artifact_name = json_file.stem.replace(f"_run_{run_dir.name.split('_', 1)[1]}", "")
            artifacts[artifact_name] = json.loads(json_file.read_text())
    
    # Test email evidence → forensic exceptions linkage
    email_evidence = artifacts.get("email_evidence", {})
    email_transaction_ids = set()
    if "email_evidence" in artifacts:
        emails = artifacts["email_evidence"].get("items", [])
        for email in emails:
            # Legacy linked_transactions
            email_transaction_ids.update(email.get("linked_transactions", []))
            # AI-discovered transaction matches
            ai_matches = email.get("ai_transaction_matches", [])
            for match in ai_matches:
                if isinstance(match, dict) and "transaction_id" in match:
                    email_transaction_ids.add(match["transaction_id"])
    
    # Check if email transaction IDs exist in reconciliation modules
    recon_modules = ["ap_reconciliation", "ar_reconciliation", "bank_reconciliation", "intercompany_reconciliation"]
    found_transactions = defaultdict(list)
    
    for module in recon_modules:
        if module in artifacts:
            module_ids = extract_transaction_ids(artifacts[module])
            for email_id in email_transaction_ids:
                if email_id in module_ids:
                    found_transactions[email_id].append(module)
    
    # Test AI citations
    ai_artifacts = {}
    for ai_file in (run_dir / "ai_cache").glob("*.json"):
        ai_name = ai_file.stem.split("_run_")[0]
        ai_artifacts[ai_name] = json.loads(ai_file.read_text())
    
    citation_issues = []
    for ai_name, ai_data in ai_artifacts.items():
        citations = ai_data.get("citations", [])
        for citation in citations:
            if citation is None:
                citation_issues.append(f"{ai_name}: Null citation found")
                continue
            citation_path = Path(citation)
            if not citation_path.exists():
                citation_issues.append(f"{ai_name}: Missing citation {citation}")
    
    results = {
        "email_transaction_coverage": {
            "total_email_transactions": len(email_transaction_ids),
            "found_in_modules": len(found_transactions),
            "coverage_pct": round(len(found_transactions) / max(len(email_transaction_ids), 1) * 100, 1),
            "orphaned_transactions": list(email_transaction_ids - set(found_transactions.keys()))
        },
        "ai_citations": {
            "total_citations": sum(len(ai_data.get("citations", [])) for ai_data in ai_artifacts.values()),
            "broken_citations": len(citation_issues),
            "issues": citation_issues
        }
    }
    
    return results

def test_drillthrough_paths(run_dir: Path) -> Dict[str, Any]:
    """Test bidirectional drillthrough paths."""
    results = {}
    
    # Load key artifacts
    email_evidence = load_artifact(run_dir, f"email_evidence_run_{run_dir.name.split('_', 1)[1]}")
    ap_recon = load_artifact(run_dir, f"ap_reconciliation_run_{run_dir.name.split('_', 1)[1]}")
    
    # Test email → transaction → forensic exception path
    drillthrough_tests = []
    
    if "items" in email_evidence:
        for email in email_evidence["items"][:3]:  # Test first 3 emails
            email_id = email.get("email_id")
            linked_txns = email.get("linked_transactions", [])
            
            for txn_id in linked_txns:
                # Check if transaction exists in AP reconciliation
                found_in_ap = False
                if "exceptions" in ap_recon:
                    for exception in ap_recon["exceptions"]:
                        if exception.get("transaction_id") == txn_id:
                            found_in_ap = True
                            break
                
                drillthrough_tests.append({
                    "email_id": email_id,
                    "transaction_id": txn_id,
                    "found_in_ap": found_in_ap,
                    "path_complete": found_in_ap
                })
    
    successful_paths = sum(1 for test in drillthrough_tests if test["path_complete"])
    
    results = {
        "total_paths_tested": len(drillthrough_tests),
        "successful_paths": successful_paths,
        "success_rate_pct": round(successful_paths / max(len(drillthrough_tests), 1) * 100, 1),
        "failed_paths": [test for test in drillthrough_tests if not test["path_complete"]]
    }
    
    return results

def test_evidence_coherence_end_to_end(run_dir: Path) -> Dict[str, Any]:
    """Comprehensive end-to-end evidence coherence test."""
    print(f"\n=== Evidence Coherence Test: {run_dir.name} ===")
    
    # Module-level tests
    print("\n1. Module Evidence Linking...")
    module_results = test_module_evidence_linking(run_dir)
    
    # Cross-module provenance
    print("2. Cross-Module Provenance...")
    provenance_results = test_cross_module_provenance(run_dir)
    
    # Drillthrough paths
    print("3. Drillthrough Paths...")
    drillthrough_results = test_drillthrough_paths(run_dir)
    
    # Overall assessment
    module_failures = sum(1 for result in module_results.values() if result["status"] == "fail")
    total_modules = len(module_results)
    
    overall_score = 0
    if total_modules > 0:
        overall_score += (total_modules - module_failures) / total_modules * 40  # 40% weight
    
    if provenance_results["email_transaction_coverage"]["coverage_pct"] > 80:
        overall_score += 30  # 30% weight
    
    if drillthrough_results["success_rate_pct"] > 80:
        overall_score += 30  # 30% weight
    
    # Summary
    summary = {
        "overall_score": round(overall_score, 1),
        "module_results": module_results,
        "provenance_results": provenance_results,
        "drillthrough_results": drillthrough_results,
        "recommendations": []
    }
    
    # Generate recommendations
    if module_failures > 0:
        summary["recommendations"].append(f"Fix {module_failures} modules with evidence linking issues")
    
    if provenance_results["email_transaction_coverage"]["coverage_pct"] < 80:
        summary["recommendations"].append("Improve email-to-transaction linkage coverage")
    
    if drillthrough_results["success_rate_pct"] < 80:
        summary["recommendations"].append("Fix broken drillthrough paths")
    
    if provenance_results["ai_citations"]["broken_citations"] > 0:
        summary["recommendations"].append("Fix broken AI citation paths")
    
    return summary

def main():
    """Run evidence coherence tests on latest run."""
    if len(sys.argv) > 1:
        run_path = Path(sys.argv[1])
    else:
        # Find latest run
        out_dir = Path(__file__).parent.parent / "out"
        run_dirs = [d for d in out_dir.iterdir() if d.is_dir() and d.name.startswith("run_")]
        if not run_dirs:
            print("No run directories found")
            return 1
        run_path = max(run_dirs, key=lambda d: d.name)
    
    if not run_path.exists():
        print(f"Run directory not found: {run_path}")
        return 1
    
    results = test_evidence_coherence_end_to_end(run_path)
    
    # Print results
    print(f"\n=== EVIDENCE COHERENCE RESULTS ===")
    print(f"Overall Score: {results['overall_score']}/100")
    
    print(f"\nModule Results:")
    for module, result in results["module_results"].items():
        status_icon = "✅" if result["status"] == "pass" else "❌"
        print(f"  {status_icon} {module}: {result['transaction_count']} transactions")
        if result["issues"]:
            for issue in result["issues"]:
                print(f"    - {issue}")
    
    print(f"\nProvenance Results:")
    coverage = results["provenance_results"]["email_transaction_coverage"]
    print(f"  Email-Transaction Coverage: {coverage['coverage_pct']}% ({coverage['found_in_modules']}/{coverage['total_email_transactions']})")
    
    citations = results["provenance_results"]["ai_citations"]
    print(f"  AI Citations: {citations['broken_citations']} broken out of {citations['total_citations']}")
    
    print(f"\nDrillthrough Results:")
    dt = results["drillthrough_results"]
    print(f"  Success Rate: {dt['success_rate_pct']}% ({dt['successful_paths']}/{dt['total_paths_tested']})")
    
    if results["recommendations"]:
        print(f"\nRecommendations:")
        for rec in results["recommendations"]:
            print(f"  • {rec}")
    
    return 0 if results["overall_score"] >= 80 else 1

if __name__ == "__main__":
    sys.exit(main())
