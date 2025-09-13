# How a Run Unfolds (Start Here)

This guide explains the end-to-end flow for a single close run. It is the best entry point for anyone new to the solution. Every step is deterministic by default and records evidence, metrics, and audit trails. AI is used as an assistive layer where noted; it never replaces core controls.

## Contents

- [1. Run kickoff and state initialization](#1-run-kickoff-and-state-initialization)
- [2. Data ingestion and checks](#2-data-ingestion-and-checks-tb-master-data-rates)
- [3. Core deterministic engines](#3-core-deterministic-engines-execute-in-sequence)
- [4. Auto Journal Creation (optional)](#4-auto-journal-creation-optional-deterministic)
- [5. Assistive AI narratives (optional)](#5-assistive-ai-narratives-optional-downstream)
- [6. Gatekeeping & risk aggregation](#6-gatekeeping--risk-aggregation-det)
- [7. HITL and re-tests](#7-human-in-the-loop-hitl-and-re-tests-if-enabled)
- [8. Controls mapping and close reporting](#8-controls-mapping-and-close-reporting-det)
- [9. Expected outputs](#9-outputs-you-should-expect-in-outrun_id)
- [10. Agentic controllership](#10-what-agentic-controllership-means-here)

## Quick links to engine docs

- FX Translation: [fx_translation.md](./fx_translation.md)
- Bank Reconciliation: [bank_reconciliation.md](./bank_reconciliation.md)
- AP & AR Reconciliation: [ap_ar_reconciliation.md](./ap_ar_reconciliation.md)
- Intercompany Reconciliation: [intercompany_reconciliation.md](./intercompany_reconciliation.md)
- Accruals: [accruals.md](./accruals.md)
- JE Lifecycle: [je_lifecycle.md](./je_lifecycle.md)
- Flux Analysis: [flux_analysis.md](./flux_analysis.md)
- Auto Journal Creation: [journal_entries.md](../modules/journal_entries.md#auto-journal-creation-module)
- Gatekeeping: [gatekeeping.md](./gatekeeping.md)
- Controls Mapping: [controls_mapping.md](./controls_mapping.md)
- Close Reporting: [close_reporting.md](./close_reporting.md)

## Visual Overview

```mermaid
flowchart TD
  Run[Run Kickoff] --> Ingest[Data Ingestion & Checks]
  Ingest --> FX[FX Translation]
  FX --> TBDiag[TB Diagnostics]
  TBDiag --> Bank[Bank Reconciliation]
  Bank --> AP[AP Reconciliation]
  AP --> AR[AR Reconciliation]
  AR --> IC[Intercompany Reconciliation]
  IC --> Accruals[Accruals]
  Accruals --> JE[JE Lifecycle]
  JE --> Flux[Flux Analysis]
  FX -- Immaterial diffs --> AutoJE[Auto Journal Creation]
  Flux -- Immaterial variances --> AutoJE
  AutoJE --> Gate[Gatekeeping]
  Flux --> Gate
  Gate --> HITL[HITL (if needed)]
  Gate --> Controls[Controls Mapping]
  Controls --> Close[Close Reporting]
  Close --> Outputs[Artifacts & Audit]
```

## 1. Run kickoff and state initialization

### What happens
- A unique run ID is created (e.g., `run_20250912T201030Z`).
- The system locks period/entity scope (for example, `period = 2025-08`, `entity = ALL`).
- Materiality thresholds (USD) by entity are loaded or computed and stored in `state.metrics`.

### Artifacts and logs
- Audit log `out/run_<id>/audit_<id>.jsonl` is opened with a `run_started` record.
- The period initialization artifact and configuration snapshot are written to `out/run_<id>/period_init_*.json`.

## 2. Data ingestion and checks (TB, master data, rates)

### What happens
- Trial Balance, entity master, FX rates, subledger files (AP, AR, Bank, Intercompany, etc.) are located and read.
- Basic validations run: schema/columns, data types, date windows, referential integrity.

### Why it matters
- Ensures inputs are usable and traceable. Any issues are captured early to keep downstream steps deterministic and stable.

## 3. Core deterministic engines execute in sequence

### Typical order (subject to graph configuration in `src/r2r/graph.py`)
1. FX Translation [DET]: recompute USD, flag differences, write `fx_translation_artifact`.
2. Trial Balance Diagnostics [DET]: validate TB integrity and accounting rules, write `tb_diagnostics_artifact`.
3. Bank Reconciliation [DET]: detect duplicates/timing/forensic patterns, write `bank_reconciliation_artifact`.
4. AP Reconciliation [DET]: overdue/aging/forensic patterns (duplicate payments, round-dollar anomalies), write `ap_reconciliation_artifact`.
5. AR Reconciliation [DET]: overdue/aging/forensic patterns (channel stuffing, credit memo abuse), write `ar_reconciliation_artifact`.
6. Intercompany Reconciliation [DET]: mismatches vs thresholds, forensic patterns (round-dollar, transfer pricing), write `intercompany_reconciliation_artifact`.
7. Accruals [DET]: reversal checks and proposals, write `accruals_artifact`.
8. JE Lifecycle [DET]: governance checks (approval, SoD/four-eyes, reversals), write `je_lifecycle_artifact`.
9. Flux Analysis [DET]: variances vs Budget/Prior, write `flux_analysis_artifact`.

### Consistent behavior across engines
- Inputs are filtered to period/entity scope.
- Each engine emits a JSON artifact under `out/run_<id>/` with drill-through rows and a `summary`.
- Each engine appends evidence (`EvidenceRef`) and a deterministic run record (with `output_hash`) to the audit log.
- Each engine adds metrics such as counts, totals, and an `<module>_artifact` path to `state.metrics`.

## 4. Auto Journal Creation (optional, deterministic)

### What happens
- The Auto-JE engine reviews immaterial FX and Flux exceptions entity-by-entity against thresholds.
- It auto-creates and auto-approves small, well-defined journals (e.g., FX translation adjustments or accruals) and writes `auto_journals_artifact`.

### Why it matters
- Reduces net exception amounts before the risk assessment, accelerating the path to close without bypassing controls.

## 5. Assistive AI narratives (optional, downstream)

### What happens
- For select steps (e.g., executive summaries, risk narratives), AI generates human-readable explanations grounded in the produced artifacts.

### Guardrails
- AI outputs are strictly non-authoritative; they do not alter deterministic results or metrics. They are for comprehension and prioritization only.

## 6. Gatekeeping & risk aggregation [DET]

### What happens
- Gatekeeping aggregates exception counts, totals, and critical control flags from `state.metrics`.
- It evaluates a policy (materiality and thresholds) to determine `risk_level` and whether to `block_close`.
- Referenced artifacts from prior steps are included for drill-through, and a deterministic rationale is recorded.

### Artifacts and metrics
- Writes `gatekeeping_artifact` and sets `gatekeeping_risk_level`, `gatekeeping_block_close`, and related metrics.

## 7. Human-in-the-loop (HITL) and re-tests (if enabled)

### What happens
- If gatekeeping indicates attention is required, exceptions can be routed to HITL cases with owners and SLAs.
- After remediation (e.g., approvals, corrections), affected engines can be re-run to update metrics and artifacts.

### Artifacts and metrics
- Writes `out/run_*/cases_run_*.json` and optional AI summaries in `out/run_*/ai_cache/hitl_ai_case_summaries_*.json`.

## 8. Controls mapping and close reporting [DET]

### Controls Mapping
- Maps key metrics to internal control IDs/families, producing a concise controls artifact.

### Close Reporting
- Collects every `<module>_artifact`, compiles an executive summary of status and counts, and references the audit log.
- Writes the final `close_report_artifact`.

## 9. Outputs you should expect in `out/run_<id>/`

- Artifacts per engine (JSON) with rows, exceptions, proposals, and summaries.
- Gatekeeping artifact with risk and referenced artifacts map.
- Controls mapping artifact with control IDs and values.
- Close report manifest with an executive summary and full drill-through URIs.
- HITL cases artifact with review statuses and AI summaries (when enabled).
- Audit log (`audit_<id>.jsonl`) with deterministic run and evidence entries for provenance.
- AI cache folder (`ai_cache/`) with optional AI narratives and cost tracking.

## 10. What “agentic controllership” means here

- Deterministic engines do the heavy lifting and remain audit-defensible.
- AI adds rationale and triage but never overrides controls.
- Auto-JE resolves immaterial items to keep people focused on what matters.
- Gatekeeping enforces a trust‑but‑verify decision on close readiness with explicit thresholds.

---

# Functional Modules (Sequential)

Each module emits labeled outputs: [DET] deterministic, [AI] assistive, [HYBRID] mixed. All items include drill-through to evidence and lineage.

1. Period Initialization & Governance [DET]
   - Inputs: entities, COA, SOX controls, approval workflows, policy config
   - Actions: lock period/scope/currency; materiality by entity/account; run ID + config/code hash
   - Outputs: run config snapshot, control checklist, audit `run_started`

2. Data Ingestion & Validation [DET + AI]
   - Actions: schema/dtype, referential integrity, date windows, duplicates, FX coverage
   - [AI]: root-cause suggestions and remediation hints for validation exceptions

3. FX Translation [DET]
   - Policy: EOM for BS, average for P&L (configurable)
   - Outputs: reporting-currency TB/transactions; FX evidence; exceptions for gaps

4. TB Integrity & Rollups [DET]
   - Actions: Debits=Credits by entity; rollups/segments; integrity metrics

5. AP/AR Reconciliations [DET + AI]
   - Actions: GL control tie-outs; cutoff; duplicates; unmatched listings
   - [AI]: fuzzy match suggestions (confidence, citations) for unresolved items

6. Bank Reconciliations [DET + AI]
   - Actions: GL cash vs bank statements; timing items; unmatched register
   - [AI]: suggestions and timing vs error rationales

7. Intercompany Reconciliation [DET + AI]
   - Actions: rule-based matching; FX-consistent imbalances; deterministic true-up JE proposals with simulation
   - [AI]: match candidates and imbalance rationale (confidence, citations)

8. Accruals & Provisions [DET + AI]
   - Actions: recurring roll-forward + reversals; cutoff accruals from actuals; permitted estimates from patterns/budget variance
   - [AI]: JE narratives and management rationale (facts cited)

9. Flux Analysis (Budget & Prior) [DET + AI]
   - Actions: variance by account/entity; materiality banding; driver analysis
   - [AI]: grounded narratives citing computed variances and exact rows

10. Journal Entry Lifecycle [DET]
   - Actions: validate, simulate TB deltas, approvals (four-eyes, SoD), post, re-run controls
   
11. Gatekeeping & Risk Aggregation [DET + AI]
   - Actions: coverage/exception metrics; thresholds; readiness decision
   - [AI]: risk rationales and escalation recommendations

12. HITL Case Management [DET + AI]
   - Actions: cases with SLA, owner, evidence; re-tests after actions
   - [AI]: summarize evidence and propose next actions

13. Close Reporting & Evidence Pack [HYBRID]
   - [DET]: registers, dashboards, controls matrix, lineage graphs, code/config hash
   - [AI]: executive/variance narratives with citations and labels

14. Metrics & Controls Mapping [DET + AI]
   - [DET]: coverage %, exception $, recon statuses, IC netting, JE latency, AI cost/latency
   - [AI]: control owner summaries and residual-risk highlights
