# AP & AR Reconciliation Module

Engine: `src/r2r/engines/ap_ar_recon.py::{ap_reconciliation, ar_reconciliation}`

## Purpose

Deterministically flag high-risk AP bills and AR invoices (e.g., overdue, aging) and provide assistive candidate hints for potential duplicates. Emit audit-ready artifacts and metrics for downstream modules.

## Where it runs in the graph sequence

- After: Bank reconciliation
- Before: Intercompany reconciliation
- Sequence: `bank_recon -> ap_recon -> ar_recon -> ic_recon`

## Inputs

- Data inputs
  - AP file: `data/subledgers/ap_detail_*.csv`
  - AR file: `data/subledgers/ar_detail_*.csv`
  - Required columns:
    - AP: `period, entity, bill_id, vendor_name, bill_date, amount, currency, age_days, status, notes`
    - AR: `period, entity, invoice_id, customer_name, invoice_date, amount, currency, age_days, status`
- Module inputs (from `state`)
  - `state.period`, `state.entity`
- Provenance inputs
  - EvidenceRef with CSV URI and `input_row_ids` (`bill_id` for AP, `invoice_id` for AR)

## Scope and filters

- Period scope: rows where `period == state.period`
- Entity scope: if `state.entity != "ALL"`, filter to that entity
- Robust parsing: NaN-safe string handling for `status`, `notes`

## Rules

### Deterministic

- AP exception rules (any true):
  - `status == "Overdue"`
  - `age_days > 60`
  - `notes` contains the word "duplicate" (case-insensitive)
- AR exception rules (any true):
  - `status == "Overdue"`
  - `age_days > 60`
- Deterministic candidate hints (both AP and AR):
  - Up to 3 candidates in same entity and counterparty with high amount similarity and date proximity; `score` in [0..1]
- Deterministic rationale per exception:
  - `deterministic_rationale` includes key fields and the reason

### AI

- None in these engines. AI suggestions may be generated downstream and do not affect detection logic.

## Outputs

- Artifacts
  - AP: `out/ap_reconciliation_{run_id}.json`
  - AR: `out/ar_reconciliation_{run_id}.json`

### AP artifact (representative schema)

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "exceptions": [
    {
      "entity": "ENT100",
      "bill_id": "B-1001",
      "vendor_name": "Acme Co",
      "bill_date": "2025-07-01",
      "amount": 123.45,
      "currency": "USD",
      "age_days": 75,
      "status": "Overdue",
      "reason": "overdue",
      "candidates": [
        {"bill_id": "B-0999", "vendor_name": "Acme Co", "bill_date": "2025-07-02", "amount": 123.45, "score": 0.97}
      ],
      "deterministic_rationale": "[DET] AP ENT100 bill B-1001: reason=overdue, 123.45 USD, age_days=75."
    }
  ],
  "summary": {
    "count": 1,
    "total_abs_amount": 123.45,
    "by_entity_abs_amount": {"ENT100": 123.45}
  }
}
```

### AR artifact (representative schema)

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "exceptions": [
    {
      "entity": "ENT200",
      "invoice_id": "I-2002",
      "customer_name": "Beta LLC",
      "invoice_date": "2025-06-15",
      "amount": 234.56,
      "currency": "USD",
      "age_days": 90,
      "status": "Open",
      "reason": "age_gt_60",
      "candidates": [
        {"invoice_id": "I-1999", "customer_name": "Beta LLC", "invoice_date": "2025-06-14", "amount": 234.56, "score": 0.93}
      ],
      "deterministic_rationale": "[DET] AR ENT200 invoice I-2002: reason=age_gt_60, 234.56 USD, age_days=90."
    }
  ],
  "summary": {
    "count": 1,
    "total_abs_amount": 234.56,
    "by_entity_abs_amount": {"ENT200": 234.56}
  }
}
```

- Metrics written to `state.metrics`
  - AP: `ap_exceptions_count`, `ap_exceptions_total_abs`, `ap_reconciliation_artifact`
  - AR: `ar_exceptions_count`, `ar_exceptions_total_abs`, `ar_reconciliation_artifact`

## Controls

- Deterministic and reproducible rules; no AI in detection
- Provenance: EvidenceRef with CSV URI and row-level `input_row_ids`
- DeterministicRun with parameters and output hash
- Data quality: NaN-safe text handling; deterministic candidate scoring and capping
- Audit signals: messages summarize counts and artifact paths; [DET] rationales for each exception
