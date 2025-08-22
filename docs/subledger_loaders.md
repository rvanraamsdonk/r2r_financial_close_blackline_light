# Subledger Loaders (Static Data Repo)

This document defines the schemas and loader functions for subledger datasets used by the static data repository under `data/lite/`.

- Data root: `data/lite/`
- Entities and currency context: `data/lite/entities.csv`
- FX rates for translation: `data/lite/fx_rates.csv`
- Subledgers: `data/lite/subledgers/`

## AR Detail
- File patterns (fallback order):
  - `data/lite/subledgers/ar_detail_{period}.csv`
  - `data/lite/subledgers/ar_detail_{period_with_underscore}.csv`
  - `data/lite/subledgers/ar_detail_aug.csv` (sample)
- Loader: `r2r.data.load_ar_detail(data_path, period, entity=None, status=None)`
- Columns: `period, entity, invoice_id, customer_name, invoice_date, amount, currency, age_days, status`
- Filters applied:
  - `period` required (exact match)
  - optional `entity` (exact match, ignored if 'ALL')
  - optional `status` (e.g., Outstanding, Overdue)

## AP Detail
- File patterns (fallback order):
  - `data/lite/subledgers/ap_detail_{period}.csv`
  - `data/lite/subledgers/ap_detail_{period_with_underscore}.csv`
  - `data/lite/subledgers/ap_detail_aug.csv` (sample)
- Loader: `r2r.data.load_ap_detail(data_path, period, entity=None, status=None)`
- Columns: `period, entity, bill_id, vendor_name, bill_date, amount, currency, age_days, status, notes`
- Filters applied:
  - `period` required
  - optional `entity`
  - optional `status`

## Bank Transactions
- Unified file patterns (fallback order):
  - `data/lite/subledgers/bank_statements/bank_transactions_{period}.csv`
  - `data/lite/subledgers/bank_statements/bank_transactions_{period_with_underscore}.csv`
  - `data/lite/subledgers/bank_statements/bank_transactions_aug.csv` (sample)
- Loader: `r2r.data.load_bank_transactions(data_path, period, entity=None)`
- Columns: `period, entity, bank_txn_id, date, amount, currency, counterparty, transaction_type, description`
- Filters applied:
  - `period` required
  - optional `entity`
- Notes:
  - Some directories also include entity-specific statement exports (e.g., `ent100_aug.csv`) with a different column layout. The loader intentionally ignores those to ensure a consistent schema.

## Intercompany Transactions
- File patterns (fallback order):
  - `data/lite/subledgers/intercompany/ic_transactions_{period}.csv`
  - `data/lite/subledgers/intercompany/ic_transactions_{period_with_underscore}.csv`
  - `data/lite/subledgers/intercompany/ic_transactions_aug.csv` (sample)
- Loader: `r2r.data.load_intercompany(data_path, period, src_entity=None, dst_entity=None)`
- Columns: `period, entity_src, entity_dst, doc_id, amount_src, amount_dst, currency, transaction_type, description`
- Filters applied:
  - `period` required
  - optional `src_entity` and/or `dst_entity`

## Currency Context
- Home currency per entity is defined in `entities.csv`.
- FX rates per `period, currency` are in `fx_rates.csv`.
- Subledgers store transactional `currency`; translation to home or USD can be performed downstream using `fx_rates.csv` and entity home currency as needed.

## Usage Examples
```python
from pathlib import Path
from r2r.data import (
    load_ar_detail,
    load_ap_detail,
    load_bank_transactions,
    load_intercompany,
)

DATA_PATH = Path('data/lite')
PERIOD = '2025-08'

ar = load_ar_detail(DATA_PATH, PERIOD, entity='ENT100', status='Outstanding')
ap = load_ap_detail(DATA_PATH, PERIOD)
bank = load_bank_transactions(DATA_PATH, PERIOD, entity='ENT101')
ic = load_intercompany(DATA_PATH, PERIOD, src_entity='ENT100')
```

## Audit Trail
- Loaders are deterministic and rely on static CSVs under source control.
- Filtering logic is explicit and documented above.
- All schemas align with the CSV headers present in `data/lite/subledgers/`.
