#!/usr/bin/env python3
"""
Complete Data Enhancement Strategy Implementation
"""
import pandas as pd
import numpy as np
from pathlib import Path
import shutil
import random
from datetime import datetime, timedelta

random.seed(42)
np.random.seed(42)

def main():
    print("🚀 COMPLETE DATA ENHANCEMENT STRATEGY")
    print("=====================================")
    
    # Step 1: Reorganize data structure
    reorganize_data_structure()
    
    # Step 2: Expand trial balance
    data_path = Path("../data")
    expand_trial_balance(data_path)
    
    # Step 3: Expand subledgers
    expand_ap_detail(data_path)
    expand_ar_detail(data_path)
    
    # Step 4: Create bank complexity
    expand_bank_statements(data_path)
    
    print("\n✅ COMPLETE DATA ENHANCEMENT FINISHED")
    print("=====================================")

def reorganize_data_structure():
    """Reorganize from /lite to proper /data structure"""
    print("📁 Reorganizing data structure...")
    
    base_path = Path("../data")
    lite_path = base_path / "lite"
    
    # Create new structure
    (base_path / "supporting").mkdir(exist_ok=True)
    (base_path / "subledgers").mkdir(exist_ok=True)
    (base_path / "subledgers" / "bank_statements").mkdir(exist_ok=True)
    (base_path / "subledgers" / "intercompany").mkdir(exist_ok=True)
    
    # Move files from lite to proper locations
    if lite_path.exists():
        # Core files
        for file in ["entities.csv", "chart_of_accounts.csv", "budget.csv"]:
            src = lite_path / file
            if src.exists():
                shutil.copy2(src, base_path / file)
        
        # Enhanced files
        enhanced_mappings = [
            ("fx_rates_enhanced.csv", "fx_rates.csv"),
            ("trial_balance_aug_enhanced.csv", "trial_balance_aug.csv"),
            ("subledgers/ap_detail_aug_enhanced.csv", "subledgers/ap_detail_aug.csv"),
            ("subledgers/ar_detail_aug_enhanced.csv", "subledgers/ar_detail_aug.csv"),
            ("subledgers/bank_statements/bank_transactions_aug_enhanced.csv", "subledgers/bank_statements/bank_transactions_aug.csv")
        ]
        
        for src_file, dst_file in enhanced_mappings:
            src = lite_path / src_file
            dst = base_path / dst_file
            if src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        
        # Supporting files
        supporting_src = lite_path / "supporting"
        if supporting_src.exists():
            for file in supporting_src.glob("*"):
                if file.is_file():
                    dst_name = file.name.replace("_enhanced", "")
                    shutil.copy2(file, base_path / "supporting" / dst_name)
    
    print("✅ Data structure reorganized")

