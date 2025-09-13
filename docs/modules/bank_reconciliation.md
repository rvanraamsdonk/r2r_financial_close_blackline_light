# Bank Reconciliation Module

Engine: `src/r2r/engines/bank_recon.py::bank_reconciliation(state, audit)`

## Purpose

Identify potential duplicate or timing-related bank transactions deterministically for the in-scope period and entity. Emit an audit-ready artifact with exception details, deterministic rationales, and metrics.

## Where it runs in the graph sequence

- Early subledger checks, before AP/AR reconciliation
- Node: `bank_reconciliation(state, audit)` (deterministic)

## Inputs

- Data inputs
  - File(s): `data/subledgers/bank_statements/bank_transactions_*.csv`
  - Loaded via: `load_bank_transactions(data_path, period, entity)`
  - Required columns: `period, entity, bank_txn_id, date, amount, currency, counterparty, transaction_type, description`
- Module inputs (from `state`)
  - `state.period` (e.g., `2025-08`)
  - `state.entity` (e.g., `ALL` or specific entity)
- Provenance inputs
  - Source CSV URI, `input_row_ids` = flagged `bank_txn_id`s

## Scope and filters

- Period scope: include rows where `period == state.period`
- Entity scope: if `state.entity != "ALL"`, include only matching entity
- Robust parsing: normalize text fields; stable ordering by `bank_txn_id` for primary-vs-duplicate selection

## Rules

### Deterministic

- Duplicate signature
  - Signature columns: `[entity, date, amount, currency, counterparty, transaction_type]`
  - For any signature group with size > 1, mark all but the first (stable by `bank_txn_id`) as `duplicate_candidate` with `primary_bank_txn_id`
- Timing heuristic
  - Same signature excluding `date` within `rules.timing_window_days` (default 3 days) → flag the later txn as `timing_candidate`
- Deterministic candidate hints
  - For each exception, compute up to 3 nearest peers by amount and date proximity; label with deterministic scores

### AI

- None in this engine. Any AI narratives or summaries are generated downstream and do not influence detection logic.

## Outputs

- Artifact path: `out/bank_reconciliation_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "rules": {
    "duplicate_signature": ["entity", "date", "amount", "currency", "counterparty", "transaction_type"],
    "timing_window_days": 3
  },
  "exceptions": [
    {
      "entity": "ENT100",
      "bank_txn_id": "BTX-001",
      "date": "2025-08-15",
      "amount": 12500.0,
      "currency": "USD",
      "counterparty": "Acme Co",
      "transaction_type": "ACH",
      "description": "Vendor payment",
      "reason": "duplicate_candidate",
      "duplicate_signature": {
        "entity": "ENT100", "date": "2025-08-15", "amount": 12500.0,
        "currency": "USD", "counterparty": "Acme Co", "transaction_type": "ACH"
      },
      "primary_bank_txn_id": "BTX-000",
      "classification": "error_duplicate",
      "deterministic_rationale": "[DET] ENT100 BTX-001 duplicate of BTX-000 on 2025-08-15 for 12,500.00 USD (ACH Acme Co)."
    },
    {
      "entity": "ENT100",
      "bank_txn_id": "BTX-010",
      "date": "2025-08-20",
      "amount": 9800.0,
      "currency": "USD",
      "counterparty": "Beta LLC",
      "transaction_type": "WIRE",
      "description": "Customer receipt",
      "reason": "timing_candidate",
      "matched_bank_txn_id": "BTX-009",
      "day_diff": 2,
      "classification": "timing_difference",
      "deterministic_rationale": "[DET] ENT100 BTX-010 within 2-day window of BTX-009 (WIRE Beta LLC) 9,800.00 USD."
    }
  ],
  "summary": {
    "count": 2,
    "total_abs_amount": 22300.0,
    "by_entity_abs_amount": {"ENT100": 22300.0}
  }
}
```

- Metrics written to `state.metrics`
  - `bank_duplicates_count`
  - `bank_duplicates_total_abs`
  - `bank_duplicates_by_entity`
  - `bank_reconciliation_artifact`

## Controls

- Deterministic and reproducible detection; no thresholds beyond timing window
- Provenance: EvidenceRef with CSV URI and row-level `input_row_ids`
- DeterministicRun with parameters and output hash for artifact
- Data quality: normalized text, stable tie-break by `bank_txn_id`
- Audit signals: messages summarize counts and artifact path; tags mark [DET] rationale
