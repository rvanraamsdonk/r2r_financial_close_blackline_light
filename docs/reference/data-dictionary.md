# Data Dictionary (Files and Semantics)

All inputs reside under `data/lite/`. Columns will be profiled and validated at ingestion; no hard-coded assumptions are used beyond file purpose.

- `trial_balance_YYYY_MM.csv`: General ledger trial balance for period. Expected: entity, account, currency, debit/credit amounts or net balance.
- `historical_balances.csv`: Prior-period balances for flux comparison.
- `chart_of_accounts.csv`: Account master; account type/class/segment metadata.
- `entities.csv`: Legal entities and hierarchy.
- `fx_rates.csv`: Exchange rates by currency and date; supports EOM and average policies.
- `budget.csv`: Budget by account/entity/period for variance analysis.
- `subledgers/ap_detail_*.csv`: AP invoices/payments detail.
- `subledgers/ar_detail_*.csv`: AR invoices/receipts detail.
- `subledgers/bank_statements/*`: Bank statement transactions by entity/account.
- `subledgers/intercompany/ic_transactions*.csv`: Intercompany transactions with counterparties.
- `journal_entries.csv`: Journal entries (historical/proposed) with lines, accounts, amounts, dates, descriptions.
- `accruals.csv`: Recurring accrual definitions and history.
- `sox_controls.csv`: Controls definitions and expectations.
- `approval_workflows.csv`: Approval routing and SoD rules.
- `risk_factors.csv`: Policy risk factors (entity/account specific).
- `transaction_patterns.csv`: Patterns used for accrual estimation where policy allows.
- `matching_keys.csv`: Deterministic keys for reconciliation matching.
- `intercompany_balancing.csv`: IC pairing and balancing rules.

Actual column names and types are discovered and validated at runtime; the system produces a profile report per file and fails fast on schema issues.
