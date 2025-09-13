# FX Translation Module

Engine: `src/r2r/engines/fx_translation.py::fx_translation(state, audit)`

## Purpose

Deterministically recompute USD balances from local currency using period FX rates and compare with reported USD balances in the trial balance (TB). Emit a drillable artifact with per-row computations and summary metrics.

## Where it runs in the graph sequence

- Early in the workflow after `period_init` and TB load/diagnostics
- Node: `fx_translation(state, audit)` (deterministic)

## Inputs

- Data inputs
  - Trial balance for period: `data/.../trial_balance_YYYY_MM.csv`
  - Entity master: `data/.../entities.csv` (entity -> home currency)
  - FX rates for period: `data/.../fx_rates_YYYY_MM.csv` (currency -> USD rate)
- Module inputs (from `state`)
  - `state.tb_df`, `state.entities_df`, `state.fx_df`
  - `state.period`, `state.entity`
- Provenance inputs
  - TB CSV URI with `input_row_ids = ["<period>|<entity>|<account>", ...]`
  - FX rate CSV URI

## Scope and filters

- Period scope: `state.period`
- Entity scope: all or specific `state.entity`
- Join TB rows to entity home currency and period FX rate
- Precision tolerance: $0.01 for difference flagging

## Rules

### Deterministic

- For each TB row
  - `computed_usd = round(balance_local * usd_rate, 2)`
  - `diff_usd = round(computed_usd - reported_usd, 2)`
  - Flag as exception when `abs(diff_usd) > 0.01`
- Summary aggregations by entity and overall totals

### AI

- None in this engine. Any AI narratives are downstream and do not affect calculations.

## Outputs

- Artifact path: `out/fx_translation_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "rows": [
    {
      "period": "2025-08",
      "entity": "ENT101",
      "account": "1000",
      "currency": "EUR",
      "balance_local": 389234.56,
      "rate": 1.0891,
      "computed_usd": 423915.36,
      "reported_usd": 423567.89,
      "diff_usd": 347.47,
      "is_exception": true
    }
  ],
  "summary": {
    "diff_count": 47,
    "total_abs_diff_usd": 12987.23,
    "by_entity_abs_diff_usd": {"ENT101": 4823.11}
  }
}
```

- Metrics written to `state.metrics`
  - `fx_translation_diff_count`
  - `fx_translation_total_abs_diff_usd`
  - `fx_translation_artifact`

## Controls

- Deterministic recomputation using supplied period FX rates
- Provenance: EvidenceRef for TB and FX rates with row-level `input_row_ids`
- DeterministicRun with parameters and output hash
- Data quality: numeric coercion, rounding to 2 decimals, tolerance guard of $0.01
- Audit signals: messages and [DET] tags for translation step
