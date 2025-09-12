# Financial Close Walkthrough (End-to-End)

This document walks through the complete R2R financial close flow in this repository. Each step summarizes: purpose, expected outcomes, example outputs, and suggested user actions (for a console or GUI).

Notes

- Always run via the repo venv: `.venv\Scripts\python.exe` on Windows (project-local venv).
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
  - Deterministically detect duplicate candidates and timing differences within bank statements; surface forensic-risk patterns (unusual counterparties, velocity anomalies, kiting).
- Expected outcomes
  - Categorized exceptions: `duplicate_candidate`, `timing_candidate`, and `forensic_risk` (no GL match rate is computed in this demo flow).
  - Metrics: counts and totals by entity; auto-approval only for immaterial duplicates/timing differences per policy.
- Example outputs
  - `out/run_*/bank_reconciliation_run_*.json` (exceptions, metrics, rules).
  - Console summary per bank account.
- User actions
  - Review matched/unmatched items.
  - Flag and resolve duplicates; approve timing differences.
  - Attach supporting evidence (statement lines, journal refs).

References: Bank engine `src/r2r/engines/bank_recon.py` with unit tests under `tests/unit/engines/`.

---

## 6) Accounts Payable (AP) Reconciliation

- Purpose
  - Deterministically flag overdue/aging issues and AP forensic patterns (duplicate payments, round-dollar anomalies, suspicious new vendors, weekend entries, split transactions).
- Expected outcomes
  - Exceptions categorized with vendor/document references (no GL variance calculation in this module).
  - Robust handling of NaN/None textual fields to avoid stalls.
- Example outputs
  - `out/run_*/ap_reconciliation_run_*.json`.
  - Console: AP variance summary by vendor.
- User actions
  - Sort by variance, filter by vendor, export exception list.
  - Approve or route items for investigation.

References: NaN-safe handling via `_safe_str` in `src/r2r/engines/ap_ar_recon.py` (see memory note), related unit tests under `tests/unit/ai/` or `tests/unit/engines/`.

---

## 7) Accounts Receivable (AR) Reconciliation

- Purpose
  - Deterministically flag overdue/aging and AR forensic patterns (channel stuffing near month-end with extended terms, credit memo abuse, related parties with unusual pricing, weekend revenue recognition). No unapplied cash logic in this module.
- Expected outcomes
  - Exceptions categorized with customer/invoice context.
- Example outputs
  - `out/run_*/ar_reconciliation_run_*.json`.
  - Console: AR variance summary by customer.
- User actions
  - Drill into invoice/payment chains.
  - Approve timing items or raise dispute tasks.

---

## 8) Intercompany (IC) Reconciliation

- Purpose
  - Deterministically flag amount mismatches by entity pair using materiality thresholds, and surface pattern-based forensic risks (round-dollar anomalies, large management fee/transfer pricing risks, structuring).
- Expected outcomes
  - Exception list by entity/counterparty with diff amounts and thresholds; may include simple true-up proposals when mismatches exist.
- Example outputs
  - `out/run_*/intercompany_reconciliation_run_*.json`.
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

## 10) Flux Analysis (Variance vs Budget/Prior)

- Purpose
  - Compare actuals vs budget and prior at entity/account level; compute variances and flags by materiality.
- Expected outcomes
  - Variance table with thresholds and directionality.
- Example outputs
  - `out/run_*/flux_analysis_run_*.json`.
  - Console variance summary by account/group.
- User actions
  - Filter by material variances.
  - Annotate with explanations or link evidence.

References: Budget input `data/budget.csv` and docs under `docs/`.

---

## 11) Controls Mapping

- Purpose
  - Map detected exceptions to control categories and frameworks for review and reporting.
- Expected outcomes
  - Control category counts and mappings to support governance and sampling.
- Example outputs
  - `out/run_*/controls_mapping_run_*.json`.
- User actions
  - Review mappings and ensure exceptions are routed to appropriate control owners.

References: `src/r2r/engines/controls_mapping.py` (artifact observed in audit log).

---

## 12) Gatekeeping Aggregate (Close Readiness)

- Purpose
  - Aggregate exceptions and apply materiality-based policies to determine close readiness and risk level.
- Expected outcomes
  - Risk level, block/allow close decision, AI rationale string, totals and auto-approval metrics.
- Example outputs
  - `out/run_*/gatekeeping_run_*.json`.
- User actions
  - Review gating decision, adjust policy thresholds as needed, and sample exceptions for review.

References: `src/r2r/engines/gatekeeping.py` (artifact observed in audit log).

---

## 13) Close Reporting

- Purpose
  - Produce an executive summary of period close status, risks, and actions.
- Expected outcomes
  - Consolidated report JSON with high-level metrics and AI summaries when enabled.
- Example outputs
  - `out/run_*/close_report_run_*.json`.
- User actions
  - Share report to stakeholders; attach to audit package.

References: `src/r2r/engines/close_reporting.py` (artifact observed in audit log).

---

# 14) Human-in-the-Loop (HITL) Review & Approvals [DET]

- Purpose
  - Route exceptions for review, collect approvals, and mark disposition (approved, adjust, follow-up).
- Expected outcomes
  - Updated status for each exception with audit trail (who/when/why).
- Example outputs
  - `out/run_*/cases_run_*.json` and AI summaries in `out/run_*/ai_cache/hitl_ai_case_summaries_*.json` when enabled.
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
  - Files under `out/run_*` with the run timestamp.
  - Provenance checks based on `out/run_*/audit_*.jsonl` (evidence and deterministic hashes).
- User actions
  - Download/export package.
  - View provenance graph and sampling checks.

References: `docs/audit.md`, provenance verification extended for email evidence input_row_ids.

---

## 15) Metrics, Performance & AI Cost Governance [DET]

- Purpose
  - Track runtime metrics (counts, durations), and AI token usage/costs when enabled.
- Expected outcomes
  - Metrics summaries; AI cost derived from env rate `R2R_AI_RATE_PER_1K`.
- Example outputs
  - AI usage metrics appear in the audit log (`ai_metrics` entries) and module-specific AI cache files under `out/run_*/ai_cache/`.
  - Optional metrics JSON if persisted by workflow.
- User actions
  - Inspect token/cost footprint by component.
  - Adjust AI usage flags or prompts accordingly.

References: `docs/ai_infra.md`, `scripts/drill_through.py`.
