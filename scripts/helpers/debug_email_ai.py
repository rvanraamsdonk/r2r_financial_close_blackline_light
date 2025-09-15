#!/usr/bin/env python3

import json
from pathlib import Path
import sys
sys.path.append('.')

from src.r2r.engines.email_evidence import _load_transaction_data
from src.r2r.state import R2RState

# Create a mock state to test transaction data loading
from pathlib import Path as PathLib
state = R2RState(
    period="2025-08",
    repo_root="/Users/robertvanraamsdonk/Code/r2r_financial_close_blackline_light",
    data_path="/Users/robertvanraamsdonk/Code/r2r_financial_close_blackline_light/data",
    out_path="/Users/robertvanraamsdonk/Code/r2r_financial_close_blackline_light/out"
)

# Test transaction data loading
transaction_data = _load_transaction_data(state)

print("=== TRANSACTION DATA DEBUG ===")
print(f"Found {len(transaction_data)} modules with transaction data:")
for module, transactions in transaction_data.items():
    print(f"\n{module}:")
    print(f"  Count: {len(transactions)}")
    if transactions:
        print(f"  Sample: {transactions[0]}")

# Test email template exists
template_path = Path("src/r2r/ai/templates/email_analysis.md")
print(f"\n=== TEMPLATE DEBUG ===")
print(f"Template exists: {template_path.exists()}")
if template_path.exists():
    print(f"Template size: {template_path.stat().st_size} bytes")

# Load sample email for testing
emails_path = Path("data/supporting/emails.json")
if emails_path.exists():
    with emails_path.open() as f:
        email_data = json.load(f)
    
    sample_email = email_data["items"][1]  # Salesforce email
    print(f"\n=== SAMPLE EMAIL ===")
    print(f"Subject: {sample_email['subject']}")
    print(f"Body: {sample_email['body'][:100]}...")
