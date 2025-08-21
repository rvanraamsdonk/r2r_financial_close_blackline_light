"""
AI-powered forensic analysis engine for root cause detection and pattern analysis.
"""
from __future__ import annotations
from ..state import CloseState
from ..console import Console
from ..llm.azure import chat
import pandas as pd
import numpy as np
from typing import Dict, List, Any

def node_forensics(state: CloseState, *, console: Console) -> CloseState:
    """Analyze discrepancies and provide AI-powered root cause analysis."""
    console.banner("Forensic Analysis")
    
    # Get data for analysis
    data = state.get("data", {})
    recs = state.get("recs", [])
    matches = state.get("matches", [])
    
    forensic_findings = []
    
    # Analyze reconciliation discrepancies
    for rec in recs:
        if abs(rec.difference) > 1000:  # Material differences
            finding = analyze_reconciliation_discrepancy(rec, data, console)
            if finding:
                forensic_findings.append(finding)
    
    # Analyze transaction patterns
    if "ar" in data and "bank" in data:
        pattern_findings = analyze_transaction_patterns(data["ar"], data["bank"], console)
        forensic_findings.extend(pattern_findings)
    
    # Analyze duplicate transactions
    if "ap" in data:
        duplicate_findings = analyze_duplicate_transactions(data["ap"], console)
        forensic_findings.extend(duplicate_findings)
    
    return {"forensic_findings": forensic_findings}

def analyze_reconciliation_discrepancy(rec, data: Dict, console: Console) -> Dict[str, Any] | None:
    """Analyze a specific reconciliation discrepancy for root causes."""
    
    # Build context for AI analysis
    context = f"""
    Reconciliation Analysis:
    - Entity: {rec.entity}
    - Account: {rec.account_id}
    - Difference: ${rec.difference:,.2f}
    - Status: {rec.status}
    - Risk Level: {rec.risk}
    """
    
    # Get AI analysis
    prompt = [
        {"role": "system", "content": "You are a forensic accountant analyzing reconciliation discrepancies. Provide concise root cause analysis and recommended actions."},
        {"role": "user", "content": f"Analyze this reconciliation discrepancy and suggest the most likely root cause:\n{context}"}
    ]
    
    ai_analysis = chat(prompt, temperature=0.3, max_tokens=200)
    
    # Determine likely root cause based on patterns
    root_cause = determine_root_cause(rec, data)
    
    finding = {
        "type": "reconciliation_discrepancy",
        "entity": rec.entity,
        "account": rec.account_id,
        "amount": rec.difference,
        "root_cause": root_cause,
        "ai_analysis": ai_analysis or "Analysis unavailable",
        "recommended_action": get_recommended_action(root_cause),
        "confidence": calculate_confidence(rec, data)
    }
    
    console.line("forensics", "Analysis", "complete", ai=True, 
                details=f"{rec.entity} {rec.account_id} root_cause={root_cause}")
    
    return finding

def analyze_transaction_patterns(ar_data: pd.DataFrame, bank_data: pd.DataFrame, console: Console) -> List[Dict[str, Any]]:
    """Analyze transaction patterns for anomalies."""
    findings = []
    
    # Timing analysis - look for cut-off issues
    if not ar_data.empty and not bank_data.empty:
        # Find AR items with payments near period end
        period_end_payments = bank_data[
            (bank_data['date'].str.contains('2025-08-31', na=False)) |
            (bank_data['date'].str.contains('2025-09-01', na=False))
        ]
        
        if not period_end_payments.empty:
            for _, payment in period_end_payments.iterrows():
                # Check if corresponding AR item exists
                matching_ar = ar_data[
                    (abs(ar_data['amount'] - abs(payment['amount'])) < 0.01) &
                    (ar_data['entity'] == payment['entity'])
                ]
                
                if not matching_ar.empty:
                    finding = {
                        "type": "timing_difference",
                        "entity": payment['entity'],
                        "amount": payment['amount'],
                        "root_cause": "cut_off_error",
                        "ai_analysis": "Payment received near period end may indicate cut-off timing issue",
                        "recommended_action": "Review cut-off procedures and consider adjustment entry",
                        "confidence": 0.85,
                        "supporting_data": {
                            "payment_date": payment['date'],
                            "payment_ref": payment.get('reference', ''),
                            "ar_invoice": matching_ar.iloc[0]['invoice_id'] if not matching_ar.empty else None
                        }
                    }
                    findings.append(finding)
                    
                    console.line("forensics", "Pattern", "detected", ai=True,
                               details=f"Timing issue {payment['entity']} ${payment['amount']:,.0f}")
    
    return findings

