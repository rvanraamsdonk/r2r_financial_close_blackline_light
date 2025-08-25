#!/usr/bin/env python3
"""
Quick fix for corrupted trial balance enhanced file
"""
import pandas as pd
from pathlib import Path

# Read the original trial balance structure
original_path = Path("../data/old/trial_balance_aug.csv")
enhanced_path = Path("../data/lite/trial_balance_aug_enhanced.csv")

# Load original to get structure
if original_path.exists():
    original_df = pd.read_csv(original_path)
    print(f"Original TB columns: {list(original_df.columns)}")
    
    # Add period column
    original_df['period'] = '2025-08'
    
    # Reorder columns to match expected format
    cols = ['period', 'entity', 'account', 'account_name', 'balance_usd', 'balance_local', 'local_currency']
    original_df = original_df[cols]
    
    # Save as enhanced version
    original_df.to_csv(enhanced_path, index=False)
    print(f"Fixed trial balance saved to {enhanced_path}")
    print(f"Shape: {original_df.shape}")
    print(f"Columns: {list(original_df.columns)}")
else:
    print(f"Original file not found at {original_path}")
