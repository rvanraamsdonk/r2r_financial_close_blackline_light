from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
from ..utils.strings import safe_str as _shared_safe_str
from ..utils import now_iso_z

from ..audit.log import AuditLogger
from ..schemas import DeterministicRun, EvidenceRef, MethodType, OutputTag
from ..state import R2RState
from ..data.static_loader import load_ap_detail, load_ar_detail


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _safe_str(val: Any) -> str:
    """Compatibility wrapper delegating to shared util `safe_str`.

    Centralizes NaN-safe handling across engines while keeping the local name
    used by tests and existing code.
    """
    return _shared_safe_str(val)


def _resolve_ap_path(data_path: Path, period: str) -> Path:
    base = Path(data_path) / "subledgers"
    for cand in [
        base / f"ap_detail_{period}.csv",
        base / f"ap_detail_{period.replace('-', '_')}.csv",
        base / "ap_detail_aug.csv",
    ]:
        if cand.exists():
            return cand
    return base / f"ap_detail_{period}.csv"  # best-effort fallback


def _resolve_ar_path(data_path: Path, period: str) -> Path:
    base = Path(data_path) / "subledgers"
    for cand in [
        base / f"ar_detail_{period}.csv",
        base / f"ar_detail_{period.replace('-', '_')}.csv",
        base / "ar_detail_aug.csv",
    ]:
        if cand.exists():
            return cand
    return base / f"ar_detail_{period}.csv"  # best-effort fallback


