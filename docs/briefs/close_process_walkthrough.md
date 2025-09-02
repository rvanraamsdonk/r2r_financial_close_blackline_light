# Financial Close Walkthrough (End-to-End)

This document walks through the complete R2R financial close flow in this repository. Each step summarizes: purpose, expected outcomes, example outputs, and suggested user actions (for a console or GUI).

Notes

- Always run via the repo venv: `.venv/bin/python`.
- Main entrypoints: `scripts/run_close.py` (end-to-end), `scripts/drill_through.py` (drill/inspect), `scripts/smoke_test.py` (quick validation).
- Static, deterministic data for repeatable demos lives under `data/`. Outputs are timestamped into `out/`.

---

## 0) Orchestration & Run Initialization

- Purpose
  - Resolve configuration (entities, period), load `.env`, create a unique run ID, and initialize the LangGraph workflow.
- Expected outcomes
  - Unique run/session ID and timestamp prefix (e.g., `20250823T103548Z`).
  - Config summary (entities, period, AI on/off, data source: static CSVs).
  - Output folders ready in `out/`.
- Example outputs
  - Console header with run ID and configuration.
- User actions
  - Start/stop run.
  - Select entities and period.
  - Toggle AI explanations/cost tracking (via env `R2R_AI_RATE_PER_1K`).

References: `.env` loading (python-dotenv), AI cost rate in `src/r2r/ai/infra.py` (see `docs/ai_infra.md`).

---

## 1) Period Initialization & Data Source Selection

- Purpose
  - Establish the reporting period window and select the data source (static CSV dataset by default).
- Expected outcomes
  - Period context (month, year) and base currencies resolved.
  - Data files located under `data/` for TB, subledgers, bank, intercompany, FX, budget, emails.
- Example outputs
  - Console period summary.
- User actions
  - Confirm/edit the period.
  - Confirm dataset (static) or select alternative connector (future).

References: `docs/period_init.md`, dataset overview in `docs/` and `data/` structure.

---

## 2) Data Ingestion & Structural Validation

- Purpose
  - Load CSVs into normalized DataFrames: Trial Balance, AP aging, AR aging, Bank statements, Intercompany, FX rates, Budget/Forecast, Email metadata.
- Expected outcomes
  - In-memory frames with schema checks (keys present, numeric columns typed, no critical nulls).
- Example outputs
  - Console load counts (e.g., 127 TB lines, 34 bank transactions).
- User actions
  - Preview sample rows per source.
  - View counts and quick integrity checks.

References: Static dataset description in `docs/` and loader implementation in `src/r2r/data/`.

---

## 3) FX Coverage (Explain) and Deterministic Translation

- Purpose
  - Validate FX rate coverage (optional AI narrative) and perform deterministic FX translation of balances.
- Expected outcomes
  - FX coverage status (gaps highlighted) and translated balances per entity.
- Example outputs
  - `out/fx_translation_YYYYMMDDThhmmssZ.json`.
  - Console summary per currency and entity.
- User actions
  - Inspect rates and translation method.
  - Drill into entity-level translated balances.

References: `src/r2r/engines/fx_translation.py`, `docs/fx_translation.md`.

---

## 4) Trial Balance Checks & Diagnostics

- Purpose
  - Validate TB integrity and accounting rules; emit diagnostics for exceptions.
- Expected outcomes
  - Pass/fail on structural and summation checks.
  - Diagnostics recorded with severity and hints.
- Example outputs
  - JSON: `out/tb_diagnostics_YYYYMMDDThhmmssZ.json` (e.g., `out/tb_diagnostics_20250823T103548Z.json`).
  - Console TB validation summary.
- User actions
  - Review diagnostics, filter by entity/account.
  - Export diagnostics to CSV/JSON from UI.

---

## 5) Bank Reconciliation

- Purpose
  - Match bank statement lines to GL cash activity; detect timing differences, duplicates, and unmatched items.
- Expected outcomes
  - Matched pairs and categorized exceptions.
  - Metrics: match rate, unexplained variance by account.
- Example outputs
  - `out/bank_recon_YYYYMMDDThhmmssZ.json` (matches, exceptions, metrics).
  - Console summary per bank account.
- User actions
  - Review matched/unmatched items.
  - Flag and resolve duplicates; approve timing differences.
  - Attach supporting evidence (statement lines, journal refs).

References: Bank engine in `src/r2r/engines/` with tests like `tests/unit/engines/TestBankReconciliation::test_no_duplicates_scenario`.

---

## 6) Accounts Payable (AP) Reconciliation

