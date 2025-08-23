"""
Pytest configuration and shared fixtures for R2R Financial Close testing.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any, Dict, Generator
from unittest.mock import Mock, MagicMock

import pandas as pd
import pytest

from src.r2r.state import R2RState
from src.r2r.audit import AuditLogger


@pytest.fixture(scope="session")
def repo_root() -> Path:
    """Repository root directory."""
    return Path(__file__).resolve().parents[1]


@pytest.fixture(scope="session")
def test_data_dir(repo_root: Path) -> Path:
    """Test data directory."""
    return repo_root / "tests" / "fixtures" / "data"


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """Temporary output directory for test artifacts."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_audit_logger(temp_output_dir: Path) -> AuditLogger:
    """Mock audit logger for testing."""
    return AuditLogger(temp_output_dir, "TEST_RUN")


@pytest.fixture
def minimal_state(repo_root: Path, temp_output_dir: Path) -> R2RState:
    """Minimal R2R state for unit testing."""
    return R2RState(
        period="2025-08",
        prior="2025-07",
        entity="TEST_ENT",
        repo_root=repo_root,
        data_path=repo_root / "tests" / "fixtures" / "data",
        out_path=temp_output_dir,
        entities_df=None,
        coa_df=None,
        tb_df=None,
        fx_df=None,
        ai_mode="off",
        show_prompts=False,
        save_evidence=False,
    )


@pytest.fixture
def sample_entities_df() -> pd.DataFrame:
    """Sample entities DataFrame for testing."""
    return DataFrameBuilder.entities().add_entity("ENT100", "Test Entity", "USD", "USD").build()


@pytest.fixture
def sample_coa_df() -> pd.DataFrame:
    """Sample chart of accounts DataFrame for testing."""
    return pd.DataFrame([
        {"account": "1000", "name": "Cash", "type": "Asset", "class": "BS"},
        {"account": "1100", "name": "Accounts Receivable", "type": "Asset", "class": "BS"},
        {"account": "2000", "name": "Accounts Payable", "type": "Liability", "class": "BS"},
        {"account": "5000", "name": "Revenue", "type": "Revenue", "class": "IS"},
    ])


@pytest.fixture
def sample_tb_df() -> pd.DataFrame:
    """Sample trial balance DataFrame for testing."""
    return pd.DataFrame([
        {"period": "2025-08", "entity": "ENT100", "account": "1000", "balance": 100000.0, "balance_usd": 100000.0},
        {"period": "2025-08", "entity": "ENT100", "account": "1100", "balance": 50000.0, "balance_usd": 50000.0},
        {"period": "2025-08", "entity": "ENT100", "account": "2000", "balance": -75000.0, "balance_usd": -75000.0},
        {"period": "2025-08", "entity": "ENT100", "account": "5000", "balance": -25000.0, "balance_usd": -25000.0},
    ])


@pytest.fixture
def sample_fx_df() -> pd.DataFrame:
    """Sample FX rates DataFrame for testing."""
    return pd.DataFrame([
        {"period": "2025-08", "currency": "USD", "rate": 1.0},
        {"period": "2025-08", "currency": "EUR", "rate": 1.092},
        {"period": "2025-08", "currency": "GBP", "rate": 1.275},
    ])


@pytest.fixture
def mock_ai_response() -> Dict[str, Any]:
    """Mock AI response for testing."""
    return {
        "text": "Test AI response",
        "prompt_run": {
            "prompt": "Test prompt",
            "response": "Test response",
            "model": "test-model",
            "tokens": 100,
            "cost_usd": 0.001,
        },
        "tag": "[AI]",
    }


@pytest.fixture
def mock_ai_module():
    """Mock AI module that returns predictable responses."""
    mock = Mock()
    mock.return_value = {
        "text": "Mock AI narrative",
        "prompt_run": {
            "prompt": "Mock prompt",
            "response": "Mock response",
            "model": "mock-model",
            "tokens": 50,
            "cost_usd": 0.0005,
        },
        "tag": "[AI]",
    }
    return mock


class MockDataLoader:
    """Mock data loader for testing without file dependencies."""
    
    def __init__(self):
        self.entities_df = pd.DataFrame([
            {"entity": "TEST_ENT", "name": "Test Entity", "currency": "USD", "country": "US"}
        ])
        self.coa_df = pd.DataFrame([
            {"account": "1000", "name": "Test Cash", "type": "Asset", "class": "BS"}
        ])
        self.tb_df = pd.DataFrame([
            {"period": "2025-08", "entity": "TEST_ENT", "account": "1000", "balance": 1000.0, "balance_usd": 1000.0}
        ])
        self.fx_df = pd.DataFrame([
            {"period": "2025-08", "currency": "USD", "rate": 1.0}
        ])


@pytest.fixture
def mock_data_loader():
    """Mock data loader fixture."""
    return MockDataLoader()


# Pytest markers for test categorization
pytestmark = pytest.mark.filterwarnings("ignore:.*:DeprecationWarning")
