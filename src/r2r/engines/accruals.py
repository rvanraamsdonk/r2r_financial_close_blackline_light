from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Dict, Any, List

import pandas as pd
from ..utils.strings import safe_str as _shared_safe_str

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def _next_period(period: str) -> str:
    """Increment YYYY-MM -> next month as YYYY-MM."""
    y, m = map(int, period.split("-"))
    if m == 12:
        return f"{y+1}-01"
    return f"{y}-{m+1:02d}"


def _safe_str(val: Any) -> str:
    """Compatibility wrapper delegating to shared util `safe_str`."""
    return _shared_safe_str(val)

def accruals_check(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic accruals check:
    - Load supporting/accruals.csv
    - Filter to current period accrual_date
    - Flag rows that explicitly require reversal (status == 'Should Reverse')
    - Flag rows missing or misaligned reversal_date for the next period
    - Export exceptions artifact and append audit/evidence
    """
    # Try enhanced accruals first
    candidates = [
        Path(state.data_path) / "supporting" / "accruals_enhanced.csv",
        Path(state.data_path) / "supporting" / "accruals.csv",
    ]
    data_fp = None
    for c in candidates:
        if c.exists():
            data_fp = c
            break
    if data_fp is None:
        data_fp = Path(state.data_path) / "supporting" / "accruals.csv"  # fallback
    msgs: List[str] = []

    if not data_fp.exists():
        msgs.append("[DET] Accruals: no supporting data found; skipping checks")
        state.messages.extend(msgs)
        state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Accruals checks (skipped)"))
        return state

    df = pd.read_csv(
        data_fp,
        dtype={
            "entity": str,
            "accrual_id": str,
            "description": str,
            "amount_local": float,
            "amount_usd": float,
            "currency": str,
            "status": str,
            "accrual_date": str,
            "reversal_date": str,
            "notes": str,
        },
    )

    period = state.period
    next_p = _next_period(period)

    # Filter to current period accruals
    df_p = df[df["accrual_date"].astype(str).str.startswith(period)].copy()

    exceptions: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []

    for _, r in df_p.iterrows():
        status = _safe_str(r.get("status"))
        rev = _safe_str(r.get("reversal_date"))
        reason = None
        if status == "Should Reverse":
            reason = "explicit_should_reverse"
        elif status in ("Active", "Should Reverse"):
            # Expect reversal in next period
            if not rev or not str(rev).startswith(next_p):
                reason = "missing_or_misaligned_reversal_date"
        if reason:
            exceptions.append(
                {
                    "entity": r["entity"],
                    "accrual_id": r["accrual_id"],
                    "description": r["description"],
                    "amount": float(r["amount_usd"]),  # Add required amount field
                    "amount_usd": float(r["amount_usd"]),
                    "currency": r["currency"],
                    "status": status,
                    "accrual_date": r["accrual_date"],
                    "reversal_date": rev,
                    "reason": reason,
                    "notes": r.get("notes"),
                }
            )
            # Row-level provenance for exceptions
            input_row_ids.append(f"{r['entity']}|{r['accrual_id']}")

    # Build proposals for reversals: for missing/misaligned or explicit reverse
    proposals: List[Dict[str, Any]] = []
    for _, r in df_p.iterrows():
        status = _safe_str(r.get("status"))
        rev = _safe_str(r.get("reversal_date"))
        needs_rev = status == "Should Reverse" or (status in ("Active", "Should Reverse") and (not rev or not str(rev).startswith(next_p)))
        if needs_rev:
            amt = float(-float(r["amount_usd"]))
            proposals.append(
                {
                    "proposal_type": "accrual_reversal",
                    "entity": r["entity"],
                    "accrual_id": r["accrual_id"],
                    "proposed_period": next_p,
                    "amount_usd": float(amt),
                    "narrative": f"Propose reversal of accrual {r['accrual_id']} in {next_p}",
                    "deterministic_narrative": (
                        f"[DET] Reverse {r['accrual_id']} for entity {r['entity']} in {next_p}: "
                        f"amount_usd={amt:.2f}. Cites entity, accrual_id, proposed_period, amount."
                    ),
                }
            )

    # Build artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"accruals_{run_id}.json"
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "period": period,
        "entity_scope": state.entity,
        "next_period": next_p,
        "exceptions": exceptions,
        "proposals": proposals,
        "summary": {
            "count": len(exceptions),
            "total_usd": float(sum(e.get("amount_usd", 0.0) for e in exceptions)),
            "by_entity": {},
            "proposal_count": len(proposals),
            # roll-forward (next period impact) derived from proposals
            "roll_forward": {
                "next_period": next_p,
                "proposed_reversals_total_usd": float(round(sum(p.get("amount_usd", 0.0) for p in proposals), 2)),
                "proposed_reversals_by_entity": {},
            },
        },
    }
    # by_entity aggregation
    by_ent: Dict[str, float] = {}
    for e in exceptions:
        by_ent[e["entity"]] = by_ent.get(e["entity"], 0.0) + e.get("amount_usd", 0.0)
    payload["summary"]["by_entity"] = {k: float(round(v, 2)) for k, v in by_ent.items()}

    # fill roll_forward by_entity from proposals
    rf_by_ent: Dict[str, float] = {}
    for p in proposals:
        ent = str(p.get("entity"))
        rf_by_ent[ent] = rf_by_ent.get(ent, 0.0) + float(p.get("amount_usd", 0.0))
    payload["summary"]["roll_forward"]["proposed_reversals_by_entity"] = {
        k: float(round(v, 2)) for k, v in rf_by_ent.items()
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    # Evidence and deterministic run logging
    ev = EvidenceRef(type="csv", uri=str(data_fp), input_row_ids=input_row_ids or None)
    state.evidence.append(ev)

    det = DeterministicRun(function_name="accruals_check")
    det.params = {"period": period, "entity": state.entity}
    det.output_hash = _hash_df(df_p)
    state.det_runs.append(det)

    # Persist evidence with row-level provenance into audit log
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

    # Messages + metrics
    if exceptions:
        msgs.append(
            f"[DET] Accruals exceptions: {len(exceptions)} items, total_usd={payload['summary']['total_usd']:.2f}, proposals={len(proposals)} (roll_fwd_total={payload['summary']['roll_forward']['proposed_reversals_total_usd']:.2f}) -> {out_path}"
        )
    else:
        msgs.append("[DET] Accruals: no exceptions for period")

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Accruals checks"))

    # Update metrics inline for export
    state.metrics.update(
        {
            "accruals_exception_count": len(exceptions),
            "accruals_exception_total_usd": float(round(payload["summary"]["total_usd"], 2)),
            "accruals_exception_by_entity": payload["summary"]["by_entity"],
            "accruals_artifact": str(out_path),
        }
    )

    return state
