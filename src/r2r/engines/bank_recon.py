from __future__ import annotations

import json
from datetime import datetime, timedelta, UTC
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd

from ..audit.log import AuditLogger
from ..schemas import DeterministicRun, EvidenceRef, MethodType, OutputTag
from ..state import R2RState
from ..data.static_loader import load_bank_transactions


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _find_bank_file(data_path: Path, period: str) -> Path:
    # Not used anymore; kept for backward-compat if needed by callers.
    base = Path(data_path) / "subledgers" / "bank_statements"
    candidates = [
        base / f"bank_transactions_{period}.csv",
        base / f"bank_transactions_{period.replace('-', '_')}.csv",
        base / "bank_transactions_aug.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"No unified bank transactions file found for period {period} in {base}")


def bank_reconciliation(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic bank reconciliation (duplicate detection):
    - Load period/entity-scoped bank transactions
    - Flag potential duplicates sharing the same signature (entity, date, amount, currency, counterparty, transaction_type)
    - Emit artifact and provenance; update messages, tags, metrics
    """
    period = state.period
    entity_scope = state.entity

    # Load data via canonical loader (already filters by period/entity)
    df = load_bank_transactions(Path(state.data_path), period, entity_scope)
    # Resolve the underlying CSV path for evidence logging
    fp = (Path(state.data_path) / "subledgers" / "bank_statements")
    # Pick the most likely filename used by loader for artifact provenance
    # This mirrors the search order in static_loader._find_bank_file
    for cand in [
        fp / f"bank_transactions_{period}.csv",
        fp / f"bank_transactions_{period.replace('-', '_')}.csv",
        fp / "bank_transactions_aug.csv",
    ]:
        if cand.exists():
            fp = cand
            break

    msgs: List[str] = []

    if df.empty:
        msgs.append("[DET] Bank reconciliation: no transactions in scope; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Bank reconciliation (skipped)"))
        return state

    # Duplicate detection signature
    # Use amount_usd for consistent comparison across entities
    if "amount_usd" in df.columns:
        df["amount"] = df["amount_usd"]
    elif "amount_local" in df.columns:
        df["amount"] = df["amount_local"]
    
    sig_cols = [
        "entity",
        "date",
        "amount",
        "currency",
        "counterparty",
        "transaction_type",
    ]

    grp = df.groupby(sig_cols, dropna=False, as_index=False)

    exceptions: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []

    # For each group with size > 1, mark all but the first as potential duplicates
    for key, idx in grp.indices.items():
        # key is a tuple aligning to sig_cols order
        if len(idx) > 1:
            # Stable order by bank_txn_id to ensure deterministic selection of primary
            rows = df.loc[list(idx)].sort_values("bank_txn_id")
            # First is primary reference; others flagged as duplicate candidates
            primary = rows.iloc[0]
            for _, r in rows.iloc[1:].iterrows():
                exc = {
                    "entity": r["entity"],
                    "bank_txn_id": r["bank_txn_id"],
                    "date": r["date"],
                    "amount": float(r["amount"]),
                    "currency": r["currency"],
                    "counterparty": r["counterparty"],
                    "transaction_type": r["transaction_type"],
                    "description": r.get("description"),
                    "reason": "duplicate_candidate",
                    "duplicate_signature": {k: v for k, v in zip(sig_cols, key if isinstance(key, Tuple) else (key,))},
                    "primary_bank_txn_id": primary["bank_txn_id"],
                    "classification": "error_duplicate",
                    "ai_rationale": (
                        f"[DET] Bank duplicate candidate: entity {r['entity']}, txn {r['bank_txn_id']} matches signature with primary {primary['bank_txn_id']} on same date. "
                        f"Classify=error_duplicate. Cites entity, date={r['date']}, amount={float(r['amount']):.2f} {r['currency']}, counterparty={r['counterparty']}, type={r['transaction_type']}."
                    ),
                }
                exceptions.append(exc)
                input_row_ids.append(str(r["bank_txn_id"]))

    # Timing-difference heuristic: same signature excluding date, within window days
    timing_window_days = 3
    sig_no_date = [c for c in sig_cols if c != "date"]
    grp2 = df.groupby(sig_no_date, dropna=False, as_index=False)
    for key2, idx2 in grp2.indices.items():
        if len(idx2) < 2:
            continue
        rows = df.loc[list(idx2)].sort_values(["entity", "amount", "currency", "counterparty", "transaction_type", "date", "bank_txn_id"]).reset_index(drop=True)
        # pair successive rows by date proximity deterministically
        dates = pd.to_datetime(rows["date"], errors="coerce")
        for i in range(1, len(rows)):
            r_prev = rows.iloc[i - 1]
            r_curr = rows.iloc[i]
            d_prev = dates.iloc[i - 1]
            d_curr = dates.iloc[i]
            if pd.isna(d_prev) or pd.isna(d_curr):
                continue
            day_diff = int(abs((d_curr - d_prev).days))
            if 0 < day_diff <= timing_window_days:
                # Flag the later transaction as timing candidate referencing the earlier one
                exc = {
                    "entity": r_curr["entity"],
                    "bank_txn_id": r_curr["bank_txn_id"],
                    "date": r_curr["date"],
                    "amount": float(r_curr["amount"]),
                    "currency": r_curr["currency"],
                    "counterparty": r_curr["counterparty"],
                    "transaction_type": r_curr["transaction_type"],
                    "description": r_curr.get("description"),
                    "reason": "timing_candidate",
                    "matched_bank_txn_id": r_prev["bank_txn_id"],
                    "day_diff": day_diff,
                    "classification": "timing_difference",
                    "ai_rationale": (
                        f"[DET] Bank timing candidate: entity {r_curr['entity']}, txn {r_curr['bank_txn_id']} matches amount/counterparty/type with txn {r_prev['bank_txn_id']} within {day_diff} days. "
                        f"Classify=timing_difference. Cites dates {r_prev['date']} -> {r_curr['date']}, amount={float(r_curr['amount']):.2f} {r_curr['currency']}, counterparty={r_curr['counterparty']}."
                    ),
                }
                exceptions.append(exc)
                input_row_ids.append(str(r_curr["bank_txn_id"]))

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"bank_reconciliation_{run_id}.json"

    total_abs = float(sum(abs(e.get("amount", 0.0)) for e in exceptions))
    by_ent: Dict[str, float] = {}
    for e in exceptions:
        ent = str(e.get("entity"))
        by_ent[ent] = by_ent.get(ent, 0.0) + abs(float(e.get("amount", 0.0)))

    payload = {
        "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "period": period,
        "entity_scope": entity_scope,
        "rules": {
            "duplicate_signature": sig_cols,
            "timing_window_days": timing_window_days,
        },
        "exceptions": exceptions,
        "summary": {
            "count": len(exceptions),
            "total_abs_amount": float(round(total_abs, 2)),
            "by_entity_abs_amount": {k: float(round(v, 2)) for k, v in by_ent.items()},
        },
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence + deterministic run
    ev = EvidenceRef(type="csv", uri=str(fp), input_row_ids=input_row_ids or None)
    state.evidence.append(ev)

    det = DeterministicRun(function_name="bank_reconciliation")
    det.params = {"period": period, "entity": entity_scope}
    det.output_hash = _hash_df(df)
    state.det_runs.append(det)

    audit.append(
        {
            "type": "evidence",
            "id": ev.id,
            "evidence_type": ev.type,
            "uri": ev.uri,
            "input_row_ids": ev.input_row_ids,
            "timestamp": ev.timestamp.isoformat() + "Z",
        }
    )
    audit.append(
        {
            "type": "deterministic",
            "fn": det.function_name,
            "evidence_id": ev.id,
            "output_hash": det.output_hash,
            "params": det.params,
            "artifact": str(out_path),
        }
    )

    # Messages, tags, metrics
    if exceptions:
        msgs.append(
            f"[DET] Bank recon duplicates: {len(exceptions)} items, total_abs={payload['summary']['total_abs_amount']:.2f} -> {out_path}"
        )
    else:
        msgs.append("[DET] Bank recon: no duplicate candidates for period")

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Bank reconciliation (duplicates)"))

    state.metrics.update(
        {
            "bank_duplicates_count": len(exceptions),
            "bank_duplicates_total_abs": payload["summary"]["total_abs_amount"],
            "bank_duplicates_by_entity": payload["summary"]["by_entity_abs_amount"],
            "bank_reconciliation_artifact": str(out_path),
        }
    )

    return state
