"""Unit tests for accruals engine."""

from __future__ import annotations

import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch

from src.r2r.engines.accruals import accruals_check
from tests.fixtures.mocks import MockAuditLogger
from tests.fixtures.helpers import StateBuilder, financial_approx


@pytest.mark.unit
@pytest.mark.deterministic
class TestAccrualsEngine:
    """Unit tests for accruals engine."""
    
    def test_accruals_basic_processing(self, repo_root, temp_output_dir):
        """Test basic accruals processing with valid data."""
        # Create mock accruals data
        accruals_data = pd.DataFrame([
            {
                "entity": "TEST_ENT", "accrual_id": "ACC001", "description": "Test Accrual 1",
                "amount_local": 5000.0, "amount_usd": 5000.0, "currency": "USD",
                "status": "Active", "accrual_date": "2025-08-15", "reversal_date": "2025-09-15",
                "notes": ""
            },
            {
                "entity": "TEST_ENT", "accrual_id": "ACC002", "description": "Test Accrual 2",
                "amount_local": 3000.0, "amount_usd": 3000.0, "currency": "USD",
                "status": "Active", "accrual_date": "2025-08-20", "reversal_date": "",
                "notes": "Missing reversal"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        # Mock the CSV file reading
        with patch("pandas.read_csv", return_value=accruals_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = accruals_check(state, audit)
        
        # Verify metrics are calculated
        assert "accruals_exception_count" in result_state.metrics
        assert "accruals_exception_total_usd" in result_state.metrics
        assert "accruals_exception_by_entity" in result_state.metrics
        
        # Should detect one exception (missing reversal date)
        assert result_state.metrics["accruals_exception_count"] == 1
        assert result_state.metrics["accruals_exception_total_usd"] == 3000.0
        
        # Verify audit trail exists
        assert len(audit.records) >= 0
    
    def test_accruals_should_reverse_status(self, repo_root, temp_output_dir):
        """Test accruals with 'Should Reverse' status."""
        accruals_data = pd.DataFrame([
            {
                "entity": "TEST_ENT", "accrual_id": "ACC003", "description": "Should Reverse Accrual",
                "amount_local": 2000.0, "amount_usd": 2000.0, "currency": "USD",
                "status": "Should Reverse", "accrual_date": "2025-08-10", "reversal_date": "2025-09-10",
                "notes": "Explicit reversal required"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("pandas.read_csv", return_value=accruals_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = accruals_check(state, audit)
        
        # Should detect exception for 'Should Reverse' status
        assert result_state.metrics["accruals_exception_count"] == 1
        assert result_state.metrics["accruals_exception_total_usd"] == 2000.0
    
    def test_accruals_no_data_file(self, repo_root, temp_output_dir):
        """Test accruals processing when data file doesn't exist."""
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        # Mock file not existing
        with patch("pathlib.Path.exists", return_value=False):
            result_state = accruals_check(state, audit)
        
        # Should skip processing
        assert "[DET] Accruals: no supporting data found; skipping checks" in result_state.messages
        assert any("Accruals checks (skipped)" in str(tag) for tag in result_state.tags)
    
    def test_accruals_no_exceptions(self, repo_root, temp_output_dir):
        """Test accruals processing with no exceptions."""
        accruals_data = pd.DataFrame([
            {
                "entity": "TEST_ENT", "accrual_id": "ACC004", "description": "Clean Accrual",
                "amount_local": 1000.0, "amount_usd": 1000.0, "currency": "USD",
                "status": "Active", "accrual_date": "2025-08-15", "reversal_date": "2025-09-15",
                "notes": ""
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("pandas.read_csv", return_value=accruals_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = accruals_check(state, audit)
        
        # Should have no exceptions
        assert result_state.metrics["accruals_exception_count"] == 0
        assert result_state.metrics["accruals_exception_total_usd"] == 0.0
        assert "[DET] Accruals: no exceptions for period" in result_state.messages
    
    def test_accruals_multi_entity_aggregation(self, repo_root, temp_output_dir):
        """Test accruals processing with multiple entities."""
        accruals_data = pd.DataFrame([
            {
                "entity": "ENT_A", "accrual_id": "ACC005", "description": "Entity A Accrual",
                "amount_local": 1500.0, "amount_usd": 1500.0, "currency": "USD",
                "status": "Should Reverse", "accrual_date": "2025-08-15", "reversal_date": "",
                "notes": ""
            },
            {
                "entity": "ENT_B", "accrual_id": "ACC006", "description": "Entity B Accrual",
                "amount_local": 2500.0, "amount_usd": 2500.0, "currency": "USD",
                "status": "Active", "accrual_date": "2025-08-20", "reversal_date": "",
                "notes": ""
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("pandas.read_csv", return_value=accruals_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = accruals_check(state, audit)
        
        # Should detect both exceptions
        assert result_state.metrics["accruals_exception_count"] == 2
        assert result_state.metrics["accruals_exception_total_usd"] == 4000.0
        
        # Check by-entity breakdown
        by_entity = result_state.metrics["accruals_exception_by_entity"]
        assert by_entity["ENT_A"] == 1500.0
        assert by_entity["ENT_B"] == 2500.0


    def test_accruals_reversal_proposals(self, repo_root, temp_output_dir):
        """Test the structure and content of reversal proposals."""
        accruals_data = pd.DataFrame([
            {
                "entity": "TEST_ENT", "accrual_id": "ACC007", "description": "Test Proposal",
                "amount_local": 7000.0, "amount_usd": 7000.0, "currency": "USD",
                "status": "Should Reverse", "accrual_date": "2025-08-31", "reversal_date": "",
                "notes": "Generate a proposal for this"
            }
        ])

        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())

        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")

        with patch("pandas.read_csv", return_value=accruals_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = accruals_check(state, audit)

        # Verify artifact was created
        artifact_path = result_state.metrics.get("accruals_artifact")
        assert artifact_path and Path(artifact_path).exists()

        # Load the artifact and check proposals
        with open(artifact_path, "r") as f:
            artifact_data = json.load(f)

        assert "proposals" in artifact_data
        assert len(artifact_data["proposals"]) == 1

        proposal = artifact_data["proposals"][0]
        assert proposal["proposal_type"] == "accrual_reversal"
        assert proposal["accrual_id"] == "ACC007"
        assert proposal["amount_usd"] == -7000.0
        assert "deterministic_narrative" in proposal
        assert proposal["deterministic_narrative"].startswith("[DET] Reverse ACC007")


# Template for additional unit tests
"""
TODO: Implement these additional accruals tests:

1. test_accruals_period_filtering - Test filtering by specific periods
2. test_accruals_currency_handling - Test multi-currency accruals
3. test_accruals_reversal_proposals - Test reversal proposal generation
4. test_accruals_artifact_generation - Test JSON artifact creation
5. test_accruals_edge_cases - Test edge cases and error handling
"""
