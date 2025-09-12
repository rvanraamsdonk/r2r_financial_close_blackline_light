from __future__ import annotations

import json
from .. import utils
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from ..audit.log import AuditLogger
from ..schemas import DeterministicRun, EvidenceRef, MethodType, OutputTag
from ..state import R2RState
from ..data.static_loader import load_budget, load_tb


def _hash_json(obj: Any) -> str:
    return sha256(json.dumps(obj, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def _derive_prior(period: str) -> str:
    # Expect YYYY-MM; simple month back logic without external deps
    yr, mo = period.split("-")
    y = int(yr)
    m = int(mo)
    if m > 1:
        return f"{y:04d}-{m-1:02d}"
    return f"{y-1:04d}-12"


def flux_analysis(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic Flux Analysis (Budget & Prior):
    - Aggregate TB actuals (USD) by entity/account for period scope
    - Join Budget (budget.csv) for the period and Prior TB for prior period
    - Compute variances vs Budget and Prior, with percent deltas
    - Flag exceptions where abs(variance) exceeds entity materiality threshold
    - Persist artifact; log evidence and deterministic run; update messages, tags, metrics
    """
    assert state.tb_df is not None, "tb_df missing"

    period = str(state.period)
    entity_scope = str(state.entity)
    prior = str(state.prior) if state.prior else _derive_prior(period)

    # Prepare Actuals (TB)
    tb = state.tb_df.copy()
    if entity_scope and entity_scope != "ALL":
        tb = tb[tb["entity"] == entity_scope]
    tb_grp = (
        tb.groupby(["entity", "account"], dropna=False)["balance_usd"].sum().reset_index(name="actual_usd")
        if not tb.empty
        else pd.DataFrame(columns=["entity", "account", "actual_usd"])
    )

    # Budget
    try:
        budget = load_budget(Path(state.data_path), period, entity_scope)
    except Exception:
        budget = pd.DataFrame(columns=["period", "entity", "account", "budget_amount"])
    bud_grp = (
        budget.groupby(["entity", "account"], dropna=False)["budget_amount"].sum().reset_index()
        if not budget.empty
        else pd.DataFrame(columns=["entity", "account", "budget_amount"])
    )

    # Prior
    try:
        prior_tb = load_tb(Path(state.data_path), prior, entity_scope if entity_scope != "ALL" else None)
    except Exception:
        prior_tb = pd.DataFrame(columns=["period", "entity", "account", "balance_usd"])
    prior_grp = (
        prior_tb.groupby(["entity", "account"], dropna=False)["balance_usd"].sum().reset_index(name="prior_usd")
        if not prior_tb.empty
        else pd.DataFrame(columns=["entity", "account", "prior_usd"])
    )

    # Merge
    df = tb_grp.merge(bud_grp, on=["entity", "account"], how="left").merge(
        prior_grp, on=["entity", "account"], how="left"
    )
    df["budget_amount"] = df["budget_amount"].fillna(0.0)
    df["prior_usd"] = df["prior_usd"].fillna(0.0)

    # Materiality
    materiality_map: Dict[str, float] = {}
    if isinstance(state.metrics.get("materiality_thresholds_usd"), dict):
        for k, v in state.metrics["materiality_thresholds_usd"].items():
            try:
                materiality_map[str(k)] = float(v)
            except Exception:
                continue

    def ent_threshold(ent: str) -> float:
        return float(materiality_map.get(str(ent), 1000.0))

    # Compute variances and exceptions
    rows: List[Dict[str, Any]] = []
    exceptions: List[Dict[str, Any]] = []
    input_row_ids: List[str] = []

    for _, r in df.iterrows():
        ent = str(r["entity"]) if pd.notna(r.get("entity")) else ""
        acct = str(r["account"]) if pd.notna(r.get("account")) else ""
        actual = float(r.get("actual_usd", 0.0))
        bud = float(r.get("budget_amount", 0.0))
        prev = float(r.get("prior_usd", 0.0))
        var_b = actual - bud
        var_p = actual - prev
        pct_b = (var_b / bud) if abs(bud) > 1e-9 else None
        pct_p = (var_p / prev) if abs(prev) > 1e-9 else None
        thr = ent_threshold(ent)
        band_b = "within" if abs(var_b) <= thr else "above"
        band_p = "within" if abs(var_p) <= thr else "above"

        # Determine a simple deterministic driver basis for narrative purposes
        basis = "budget" if abs(var_b) >= abs(var_p) else "prior"
        var_used = var_b if basis == "budget" else var_p
        band_used = ("within" if abs(var_used) <= thr else "above") if basis == "budget" else (
            "within" if abs(var_used) <= thr else "above"
        )

        # Deterministic narrative with citations to computed fields
        deterministic_summary = (
            f"[FORENSIC] {ent}/{acct}: variance vs {basis} = {var_used:.2f} USD (thr={thr:.2f}, band={band_used}). "
            f"Cites entity={ent}, account={acct}, period={period}."
        )

        row = {
            "entity": ent,
            "account": acct,
            "actual_usd": round(actual, 2),
            "budget_amount": round(bud, 2),
            "prior_usd": round(prev, 2),
            "var_vs_budget": round(var_b, 2),
            "var_vs_prior": round(var_p, 2),
            "pct_vs_budget": round(pct_b, 4) if pct_b is not None else None,
            "pct_vs_prior": round(pct_p, 4) if pct_p is not None else None,
            "threshold_usd": round(thr, 2),
            "band_vs_budget": band_b,
            "band_vs_prior": band_p,
            "ai_basis": basis,
            "deterministic_summary": deterministic_summary,
        }
        rows.append(row)

        # Rule: flag if abs variance exceeds entity threshold (either budget or prior)
        flagged = False
        if abs(var_b) > thr:
            exceptions.append(
                {
                    "entity": ent,
                    "account": acct,
                    "amount": abs(var_b),
                    "reason": "flux_budget_above_threshold",
                    "actual_usd": round(actual, 2),
                    "budget_amount": round(bud, 2),
                    "variance_usd": round(var_b, 2),
                    "threshold_usd": round(thr, 2),
                }
            )
            flagged = True
        if abs(var_p) > thr:
            exceptions.append(
                {
                    "entity": ent,
                    "account": acct,
                    "amount": abs(var_p),
                    "reason": "flux_prior_above_threshold",
                    "actual_usd": round(actual, 2),
                    "prior_usd": round(prev, 2),
                    "variance_usd": round(var_p, 2),
                    "threshold_usd": round(thr, 2),
                }
            )
            flagged = True
        if flagged:
            input_row_ids.append(f"{ent}|{acct}")

    # Artifact
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    out_path = Path(audit.out_dir) / f"flux_analysis_{run_id}.json"

    summary = {
        "rows": len(rows),
        "exceptions_count": len(exceptions),
        "by_entity_count": {},
        "band_counts": {"budget": {"within": 0, "above": 0}, "prior": {"within": 0, "above": 0}},
    }
    by_ent: Dict[str, int] = {}
    for e in exceptions:
        ent = str(e.get("entity"))
        by_ent[ent] = by_ent.get(ent, 0) + 1
    summary["by_entity_count"] = by_ent
    # Band counts
    for r in rows:
        summary["band_counts"]["budget"][str(r.get("band_vs_budget"))] += 1
        summary["band_counts"]["prior"][str(r.get("band_vs_prior"))] += 1

    # AI highlights: top absolute variances across chosen basis, and counts
    # Build a list of (entity, account, basis, variance_abs, variance_usd)
    top_items: List[Dict[str, Any]] = []
    for r in rows:
        basis = str(r.get("ai_basis"))
        v = float(r.get("var_vs_budget")) if basis == "budget" else float(r.get("var_vs_prior"))
        top_items.append(
            {
                "entity": r.get("entity"),
                "account": r.get("account"),
                "basis": basis,
                "variance_usd": round(v, 2),
                "variance_abs": round(abs(v), 2),
            }
        )
    top_items_sorted = sorted(top_items, key=lambda x: x["variance_abs"], reverse=True)
    ai_highlights = {
        "top_variances": top_items_sorted[:3],
        "count_above_budget": int(summary["band_counts"]["budget"]["above"]),
        "count_above_prior": int(summary["band_counts"]["prior"]["above"]),
    }
    summary["ai_highlights"] = ai_highlights

    artifact = {
        "generated_at": utils.now_iso_z(),
        "period": period,
        "prior": prior,
        "entity_scope": entity_scope,
        "rules": {
            "threshold_basis": "entity materiality (period_init)",
            "default_floor_usd": 1000.0,
        },
        "rows": rows,
        "exceptions": exceptions,
        "summary": summary,
    }

    with out_path.open("w", encoding="utf-8") as f:
        json.dump(artifact, f, indent=2)

    # Evidence & deterministic run
    period_fs = period.replace("-", "_")
    prior_fs = prior.replace("-", "_")
    tb_uri = Path(state.data_path) / f"trial_balance_{period_fs}.csv"
    prior_uri = Path(state.data_path) / f"trial_balance_{prior_fs}.csv"
    budget_uri = Path(state.data_path) / "budget.csv"

    ev_tb = EvidenceRef(type="csv", uri=str(tb_uri) if tb_uri.exists() else None)
    ev_prior = EvidenceRef(type="csv", uri=str(prior_uri) if prior_uri.exists() else None)
    ev_budget = EvidenceRef(type="csv", uri=str(budget_uri) if budget_uri.exists() else None, input_row_ids=input_row_ids or None)

    # Only attach row ids to budget evidence for drill-through; TB/prior are context
    state.evidence.extend([ev_tb, ev_prior, ev_budget])

    det = DeterministicRun(function_name="flux_analysis")
    det.params = {"period": period, "prior": prior, "entity": entity_scope}
    det.output_hash = _hash_json(artifact)
    state.det_runs.append(det)

    # Audit trail
    for ev in [ev_tb, ev_prior, ev_budget]:
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
            "evidence_id": ev_budget.id,
            "output_hash": det.output_hash,
            "params": det.params,
            "artifact": str(out_path),
        }
    )

    # Messages, tags, metrics
    if exceptions:
        state.messages.append(
            f"[DET] Flux analysis: {len(exceptions)} exceptions across {len(rows)} accounts -> {out_path}"
        )
    else:
        state.messages.append("[DET] Flux analysis: no exceptions above materiality")
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Flux analysis (Budget & Prior)"))

    state.metrics.update(
        {
            "flux_exceptions_count": len(exceptions),
            "flux_by_entity_count": summary["by_entity_count"],
            "flux_analysis_artifact": str(out_path),
        }
    )

    return state
