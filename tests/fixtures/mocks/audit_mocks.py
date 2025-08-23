"""
Audit logging mocks for testing.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import Mock


class MockAuditLogger:
    """Mock audit logger that captures calls without file I/O."""
    
    def __init__(self, out_dir: Path, run_id: str):
        self.out_dir = out_dir
        self.run_id = run_id
        self.log_path = out_dir / f"audit_{run_id}.jsonl"
        self.records: List[Dict[str, Any]] = []
    
    def append(self, record: Dict[str, Any]) -> None:
        """Capture audit record without writing to file."""
        self.records.append({
            "ts": "2025-08-23T12:00:00Z",  # Fixed timestamp for testing
            **record
        })
    
    def get_records_by_type(self, record_type: str) -> List[Dict[str, Any]]:
        """Get all records of a specific type."""
        return [r for r in self.records if r.get("type") == record_type]
    
    def get_records_by_step(self, step: str) -> List[Dict[str, Any]]:
        """Get all records for a specific step."""
        return [r for r in self.records if r.get("step") == step]
    
    def clear(self) -> None:
        """Clear all captured records."""
        self.records.clear()
    
    def record_count(self) -> int:
        """Get total number of records."""
        return len(self.records)
