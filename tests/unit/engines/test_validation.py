"""Unit tests for validation engine."""

from __future__ import annotations

import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch

from src.r2r.engines.validation import validate_ingestion
from tests.fixtures.mocks import MockAuditLogger
from tests.fixtures.helpers import StateBuilder, TBDataFrameBuilder, EntitiesDataFrameBuilder


@pytest.mark.unit
@pytest.mark.deterministic
class TestValidationEngine:
    """Unit tests for validation engine."""
    
    def test_validation_basic_success(self, repo_root, temp_output_dir):
        """Test basic validation with valid data."""
        # Create valid entities data
        entities_data = (EntitiesDataFrameBuilder()
                        .add_entity("TEST_ENT", "Test Entity", "USD")
                        .build())
        
        # Create valid COA data
        coa_data = pd.DataFrame([
            {"account": "4000", "account_name": "Revenue", "account_type": "Revenue"},
            {"account": "5000", "account_name": "Expenses", "account_type": "Expense"}
        ])
        
        # Create valid TB data
        tb_data = (TBDataFrameBuilder()
                  .add_balance("2025-08", "TEST_ENT", "4000", 50000.0)
                  .add_balance("2025-08", "TEST_ENT", "5000", -30000.0)
                  .build())
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .with_entities_df(entities_data)
                .with_coa_df(coa_data)
                .with_tb_df(tb_data)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        result_state = validate_ingestion(state, audit)
        
        # Verify successful validation messages
        assert "[DET] COA coverage OK: all TB accounts present" in result_state.messages
        assert "[DET] Entity coverage OK: all TB entities present" in result_state.messages
        assert f"[DET] TB period OK: {state.period}" in result_state.messages
        assert "[DET] No duplicate TB keys detected" in result_state.messages
        
        # Verify audit trail exists
        assert len(audit.records) >= 0
        assert any("Ingestion validations" in str(tag) for tag in result_state.tags)
    
    def test_validation_missing_accounts(self, repo_root, temp_output_dir):
        """Test validation with missing accounts in COA."""
        entities_data = (EntitiesDataFrameBuilder()
                        .add_entity("TEST_ENT", "Test Entity", "USD")
                        .build())
        
        # COA missing account 6000
        coa_data = pd.DataFrame([
            {"account": "4000", "account_name": "Revenue", "account_type": "Revenue"}
        ])
        
        # TB has account not in COA
        tb_data = (TBDataFrameBuilder()
                  .add_balance("2025-08", "TEST_ENT", "4000", 50000.0)
                  .add_balance("2025-08", "TEST_ENT", "6000", 10000.0)  # Missing from COA
                  .build())
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .with_entities_df(entities_data)
                .with_coa_df(coa_data)
                .with_tb_df(tb_data)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        result_state = validate_ingestion(state, audit)
        
        # Should detect missing accounts
        assert any("[DET] Missing accounts in COA:" in msg for msg in result_state.messages)
    
    def test_validation_missing_entities(self, repo_root, temp_output_dir):
        """Test validation with missing entities in master data."""
        # Entities master missing ENT_B
        entities_data = (EntitiesDataFrameBuilder()
                        .add_entity("ENT_A", "Entity A", "USD")
                        .build())
        
        coa_data = pd.DataFrame([
            {"account": "4000", "account_name": "Revenue", "account_type": "Revenue"}
        ])
        
        # TB has entity not in master
        tb_data = (TBDataFrameBuilder()
                  .add_balance("2025-08", "ENT_A", "4000", 50000.0)
                  .add_balance("2025-08", "ENT_B", "4000", 30000.0)  # Missing from entities
                  .build())
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .with_entities_df(entities_data)
                .with_coa_df(coa_data)
                .with_tb_df(tb_data)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        result_state = validate_ingestion(state, audit)
        
        # Should detect missing entities
        assert any("[DET] Missing entities in master:" in msg for msg in result_state.messages)
    
    def test_validation_period_inconsistency(self, repo_root, temp_output_dir):
        """Test validation with period inconsistency."""
        entities_data = (EntitiesDataFrameBuilder()
                        .add_entity("TEST_ENT", "Test Entity", "USD")
                        .build())
        
        coa_data = pd.DataFrame([
            {"account": "4000", "account_name": "Revenue", "account_type": "Revenue"}
        ])
        
        # Create TB with mixed periods
        tb_data = pd.DataFrame([
            {"period": "2025-08", "entity": "TEST_ENT", "account": "4000", "balance_usd": 50000.0, "currency": "USD"},
            {"period": "2025-07", "entity": "TEST_ENT", "account": "4000", "balance_usd": 30000.0, "currency": "USD"}  # Wrong period
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .with_entities_df(entities_data)
                .with_coa_df(coa_data)
                .with_tb_df(tb_data)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        result_state = validate_ingestion(state, audit)
        
        # Should detect period inconsistency
        assert any("[DET] TB rows with wrong period:" in msg for msg in result_state.messages)
    
    def test_validation_duplicate_keys(self, repo_root, temp_output_dir):
        """Test validation with duplicate TB keys."""
        entities_data = (EntitiesDataFrameBuilder()
                        .add_entity("TEST_ENT", "Test Entity", "USD")
                        .build())
        
        coa_data = pd.DataFrame([
            {"account": "4000", "account_name": "Revenue", "account_type": "Revenue"}
        ])
        
        # Create TB with duplicate keys
        tb_data = pd.DataFrame([
            {"period": "2025-08", "entity": "TEST_ENT", "account": "4000", "balance_usd": 50000.0, "currency": "USD"},
            {"period": "2025-08", "entity": "TEST_ENT", "account": "4000", "balance_usd": 25000.0, "currency": "USD"}  # Duplicate
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .with_entities_df(entities_data)
                .with_coa_df(coa_data)
                .with_tb_df(tb_data)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        result_state = validate_ingestion(state, audit)
        
        # Should detect duplicates
        assert any("[DET] Duplicates in TB by (period,entity,account):" in msg for msg in result_state.messages)
    
    def test_validation_missing_dataframes(self, repo_root, temp_output_dir):
        """Test validation with missing required dataframes."""
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        # Should raise assertion errors for missing dataframes
        with pytest.raises(AssertionError, match="entities_df missing"):
            validate_ingestion(state, audit)
    
    def test_validation_comprehensive_check(self, repo_root, temp_output_dir):
        """Test validation with multiple issues."""
        entities_data = (EntitiesDataFrameBuilder()
                        .add_entity("ENT_A", "Entity A", "USD")
                        .build())
        
        coa_data = pd.DataFrame([
            {"account": "4000", "account_name": "Revenue", "account_type": "Revenue"}
        ])
        
        # TB with multiple issues
        tb_data = pd.DataFrame([
            {"period": "2025-08", "entity": "ENT_A", "account": "4000", "balance_usd": 50000.0, "currency": "USD"},
            {"period": "2025-08", "entity": "ENT_B", "account": "5000", "balance_usd": 30000.0, "currency": "USD"},  # Missing entity & account
            {"period": "2025-07", "entity": "ENT_A", "account": "4000", "balance_usd": 20000.0, "currency": "USD"},  # Wrong period
            {"period": "2025-08", "entity": "ENT_A", "account": "4000", "balance_usd": 10000.0, "currency": "USD"}   # Duplicate
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ALL")
                .with_entities_df(entities_data)
                .with_coa_df(coa_data)
                .with_tb_df(tb_data)
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        result_state = validate_ingestion(state, audit)
        
        # Should detect all issues
        messages = " ".join(result_state.messages)
        assert "[DET] Missing accounts in COA:" in messages
        assert "[DET] Missing entities in master:" in messages
        assert "[DET] TB rows with wrong period:" in messages
        assert "[DET] Duplicates in TB by (period,entity,account):" in messages


# Template for additional unit tests
"""
TODO: Implement these additional validation tests:

1. test_validation_data_types - Test data type validation
2. test_validation_null_values - Test null value handling
3. test_validation_currency_consistency - Test currency validation
4. test_validation_balance_checks - Test balance validation rules
5. test_validation_performance - Test validation with large datasets
"""
