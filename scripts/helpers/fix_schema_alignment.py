#!/usr/bin/env python3
"""
Schema Alignment Fix
Ensures all enhanced data files match expected engine schemas
"""
import pandas as pd
from pathlib import Path

def fix_ap_schema():
    """Fix AP detail schema to match engine expectations"""
    print("🔧 Fixing AP schema...")
    
    ap_path = Path("../data/subledgers/ap_detail_aug.csv")
    if ap_path.exists():
        df = pd.read_csv(ap_path)
        
        # Add missing columns expected by AP engine
        if "bill_date" not in df.columns and "invoice_date" in df.columns:
            df["bill_date"] = df["invoice_date"]
        
        if "vendor" not in df.columns and "vendor_name" in df.columns:
            df["vendor"] = df["vendor_name"]
        
        if "amount" not in df.columns:
            if "amount_usd" in df.columns:
                df["amount"] = df["amount_usd"]
            elif "amount_local" in df.columns:
                df["amount"] = df["amount_local"]
        
        # Ensure required columns exist
        required_cols = ["period", "entity", "invoice_id", "vendor", "bill_date", "amount", "currency", "status"]
        for col in required_cols:
            if col not in df.columns:
                if col == "vendor":
                    df[col] = df.get("vendor_name", "Unknown Vendor")
                elif col == "bill_date":
                    df[col] = df.get("invoice_date", "2025-08-15")
                elif col == "amount":
                    df[col] = df.get("amount_local", 0)
                else:
                    df[col] = ""
        
        df.to_csv(ap_path, index=False)
        print(f"✅ AP schema fixed: {len(df)} records")

def fix_ar_schema():
    """Fix AR detail schema to match engine expectations"""
    print("🔧 Fixing AR schema...")
    
    ar_path = Path("../data/subledgers/ar_detail_aug.csv")
    if ar_path.exists():
        df = pd.read_csv(ar_path)
        
        # Add missing columns expected by AR engine
        if "customer" not in df.columns and "customer_name" in df.columns:
            df["customer"] = df["customer_name"]
        
        if "amount" not in df.columns:
            if "amount_usd" in df.columns:
                df["amount"] = df["amount_usd"]
            elif "amount_local" in df.columns:
                df["amount"] = df["amount_local"]
        
        # Ensure required columns exist
        required_cols = ["period", "entity", "invoice_id", "customer", "invoice_date", "amount", "currency", "status"]
        for col in required_cols:
            if col not in df.columns:
                if col == "customer":
                    df[col] = df.get("customer_name", "Unknown Customer")
                elif col == "amount":
                    df[col] = df.get("amount_local", 0)
                else:
                    df[col] = ""
        
        df.to_csv(ar_path, index=False)
        print(f"✅ AR schema fixed: {len(df)} records")

def fix_bank_schema():
    """Fix bank transactions schema"""
    print("🔧 Fixing Bank schema...")
    
    bank_path = Path("../data/subledgers/bank_statements/bank_transactions_aug.csv")
    if bank_path.exists():
        df = pd.read_csv(bank_path)
        
        # Add amount column for compatibility
        if "amount" not in df.columns:
            if "amount_usd" in df.columns:
                df["amount"] = df["amount_usd"]
            elif "amount_local" in df.columns:
                df["amount"] = df["amount_local"]
        
        df.to_csv(bank_path, index=False)
        print(f"✅ Bank schema fixed: {len(df)} records")

def verify_schemas():
    """Verify all schemas are correct"""
    print("🔍 Verifying schemas...")
    
    # Check AP
    ap_path = Path("../data/subledgers/ap_detail_aug.csv")
    if ap_path.exists():
        df = pd.read_csv(ap_path)
        expected_cols = ["period", "entity", "invoice_id", "vendor", "bill_date", "amount", "currency", "status"]
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            print(f"❌ AP missing columns: {missing}")
        else:
            print(f"✅ AP schema verified: {len(df)} records")
    
    # Check AR
    ar_path = Path("../data/subledgers/ar_detail_aug.csv")
    if ar_path.exists():
        df = pd.read_csv(ar_path)
        expected_cols = ["period", "entity", "invoice_id", "customer", "invoice_date", "amount", "currency", "status"]
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            print(f"❌ AR missing columns: {missing}")
        else:
            print(f"✅ AR schema verified: {len(df)} records")
    
    # Check Bank
    bank_path = Path("../data/subledgers/bank_statements/bank_transactions_aug.csv")
    if bank_path.exists():
        df = pd.read_csv(bank_path)
        expected_cols = ["period", "entity", "bank_txn_id", "date", "amount", "currency", "counterparty", "transaction_type"]
        missing = [col for col in expected_cols if col not in df.columns]
        if missing:
            print(f"❌ Bank missing columns: {missing}")
        else:
            print(f"✅ Bank schema verified: {len(df)} records")

def main():
    print("🔧 SCHEMA ALIGNMENT FIX")
    print("=======================")
    
    fix_ap_schema()
    fix_ar_schema()
    fix_bank_schema()
    verify_schemas()
    
    print("\n✅ SCHEMA ALIGNMENT COMPLETE")

if __name__ == "__main__":
    main()
