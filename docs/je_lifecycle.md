# Journal Entry (JE) Lifecycle (Deterministic)

- Engine module: `src/r2r/engines/je_lifecycle.py`
- Function: `je_lifecycle(state, audit)`
- Artifact: `out/je_lifecycle_<run_id>.json`
- Provenance:
  - EvidenceRef: `data/<env>/supporting/journal_entries.csv`
  - input_row_ids: `je_id`
  - DeterministicRun fn: `je_lifecycle`

## Logic

For the in-scope period (and optional entity):
- Flags JEs where `approval_status` is not `Approved`.
  - If `Rejected` → `approval_rejected`
  - Otherwise → `approval_pending`
- Flags manual JEs with missing `supporting_doc` → `manual_missing_support`
- Flags entries where `reversal_flag` is true → `reversal_flagged`

Each exception includes `je_id`, `entity`, `amount`, `currency`, `source_system`, and `reason`.

## Output & Metrics

- JSON artifact contains:
  - `exceptions[]`
  - `summary.count`, `summary.total_abs_amount`, `summary.by_reason`
- `state.metrics` keys:
  - `je_exceptions_count`
  - `je_exceptions_total_abs`
  - `je_exceptions_by_reason`
  - `je_lifecycle_artifact`

## Graph Placement

- Inserted after `accruals` and before `flux_analysis`:
  - `... -> ic_recon -> accruals -> je_lifecycle -> flux_analysis ...`

## Audit & Evidence

- Audit log (`out/audit_<run_id>.jsonl`) records `evidence` and `deterministic` entries.
- `scripts/verify_provenance.py` checks `je_lifecycle` evidence has valid `input_row_ids` (allowing empty/None when no exceptions).

## Robustness

- Fields like `approval_status` and `supporting_doc` can be `NaN` when blank.
- The engine uses a NaN-safe string helper to coerce such values to empty strings before
  applying operations like `.strip()`/`.lower()` to avoid runtime errors.
