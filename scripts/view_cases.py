#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "out"


def _latest_cases_file() -> Path | None:
    candidates = sorted(OUT.glob("cases_*.json"))
    return candidates[-1] if candidates else None


def main() -> int:
    p = _latest_cases_file()
    if not p or not p.exists():
        print("No cases_*.json found in out/")
        return 1
    data: List[Dict[str, Any]] = json.loads(p.read_text())
    print(f"HITL Cases ({len(data)}) -> {p}")
    for c in data:
        print(
            f"- {c.get('id')} | {c.get('severity')} | {c.get('source')} | {c.get('title')} | evidence={len(c.get('evidence_uris', []))}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
