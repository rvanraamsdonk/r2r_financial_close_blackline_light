"""
Generates a comprehensive, realistic financial dataset from scratch.

This script creates a full set of subledger and supporting files for a financial close process,
embedding a variety of forensic and reconciliation scenarios for testing and demonstration purposes.
The goal is to produce a dataset that is algorithmically detectable by the R2R system's engines.

Based on the specification in: docs/data-enhancement-summary-v2.md
"""

import pandas as pd
import numpy as np
from faker import Faker
from pathlib import Path
import datetime
import sys

# --- Configuration ---
DATA_DIR = Path(__file__).parent.parent / 'data'
SUBLEDGERS_DIR = DATA_DIR / 'subledgers'
SUPPORTING_DIR = DATA_DIR / 'supporting'

# Ensure output directories exist
SUBLEDGERS_DIR.mkdir(exist_ok=True)
(SUBLEDGERS_DIR / 'intercompany').mkdir(exist_ok=True)
(SUBLEDGERS_DIR / 'bank_statements').mkdir(exist_ok=True)
SUPPORTING_DIR.mkdir(exist_ok=True)

# Initialize Faker for data generation
fake = Faker()
Faker.seed(42) # for reproducibility
np.random.seed(42)

# --- Data Generation Parameters ---
NUM_AP_TRANSACTIONS = 2000
NUM_AR_TRANSACTIONS = 1500
NUM_IC_PAIRS = 100
NUM_BANK_TRANSACTIONS = 5000
START_DATE = datetime.date(2025, 8, 1)
END_DATE = datetime.date(2025, 8, 31)

# --- Helper Functions ---

def generate_realistic_amount(min_val, max_val, skew_factor=0.1):
    """Generates a realistic, skewed distribution of transaction amounts."""
    return round(min_val + (max_val - min_val) * (np.random.power(skew_factor)))

# --- AP Data Generation ---

