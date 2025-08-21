"""
Configurable forensic scenario generator for testing and training purposes.
"""
from __future__ import annotations
from ..state import CloseState
from ..console import Console
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import random

class ScenarioConfig:
    """Configuration for forensic scenario generation."""
    
    def __init__(self):
        self.scenarios = {
            "timing_differences": {
                "enabled": True,
                "frequency": 0.15,  # 15% of transactions
                "amount_range": (10000, 100000),
                "date_shift_days": (1, 5)
            },
            "duplicate_payments": {
                "enabled": True,
                "frequency": 0.05,  # 5% of AP transactions
                "amount_range": (5000, 50000),
                "duplicate_count": (2, 3)
            },
            "fx_revaluation": {
                "enabled": True,
                "frequency": 0.1,  # 10% of foreign currency transactions
                "rate_change_pct": (0.02, 0.08),  # 2-8% rate changes
                "currencies": ["EUR", "GBP", "JPY"]
            },
            "unrecorded_transactions": {
                "enabled": True,
                "frequency": 0.08,  # 8% missing from books
                "amount_range": (1000, 25000),
                "transaction_types": ["bank_fees", "interest", "adjustments"]
            },
            "accrual_reversals": {
                "enabled": True,
                "frequency": 0.12,  # 12% of accruals fail to reverse
                "amount_range": (15000, 75000),
                "reversal_delay_days": (1, 10)
            }
        }

def node_generate_scenarios(state: CloseState, *, console: Console) -> CloseState:
    """Generate configurable forensic scenarios for testing."""
    console.banner("Scenario Generation")
    
    config = ScenarioConfig()
    data = state.get("data", {})
    
    if not data:
        console.line("scenario_gen", "No Data", "warning", det=True)
        return {"scenarios_applied": []}
    
    scenarios_applied = []
    
    # Apply each enabled scenario type
    for scenario_type, scenario_config in config.scenarios.items():
        if scenario_config["enabled"]:
            applied = apply_scenario(scenario_type, scenario_config, data, console)
            scenarios_applied.extend(applied)
    
    console.line("scenario_gen", "Complete", "success", det=True,
                details=f"Applied {len(scenarios_applied)} scenarios")
    
    return {"scenarios_applied": scenarios_applied, "modified_data": data}

def apply_scenario(scenario_type: str, config: Dict, data: Dict, console: Console) -> List[Dict[str, Any]]:
    """Apply a specific scenario type to the data."""
    
    scenarios = {
        "timing_differences": apply_timing_differences,
        "duplicate_payments": apply_duplicate_payments,
        "fx_revaluation": apply_fx_revaluation,
        "unrecorded_transactions": apply_unrecorded_transactions,
        "accrual_reversals": apply_accrual_reversals
    }
    
    if scenario_type in scenarios:
        return scenarios[scenario_type](config, data, console)
    
    return []

def apply_timing_differences(config: Dict, data: Dict, console: Console) -> List[Dict[str, Any]]:
    """Apply timing difference scenarios."""
    applied = []
    
    if "ar" not in data or "bank" not in data:
        return applied
    
    ar_df = data["ar"]
    bank_df = data["bank"]
    
    # Select random AR transactions for timing issues
    num_scenarios = int(len(ar_df) * config["frequency"])
    selected_indices = random.sample(range(len(ar_df)), min(num_scenarios, len(ar_df)))
    
    for idx in selected_indices:
        ar_row = ar_df.iloc[idx]
        
        # Find corresponding bank transaction
        matching_bank = bank_df[
            (abs(bank_df['amount'] - ar_row['amount']) < 0.01) &
            (bank_df['entity'] == ar_row['entity'])
        ]
        
        if not matching_bank.empty:
            bank_idx = matching_bank.index[0]
            
            # Shift the bank transaction date
            shift_days = random.randint(*config["date_shift_days"])
            original_date = pd.to_datetime(bank_df.loc[bank_idx, 'date'])
            
            # Randomly shift forward or backward across period boundary
            if random.choice([True, False]):
                new_date = original_date + timedelta(days=shift_days)
            else:
                new_date = original_date - timedelta(days=shift_days)
            
            # Update the bank transaction date
            data["bank"].loc[bank_idx, 'date'] = new_date.strftime('%Y-%m-%d')
            
            scenario = {
                "type": "timing_difference",
                "entity": ar_row['entity'],
                "ar_invoice": ar_row['invoice_id'],
                "bank_txn": bank_df.loc[bank_idx, 'bank_txn_id'],
                "amount": ar_row['amount'],
                "original_date": original_date.strftime('%Y-%m-%d'),
                "shifted_date": new_date.strftime('%Y-%m-%d'),
                "shift_days": shift_days,
                "description": f"Payment timing shifted by {shift_days} days"
            }
            applied.append(scenario)
            
            console.line("scenario_gen", "Timing", "applied", det=True,
                        details=f"{ar_row['entity']} ${ar_row['amount']:,.0f} +{shift_days}d")
    
    return applied

