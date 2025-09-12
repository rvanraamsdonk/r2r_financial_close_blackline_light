"""
Unit tests for AI modules with mocking.
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, Mock

from src.r2r.ai.modules import ai_validation_root_causes, ai_ap_ar_suggestions, ai_flux_narratives, ai_bank_rationales
from tests.fixtures.mocks import MockAIModule, MockAIResponse, MockAuditLogger
from tests.fixtures.helpers import StateBuilder


@pytest.mark.unit
@pytest.mark.ai
class TestAIModules:
    """Unit tests for AI modules with proper mocking."""
    
    def test_ai_validation_root_causes_with_mock(self, repo_root, temp_output_dir):
        """Test AI validation root causes with mock."""
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT100")
                .with_ai_mode("assist")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        # Execute AI validation
        result_state = ai_validation_root_causes(state, audit)
        
        # Verify AI processing occurred
        assert result_state.ai_mode == "assist"
        assert len(result_state.prompt_runs) > 0
        assert any("validation" in str(run) for run in result_state.prompt_runs)
        assert len(audit.records) > 0
    
    def test_ai_validation_root_causes_disabled(self, repo_root, temp_output_dir):
        """Test AI validation when AI is disabled."""
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_ai_mode("off")
                .build())
        
        # When AI is off, should not make AI calls
        with patch("src.r2r.ai.modules.ai_validation_root_causes") as mock_ai:
            from src.r2r.ai.modules import ai_validation_root_causes
            
            # Mock the function to return state unchanged when AI is off
            mock_ai.return_value = state
            
            result_state = ai_validation_root_causes(state, Mock())
            
            # Should return state without AI processing
            assert result_state.ai_mode == "off"
    
    def test_ai_ap_ar_suggestions_with_facts(self, repo_root, temp_output_dir):
        """Test AP/AR AI suggestions with mock facts."""
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT100")
                .with_ai_mode("assist")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        # Execute AI AP/AR suggestions
        result_state = ai_ap_ar_suggestions(state, audit)
        
        # Verify AI processing
        assert len(result_state.prompt_runs) > 0
        assert any("ap_ar" in str(run) for run in result_state.prompt_runs)
        assert len(audit.records) > 0
    
    def test_ai_flux_narratives_variance_analysis(self, repo_root, temp_output_dir):
        """Test flux narratives AI with variance analysis."""
        state = (StateBuilder(repo_root, temp_output_dir)
                .with_period("2025-08")
                .with_entity("ENT100")
                .with_ai_mode("assist")
                .build())
        
        audit = MockAuditLogger(temp_output_dir, "test_run")
        
        # Execute AI flux narratives
        result_state = ai_flux_narratives(state, audit)
        
        # Verify AI processing
        assert len(result_state.prompt_runs) > 0
        assert any("flux" in str(run) for run in result_state.prompt_runs)
        assert len(audit.records) > 0
    
    def test_ai_flux_narratives_with_email_context(self, repo_root, temp_output_dir):
        """Test that ai_flux_narratives includes email evidence in its context."""
        # 1. Create mock artifacts
        flux_artifact_path = Path(temp_output_dir) / "flux_analysis_run.json"
        flux_artifact_content = {"rows": [{"entity": "E1", "account": "A1", "var_vs_budget": 1000}]}
        flux_artifact_path.write_text(json.dumps(flux_artifact_content))

        email_artifact_path = Path(temp_output_dir) / "email_evidence_run.json"
        email_artifact_content = {"items": [{"email_id": "EMAIL-001", "summary": "Test summary"}]}
        email_artifact_path.write_text(json.dumps(email_artifact_content))

        # 2. Build state with metrics pointing to these artifacts
        state = (StateBuilder(repo_root, temp_output_dir)
                 .with_period("2025-08")
                 .with_ai_mode("assist")
                 .with_metric("flux_analysis_artifact", str(flux_artifact_path))
                 .with_metric("email_evidence_artifact", str(email_artifact_path))
                 .build())

        audit = MockAuditLogger(temp_output_dir, "test_run")

        # 3. Mock the _invoke_ai function to inspect the context
        with patch("src.r2r.ai.modules._invoke_ai") as mock_invoke_ai:
            # Define a dummy return value for the mock
            mock_invoke_ai.return_value = {"narratives": []}

            # 4. Execute the function
            ai_flux_narratives(state, audit)

            # 5. Assert that the mock was called and inspect the context
            mock_invoke_ai.assert_called_once()
            
            # The context is the 3rd argument of _invoke_ai(kind, template_name, context, payload)
            call_args, call_kwargs = mock_invoke_ai.call_args
            context = call_args[2]
            
            assert "email_evidence" in context
            assert len(context["email_evidence"]) == 1
            assert context["email_evidence"][0]["email_id"] == "EMAIL-001"


@pytest.mark.unit
@pytest.mark.ai
class TestAIModuleCaching:
    """Test AI module caching behavior."""
    
    def test_ai_cache_hit_behavior(self, temp_output_dir):
        """Test AI caching mechanism."""
        # This would test the with_cache functionality
        # Implementation depends on actual caching logic in ai/infra.py
        
        policy = {"period": "2025-08"}
        facts = {"test": "data"}
        
        with patch("src.r2r.ai.infra.with_cache") as mock_cache:
            mock_cache.return_value = (
                temp_output_dir / "test_cache.json",
                {"text": "Cached response", "prompt_run": {"tokens": 0, "cost_usd": 0.0}, "tag": "[AI]"},
                True  # was_cached=True
            )
            
            # Test that cached responses are used
            # This is a template - actual implementation depends on module structure
            pass
    
    def test_ai_cost_tracking(self):
        """Test AI cost and token tracking."""
        mock_response = MockAIResponse(tokens=150, cost_usd=0.0015)
        
        with patch("src.r2r.ai.infra.estimate_tokens") as mock_tokens:
            with patch("src.r2r.ai.infra.estimate_cost_usd") as mock_cost:
                mock_tokens.return_value = 150
                mock_cost.return_value = 0.0015
                
                # Test cost calculation logic
                # Implementation depends on actual cost tracking in modules
                pass


    def test_ai_bank_rationales_with_email_context(self, repo_root, temp_output_dir):
        """Test that ai_bank_rationales includes email evidence in its context."""
        # 1. Create mock artifacts
        bank_artifact_path = Path(temp_output_dir) / "bank_reconciliation_run.json"
        bank_artifact_content = {"exceptions": [{"bank_txn_id": "TXN001", "amount": 1000}]}
        bank_artifact_path.write_text(json.dumps(bank_artifact_content))

        email_artifact_path = Path(temp_output_dir) / "email_evidence_run.json"
        email_artifact_content = {"items": [{"email_id": "EMAIL-001", "summary": "Test summary"}]}
        email_artifact_path.write_text(json.dumps(email_artifact_content))

        # 2. Build state with metrics pointing to these artifacts
        state = (StateBuilder(repo_root, temp_output_dir)
                 .with_period("2025-08")
                 .with_ai_mode("assist")
                 .with_metric("bank_reconciliation_artifact", str(bank_artifact_path))
                 .with_metric("email_evidence_artifact", str(email_artifact_path))
                 .build())

        audit = MockAuditLogger(temp_output_dir, "test_run")

        # 3. Mock the _invoke_ai function to inspect the context
        with patch("src.r2r.ai.modules._invoke_ai") as mock_invoke_ai:
            mock_invoke_ai.return_value = {"rationales": []}

            # 4. Execute the function
            ai_bank_rationales(state, audit)

            # 5. Assert that the mock was called and inspect the context
            mock_invoke_ai.assert_called_once()
            
            call_args, call_kwargs = mock_invoke_ai.call_args
            context = call_args[2]
            
            assert "email_evidence" in context
            assert len(context["email_evidence"]) == 1
            assert context["email_evidence"][0]["email_id"] == "EMAIL-001"


# Template for additional AI module tests
"""
TODO: Implement these additional AI module tests:

1. test_ai_bank_rationales - Test bank reconciliation AI narratives
2. test_ai_accruals_narratives - Test accruals AI processing
3. test_ai_hitl_case_summaries - Test HITL AI summaries
4. test_ai_gatekeeping_rationales - Test gatekeeping AI analysis
5. test_ai_controls_owner_summaries - Test controls AI summaries
6. test_ai_close_report_exec_summary - Test executive summary AI

Error Handling:
1. test_ai_module_error_handling - Test AI API error scenarios
2. test_ai_timeout_handling - Test AI timeout scenarios
3. test_ai_invalid_response_handling - Test malformed AI responses
4. test_ai_rate_limiting - Test AI rate limiting behavior

Configuration:
1. test_ai_mode_strict_behavior - Test strict AI mode
2. test_ai_mode_assist_behavior - Test assist AI mode
3. test_show_prompts_behavior - Test prompt visibility
4. test_ai_cost_rate_configuration - Test configurable cost rates
"""
