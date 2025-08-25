#!/usr/bin/env python3
"""
Add Forensic Scenarios to Enhanced Data
Embeds forensic accounting scenarios across all transaction types
"""
import pandas as pd
import numpy as np
from pathlib import Path
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

def add_forensic_to_ap():
    """Add forensic scenarios to AP data"""
    print("🔍 Adding forensic scenarios to AP data...")
    
    ap_path = Path("../data/subledgers/ap_detail_aug.csv")
    df = pd.read_csv(ap_path)
    
    # Add forensic flags
    df['duplicate_payment_risk'] = False
    df['vendor_fraud_risk'] = False
    df['round_dollar_anomaly'] = False
    df['weekend_entry_flag'] = False
    df['split_transaction_risk'] = False
    
    # Duplicate payment scenarios (5%)
    duplicate_indices = random.sample(range(len(df)), int(len(df) * 0.05))
    df.loc[duplicate_indices, 'duplicate_payment_risk'] = True
    
    # Vendor fraud scenarios (3%)
    fraud_indices = random.sample(range(len(df)), int(len(df) * 0.03))
    df.loc[fraud_indices, 'vendor_fraud_risk'] = True
    
    # Round dollar anomalies (10%)
    round_indices = random.sample(range(len(df)), int(len(df) * 0.10))
    df.loc[round_indices, 'round_dollar_anomaly'] = True
    for idx in round_indices:
        df.loc[idx, 'amount'] = round(df.loc[idx, 'amount'] / 100) * 100
    
    # Weekend entries (2%)
    weekend_indices = random.sample(range(len(df)), int(len(df) * 0.02))
    df.loc[weekend_indices, 'weekend_entry_flag'] = True
    
    # Split transaction risk (4%)
    split_indices = random.sample(range(len(df)), int(len(df) * 0.04))
    df.loc[split_indices, 'split_transaction_risk'] = True
    
    df.to_csv(ap_path, index=False)
    print(f"✅ AP forensic scenarios added: {len(df)} records")

def add_forensic_to_ar():
    """Add forensic scenarios to AR data"""
    print("🔍 Adding forensic scenarios to AR data...")
    
    ar_path = Path("../data/subledgers/ar_detail_aug.csv")
    df = pd.read_csv(ar_path)
    
    # Add forensic flags
    df['revenue_recognition_risk'] = False
    df['credit_memo_abuse'] = False
    df['channel_stuffing_risk'] = False
    df['related_party_transaction'] = False
    df['unusual_payment_terms'] = False
    
    # Revenue recognition issues (6%)
    rev_indices = random.sample(range(len(df)), int(len(df) * 0.06))
    df.loc[rev_indices, 'revenue_recognition_risk'] = True
    
    # Credit memo abuse (3%)
    credit_indices = random.sample(range(len(df)), int(len(df) * 0.03))
    df.loc[credit_indices, 'credit_memo_abuse'] = True
    
    # Channel stuffing (4%)
    stuffing_indices = random.sample(range(len(df)), int(len(df) * 0.04))
    df.loc[stuffing_indices, 'channel_stuffing_risk'] = True
    
    # Related party transactions (2%)
    related_indices = random.sample(range(len(df)), int(len(df) * 0.02))
    df.loc[related_indices, 'related_party_transaction'] = True
    
    # Unusual payment terms (5%)
    terms_indices = random.sample(range(len(df)), int(len(df) * 0.05))
    df.loc[terms_indices, 'unusual_payment_terms'] = True
    
    df.to_csv(ar_path, index=False)
    print(f"✅ AR forensic scenarios added: {len(df)} records")

def add_forensic_to_bank():
    """Add forensic scenarios to bank data"""
    print("🔍 Adding forensic scenarios to bank data...")
    
    bank_paths = [
        Path("../data/subledgers/bank_statements/bank_transactions_aug.csv"),
        Path("../data/subledgers/bank_statements/bank_transactions_ent101.csv"),
        Path("../data/subledgers/bank_statements/bank_transactions_ent102.csv")
    ]
    
    for bank_path in bank_paths:
        if not bank_path.exists():
            continue
            
        df = pd.read_csv(bank_path)
        
        # Add forensic flags
        df['suspicious_timing'] = False
        df['kiting_risk'] = False
        df['cash_lapping_risk'] = False
        df['unusual_counterparty'] = False
        df['velocity_anomaly'] = False
        
        # Suspicious timing (3%)
        timing_indices = random.sample(range(len(df)), int(len(df) * 0.03))
        df.loc[timing_indices, 'suspicious_timing'] = True
        
        # Kiting risk (1%)
        kiting_indices = random.sample(range(len(df)), int(len(df) * 0.01))
        df.loc[kiting_indices, 'kiting_risk'] = True
        
        # Cash lapping (2%)
        lapping_indices = random.sample(range(len(df)), int(len(df) * 0.02))
        df.loc[lapping_indices, 'cash_lapping_risk'] = True
        
        # Unusual counterparty (4%)
        counter_indices = random.sample(range(len(df)), int(len(df) * 0.04))
        df.loc[counter_indices, 'unusual_counterparty'] = True
        
        # Velocity anomaly (3%)
        velocity_indices = random.sample(range(len(df)), int(len(df) * 0.03))
        df.loc[velocity_indices, 'velocity_anomaly'] = True
        
        df.to_csv(bank_path, index=False)
        print(f"✅ Bank forensic scenarios added to {bank_path.name}: {len(df)} records")

