# Intercompany Reconciliation (Deterministic)

- Purpose: Identify intercompany amount mismatches that exceed entity materiality thresholds.
- Engine: `r2r.engines.intercompany_recon.intercompany_reconciliation(state, audit)`
- Data source: `data/lite/subledgers/intercompany/ic_transactions_*.csv` (loaded via `load_intercompany()`)

## Input Scope

- `period`: `state.period` (e.g., `2025-08`)
- Entities: all pairs in file; optionally filter by `src/dst` in loader (not used by default).

## Rule Logic

- For each row, compute `diff_abs = |amount_src - amount_dst|`.
- Threshold per pair = `max(materiality[src], materiality[dst])` if available from `period_init`; else `$1,000` floor.
- Flag exception when `diff_abs > threshold` with `reason = ic_amount_mismatch_above_threshold`.

## Artifact

- Path: `out/intercompany_reconciliation_{run_id}.json`
- Schema:
  - `generated_at`: UTC ISO timestamp
  - `period`
  - `rules.mismatch_rule`, `rules.default_floor_usd`
  - `exceptions` items:
    - `doc_id`, `entity_src`, `entity_dst`, `amount_src`, `amount_dst`, `currency`, `transaction_type`, `description`
    - `diff_abs`, `threshold`, `reason`
  - `summary`:
    - `count`, `total_diff_abs`, `by_pair_diff_abs`

## Provenance & Audit

- Evidence: CSV URI + `input_row_ids` = flagged `doc_id`s.
- Deterministic run: function name, params, dataset hash of filtered DataFrame, artifact path.

## Metrics

- `ic_mismatch_count`
- `ic_mismatch_total_diff_abs`
- `ic_mismatch_by_pair`
- `intercompany_reconciliation_artifact`

## Notes

- Relies on `period_init` to compute `materiality_thresholds_usd`; if absent, uses `$1,000` floor.
- Purely deterministic; no probabilistic assumptions.
