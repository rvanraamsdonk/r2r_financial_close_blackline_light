#!/usr/bin/env python3
"""
Create Sophisticated Forensic Patterns in Financial Data
Embeds realistic transaction patterns that trigger algorithmic detection
"""
import pandas as pd
import numpy as np
from pathlib import Path
import random
from datetime import datetime, timedelta
import uuid

random.seed(42)
np.random.seed(42)

def create_ap_forensic_patterns():
    """Create AP data with embedded forensic patterns"""
    print("🔍 Creating AP data with sophisticated forensic patterns...")
    
    # Load existing AP data and remove explicit flags
    ap_path = Path("data/subledgers/ap_detail_aug.csv")
    df = pd.read_csv(ap_path)
    
    # Remove all explicit forensic flag columns
    forensic_cols = ['duplicate_payment_risk', 'vendor_fraud_risk', 'round_dollar_anomaly', 
                    'weekend_entry_flag', 'split_transaction_risk']
    df = df.drop(columns=[col for col in forensic_cols if col in df.columns], errors='ignore')
    
    # Reset index for clean manipulation
    df = df.reset_index(drop=True)
    
    # Pattern 1: Duplicate Payments (5% of records)
    duplicate_count = int(len(df) * 0.05)
    for i in range(duplicate_count):
        # Find a base record to duplicate
        base_idx = random.randint(0, len(df) - 1)
        base_record = df.iloc[base_idx].copy()
        
        # Create duplicate with slight variations
        duplicate_record = base_record.copy()
        duplicate_record['invoice_id'] = f"AP{random.randint(100000, 999999)}"
        
        # Same vendor, very similar amount (within $50)
        amount_variation = random.uniform(-50, 50)
        duplicate_record['amount'] = max(100, base_record['amount'] + amount_variation)
        duplicate_record['amount_usd'] = duplicate_record['amount']
        
        # Date within 7 days
        base_date = pd.to_datetime(base_record['invoice_date'])
        date_offset = random.randint(1, 7)
        duplicate_record['invoice_date'] = (base_date + timedelta(days=date_offset)).strftime('%Y-%m-%d')
        duplicate_record['bill_date'] = duplicate_record['invoice_date']
        
        # Add to dataframe
        df = pd.concat([df, duplicate_record.to_frame().T], ignore_index=True)
    
    # Pattern 2: Round Dollar Anomalies (10% of records)
    round_indices = random.sample(range(len(df)), min(int(len(df) * 0.10), len(df)))
    for idx in round_indices:
        # Create suspiciously round amounts
        base_amount = df.loc[idx, 'amount']
        if base_amount > 1000:
            # Large round numbers: $10K, $25K, $50K, $100K
            round_amounts = [10000, 25000, 50000, 75000, 100000]
            df.loc[idx, 'amount'] = random.choice(round_amounts)
        else:
            # Smaller round numbers: $500, $1000, $2500
            round_amounts = [500, 1000, 1500, 2000, 2500]
            df.loc[idx, 'amount'] = random.choice(round_amounts)
        
        df.loc[idx, 'amount_usd'] = df.loc[idx, 'amount']
    
    # Pattern 3: Suspicious New Vendors (3% of records)
    fraud_indices = random.sample(range(len(df)), int(len(df) * 0.03))
    suspicious_vendors = [
        "QuickPay Solutions LLC", "Rapid Services Inc", "Express Consulting Group",
        "Swift Solutions Corp", "Immediate Services LLC", "Fast Track Consulting",
        "Priority Services Inc", "Urgent Solutions Group"
    ]
    
    for idx in fraud_indices:
        df.loc[idx, 'vendor_name'] = random.choice(suspicious_vendors)
        df.loc[idx, 'vendor'] = df.loc[idx, 'vendor_name']
        # Large amounts for new vendors
        df.loc[idx, 'amount'] = random.uniform(25000, 150000)
        df.loc[idx, 'amount_usd'] = df.loc[idx, 'amount']
    
    # Pattern 4: Weekend Entries (2% of records)
    weekend_indices = random.sample(range(len(df)), int(len(df) * 0.02))
    for idx in weekend_indices:
        # Set invoice date to weekend
        year, month = 2025, 8
        weekend_dates = []
        for day in range(1, 32):
            try:
                date = datetime(year, month, day)
                if date.weekday() >= 5:  # Saturday or Sunday
                    weekend_dates.append(date.strftime('%Y-%m-%d'))
            except ValueError:
                continue
        
        if weekend_dates:
            df.loc[idx, 'invoice_date'] = random.choice(weekend_dates)
            df.loc[idx, 'bill_date'] = df.loc[idx, 'invoice_date']
    
    # Pattern 5: Split Transactions (4% of records)
    split_base_count = int(len(df) * 0.02)  # Base transactions to split
    for i in range(split_base_count):
        base_idx = random.randint(0, len(df) - 1)
        base_record = df.iloc[base_idx].copy()
        
        # Split large amount into 2-3 smaller transactions
        original_amount = base_record['amount']
        if original_amount > 10000:  # Only split large transactions
            num_splits = random.randint(2, 3)
            split_amounts = []
            remaining = original_amount
            
            for j in range(num_splits - 1):
                split_amt = remaining * random.uniform(0.3, 0.5)
                split_amounts.append(split_amt)
                remaining -= split_amt
            split_amounts.append(remaining)
            
            # Create split transactions
            for j, split_amt in enumerate(split_amounts):
                split_record = base_record.copy()
                split_record['invoice_id'] = f"AP{random.randint(100000, 999999)}"
                split_record['amount'] = round(split_amt, 2)
                split_record['amount_usd'] = split_record['amount']
                split_record['description'] = f"{base_record['description']} - Part {j+1}"
                
                df = pd.concat([df, split_record.to_frame().T], ignore_index=True)
    
    # Save enhanced data
    df.to_csv(ap_path, index=False)
    print(f"✅ AP forensic patterns created: {len(df)} records")
    return len(df)

