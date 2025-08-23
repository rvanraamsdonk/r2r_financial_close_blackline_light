from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console


@dataclass
class SectionInfo:
    number: int
    name: str
    pattern: str  # glob pattern to find latest artifact


SECTIONS: List[SectionInfo] = [
    SectionInfo(1, "AP RECONCILIATION", "ap_reconciliation_*.json"),
    SectionInfo(2, "AR RECONCILIATION", "ar_reconciliation_*.json"),
    SectionInfo(3, "FLUX ANALYSIS", "flux_analysis_*.json"),
    SectionInfo(4, "BANK RECONCILIATION", "bank_reconciliation_*.json"),
    SectionInfo(5, "JE LIFECYCLE", "je_lifecycle_*.json"),
    SectionInfo(6, "ACCRUALS", "accruals_*.json"),
]


def _latest_artifact(out_dir: Path, pattern: str) -> Optional[Path]:
    files = sorted(out_dir.glob(pattern))
    if not files:
        return None
    # Prefer lexicographically latest which works for timestamped names
    return files[-1]


def _osc8(label: str, url: str) -> str:
    # OSC-8 hyperlink; terminals that don't support will show label
    return f"\x1b]8;;{url}\x1b\\{label}\x1b]8;;\x1b\\"


def _pct(v: Optional[float]) -> Optional[int]:
    if v is None:
        return None
    try:
        return int(round(float(v) * 100))
    except Exception:
        return None


def _fmt_amt(amount: Any, currency: Optional[str]) -> str:
    try:
        val = float(amount)
    except Exception:
        return str(amount)
    cur = (currency or "").upper()
    sign = "-" if val < 0 else ""
    return f"{sign}{cur} {abs(val):,.2f}".strip()


def _derive_id(item: Dict[str, Any], domain: str) -> str:
    # Prefer explicit ids
    if domain == "AP" and item.get("bill_id"):
        return f"AP-{item['bill_id']}"
    if domain == "AR" and item.get("invoice_id"):
        return f"AR-{item['invoice_id']}"
    if item.get("id"):
        return str(item["id"])
    # Fallback stable key from known fields
    key = "|".join(str(item.get(k, "")) for k in ("entity", "vendor_name", "customer_name", "bill_id", "invoice_id", "amount"))
    return f"{domain}-{abs(hash(key)) % (10**9):09d}"


def _collect_evidence(item: Dict[str, Any]) -> List[str]:
    # Evidence may appear as list of paths under common keys
    for k in ("evidence", "evidences", "evidence_paths", "attachments"):
        v = item.get(k)
        if isinstance(v, list):
            return [str(x) for x in v]
        if isinstance(v, str):
            return [v]
    return []


def _ai_fields(item: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[float]]:
    ai = item.get("ai")
    if isinstance(ai, dict):
        return (
            ai.get("recommended_action"),
            ai.get("rationale_short") or ai.get("rationale") or ai.get("why"),
            ai.get("confidence"),
        )
    # Back-compat for older fields
    return (
        item.get("recommended_action"),
        item.get("ai_rationale") or item.get("rationale"),
        item.get("confidence"),
    )


def _owner(item: Dict[str, Any]) -> Optional[str]:
    return item.get("owner") or item.get("assignee") or item.get("team")


def _due(item: Dict[str, Any]) -> Optional[str]:
    return item.get("due_date") or item.get("due")


def _domain(item: Dict[str, Any], default_domain: str) -> str:
    return item.get("subledger") or item.get("domain") or default_domain


def _amount_fields(item: Dict[str, Any]) -> Tuple[Optional[Any], Optional[str]]:
    for amt_key in ("amount", "amount_usd", "variance", "diff", "amt"):
        if amt_key in item:
            return item[amt_key], item.get("currency")
    return None, None


def _kv_presentable(item: Dict[str, Any], keys: List[str]) -> List[str]:
    parts: List[str] = []
    for k in keys:
        v = item.get(k)
        if v is not None and v != "":
            parts.append(f"{k.replace('_', '').capitalize()}={v}")
    return parts


