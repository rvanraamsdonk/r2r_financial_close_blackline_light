#!/usr/bin/env python3
"""
Create Missing Data Files
Creates intercompany and other missing files for complete data structure
"""
import pandas as pd
import numpy as np
from pathlib import Path
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

def create_intercompany_data():
    """Create intercompany transactions file"""
    print("🔗 Creating intercompany data...")
    
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    ic_data = []
    doc_id = 80000
    
    # Create intercompany transactions between entities
    for i in range(50):  # 50 IC transactions
        src_entity = random.choice(entities)
        dst_entity = random.choice([e for e in entities if e != src_entity])
        
        date = datetime(2025, 8, random.randint(1, 31))
        amount = random.uniform(10000, 500000)
        
        # Transaction types
        txn_types = ["Management Fee", "Shared Services", "Loan", "Dividend", "Royalty", "Transfer Pricing"]
        txn_type = random.choice(txn_types)
        
        # Some timing differences for testing
        timing_diff = random.random() < 0.2  # 20% have timing differences
        
        ic_data.append({
            "period": "2025-08",
            "entity_src": src_entity,
            "entity_dst": dst_entity,
            "doc_id": f"IC{doc_id:06d}",
            "date": date.strftime("%Y-%m-%d"),
            "amount_local": round(amount, 2),
            "amount_usd": round(amount * (1.0 if currencies[src_entity] == "USD" else 1.08 if currencies[src_entity] == "EUR" else 1.27), 2),
            "currency": currencies[src_entity],
            "transaction_type": txn_type,
            "description": f"{txn_type} - {src_entity} to {dst_entity}",
            "timing_difference": timing_diff,
            "reference": f"REF{random.randint(100000, 999999)}"
        })
        doc_id += 1
    
    ic_df = pd.DataFrame(ic_data)
    ic_path = Path("../data/subledgers/intercompany/ic_transactions_aug.csv")
    ic_path.parent.mkdir(parents=True, exist_ok=True)
    ic_df.to_csv(ic_path, index=False)
    
    print(f"✅ Intercompany data created: {len(ic_df)} transactions")
    print(f"   Timing differences: {len(ic_df[ic_df['timing_difference'] == True])}")

def create_enhanced_accruals():
    """Create enhanced accruals file if missing"""
    print("📝 Creating enhanced accruals...")
    
    accruals_path = Path("../data/supporting/accruals.csv")
    
    # Check if we need to create or enhance
    if accruals_path.exists():
        df = pd.read_csv(accruals_path)
        if len(df) >= 50:
            print(f"✅ Accruals already enhanced: {len(df)} entries")
            return
    
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    accrual_data = []
    accrual_id = 90000
    
    # Accrual types and scenarios
    accrual_types = [
        ("Payroll", "Monthly payroll accrual"),
        ("Utilities", "Electricity and water bills"),
        ("Legal Fees", "External legal counsel"),
        ("Consulting", "Management consulting fees"),
        ("Rent", "Office rent accrual"),
        ("Insurance", "Professional liability insurance"),
        ("Audit Fees", "External audit costs"),
        ("Tax Advisory", "Tax consulting services"),
        ("Software Licenses", "Annual software subscriptions"),
        ("Marketing", "Advertising campaign costs"),
        ("Travel", "Employee travel expenses"),
        ("Training", "Employee development programs"),
        ("Bonuses", "Performance bonus accruals"),
        ("Severance", "Employee termination costs"),
        ("Warranty", "Product warranty reserves"),
        ("Restructuring", "Organizational restructuring costs")
    ]
    
    for i in range(60):  # 60 accrual entries
        entity = random.choice(entities)
        currency = currencies[entity]
        accrual_type, description = random.choice(accrual_types)
        
        accrual_date = datetime(2025, 8, random.randint(1, 31))
        reversal_date = datetime(2025, 9, random.randint(1, 15))
        
        amount = random.uniform(5000, 200000)
        
        # Status scenarios
        status_options = ["Active", "Should Reverse", "Reversed", "Adjusted", "Disputed"]
        status = random.choices(status_options, weights=[0.4, 0.2, 0.2, 0.1, 0.1])[0]
        
        # Some failed reversals for testing
        reversal_failed = status == "Should Reverse" and random.random() < 0.3
        
        accrual_data.append({
            "period": "2025-08",
            "entity": entity,
            "accrual_id": f"ACC{accrual_id:06d}",
            "accrual_type": accrual_type,
            "description": description,
            "accrual_date": accrual_date.strftime("%Y-%m-%d"),
            "reversal_date": reversal_date.strftime("%Y-%m-%d"),
            "amount_local": round(amount, 2),
            "amount_usd": round(amount * (1.0 if currency == "USD" else 1.08 if currency == "EUR" else 1.27), 2),
            "currency": currency,
            "status": status,
            "reversal_failed": reversal_failed,
            "approval_required": random.choice([True, False]),
            "materiality_threshold": random.uniform(0.01, 0.05),
            "supporting_doc": f"DOC{random.randint(100000, 999999)}"
        })
        accrual_id += 1
    
    accruals_df = pd.DataFrame(accrual_data)
    accruals_df.to_csv(accruals_path, index=False)
    
    print(f"✅ Enhanced accruals created: {len(accruals_df)} entries")
    print(f"   Failed reversals: {len(accruals_df[accruals_df['reversal_failed'] == True])}")