def create_ar_forensic_patterns():
    """Create AR data with embedded forensic patterns"""
    print("🔍 Creating AR data with sophisticated forensic patterns...")
    
    ar_path = Path("data/subledgers/ar_detail_aug.csv")
    df = pd.read_csv(ar_path)
    
    # Remove explicit forensic flags
    forensic_cols = ['revenue_recognition_risk', 'credit_memo_abuse', 'channel_stuffing_risk',
                    'related_party_transaction', 'unusual_payment_terms']
    df = df.drop(columns=[col for col in forensic_cols if col in df.columns], errors='ignore')
    
    df = df.reset_index(drop=True)
    
    # Pattern 1: Channel Stuffing - End of month spike (6% of records)
    channel_indices = random.sample(range(len(df)), int(len(df) * 0.06))
    end_of_month_dates = ['2025-08-29', '2025-08-30', '2025-08-31']
    
    for idx in channel_indices:
        df.loc[idx, 'invoice_date'] = random.choice(end_of_month_dates)
        # Large amounts near month end
        df.loc[idx, 'amount'] = random.uniform(50000, 200000)
        df.loc[idx, 'amount_usd'] = df.loc[idx, 'amount']
        # Extended payment terms
        df.loc[idx, 'payment_terms'] = random.choice(['Net 90', 'Net 120', 'Net 180'])
    
    # Pattern 2: Credit Memo Abuse - Unusual credit patterns (3% of records)
    credit_indices = random.sample(range(len(df)), int(len(df) * 0.03))
    for idx in credit_indices:
        # Negative amounts (credits)
        df.loc[idx, 'amount'] = -abs(random.uniform(5000, 50000))
        df.loc[idx, 'amount_usd'] = df.loc[idx, 'amount']
        df.loc[idx, 'description'] = f"Credit Memo - {df.loc[idx, 'description']}"
    
    # Pattern 3: Related Party Transactions (2% of records)
    related_party_customers = [
        "Subsidiary Holdings Inc", "Affiliate Services Corp", "Related Entity LLC",
        "Sister Company Ltd", "Associated Business Group"
    ]
    related_indices = random.sample(range(len(df)), int(len(df) * 0.02))
    for idx in related_indices:
        df.loc[idx, 'customer_name'] = random.choice(related_party_customers)
        # Unusual pricing
        df.loc[idx, 'amount'] = random.uniform(75000, 300000)
        df.loc[idx, 'amount_usd'] = df.loc[idx, 'amount']
    
    df.to_csv(ar_path, index=False)
    print(f"✅ AR forensic patterns created: {len(df)} records")
    return len(df)

