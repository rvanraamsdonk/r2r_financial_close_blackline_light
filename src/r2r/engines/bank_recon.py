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
                    "deterministic_rationale": (
                        f"[DET] Bank duplicate candidate: entity {r['entity']}, txn {r['bank_txn_id']} matches signature with primary {primary['bank_txn_id']} on same date. "
                        f"Classify=error_duplicate. Cites entity, date={r['date']}, amount={float(r['amount']):.2f} {r['currency']}, counterparty={r['counterparty']}, type={r['transaction_type']}."
                    ),
                }
                exceptions.append(exc)
                input_row_ids.append(str(r["bank_txn_id"]))

    # Forensic Pattern Detection
    def _norm_name(name):
        if pd.isna(name) or name is None:
            return ""
        return str(name).strip().lower()
    
    def _parse_date(date_str):
        if pd.isna(date_str) or date_str is None:
            return None
        try:
            return pd.to_datetime(date_str)
        except:
            return None
    
    # 1. Unusual Counterparty Detection (Cash Advance keywords + >$25K)
    suspicious_keywords = ["cash advance", "quick loan", "payday", "immediate funding", "rapid cash"]
    for _, r in df.iterrows():
        counterparty = _norm_name(r.get("counterparty", ""))
        amount = abs(float(r.get("amount", 0.0)))
        if amount > 25000 and any(keyword in counterparty for keyword in suspicious_keywords):
            exc = {
                "entity": r["entity"],
                "bank_txn_id": r["bank_txn_id"],
                "date": r["date"],
                "amount": float(r["amount"]),
                "currency": r["currency"],
                "counterparty": r["counterparty"],
                "transaction_type": r["transaction_type"],
                "description": r.get("description"),
                "reason": "unusual_counterparty",
                "classification": "forensic_risk",
                "deterministic_rationale": f"[FORENSIC] Unusual counterparty: Large transaction (${amount:.2f}) with suspicious entity '{r['counterparty']}' containing cash advance keywords",
            }
            exceptions.append(exc)
            input_row_ids.append(str(r["bank_txn_id"]))
    
    # 2. Velocity Anomaly Detection (Multiple transactions same counterparty same day)
    velocity_groups = df.groupby(["entity", "counterparty", "date"], dropna=False)
    for (entity, counterparty, date), group in velocity_groups:
        if len(group) >= 3:  # 3+ transactions same counterparty same day
            total_amount = group["amount"].abs().sum()
            for _, r in group.iterrows():
                exc = {
                    "entity": r["entity"],
                    "bank_txn_id": r["bank_txn_id"],
                    "date": r["date"],
                    "amount": float(r["amount"]),
                    "currency": r["currency"],
                    "counterparty": r["counterparty"],
                    "transaction_type": r["transaction_type"],
                    "description": r.get("description"),
                    "reason": "velocity_anomaly",
                    "classification": "forensic_risk",
                    "velocity_count": len(group),
                    "velocity_total": float(total_amount),
                    "deterministic_rationale": f"[FORENSIC] Velocity anomaly: {len(group)} transactions with '{counterparty}' on {date}, total ${total_amount:.2f}",
                }
                exceptions.append(exc)
                input_row_ids.append(str(r["bank_txn_id"]))
    
    # 3. Kiting Detection (Round-trip transfers with suspicious timing)
    transfer_out = df[df["transaction_type"] == "Transfer Out"].copy()
    transfer_in = df[df["transaction_type"] == "Transfer In"].copy()
    
    for _, out_txn in transfer_out.iterrows():
        out_amount = abs(float(out_txn.get("amount", 0.0)))
        out_date = _parse_date(out_txn.get("date"))
        if not out_date:
            continue
            
        # Look for matching transfer in within 3 days with similar amount
        for _, in_txn in transfer_in.iterrows():
            in_amount = abs(float(in_txn.get("amount", 0.0)))
            in_date = _parse_date(in_txn.get("date"))
            if not in_date:
                continue
                
            # Check if amounts are similar (within 5%) and dates are close (1-3 days)
            amount_diff_pct = abs(out_amount - in_amount) / max(out_amount, in_amount) if max(out_amount, in_amount) > 0 else 0
            day_diff = abs((in_date - out_date).days)
            
            if amount_diff_pct <= 0.05 and 1 <= day_diff <= 3 and out_amount > 10000:  # >$10K threshold
                exc = {
                    "entity": out_txn["entity"],
                    "bank_txn_id": out_txn["bank_txn_id"],
                    "date": out_txn["date"],
                    "amount": float(out_txn["amount"]),
                    "currency": out_txn["currency"],
                    "counterparty": out_txn["counterparty"],
                    "transaction_type": out_txn["transaction_type"],
                    "description": out_txn.get("description"),
                    "reason": "kiting_pattern",
                    "classification": "forensic_risk",
                    "matched_bank_txn_id": in_txn["bank_txn_id"],
                    "matched_amount": float(in_txn["amount"]),
                    "matched_date": in_txn["date"],
                    "day_diff": day_diff,
                    "deterministic_rationale": f"[FORENSIC] Potential kiting: Transfer out ${out_amount:.2f} on {out_txn['date']} followed by transfer in ${in_amount:.2f} on {in_txn['date']} ({day_diff} days later)",
                }
                exceptions.append(exc)
                input_row_ids.append(str(out_txn["bank_txn_id"]))
                break  # Only flag once per out transaction
    
    # 4. Timing-difference heuristic: same signature excluding date, within window days
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
                    "deterministic_rationale": (
                        f"[DET] Bank timing candidate: entity {r_curr['entity']}, txn {r_curr['bank_txn_id']} matches amount/counterparty/type with txn {r_prev['bank_txn_id']} within {day_diff} days. "
                        f"Classify=timing_difference. Cites dates {r_prev['date']} -> {r_curr['date']}, amount={float(r_curr['amount']):.2f} {r_curr['currency']}, counterparty={r_curr['counterparty']}."
                    ),
                }
                exceptions.append(exc)
                input_row_ids.append(str(r_curr["bank_txn_id"]))

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"bank_reconciliation_{run_id}.json"

    # AI-first confidence scoring and auto-approval policy (align with gatekeeping)
    MATERIALITY_THRESHOLD = 50000  # $50K

    def _score_exception(e: Dict[str, Any]) -> tuple[float, bool, str]:
        reason = e.get("reason")
        amount = abs(float(e.get("amount", 0.0)))
        cls = e.get("classification")
        # Defaults
        conf = 0.5
        auto = False
        note = ""
        if cls == "error_duplicate" or reason == "duplicate_candidate":
            conf = 0.95
            auto = amount <= MATERIALITY_THRESHOLD
            note = (
                "Duplicate candidate reliably detected; within materiality auto-approve."
                if auto
                else "Duplicate candidate detected; over materiality -> manual review."
            )
        elif cls == "timing_difference" or reason == "timing_candidate":
            conf = 0.85
            auto = amount <= MATERIALITY_THRESHOLD
            note = (
                "Timing difference likely benign; within materiality auto-approve."
                if auto
                else "Timing difference over materiality -> manual review."
            )
        elif cls == "forensic_risk":
            conf = 0.40
            auto = False
            note = "Forensic risk pattern -> require analyst review."
        else:
            conf = 0.60
            auto = amount <= MATERIALITY_THRESHOLD
            note = "Unclassified exception; conservative policy."
        return conf, auto, note

    auto_approved_count = 0
    auto_approved_total_abs = 0.0
    for e in exceptions:
        conf, auto, note = _score_exception(e)
        # Removed fake confidence score
        e["auto_approve"] = auto
        prior = e.get("deterministic_rationale")
        suffix = f" Policy: {note} Materiality threshold=${MATERIALITY_THRESHOLD:,.0f}."
        e["deterministic_rationale"] = (prior + " " + suffix).strip() if prior else suffix.strip()
        if auto:
            auto_approved_count += 1
            auto_approved_total_abs += abs(float(e.get("amount", 0.0)))

    total_abs = float(sum(abs(e.get("amount", 0.0)) for e in exceptions))
    by_ent: Dict[str, float] = {}
    for e in exceptions:
        ent = str(e.get("entity"))
        by_ent[ent] = by_ent.get(ent, 0.0) + abs(float(e.get("amount", 0.0)))

    # Summary AI rationale
    high_risk_count = sum(1 for e in exceptions if e.get("classification") == "forensic_risk")
    if high_risk_count == 0 and total_abs <= MATERIALITY_THRESHOLD:
        summary_conf = 0.90
        summary_rationale = (
            f"Bank recon exceptions are immaterial in aggregate (${total_abs:,.0f} <= ${MATERIALITY_THRESHOLD:,.0f}) with no forensic-risk flags. "
            f"Auto-approvals applied to {auto_approved_count} items totaling ${auto_approved_total_abs:,.0f}."
        )
    elif high_risk_count == 0:
        summary_conf = 0.80
        summary_rationale = (
            f"No forensic-risk flags detected. Aggregate impact ${total_abs:,.0f} exceeds materiality; timing/duplicates require sampling review."
        )
    else:
        summary_conf = 0.60
        summary_rationale = (
            f"Detected {high_risk_count} forensic-risk pattern(s); route to analyst. Duplicates/timing auto-approvals limited to immaterial items only."
        )

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
            "materiality_threshold": MATERIALITY_THRESHOLD,
            "auto_approved_count": auto_approved_count,
            "auto_approved_total_abs": float(round(auto_approved_total_abs, 2)),
            "deterministic_rationale": summary_rationale,
            # Removed fake confidence score
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
            f"[DET] Bank recon: {len(exceptions)} items, total_abs={payload['summary']['total_abs_amount']:.2f}, auto_approved={auto_approved_count} -> {out_path}"
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
            # Removed fake confidence score
            "bank_deterministic_rationale": payload["summary"].get("deterministic_rationale"),
            "bank_auto_approved_count": auto_approved_count,
            "bank_auto_approved_total_abs": float(round(auto_approved_total_abs, 2)),
        }
    )

    return state
