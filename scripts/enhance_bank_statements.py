#!/usr/bin/env python3
"""
Script to enhance bank statement data with unmatched transactions and complex scenarios
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
from pathlib import Path

def enhance_bank_statements():
    """Enhance bank statement data with unmatched transactions and complex scenarios"""
    
    # Read original bank transactions
    bank_file = Path("data/lite/subledgers/bank_statements/bank_transactions_aug.csv")
    df = pd.read_csv(bank_file)
    
    # Create enhanced dataset
    enhanced_rows = []
    
    # Add original data
    enhanced_rows.extend(df.to_dict('records'))
    
    # Define complex bank transaction scenarios
    counterparties = [
        "Microsoft Corporation", "Google LLC", "Amazon Web Services", "Salesforce Inc",
        "Oracle Corporation", "IBM Corporation", "SAP SE", "Adobe Inc", "Workday Inc",
        "ServiceNow Inc", "Payroll Services Inc", "Tax Authority", "Utility Company",
        "Office Lease Corp", "Insurance Company", "Legal Services LLC", "Consulting Group",
        "Marketing Agency", "Travel Services", "Equipment Leasing", "Software Vendor",
        "Cloud Provider", "Security Services", "Audit Firm", "Bank Fees", "Interest Payment",
        "Customer Refund", "Vendor Rebate", "Government Grant", "Investment Income"
    ]
    
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    # Generate complex scenarios including unmatched transactions
    txn_counter = 214  # Continue from existing data
    
    for entity in entities:
        currency = currencies[entity]
        
        # Generate 150 additional transactions per entity with various scenarios
        for i in range(150):
            counterparty = random.choice(counterparties)
            
            # Create different transaction scenarios
            scenarios = [
                # Matched transactions (70%)
                {"type": "matched", "amount_range": (1000, 15000), "description_match": True},
                
                # Unmatched - timing differences (15%)
                {"type": "unmatched_timing", "amount_range": (500, 8000), "description_match": False},
                
                # Unmatched - amount differences (8%)
                {"type": "unmatched_amount", "amount_range": (1200, 12000), "description_match": False},
                
                # Bank errors (3%)
                {"type": "bank_error", "amount_range": (100, 5000), "description_match": False},
                
                # Duplicate transactions (2%)
                {"type": "duplicate", "amount_range": (800, 6000), "description_match": False},
                
                # Unknown transactions (2%)
                {"type": "unknown", "amount_range": (50, 2000), "description_match": False}
            ]
            
            # Select scenario based on probability
            rand = random.random()
            if rand < 0.70:
                scenario_type = "matched"
            elif rand < 0.85:
                scenario_type = "unmatched_timing"
            elif rand < 0.93:
                scenario_type = "unmatched_amount"
            elif rand < 0.96:
                scenario_type = "bank_error"
            elif rand < 0.98:
                scenario_type = "duplicate"
            else:
                scenario_type = "unknown"
            
            scenario = next(s for s in scenarios if s["type"] == scenario_type)
            
            # Generate transaction details
            is_payment = random.choice([True, False])
            base_amount = random.uniform(*scenario["amount_range"])
            
            # Add amount variance for unmatched scenarios
            if scenario_type == "unmatched_amount":
                variance = random.uniform(0.95, 1.15)  # 5-15% variance
                base_amount *= variance
            elif scenario_type == "bank_error":
                # Bank errors can have significant differences
                variance = random.uniform(0.5, 2.0)
                base_amount *= variance
            
            amount = -base_amount if is_payment else base_amount
            
            # Generate transaction types and descriptions
            txn_types = ["ACH", "Wire", "Check", "Card", "Transfer", "Fee"]
            txn_type = random.choice(txn_types)
            
            # Create realistic but potentially mismatched descriptions
            if scenario["description_match"]:
                description = f"Payment to/from {counterparty}"
            else:
                # Create mismatched descriptions for reconciliation challenges
                mismatch_descriptions = [
                    f"Electronic payment - {counterparty[:10]}...",
                    f"Wire transfer ref #{random.randint(100000, 999999)}",
                    f"ACH debit/credit - {random.choice(['RECURRING', 'ONE-TIME', 'SCHEDULED'])}",
                    f"Check #{random.randint(1000, 9999)} - {counterparty[:8]}",
                    f"Card transaction - {counterparty[:12]}",
                    f"Bank fee - {random.choice(['WIRE', 'ACH', 'MAINTENANCE', 'OVERDRAFT'])}",
                    f"Interest {random.choice(['earned', 'charged'])} - {counterparty[:10]}",
                    f"Return item - {counterparty[:15]}",
                    f"Correction entry - ref {random.randint(10000, 99999)}",
                    f"Memo posting - {counterparty[:20]}"
                ]
                description = random.choice(mismatch_descriptions)
            
            # Add special scenario markers
            if scenario_type == "duplicate":
                description += " [DUPLICATE]"
            elif scenario_type == "bank_error":
                description += " [ERROR]"
            elif scenario_type == "unknown":
                description = f"Unknown transaction - ref {random.randint(100000, 999999)}"
                counterparty = "UNKNOWN COUNTERPARTY"
            
            txn_date = datetime(2025, 8, random.randint(1, 31))
            
            row = {
                "period": "2025-08",
                "entity": entity,
                "bank_txn_id": f"BNK-2025-08-{entity}-{txn_counter:04d}",
                "date": txn_date.strftime("%Y-%m-%d"),
                "amount": round(amount, 2),
                "currency": currency,
                "counterparty": counterparty,
                "transaction_type": txn_type,
                "description": description
            }
            
            enhanced_rows.append(row)
            txn_counter += 1
    
    # Create enhanced dataframe
    enhanced_df = pd.DataFrame(enhanced_rows)
    
    # Save enhanced bank transactions
    output_file = Path("data/lite/subledgers/bank_statements/bank_transactions_aug_enhanced.csv")
    enhanced_df.to_csv(output_file, index=False)
    print(f"Enhanced bank transactions saved to {output_file}")
    print(f"Original rows: {len(df)}, Enhanced rows: {len(enhanced_df)}")
    
    # Generate summary statistics
    total_enhanced = len(enhanced_df) - len(df)
    print(f"Added {total_enhanced} new transactions with complex reconciliation scenarios")
    
    # Count scenario types in new data
    new_data = enhanced_df.iloc[len(df):]
    unmatched_count = sum(1 for desc in new_data['description'] if any(marker in desc for marker in ['[DUPLICATE]', '[ERROR]', 'Unknown transaction', 'ref #', 'Electronic payment']))
    print(f"Approximately {unmatched_count} transactions will require manual reconciliation")

if __name__ == "__main__":
    print("Enhancing bank statement data...")
    enhance_bank_statements()
    print("Bank statement enhancement complete!")
