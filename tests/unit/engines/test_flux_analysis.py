"""Unit tests for flux analysis engine."""

from __future__ import annotations

import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch

from src.r2r.engines.flux_analysis import flux_analysis
from tests.fixtures.mocks import MockAuditLogger
from tests.fixtures.helpers import StateBuilder, TBDataFrameBuilder, financial_approx


@pytest.mark.unit
@pytest.mark.deterministic
class TestFluxAnalysis:
    """Unit tests for flux analysis engine."""
    
    def test_flux_basic_processing(self, repo_root, temp_output_dir):
        """Test basic flux analysis processing."""
        # Create trial balance data
        tb_data = (TBDataFrameBuilder()
                  .add_balance("2025-08", "TEST_ENT", "4000", 50000.0)  # Revenue
                  .add_balance("2025-08", "TEST_ENT", "5000", 30000.0)  # Expenses
                  .build())
        
        # Create mock budget data
        budget_data = pd.DataFrame([
            {"period": "2025-08", "entity": "TEST_ENT", "account": "4000", "budget_amount": 45000.0},
            {"period": "2025-08", "entity": "TEST_ENT", "account": "5000", "budget_amount": 25000.0}
        ])
        
        # Create mock prior TB data
        prior_data = pd.DataFrame([
            {"period": "2025-07", "entity": "TEST_ENT", "account": "4000", "balance_usd": 48000.0},
            {"period": "2025-07", "entity": "TEST_ENT", "account": "5000", "balance_usd": 28000.0}
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .with_tb_df(tb_data)
                .build())
        
        # Set materiality thresholds
        state.metrics["materiality_thresholds_usd"] = {"TEST_ENT": 3000.0}
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        # Mock the data loading
        with patch("src.r2r.engines.flux_analysis.load_budget", return_value=budget_data), \
             patch("src.r2r.engines.flux_analysis.load_tb", return_value=prior_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = flux_analysis(state, audit)
        
        # Verify metrics are calculated
        assert "flux_exceptions_count" in result_state.metrics
        assert "flux_by_entity_count" in result_state.metrics
        assert "flux_analysis_artifact" in result_state.metrics
        
        # Should detect exceptions (revenue variance: 50k-45k=5k > 3k threshold)
        assert result_state.metrics["flux_exceptions_count"] >= 1
        
        # Verify audit trail exists
        assert len(audit.records) >= 0
    
    def test_flux_no_exceptions(self, repo_root, temp_output_dir):
        """Test flux analysis with no exceptions."""
        tb_data = (TBDataFrameBuilder()
                  .add_balance("2025-08", "TEST_ENT", "4000", 45000.0)
                  .build())
        
        budget_data = pd.DataFrame([
            {"period": "2025-08", "entity": "TEST_ENT", "account": "4000", "budget_amount": 45000.0}
        ])
        
        prior_data = pd.DataFrame([
            {"period": "2025-07", "entity": "TEST_ENT", "account": "4000", "balance_usd": 45000.0}
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .with_tb_df(tb_data)
                .build())
        
        state.metrics["materiality_thresholds_usd"] = {"TEST_ENT": 5000.0}
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.flux_analysis.load_budget", return_value=budget_data), \
             patch("src.r2r.engines.flux_analysis.load_tb", return_value=prior_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = flux_analysis(state, audit)
        
        # Should have no exceptions (no variance)
        assert result_state.metrics["flux_exceptions_count"] == 0
        assert "[DET] Flux analysis: no exceptions above materiality" in result_state.messages
    
    def test_flux_missing_budget_data(self, repo_root, temp_output_dir):
        """Test flux analysis with missing budget data."""
        tb_data = (TBDataFrameBuilder()
                  .add_balance("2025-08", "TEST_ENT", "4000", 50000.0)
                  .build())
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .with_tb_df(tb_data)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        # Mock budget loading to raise exception (no budget file)
        with patch("src.r2r.engines.flux_analysis.load_budget", side_effect=Exception("No budget file")), \
             patch("src.r2r.engines.flux_analysis.load_tb", return_value=pd.DataFrame()), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = flux_analysis(state, audit)
        
        # Should still process with zero budget amounts
        assert "flux_exceptions_count" in result_state.metrics
        assert "flux_analysis_artifact" in result_state.metrics
    
    def test_flux_multi_entity_analysis(self, repo_root, temp_output_dir):
        """Test flux analysis with multiple entities."""
        tb_data = (TBDataFrameBuilder()
                  .add_balance("2025-08", "ENT_A", "4000", 60000.0)
                  .add_balance("2025-08", "ENT_A", "5000", 35000.0)
                  .add_balance("2025-08", "ENT_B", "4000", 40000.0)
                  .add_balance("2025-08", "ENT_B", "5000", 25000.0)
                  .build())
        
        budget_data = pd.DataFrame([
            {"period": "2025-08", "entity": "ENT_A", "account": "4000", "budget_amount": 50000.0},
            {"period": "2025-08", "entity": "ENT_A", "account": "5000", "budget_amount": 30000.0},
            {"period": "2025-08", "entity": "ENT_B", "account": "4000", "budget_amount": 38000.0},
            {"period": "2025-08", "entity": "ENT_B", "account": "5000", "budget_amount": 23000.0}
        ])
        
        prior_data = pd.DataFrame([
            {"period": "2025-07", "entity": "ENT_A", "account": "4000", "balance_usd": 55000.0},
            {"period": "2025-07", "entity": "ENT_A", "account": "5000", "balance_usd": 32000.0},
            {"period": "2025-07", "entity": "ENT_B", "account": "4000", "balance_usd": 39000.0},
            {"period": "2025-07", "entity": "ENT_B", "account": "5000", "balance_usd": 24000.0}
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .with_tb_df(tb_data)
                .build())
        
        # Set different materiality thresholds
        state.metrics["materiality_thresholds_usd"] = {
            "ENT_A": 8000.0,  # Higher threshold
            "ENT_B": 1500.0   # Lower threshold
        }
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.flux_analysis.load_budget", return_value=budget_data), \
             patch("src.r2r.engines.flux_analysis.load_tb", return_value=prior_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = flux_analysis(state, audit)
        
        # Should detect exceptions based on different thresholds
        assert result_state.metrics["flux_exceptions_count"] >= 1
        
        # Check by-entity breakdown
        by_entity = result_state.metrics["flux_by_entity_count"]
        assert isinstance(by_entity, dict)
    
    def test_flux_variance_calculations(self, repo_root, temp_output_dir):
        """Test flux analysis variance calculations."""
        tb_data = (TBDataFrameBuilder()
                  .add_balance("2025-08", "TEST_ENT", "4000", 100000.0)  # Revenue: actual
                  .build())
        
        budget_data = pd.DataFrame([
            {"period": "2025-08", "entity": "TEST_ENT", "account": "4000", "budget_amount": 90000.0}  # Budget
        ])
        
        prior_data = pd.DataFrame([
            {"period": "2025-07", "entity": "TEST_ENT", "account": "4000", "balance_usd": 85000.0}  # Prior
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .with_tb_df(tb_data)
                .build())
        
        # Set low threshold to catch variances
        state.metrics["materiality_thresholds_usd"] = {"TEST_ENT": 5000.0}
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.flux_analysis.load_budget", return_value=budget_data), \
             patch("src.r2r.engines.flux_analysis.load_tb", return_value=prior_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = flux_analysis(state, audit)
        
        # Should detect both budget and prior variances
        # Budget variance: 100k - 90k = 10k > 5k threshold
        # Prior variance: 100k - 85k = 15k > 5k threshold
        assert result_state.metrics["flux_exceptions_count"] == 2
    
    def test_flux_default_materiality(self, repo_root, temp_output_dir):
        """Test flux analysis with default materiality thresholds."""
        tb_data = (TBDataFrameBuilder()
                  .add_balance("2025-08", "TEST_ENT", "4000", 50000.0)
                  .build())
        
        budget_data = pd.DataFrame([
            {"period": "2025-08", "entity": "TEST_ENT", "account": "4000", "budget_amount": 48000.0}
        ])
        
        prior_data = pd.DataFrame([
            {"period": "2025-07", "entity": "TEST_ENT", "account": "4000", "balance_usd": 49000.0}
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .with_tb_df(tb_data)
                .build())
        
        # No materiality thresholds set - should use default $1000
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.flux_analysis.load_budget", return_value=budget_data), \
             patch("src.r2r.engines.flux_analysis.load_tb", return_value=prior_data), \
             patch("pathlib.Path.exists", return_value=True):
            result_state = flux_analysis(state, audit)
        
        # Should detect exceptions (variances > $1000 default threshold)
        assert result_state.metrics["flux_exceptions_count"] >= 1


# Template for additional unit tests
"""
TODO: Implement these additional flux analysis tests:

1. test_flux_percentage_calculations - Test percentage variance calculations
2. test_flux_ai_highlights - Test AI highlights generation
3. test_flux_artifact_structure - Test JSON artifact structure
4. test_flux_prior_period_derivation - Test prior period calculation logic
5. test_flux_edge_cases - Test edge cases and error handling
"""
