#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Drill-through to source rows using audit evidence input_row_ids")
    p.add_argument(
        "--fn",
        required=True,
        choices=["tb_diagnostics", "accruals_check", "email_evidence"],
        help="Function to drill through",
    )
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
            rows.append(json.loads(line))
    return rows


def load_evidence_for_fn(recs: List[Dict[str, Any]], fn_name: str) -> Dict[str, Any]:
    evid = None
    for r in recs:
        if r.get("type") == "deterministic" and r.get("fn") == fn_name:
            evid = r.get("evidence_id")
    if not evid:
        raise RuntimeError(f"No deterministic record with evidence_id for fn={fn_name}")
    for r in recs:
        if r.get("type") == "evidence" and r.get("id") == evid:
            return r
    raise RuntimeError(f"Evidence record not found for id={evid}")


def drill_tb(uri: str, input_row_ids: List[str]) -> pd.DataFrame:
    df = pd.read_csv(uri, dtype={"period": str, "entity": str, "account": str})
    ids = set(input_row_ids)
    key = df.apply(lambda r: f"{r['period']}|{r['entity']}|{r['account']}", axis=1)
    mask = key.isin(ids)
    return df.loc[mask]


def drill_accruals(uri: str, input_row_ids: List[str]) -> pd.DataFrame:
    df = pd.read_csv(uri, dtype={"entity": str, "accrual_id": str})
    ids = set(input_row_ids)
    key = df.apply(lambda r: f"{r['entity']}|{r['accrual_id']}", axis=1)
    mask = key.isin(ids)
    return df.loc[mask]


def drill_emails(uri: str, input_row_ids: List[str]) -> pd.DataFrame:
    data = json.loads(Path(uri).read_text(encoding="utf-8"))
    ids = set(input_row_ids)
    rows = [e for e in data if str(e.get("email_id")) in ids]
    if not rows:
        return pd.DataFrame()
    return pd.json_normalize(rows)


def main() -> int:
    args = parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    out_dir = repo_root / "out"

    audit_path = Path(args.audit_path) if args.audit_path else (find_latest_audit(out_dir) or Path())
    if not audit_path.exists():
        print(f"[DET] Audit file not found. Searched: {audit_path or out_dir}")
        return 1

    recs = read_jsonl(audit_path)
    ev = load_evidence_for_fn(recs, args.fn)
    uri = ev.get("uri")
    rows = ev.get("input_row_ids") or []
    if not uri or not rows:
        print(f"[DET] Missing uri or input_row_ids for fn={args.fn}")
        return 1

    if args.fn == "tb_diagnostics":
        out_df = drill_tb(uri, rows)
    elif args.fn == "accruals_check":
        out_df = drill_accruals(uri, rows)
    else:
        out_df = drill_emails(uri, rows)

    print(f"[DET] Drill-through for {args.fn}")
    print(f"[DET] Evidence URI: {uri}")
    print(f"[DET] input_row_ids: {len(rows)} (showing matched rows below)")
    if out_df.empty:
        print("[DET] No matching rows found in source file")
        return 1
    # Print as CSV to stdout
    print(out_df.to_csv(index=False).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