def create_bank_forensic_patterns():
    """Create bank data with embedded forensic patterns"""
    print("🔍 Creating bank data with sophisticated forensic patterns...")
    
    bank_path = Path("data/subledgers/bank_statements/bank_transactions_aug.csv")
    if not bank_path.exists():
        print(f"⚠️  Bank file not found: {bank_path}")
        return 0
        
    df = pd.read_csv(bank_path)
    
    # Remove explicit forensic flags if they exist
    forensic_cols = ['suspicious_timing', 'kiting_risk', 'cash_lapping_risk', 
                    'unusual_counterparty', 'velocity_anomaly']
    df = df.drop(columns=[col for col in forensic_cols if col in df.columns], errors='ignore')
    
    df = df.reset_index(drop=True)
    
    # Pattern 1: Kiting - Round trip transfers (1% of records)
    kiting_count = int(len(df) * 0.01)
    for i in range(0, kiting_count, 2):  # Create pairs
        if i + 1 < len(df):
            # First transfer
            df.loc[i, 'transaction_type'] = 'Transfer Out'
            df.loc[i, 'counterparty'] = 'Internal Account 2'
            df.loc[i, 'amount'] = random.uniform(100000, 500000)
            df.loc[i, 'date'] = '2025-08-30'
            
            # Return transfer (next day)
            df.loc[i + 1, 'transaction_type'] = 'Transfer In'
            df.loc[i + 1, 'counterparty'] = 'Internal Account 2'
            df.loc[i + 1, 'amount'] = df.loc[i, 'amount']  # Same amount
            df.loc[i + 1, 'date'] = '2025-08-31'
    
    # Pattern 2: Unusual Counterparties (4% of records)
    unusual_counterparties = [
        "Cash Advance LLC", "Quick Loan Services", "Payday Solutions Inc",
        "Immediate Funding Corp", "Rapid Cash Group"
    ]
    unusual_indices = random.sample(range(len(df)), int(len(df) * 0.04))
    for idx in unusual_indices:
        df.loc[idx, 'counterparty'] = random.choice(unusual_counterparties)
        df.loc[idx, 'amount'] = random.uniform(25000, 100000)
    
    # Pattern 3: Velocity Anomalies - High frequency transactions (3% of records)
    velocity_indices = random.sample(range(len(df)), int(len(df) * 0.03))
    for idx in velocity_indices:
        # Multiple transactions same day, same counterparty
        df.loc[idx, 'date'] = '2025-08-15'  # Cluster on one day
        df.loc[idx, 'counterparty'] = 'High Volume Vendor Inc'
        df.loc[idx, 'amount'] = random.uniform(5000, 15000)
    
    df.to_csv(bank_path, index=False)
    print(f"✅ Bank forensic patterns created: {len(df)} records")
    return len(df)

def main():
    """Main execution"""
    print("🚀 Creating sophisticated forensic patterns in financial data...")
    print("📊 This approach embeds realistic patterns for algorithmic detection")
    print("🎯 No explicit boolean flags - patterns must be detected by analysis\n")
    
    ap_count = create_ap_forensic_patterns()
    ar_count = create_ar_forensic_patterns()
    bank_count = create_bank_forensic_patterns()
    
    print(f"\n✅ Forensic pattern creation complete!")
    print(f"📈 AP Records: {ap_count}")
    print(f"📈 AR Records: {ar_count}")
    print(f"📈 Bank Records: {bank_count}")
    print("\n🔍 Patterns embedded:")
    print("   • Duplicate payments (same vendor + similar amounts + close dates)")
    print("   • Round dollar anomalies (suspiciously round amounts)")
    print("   • Suspicious new vendors (large payments to new entities)")
    print("   • Weekend entries (transactions on Sat/Sun)")
    print("   • Split transactions (large amounts broken into pieces)")
    print("   • Channel stuffing (AR spikes at month end)")
    print("   • Credit memo abuse (unusual credit patterns)")
    print("   • Bank kiting (round-trip transfers)")
    print("   • Unusual counterparties (suspicious entities)")
    print("\n🎯 Next: Update reconciliation engines to detect these patterns algorithmically")

if __name__ == "__main__":
    main()
