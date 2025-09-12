"""Unit tests for the email evidence engine."""

import json
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.r2r.engines.email_evidence import email_evidence_analysis
from tests.fixtures.mocks import MockAuditLogger
from tests.fixtures.helpers import StateBuilder

@pytest.mark.unit
class TestEmailEvidenceEngine:

    def test_source_evidence_is_added(self, repo_root, temp_output_dir):
        """Test that the source_evidence field is correctly added for drill-through."""
        # 1. Mock the input data
        mock_emails = {
            "items": [
                {
                    "email_id": "EMAIL-TEST-001",
                    "subject": "Test Email",
                    "body": "This is a test concerning an accrual for $10,000.",
                    "timestamp": "2025-08-15T10:00:00Z"
                }
            ]
        }
        emails_path = Path(temp_output_dir) / "emails.json"
        emails_path.write_text(json.dumps(mock_emails))

        # 2. Setup the state
        state = (StateBuilder(repo_root, temp_output_dir)
                 .with_period("2025-08")
                 .with_entity("ALL")
                 .with_data_path(str(temp_output_dir)) # Point data path to temp dir
                 .build())
        
        # The engine looks for supporting/emails.json, so let's create that structure
        supporting_dir = Path(temp_output_dir) / "supporting"
        supporting_dir.mkdir()
        (supporting_dir / "emails.json").write_text(json.dumps(mock_emails))

        audit = MockAuditLogger(temp_output_dir, "TEST_RUN")

        # 3. Mock the AI call to isolate the deterministic logic we're testing
        with patch('src.r2r.engines.email_evidence._analyze_email_with_ai') as mock_analyze_ai:
            # Have the mock return a basic structure including the new source_evidence field
            def side_effect(email, state, audit, source_file_path):
                enhanced = email.copy()
                enhanced["source_evidence"] = {"uri": str(source_file_path), "id": email.get("email_id")}
                enhanced["ai_transaction_matches"] = []
                return enhanced
            mock_analyze_ai.side_effect = side_effect

            # 4. Run the engine
            result_state = email_evidence_analysis(state, audit)

        # 5. Verify the output
        artifact_path_str = result_state.metrics.get("email_evidence_artifact")
        assert artifact_path_str, "Email evidence artifact not found in metrics"
        artifact_path = Path(artifact_path_str)
        assert artifact_path.exists(), "Email evidence artifact file does not exist"

        with artifact_path.open("r") as f:
            artifact_data = json.load(f)

        assert "items" in artifact_data
        assert len(artifact_data["items"]) == 1

        email_item = artifact_data["items"][0]
        assert "source_evidence" in email_item
        
        source_evidence = email_item["source_evidence"]
        assert "uri" in source_evidence
        assert "id" in source_evidence
        assert source_evidence["id"] == "EMAIL-TEST-001"
        # Check that the URI points to the correct source file
        assert Path(source_evidence["uri"]).name == "emails.json"