def apply_duplicate_payments(config: Dict, data: Dict, console: Console) -> List[Dict[str, Any]]:
    """Apply duplicate payment scenarios."""
    applied = []
    
    if "ap" not in data:
        return applied
    
    ap_df = data["ap"]
    
    # Select random AP transactions for duplication
    num_scenarios = int(len(ap_df) * config["frequency"])
    selected_indices = random.sample(range(len(ap_df)), min(num_scenarios, len(ap_df)))
    
    for idx in selected_indices:
        ap_row = ap_df.iloc[idx]
        
        # Create duplicate entries
        duplicate_count = random.randint(*config["duplicate_count"])
        
        for i in range(1, duplicate_count):  # Start from 1 to keep original
            duplicate_row = ap_row.copy()
            
            # Modify payment reference to make it unique
            original_ref = duplicate_row['payment_ref']
            duplicate_row['payment_ref'] = f"{original_ref}-DUP{i}"
            
            # Slightly vary the payment date
            original_date = pd.to_datetime(duplicate_row['payment_date'])
            if pd.notna(original_date):
                new_date = original_date + timedelta(days=random.randint(1, 7))
                duplicate_row['payment_date'] = new_date.strftime('%Y-%m-%d')
            else:
                # Use a default date if original is NaT
                duplicate_row['payment_date'] = '2025-08-15'
            
            # Add to dataframe
            data["ap"] = pd.concat([data["ap"], duplicate_row.to_frame().T], ignore_index=True)
        
        scenario = {
            "type": "duplicate_payment",
            "entity": ap_row['entity'],
            "vendor": ap_row['vendor_name'],
            "original_bill": ap_row['bill_id'],
            "amount": ap_row.get('amount_usd', ap_row.get('amount_local', 0)),
            "duplicate_count": duplicate_count,
            "total_overpayment": ap_row.get('amount_usd', ap_row.get('amount_local', 0)) * (duplicate_count - 1),
            "description": f"Invoice paid {duplicate_count} times"
        }
        applied.append(scenario)
        
        amount_display = ap_row.get('amount_usd', ap_row.get('amount_local', 0))
        console.line("scenario_gen", "Duplicate", "applied", det=True,
                    details=f"{ap_row['vendor_name']} ${amount_display:,.0f} x{duplicate_count}")
    
    return applied

def apply_fx_revaluation(config: Dict, data: Dict, console: Console) -> List[Dict[str, Any]]:
    """Apply FX revaluation scenarios."""
    applied = []
    
    # Apply to intercompany and foreign currency transactions
    for data_type in ["intercompany", "ar", "ap"]:
        if data_type not in data:
            continue
        
        df = data[data_type]
        
        # Find foreign currency transactions
        if 'currency' in df.columns:
            foreign_txns = df[df['currency'].isin(config["currencies"])]
        else:
            continue
        
        if foreign_txns.empty:
            continue
        
        # Select transactions for FX revaluation
        num_scenarios = int(len(foreign_txns) * config["frequency"])
        selected_indices = random.sample(range(len(foreign_txns)), min(num_scenarios, len(foreign_txns)))
        
        for idx in selected_indices:
            fx_row = foreign_txns.iloc[idx]
            currency = fx_row['currency']
            
            # Calculate new FX rate
            rate_change = random.uniform(*config["rate_change_pct"])
            if random.choice([True, False]):
                rate_change = -rate_change  # Negative change
            
            # Apply FX impact (simplified calculation)
            original_amount = fx_row.get('amount_usd', fx_row.get('amount', 0))
            fx_impact = original_amount * rate_change
            
            scenario = {
                "type": "fx_revaluation",
                "entity": fx_row['entity'],
                "currency": currency,
                "original_amount": original_amount,
                "fx_impact": fx_impact,
                "rate_change_pct": rate_change * 100,
                "data_type": data_type,
                "description": f"{currency} revaluation impact {rate_change*100:.1f}%"
            }
            applied.append(scenario)
            
            console.line("scenario_gen", "FX Reval", "applied", det=True,
                        details=f"{currency} ${fx_impact:,.0f} ({rate_change*100:+.1f}%)")
    
    return applied