def _embed_ap_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to embed all AP forensic patterns into the dataframe."""
    print("Embedding AP forensic patterns...")
    
    # 1. Duplicate Payments (5% of records)
    num_duplicates = int(len(df) * 0.05)
    dup_indices = df.sample(n=num_duplicates, random_state=42).index
    for idx in dup_indices:
        original_row = df.loc[idx].copy()
        original_row['invoice_id'] = f"{original_row['invoice_id']}-DUP"
        original_row['amount'] *= np.random.uniform(0.99, 1.01) # Slight variation
        original_row['invoice_date'] += datetime.timedelta(days=np.random.randint(1, 7))
        df = pd.concat([df, original_row.to_frame().T], ignore_index=True)

    # 2. Round Dollar Anomalies (10% of records)
    num_round_dollars = int(len(df) * 0.1)
    round_indices = df.sample(n=num_round_dollars, random_state=43).index
    round_amounts = [1000, 5000, 10000, 25000, 50000]
    df.loc[round_indices, 'amount'] = np.random.choice(round_amounts, size=num_round_dollars)

    # 3. Suspicious New Vendors (3% of records)
    num_suspicious = int(len(df) * 0.03)
    suspicious_indices = df.sample(n=num_suspicious, random_state=44).index
    keywords = ["QuickPay", "Rapid", "Express", "Swift", "Immediate", "Fast Track"]
    suspicious_vendors = [f"{fake.company_suffix()} {kw}" for kw in keywords]
    df.loc[suspicious_indices, 'vendor_name'] = np.random.choice(suspicious_vendors, size=num_suspicious)
    df.loc[suspicious_indices, 'amount'] = [generate_realistic_amount(25001, 75000) for _ in range(num_suspicious)]

    # 4. Weekend Entries (2% of records)
    num_weekend = int(len(df) * 0.02)
    weekend_indices = df.sample(n=num_weekend, random_state=45).index
    for idx in weekend_indices:
        date = df.loc[idx, 'invoice_date']
        # 5=Saturday, 6=Sunday
        while date.weekday() < 5:
            date += datetime.timedelta(days=1)
        df.loc[idx, 'invoice_date'] = date

    # 5. Split Transactions (4% of records)
    num_splits = int(len(df) * 0.04)
    split_indices = df.query('amount > 20000').sample(n=num_splits, random_state=46).index
    for idx in split_indices:
        original_row = df.loc[idx].copy()
        num_new_tx = np.random.randint(2, 4)
        split_amounts = original_row['amount'] / num_new_tx
        df.loc[idx, 'amount'] = split_amounts # Modify original
        for i in range(1, num_new_tx):
            split_row = original_row.copy()
            split_row['invoice_id'] = f"{original_row['invoice_id']}-SPLIT{i}"
            split_row['amount'] = split_amounts
            df = pd.concat([df, split_row.to_frame().T], ignore_index=True)

    print("AP patterns embedded.")
    return df.sample(frac=1).reset_index(drop=True) # Shuffle

def generate_ap_subledger(num_records: int):
    """Generates the Accounts Payable subledger with embedded forensic patterns."""
    print(f"Generating {num_records} AP transactions...")
    data = []
    vendors = [fake.company() for _ in range(num_records // 10)]

    for i in range(num_records):
        invoice_date = fake.date_between(start_date=START_DATE, end_date=END_DATE)
        data.append({
            'invoice_id': f"INV-{i+1000}",
            'vendor_name': np.random.choice(vendors),
            'invoice_date': invoice_date,
            'due_date': invoice_date + datetime.timedelta(days=30),
            'amount': generate_realistic_amount(50, 50000, 0.2),
            'currency': 'USD',
            'status': 'Open',
            'payment_date': pd.NaT,
            'description': fake.bs()
        })
    
    df = pd.DataFrame(data)
    df['invoice_date'] = pd.to_datetime(df['invoice_date'])

    # Embed forensic patterns
    df = _embed_ap_patterns(df)

    output_path = SUBLEDGERS_DIR / 'ap_detail_aug.csv'
    df.to_csv(output_path, index=False, date_format='%Y-%m-%d')
    print(f"AP subledger saved to {output_path}")
    return df

# --- AR Data Generation ---

def _embed_ar_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to embed all AR forensic patterns into the dataframe."""
    print("Embedding AR forensic patterns...")
    month_end = END_DATE
    month_start_of_end = month_end - datetime.timedelta(days=2)

    # 1. Channel Stuffing (6% of records)
    num_stuffing = int(len(df) * 0.06)
    stuffing_indices = df.sample(n=num_stuffing, random_state=50).index
    for idx in stuffing_indices:
        df.loc[idx, 'amount'] = generate_realistic_amount(50001, 150000)
        df.loc[idx, 'invoice_date'] = fake.date_between(start_date=month_start_of_end, end_date=month_end)
        df.loc[idx, 'payment_terms'] = np.random.choice(['Net 90', 'Net 120', 'Net 180'])

    # 2. Credit Memo Abuse (3% of records)
    num_credits = int(len(df) * 0.03)
    credit_indices = df.sample(n=num_credits, random_state=51).index
    df.loc[credit_indices, 'amount'] = -1 * np.random.randint(5001, 20000, size=num_credits)
    df.loc[credit_indices, 'description'] = 'Credit Memo for returned goods'

    # 3. Related Party Transactions (2% of records)
    num_related = int(len(df) * 0.02)
    related_indices = df.sample(n=num_related, random_state=52).index
    keywords = ["Subsidiary", "Affiliate", "Related Entity", "Sister Company"]
    related_customers = [f"{fake.company()} {kw}" for kw in keywords]
    df.loc[related_indices, 'customer_name'] = np.random.choice(related_customers, size=num_related)
    df.loc[related_indices, 'amount'] = [generate_realistic_amount(75001, 250000) for _ in range(num_related)]

    # 4. Weekend Revenue Recognition (embedded in 1% of records)
    num_weekend = int(len(df) * 0.01)
    weekend_indices = df.query('amount > 25000').sample(n=num_weekend, random_state=53).index
    for idx in weekend_indices:
        date = df.loc[idx, 'invoice_date']
        while date.weekday() < 5: # Move to Saturday or Sunday
            date += datetime.timedelta(days=1)
        df.loc[idx, 'invoice_date'] = date

    print("AR patterns embedded.")
    return df.sample(frac=1).reset_index(drop=True) # Shuffle