def create_enhanced_journal_entries():
    """Create enhanced journal entries file"""
    print("📋 Creating enhanced journal entries...")
    
    je_path = Path("../data/supporting/journal_entries.csv")
    
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    je_data = []
    je_id = 95000
    
    # JE types and scenarios
    je_types = [
        ("Accrual", "Period-end accrual entry"),
        ("Reversal", "Accrual reversal entry"),
        ("Reclassification", "Account reclassification"),
        ("Correction", "Error correction entry"),
        ("Depreciation", "Monthly depreciation"),
        ("FX Revaluation", "Foreign exchange revaluation"),
        ("Provision", "Bad debt provision"),
        ("Adjustment", "Management adjustment"),
        ("Consolidation", "Consolidation adjustment"),
        ("Tax", "Tax provision adjustment")
    ]
    
    approval_levels = ["Manager", "Controller", "CFO", "CEO"]
    
    for i in range(75):  # 75 journal entries
        entity = random.choice(entities)
        currency = currencies[entity]
        je_type, description = random.choice(je_types)
        
        entry_date = datetime(2025, 8, random.randint(1, 31))
        amount = random.uniform(1000, 100000)
        
        # Approval workflow scenarios
        approval_status = random.choices(
            ["Approved", "Pending", "Rejected", "Under Review"],
            weights=[0.6, 0.2, 0.1, 0.1]
        )[0]
        
        approver_level = random.choice(approval_levels)
        
        # Some entries flagged for reversal
        reversal_flagged = random.random() < 0.15
        
        je_data.append({
            "period": "2025-08",
            "entity": entity,
            "je_id": f"JE{je_id:06d}",
            "je_type": je_type,
            "description": description,
            "entry_date": entry_date.strftime("%Y-%m-%d"),
            "amount_local": round(amount, 2),
            "amount_usd": round(amount * (1.0 if currency == "USD" else 1.08 if currency == "EUR" else 1.27), 2),
            "currency": currency,
            "approval_status": approval_status,
            "approver_level": approver_level,
            "approver_name": f"Approver_{random.randint(1, 20):02d}",
            "reversal_flagged": reversal_flagged,
            "supporting_doc": f"DOC{random.randint(100000, 999999)}",
            "account_dr": f"{random.randint(1000, 9999)}",
            "account_cr": f"{random.randint(1000, 9999)}"
        })
        je_id += 1
    
    je_df = pd.DataFrame(je_data)
    je_df.to_csv(je_path, index=False)
    
    print(f"✅ Enhanced journal entries created: {len(je_df)} entries")
    print(f"   Pending approval: {len(je_df[je_df['approval_status'] == 'Pending'])}")

def main():
    print("📁 CREATING MISSING DATA FILES")
    print("===============================")
    
    create_intercompany_data()
    create_enhanced_accruals()
    create_enhanced_journal_entries()
    
    print("\n✅ MISSING FILES CREATION COMPLETE")

if __name__ == "__main__":
    main()
