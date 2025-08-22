# Bank Reconciliation (Deterministic)

- Purpose: Identify potential duplicate bank transactions deterministically for the in-scope period/entity.
- Engine: `r2r.engines.bank_recon.bank_reconciliation(state, audit)`
- Data source: `data/lite/subledgers/bank_statements/bank_transactions_*.csv` (loaded via `load_bank_transactions()`)

## Input Scope
- `period`: `state.period` (e.g., `2025-08`)
- `entity`: `state.entity` (e.g., `ALL` or `ENT100`)

## Rule Logic
- Duplicate signature: `[entity, date, amount, currency, counterparty, transaction_type]`
- For any signature group with size > 1, mark all but the first (stable by `bank_txn_id`) as `duplicate_candidate`.

## Artifact
- Path: `out/bank_reconciliation_{run_id}.json`
- Schema:
  - `generated_at`: UTC ISO timestamp
  - `period`, `entity_scope`
  - `rules.duplicate_signature`: list of columns used for matching
  - `exceptions`: array of objects
    - `entity`, `bank_txn_id`, `date`, `amount`, `currency`, `counterparty`, `transaction_type`, `description`
    - `reason`: `duplicate_candidate`
    - `duplicate_signature`: map of signature values
    - `primary_bank_txn_id`: reference to the primary record in the group
  - `summary`
    - `count`: number of exceptions
    - `total_abs_amount`: sum(|amount|) of duplicates
    - `by_entity_abs_amount`: map of entity -> sum(|amount|)

## Provenance & Audit
- Evidence: CSV URI of the bank transactions file + `input_row_ids` = list of flagged `bank_txn_id`s.
- Deterministic run: function name, params, dataset hash of filtered DataFrame, artifact path.

## Metrics
- `bank_duplicates_count`
- `bank_duplicates_total_abs`
- `bank_duplicates_by_entity`
- `bank_reconciliation_artifact`

## Notes
- Uses canonical loader for consistent filtering and CSV resolution.
- No assumptions beyond input data; thresholds are not applied here (pure duplicate detection).