def ap_reconciliation(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic AP reconciliation (aging & duplicate flags):
    - Load AP detail filtered by period/entity
    - Flag overdue (status == 'Overdue') or age_days > 60
    - Flag notes containing 'Duplicate'
    - Emit artifact, evidence with input_row_ids, deterministic run, and metrics
    """
    period = state.period
    entity_scope = state.entity

    df = load_ap_detail(Path(state.data_path), period, entity_scope)

    # Resolve file path for evidence
    fp = _resolve_ap_path(Path(state.data_path), period)

    msgs: List[str] = []
    if df.empty:
        msgs.append("[DET] AP recon: no AP bills in scope; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="AP reconciliation (skipped)"))
        return state

    exceptions: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []

    # Precompute simple deterministic duplicate candidates within AP
    def _norm_name(x: Any) -> str:
        s = _safe_str(x).lower().strip()
        return " ".join(s.split())

    def _parse_date(s: Any) -> pd.Timestamp | None:
        try:
            return pd.to_datetime(s, errors="coerce")
        except Exception:
            return None

    df["_norm_vendor"] = df["vendor_name"].map(_norm_name)
    df["_date"] = df["bill_date"].map(_parse_date)

    def _ap_candidates(row: pd.Series) -> List[Dict[str, Any]]:
        cand: List[Dict[str, Any]] = []
        amt0 = float(row.get("amount", 0.0))
        ent0 = _safe_str(row.get("entity"))
        name0 = _norm_name(row.get("vendor_name"))
        d0 = row.get("_date")
        for _, r2 in df.iterrows():
            if str(r2.get("bill_id")) == str(row.get("bill_id")):
                continue
            if _safe_str(r2.get("entity")) != ent0:
                continue
            if _norm_name(r2.get("vendor_name")) != name0:
                continue
            amt2 = float(r2.get("amount", 0.0))
            # amount similarity in [0,1]
            denom = max(abs(amt0), abs(amt2), 1.0)
            amt_sim = 1.0 - (abs(amt0 - amt2) / denom)
            # date proximity contribution
            d2 = r2.get("_date")
            if pd.notna(d0) and pd.notna(d2):
                days = abs((d0 - d2).days)
                date_sim = max(0.0, 1.0 - min(days, 30) / 30.0)  # within 30 days -> down to 0
            else:
                date_sim = 0.5
            score = round(0.7 * amt_sim + 0.3 * date_sim, 3)
            if score >= 0.6:
                cand.append(
                    {
                        "bill_id": r2.get("bill_id"),
                        "vendor_name": r2.get("vendor_name"),
                        "bill_date": r2.get("bill_date"),
                        "amount": float(amt2),
                        "score": float(score),
                    }
                )
        # sort and cap
        cand.sort(key=lambda x: x["score"], reverse=True)
        return cand[:3]

    for _, r in df.iterrows():
        status = _safe_str(r.get("status"))
        # age_days may be str/int; coerce safely
        try:
            age = int(r.get("age_days")) if pd.notna(r.get("age_days")) else 0
        except Exception:
            age = 0
        notes = _safe_str(r.get("notes"))
        amount = float(r.get("amount_usd", 0.0))
        vendor_name = _safe_str(r.get("vendor_name"))
        bill_date = _parse_date(r.get("bill_date"))
        
        reason: str | None = None
        
        # Original flags
        if status == "Overdue":
            reason = "overdue"
        elif age > 60:
            reason = "age_gt_60"
        elif "duplicate" in notes.lower():
            reason = "duplicate_flag"
        
        # Forensic Pattern Detection
        
        # 1. Duplicate Payment Detection (same vendor + similar amount + close dates)
        if not reason:
            for _, r2 in df.iterrows():
                if str(r2.get("bill_id")) == str(r.get("bill_id")):
                    continue
                if _norm_name(r2.get("vendor_name")) == _norm_name(vendor_name):
                    amt2 = float(r2.get("amount_usd", 0.0))
                    date2 = _parse_date(r2.get("bill_date"))
                    
                    # Similar amount (within $50)
                    if abs(amount - amt2) <= 50:
                        # Close dates (within 7 days)
                        if bill_date and date2 and abs((bill_date - date2).days) <= 7:
                            reason = "duplicate_payment_pattern"
                            break
        
        # 2. Round Dollar Anomaly Detection
        if not reason and amount > 0:
            # Check for suspiciously round amounts
            if amount >= 10000 and amount % 10000 == 0:  # $10K, $20K, etc.
                reason = "round_dollar_large"
            elif amount >= 1000 and amount % 1000 == 0:  # $1K, $2K, etc.
                reason = "round_dollar_medium"
            elif amount >= 500 and amount % 500 == 0:  # $500, $1000, etc.
                reason = "round_dollar_small"
        
        # 3. Suspicious New Vendor Detection
        if not reason:
            suspicious_keywords = ["quickpay", "rapid", "express", "swift", "immediate", 
                                 "fast track", "priority", "urgent"]
            vendor_lower = vendor_name.lower()
            if any(keyword in vendor_lower for keyword in suspicious_keywords):
                if amount > 25000:  # Large payment to suspicious vendor
                    reason = "suspicious_new_vendor"
        
        # 4. Weekend Entry Detection
        if not reason and bill_date:
            if bill_date.weekday() >= 5:  # Saturday (5) or Sunday (6)
                reason = "weekend_entry"
        
        # 5. Split Transaction Detection (same vendor, same day, multiple invoices)
        if not reason and bill_date:
            same_vendor_same_day = df[
                (df["vendor_name"].map(_norm_name) == _norm_name(vendor_name)) &
                (df["bill_date"].map(_parse_date).dt.date == bill_date.date()) &
                (df["bill_id"] != r.get("bill_id"))
            ]
            if len(same_vendor_same_day) >= 2:  # Multiple transactions same vendor/day
                reason = "split_transaction_pattern"
        if reason:
            e = {
                "subledger": "AP",
                "entity": r.get("entity"),
                "bill_id": r.get("bill_id"),
                "vendor_name": r.get("vendor_name"),
                "bill_date": r.get("bill_date"),
                "amount": float(r.get("amount_usd", 0.0)),
                "currency": r.get("currency"),
                "age_days": age,
                "status": status,
                "reason": reason,
                "notes": notes or None,
            }
            # Attach deterministic candidates and rationale
            cand = _ap_candidates(r) if reason in ("duplicate_flag", "overdue", "age_gt_60", "duplicate_payment_pattern") else []
            if cand:
                e["candidates"] = cand
            
            # Enhanced rationale for forensic patterns
            if reason == "duplicate_payment_pattern":
                e["ai_rationale"] = (
                    f"[FORENSIC] Potential duplicate payment detected: vendor={vendor_name}, "
                    f"amount=${amount:.2f}, similar transaction found within 7 days"
                )
            elif reason.startswith("round_dollar"):
                e["ai_rationale"] = (
                    f"[FORENSIC] Round dollar anomaly: amount=${amount:.2f} is suspiciously round"
                )
            elif reason == "suspicious_new_vendor":
                e["ai_rationale"] = (
                    f"[FORENSIC] Suspicious vendor pattern: {vendor_name} with large payment ${amount:.2f}"
                )
            elif reason == "weekend_entry":
                e["ai_rationale"] = (
                    f"[FORENSIC] Weekend entry: transaction dated {bill_date.strftime('%Y-%m-%d')} (%s)"
                    % bill_date.strftime('%A')
                )
            elif reason == "split_transaction_pattern":
                e["ai_rationale"] = (
                    f"[FORENSIC] Split transaction pattern: multiple payments to {vendor_name} on same day"
                )
            else:
                e["ai_rationale"] = (
                    f"[DET] AP {r.get('entity')} bill {r.get('bill_id')}: reason={reason}, "
                    f"amount={float(r.get('amount', 0.0)):.2f} {r.get('currency')}, age_days={age}. "
                    f"Candidates={len(cand)} (vendor={_safe_str(r.get('vendor_name'))})."
                )
            exceptions.append(e)
            input_row_ids.append(str(r.get("bill_id")))

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"ap_reconciliation_{run_id}.json"

    total_abs = float(sum(abs(e.get("amount", 0.0)) for e in exceptions))
    by_ent: Dict[str, float] = {}
    for e in exceptions:
        ent = str(e.get("entity"))
        by_ent[ent] = by_ent.get(ent, 0.0) + abs(float(e.get("amount", 0.0)))

    payload = {
        "generated_at": now_iso_z(),
        "period": period,
        "entity_scope": entity_scope,
        "rules": {
            "overdue_status": True,
            "age_days_threshold": 60,
            "duplicate_in_notes": True,
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

    det = DeterministicRun(function_name="ap_reconciliation")
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
            f"[DET] AP recon exceptions: {len(exceptions)} items, total_abs={payload['summary']['total_abs_amount']:.2f} -> {out_path}"
        )
    else:
        msgs.append("[DET] AP recon: no exceptions for period")

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="AP reconciliation"))

    state.metrics.update(
        {
            "ap_exceptions_count": len(exceptions),
            "ap_exceptions_total_abs": payload["summary"]["total_abs_amount"],
            "ap_exceptions_by_entity": payload["summary"]["by_entity_abs_amount"],
            "ap_reconciliation_artifact": str(out_path),
        }
    )

    return state


def ar_reconciliation(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic AR reconciliation (aging):
    - Load AR detail filtered by period/entity
    - Flag overdue (status == 'Overdue') or age_days > 60
    - Emit artifact, evidence with input_row_ids, deterministic run, and metrics
    """
    period = state.period
    entity_scope = state.entity

    df = load_ar_detail(Path(state.data_path), period, entity_scope)

    # Resolve file path for evidence
    fp = _resolve_ar_path(Path(state.data_path), period)

    msgs: List[str] = []
    if df.empty:
        msgs.append("[DET] AR recon: no AR invoices in scope; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="AR reconciliation (skipped)"))
        return state

    exceptions: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []
    # Precompute deterministic candidates within AR (near-duplicates)
    def _norm_cust(x: Any) -> str:
        s = _safe_str(x).lower().strip()
        return " ".join(s.split())

    def _parse_date_ar(s: Any) -> pd.Timestamp | None:
        try:
            return pd.to_datetime(s, errors="coerce")
        except Exception:
            return None

    df["_norm_customer"] = df["customer_name"].map(_norm_cust)
    df["_date"] = df["invoice_date"].map(_parse_date_ar)

    def _ar_candidates(row: pd.Series) -> List[Dict[str, Any]]:
        cand: List[Dict[str, Any]] = []
        amt0 = float(row.get("amount", 0.0))
        ent0 = _safe_str(row.get("entity"))
        name0 = _norm_cust(row.get("customer_name"))
        d0 = row.get("_date")
        for _, r2 in df.iterrows():
            if str(r2.get("invoice_id")) == str(row.get("invoice_id")):
                continue
            if _safe_str(r2.get("entity")) != ent0:
                continue
            if _norm_cust(r2.get("customer_name")) != name0:
                continue
            amt2 = float(r2.get("amount", 0.0))
            denom = max(abs(amt0), abs(amt2), 1.0)
            amt_sim = 1.0 - (abs(amt0 - amt2) / denom)
            d2 = r2.get("_date")
            if pd.notna(d0) and pd.notna(d2):
                days = abs((d0 - d2).days)
                date_sim = max(0.0, 1.0 - min(days, 30) / 30.0)
            else:
                date_sim = 0.5
            score = round(0.7 * amt_sim + 0.3 * date_sim, 3)
            if score >= 0.6:
                cand.append(
                    {
                        "invoice_id": r2.get("invoice_id"),
                        "customer_name": r2.get("customer_name"),
                        "invoice_date": r2.get("invoice_date"),
                        "amount": float(amt2),
                        "score": float(score),
                    }
                )
        cand.sort(key=lambda x: x["score"], reverse=True)
        return cand[:3]

    for _, r in df.iterrows():
        status = _safe_str(r.get("status"))
        try:
            age = int(r.get("age_days")) if pd.notna(r.get("age_days")) else 0
        except Exception:
            age = 0
        amount = float(r.get("amount_usd", 0.0))
        customer_name = _safe_str(r.get("customer_name"))
        invoice_date = _parse_date_ar(r.get("invoice_date"))
        payment_terms = _safe_str(r.get("payment_terms", ""))
        description = _safe_str(r.get("description", ""))
        
        reason: str | None = None
        
        # Original flags
        if status == "Overdue":
            reason = "overdue"
        elif age > 60:
            reason = "age_gt_60"
        
        # Forensic Pattern Detection
        
        # 1. Channel Stuffing Detection (large amounts at month end)
        if not reason and invoice_date and amount > 50000:
            # Check if invoice is in last 3 days of month
            try:
                # Get last day of the month
                if invoice_date.month == 12:
                    next_month = invoice_date.replace(year=invoice_date.year + 1, month=1, day=1)
                else:
                    next_month = invoice_date.replace(month=invoice_date.month + 1, day=1)
                month_end = next_month - pd.Timedelta(days=1)
                days_from_month_end = (month_end - invoice_date).days
                
                if days_from_month_end <= 3:
                    # Additional check for extended payment terms
                    if any(term in payment_terms.lower() for term in ["net 90", "net 120", "net 180"]):
                        reason = "channel_stuffing_pattern"
            except:
                pass
        
        # 2. Credit Memo Abuse Detection (negative amounts)
        if not reason and amount < 0:
            if abs(amount) > 5000:  # Significant credit amounts
                if "credit memo" in customer_name.lower():
                    reason = "credit_memo_abuse"
        
        # 3. Related Party Transaction Detection
        if not reason:
            related_party_keywords = ["subsidiary", "affiliate", "related entity", 
                                    "sister company", "associated business"]
            customer_lower = customer_name.lower()
            if any(keyword in customer_lower for keyword in related_party_keywords):
                if amount > 75000:  # Large amounts to related parties
                    reason = "related_party_transaction"
        
        # 4. Revenue Recognition Risk (unusual patterns)
        if not reason and invoice_date:
            # Check for unusual invoice timing patterns
            if invoice_date.weekday() >= 5:  # Weekend invoicing
                if amount > 25000:
                    reason = "weekend_revenue_recognition"
        if reason:
            e = {
                "subledger": "AR",
                "entity": r.get("entity"),
                "invoice_id": r.get("invoice_id"),
                "customer_name": r.get("customer_name"),
                "invoice_date": r.get("invoice_date"),
                "amount": float(r.get("amount_usd", 0.0)),
                "currency": r.get("currency"),
                "age_days": age,
                "status": status,
                "reason": reason,
            }
            cand = _ar_candidates(r) if reason in ("overdue", "age_gt_60") else []
            if cand:
                e["candidates"] = cand
            
            # Enhanced rationale for forensic patterns
            if reason == "channel_stuffing_pattern":
                e["ai_rationale"] = (
                    f"[FORENSIC] Channel stuffing detected: large invoice ${amount:.2f} "
                    f"to {customer_name} near month-end with extended terms ({payment_terms})"
                )
            elif reason == "credit_memo_abuse":
                e["ai_rationale"] = (
                    f"[FORENSIC] Credit memo abuse: significant credit ${abs(amount):.2f} "
                    f"to {customer_name}"
                )
            elif reason == "related_party_transaction":
                e["ai_rationale"] = (
                    f"[FORENSIC] Related party transaction: ${amount:.2f} "
                    f"to {customer_name} with unusual pricing"
                )
            elif reason == "weekend_revenue_recognition":
                e["ai_rationale"] = (
                    f"[FORENSIC] Weekend revenue recognition: ${amount:.2f} invoice "
                    f"dated {invoice_date.strftime('%Y-%m-%d')} ({invoice_date.strftime('%A')})"
                )
            else:
                e["ai_rationale"] = (
                    f"[DET] AR {r.get('entity')} invoice {r.get('invoice_id')}: reason={reason}, "
                    f"amount={float(r.get('amount', 0.0)):.2f} {r.get('currency')}, age_days={age}. "
                    f"Candidates={len(cand)} (customer={_safe_str(r.get('customer_name'))})."
                )
            exceptions.append(e)
            input_row_ids.append(str(r.get("invoice_id")))

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"ar_reconciliation_{run_id}.json"

    total_abs = float(sum(abs(e.get("amount", 0.0)) for e in exceptions))
    by_ent: Dict[str, float] = {}
    for e in exceptions:
        ent = str(e.get("entity"))
        by_ent[ent] = by_ent.get(ent, 0.0) + abs(float(e.get("amount", 0.0)))

    payload = {
        "generated_at": now_iso_z(),
        "period": period,
        "entity_scope": entity_scope,
        "rules": {
            "overdue_status": True,
            "age_days_threshold": 60,
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

    det = DeterministicRun(function_name="ar_reconciliation")
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
            f"[DET] AR recon exceptions: {len(exceptions)} items, total_abs={payload['summary']['total_abs_amount']:.2f} -> {out_path}"
        )
    else:
        msgs.append("[DET] AR recon: no exceptions for period")

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="AR reconciliation"))

    state.metrics.update(
        {
            "ar_exceptions_count": len(exceptions),
            "ar_exceptions_total_abs": payload["summary"]["total_abs_amount"],
            "ar_exceptions_by_entity": payload["summary"]["by_entity_abs_amount"],
            "ar_reconciliation_artifact": str(out_path),
        }
    )

    return state
