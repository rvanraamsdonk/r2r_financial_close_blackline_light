# Flux Analysis (Budget & Prior)

## Purpose
- Provide deterministic variance analysis between Actuals (TB) and (a) Budget, (b) Prior period.
- Surface material exceptions by entity/account for professional close review.
- Produce audit-ready artifact, provenance, and metrics for transparency.
- Compute variances and percents: 

## Inputs
- Trial Balance (current period) CSV: `data/.../trial_balance_YYYY_MM.csv`
- Budget CSV: `data/.../budget.csv`
- Trial Balance (prior period) CSV: `data/.../trial_balance_YYYY_MM.csv`
- Materiality thresholds from `period_init` (state.metrics.materiality_thresholds_usd)

## Scope & Filters
- Period: `state.period` (e.g., `2025-08`)
- Prior: `state.prior` or derived automatically as previous month
- Entity scope: `state.entity` or ALL

## Rules
- Aggregate Actuals: sum `balance_usd` by `entity, account`
- Aggregate Budget: sum `budget_amount` by `entity, account`
- Aggregate Prior: sum prior-period `balance_usd` by `entity, account`
  - `var_vs_budget = actual_usd - budget_amount`; `pct_vs_budget = var_vs_budget / budget_amount` if denom != 0
  - `var_vs_prior = actual_usd - prior_usd`; `pct_vs_prior = var_vs_prior / prior_usd` if denom != 0
- Exception: flag if `abs(var_vs_budget) > threshold(entity)` or `abs(var_vs_prior) > threshold(entity)`
- Threshold basis: `materiality_thresholds_usd[entity]` else default floor USD 1,000
- `deterministic_summary`: A `[FORENSIC]`-labeled text field summarizing the largest variance driver (budget or prior) for each account.

## Artifact
- File: `out/flux_analysis_<RUNID>.json`
- Schema (excerpt):
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

## Provenance & Audit
- Evidence appended:
  - TB (current period) CSV URI (context)
  - TB (prior period) CSV URI (context)
  - Budget CSV URI (primary) with `input_row_ids` = `["<entity>|<account>", ...]` for flagged items
- Deterministic run:
  - `function_name = "flux_analysis"`
  - Params: `{period, prior, entity}`
  - `output_hash`: hash of artifact content
- Provenance verifier allows None/empty `input_row_ids` for this step (zero exceptions possible)

## Metrics
- `flux_exceptions_count` — total exceptions
- `flux_by_entity_count` — mapping entity -> count
- `flux_analysis_artifact` — path to artifact

## Workflow Placement
- Inserted after `intercompany_reconciliation` and `accruals_check`, before `email_evidence_analysis`.

## Determinism & Security
- No network calls. Pure CSV inputs. Reproducible given same inputs and settings.
- Honors repo-wide policy flags and runs with AI off unless otherwise configured.
