# FX Translation [DET]

Purpose: deterministically recompute USD balances from local currency using period FX rates and compare with reported USD balances in the TB.

Key actions:

- Map entity -> home currency from `entities.csv`
- Use `fx_rates.csv` for the run `period` to get `usd_rate`
- For each TB row, compute `computed_usd = balance * usd_rate`
- Compare against `balance_usd`; record differences over $0.01
- Persist drill-through artifact with per-row computation and evidence

Function: `r2r.engines.fx_translation.fx_translation(state, audit)`

Inputs:

- `state.tb_df`, `state.entities_df`, `state.fx_df`
- `state.period`, `state.entity`

Outputs:

- Artifact: `out/fx_translation_<run_id>.json` with rows and summary
- Evidence: TB with `input_row_ids` (period|entity|account) and FX rates CSV
- Deterministic run log with `output_hash`
- Messages/tags: `[DET] FX translation: ...` and DET tag rationale
- Metrics: `fx_translation_diff_count`, `fx_translation_total_abs_diff_usd`, `fx_translation_artifact`

Policy notes:

- Uses single period rate per currency as provided in dataset
- Precision tolerance set at $0.01 for difference flagging
- Purely deterministic; no AI influence
