#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure src/ is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from r2r.app import main

if __name__ == "__main__":
    # Run with no args for defaults. You can pass CLI flags as usual.
    raise SystemExit(main())
