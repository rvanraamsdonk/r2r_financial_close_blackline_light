"""
Data loading mocks for testing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional
from unittest.mock import Mock

import pandas as pd


class MockDataRepo:
    """Mock data repository for testing without file dependencies."""
    
    def __init__(self, use_static: bool = True):
        self.use_static = use_static
        self._setup_mock_data()
    
    def _setup_mock_data(self):
        """Setup predictable mock data."""
        self.entities_df = pd.DataFrame([
            {"entity": "ENT100", "name": "Test Entity 1", "currency": "USD", "home_currency": "USD"},
            {"entity": "ENT200", "name": "Test Entity 2", "currency": "EUR", "home_currency": "USD"},
        ])
        
        self.coa_df = pd.DataFrame([
            {"account": "1000", "name": "Cash", "type": "Asset", "class": "BS"},
            {"account": "1100", "name": "AR", "type": "Asset", "class": "BS"},
            {"account": "2000", "name": "AP", "type": "Liability", "class": "BS"},
            {"account": "5000", "name": "Revenue", "type": "Revenue", "class": "IS"},
        ])
        
        self.tb_df = pd.DataFrame([
            {"period": "2025-08", "entity": "TEST_ENT", "account": "1000", "balance": 100000.0, "balance_usd": 100000.0},
            {"period": "2025-08", "entity": "TEST_ENT", "account": "1100", "balance": 50000.0, "balance_usd": 50000.0},
            {"period": "2025-08", "entity": "TEST_ENT", "account": "2000", "balance": -75000.0, "balance_usd": -75000.0},
            {"period": "2025-08", "entity": "TEST_ENT", "account": "5000", "balance": -75000.0, "balance_usd": -75000.0},
        ])
        
        self.fx_df = pd.DataFrame([
            {"period": "2025-08", "currency": "USD", "rate": 1.0},
            {"period": "2025-08", "currency": "EUR", "rate": 1.092},
        ])
        
        self.ap_details_df = pd.DataFrame([
            {"entity_id": "ENT100", "vendor": "VENDOR001", "amount": 2000.0, "due_date": "2025-09-15", "invoice_date": "2025-08-15", "invoice_number": "INV001"},
            {"entity_id": "ENT100", "vendor": "VENDOR002", "amount": 1500.0, "due_date": "2025-09-30", "invoice_date": "2025-08-30", "invoice_number": "INV002"},
            {"entity_id": "ENT100", "vendor": "VENDOR003", "amount": 500.0, "due_date": "2025-07-15", "invoice_date": "2025-07-01", "invoice_number": "INV003"},  # Overdue
        ])
        
        self.bank_transactions_df = pd.DataFrame([
            {"period": "2025-08", "entity": "ENT100", "bank_txn_id": "TXN001", "amount": 1000.0, "date": "2025-08-15", "currency": "USD", "counterparty": "Customer A", "transaction_type": "Receipt", "description": "Payment received"},
            {"period": "2025-08", "entity": "ENT100", "bank_txn_id": "TXN002", "amount": -500.0, "date": "2025-08-16", "currency": "USD", "counterparty": "Bank", "transaction_type": "Fee", "description": "Bank fee"},
            {"period": "2025-08", "entity": "ENT100", "bank_txn_id": "TXN001", "amount": 1000.0, "date": "2025-08-15", "currency": "USD", "counterparty": "Customer A", "transaction_type": "Receipt", "description": "Payment received"},  # Duplicate for testing
            {"period": "2025-08", "entity": "ENT200", "bank_txn_id": "TXN003", "amount": 750.0, "date": "2025-08-17", "currency": "EUR", "counterparty": "Vendor B", "transaction_type": "Payment", "description": "Transfer"},
        ])
        
        self.ap_detail_df = pd.DataFrame([
            {
                "period": "2025-08", "entity": "ENT100", "bill_id": "BILL001",
                "vendor_name": "Test Vendor", "amount": 5000.0, "currency": "USD",
                "bill_date": "2025-08-01", "status": "Outstanding", "notes": "Test bill"
            }
        ])
        
        self.ar_detail_df = pd.DataFrame([
            {
                "period": "2025-08", "entity": "ENT100", "invoice_id": "INV001",
                "customer_name": "Test Customer", "amount": 3000.0, "currency": "USD",
                "invoice_date": "2025-08-01", "status": "Outstanding"
            }
        ])
        
        self.ar_detail_df = pd.DataFrame([
            {
                "period": "2025-08", "entity": "TEST_ENT", "invoice_id": "INV001",
                "customer_name": "Test Customer", "amount": 10000.0, "currency": "USD",
                "status": "Outstanding", "age_days": 30
            }
        ])


class MockStaticDataRepo(MockDataRepo):
    """Mock static data repository that simulates the StaticDataRepo behavior."""
    
    def load_entities(self, data_path: Path) -> pd.DataFrame:
        return self.entities_df
    
    def load_coa(self, data_path: Path) -> pd.DataFrame:
        return self.coa_df
    
    def load_tb(self, data_path: Path, period: str, entity: Optional[str] = None) -> pd.DataFrame:
        df = self.tb_df.copy()
        if entity and entity != "ALL":
            df = df[df["entity"] == entity]
        return df[df["period"] == period]
    
    def load_fx(self, data_path: Path, period: str) -> pd.DataFrame:
        return self.fx_df[self.fx_df["period"] == period]
    
    def load_bank_transactions(self, data_path: Path, period: str, entity: Optional[str] = None) -> pd.DataFrame:
        df = self.bank_transactions_df.copy()
        if entity and entity != "ALL":
            df = df[df["entity"] == entity]
        return df[df["period"] == period]
    
    def load_ap_detail(self, data_path: Path, period: str, entity: Optional[str] = None) -> pd.DataFrame:
        df = self.ap_detail_df.copy()
        if entity and entity != "ALL":
            df = df[df["entity"] == entity]
        return df[df["period"] == period]
    
    def load_ar_detail(self, data_path: Path, period: str, entity: Optional[str] = None) -> pd.DataFrame:
        df = self.ar_detail_df.copy()
        if entity and entity != "ALL":
            df = df[df["entity"] == entity]
        return df[df["period"] == period]


def patch_data_loading(monkeypatch, mock_repo: Optional[MockStaticDataRepo] = None):
    """Patch data loading functions to use mock data."""
    if mock_repo is None:
        mock_repo = MockStaticDataRepo()
    
    # Patch the main data loading functions
    monkeypatch.setattr("src.r2r.data.load_entities", lambda path: mock_repo.load_entities(path))
    monkeypatch.setattr("src.r2r.data.load_coa", lambda path: mock_repo.load_coa(path))
    monkeypatch.setattr("src.r2r.data.load_tb", lambda path, period, entity: mock_repo.load_tb(path, period, entity))
    monkeypatch.setattr("src.r2r.data.load_fx", lambda path, period: mock_repo.load_fx(path, period))
    
    # Patch static loader functions
    monkeypatch.setattr("src.r2r.data.static_loader.load_bank_transactions", 
                       lambda path, period, entity: mock_repo.load_bank_transactions(path, period, entity))
    monkeypatch.setattr("src.r2r.data.static_loader.load_ap_detail",
                       lambda path, period, entity: mock_repo.load_ap_detail(path, period, entity))
    monkeypatch.setattr("src.r2r.data.static_loader.load_ar_detail",
                       lambda path, period, entity: mock_repo.load_ar_detail(path, period, entity))
    
    return mock_repo
