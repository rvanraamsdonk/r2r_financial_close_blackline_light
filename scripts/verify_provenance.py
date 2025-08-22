#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Verify audit evidence has input_row_ids for key steps")
    p.add_argument("--audit", dest="audit_path", default=None, help="Path to audit_*.jsonl; if omitted, pick latest in out/")
    return p.parse_args()


def find_latest_audit(out_dir: Path) -> Path | None:
    files = sorted(out_dir.glob("audit_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception as e:
                print(f"[DET] Skip malformed line: {e}")
    return rows


def verify(audit_path: Path) -> int:
    recs = read_jsonl(audit_path)
    if not recs:
        print(f"[DET] No records in {audit_path}")
        return 1

    # Map deterministic runs to evidence ids, and evidence ids to evidence records
    det_to_ev: Dict[str, str] = {}
    ev_by_id: Dict[str, Dict[str, Any]] = {}

    for r in recs:
        if r.get("type") == "deterministic":
            fn = r.get("fn")
            evid = r.get("evidence_id")
            if fn and evid:
                det_to_ev[fn] = evid
        elif r.get("type") == "evidence":
            evid = r.get("id")
            if evid:
                ev_by_id[evid] = r

    failures: List[str] = []

    def check_fn(fn_name: str, *, allow_empty_or_none: bool = False) -> None:
        evid = det_to_ev.get(fn_name)
        if not evid:
            failures.append(f"Missing deterministic record for {fn_name}")
            return
        ev = ev_by_id.get(evid)
        if not ev:
            failures.append(f"Missing evidence record for {fn_name} (evidence_id={evid})")
            return
        rows = ev.get("input_row_ids")
        if allow_empty_or_none:
            # For steps that may legitimately produce zero exceptions, accept None or a (possibly empty) list
            if rows is None:
                return
            if isinstance(rows, list) and all(isinstance(x, str) for x in rows):
                return
            failures.append(f"Invalid input_row_ids for {fn_name}: expected None or list[str]")
        else:
            # Strict: must be a non-empty list[str]
            if not isinstance(rows, list) or not rows or not all(isinstance(x, str) for x in rows):
                failures.append(f"Invalid or empty input_row_ids for {fn_name}")

    check_fn("tb_diagnostics")
    check_fn("accruals_check")
    check_fn("email_evidence")
    # New deterministic engines: allow None/empty as there may be zero exceptions
    check_fn("bank_reconciliation", allow_empty_or_none=True)
    check_fn("intercompany_reconciliation", allow_empty_or_none=True)
    check_fn("flux_analysis", allow_empty_or_none=True)

    if failures:
        print("[DET] Provenance verification FAILED:")
        for m in failures:
            print(f"[DET] - {m}")
        return 1

    print(
        "[DET] Provenance verification PASSED: input_row_ids present/valid for tb_diagnostics, accruals_check, email_evidence, bank_reconciliation, intercompany_reconciliation, flux_analysis",
        flush=True,
    )
    return 0


def main(argv: List[str] | None = None) -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "out"

    if args.audit_path:
        audit_path = Path(args.audit_path)
    else:
        audit_path = find_latest_audit(out_dir) or Path()

    if not audit_path.exists():
        print(f"[DET] Audit file not found. Searched: {audit_path or out_dir}")
        return 1

    print(f"[DET] Using audit: {audit_path}", flush=True)
    rc = verify(audit_path)
    # Ensure a line is printed even if upstream prints are buffered or suppressed
    if rc == 0:
        print("[DET] Verification completed successfully.", flush=True)
    else:
        print("[DET] Verification completed with failures.", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
