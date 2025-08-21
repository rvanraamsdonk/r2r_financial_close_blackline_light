"""
Static data loader for realistic financial close dataset.
Replaces synthetic data generation with curated forensic scenarios.
"""
from __future__ import annotations
import pandas as pd
import os
from pathlib import Path

class StaticDataRepo:
    """Loads static financial close dataset with embedded forensic scenarios."""
    
    def __init__(self, data_path: str = None):
        if data_path is None:
            # Default to data folder in project root
            project_root = Path(__file__).parent.parent.parent.parent
            self.data_path = project_root / "data"
        else:
            self.data_path = Path(data_path)
        
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data path not found: {self.data_path}")
        
        # Load all datasets
        self._load_core_data()
        self._load_subledgers()
        self._load_supporting_docs()
    
    def _load_core_data(self):
        """Load core financial data files."""
        self.entities = pd.read_csv(self.data_path / "entities.csv")
        self.coa = pd.read_csv(self.data_path / "chart_of_accounts.csv")
        self.trial_balance = pd.read_csv(self.data_path / "trial_balance_aug.csv")
        self.fx_rates = pd.read_csv(self.data_path / "fx_rates.csv")
        
        # Convert trial balance to GL format for compatibility
        self.gl = self.trial_balance.rename(columns={
            'balance_usd': 'balance'
        })[['entity', 'account', 'balance']].copy()
        self.gl['period'] = '2025-08'
        
        # Create July GL for variance analysis (10% different from August)
        self.gl_prev = self.gl.copy()
        self.gl_prev['period'] = '2025-07'
        self.gl_prev['balance'] = self.gl_prev['balance'] * 0.9  # 10% lower in July
    
    def _load_subledgers(self):
        """Load subledger detail files."""
        subledger_path = self.data_path / "subledgers"
        
        # AR and AP details
        self.ar = pd.read_csv(subledger_path / "ar_detail_aug.csv")
        self.ar['period'] = '2025-08'  # Add period column for compatibility
        # Rename columns for compatibility with matching agent
        self.ar = self.ar.rename(columns={'amount_usd': 'amount'})
        
        self.ap = pd.read_csv(subledger_path / "ap_detail_aug.csv")
        self.ap['period'] = '2025-08'  # Add period column for compatibility
        # Rename columns for compatibility
        self.ap = self.ap.rename(columns={'amount_usd': 'amount'})
        
        # Bank statements (combine all entities)
        bank_path = subledger_path / "bank_statements"
        bank_files = []
        
        for entity_file in bank_path.glob("ent*_aug.csv"):
            entity_id = entity_file.stem.split('_')[0].upper()  # ENT100, ENT101, ENT102
            bank_data = pd.read_csv(entity_file)
            bank_data['entity'] = entity_id
            bank_data['period'] = '2025-08'
            
            # Standardize columns for compatibility
            if 'amount_usd' in bank_data.columns:
                bank_data['amount'] = bank_data['amount_usd']
            elif 'amount_eur' in bank_data.columns:
                bank_data['amount'] = bank_data['amount_eur']
            elif 'amount_gbp' in bank_data.columns:
                bank_data['amount'] = bank_data['amount_gbp']
            
            bank_data['bank_txn_id'] = bank_data['transaction_id']
            bank_data['date'] = bank_data['transaction_date']
            bank_data['method'] = 'WIRE'  # Default method
            bank_data['currency'] = self.entities[self.entities['entity'] == entity_id]['home_currency'].iloc[0]
            
            bank_files.append(bank_data[['period', 'entity', 'bank_txn_id', 'date', 'amount', 'currency', 'method', 'counterparty']])
        
        self.bank = pd.concat(bank_files, ignore_index=True) if bank_files else pd.DataFrame()
        
        # Intercompany transactions
        ic_path = subledger_path / "intercompany"
        if (ic_path / "ic_transactions.csv").exists():
            ic_data = pd.read_csv(ic_path / "ic_transactions.csv")
            # Convert to expected format
            self.ic = pd.DataFrame({
                'period': '2025-08',
                'entity_src': ic_data['entity_src'],
                'entity_dst': ic_data['entity_dst'],
                'doc_id': ic_data['doc_id'],
                'amount_src': ic_data['amount_src'],
                'amount_dst': ic_data['amount_dst'],
                'currency': ic_data['currency_src']
            })
        else:
            self.ic = pd.DataFrame()
    
    def _load_supporting_docs(self):
        """Load supporting documents for forensic analysis."""
        supporting_path = self.data_path / "supporting"
        
        if (supporting_path / "accruals.csv").exists():
            self.accruals = pd.read_csv(supporting_path / "accruals.csv")
        else:
            self.accruals = pd.DataFrame()
        
        if (supporting_path / "journal_entries.csv").exists():
            self.journal_entries = pd.read_csv(supporting_path / "journal_entries.csv")
        else:
            self.journal_entries = pd.DataFrame()
            
        # Load email evidence
        import json
        if (supporting_path / "emails.json").exists():
            with open(supporting_path / "emails.json", 'r') as f:
                self.emails = json.load(f)
        else:
            self.emails = {"emails": []}
    
    def snapshot(self) -> dict[str, pd.DataFrame]:
        """Return snapshot compatible with existing system."""
        return {
            "entities": self.entities,
            "coa": self.coa,
            "fx": self.fx_rates,
            "budget": pd.DataFrame(),  # Not used in current system
            "gl": self.gl,
            "ar": self.ar,
            "ap": self.ap,
            "bank": self.bank,
            "ic": self.ic,
            "gl_prev": self.gl_prev
        }
    
    def get_forensic_scenarios(self) -> dict:
        """Return embedded forensic scenarios for analysis."""
        return {
            "timing_differences": {
                "description": "Customer payments received Aug 31, recorded Sep 1",
                "amount": 45000.00,
                "affected_accounts": ["1100", "1000"],
                "solution": "Cut-off adjustment entry"
            },
            "duplicate_transactions": {
                "description": "Salesforce invoice paid twice with different references",
                "amount": 12500.00,
                "affected_accounts": ["2000", "1000"],
                "solution": "Reverse duplicate payment"
            },
            "fx_revaluation": {
                "description": "EUR/USD rate change impacts intercompany balance",
                "amount": 5950.00,
                "affected_accounts": ["1400", "6000"],
                "solution": "FX gain/loss journal entry"
            },
            "accrual_reversal": {
                "description": "July payroll accrual not automatically reversed",
                "amount": 28000.00,
                "affected_accounts": ["2100", "5000"],
                "solution": "Manual reversal entry"
            }
        }
