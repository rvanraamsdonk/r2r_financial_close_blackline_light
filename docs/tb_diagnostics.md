# TB Diagnostics (Deterministic)

- **Engine**: `r2r/engines/tb_diagnostics.py`
- **Stage**: Runs after `tb_integrity` and before `accruals` in `r2r/graph.py`
- **Method**: [DET] deterministic, reproducible

## Purpose

Identify entities whose trial balance (TB) does not sum to zero and provide a drill-through of top contributing accounts with COA details.

## Inputs

- `data/lite/trial_balance_<period>.csv` (via `load_tb()`)
- `data/lite/chart_of_accounts.csv` (via `load_coa()`)
- CLI scope: `--period`, optional `--entity`

## Logic (deterministic)

- Group TB by `entity` and sum `balance_usd`.
- Any entity with non-zero sum (rounded to 2 decimals) is flagged as imbalanced.
- For each imbalanced entity:
  - Aggregate by `account`, sum `balance_usd`.
  - Sort by absolute `balance_usd` descending.
  - Merge COA to add `account_name`, `account_type`.
  - Return top 10 rows as `top_accounts`.

## Artifact

- Path: `out/tb_diagnostics_<run_id>.json`
- Keys:
  - `generated_at`, `period`, `entity_scope`
  - `diagnostics`: list of `{ entity, imbalance_usd, top_accounts[] }`
  - `top_accounts[]`: `{ account, balance_usd, account_name?, account_type? }`

## CLI Summary

`src/r2r/app.py` prints a concise summary by reading the artifact:

- `Entity <ID> imbalance=<amount> USD | Top3: <acct>: <amt>, ...`

## Metrics & Audit

- Messages include export path and entities.
- Evidence: TB CSV is recorded in audit as `EvidenceRef`.
- DeterministicRun captures function params and a hash of the input dataframe.
- Audit log: `out/audit_<run_id>.jsonl` contains an entry with `artifact` path.

## Reproducibility

- Fully deterministic given the same TB and COA inputs.
- No AI influence on calculations.

## Provenance & Drill-Through

- Evidence recorded as `EvidenceRef` now includes `input_row_ids` for row-level traceability.
- For each imbalanced entity, we capture all TB rows as row IDs using the key format: `<period>|<entity>|<account>`.
- This enables drill-through from the audit log (`out/audit_<run_id>.jsonl`) to the source CSV rows in `data/lite/trial_balance_<period>.csv`.
