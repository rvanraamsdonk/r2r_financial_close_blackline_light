"""
Unit tests for bank reconciliation engine.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, Mock
import pandas as pd

from src.r2r.engines.bank_recon import bank_reconciliation
from src.r2r.audit.log import AuditLogger
from tests.fixtures.mocks import MockAuditLogger, MockDataRepo
from tests.fixtures.helpers import StateBuilder, financial_approx


@pytest.mark.unit
@pytest.mark.deterministic
class TestBankReconciliation:
    """Unit tests for bank reconciliation engine."""
    
    @patch('src.r2r.engines.bank_recon.load_bank_transactions')
    def test_duplicate_detection_basic(self, mock_load_bank, repo_root, temp_output_dir):
        """Test basic duplicate detection logic."""
        # Setup mock data with duplicates
        mock_repo = MockDataRepo()
        mock_load_bank.return_value = mock_repo.bank_transactions_df
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT100")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        # Execute
        result_state = bank_reconciliation(state, audit)
        
        # Assert duplicates were detected
        assert "bank_duplicates_count" in result_state.metrics
        assert result_state.metrics["bank_duplicates_count"] > 0
        
        # Verify audit trail
        assert len(audit.records) > 0
        # Check for bank reconciliation message in results
        assert "Bank recon duplicates" in result_state.messages[0]
    
    @patch('src.r2r.engines.bank_recon.load_bank_transactions')
    def test_no_duplicates_scenario(self, mock_load_bank, repo_root, temp_output_dir):
        """Test scenario with no duplicates."""
        # Setup mock data with no duplicates
        mock_data = pd.DataFrame([
            {
                "period": "2025-08", "entity": "ENT100", "bank_txn_id": "TXN001",
                "date": "2025-08-15", "amount": 1000.0, "currency": "USD",
                "counterparty": "Vendor A", "transaction_type": "Payment", "description": "Payment 1"
            },
            {
                "period": "2025-08", "entity": "ENT100", "bank_txn_id": "TXN002",
                "date": "2025-08-16", "amount": 2000.0, "currency": "USD",
                "counterparty": "Vendor B", "transaction_type": "Receipt", "description": "Payment 2"
            }
        ])
        mock_load_bank.return_value = mock_data
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT100")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        # Execute
        result_state = bank_reconciliation(state, audit)
        
        # Assert no duplicates
        assert "bank_duplicates_count" in result_state.metrics
        assert result_state.metrics["bank_duplicates_count"] == 0
        
        # Verify audit trail
        assert len(audit.records) > 0
        
    @patch('src.r2r.engines.bank_recon.load_bank_transactions')
    def test_entity_filtering(self, mock_load_bank, repo_root, temp_output_dir):
        """Test entity-specific filtering."""
        mock_data = pd.DataFrame([
            {
                "period": "2025-08", "entity": "ENT_A", "bank_txn_id": "TXN001",
                "date": "2025-08-15", "amount": 1000.0, "currency": "USD",
                "counterparty": "Vendor A", "transaction_type": "Payment", "description": "Payment A"
            },
            {
                "period": "2025-08", "entity": "ENT_B", "bank_txn_id": "TXN002",
                "date": "2025-08-15", "amount": 1000.0, "currency": "USD",
                "counterparty": "Vendor A", "transaction_type": "Payment", "description": "Payment B"
            }
        ])
        mock_load_bank.return_value = mock_data
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT_A")  # Filter to specific entity
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        # Execute
        result_state = bank_reconciliation(state, audit)
        
        # Assert processing occurred
        assert len(audit.records) > 0
        
    @pytest.mark.parametrize("amount,expected_duplicate", [
        (1000.0, True),   # Exact match
        (1000.01, False), # Close but not exact
        (999.99, False),  # Close but not exact
    ])
    @patch('src.r2r.engines.bank_recon.load_bank_transactions')
    def test_duplicate_threshold_sensitivity(self, mock_load_bank, amount, expected_duplicate, repo_root, temp_output_dir):
        """Test sensitivity of duplicate detection to amount differences."""
        mock_data = pd.DataFrame([
            {
                "period": "2025-08", "entity": "ENT100", "bank_txn_id": "TXN001",
                "date": "2025-08-15", "amount": 1000.0, "currency": "USD",
                "counterparty": "Vendor A", "transaction_type": "Payment", "description": "Payment 1"
            },
            {
                "period": "2025-08", "entity": "ENT100", "bank_txn_id": "TXN002",
                "date": "2025-08-15", "amount": amount, "currency": "USD",
                "counterparty": "Vendor A", "transaction_type": "Payment", "description": "Payment 2"
            }
        ])
        mock_load_bank.return_value = mock_data
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT100")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        # Execute
        result_state = bank_reconciliation(state, audit)
        
        # Assert duplicate detection based on threshold
        if expected_duplicate:
            assert result_state.metrics.get("bank_duplicates_count", 0) > 0
        else:
            assert result_state.metrics.get("bank_duplicates_count", 0) == 0


@pytest.fixture
def sample_bank_data():
    """Sample bank transaction data for testing."""
    return pd.DataFrame([
        {
            "period": "2025-08", "entity": "TEST_ENT", "transaction_id": "TXN001",
            "date": "2025-08-15", "amount": 1000.0, "currency": "USD",
            "counterparty": "Test Vendor", "transaction_type": "Payment"
        },
        {
            "period": "2025-08", "entity": "TEST_ENT", "transaction_id": "TXN002",
            "date": "2025-08-16", "amount": -500.0, "currency": "USD",
            "counterparty": "Test Customer", "transaction_type": "Receipt"
        }
    ])


# Template for additional unit tests that can be implemented by lower reasoning model
"""
TODO: Implement these additional unit tests:

1. test_duplicate_signature_generation - Test the duplicate signature logic
2. test_currency_handling - Test multi-currency transaction handling  
3. test_empty_data_handling - Test behavior with empty transaction data
4. test_invalid_data_handling - Test error handling for malformed data
5. test_metrics_calculation - Test all metrics are calculated correctly
6. test_audit_trail_completeness - Test all audit records are created
7. test_artifact_generation - Test output artifact structure and content
"""