def apply_unrecorded_transactions(config: Dict, data: Dict, console: Console) -> List[Dict[str, Any]]:
    """Apply unrecorded transaction scenarios."""
    applied = []
    
    if "bank" not in data:
        return applied
    
    bank_df = data["bank"]
    
    # Select random bank transactions to "hide" from books
    num_scenarios = int(len(bank_df) * config["frequency"])
    selected_indices = random.sample(range(len(bank_df)), min(num_scenarios, len(bank_df)))
    
    for idx in selected_indices:
        bank_row = bank_df.iloc[idx]
        
        # Create unrecorded transaction
        txn_type = random.choice(config["transaction_types"])
        amount = random.uniform(*config["amount_range"])
        
        # Add unrecorded transaction to bank but not to books
        unrecorded_txn = {
            'bank_txn_id': f"UNREC-{len(bank_df) + len(applied)}",
            'entity': bank_row['entity'],
            'date': bank_row['date'],
            'amount': -amount if txn_type == "bank_fees" else amount,
            'description': f"Unrecorded {txn_type}",
            'counterparty': f"{txn_type.title()} Transaction",
            'period': bank_row['period']
        }
        
        # Add to bank data
        data["bank"] = pd.concat([data["bank"], pd.DataFrame([unrecorded_txn])], ignore_index=True)
        
        scenario = {
            "type": "unrecorded_transaction",
            "entity": bank_row['entity'],
            "transaction_type": txn_type,
            "amount": amount,
            "bank_txn_id": unrecorded_txn['bank_txn_id'],
            "description": f"Unrecorded {txn_type} transaction"
        }
        applied.append(scenario)
        
        console.line("scenario_gen", "Unrecorded", "applied", det=True,
                    details=f"{bank_row['entity']} {txn_type} ${amount:,.0f}")
    
    return applied

def apply_accrual_reversals(config: Dict, data: Dict, console: Console) -> List[Dict[str, Any]]:
    """Apply failed accrual reversal scenarios."""
    applied = []
    
    if "supporting" not in data or "accruals" not in data["supporting"]:
        return applied
    
    accruals_df = data["supporting"]["accruals"]
    
    # Select accruals that should have reversed but didn't
    num_scenarios = int(len(accruals_df) * config["frequency"])
    selected_indices = random.sample(range(len(accruals_df)), min(num_scenarios, len(accruals_df)))
    
    for idx in selected_indices:
        accrual_row = accruals_df.iloc[idx]
        
        # Create scenario where accrual wasn't properly reversed
        reversal_delay = random.randint(*config["reversal_delay_days"])
        
        scenario = {
            "type": "accrual_reversal_failure",
            "entity": accrual_row['entity'],
            "accrual_id": accrual_row.get('accrual_id', f"ACR-{idx}"),
            "amount": accrual_row['amount'],
            "original_date": accrual_row['accrual_date'],
            "expected_reversal": accrual_row['reversal_date'],
            "actual_delay_days": reversal_delay,
            "description": f"Accrual reversal delayed by {reversal_delay} days"
        }
        applied.append(scenario)
        
        console.line("scenario_gen", "Accrual", "applied", det=True,
                    details=f"{accrual_row['entity']} ${accrual_row['amount']:,.0f} +{reversal_delay}d")
    
    return applied
