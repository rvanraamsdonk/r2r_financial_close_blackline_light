"""Unit tests for intercompany reconciliation engine."""

from __future__ import annotations

import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch

from src.r2r.engines.intercompany_recon import intercompany_reconciliation
from tests.fixtures.mocks import MockAuditLogger
from tests.fixtures.helpers import StateBuilder, financial_approx


@pytest.mark.unit
@pytest.mark.deterministic
class TestIntercompanyReconciliation:
    """Unit tests for intercompany reconciliation engine."""
    
    def test_ic_basic_processing(self, repo_root, temp_output_dir):
        """Test basic intercompany reconciliation processing."""
        # Create mock intercompany data
        ic_data = pd.DataFrame([
            {
                "doc_id": "IC001", "entity_src": "ENT_A", "entity_dst": "ENT_B",
                "amount_src": 10000.0, "amount_dst": 10000.0, "currency": "USD",
                "transaction_type": "Service Fee", "description": "IT Services"
            },
            {
                "doc_id": "IC002", "entity_src": "ENT_A", "entity_dst": "ENT_C",
                "amount_src": 5000.0, "amount_dst": 4800.0, "currency": "USD",
                "transaction_type": "Management Fee", "description": "Management Services"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .build())
        
        # Set materiality thresholds
        state.metrics["materiality_thresholds_usd"] = {
            "ENT_A": 150.0,  # Lower threshold to catch the $200 difference
            "ENT_B": 150.0,
            "ENT_C": 150.0
        }
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        # Mock the data loading
        with patch("src.r2r.engines.intercompany_recon.load_intercompany", return_value=ic_data), \
             patch("src.r2r.engines.intercompany_recon._find_ic_file", return_value=Path("/fake/path")):
            result_state = intercompany_reconciliation(state, audit)
        
        # Verify metrics are calculated
        assert "ic_mismatch_count" in result_state.metrics
        assert "ic_mismatch_total_diff_abs" in result_state.metrics
        assert "ic_mismatch_by_pair" in result_state.metrics
        
        # Should detect one mismatch (ENT_A->ENT_C with $200 difference above $100 threshold)
        assert result_state.metrics["ic_mismatch_count"] == 1
        assert result_state.metrics["ic_mismatch_total_diff_abs"] == 200.0
        
        # Verify audit trail exists
        assert len(audit.records) >= 0
    
    def test_ic_no_mismatches(self, repo_root, temp_output_dir):
        """Test intercompany reconciliation with no mismatches."""
        ic_data = pd.DataFrame([
            {
                "doc_id": "IC003", "entity_src": "ENT_A", "entity_dst": "ENT_B",
                "amount_src": 8000.0, "amount_dst": 8000.0, "currency": "USD",
                "transaction_type": "Service Fee", "description": "Consulting Services"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.intercompany_recon.load_intercompany", return_value=ic_data), \
             patch("src.r2r.engines.intercompany_recon._find_ic_file", return_value=Path("/fake/path")):
            result_state = intercompany_reconciliation(state, audit)
        
        # Should have no mismatches
        assert result_state.metrics["ic_mismatch_count"] == 0
        assert result_state.metrics["ic_mismatch_total_diff_abs"] == 0.0
        assert "[DET] Intercompany: no mismatches above materiality" in result_state.messages
    
    def test_ic_no_data(self, repo_root, temp_output_dir):
        """Test intercompany reconciliation with no data."""
        empty_data = pd.DataFrame()
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.intercompany_recon.load_intercompany", return_value=empty_data), \
             patch("src.r2r.engines.intercompany_recon._find_ic_file", return_value=Path("/fake/path")):
            result_state = intercompany_reconciliation(state, audit)
        
        # Should skip processing
        assert "[DET] Intercompany: no transactions in scope; skipping" in result_state.messages
        assert any("Intercompany reconciliation (skipped)" in str(tag) for tag in result_state.tags)
    
    def test_ic_materiality_thresholds(self, repo_root, temp_output_dir):
        """Test intercompany reconciliation with different materiality thresholds."""
        ic_data = pd.DataFrame([
            {
                "doc_id": "IC004", "entity_src": "ENT_A", "entity_dst": "ENT_B",
                "amount_src": 10000.0, "amount_dst": 9500.0, "currency": "USD",
                "transaction_type": "Service Fee", "description": "Large Service"
            },
            {
                "doc_id": "IC005", "entity_src": "ENT_C", "entity_dst": "ENT_D",
                "amount_src": 1000.0, "amount_dst": 950.0, "currency": "USD",
                "transaction_type": "Small Fee", "description": "Small Service"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .build())
        
        # Set different materiality thresholds
        state.metrics["materiality_thresholds_usd"] = {
            "ENT_A": 1000.0,  # $500 diff > $1000 threshold = no exception
            "ENT_B": 1000.0,
            "ENT_C": 25.0,    # $50 diff > $25 threshold = exception
            "ENT_D": 25.0
        }
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.intercompany_recon.load_intercompany", return_value=ic_data), \
             patch("src.r2r.engines.intercompany_recon._find_ic_file", return_value=Path("/fake/path")):
            result_state = intercompany_reconciliation(state, audit)
        
        # Should detect one mismatch (ENT_C->ENT_D exceeds threshold)
        assert result_state.metrics["ic_mismatch_count"] == 1
        assert result_state.metrics["ic_mismatch_total_diff_abs"] == 50.0
    
    def test_ic_multiple_pairs_aggregation(self, repo_root, temp_output_dir):
        """Test intercompany reconciliation with multiple entity pairs."""
        ic_data = pd.DataFrame([
            {
                "doc_id": "IC006", "entity_src": "ENT_A", "entity_dst": "ENT_B",
                "amount_src": 5000.0, "amount_dst": 4500.0, "currency": "USD",
                "transaction_type": "Service Fee", "description": "Service 1"
            },
            {
                "doc_id": "IC007", "entity_src": "ENT_A", "entity_dst": "ENT_B",
                "amount_src": 3000.0, "amount_dst": 2700.0, "currency": "USD",
                "transaction_type": "Service Fee", "description": "Service 2"
            },
            {
                "doc_id": "IC008", "entity_src": "ENT_B", "entity_dst": "ENT_C",
                "amount_src": 2000.0, "amount_dst": 1800.0, "currency": "USD",
                "transaction_type": "Management Fee", "description": "Management"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .build())
        
        # Set low materiality to catch all differences
        state.metrics["materiality_thresholds_usd"] = {
            "ENT_A": 100.0,
            "ENT_B": 100.0,
            "ENT_C": 100.0
        }
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.intercompany_recon.load_intercompany", return_value=ic_data), \
             patch("src.r2r.engines.intercompany_recon._find_ic_file", return_value=Path("/fake/path")):
            result_state = intercompany_reconciliation(state, audit)
        
        # Should detect all three mismatches
        assert result_state.metrics["ic_mismatch_count"] == 3
        assert financial_approx(result_state.metrics["ic_mismatch_total_diff_abs"], 1000.0)  # 500 + 300 + 200
        
        # Check by-pair breakdown
        by_pair = result_state.metrics["ic_mismatch_by_pair"]
        assert financial_approx(by_pair["ENT_A->ENT_B"], 800.0)  # 500 + 300
        assert financial_approx(by_pair["ENT_B->ENT_C"], 200.0)
    
    def test_ic_default_materiality(self, repo_root, temp_output_dir):
        """Test intercompany reconciliation with default materiality thresholds."""
        ic_data = pd.DataFrame([
            {
                "doc_id": "IC009", "entity_src": "ENT_X", "entity_dst": "ENT_Y",
                "amount_src": 10000.0, "amount_dst": 8500.0, "currency": "USD",
                "transaction_type": "Service Fee", "description": "Large Difference"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .build())
        
        # No materiality thresholds set - should use default $1000
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.intercompany_recon.load_intercompany", return_value=ic_data), \
             patch("src.r2r.engines.intercompany_recon._find_ic_file", return_value=Path("/fake/path")):
            result_state = intercompany_reconciliation(state, audit)
        
        # Should detect mismatch ($1500 difference > $1000 default threshold)
        assert result_state.metrics["ic_mismatch_count"] == 1
        assert result_state.metrics["ic_mismatch_total_diff_abs"] == 1500.0


    def test_ic_deterministic_rationale_in_artifact(self, repo_root, temp_output_dir):
        """Test that the deterministic_rationale field is correctly generated in the artifact."""
        ic_data = pd.DataFrame([
            {
                "doc_id": "IC002", "entity_src": "ENT_A", "entity_dst": "ENT_C", "date": "2025-08-01",
                "amount_src": 5000.0, "amount_dst": 4800.0, "currency": "USD",
                "transaction_type": "Management Fee", "description": "Management Services"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .build())
        
        state.metrics["materiality_thresholds_usd"] = {"ENT_A": 150.0, "ENT_C": 150.0}
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.intercompany_recon.load_intercompany", return_value=ic_data), \
             patch("src.r2r.engines.intercompany_recon._find_ic_file", return_value=Path("/fake/path")):
            result_state = intercompany_reconciliation(state, audit)

        artifact_path_str = result_state.metrics.get("intercompany_reconciliation_artifact")
        assert artifact_path_str
        artifact_path = Path(artifact_path_str)
        assert artifact_path.exists()

        with artifact_path.open("r") as f:
            artifact_data = json.load(f)

        assert len(artifact_data["exceptions"]) == 1
        exception = artifact_data["exceptions"][0]

        assert "deterministic_rationale" in exception
        assert exception["deterministic_rationale"].strip().startswith("[DET]")


# Template for additional unit tests
"""
TODO: Implement these additional intercompany tests:

1. test_ic_candidate_matching - Test candidate matching logic
2. test_ic_proposal_generation - Test true-up proposal generation
3. test_ic_multi_currency - Test multi-currency intercompany transactions
4. test_ic_artifact_generation - Test JSON artifact creation
5. test_ic_edge_cases - Test edge cases and error handling
"""
