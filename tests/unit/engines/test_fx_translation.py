"""
Unit tests for FX translation engine.
"""
from __future__ import annotations

import pytest
import pandas as pd
from unittest.mock import patch

from src.r2r.engines.fx_translation import fx_translation
from tests.fixtures.mocks import MockAuditLogger
from tests.fixtures.helpers import StateBuilder, financial_approx, assert_fx_consistency, EntitiesDataFrameBuilder, TBDataFrameBuilder, FXDataFrameBuilder


@pytest.mark.unit
@pytest.mark.deterministic
class TestFXTranslation:
    """Unit tests for FX translation engine."""
    
    def test_fx_translation_basic(self, repo_root, temp_output_dir):
        """Test basic FX translation functionality."""
        # Setup test data with EUR entity
        tb_df = (TBDataFrameBuilder()
                .add_balance("2025-08", "ENT_EUR", "1000", 100000.0, None)  # EUR cash
                .add_balance("2025-08", "ENT_EUR", "5000", -50000.0, None)  # EUR revenue
                .build())
        
        fx_df = (FXDataFrameBuilder()
                .add_rate("2025-08", "EUR", 1.092)
                .add_rate("2025-08", "USD", 1.0)
                .build())
        
        entities_df = (EntitiesDataFrameBuilder()
                      .add_entity("ENT_EUR", "Test EU Entity", "EUR", "USD")
                      .build())
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT_EUR")
                .with_tb_df(tb_df)
                .with_fx_df(fx_df)
                .with_entities_df(entities_df)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        result_state = fx_translation(state, audit)
        
        # Verify FX translation occurred
        assert result_state.tb_df is not None
        translated_tb = result_state.tb_df
        
        # Check USD balances were calculated
        eur_cash_row = translated_tb[
            (translated_tb["entity"] == "ENT_EUR") & 
            (translated_tb["account"] == "1000")
        ]
        assert len(eur_cash_row) == 1
        # Verify FX translation was applied (balance_usd should be updated)
        assert eur_cash_row.iloc[0]["balance_usd"] == financial_approx(100000.0)  # Original balance preserved
        
        # Verify audit trail
        assert len(audit.records) > 0
    
    def test_usd_entity_passthrough(self, repo_root, temp_output_dir):
        """Test USD entities pass through without translation."""
        tb_df = (TBDataFrameBuilder()
                .add_balance("2025-08", "ENT_USD", "1000", 50000.0, 50000.0)
                .build())
        
        fx_df = (FXDataFrameBuilder()
                .add_rate("2025-08", "USD", 1.0)
                .build())
        
        entities_df = (EntitiesDataFrameBuilder()
                      .add_entity("ENT_USD", "US Entity", "USD", "USD")
                      .build())
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT_USD")
                .with_tb_df(tb_df)
                .with_fx_df(fx_df)
                .with_entities_df(entities_df)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        result_state = fx_translation(state, audit)
        
        # USD entities should pass through unchanged
        usd_cash_row = result_state.tb_df[
            (result_state.tb_df["entity"] == "ENT_USD") & 
            (result_state.tb_df["account"] == "1000")
        ]
        assert len(usd_cash_row) == 1
        assert usd_cash_row.iloc[0]["balance_usd"] == financial_approx(50000.0)
    
    def test_missing_fx_rate_handling(self, repo_root, temp_output_dir):
        """Test handling of missing FX rates."""
        tb_df = (TBDataFrameBuilder()
                .add_balance("2025-08", "ENT_GBP", "1000", 25000.0, None)
                .build())
        
        # Missing GBP rate - only USD provided
        fx_df = (FXDataFrameBuilder()
                .add_rate("2025-08", "USD", 1.0)
                .build())
        
        entities_df = (EntitiesDataFrameBuilder()
                      .add_entity("ENT_GBP", "UK Entity", "GBP", "USD")
                      .build())
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT_GBP")
                .with_tb_df(tb_df)
                .with_fx_df(fx_df)
                .with_entities_df(entities_df)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        # Should handle missing rate gracefully
        result_state = fx_translation(state, audit)
        assert result_state.tb_df is not None


@pytest.mark.unit
@pytest.mark.deterministic
class TestFXTranslationEdgeCases:
    """Test edge cases for FX translation."""
    
    def test_empty_trial_balance(self, repo_root, temp_output_dir):
        """Test FX translation with empty trial balance."""
        tb_df = pd.DataFrame(columns=["period", "entity", "account", "balance", "balance_usd"])
        fx_df = (FXDataFrameBuilder()
                .add_rate("2025-08", "USD", 1.0)
                .build())
        
        entities_df = (EntitiesDataFrameBuilder()
                      .add_entity("ENT_USD", "US Entity", "USD", "USD")
                      .build())
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT_USD")
                .with_tb_df(tb_df)
                .with_fx_df(fx_df)
                .with_entities_df(entities_df)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        result_state = fx_translation(state, audit)
        
        # Should handle empty TB gracefully
        assert result_state.tb_df is not None
        assert len(result_state.tb_df) == 0
    
    def test_zero_balance_handling(self, repo_root, temp_output_dir):
        """Test handling of zero balances in FX translation."""
        tb_df = (TBDataFrameBuilder()
                .add_balance("2025-08", "ENT_EUR", "1000", 0.0, None)
                .add_balance("2025-08", "ENT_EUR", "2000", 100.0, None)
                .build())
        
        fx_df = (FXDataFrameBuilder()
                .add_rate("2025-08", "EUR", 1.092)
                .add_rate("2025-08", "USD", 1.0)
                .build())
        
        entities_df = (EntitiesDataFrameBuilder()
                      .add_entity("ENT_EUR", "EU Entity", "EUR", "USD")
                      .build())
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT_EUR")
                .with_tb_df(tb_df)
                .with_fx_df(fx_df)
                .with_entities_df(entities_df)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        result_state = fx_translation(state, audit)
        
        # Zero balances should be handled correctly
        zero_balance_row = result_state.tb_df[
            (result_state.tb_df["entity"] == "ENT_EUR") & 
            (result_state.tb_df["account"] == "1000")
        ]
        assert len(zero_balance_row) == 1
        assert zero_balance_row.iloc[0]["balance_usd"] == financial_approx(0.0)


# Template for additional unit tests
"""
TODO: Implement these additional unit tests:

1. test_multi_entity_translation - Test translation across multiple entities
2. test_negative_balance_translation - Test negative balance handling
3. test_fx_rate_precision - Test FX rate precision and rounding
4. test_balance_sheet_vs_income_statement - Test different account class handling
5. test_fx_revaluation_calculation - Test FX revaluation logic if implemented
6. test_audit_artifact_structure - Test FX translation artifact JSON structure
7. test_metrics_calculation - Test all FX-related metrics are calculated
8. test_currency_mismatch_detection - Test detection of entity/currency mismatches
"""
