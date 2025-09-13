from __future__ import annotations

import json
from .. import utils
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from ..audit.log import AuditLogger
from ..schemas import DeterministicRun, EvidenceRef, MethodType, OutputTag
from ..state import R2RState
from ..data.static_loader import load_intercompany


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _find_ic_file(data_path: Path, period: str) -> Path:
    # Not used by loader directly; retained for provenance URI resolution
    base = Path(data_path) / "subledgers" / "intercompany"
    candidates = [
        base / f"ic_transactions_{period}.csv",
        base / f"ic_transactions_{period.replace('-', '_')}.csv",
        base / "ic_transactions_aug.csv",
    ]
    for c in candidates:
        if c.exists():
            return c
    raise FileNotFoundError(f"No intercompany file found for period {period} in {base}")


def intercompany_reconciliation(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic intercompany reconciliation (mismatch detection):
    - Load intercompany transactions for period
    - Compute absolute difference |amount_src - amount_dst|
    - Flag exceptions where difference exceeds materiality threshold
      threshold = max(materiality[src], materiality[dst]) if available, else $1,000
    - Emit artifact and provenance; update messages, tags, metrics
    """
    period = state.period
    # Load via canonical loader (filters by period only; entities optional)
    df = load_intercompany(Path(state.data_path), period)
    # Resolve CSV URI for evidence
    fp = _find_ic_file(Path(state.data_path), period)

    msgs: List[str] = []

    if df.empty:
        msgs.append("[DET] Intercompany: no transactions in scope; skipping")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Intercompany reconciliation (skipped)"))
        return state

    # Materiality thresholds by entity
    materiality_map: Dict[str, float] = {}
    if isinstance(state.metrics.get("materiality_thresholds_usd"), dict):
        for k, v in state.metrics["materiality_thresholds_usd"].items():
            try:
                materiality_map[str(k)] = float(v)
            except Exception:
                continue

    def pair_threshold(src: str, dst: str) -> float:
        # Default floor if not available
        thr_src = materiality_map.get(str(src), 1000.0)
        thr_dst = materiality_map.get(str(dst), 1000.0)
        return float(max(thr_src, thr_dst))

    exceptions: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []
    # AI governance accumulators (Master Plan Coverage Analysis: Phase 4–7 Immediate Priority)
    weighted_conf_sum = 0.0
    amount_sum_abs = 0.0
    auto_approved_count = 0
    auto_approved_total_abs = 0.0

    for _, r in df.iterrows():
        src = str(r["entity_src"])  # e.g., ENT100
        dst = str(r["entity_dst"])  # e.g., ENT101
        diff = abs(float(r["amount_src"]) - float(r["amount_dst"]))
        thr = pair_threshold(src, dst)
        amount_src = float(r["amount_src"])
        amount_dst = float(r["amount_dst"])
        doc_id = str(r["doc_id"])
        transaction_type = str(r.get("transaction_type", ""))
        description = str(r.get("description", ""))
        
        reason = None
        
        # Standard mismatch detection
        if diff > thr:
            reason = "ic_amount_mismatch_above_threshold"
        
        # Forensic Pattern Detection for Intercompany
        if not reason:
            # 1. Round Dollar Anomaly Detection
            if amount_src % 1000 == 0 and amount_src >= 10000:
                reason = "ic_round_dollar_anomaly"
            
            # 2. Unusual Transaction Type Patterns
            elif "management fee" in transaction_type.lower() and amount_src > 50000:
                # Large management fees could indicate transfer pricing manipulation
                reason = "ic_transfer_pricing_risk"
            
            # 3. Frequent Small Transactions (potential structuring)
            elif amount_src < 10000:
                # Count similar small transactions from same entity pair on same day
                same_day_small = df[
                    (df["entity_src"] == src) & 
                    (df["entity_dst"] == dst) & 
                    (df["date"] == r["date"]) & 
                    (df["amount_src"] < 10000)
                ]
                if len(same_day_small) >= 3:
                    reason = "ic_structuring_pattern"
        
        if reason:
            exception_data = {
                "doc_id": doc_id,
                "entity": src,  # Add required entity field
                "entity_src": src,
                "entity_dst": dst,
                "amount": float(round(amount_src, 2)),  # Use actual transaction amount, not diff
                "amount_src": amount_src,
                "amount_dst": amount_dst,
                "diff_abs": float(round(diff, 2)),
                "threshold": float(round(thr, 2)),
                "reason": reason,
            }
            
            # Enhanced rationale for forensic patterns
            if reason == "ic_amount_mismatch_above_threshold":
                exception_data["deterministic_rationale"] = f"[DET] IC doc {doc_id} {src}->{dst}: diff={diff:.2f} USD exceeds threshold {thr:.2f}. Cites doc_id, entities, and computed threshold."
            elif reason == "ic_round_dollar_anomaly":
                exception_data["deterministic_rationale"] = f"[FORENSIC] Round dollar anomaly: IC transaction {doc_id} for exactly ${amount_src:,.0f} between {src} and {dst} suggests potential manipulation"
            elif reason == "ic_transfer_pricing_risk":
                exception_data["deterministic_rationale"] = f"[FORENSIC] Transfer pricing risk: Large management fee ${amount_src:,.2f} from {src} to {dst} may indicate profit shifting"
            elif reason == "ic_structuring_pattern":
                exception_data["deterministic_rationale"] = f"[FORENSIC] Structuring pattern: Multiple small transactions from {src} to {dst} on same day may indicate avoidance of controls"
            
            # AI confidence scoring and auto-approval (conservative for Intercompany)
            # Choose materiality basis
            if reason == "ic_amount_mismatch_above_threshold":
                amt_abs = float(exception_data.get("diff_abs", 0.0))
                # Base confidence for deterministic mismatch above threshold
                base_conf = 0.85
                # Materiality factor relative to pair threshold
                mat_factor = 0.85 if amt_abs >= thr else 1.0
            else:
                # For forensic patterns, use transaction magnitude vs global materiality
                GLOBAL_MATERIALITY = 50000.0
                amt_abs = abs(float(exception_data.get("amount", 0.0)))
                if reason == "ic_round_dollar_anomaly":
                    base_conf = 0.80
                elif reason == "ic_transfer_pricing_risk":
                    base_conf = 0.72
                elif reason == "ic_structuring_pattern":
                    base_conf = 0.76
                else:
                    base_conf = 0.7
                mat_factor = 1.0 if amt_abs < GLOBAL_MATERIALITY else 0.85

            # Removed fake confidence score - deterministic logic doesn't need confidence
            auto_approve = False  # Policy: no auto-approvals for IC exceptions at this stage

            # Removed fake confidence score
            exception_data["auto_approve"] = auto_approve

            # Accumulate AI governance metrics
            # Removed fake confidence tracking
            amount_sum_abs += amt_abs
            if auto_approve:
                auto_approved_count += 1
                auto_approved_total_abs += amt_abs

            exceptions.append(exception_data)
            input_row_ids.append(doc_id)

    # Build simple candidate hints per exception: other exceptions in same pair/currency with closest diff_abs
    if exceptions:
        # Precompute by pair+currency for deterministic filtering
        buckets: Dict[str, List[Dict[str, Any]]] = {}
        for e in exceptions:
            key = f"{e['entity_src']}->{e['entity_dst']}|{e.get('currency')}"
            buckets.setdefault(key, []).append(e)

        for e in exceptions:
            key = f"{e['entity_src']}->{e['entity_dst']}|{e.get('currency')}"
            peers = [p for p in buckets.get(key, []) if p is not e]
            base = float(e.get("diff_abs", 0.0))
            cands: List[Dict[str, Any]] = []
            for p in peers:
                dv = float(p.get("diff_abs", 0.0))
                denom = base + dv + 1e-6
                score = max(0.0, 1.0 - abs(base - dv) / denom)
                cands.append(
                    {
                        "doc_id": p["doc_id"],
                        "entity_src": p["entity_src"],
                        "entity_dst": p["entity_dst"],
                        "diff_abs": float(round(dv, 2)),
                        "det_score": float(round(score, 4)),
                    }
                )
            # Deterministic sort: by score desc, then doc_id asc
            cands.sort(key=lambda x: (-x["det_score"], str(x["doc_id"])) )
            e["candidates"] = cands[:3]
            e["assistive_hint"] = True
            e["det_candidate_summary"] = (
                f"[DET] {e['entity_src']}->{e['entity_dst']} doc {e['doc_id']}: {len(e['candidates'])} assistive candidate hint(s) by diff magnitude in {e.get('currency')}; no match claim."
            )

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"intercompany_reconciliation_{run_id}.json"

    total_diff = float(sum(e.get("diff_abs", 0.0) for e in exceptions))

    by_pair: Dict[str, float] = {}
    for e in exceptions:
        key = f"{e['entity_src']}->{e['entity_dst']}"
        by_pair[key] = by_pair.get(key, 0.0) + e.get("diff_abs", 0.0)

    # Build simple true-up proposals for each exception: adjust dst to match src
    proposals: List[Dict[str, Any]] = []
    for e in exceptions:
        amt_src = float(e["amount_src"])  # positive means debit on src in this simplified model
        amt_dst = float(e["amount_dst"])  # should match src
        adj = round(amt_src - amt_dst, 2)
        if adj == 0.0:
            continue
        simulated_after = round(amt_dst + adj, 2)
        proposals.append(
            {
                "proposal_type": "ic_true_up",
                "doc_id": e["doc_id"],
                "entity_src": e["entity_src"],
                "entity_dst": e["entity_dst"],
                "adjustment_usd": float(adj),
                "simulated_dst_after": float(simulated_after),
                "balanced_after": bool(abs(simulated_after - amt_src) < 1e-6),
                "narrative": f"Adjust destination entity to match source (delta {adj:+.2f} USD)",
            }
        )

    # Summary AI confidence and rationale
    # Removed fake confidence score calculation
    if exceptions:
        ic_deterministic_rationale = (
            f"IC AI assessment: {len(exceptions)} exceptions across pairs; auto-approval disabled for intercompany at this stage. "
            f"Pair thresholds enforced; forensic patterns flagged for review."
        )
    else:
        ic_deterministic_rationale = "IC AI assessment: no exceptions."

    payload = {
        "generated_at": utils.now_iso_z(),
        "period": period,
        "rules": {
            "mismatch_rule": "flag |amount_src-amount_dst| > max(materiality[src], materiality[dst])",
            "default_floor_usd": 1000.0,
        },
        "exceptions": exceptions,
        "proposals": proposals,
        "summary": {
            "count": len(exceptions),
            "total_diff_abs": float(round(total_diff, 2)),
            "by_pair_diff_abs": {k: float(round(v, 2)) for k, v in by_pair.items()},
            "proposal_count": len(proposals),
            # Removed fake confidence score
            "deterministic_rationale": ic_deterministic_rationale,
            "auto_approved_count": auto_approved_count,
            "auto_approved_total_abs": float(round(auto_approved_total_abs, 2)),
        },
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence and deterministic run
    ev = EvidenceRef(type="csv", uri=str(fp), input_row_ids=input_row_ids or None)
    state.evidence.append(ev)

    det = DeterministicRun(function_name="intercompany_reconciliation")
    det.params = {"period": period}
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
            f"[DET] Intercompany mismatches: {len(exceptions)} items, total_diff_abs={payload['summary']['total_diff_abs']:.2f}, proposals={len(proposals)} -> {out_path}"
        )
    else:
        msgs.append("[DET] Intercompany: no mismatches above materiality")

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Intercompany reconciliation (mismatches)"))

    state.metrics.update(
        {
            "ic_mismatch_count": len(exceptions),
            "ic_mismatch_total_diff_abs": payload["summary"]["total_diff_abs"],
            "ic_mismatch_by_pair": payload["summary"]["by_pair_diff_abs"],
            "intercompany_reconciliation_artifact": str(out_path),
            # Removed fake confidence score
            "ic_deterministic_rationale": ic_deterministic_rationale,
            "ic_auto_approved_count": auto_approved_count,
            "ic_auto_approved_total_abs": float(round(auto_approved_total_abs, 2)),
        }
    )

    return state
