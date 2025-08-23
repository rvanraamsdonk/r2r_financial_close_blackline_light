# Accruals Checks (Deterministic)

- **Engine**: `r2r/engines/accruals.py`
- **Stage**: Runs after `tb_diagnostics` and before `metrics` in `r2r/graph.py`
- **Method**: [DET] deterministic, reproducible

## Purpose

Detect accruals that should have reversed and those with missing or misaligned reversal dates. Produces an exceptions artifact and metrics for audit.

## Inputs

- `data/lite/supporting/accruals.csv`
  - Columns: `entity, accrual_id, description, amount_local, amount_usd, currency, status, accrual_date, reversal_date, notes`
- CLI scope: `--period`, optional `--entity`

## Logic (deterministic)

- Filter rows where `accrual_date` starts with the current `--period` (YYYY-MM).
- Compute next period (YYYY-MM) deterministically.
- Exceptions:
  - `status == "Should Reverse"` → `reason = explicit_should_reverse`.
  - `status in {"Active", "Should Reverse"}` and `reversal_date` not in the next period → `reason = missing_or_misaligned_reversal_date`.

## Artifact

- Path: `out/accruals_<run_id>.json`
- Keys:
  - `generated_at`, `period`, `next_period`, `entity_scope`
  - `exceptions[]`: `{ entity, accrual_id, description, amount_usd, currency, status, accrual_date, reversal_date, notes, reason }`
  - `proposals` (new): deterministic reversal suggestions for flagged items
    - `proposal_type = "accrual_reversal"`
    - `proposed_period` (next period), `amount_usd` (negative of accrual)
    - `narrative`
    - `ai_narrative` (new): `[DET]`-labeled deterministic helper text citing `entity`, `accrual_id`, `proposed_period`, and `amount_usd`.
      - Example: `[DET] Reverse A-123 for entity E1 in 2025-09: amount_usd=-1200.00. Cites entity, accrual_id, proposed_period, amount.`
      - Note: The `ai_narrative` field is generated deterministically from computed values and is clearly labeled as `[DET]`.
  - `summary`: `{ count, total_usd, by_entity, proposal_count }`
    - `roll_forward` (new): `{ next_period, proposed_reversals_total_usd, proposed_reversals_by_entity }`

## Metrics & Audit

- Metrics appended to `state.metrics`:
  - `accruals_exception_count`
  - `accruals_exception_total_usd`
  - `accruals_exception_by_entity`
- Evidence recorded for `supporting/accruals.csv` with a deterministic input hash.
- Audit log entry (`out/audit_<run_id>.jsonl`) includes `artifact` path and parameters.
- Message includes the number of proposals alongside the exception count.

## Reproducibility

- Fully deterministic given the same inputs.
- No AI influence on calculations. The `[DET]` fields are template-generated from computed values and clearly labeled.

## Provenance & Drill-Through

- Evidence recorded as `EvidenceRef` includes `input_row_ids` for row-level traceability.
- For each exception, we capture the accrual row ID as `<entity>|<accrual_id>`.
- Enables drill-through from `out/audit_<run_id>.jsonl` to `data/lite/supporting/accruals.csv`.

## Robustness

- Text fields like `status` and `reversal_date` may be `NaN` when blank.
- The engine uses a NaN-safe string helper to coerce such values to empty strings before
  applying `.strip()` or prefix checks, preventing runtime errors on messy data.
