"""
Data quality validation module for R2R financial close system.
Ensures data integrity and consistency across all outputs.
"""
from typing import Dict, List, Any, Optional
import json
from pathlib import Path


def validate_amount_rationale_consistency(exceptions: List[Dict[str, Any]]) -> List[str]:
    """Validate that amounts in exceptions match their AI rationales."""
    issues = []
    
    for exc in exceptions:
        amount = exc.get("amount", 0.0)
        rationale = exc.get("ai_rationale", "")
        
        if amount == 0.0 and "$" in rationale:
            # Extract amount from rationale
            import re
            amounts_in_rationale = re.findall(r'\$([0-9,]+\.?\d*)', rationale)
            if amounts_in_rationale:
                rationale_amount = amounts_in_rationale[0].replace(',', '')
                try:
                    if float(rationale_amount) > 0:
                        issues.append(f"Amount mismatch: record shows $0 but rationale mentions ${rationale_amount}")
                except ValueError:
                    pass
    
    return issues


def validate_ai_output_completeness(ai_cache_path: Path) -> List[str]:
    """Validate that AI outputs are not empty when they should contain data."""
    issues = []
    
    if not ai_cache_path.exists():
        return ["AI cache file does not exist"]
    
    try:
        with ai_cache_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        # Check for empty narratives when citations exist
        narratives = data.get("narratives", [])
        citations = data.get("citations", [])
        
        if not narratives and any(c for c in citations if c is not None):
            issues.append("AI output is empty despite having valid citations")
        
        # Check for null citations
        null_citations = sum(1 for c in citations if c is None)
        if null_citations > 0:
            issues.append(f"Found {null_citations} null citations out of {len(citations)}")
            
    except Exception as e:
        issues.append(f"Failed to validate AI output: {e}")
    
    return issues


def validate_forensic_labeling_consistency(data: Dict[str, Any]) -> List[str]:
    """Validate consistent use of forensic labels across the system."""
    issues = []
    
    # Check for mixed labeling in rationales
    rationales = []
    
    # Extract rationales from different sources
    if "exceptions" in data:
        for exc in data["exceptions"]:
            if "ai_rationale" in exc:
                rationales.append(exc["ai_rationale"])
    
    if "rows" in data:
        for row in data["rows"]:
            if "ai_narrative" in row:
                rationales.append(row["ai_narrative"])
    
    # Count label types
    det_count = sum(1 for r in rationales if "[DET]" in r)
    forensic_count = sum(1 for r in rationales if "[FORENSIC]" in r)
    ai_count = sum(1 for r in rationales if "[AI]" in r and "[AI][WARN]" not in r)
    
    if det_count > 0 and forensic_count > 0:
        issues.append(f"Mixed deterministic labeling: {det_count} [DET] and {forensic_count} [FORENSIC] labels")
    
    if ai_count > 0:
        # Check if these are truly AI-generated or hardcoded
        for rationale in rationales:
            if "[AI]" in rationale and ("variance vs" in rationale or "Cites entity=" in rationale):
                issues.append("Found [AI] label in deterministic content")
    
    return issues


def validate_exception_completeness(data: Dict[str, Any]) -> List[str]:
    """Validate that expected exceptions are present based on data patterns."""
    issues = []
    
    exceptions = data.get("exceptions", [])
    
    # Check for AR reconciliation with zero exceptions (likely a bug)
    if "ar_reconciliation" in str(data) and len(exceptions) == 0:
        # This could be valid, but flag for review
        issues.append("AR reconciliation shows zero exceptions - verify this is correct")
    
    # Check for missing required fields in exceptions
    for i, exc in enumerate(exceptions):
        required_fields = ["entity", "reason", "amount"]
        missing_fields = [f for f in required_fields if f not in exc or exc[f] is None]
        if missing_fields:
            issues.append(f"Exception {i} missing required fields: {missing_fields}")
    
    return issues


def run_data_quality_checks(run_dir: Path) -> Dict[str, List[str]]:
    """Run comprehensive data quality checks on a run directory."""
    all_issues = {}
    
    # Check all JSON files in the run directory
    for json_file in run_dir.glob("*.json"):
        try:
            with json_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            file_issues = []
            
            # Run validation checks
            file_issues.extend(validate_amount_rationale_consistency(data.get("exceptions", [])))
            file_issues.extend(validate_forensic_labeling_consistency(data))
            file_issues.extend(validate_exception_completeness(data))
            
            if file_issues:
                all_issues[json_file.name] = file_issues
                
        except Exception as e:
            all_issues[json_file.name] = [f"Failed to validate file: {e}"]
    
    # Check AI cache files
    ai_cache_dir = run_dir / "ai_cache"
    if ai_cache_dir.exists():
        for ai_file in ai_cache_dir.glob("*.json"):
            try:
                ai_issues = validate_ai_output_completeness(ai_file)
                if ai_issues:
                    all_issues[f"ai_cache/{ai_file.name}"] = ai_issues
            except Exception as e:
                all_issues[f"ai_cache/{ai_file.name}"] = [f"Failed to validate AI file: {e}"]
    
    return all_issues
