#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Audit drill-through and AI artifact inspection")
    sub = p.add_subparsers(dest="cmd", required=True)

    # drill subcommand
    pdrl = sub.add_parser("drill", help="Drill-through to source rows using audit evidence input_row_ids")
    pdrl.add_argument(
        "--fn",
        required=True,
        choices=["tb_diagnostics", "accruals_check", "email_evidence"],
        help="Function to drill through",
    )
    pdrl.add_argument("--audit", dest="audit_path", default=None, help="Path to audit_*.jsonl; if omitted, pick latest in out/")
    pdrl.add_argument("--limit", type=int, default=None, help="Limit number of matched rows printed")
    pdrl.add_argument("--format", dest="fmt", choices=["csv", "json"], default="csv", help="Output format")

    # list-ai subcommand
    plai = sub.add_parser("list-ai", help="List AI artifacts and metrics from audit log")
    plai.add_argument("--audit", dest="audit_path", default=None, help="Path to audit_*.jsonl; if omitted, pick latest in out/")
    plai.add_argument("--run", dest="run_id", default=None, help="Run ID to select audit_*.jsonl explicitly (overrides --audit)")
    plai.add_argument("--json", dest="as_json", action="store_true", help="Emit JSON instead of text lines")
    return p.parse_args()


def find_latest_audit(out_dir: Path) -> Path | None:
    files = sorted(out_dir.glob("audit_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def find_audit_by_run(out_dir: Path, run_id: str) -> Path | None:
    cand = out_dir / f"audit_{run_id}.jsonl"
    return cand if cand.exists() else None


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
    # Some runs may log a TB URI using hyphenated period (YYYY-MM) while files
    # use underscore (YYYY_MM). If the original path is missing, try an
    # underscore variant of the filename.
    p = Path(uri)
    if not p.exists():
        name = p.name
        if name.startswith("trial_balance_") and "-" in name:
            alt = p.with_name(name.replace("-", "_"))
            if alt.exists():
                p = alt
    df = pd.read_csv(p, dtype={"period": str, "entity": str, "account": str})
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

    # Resolve audit path based on subcommand
    audit_path: Path | None = None
    if getattr(args, "run_id", None):
        audit_path = find_audit_by_run(out_dir, args.run_id)
    if not audit_path and getattr(args, "audit_path", None):
        audit_path = Path(args.audit_path)
    if not audit_path:
        audit_path = find_latest_audit(out_dir)
    if not audit_path or not audit_path.exists():
        print(f"[DET] Audit file not found. Searched: {audit_path or out_dir}")
        return 1

    recs = read_jsonl(audit_path)

    if args.cmd == "list-ai":
        # Gather ai_output, ai_metrics
        outputs: List[Dict[str, Any]] = []
        metrics_map: Dict[str, Dict[str, Any]] = {}
        for r in recs:
            if r.get("type") == "ai_output":
                outputs.append(r)
            elif r.get("type") == "ai_metrics":
                k = r.get("kind")
                metrics_map[k] = {"tokens": r.get("tokens"), "cost_usd": r.get("cost_usd")}
        outputs.sort(key=lambda r: r.get("generated_at", ""))
        if args.as_json:
            enriched = []
            for o in outputs:
                k = o.get("kind")
                mm = metrics_map.get(k, {})
                enriched.append({**o, **{f"ai_{k}_tokens": mm.get("tokens"), f"ai_{k}_cost_usd": mm.get("cost_usd")}})
            # Write explicitly to stdout and flush to avoid buffered/no-output issues in some environments
            sys.stdout.write(json.dumps(enriched, indent=2) + "\n")
            sys.stdout.flush()
        else:
            print(f"[DET] AI artifacts for run: {audit_path.name}")
            for o in outputs:
                k = o.get("kind")
                mm = metrics_map.get(k, {})
                print(
                    f"[AI] kind={k} artifact={o.get('artifact')} tokens={mm.get('tokens')} cost_usd={mm.get('cost_usd')} generated_at={o.get('generated_at')}"
                )
        return 0

    # cmd == drill
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
    # Apply limit before printing
    if args.limit is not None and args.limit >= 0:
        out_df = out_df.head(args.limit)
    # Print in requested format
    if args.fmt == "json":
        print(out_df.to_json(orient="records", force_ascii=False, indent=2))
    else:
        # CSV to stdout
        print(out_df.to_csv(index=False).strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
