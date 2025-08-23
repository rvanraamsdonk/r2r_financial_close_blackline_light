# AP & AR Reconciliation (Deterministic)

- Engine module: `src/r2r/engines/ap_ar_recon.py`
- Functions: `ap_reconciliation(state, audit)`, `ar_reconciliation(state, audit)`
- Artifacts: `out/ap_reconciliation_<run_id>.json`, `out/ar_reconciliation_<run_id>.json`
- Provenance:
  - EvidenceRef: source CSV under `data/lite/subledgers/`
  - input_row_ids: AP uses `bill_id`, AR uses `invoice_id`
  - DeterministicRun fn: `ap_reconciliation`, `ar_reconciliation`

## Logic

- AP: flags exceptions when any of the following is true:
  - `status == "Overdue"`
  - `age_days > 60`
  - `notes` contains the word "duplicate" (case-insensitive)

- AR: flags exceptions when any of the following is true:
  - `status == "Overdue"`
  - `age_days > 60`

Both engines:

- Filter to `state.period` and (optional) `state.entity`
- Persist JSON artifact with exceptions and summary totals by entity
- Append `EvidenceRef` with row-level `input_row_ids`
- Append `DeterministicRun` with parameters and output hash
- Update `state.messages`, `state.tags`, and `state.metrics`

## Graph Placement

- Inserted after bank reconciliation and before intercompany reconciliation:
  - `bank_recon -> ap_recon -> ar_recon -> ic_recon`

## Schema Expectations

Minimum columns in subledger files:

- AP: `period, entity, bill_id, vendor_name, bill_date, amount, currency, age_days, status, notes`
- AR: `period, entity, invoice_id, customer_name, invoice_date, amount, currency, age_days, status`

### New deterministic [DET]-labeled fields

- Each exception now includes a `[DET]`-labeled rationale string summarizing the reason and citing key fields.
  - AP: `ai_rationale` e.g. `[DET] AP E1 bill B-1001: reason=overdue, amount=123.45 USD, age_days=75. Candidates=2 (vendor=Acme).`
  - AR: `ai_rationale` e.g. `[DET] AR E1 invoice I-2002: reason=age_gt_60, amount=234.56 USD, age_days=90. Candidates=1 (customer=Beta).`
- Deterministic candidate suggestions for potential near-duplicates within the same subledger and entity.
  - AP: `candidates[]` objects include `bill_id, vendor_name, bill_date, amount, score (0..1)`
  - AR: `candidates[]` objects include `invoice_id, customer_name, invoice_date, amount, score (0..1)`
  - Scoring is deterministic based on amount similarity and bill/invoice date proximity (capped to top 3).
  - These are assistive hints, not auto-matches. They are grounded in artifact rows and clearly labeled.

## Audit & Evidence

- The audit log (`out/audit_<run_id>.jsonl`) contains matching `evidence` and `deterministic` records.
- `scripts/verify_provenance.py` asserts presence and structure of `input_row_ids` for these engines.

## Robustness

- Text fields like `status` and `notes` may be parsed by pandas as `NaN` (float) when blank.
- The engine uses a small helper to coerce such values to empty strings safely before applying
  operations like `.strip()` or `.lower()`. This prevents runtime errors on real-world data
  with partial/null text fields.