- Purpose
  - Reconcile AP subledger aging vs GL; identify duplicates, cut-off issues, and status anomalies.
- Expected outcomes
  - Variances categorized with vendor/document references.
  - Robust handling of NaN/None textual fields to avoid stalls.
- Example outputs
  - `out/ap_recon_YYYYMMDDThhmmssZ.json`.
  - Console: AP variance summary by vendor.
- User actions
  - Sort by variance, filter by vendor, export exception list.
  - Approve or route items for investigation.

References: NaN-safe handling via `_safe_str` in `src/r2r/engines/ap_ar_recon.py` (see memory note), related unit tests under `tests/unit/ai/` or `tests/unit/engines/`.

---

## 7) Accounts Receivable (AR) Reconciliation

- Purpose
  - Reconcile AR subledger vs GL; detect duplicates, timing, and unapplied cash.
- Expected outcomes
  - Variances categorized with customer/invoice context.
- Example outputs
  - `out/ar_recon_YYYYMMDDThhmmssZ.json`.
  - Console: AR variance summary by customer.
- User actions
  - Drill into invoice/payment chains.
  - Approve timing items or raise dispute tasks.

---

## 8) Intercompany (IC) Reconciliation

- Purpose
  - Reconcile intercompany balances across entities; identify mismatches by counterparty and currency.
- Expected outcomes
  - Pairwise matrices and exception items by entity/counterparty.
- Example outputs
  - `out/ic_recon_YYYYMMDDThhmmssZ.json`.
  - Console matrix with variances and thresholds.
- User actions
  - Assign follow-ups to counterparties.
  - Document settlements or FX explanations.

References: Tests and fixtures under `tests/` confirm materiality thresholds and file discovery logic.

---

## 9) Accruals Processing & Reversals

- Purpose
  - Evaluate period-end accruals and expected reversals; flag missing or incorrect reversals.
- Expected outcomes
  - List of accruals with reversal status and impact.
- Example outputs
  - `out/accruals_YYYYMMDDThhmmssZ.json`.
  - Optional AI narratives in `out/ai_cache/accruals_ai_narratives_*.json` when enabled.
- User actions
  - Review failed/missing reversals.
  - Generate adjustment proposals or approve explanations.

References: Business context in `docs/accruals.md` and related narratives.

---

## 10) Variance Analysis vs Budget/Forecast

- Purpose
  - Compare actuals vs budget/forecast at account/cost center level; compute variances and flags.
- Expected outcomes
  - Variance table with thresholds and directionality.
- Example outputs
  - `out/variance_YYYYMMDDThhmmssZ.json`.
  - Console variance summary by account/group.
- User actions
  - Filter by material variances.
  - Annotate with explanations or link evidence.

References: Budget input in `data/lite/budget.csv` and docs under `docs/`.

---

# 11) Human-in-the-Loop (HITL) Review & Approvals [DET]

- Purpose
  - Route exceptions for review, collect approvals, and mark disposition (approved, adjust, follow-up).
- Expected outcomes
  - Updated status for each exception with audit trail (who/when/why).
- Example outputs
  - `out/review_queue_YYYYMMDDThhmmssZ.json` (status changes) if persisted by workflow.
  - Console: summarized queue with counts and statuses.
- User actions
  - Approve/Reject with comments.
  - Assign tasks and due dates.

References: Interactive flows shown in demo mode, with stop markers for HITL items.

---

## 12) Audit Package

- Purpose
  - Export key artifacts with immutable run IDs, input row references, and processing lineage for audit.
- Expected outcomes
  - Bundle of JSON/CSV files and a manifest referencing data lineage.
- Example outputs
  - Files under `out/` with the run timestamp.
  - Provenance checks (e.g., `verify_provenance.py`) passing.
- User actions
  - Download/export package.
  - View provenance graph and sampling checks.

References: `docs/audit.md`, provenance verification extended for email evidence input_row_ids.

---

## 13) Metrics, Performance & AI Cost Governance [DET]

- Purpose
  - Track runtime metrics (counts, durations), and AI token usage/costs when enabled.
- Expected outcomes
  - Metrics summaries; AI cost derived from env rate `R2R_AI_RATE_PER_1K`.
- Example outputs
  - `scripts/drill_through.py list-ai --sum` outputs total tokens/costs (text/JSON).
  - `out/metrics_YYYYMMDDThhmmssZ.json` if persisted by workflow.
- User actions
  - Inspect token/cost footprint by component.
  - Adjust AI usage flags or prompts accordingly.

References: `docs/ai_infra.md`, `scripts/drill_through.py`.
