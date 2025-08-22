#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lightweight smoke test for provenance")
    p.add_argument("--audit", dest="audit_path", default=None, help="Path to audit_*.jsonl; if omitted, pick latest in out/")
    return p.parse_args()


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    scripts_dir = repo_root / "scripts"
    out_dir = repo_root / "out"

    # Import verify_provenance utilities from scripts/
    sys.path.append(str(scripts_dir))
    try:
        from verify_provenance import verify as verify_provenance, find_latest_audit  # type: ignore
    except Exception as e:  # pragma: no cover
        print(f"[DET] Failed to import verify_provenance: {e}")
        return 1

    args = parse_args()

    if args.audit_path:
        audit_path = Path(args.audit_path)
    else:
        audit_path = find_latest_audit(out_dir) or Path()

    if not audit_path.exists():
        print(f"[DET] Audit file not found. Searched: {audit_path or out_dir}")
        return 1

    print(f"[DET] Using audit: {audit_path}")
    rc = verify_provenance(audit_path)
    if rc == 0:
        print("[DET] Smoke test PASSED.")
    else:
        print("[DET] Smoke test FAILED.")
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