def analyze_duplicate_transactions(ap_data: pd.DataFrame, console: Console) -> List[Dict[str, Any]]:
    """Analyze AP data for duplicate transactions."""
    findings = []
    
    if ap_data.empty:
        return findings
    
    # Group by vendor and amount to find potential duplicates
    duplicates = ap_data.groupby(['vendor_name', 'amount_usd']).size()
    duplicate_groups = duplicates[duplicates > 1]
    
    for (vendor, amount), count in duplicate_groups.items():
        duplicate_records = ap_data[
            (ap_data['vendor_name'] == vendor) & 
            (ap_data['amount_usd'] == amount)
        ]
        
        # Check if they have different payment references (indicating true duplicates)
        payment_refs = duplicate_records['payment_ref'].dropna().unique()
        if len(payment_refs) > 1:
            finding = {
                "type": "duplicate_transaction",
                "entity": duplicate_records.iloc[0]['entity'],
                "vendor": vendor,
                "amount": amount,
                "count": count,
                "root_cause": "duplicate_payment_processing",
                "ai_analysis": f"Same invoice from {vendor} paid {count} times with different payment references",
                "recommended_action": f"Reverse {count-1} duplicate payments totaling ${amount * (count-1):,.2f}",
                "confidence": 0.95,
                "supporting_data": {
                    "payment_refs": payment_refs.tolist(),
                    "bill_ids": duplicate_records['bill_id'].tolist()
                }
            }
            findings.append(finding)
            
            console.line("forensics", "Duplicate", "detected", ai=True,
                        details=f"{vendor} ${amount:,.0f} x{count}")
    
    return findings

def determine_root_cause(rec, data: Dict) -> str:
    """Determine most likely root cause based on reconciliation patterns."""
    
    # Cash account discrepancies often indicate timing or unrecorded items
    if rec.account_id == "1000":  # Cash
        if abs(rec.difference) > 10000:
            return "unrecorded_transactions"
        else:
            return "timing_differences"
    
    # AR discrepancies often indicate collection or cut-off issues
    elif rec.account_id == "1100":  # AR
        if rec.difference < 0:  # AR lower than expected
            return "early_collections_or_cutoff"
        else:
            return "uncollected_receivables"
    
    # AP discrepancies often indicate accrual or duplicate issues
    elif rec.account_id == "2000":  # AP
        if rec.difference > 0:  # AP higher than expected
            return "unrecorded_liabilities"
        else:
            return "duplicate_payments_or_early_payment"
    
    # Intercompany often indicates timing or FX issues
    elif rec.account_id in ["1400", "2200"]:  # IC accounts
        return "intercompany_timing_or_fx"
    
    return "unknown_variance"

def get_recommended_action(root_cause: str) -> str:
    """Get recommended action based on root cause."""
    
    actions = {
        "unrecorded_transactions": "Review bank statements and record missing transactions",
        "timing_differences": "Implement cut-off adjustment entries",
        "early_collections_or_cutoff": "Verify customer payment timing and adjust if needed",
        "uncollected_receivables": "Review aging and consider allowance adjustment",
        "unrecorded_liabilities": "Search for unrecorded vendor invoices and accrue",
        "duplicate_payments_or_early_payment": "Investigate duplicate payments and reverse if confirmed",
        "intercompany_timing_or_fx": "Align intercompany booking dates and revalue for FX",
        "cut_off_error": "Review period-end cut-off procedures",
        "duplicate_payment_processing": "Reverse duplicate payments and strengthen controls"
    }
    
    return actions.get(root_cause, "Investigate further and document findings")

def calculate_confidence(rec, data: Dict) -> float:
    """Calculate confidence score for root cause analysis."""
    
    confidence = 0.5  # Base confidence
    
    # Higher confidence for larger, material amounts
    if abs(rec.difference) > 50000:
        confidence += 0.2
    elif abs(rec.difference) > 10000:
        confidence += 0.1
    
    # Higher confidence for accounts with clear patterns
    if rec.account_id in ["1000", "1100", "2000"]:  # Core accounts
        confidence += 0.2
    
    # Higher confidence if supporting data is available
    if data and any(key in data for key in ["ar", "ap", "bank"]):
        confidence += 0.1
    
    return min(confidence, 0.95)  # Cap at 95%
