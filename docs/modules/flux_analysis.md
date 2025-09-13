# Flux Analysis Module

Engine: `src/r2r/engines/flux_analysis.py::flux_analysis(state, audit)`

## Purpose

Deterministically compute variances between Actuals (TB) and Budget/Prior, flag material exceptions by entity/account, and emit an audit-ready artifact with drill-through evidence and metrics.

## Where it runs in the graph sequence

- After: Intercompany reconciliation and Accruals
- Before: Email Evidence and Gatekeeping
- Node: `flux_analysis(state, audit)` (deterministic)

## Inputs

- Data inputs
  - Trial Balance (current): `data/.../trial_balance_YYYY_MM.csv`
  - Budget: `data/.../budget.csv`
  - Trial Balance (prior): `data/.../trial_balance_YYYY_MM.csv`
- Module inputs (from `state.metrics`)
  - `materiality_thresholds_usd` by entity; default floor USD 1,000
  - `state.period`, `state.prior` (or derived), `state.entity`
- Provenance inputs
  - EvidenceRef URIs for TB current/prior and Budget; `input_row_ids` = `["<entity>|<account>", ...]` for flagged rows

## Scope and filters

- Period scope: `state.period`; prior derived as previous month if absent
- Entity scope: `state.entity` or ALL
- Aggregate Actuals/Budget/Prior by `[entity, account]`

## Rules

### Deterministic

- Compute per account:
  - `var_vs_budget = actual_usd - budget_amount`; `pct_vs_budget = var_vs_budget / budget_amount` if denom != 0
  - `var_vs_prior = actual_usd - prior_usd`; `pct_vs_prior = var_vs_prior / prior_usd` if denom != 0
- Thresholding
  - Flag exception if `abs(var_vs_budget) > threshold(entity)` or `abs(var_vs_prior) > threshold(entity)`
  - `threshold(entity)` from `materiality_thresholds_usd` or default 1,000 USD
- Optional deterministic summaries may describe largest driver

### AI

- None in this engine. AI narratives for flux are generated downstream and do not affect detection logic.

## Outputs

- Artifact path: `out/flux_analysis_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-08-22T20:45:00Z",
  "period": "2025-08",
  "prior": "2025-07",
  "entity_scope": "ALL",
  "rules": {
    "threshold_basis": "entity materiality (period_init)",
    "default_floor_usd": 1000.0
  },
  "rows": [
    {
      "entity": "ENT100",
      "account": "4000",
      "actual_usd": 9599488.0,
      "budget_amount": 9300000.0,
      "prior_usd": 9400000.0,
      "var_vs_budget": 299488.0,
      "var_vs_prior": 199488.0,
      "pct_vs_budget": 0.0322,
      "pct_vs_prior": 0.0212,
      "threshold_usd": 100000.0,
      "band_vs_budget": "within",
      "band_vs_prior": "above"
    }
  ],
  "exceptions": [
    {
      "entity": "ENT100",
      "account": "4000",
      "reason": "flux_budget_above_threshold",
      "actual_usd": 9599488.0,
      "budget_amount": 9300000.0,
      "variance_usd": 299488.0,
      "threshold_usd": 100000.0
    }
  ],
  "summary": {
    "rows": 120,
    "exceptions_count": 3,
    "by_entity_count": {"ENT100": 2, "ENT101": 1},
    "band_counts": {
      "budget": {"within": 95, "above": 25},
      "prior": {"within": 90, "above": 30}
    }
  }
}
```

- Metrics written to `state.metrics`
  - `flux_exceptions_count`, `flux_by_entity_count`, `flux_analysis_artifact`

## Controls

- Deterministic computation and thresholding
- Provenance: EvidenceRef for TB (current/prior) and Budget with `input_row_ids`
- DeterministicRun with parameters and output hash
- Data quality: numeric coercion, safe handling of zero denominators
- Audit signals: messages summarize counts, thresholds, and artifact path
