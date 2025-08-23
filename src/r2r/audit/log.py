from __future__ import annotations

import json
from datetime import datetime, UTC
from pathlib import Path
from typing import Any, Dict


class AuditLogger:
    def __init__(self, out_dir: Path, run_id: str) -> None:
        self.out_dir = Path(out_dir)
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.out_dir / f"audit_{run_id}.jsonl"

    def append(self, record: Dict[str, Any]) -> None:
        with self.log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps({"ts": datetime.now(UTC).isoformat().replace("+00:00", "Z"), **record}) + "\n")