def generate_ar_subledger(num_records: int):
    """Generates the Accounts Receivable subledger with embedded forensic patterns."""
    print(f"\nGenerating {num_records} AR transactions...")
    data = []
    customers = [fake.company() for _ in range(num_records // 10)]

    for i in range(num_records):
        invoice_date = fake.date_between(start_date=START_DATE, end_date=END_DATE)
        data.append({
            'invoice_id': f"AR-INV-{i+5000}",
            'customer_name': np.random.choice(customers),
            'invoice_date': invoice_date,
            'amount': generate_realistic_amount(100, 80000, 0.3),
            'currency': 'USD',
            'status': 'Billed',
            'payment_terms': np.random.choice(['Net 30', 'Net 60']),
            'description': fake.catch_phrase()
        })

    df = pd.DataFrame(data)
    df['invoice_date'] = pd.to_datetime(df['invoice_date'])

    # Embed forensic patterns
    df = _embed_ar_patterns(df)

    output_path = SUBLEDGERS_DIR / 'ar_detail_aug.csv'
    df.to_csv(output_path, index=False, date_format='%Y-%m-%d')
    print(f"AR subledger saved to {output_path}")
    return df

# --- Intercompany Data Generation ---

def _embed_ic_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to embed intercompany reconciliation issues."""
    print("Embedding Intercompany reconciliation patterns...")
    
    # 1. Amount Mismatches (15% of pairs)
    num_mismatches = int(len(df['transaction_id'].unique()) * 0.15)
    tx_ids_to_modify = np.random.choice(df['transaction_id'].unique(), num_mismatches, replace=False)
    for tx_id in tx_ids_to_modify:
        indices = df[df['transaction_id'] == tx_id].index
        # Modify the amount of the first leg of the pair
        df.loc[indices[0], 'amount'] *= np.random.uniform(1.05, 1.15)

    # 2. Missing Transactions (10% of pairs)
    num_missing = int(len(df['transaction_id'].unique()) * 0.10)
    tx_ids_to_break = np.random.choice(df['transaction_id'].unique(), num_missing, replace=False)
    indices_to_drop = []
    for tx_id in tx_ids_to_break:
        indices = df[df['transaction_id'] == tx_id].index
        indices_to_drop.append(indices[0]) # Drop one leg of the pair
    df = df.drop(indices_to_drop)

    print("Intercompany patterns embedded.")
    return df.sample(frac=1).reset_index(drop=True)

def generate_intercompany_transactions(num_pairs: int):
    """Generates intercompany transactions with embedded reconciliation issues."""
    print(f"\nGenerating {num_pairs} intercompany transaction pairs...")
    data = []
    entities = ['Entity A', 'Entity B', 'Entity C', 'Entity D', 'Entity E']

    for i in range(num_pairs):
        tx_id = f"IC-{i+200}"
        amount = generate_realistic_amount(1000, 100000, 0.4)
        tx_date = fake.date_between(start_date=START_DATE, end_date=END_DATE)
        source, dest = np.random.choice(entities, 2, replace=False)
        
        # Create the pair
        data.append({
            'transaction_id': tx_id,
            'source_entity': source,
            'destination_entity': dest,
            'amount': amount,
            'currency': 'USD',
            'transaction_date': tx_date,
            'description': f"Management fee from {source} to {dest}"
        })
        data.append({
            'transaction_id': tx_id,
            'source_entity': dest, # Reversed
            'destination_entity': source, # Reversed
            'amount': amount,
            'currency': 'USD',
            'transaction_date': tx_date,
            'description': f"Management fee to {dest} from {source}"
        })

    df = pd.DataFrame(data)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # Embed reconciliation issues
    df = _embed_ic_patterns(df)

    output_path = SUBLEDGERS_DIR / 'intercompany' / 'intercompany_transactions.csv'
    df.to_csv(output_path, index=False, date_format='%Y-%m-%d')
    print(f"Intercompany transactions saved to {output_path}")
    return df

# --- Bank Data Generation ---

def _embed_bank_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Helper function to embed bank forensic patterns."""
    print("Embedding Bank forensic patterns...")

    # 1. Kiting (1% of records, created in pairs)
    num_kiting = int(len(df) * 0.01)
    for i in range(num_kiting):
        amount = generate_realistic_amount(10000, 50000)
        date1 = fake.date_between(start_date=START_DATE, end_date=END_DATE - datetime.timedelta(days=1))
        date2 = date1 + datetime.timedelta(days=1)
        kiting_pair = [
            {'transaction_date': date1, 'amount': -amount, 'description': 'Transfer to Account #XXX', 'counterparty': 'Internal Transfer'},
            {'transaction_date': date2, 'amount': amount, 'description': 'Transfer from Account #YYY', 'counterparty': 'Internal Transfer'}
        ]
        df = pd.concat([df, pd.DataFrame(kiting_pair)], ignore_index=True)

    # 2. Unusual Counterparties (4% of records)
    num_unusual = int(len(df) * 0.04)
    unusual_indices = df.sample(n=num_unusual, random_state=60).index
    keywords = ["Cash Advance", "Quick Loan", "Payday Solutions", "Immediate Funding"]
    unusual_counterparties = [f"{kw} Inc." for kw in keywords]
    df.loc[unusual_indices, 'counterparty'] = np.random.choice(unusual_counterparties, size=num_unusual)
    df.loc[unusual_indices, 'amount'] = [generate_realistic_amount(-30000, -25000) for _ in range(num_unusual)]

    # 3. Velocity Anomalies (3% of records)
    num_velocity = int(len(df) * 0.03)
    velocity_indices = df.sample(n=num_velocity, random_state=61).index
    for idx in velocity_indices:
        base_row = df.loc[idx].copy()
        num_extra_tx = np.random.randint(2, 5)
        for i in range(num_extra_tx):
            new_row = base_row.copy()
            new_row['amount'] *= np.random.uniform(0.8, 1.2)
            df = pd.concat([df, new_row.to_frame().T], ignore_index=True)

    print("Bank patterns embedded.")
    return df.sample(frac=1).reset_index(drop=True)

def generate_bank_statements(num_records: int):
    """Generates bank statement files with embedded forensic patterns."""
    print(f"\nGenerating {num_records} bank transactions...")
    data = []
    counterparties = [fake.company() for _ in range(num_records // 20)]

    for i in range(num_records):
        data.append({
            'transaction_date': fake.date_between(start_date=START_DATE, end_date=END_DATE),
            'amount': generate_realistic_amount(-10000, 10000, 0.5),
            'description': fake.text(max_nb_chars=50),
            'counterparty': np.random.choice(counterparties)
        })

    df = pd.DataFrame(data)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])

    # Embed forensic patterns
    df = _embed_bank_patterns(df)

    output_path = SUBLEDGERS_DIR / 'bank_statements' / 'bank_statement_aug.csv'
    df.to_csv(output_path, index=False, date_format='%Y-%m-%d')
    print(f"Bank statements saved to {output_path}")
    return df

# --- Supporting Data Generation ---

def generate_supporting_files(ap_df: pd.DataFrame, ar_df: pd.DataFrame):
    """Generates all other supporting CSV files needed for the close."""
    print("\nGenerating supporting files...")

    # 1. Generate Chart of Accounts
    coa_data = [
        {'account_id': 1010, 'account_name': 'Cash', 'category': 'Assets', 'subcategory': 'Current Assets'},
        {'account_id': 1200, 'account_name': 'Accounts Receivable', 'category': 'Assets', 'subcategory': 'Current Assets'},
        {'account_id': 1500, 'account_name': 'Prepaid Expenses', 'category': 'Assets', 'subcategory': 'Current Assets'},
        {'account_id': 1700, 'account_name': 'Fixed Assets', 'category': 'Assets', 'subcategory': 'Long-Term Assets'},
        {'account_id': 2010, 'account_name': 'Accounts Payable', 'category': 'Liabilities', 'subcategory': 'Current Liabilities'},
        {'account_id': 2100, 'account_name': 'Accrued Expenses', 'category': 'Liabilities', 'subcategory': 'Current Liabilities'},
        {'account_id': 3000, 'account_name': 'Common Stock', 'category': 'Equity', 'subcategory': 'Contributed Capital'},
        {'account_id': 3500, 'account_name': 'Retained Earnings', 'category': 'Equity', 'subcategory': 'Retained Earnings'},
        {'account_id': 4000, 'account_name': 'Sales Revenue', 'category': 'Revenue', 'subcategory': 'Sales'},
        {'account_id': 5010, 'account_name': 'Cost of Goods Sold', 'category': 'Expenses', 'subcategory': 'COGS'},
        {'account_id': 6000, 'account_name': 'Salaries and Wages', 'category': 'Expenses', 'subcategory': 'Operating Expenses'},
        {'account_id': 6100, 'account_name': 'Rent Expense', 'category': 'Expenses', 'subcategory': 'Operating Expenses'},
        {'account_id': 6200, 'account_name': 'Utilities Expense', 'category': 'Expenses', 'subcategory': 'Operating Expenses'},
    ]
    coa_df = pd.DataFrame(coa_data)
    coa_path = SUPPORTING_DIR / 'chart_of_accounts.csv'
    coa_df.to_csv(coa_path, index=False)
    print(f"Chart of Accounts saved to {coa_path}")

    # 2. Generate Trial Balance based on subledgers
    ar_total = ar_df['amount'].sum()
    ap_total = ap_df['amount'].sum()

    tb_data = {
        'account_id': [1010, 1200, 1700, 2010, 3000, 3500, 4000, 5010, 6000, 6100, 6200],
        'account_name': ['Cash', 'Accounts Receivable', 'Fixed Assets', 'Accounts Payable', 'Common Stock', 'Retained Earnings', 'Sales Revenue', 'Cost of Goods Sold', 'Salaries and Wages', 'Rent Expense', 'Utilities Expense'],
        'debit': [500000, ar_total, 750000, 0, 0, 0, 0, 350000, 200000, 50000, 15000],
        'credit': [0, 0, 0, ap_total, 600000, 400000, 800000, 0, 0, 0, 0]
    }
    tb_df = pd.DataFrame(tb_data)
    
    # Balance the trial balance using cash
    debit_sum = tb_df['debit'].sum()
    credit_sum = tb_df['credit'].sum()
    cash_adjustment = credit_sum - debit_sum
    tb_df.loc[tb_df['account_id'] == 1010, 'debit'] += cash_adjustment

    tb_path = SUPPORTING_DIR / 'trial_balance_aug.csv'
    tb_df.to_csv(tb_path, index=False)
    print(f"Trial Balance saved to {tb_path}")

    # 3. Generate other supporting files (e.g., Accruals)
    accruals_data = [
        {'accrual_id': 'ACC-001', 'description': 'Unbilled legal services', 'amount': 15000, 'status': 'Pending'},
        {'accrual_id': 'ACC-002', 'description': 'Q3 Bonus Accrual', 'amount': 120000, 'status': 'Pending'},
    ]
    accruals_df = pd.DataFrame(accruals_data)
    accruals_path = SUPPORTING_DIR / 'accruals.csv'
    accruals_df.to_csv(accruals_path, index=False)
    print(f"Accruals saved to {accruals_path}")

    print("Supporting files generated.")

# --- Main Execution ---

def main():
    """Main function to orchestrate the generation of the entire dataset."""
    print("--- Starting Master Dataset Generation ---")

    ap_df = generate_ap_subledger(NUM_AP_TRANSACTIONS)
    ar_df = generate_ar_subledger(NUM_AR_TRANSACTIONS)
    generate_intercompany_transactions(NUM_IC_PAIRS)
    generate_bank_statements(NUM_BANK_TRANSACTIONS)
    generate_supporting_files(ap_df, ar_df)

    print("\n--- Master Dataset Generation Complete ---")
    print(f"All data files have been created in {DATA_DIR}")

if __name__ == '__main__':
    main()