def expand_trial_balance(data_path):
    """Expand trial balance to 200+ accounts"""
    print("📊 Expanding trial balance...")
    
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    # Account structure
    accounts = [
        # Assets 1000-1999
        (1000, "Cash and Cash Equivalents"), (1010, "Petty Cash"), (1020, "Money Market"),
        (1100, "Accounts Receivable"), (1110, "Notes Receivable"), (1200, "Allowance for Doubtful Accounts"),
        (1300, "Raw Materials"), (1310, "Work in Process"), (1320, "Finished Goods"),
        (1400, "Prepaid Insurance"), (1410, "Prepaid Rent"), (1420, "Prepaid Software"),
        (1500, "Land"), (1510, "Buildings"), (1520, "Equipment"), (1530, "Vehicles"),
        (1600, "Accumulated Depreciation - Buildings"), (1610, "Accumulated Depreciation - Equipment"),
        (1700, "Short-term Investments"), (1710, "Long-term Investments"),
        (1800, "Patents"), (1810, "Trademarks"), (1820, "Goodwill"),
        
        # Liabilities 2000-2999
        (2000, "Accounts Payable"), (2010, "Accrued Expenses"), (2020, "Payroll Liabilities"),
        (2030, "Tax Payable"), (2040, "Interest Payable"), (2050, "Customer Deposits"),
        (2100, "Bank Loans"), (2110, "Bonds Payable"), (2120, "Mortgage Payable"),
        (2200, "Deferred Revenue"), (2210, "Pension Obligations"),
        
        # Equity 3000-3999
        (3000, "Common Stock"), (3010, "Preferred Stock"), (3020, "Additional Paid-in Capital"),
        (3030, "Retained Earnings"), (3040, "Treasury Stock"), (3050, "Accumulated OCI"),
        
        # Revenue 4000-4999
        (4000, "Product Sales"), (4010, "Service Revenue"), (4020, "Licensing Revenue"),
        (4030, "Interest Income"), (4040, "Other Revenue"),
        
        # Expenses 5000-9999
        (5000, "Cost of Goods Sold"), (5010, "Direct Labor"), (5020, "Manufacturing Overhead"),
        (6000, "Salaries & Wages"), (6010, "Benefits"), (6020, "Rent"), (6030, "Utilities"),
        (6040, "Insurance"), (6050, "Professional Fees"), (6060, "Marketing"), (6070, "Travel"),
        (6080, "Office Supplies"), (6090, "Software Licenses"), (6100, "Depreciation"),
        (7000, "Interest Expense"), (7010, "Bank Fees"), (8000, "Other Expenses"),
        (9000, "Income Tax Expense")
    ]
    
    tb_data = []
    for entity in entities:
        currency = currencies[entity]
        for account_num, account_name in accounts:
            # Generate realistic balances
            if account_num < 2000:  # Assets
                balance = random.uniform(10000, 500000)
                if "Allowance" in account_name or "Accumulated" in account_name:
                    balance = -balance
            elif account_num < 3000:  # Liabilities
                balance = -random.uniform(10000, 300000)
            elif account_num < 4000:  # Equity
                balance = -random.uniform(50000, 1000000)
            elif account_num < 5000:  # Revenue
                balance = -random.uniform(100000, 1000000)
            else:  # Expenses
                balance = random.uniform(50000, 500000)
            
            # Currency adjustments
            if entity == "ENT101":
                balance *= 0.92
            elif entity == "ENT102":
                balance *= 0.79
            
            tb_data.append({
                "period": "2025-08",
                "entity": entity,
                "account": str(account_num),
                "account_name": account_name,
                "balance_usd": round(balance if entity == "ENT100" else balance / (0.92 if entity == "ENT101" else 0.79), 2),
                "balance_local": round(balance, 2),
                "local_currency": currency
            })
    
    # Add intentional imbalances
    for entity in entities:
        tb_data.append({
            "period": "2025-08",
            "entity": entity,
            "account": "9999",
            "account_name": "Suspense Account - Imbalance",
            "balance_usd": round(random.uniform(1000, 50000), 2),
            "balance_local": round(random.uniform(1000, 50000), 2),
            "local_currency": currencies[entity]
        })
    
    tb_df = pd.DataFrame(tb_data)
    tb_df.to_csv(data_path / "trial_balance_aug.csv", index=False)
    print(f"✅ Trial balance: {len(tb_df)} accounts")

def expand_ap_detail(data_path):
    """Expand AP to 500+ invoices"""
    print("📋 Expanding AP detail...")
    
    vendors = ["Microsoft", "Google", "Amazon", "Oracle", "SAP", "Adobe", "IBM", "Cisco"]
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    ap_data = []
    for i in range(500):
        entity = random.choice(entities)
        vendor = random.choice(vendors)
        currency = currencies[entity]
        
        invoice_date = datetime(2025, 8, random.randint(1, 31))
        due_date = invoice_date + timedelta(days=30)
        amount = random.uniform(5000, 100000)
        
        ap_data.append({
            "period": "2025-08",
            "entity": entity,
            "invoice_id": f"AP{50000+i:06d}",
            "vendor_name": f"{vendor} Corporation",
            "invoice_date": invoice_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "amount_local": round(amount, 2),
            "amount_usd": round(amount * (1.0 if currency == "USD" else 1.08 if currency == "EUR" else 1.27), 2),
            "currency": currency,
            "status": random.choice(["Outstanding", "Paid", "Disputed"]),
            "description": f"{vendor} - Professional Services"
        })
    
    ap_df = pd.DataFrame(ap_data)
    ap_df.to_csv(data_path / "subledgers" / "ap_detail_aug.csv", index=False)
    print(f"✅ AP detail: {len(ap_df)} invoices")

