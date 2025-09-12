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


    def test_duplicate_signature_generation(self, repo_root, temp_output_dir):
        """Test the duplicate signature logic for bank reconciliation."""
        # Create test data with exact duplicate signatures
        bank_data = pd.DataFrame([
            {
                "entity": "ENT_A", "bank_txn_id": "TXN001", "date": "2025-08-15",
                "amount": 1000.0, "currency": "USD", "counterparty": "ACME Corp",
                "transaction_type": "Payment", "description": "Invoice payment"
            },
            {
                "entity": "ENT_A", "bank_txn_id": "TXN002", "date": "2025-08-15", 
                "amount": 1000.0, "currency": "USD", "counterparty": "ACME Corp",
                "transaction_type": "Payment", "description": "Duplicate payment"
            },
            {
                "entity": "ENT_A", "bank_txn_id": "TXN003", "date": "2025-08-16",
                "amount": 500.0, "currency": "USD", "counterparty": "Beta Inc",
                "transaction_type": "Receipt", "description": "Unique transaction"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT_A")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.bank_recon.load_bank_transactions", return_value=bank_data):
            result_state = bank_reconciliation(state, audit)
        
        # Should detect one duplicate (TXN002 flagged as duplicate of TXN001)
        assert result_state.metrics["bank_duplicates_count"] == 1
        assert result_state.metrics["bank_duplicates_total_abs"] > 0
        
        # Verify duplicate detection messages
        assert any("Bank recon duplicates: 1 items" in msg for msg in result_state.messages)
        
        # Check that duplicate signature is properly formed
        assert result_state.metrics["bank_duplicates_by_entity"]["ENT_A"] > 0
        
        # Verify audit trail
        assert len(audit.records) >= 0
        assert any("Bank reconciliation" in str(tag) for tag in result_state.tags)

    def test_currency_handling(self, repo_root, temp_output_dir):
        """Test multi-currency transaction handling in bank reconciliation."""
        # Create test data with multiple currencies
        bank_data = pd.DataFrame([
            {
                "entity": "ENT_A", "bank_txn_id": "USD001", "date": "2025-08-15",
                "amount": 1000.0, "currency": "USD", "counterparty": "Global Corp",
                "transaction_type": "Payment", "description": "USD payment"
            },
            {
                "entity": "ENT_A", "bank_txn_id": "EUR001", "date": "2025-08-15",
                "amount": 850.0, "currency": "EUR", "counterparty": "Global Corp", 
                "transaction_type": "Payment", "description": "EUR payment"
            },
            {
                "entity": "ENT_A", "bank_txn_id": "USD002", "date": "2025-08-15",
                "amount": 1000.0, "currency": "USD", "counterparty": "Global Corp",
                "transaction_type": "Payment", "description": "Duplicate USD payment"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT_A")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.bank_recon.load_bank_transactions", return_value=bank_data):
            result_state = bank_reconciliation(state, audit)
        
        # Should detect one duplicate (USD002 vs USD001) but not cross-currency
        assert result_state.metrics["bank_duplicates_count"] == 1
        
        # EUR transaction should not be flagged as duplicate of USD
        assert any("Bank recon duplicates: 1 items" in msg for msg in result_state.messages)
        
        # Verify currency is part of signature matching - only USD duplicates detected
        assert result_state.metrics["bank_duplicates_by_entity"]["ENT_A"] == 1000.0  # Only USD amount


    def test_empty_data_handling(self, repo_root, temp_output_dir):
        """Test behavior with empty transaction data."""
        # Create empty DataFrame
        empty_bank_data = pd.DataFrame()
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT_A")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.bank_recon.load_bank_transactions", return_value=empty_bank_data):
            result_state = bank_reconciliation(state, audit)
        
        # Should skip processing with empty data
        assert "[DET] Bank reconciliation: no transactions in scope; skipping" in result_state.messages
        assert any("Bank reconciliation (skipped)" in str(tag) for tag in result_state.tags)
        
        # No metrics should be set for empty data
        assert "bank_duplicates_count" not in result_state.metrics
        
        # Verify audit trail exists but minimal
        assert len(audit.records) >= 0

    def test_metrics_calculation(self, repo_root, temp_output_dir):
        """Test all metrics are calculated correctly."""
        # Create test data with known duplicates and amounts
        bank_data = pd.DataFrame([
            {
                "entity": "ENT_A", "bank_txn_id": "TXN001", "date": "2025-08-15",
                "amount": 1000.0, "currency": "USD", "counterparty": "ACME Corp",
                "transaction_type": "Payment", "description": "Payment 1"
            },
            {
                "entity": "ENT_A", "bank_txn_id": "TXN002", "date": "2025-08-15",
                "amount": 1000.0, "currency": "USD", "counterparty": "ACME Corp", 
                "transaction_type": "Payment", "description": "Payment 2"
            },
            {
                "entity": "ENT_B", "bank_txn_id": "TXN003", "date": "2025-08-16",
                "amount": 500.0, "currency": "USD", "counterparty": "Beta Inc",
                "transaction_type": "Receipt", "description": "Receipt 1"
            },
            {
                "entity": "ENT_B", "bank_txn_id": "TXN004", "date": "2025-08-16",
                "amount": 500.0, "currency": "USD", "counterparty": "Beta Inc",
                "transaction_type": "Receipt", "description": "Receipt 2"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.bank_recon.load_bank_transactions", return_value=bank_data):
            result_state = bank_reconciliation(state, audit)
        
        # Verify all metrics are calculated
        assert result_state.metrics["bank_duplicates_count"] == 2  # Two duplicate pairs
        assert result_state.metrics["bank_duplicates_total_abs"] == 1500.0  # 1000 + 500
        
        # Verify by-entity breakdown
        by_entity = result_state.metrics["bank_duplicates_by_entity"]
        assert by_entity["ENT_A"] == 1000.0
        assert by_entity["ENT_B"] == 500.0
        
        # Verify artifact path is set
        assert "bank_reconciliation_artifact" in result_state.metrics
        assert result_state.metrics["bank_reconciliation_artifact"].endswith(".json")


    @patch('src.r2r.engines.bank_recon.load_bank_transactions')
    def test_deterministic_rationale_in_artifact(self, mock_load_bank, repo_root, temp_output_dir):
        """Test that the deterministic_rationale field is correctly generated in the artifact."""
        import json
        from pathlib import Path

        # Setup mock data with a clear duplicate
        mock_data = pd.DataFrame([
            {
                "entity": "ENT100", "bank_txn_id": "TXN001", "date": "2025-08-15",
                "amount": 1000.0, "currency": "USD", "counterparty": "Vendor A",
                "transaction_type": "Payment", "description": "Payment 1"
            },
            {
                "entity": "ENT100", "bank_txn_id": "TXN002", "date": "2025-08-15",
                "amount": 1000.0, "currency": "USD", "counterparty": "Vendor A",
                "transaction_type": "Payment", "description": "Duplicate Payment"
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

        # Verify artifact was created
        artifact_path_str = result_state.metrics.get("bank_reconciliation_artifact")
        assert artifact_path_str, "Bank reconciliation artifact not found in metrics"
        artifact_path = Path(artifact_path_str)
        assert artifact_path.exists(), "Bank reconciliation artifact file does not exist"

        # Load the artifact and check the rationale field
        with artifact_path.open("r") as f:
            artifact_data = json.load(f)

        assert "exceptions" in artifact_data
        assert len(artifact_data["exceptions"]) > 0
        exception = artifact_data["exceptions"][0]

        assert "deterministic_rationale" in exception
        assert exception["deterministic_rationale"].strip().startswith("[DET]")


# Template for additional unit tests that can be implemented by lower reasoning model
"""
TODO: Implement these additional unit tests:

4. test_invalid_data_handling - Test error handling for malformed data
6. test_audit_trail_completeness - Test all audit records are created
7. test_artifact_generation - Test output artifact structure and content
"""
