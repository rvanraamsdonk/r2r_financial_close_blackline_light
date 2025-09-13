# Journal Entry (JE) Lifecycle Module

Engine: `src/r2r/engines/je_lifecycle.py::je_lifecycle(state, audit)`

## Purpose

Deterministically evaluate journal entries for approval state, supporting documentation, reversal flags, and four-eyes (SoD) compliance. Emit exceptions and summary metrics for governance and gatekeeping.

## Where it runs in the graph sequence

- After: Accruals
- Before: Flux Analysis
- Sequence: `... -> ic_recon -> accruals -> je_lifecycle -> flux_analysis ...`

## Inputs

- Data inputs
  - File: `data/supporting/journal_entries.csv`
  - Required columns: `period, entity, je_id, amount, currency, source_system, approval_status, approver, supporting_doc, reversal_flag`
- Module inputs (from `state.metrics`)
  - `materiality_thresholds_usd` by entity (for SoD checks)
  - `state.period`, `state.entity`
- Provenance inputs
  - EvidenceRef with CSV URI and `input_row_ids = [je_id, ...]`

## Scope and filters

- Period scope: rows where `period == state.period`
- Entity scope: if `state.entity != "ALL"`, filter to that entity
- Robust parsing: NaN-safe strings for `approval_status`, `supporting_doc`, `approver`

## Rules

### Deterministic

- Approval state
  - If `approval_status == "Rejected"` → `approval_rejected`
  - Else if `approval_status != "Approved"` → `approval_pending`
- Supporting documentation
  - If `source_system == "manual"` and `supporting_doc` is blank → `manual_missing_support`
- Reversal handling
  - If `reversal_flag` is true → `reversal_flagged`
- Four-eyes (SoD) enforcement
  - If `abs(amount) > materiality_thresholds_usd[entity]` and (`approval_status != "Approved"` or missing `approver`) → `four_eyes_breach`

### AI

- None in this engine. Any narratives are downstream and do not influence detection.

## Outputs

- Artifact path: `out/je_lifecycle_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "exceptions": [
    {
      "je_id": "JE-1001",
      "entity": "ENT100",
      "amount": 12500.0,
      "currency": "USD",
      "source_system": "manual",
      "reason": "manual_missing_support"
    },
    {
      "je_id": "JE-2002",
      "entity": "ENT200",
      "amount": 250000.0,
      "currency": "USD",
      "source_system": "ERP",
      "reason": "four_eyes_breach"
    }
  ],
  "summary": {
    "count": 2,
    "total_abs_amount": 262500.0,
    "by_reason": {"manual_missing_support": 1, "four_eyes_breach": 1}
  }
}
```

- Metrics written to `state.metrics`
  - `je_exceptions_count`, `je_exceptions_total_abs`, `je_exceptions_by_reason`, `je_lifecycle_artifact`

## Controls

- Deterministic rule set for approval, documentation, reversal, and SoD
- Provenance: EvidenceRef for CSV and row-level `input_row_ids`
- DeterministicRun with parameters and output hash
- Data quality: NaN-safe string handling; explicit numeric coercion for amounts
- Audit signals: messages summarize counts and artifact path
