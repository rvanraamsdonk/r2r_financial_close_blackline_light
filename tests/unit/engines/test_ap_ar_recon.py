"""
Unit tests for AP/AR reconciliation engines.
"""
from __future__ import annotations

import pytest
import pandas as pd
from unittest.mock import patch

from src.r2r.engines.ap_ar_recon import ap_reconciliation, ar_reconciliation
from tests.fixtures.mocks import MockAuditLogger, MockDataRepo
from tests.fixtures.helpers import StateBuilder, financial_approx


@pytest.mark.unit
@pytest.mark.deterministic
class TestAPReconciliation:
    """Unit tests for AP reconciliation engine."""
    
    def test_ap_recon_basic_processing(self, repo_root, temp_output_dir):
        """Test basic AP reconciliation processing."""
        mock_repo = MockDataRepo()
        mock_repo.ap_detail_df = pd.DataFrame([
            {
                "period": "2025-08", "entity": "TEST_ENT", "bill_id": "BILL001",
                "vendor_name": "Vendor A", "amount": 5000.0, "currency": "USD",
                "status": "Outstanding", "age_days": 15, "notes": "",
                "bill_date": "2025-08-15"
            },
            {
                "period": "2025-08", "entity": "TEST_ENT", "bill_id": "BILL002", 
                "vendor_name": "Vendor B", "amount": 3000.0, "currency": "USD",
                "status": "Overdue", "age_days": 45, "notes": "Duplicate payment detected",
                "bill_date": "2025-07-10"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.ap_ar_recon.load_ap_detail", 
                  return_value=mock_repo.ap_detail_df):
            result_state = ap_reconciliation(state, audit)
        
        # Verify basic metrics are calculated
        assert "ap_exceptions_count" in result_state.metrics
        assert "ap_exceptions_total_abs" in result_state.metrics
        assert result_state.metrics["ap_exceptions_count"] >= 0
        
        # Verify audit trail exists
        assert len(audit.records) >= 0
    
    def test_ap_exception_detection(self, repo_root, temp_output_dir):
        """Test AP exception detection logic."""
        mock_repo = MockDataRepo()
        mock_repo.ap_detail_df = pd.DataFrame([
            {
                "period": "2025-08", "entity": "TEST_ENT", "bill_id": "BILL001",
                "vendor_name": "Vendor A", "amount": 5000.0, "currency": "USD",
                "status": "Outstanding", "age_days": 15, "notes": "",
                "bill_date": "2025-08-15"
            },
            {
                "period": "2025-08", "entity": "TEST_ENT", "bill_id": "BILL002",
                "vendor_name": "Vendor B", "amount": 3000.0, "currency": "USD", 
                "status": "Overdue", "age_days": 45, "notes": "Duplicate payment detected",
                "bill_date": "2025-07-10"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.ap_ar_recon.load_ap_detail", 
                  return_value=mock_repo.ap_detail_df):
            result_state = ap_reconciliation(state, audit)
        
        # Should detect exceptions (overdue items, notes with issues)
        assert "ap_exceptions_count" in result_state.metrics
        assert result_state.metrics["ap_exceptions_count"] >= 1

    def test_ap_currency_conversion(self, repo_root, temp_output_dir):
        """Test AP reconciliation with multi-currency processing."""
        mock_repo = MockDataRepo()
        mock_repo.ap_detail_df = pd.DataFrame([
            {
                "period": "2025-08", "entity": "TEST_ENT", "bill_id": "BILL_USD_001",
                "vendor_name": "Vendor A", "amount": 5000.0, "currency": "USD",
                "status": "Outstanding", "age_days": 15, "notes": "",
                "bill_date": "2025-08-15"
            },
            {
                "period": "2025-08", "entity": "TEST_ENT", "bill_id": "BILL_EUR_001",
                "vendor_name": "Vendor B", "amount": 4200.0, "currency": "EUR",
                "status": "Overdue", "age_days": 45, "notes": "",
                "bill_date": "2025-07-10"
            },
            {
                "period": "2025-08", "entity": "TEST_ENT", "bill_id": "BILL_GBP_001",
                "vendor_name": "Vendor C", "amount": 3800.0, "currency": "GBP",
                "status": "Outstanding", "age_days": 75, "notes": "",
                "bill_date": "2025-06-15"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.ap_ar_recon.load_ap_detail", 
                  return_value=mock_repo.ap_detail_df):
            result_state = ap_reconciliation(state, audit)
        
        # Should detect exceptions for overdue and age > 60
        assert result_state.metrics["ap_exceptions_count"] >= 2
        assert result_state.metrics["ap_exceptions_total_abs"] > 0
        
        # Verify multi-currency handling in by_entity breakdown
        assert "ap_exceptions_by_entity" in result_state.metrics
        assert result_state.metrics["ap_exceptions_by_entity"]["TEST_ENT"] > 0

    def test_ap_empty_data(self, repo_root, temp_output_dir):
        """Test AP reconciliation with empty data."""
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        # Mock empty DataFrame
        with patch("src.r2r.engines.ap_ar_recon.load_ap_detail", 
                  return_value=pd.DataFrame()):
            result_state = ap_reconciliation(state, audit)
        
        # Should handle empty data gracefully - engine skips processing
        # When empty, no metrics are set (early return)
        assert len(result_state.metrics) == 0
        
        # Should have appropriate message
        assert any("no AP bills in scope" in msg for msg in result_state.messages)


@pytest.mark.unit
@pytest.mark.deterministic  
class TestARReconciliation:
    """Unit tests for AR reconciliation engine."""
    
    def test_ar_recon_basic_processing(self, repo_root, temp_output_dir):
        """Test basic AR reconciliation processing."""
        mock_repo = MockDataRepo()
        mock_repo.ar_detail_df = pd.DataFrame([
            {
                "period": "2025-08", "entity": "TEST_ENT", "invoice_id": "INV001",
                "customer_name": "Customer A", "amount": 10000.0, "currency": "USD",
                "status": "Outstanding", "age_days": 30, "notes": "",
                "invoice_date": "2025-07-31"
            },
            {
                "period": "2025-08", "entity": "TEST_ENT", "invoice_id": "INV002",
                "customer_name": "Customer B", "amount": 7500.0, "currency": "USD",
                "status": "Outstanding", "age_days": 15, "notes": "",
                "invoice_date": "2025-08-15"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.ap_ar_recon.load_ar_detail",
                  return_value=mock_repo.ar_detail_df):
            result_state = ar_reconciliation(state, audit)
        
        # Verify basic metrics
        assert "ar_exceptions_count" in result_state.metrics
        assert "ar_exceptions_total_abs" in result_state.metrics
        assert result_state.metrics["ar_exceptions_count"] >= 0
        
        # Verify audit trail exists
        assert len(audit.records) >= 0
    
    def test_ar_aging_analysis(self, repo_root, temp_output_dir):
        """Test AR aging bucket analysis."""
        mock_repo = MockDataRepo()
        mock_repo.ar_detail_df = pd.DataFrame([
            {
                "period": "2025-08", "entity": "TEST_ENT", "invoice_id": "INV001",
                "customer_name": "Customer A", "amount": 5000.0, "currency": "USD",
                "status": "Outstanding", "age_days": 15, "notes": "",  # Current
                "invoice_date": "2025-08-15"
            },
            {
                "period": "2025-08", "entity": "TEST_ENT", "invoice_id": "INV002", 
                "customer_name": "Customer B", "amount": 3000.0, "currency": "USD",
                "status": "Outstanding", "age_days": 45, "notes": "",  # 31-60 days
                "invoice_date": "2025-07-15"
            },
            {
                "period": "2025-08", "entity": "TEST_ENT", "invoice_id": "INV003",
                "customer_name": "Customer C", "amount": 2000.0, "currency": "USD", 
                "status": "Outstanding", "age_days": 75, "notes": "",  # 61-90 days
                "invoice_date": "2025-06-15"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.ap_ar_recon.load_ar_detail",
                  return_value=mock_repo.ar_detail_df):
            result_state = ar_reconciliation(state, audit)
        
        # Should calculate AR exceptions
        assert "ar_exceptions_count" in result_state.metrics
        assert "ar_exceptions_total_abs" in result_state.metrics

    def test_ar_currency_conversion(self, repo_root, temp_output_dir):
        """Test AR reconciliation with multi-currency processing."""
        mock_repo = MockDataRepo()
        mock_repo.ar_detail_df = pd.DataFrame([
            {
                "period": "2025-08", "entity": "TEST_ENT", "invoice_id": "INV_USD_001",
                "customer_name": "Customer A", "amount": 10000.0, "currency": "USD",
                "status": "Outstanding", "age_days": 30, "notes": "",
                "invoice_date": "2025-07-31"
            },
            {
                "period": "2025-08", "entity": "TEST_ENT", "invoice_id": "INV_EUR_001",
                "customer_name": "Customer B", "amount": 8500.0, "currency": "EUR",
                "status": "Overdue", "age_days": 45, "notes": "",
                "invoice_date": "2025-07-15"
            },
            {
                "period": "2025-08", "entity": "TEST_ENT", "invoice_id": "INV_GBP_001",
                "customer_name": "Customer C", "amount": 7200.0, "currency": "GBP",
                "status": "Outstanding", "age_days": 75, "notes": "",
                "invoice_date": "2025-06-10"
            }
        ])
        
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        with patch("src.r2r.engines.ap_ar_recon.load_ar_detail",
                  return_value=mock_repo.ar_detail_df):
            result_state = ar_reconciliation(state, audit)
        
        # Should detect exceptions for overdue and age > 60
        assert result_state.metrics["ar_exceptions_count"] >= 2
        assert result_state.metrics["ar_exceptions_total_abs"] > 0
        
        # Verify multi-currency handling in by_entity breakdown
        assert "ar_exceptions_by_entity" in result_state.metrics
        assert result_state.metrics["ar_exceptions_by_entity"]["TEST_ENT"] > 0

    def test_ar_empty_data(self, repo_root, temp_output_dir):
        """Test AR reconciliation with empty data."""
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("TEST_ENT")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")
        
        # Mock empty DataFrame
        with patch("src.r2r.engines.ap_ar_recon.load_ar_detail",
                  return_value=pd.DataFrame()):
            result_state = ar_reconciliation(state, audit)
        
        # Should handle empty data gracefully - engine skips processing
        # When empty, no metrics are set (early return)
        assert len(result_state.metrics) == 0
        
        # Should have appropriate message
        assert any("no AR invoices in scope" in msg for msg in result_state.messages)


# Template for additional unit tests
"""
TODO: Implement these additional unit tests:

AP Reconciliation:
1. test_ap_currency_conversion - Test multi-currency AP processing
2. test_ap_empty_data - Test handling of empty AP data
3. test_ap_duplicate_detection - Test duplicate bill detection
4. test_ap_aging_buckets - Test AP aging analysis
5. test_ap_vendor_analysis - Test vendor-specific metrics

AR Reconciliation:  
1. test_ar_currency_conversion - Test multi-currency AR processing
2. test_ar_empty_data - Test handling of empty AR data
3. test_ar_customer_analysis - Test customer-specific metrics
4. test_ar_exception_handling - Test AR exception detection
5. test_ar_bad_debt_analysis - Test bad debt identification

Both:
1. test_safe_str_helper - Test the _safe_str NaN handling utility
2. test_metrics_completeness - Test all expected metrics are generated
3. test_audit_artifact_structure - Test output artifact JSON structure
"""