def expand_ar_detail(data_path):
    """Expand AR to 300+ customer invoices"""
    print("💰 Expanding AR detail...")
    
    customers = ["Apple", "Tesla", "NVIDIA", "Meta", "Netflix", "Uber", "Airbnb", "Spotify"]
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    ar_data = []
    for i in range(300):
        entity = random.choice(entities)
        customer = random.choice(customers)
        currency = currencies[entity]
        
        days_old = random.randint(0, 120)
        invoice_date = datetime(2025, 8, 31) - timedelta(days=days_old)
        due_date = invoice_date + timedelta(days=30)
        amount = random.uniform(25000, 500000)
        
        status = "Outstanding" if days_old < 60 else random.choice(["Outstanding", "Disputed", "Collection"])
        
        ar_data.append({
            "period": "2025-08",
            "entity": entity,
            "invoice_id": f"AR{60000+i:06d}",
            "customer_name": f"{customer} Inc",
            "invoice_date": invoice_date.strftime("%Y-%m-%d"),
            "due_date": due_date.strftime("%Y-%m-%d"),
            "amount_local": round(amount, 2),
            "amount_usd": round(amount * (1.0 if currency == "USD" else 1.08 if currency == "EUR" else 1.27), 2),
            "currency": currency,
            "status": status,
            "days_outstanding": days_old,
            "aging_bucket": "0-30" if days_old <= 30 else "31-60" if days_old <= 60 else "60+",
            "description": f"{customer} - Product Sales"
        })
    
    ar_df = pd.DataFrame(ar_data)
    ar_df.to_csv(data_path / "subledgers" / "ar_detail_aug.csv", index=False)
    print(f"✅ AR detail: {len(ar_df)} invoices")

def expand_bank_statements(data_path):
    """Create multiple bank accounts with unmatched transactions"""
    print("🏦 Expanding bank statements...")
    
    entities = ["ENT100", "ENT101", "ENT102"]
    currencies = {"ENT100": "USD", "ENT101": "EUR", "ENT102": "GBP"}
    
    bank_data = []
    txn_id = 70000
    
    for entity in entities:
        currency = currencies[entity]
        
        # Generate 200+ transactions per entity
        for i in range(200):
            date = datetime(2025, 8, random.randint(1, 31))
            amount = random.uniform(1000, 100000)
            
            # Transaction types
            txn_types = ["Wire Transfer", "ACH Credit", "ACH Debit", "Check", "Fee", "Interest"]
            txn_type = random.choice(txn_types)
            
            # Some unmatched scenarios
            if random.random() < 0.15:  # 15% unmatched
                description = f"UNMATCHED - {txn_type}"
                counterparty = "Unknown Counterparty"
            else:
                counterparty = random.choice(["Microsoft", "Google", "Apple", "Customer Payment"])
                description = f"{txn_type} - {counterparty}"
            
            bank_data.append({
                "period": "2025-08",
                "entity": entity,
                "bank_txn_id": f"BNK{txn_id:06d}",
                "date": date.strftime("%Y-%m-%d"),
                "amount_local": round(amount if txn_type != "ACH Debit" else -amount, 2),
                "amount_usd": round((amount if txn_type != "ACH Debit" else -amount) * (1.0 if currency == "USD" else 1.08 if currency == "EUR" else 1.27), 2),
                "currency": currency,
                "counterparty": counterparty,
                "transaction_type": txn_type,
                "description": description,
                "reference": f"REF{random.randint(100000, 999999)}"
            })
            txn_id += 1
    
    bank_df = pd.DataFrame(bank_data)
    bank_df.to_csv(data_path / "subledgers" / "bank_statements" / "bank_transactions_aug.csv", index=False)
    print(f"✅ Bank statements: {len(bank_df)} transactions")
    print(f"   Unmatched: {len(bank_df[bank_df['description'].str.contains('UNMATCHED')])}")

if __name__ == "__main__":
    main()