def _section_stats(items: List[Dict[str, Any]]) -> Tuple[int, int, int]:
    total = len(items)
    open_cnt = sum(1 for x in items if str(x.get("status", "")).lower() in ("open", "outstanding", "overdue"))
    resolved = total - open_cnt
    return total, open_cnt, resolved


def _render_section(console: Console, num: int, name: str, artifact: Path, items_key: str = "exceptions") -> None:
    data = json.loads(artifact.read_text())
    items = data.get(items_key, [])
    total, open_cnt, resolved = _section_stats(items)

    # Header line
    run_id = _extract_run_id(artifact.name)
    header = f"{num}. {name}  —  items={total} open={open_cnt} resolved={resolved}  •  run={run_id}"
    console.print(f"[bold cyan]{header}[/bold cyan]")
    console.print("-" * 80)

    for it in items:
        domain = _domain(it, name.split()[0])
        iid = _derive_id(it, domain)
        owner = _owner(it) or ""
        due = _due(it) or ""
        amt, cur = _amount_fields(it)
        amt_s = _fmt_amt(amt, cur) if amt is not None else ""

        # Domain-specific kvs
        kvs: List[str] = []
        if domain.startswith("AP"):
            kvs.extend(_kv_presentable(it, ["vendor_name", "bill_id"]))
        elif domain.startswith("AR"):
            kvs.extend(_kv_presentable(it, ["customer_name", "invoice_id"]))
        elif name.startswith("FLUX"):
            kvs.extend(_kv_presentable(it, ["account", "dimension"]))
        elif name.startswith("BANK"):
            kvs.extend(_kv_presentable(it, ["statement_id", "txn_id"]))
        elif name.startswith("JE"):
            kvs.extend(_kv_presentable(it, ["je_id", "je_source"]))
        elif name.startswith("ACCRUALS"):
            kvs.extend(_kv_presentable(it, ["accrual_id", "ref"]))

        line1_parts = [f"ID={iid}"]
        if kvs:
            line1_parts.append("  ".join(kvs))
        if amt_s:
            line1_parts.append(f"Amt={amt_s}")
        if due:
            line1_parts.append(f"Due={due}")
        if owner:
            line1_parts.append(f"Owner={owner}")
        console.print("  ".join(line1_parts))

        rec, why, conf = _ai_fields(it)
        rec_s = rec or "Review"
        pct = _pct(conf)
        conf_s = f" [Conf; {pct}%]" if pct is not None else ""
        console.print(f"AI recommends: {rec_s}{conf_s}")
        if why:
            console.print(f"WHY: {why}")
        else:
            console.print("WHY: -")

        # Evidence
        evid = _collect_evidence(it)
        if evid:
            labels = []
            for e in evid:
                url = e if re.match(r"^[a-z]+://", str(e)) else f"file://{Path(e).resolve()}"
                labels.append(_osc8(Path(e).name, url) + f" ({url})")
            console.print("Evidence: " + "  ".join(labels))
        else:
            console.print("Evidence: -")

        console.print(f"Provenance: {artifact.name}:item_id={iid}")
        # Spacing between items kept minimal for density


def _extract_run_id(filename: str) -> str:
    # Expect *_YYYYmmddTHHMMSSZ.json
    m = re.search(r"_(\d{8}T\d{6}Z)\.json$", filename)
    return m.group(1) if m else "unknown"


def render_printable(out_dir: Path, console: Optional[Console] = None) -> None:
    console = console or Console()

    # Walk each section, render if artifact exists
    for s in SECTIONS:
        art = _latest_artifact(out_dir, s.pattern)
        if not art:
            continue
        try:
            key = "exceptions" if s.name in ("AP RECONCILIATION", "AR RECONCILIATION") else "items"
            _render_section(console, s.number, s.name, art, items_key=key)
            console.print("")
        except Exception as e:
            console.print(f"[yellow][WARN][/yellow] Failed to render {s.name}: {e}")

    # Footer: minimal; main policy header appears in app
    console.print("—")