def add_forensic_to_trial_balance():
    """Add forensic scenarios to trial balance"""
    print("🔍 Adding forensic scenarios to trial balance...")
    
    tb_path = Path("../data/trial_balance_aug.csv")
    df = pd.read_csv(tb_path)
    
    # Add forensic flags
    df['balance_manipulation_risk'] = False
    df['expense_shifting_risk'] = False
    df['reserve_manipulation'] = False
    df['classification_error'] = False
    
    # Balance manipulation (5%)
    balance_indices = random.sample(range(len(df)), int(len(df) * 0.05))
    df.loc[balance_indices, 'balance_manipulation_risk'] = True
    
    # Expense shifting (3%)
    expense_indices = random.sample(range(len(df)), int(len(df) * 0.03))
    df.loc[expense_indices, 'expense_shifting_risk'] = True
    
    # Reserve manipulation (4%)
    reserve_indices = random.sample(range(len(df)), int(len(df) * 0.04))
    df.loc[reserve_indices, 'reserve_manipulation'] = True
    
    # Classification errors (6%)
    class_indices = random.sample(range(len(df)), int(len(df) * 0.06))
    df.loc[class_indices, 'classification_error'] = True
    
    df.to_csv(tb_path, index=False)
    print(f"✅ Trial balance forensic scenarios added: {len(df)} records")

def add_forensic_to_intercompany():
    """Add forensic scenarios to intercompany data"""
    print("🔍 Adding forensic scenarios to intercompany data...")
    
    ic_path = Path("../data/subledgers/intercompany/ic_transactions_aug.csv")
    df = pd.read_csv(ic_path)
    
    # Add forensic flags
    df['transfer_pricing_risk'] = False
    df['profit_shifting_risk'] = False
    df['documentation_gap'] = False
    df['arm_length_violation'] = False
    
    # Transfer pricing issues (15%)
    tp_indices = random.sample(range(len(df)), int(len(df) * 0.15))
    df.loc[tp_indices, 'transfer_pricing_risk'] = True
    
    # Profit shifting (10%)
    profit_indices = random.sample(range(len(df)), int(len(df) * 0.10))
    df.loc[profit_indices, 'profit_shifting_risk'] = True
    
    # Documentation gaps (20%)
    doc_indices = random.sample(range(len(df)), int(len(df) * 0.20))
    df.loc[doc_indices, 'documentation_gap'] = True
    
    # Arm's length violations (8%)
    arm_indices = random.sample(range(len(df)), int(len(df) * 0.08))
    df.loc[arm_indices, 'arm_length_violation'] = True
    
    df.to_csv(ic_path, index=False)
    print(f"✅ Intercompany forensic scenarios added: {len(df)} records")

def add_forensic_to_accruals():
    """Add forensic scenarios to accruals"""
    print("🔍 Adding forensic scenarios to accruals...")
    
    acc_path = Path("../data/supporting/accruals.csv")
    df = pd.read_csv(acc_path)
    
    # Add forensic flags
    df['earnings_management_risk'] = False
    df['cookie_jar_reserve'] = False
    df['big_bath_accounting'] = False
    df['timing_manipulation'] = False
    
    # Earnings management (12%)
    earnings_indices = random.sample(range(len(df)), int(len(df) * 0.12))
    df.loc[earnings_indices, 'earnings_management_risk'] = True
    
    # Cookie jar reserves (8%)
    cookie_indices = random.sample(range(len(df)), int(len(df) * 0.08))
    df.loc[cookie_indices, 'cookie_jar_reserve'] = True
    
    # Big bath accounting (5%)
    bath_indices = random.sample(range(len(df)), int(len(df) * 0.05))
    df.loc[bath_indices, 'big_bath_accounting'] = True
    
    # Timing manipulation (10%)
    timing_indices = random.sample(range(len(df)), int(len(df) * 0.10))
    df.loc[timing_indices, 'timing_manipulation'] = True
    
    df.to_csv(acc_path, index=False)
    print(f"✅ Accruals forensic scenarios added: {len(df)} records")

def add_forensic_to_journal_entries():
    """Add forensic scenarios to journal entries"""
    print("🔍 Adding forensic scenarios to journal entries...")
    
    je_path = Path("../data/supporting/journal_entries.csv")
    df = pd.read_csv(je_path)
    
    # Add forensic flags
    df['manual_override_risk'] = False
    df['period_end_manipulation'] = False
    df['unauthorized_entry'] = False
    df['segregation_violation'] = False
    
    # Manual override risks (15%)
    override_indices = random.sample(range(len(df)), int(len(df) * 0.15))
    df.loc[override_indices, 'manual_override_risk'] = True
    
    # Period-end manipulation (8%)
    period_indices = random.sample(range(len(df)), int(len(df) * 0.08))
    df.loc[period_indices, 'period_end_manipulation'] = True
    
    # Unauthorized entries (3%)
    unauth_indices = random.sample(range(len(df)), int(len(df) * 0.03))
    df.loc[unauth_indices, 'unauthorized_entry'] = True
    
    # Segregation violations (5%)
    seg_indices = random.sample(range(len(df)), int(len(df) * 0.05))
    df.loc[seg_indices, 'segregation_violation'] = True
    
    df.to_csv(je_path, index=False)
    print(f"✅ Journal entries forensic scenarios added: {len(df)} records")

def main():
    print("🕵️ ADDING FORENSIC SCENARIOS")
    print("=============================")
    
    add_forensic_to_ap()
    add_forensic_to_ar()
    add_forensic_to_bank()
    add_forensic_to_trial_balance()
    add_forensic_to_intercompany()
    add_forensic_to_accruals()
    add_forensic_to_journal_entries()
    
    print("\n✅ FORENSIC SCENARIOS EMBEDDING COMPLETE")
    print("All transaction types now include forensic accounting scenarios")

if __name__ == "__main__":
    main()
