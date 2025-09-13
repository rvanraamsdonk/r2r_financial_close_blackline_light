# Agentic Controllership Pitch Pack\n
\n---\n\n
# Agentic Controllership Pitch Pack

This pack compiles the essential, audit-ready documentation to present the R2R AI-first close. Use it as a printable source (export to PDF) and as a navigation guide for stakeholders.

## Contents

1. Executive KPI Dashboard
2. How a Run Unfolds (Start Here)
3. Metrics & Controls Mapping (SOX/COSO)
4. Engine Modules (Deterministic Rules & Outputs)
5. Gatekeeping & Close Reporting
6. Appendices (JE Platform & UI, Data Paths)

---

## 1) Executive KPI Dashboard

See: `docs/briefs/kpi_dashboard.md`

- Close readiness at a glance (risk level, block close, auto-close eligibility)
- Core KPIs with targets and tolerances
- Evidence snapshot linking to artifacts and audit log

---

## 2) How a Run Unfolds (Start Here)

See: `docs/modules/functional_modules.md`

- Step-by-step deterministic flow with artifacts and audit trails
- Visual overview of the graph (Mermaid)
- Quick links into each engine doc

---

## 3) Metrics & Controls Mapping (SOX/COSO)

See: `docs/modules/metrics_and_controls.md`

- Executive KPIs and tolerances
- Metric dictionary (definitions, formulae, evidence, owners)
- Controls mapping examples (control_id, objective, precision, assertions)
- Gatekeeping policy thresholds and deterministic rationale
- Evidence & reproducibility; AI governance (assistive-only)

---

## 4) Engine Modules (Deterministic Rules & Outputs)

- FX Translation â€” `docs/modules/fx_translation.md`
- Bank Reconciliation â€” `docs/modules/bank_reconciliation.md`
- AP & AR Reconciliation â€” `docs/modules/ap_ar_reconciliation.md`
- Intercompany Reconciliation â€” `docs/modules/intercompany_reconciliation.md`
- Accruals â€” `docs/modules/accruals.md`
- JE Lifecycle â€” `docs/modules/je_lifecycle.md`
- Flux Analysis â€” `docs/modules/flux_analysis.md`
- Auto Journal Creation â€” `docs/modules/journal_entries.md`
- Gatekeeping â€” `docs/modules/gatekeeping.md`
- Controls Mapping â€” `docs/modules/controls_mapping.md`
- Close Reporting â€” `docs/modules/close_reporting.md`

Each module doc follows: purpose, graph placement, inputs, scope/filters, deterministic vs AI rules, outputs (JSON example), and controls.

---

## 5) Gatekeeping & Close Reporting

- Gatekeeping aggregates exception signals, applies thresholds, and determines readiness.
- Close Reporting builds the evidence manifest and executive summary with drill-through to artifacts and audit log.

Docs:
- `docs/modules/gatekeeping.md`
- `docs/modules/close_reporting.md`

---

## 6) Appendices

- JE Platform & UI workflows â€” `docs/modules/journal_entries.md` (appendix section)
- Data paths (inputs/outputs) â€” `data/` and `out/` tree; see artifacts listed within each engine doc
- Testing â€” unit/integration tests under `tests/`

---

## Export to PDF

Run the PowerShell script (requires Pandoc installed) to generate a PDF version of this pack:

```powershell
# From repository root
scripts\make_pitch_pack.ps1
```

The script will:
- Concatenate this pack with the KPI Dashboard and key module docs into `out/pitch_pack/pitch_pack.md`
- If `pandoc` is available, produce `out/pitch_pack/pitch_pack.pdf`

\n---\n\n
# Executive KPI Dashboard (One Pager)

This page provides a concise view of close-readiness KPIs for the current run, aligned to audit-ready artifacts and controls. Use it as the first page in stakeholder decks.

## Period Context
- Period: 2025-08 (example)
- Entity scope: ALL (or specific entity)
- Run ID: run_YYYYMMDDThhmmssZ

## Close Readiness (At a Glance)
- Gatekeeping risk level: low
- Block close: false
- Auto-close eligible: true

## Core KPIs and Targets
- FX translation differences (count): 47  | Target: 0 (â‰¤ entity materiality tolerance)
- Bank duplicate/timing items (count): 2  | Target: 0
- AP/AR exceptions (count): 34             | Target: within tolerance by entity
- Intercompany residuals (total USD): 0.00 | Target: 0 (pair thresholds)
- Accruals exceptions (total USD): 711,808.57 | Target: decreasing trend
- JE exceptions (count): 2                 | Target: 0; p95 approval latency â‰¤ 2 days
- Flux exceptions (count): 47              | Target: within entity materiality band
- Auto journals (count / USD): 12 / 2,897.12 | Target: immaterial and bounded
- HITL open cases / SLA breaches: 0 / 0    | Target: 0
- AI cost (USD) / latency (ms): within budget and SLOs

## Interpreting the Numbers
- Exceptions above materiality require remediation or documented rationale.
- Auto journals reduce net exceptions only for immaterial items and are fully evidenced.
- Gatekeeping aggregates control signals to determine readiness (trust-but-verify).

## Evidence Snapshot (links)
- Close report: `out/run_.../close_report_...json`
- Gatekeeping: `out/run_.../gatekeeping_...json`
- FX translation: `out/run_.../fx_translation_...json`
- Bank reconciliation: `out/run_.../bank_reconciliation_...json`
- AP/AR reconciliation: `out/run_.../ap_reconciliation_...json` / `out/run_.../ar_reconciliation_...json`
- Intercompany reconciliation: `out/run_.../intercompany_reconciliation_...json`
- Accruals: `out/run_.../accruals_...json`
- JE lifecycle: `out/run_.../je_lifecycle_...json`
- Flux analysis: `out/run_.../flux_analysis_...json`
- Auto journals: `out/run_.../auto_journals_...json`
- Audit log: `out/run_.../audit_...jsonl`

## Example KPIs JSON (excerpt)
```json
{
  "kpis": {
    "gatekeeping_risk_level": "low",
    "block_close": false,
    "auto_close_eligible": true
  },
  "metrics": {
    "fx_translation_diff_count": 47,
    "bank_duplicates_count": 2,
    "ap_exceptions_count": 19,
    "ar_exceptions_count": 15,
    "ic_mismatch_total_diff_abs": 0.0,
    "accruals_exception_total_usd": 711808.57,
    "je_exceptions_count": 2,
    "flux_exceptions_count": 47,
    "auto_journals_count": 12,
    "auto_journals_total_usd": 2897.12
  }
}
```

## Cross-References
- Metrics & Controls: `docs/modules/metrics_and_controls.md`
- Functional Run Flow: `docs/modules/functional_modules.md`
- Engine Modules: see Quick links in `functional_modules.md`

\n---\n\n
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

## 10. What â€œagentic controllershipâ€ means here

- Deterministic engines do the heavy lifting and remain audit-defensible.
- AI adds rationale and triage but never overrides controls.
- Auto-JE resolves immaterial items to keep people focused on what matters.
- Gatekeeping enforces a trustâ€‘butâ€‘verify decision on close readiness with explicit thresholds.

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

\n---\n\n
# Metrics & Controls Mapping

This document presents the metrics and controls framework in a form suitable for senior audit (SOX/COSO) and Controllership audiences. It defines the KPIs, calculation methods, thresholds/targets, and the evidence trail that enables independent re-performance.

Aligned with engine docs in `docs/modules/`, this framework combines deterministic controls with assistive AI narratives while preserving auditability.

## Oneâ€‘pager summary and quick links

- Start with the KPI snapshot: `docs/briefs/kpi_dashboard.md`
- How a run unfolds: `docs/modules/functional_modules.md`
- Engine docs quick links: [FX Translation](./fx_translation.md) Â· [Bank](./bank_reconciliation.md) Â· [AP/AR](./ap_ar_reconciliation.md) Â· [Intercompany](./intercompany_reconciliation.md) Â· [Accruals](./accruals.md) Â· [JE Lifecycle](./je_lifecycle.md) Â· [Flux](./flux_analysis.md) Â· [Gatekeeping](./gatekeeping.md) Â· [Controls Mapping](./controls_mapping.md) Â· [Close Reporting](./close_reporting.md)

## 1) Executive KPIs (targets and tolerances)

- fx_translation_diff_count â€” Target: 0; Tolerance: â‰¤ entity materiality (USD)
- bank_duplicates_count â€” Target: 0; Red flag if > 0 for high-risk entities/accounts
- ap_exceptions_count / ar_exceptions_count â€” Target: within tolerance by entity; trends decreasing
- ic_mismatch_total_diff_abs â€” Target: 0; Floor-based thresholding per entity pair
- accruals_exception_total_usd â€” Target: decreasing trend; flagged reversals corrected next period
- je_exceptions_count â€” Target: 0; je_approval_latency_p95_days â€” Target: â‰¤ 2 business days
- flux_exceptions_count â€” Target: within entity materiality band; explanations attached
- gatekeeping_risk_level â€” Target: low; block_close â€” Target: false; auto_close_eligible â€” Target: true
- auto_journals_count / auto_journals_total_usd â€” Target: immaterial and bounded (below thresholds)
- hitl_open_cases / hitl_sla_breaches â€” Target: 0
- ai_cost_usd / ai_latency_ms â€” Target: within budget and SLOs; assistive only
- reproducibility_hash (code/config) â€” Target: stable across reruns with same inputs

## 2) Metric dictionary (definitions and evidence)

For each metric, we specify key, definition, formula, scope, target/threshold, frequency, owner, and evidence. Evidence always includes the artifact path and row-level `input_row_ids` when applicable.

### 2.1 fx_translation_diff_count
- Definition: Number of TB rows where abs(computed_usd - reported_usd) > tolerance (default $0.01). See engine: [FX Translation](./fx_translation.md)
- Formula: count of `rows[].is_exception == true` in `out/fx_translation_{run_id}.json`
- Scope: period = `state.period`, entity = `state.entity|ALL`
- Target/Threshold: Target 0; tolerance â‰¤ entity materiality for presentation
- Frequency: per run/month
- Owner: Controller / GL
- Evidence: `fx_translation_artifact` + `input_row_ids = ["<period>|<entity>|<account>"]`

### 2.2 bank_duplicates_count / bank_duplicates_total_abs
- Definition: Duplicate/timing candidates from bank statements; totals are sum of absolute amounts. See engine: [Bank Reconciliation](./bank_reconciliation.md)
- Formula: count/sum over `exceptions[]` in `out/bank_reconciliation_{run_id}.json` by `reason`
- Scope: statement period; entity scope per run
- Target/Threshold: Target 0; timing items reviewed and dispositioned
- Frequency: per run/month
- Owner: Treasury / Controller
- Evidence: `bank_reconciliation_artifact`, `input_row_ids = [bank_txn_id]`

### 2.3 ap_exceptions_count / ar_exceptions_count
- Definition: Deterministic AP/AR exceptions (overdue, age > 60, duplicate hints). See engine: [AP & AR Reconciliation](./ap_ar_reconciliation.md)
- Formula: count over `exceptions[]` in respective artifacts
- Scope: subledger period; entity scope per run
- Target/Threshold: within tolerance; trends decreasing; duplicates escalated
- Frequency: per run/month
- Owner: AP/AR Process Owner
- Evidence: `ap_reconciliation_artifact`, `ar_reconciliation_artifact`; `input_row_ids = [bill_id|invoice_id]`

### 2.4 ic_mismatch_count / ic_mismatch_total_diff_abs
- Definition: Intercompany mismatches exceeding pair materiality thresholds. See engine: [Intercompany Reconciliation](./intercompany_reconciliation.md)
- Formula: count/sum of `exceptions[]` where `diff_abs > threshold` in `out/intercompany_reconciliation_{run_id}.json`
- Scope: entity pairs within period; currency-consistent
- Target/Threshold: Target 0; thresholds = `max(materiality[src], materiality[dst])` or floor $1,000
- Frequency: per run/month
- Owner: IC Accounting
- Evidence: `intercompany_reconciliation_artifact`, `input_row_ids = [doc_id]`

### 2.5 accruals_exception_count / accruals_exception_total_usd
- Definition: Accruals with missing or misaligned reversals; explicit should-reverse. See engine: [Accruals](./accruals.md)
- Formula: count/sum over `exceptions[]` in `out/accruals_{run_id}.json`
- Scope: current period accruals; next-period reversals
- Target/Threshold: target decreasing trend; timely reversals in next period
- Frequency: per run/month
- Owner: Controller / FP&A
- Evidence: `accruals_artifact`, `input_row_ids = ["<entity>|<accrual_id>"]`

### 2.6 je_exceptions_count / je_approval_latency_p95_days
- Definition: JE governance exceptions and approval latency statistics. See engine: [JE Lifecycle](./je_lifecycle.md)
- Formula: count over `exceptions[]` in `out/je_lifecycle_{run_id}.json`; latency derived from JE process logs (submit vs approve timestamps)
- Scope: all JEs in-scope for period/entity
- Target/Threshold: je_exceptions_count = 0; p95 latency â‰¤ 2 business days
- Frequency: per run/month
- Owner: Controller
- Evidence: `je_lifecycle_artifact` (+ JE logs if persisted)

### 2.7 flux_exceptions_count / flux_by_entity_count
- Definition: Variances vs Budget/Prior exceeding materiality by entity. See engine: [Flux Analysis](./flux_analysis.md)
- Formula: count and grouping from `exceptions[]` in `out/flux_analysis_{run_id}.json`
- Scope: `state.period`, prior = previous month; entity scope per run
- Target/Threshold: within materiality band; explanations documented
- Frequency: per run/month
- Owner: FP&A / Controller
- Evidence: `flux_analysis_artifact`, `input_row_ids = ["<entity>|<account>"]`

### 2.8 gatekeeping_risk_level / block_close / auto_close_eligible
- Definition: Run-level risk assessment and decision flags. See engine: [Gatekeeping](./gatekeeping.md)
- Formula: computed in `out/gatekeeping_{run_id}.json` per policy
- Scope: run-level aggregation across modules
- Target/Threshold: risk = low; block_close = false
- Frequency: per run
- Owner: Controller / SOX PMO
- Evidence: `gatekeeping_artifact` + referenced artifacts map

### 2.9 auto_journals_count / auto_journals_total_usd
- Definition: Auto-created JEs for immaterial items (FX, Flux), deterministically approved
- Formula: count/sum in `out/auto_journals_{run_id}.json`
- Scope: limited to thresholds by entity
- Target/Threshold: bounded; strictly below entity materiality
- Frequency: per run/month
- Owner: Controller
- Evidence: `auto_journals_artifact`, with lines and `source_data` drill-through

### 2.10 hitl_open_cases / hitl_sla_breaches
- Definition: Open cases in HITL and SLA breaches during the run
- Formula: counts from `out/run_*/cases_run_*.json` (when HITL enabled)
- Scope: run-level
- Target/Threshold: 0 open at close sign-off; 0 SLA breaches
- Frequency: per run/month
- Owner: Controller / Case Owners
- Evidence: HITL cases artifacts; AI case summaries (optional) in `out/run_*/ai_cache/`

### 2.11 ai_cost_usd / ai_latency_ms / ai_tokens
- Definition: Cost and latency for assistive AI calls; usage by task
- Formula: aggregated from audit log `ai_metrics` entries
- Scope: run-level
- Target/Threshold: within budgeted limits and SLOs
- Frequency: per run/month
- Owner: Controllership / AI Governance
- Evidence: audit log `out/run_*/audit_*.jsonl` (ai_metrics)

### 2.12 reproducibility_hash
- Definition: Hash of code/config snapshot for re-performance
- Formula: sha256 over relevant config/code manifest at run start
- Scope: run-level
- Target/Threshold: stability across reruns with same inputs
- Frequency: per run
- Owner: Engineering / Controllership
- Evidence: present in audit log run header and close report

## 3) Controls mapping (SOX/COSO alignment)

Each mapped control includes: control_id, objective, activity, type (Preventive/Detective), frequency, precision, owner, evidence (artifact + `input_row_ids`), and assertions (Existence, Completeness, Accuracy, Cutoff).

Example mapping rows:

```json
[
  {
    "control_id": "BANK-REC-001",
    "objective": "Cash balances are accurate and free of duplicate entries",
    "activity": "Detect duplicate/timing items in bank statements and disposition",
    "type": "Detective",
    "frequency": "Per run",
    "precision": "High (signature-based match; 3-day timing window)",
    "owner": "Treasury",
    "evidence": "out/run_.../bank_reconciliation_...json",
    "assertions": ["Existence", "Accuracy"]
  },
  {
    "control_id": "JE-SOD-001",
    "objective": "JEs are authorized and appropriately reviewed",
    "activity": "Four-eyes approval for JEs above entity materiality",
    "type": "Detective",
    "frequency": "Per run",
    "precision": "High (threshold = entity materiality)",
    "owner": "Controller",
    "evidence": "out/run_.../je_lifecycle_...json",
    "assertions": ["Authorization", "Accuracy"]
  }
]
```

## 4) Gatekeeping policy (readiness assessment)

- Inputs: exception counts/totals from `state.metrics`, TB/FX coverage flags, and auto journal totals
- Derived values:
  - `gross_exception_amount = ap_total + ar_total + ic_total + accruals_total + je_total`
  - `net_exception_amount = gross_exception_amount - auto_journals_total_amount`
- Threshold parameters (configurable):
  - `MATERIALITY_THRESHOLD = 50,000` (USD)
  - `HIGH_RISK_THRESHOLD = 250,000` (USD)
- Decision logic:
  - High risk if: `fx_coverage_ok == false` OR `tb_balanced_by_entity == false` OR `net_exception_amount > HIGH_RISK_THRESHOLD`
  - Medium risk if: multiple exception sources with net > materiality (but â‰¤ high risk)
  - Low risk if: â‰¤ 2 sources and net â‰¤ materiality
  - `block_close = (risk == "high" or not auto_close_eligible)`
- Evidence: `out/gatekeeping_{run_id}.json` includes deterministic rationale and referenced artifacts

## 5) Evidence and reproducibility

- Every engine writes a JSON artifact under `out/run_<id>/` with drill-through rows and a `summary`
- `EvidenceRef` captures input URIs and `input_row_ids` for row-level traceability
- `DeterministicRun` captures function name, parameters, and `output_hash` over payload
- `close_report_{run_id}.json` aggregates artifact URIs and key status metrics
- Provenance enables independent re-performance and sampling

Example metrics manifest (excerpt):

```json
{
  "period": "2025-08",
  "entity_scope": "ALL",
  "kpis": {"gatekeeping_risk_level": "low", "block_close": false, "auto_close_eligible": true},
  "metrics": {
    "fx_translation_diff_count": 47,
    "bank_duplicates_count": 2,
    "ap_exceptions_count": 19,
    "ar_exceptions_count": 15,
    "ic_mismatch_total_diff_abs": 0.0,
    "accruals_exception_total_usd": 711808.57,
    "je_exceptions_count": 2,
    "flux_exceptions_count": 47,
    "auto_journals_count": 12,
    "auto_journals_total_usd": 2897.12
  },
  "artifacts": {
    "fx_translation_artifact": "out/run_.../fx_translation_...json",
    "bank_reconciliation_artifact": "out/run_.../bank_reconciliation_...json",
    "ap_reconciliation_artifact": "out/run_.../ap_reconciliation_...json"
  },
  "audit_log": "out/run_.../audit_...jsonl",
  "hash": "sha256:..."
}
```

## 6) AI governance (assistive only)

- Scope: AI is used for narratives and summaries; it does not alter deterministic calculations or decisions
- Metrics: `ai_cost_usd`, `ai_tokens`, `ai_latency_ms`, `ai_usage_by_task` from audit log
- Guardrails: prompts change control, model versioning, budget and SLO thresholds, reviewer sign-off for material narratives
- Artifacts: optional AI cache under `out/run_*/ai_cache/` with narrative files per module

## 7) Reporting views (for controllers and auditors)

- Risk heatmap by entity (bank/AP/AR/IC/JE/Flux exceptions)
- Exception waterfall: gross â†’ auto-JE net â†’ gatekeeping net
- JE approval latency distribution (p50/p95)
- Coverage dashboards and quarter-over-quarter trends

\n---\n\n
# FX Translation Module

Engine: `src/r2r/engines/fx_translation.py::fx_translation(state, audit)`

## Purpose

Deterministically recompute USD balances from local currency using period FX rates and compare with reported USD balances in the trial balance (TB). Emit a drillable artifact with per-row computations and summary metrics.

## Where it runs in the graph sequence

- Early in the workflow after `period_init` and TB load/diagnostics
- Node: `fx_translation(state, audit)` (deterministic)

## Inputs

- Data inputs
  - Trial balance for period: `data/.../trial_balance_YYYY_MM.csv`
  - Entity master: `data/.../entities.csv` (entity -> home currency)
  - FX rates for period: `data/.../fx_rates_YYYY_MM.csv` (currency -> USD rate)
- Module inputs (from `state`)
  - `state.tb_df`, `state.entities_df`, `state.fx_df`
  - `state.period`, `state.entity`
- Provenance inputs
  - TB CSV URI with `input_row_ids = ["<period>|<entity>|<account>", ...]`
  - FX rate CSV URI

## Scope and filters

- Period scope: `state.period`
- Entity scope: all or specific `state.entity`
- Join TB rows to entity home currency and period FX rate
- Precision tolerance: $0.01 for difference flagging

## Rules

### Deterministic

- For each TB row
  - `computed_usd = round(balance_local * usd_rate, 2)`
  - `diff_usd = round(computed_usd - reported_usd, 2)`
  - Flag as exception when `abs(diff_usd) > 0.01`
- Summary aggregations by entity and overall totals

### AI

- None in this engine. Any AI narratives are downstream and do not affect calculations.

## Outputs

- Artifact path: `out/fx_translation_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "rows": [
    {
      "period": "2025-08",
      "entity": "ENT101",
      "account": "1000",
      "currency": "EUR",
      "balance_local": 389234.56,
      "rate": 1.0891,
      "computed_usd": 423915.36,
      "reported_usd": 423567.89,
      "diff_usd": 347.47,
      "is_exception": true
    }
  ],
  "summary": {
    "diff_count": 47,
    "total_abs_diff_usd": 12987.23,
    "by_entity_abs_diff_usd": {"ENT101": 4823.11}
  }
}
```

- Metrics written to `state.metrics`
  - `fx_translation_diff_count`
  - `fx_translation_total_abs_diff_usd`
  - `fx_translation_artifact`

## Controls

- Deterministic recomputation using supplied period FX rates
- Provenance: EvidenceRef for TB and FX rates with row-level `input_row_ids`
- DeterministicRun with parameters and output hash
- Data quality: numeric coercion, rounding to 2 decimals, tolerance guard of $0.01
- Audit signals: messages and [DET] tags for translation step

\n---\n\n
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
  - Same signature excluding `date` within `rules.timing_window_days` (default 3 days) â†’ flag the later txn as `timing_candidate`
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

\n---\n\n
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

\n---\n\n
# Intercompany Reconciliation Module

Engine: `src/r2r/engines/intercompany_recon.py::intercompany_reconciliation(state, audit)`

## Purpose

Identify intercompany mismatches and forensic risk patterns deterministically, applying entity-pair materiality thresholds. Emit assistive candidate hints and deterministic true-up proposals.

## Where it runs in the graph sequence

- After: AR reconciliation
- Before: Accruals and Flux Analysis
- Node: `intercompany_reconciliation(state, audit)` (deterministic)

## Inputs

- Data inputs
  - File(s): `data/subledgers/intercompany/ic_transactions_*.csv`
  - Loaded via: `load_intercompany(data_path, period)`
  - Required columns: `doc_id, entity_src, entity_dst, amount_src, amount_dst, currency, transaction_type, description, date`
- Module inputs (from `state.metrics`)
  - `materiality_thresholds_usd` by entity (optional)
  - Defaults: `$1,000` floor when thresholds missing
  - `state.period`
- Provenance inputs
  - Source CSV URI, `input_row_ids` = flagged `doc_id`s

## Scope and filters

- Period scope: loader filters to current `state.period`
- Entity pairs: all in file; optional src/dst filters can be added in loader if needed
- Deterministic normalization of numeric fields; safe string handling

## Rules

### Deterministic

- Mismatch detection
  - `diff_abs = |amount_src - amount_dst|`
  - Threshold per pair: `max(materiality[src], materiality[dst])` if available, else `$1,000`
  - Flag when `diff_abs > threshold` â†’ `reason = ic_amount_mismatch_above_threshold`
- Forensic patterns
  - Round-dollar anomaly: `amount_src % 1000 == 0 and amount_src >= 10000` â†’ `ic_round_dollar_anomaly`
  - Transfer pricing risk: `"management fee" in transaction_type.lower()` and `amount_src > 50000` â†’ `ic_transfer_pricing_risk`
  - Structuring pattern: â‰¥3 small transactions (`amount_src < 10000`) from same pair on same `date` â†’ `ic_structuring_pattern`
- Candidate hints (assistive only)
  - Up to 3 peers within same pair/currency with closest `diff_abs`, deterministically scored and sorted
- True-up proposals
  - For each exception, deterministic proposal adjusting destination to match source:
    - `proposal_type = "ic_true_up"`, `adjustment_usd`, `simulated_dst_after`, `balanced_after`, `narrative`
- Deterministic rationale per exception
  - `deterministic_rationale` labeled `[DET]` or `[FORENSIC]` with doc_id, entities, diffs, thresholds

### AI

- None in this engine. AI-based IC matching/elimination proposals are generated downstream and do not influence deterministic detection here.

## Outputs

- Artifact path: `out/intercompany_reconciliation_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "rules": {
    "mismatch_rule": "flag |amount_src-amount_dst| > max(materiality[src], materiality[dst])",
    "default_floor_usd": 1000.0
  },
  "exceptions": [
    {
      "doc_id": "IC-001",
      "entity_src": "ENT100",
      "entity_dst": "ENT101",
      "amount_src": 75000.0,
      "amount_dst": 75000.0,
      "diff_abs": 0.0,
      "threshold": 50034.04,
      "reason": "ic_round_dollar_anomaly",
      "deterministic_rationale": "[FORENSIC] Round dollar anomaly: IC-001 for $75,000 ENT100->ENT101"
    }
  ],
  "proposals": [
    {
      "proposal_type": "ic_true_up",
      "doc_id": "IC-002",
      "entity_src": "ENT200",
      "entity_dst": "ENT201",
      "adjustment_usd": -1500.0,
      "simulated_dst_after": 98500.0,
      "balanced_after": true,
      "narrative": "Adjust destination to match source (delta -1,500.00 USD)"
    }
  ],
  "summary": {
    "count": 6,
    "total_diff_abs": 125000.0,
    "by_pair_diff_abs": {"ENT100->ENT101": 75000.0},
    "proposal_count": 3
  }
}
```

- Metrics written to `state.metrics`
  - `ic_mismatch_count`, `ic_mismatch_total_diff_abs`, `ic_mismatch_by_pair`, `intercompany_reconciliation_artifact`

## Controls

- Deterministic mismatch and forensic rule set; thresholds governed by `period_init`
- Provenance: EvidenceRef with CSV URI and row-level `input_row_ids`
- DeterministicRun with parameters and output hash
- Assistive candidates are non-binding and clearly labeled
- Audit messages include counts and artifact path; [DET]/[FORENSIC] rationales for each exception

\n---\n\n
# Accruals Module

Engine: `src/r2r/engines/accruals.py`

## Purpose

Detect accruals that should reverse and those with missing or misaligned reversal dates in the next period. Emit a deterministic exceptions artifact with reversal proposals and auditable metrics for downstream gatekeeping and reporting.

## Where it runs in the graph sequence

- After: `tb_diagnostics`
- Before: `metrics`
- Node: `accruals(state, audit)` (deterministic)

## Inputs

- Data inputs
  - File: `data/supporting/accruals.csv`
  - Columns:
    - `entity`: string
    - `accrual_id`: string
    - `description`: string
    - `amount_local`: number
    - `amount_usd`: number
    - `currency`: string
    - `status`: string (e.g., `Active`, `Should Reverse`)
    - `accrual_date`: `YYYY-MM-DD`
    - `reversal_date`: `YYYY-MM-DD` (may be blank)
    - `notes`: string
- Module inputs (from `state` / other nodes)
  - `state.period` (e.g., `2025-08`)
  - `state.entity` (e.g., `ALL` or specific entity)
- Provenance inputs
  - Source CSV URI
  - `input_row_ids` constructed as `<entity>|<accrual_id>` for flagged rows

## Scope and filters

- Period scope: rows where `accrual_date` starts with `state.period` (`YYYY-MM`)
- Entity scope: if `state.entity != "ALL"`, filter to that entity
- Robust parsing:
  - Treat empty/NaN text as empty strings before string ops
  - Coerce invalid dates to `None`
- Next period is computed deterministically from `state.period` (`YYYY-MM` â†’ `YYYY-MM`)

## Rules

### Deterministic

- Reverse-required
  - If `status == "Should Reverse"` â†’ `reason = explicit_should_reverse`
- Missing/misaligned reversal date
  - If `status in {"Active", "Should Reverse"}` AND `reversal_date` not in next period â†’ `reason = missing_or_misaligned_reversal_date`
- Proposal generation (deterministic)
  - For every exception, emit proposal:
    - `proposal_type = "accrual_reversal"`
    - `proposed_period = next_period`
    - `amount_usd = -amount_usd` (rounded)
    - `narrative`: concise description
    - `deterministic_rationale`: `[DET] Reverse {accrual_id} for {entity} in {next_period}: amount_usd={amt}`

### AI

- None. The accruals engine is fully deterministic. Any AI commentary occurs in downstream AI modules and does not affect calculations.

## Outputs

- Artifact path: `out/accruals_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "next_period": "2025-09",
  "entity_scope": "ALL",
  "exceptions": [
    {
      "entity": "ENT100",
      "accrual_id": "A-123",
      "description": "Payroll accrual",
      "amount_usd": 1200.0,
      "currency": "USD",
      "status": "Should Reverse",
      "accrual_date": "2025-08-28",
      "reversal_date": "",
      "notes": "",
      "reason": "explicit_should_reverse"
    },
    {
      "entity": "ENT200",
      "accrual_id": "A-456",
      "description": "Utilities accrual",
      "amount_usd": 800.0,
      "currency": "USD",
      "status": "Active",
      "accrual_date": "2025-08-10",
      "reversal_date": "2025-10-01",
      "notes": "",
      "reason": "missing_or_misaligned_reversal_date"
    }
  ],
  "proposals": [
    {
      "proposal_type": "accrual_reversal",
      "entity": "ENT100",
      "accrual_id": "A-123",
      "proposed_period": "2025-09",
      "amount_usd": -1200.0,
      "narrative": "Reverse A-123 in 2025-09 to offset August accrual.",
      "deterministic_rationale": "[DET] Reverse A-123 for ENT100 in 2025-09: amount_usd=-1200.00."
    }
  ],
  "summary": {
    "count": 2,
    "total_usd": 2000.0,
    "by_entity": {
      "ENT100": 1200.0,
      "ENT200": 800.0
    },
    "proposal_count": 1,
    "roll_forward": {
      "next_period": "2025-09",
      "proposed_reversals_total_usd": -1200.0,
      "proposed_reversals_by_entity": {
        "ENT100": -1200.0
      }
    }
  }
}
```

- Metrics written to `state.metrics`
  - `accruals_exception_count`: integer
  - `accruals_exception_total_usd`: number
  - `accruals_exception_by_entity`: map
  - `accruals_artifact`: string (artifact path)

## Controls

- Deterministic and reproducible
  - Fixed period/entity scoping and next-period calculation
  - No AI influence on logic or amounts
- Provenance and drill-through
  - `EvidenceRef` captures CSV URI and `input_row_ids` for flagged rows
  - Deterministic run record with output hash and parameters
- Data quality safeguards
  - NaN-safe string handling and date parsing
  - Explicit numeric coercion for amounts
- Audit signals
  - Messages include exception and proposal counts
  - Artifact is referenced in the audit log
- Segregation of duties
  - Proposals are suggestions; posting occurs via JE workflow or human review

\n---\n\n
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
  - If `approval_status == "Rejected"` â†’ `approval_rejected`
  - Else if `approval_status != "Approved"` â†’ `approval_pending`
- Supporting documentation
  - If `source_system == "manual"` and `supporting_doc` is blank â†’ `manual_missing_support`
- Reversal handling
  - If `reversal_flag` is true â†’ `reversal_flagged`
- Four-eyes (SoD) enforcement
  - If `abs(amount) > materiality_thresholds_usd[entity]` and (`approval_status != "Approved"` or missing `approver`) â†’ `four_eyes_breach`

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

\n---\n\n
# Flux Analysis Module

Engine: `src/r2r/engines/flux_analysis.py::flux_analysis(state, audit)`

## Purpose

Deterministically compute variances between Actuals (TB) and Budget/Prior, flag material exceptions by entity/account, and emit an audit-ready artifact with drill-through evidence and metrics.

## Where it runs in the graph sequence

- After: Intercompany reconciliation and Accruals
- Before: Email Evidence and Gatekeeping
- Node: `flux_analysis(state, audit)` (deterministic)

## Inputs

- Data inputs
  - Trial Balance (current): `data/.../trial_balance_YYYY_MM.csv`
  - Budget: `data/.../budget.csv`
  - Trial Balance (prior): `data/.../trial_balance_YYYY_MM.csv`
- Module inputs (from `state.metrics`)
  - `materiality_thresholds_usd` by entity; default floor USD 1,000
  - `state.period`, `state.prior` (or derived), `state.entity`
- Provenance inputs
  - EvidenceRef URIs for TB current/prior and Budget; `input_row_ids` = `["<entity>|<account>", ...]` for flagged rows

## Scope and filters

- Period scope: `state.period`; prior derived as previous month if absent
- Entity scope: `state.entity` or ALL
- Aggregate Actuals/Budget/Prior by `[entity, account]`

## Rules

### Deterministic

- Compute per account:
  - `var_vs_budget = actual_usd - budget_amount`; `pct_vs_budget = var_vs_budget / budget_amount` if denom != 0
  - `var_vs_prior = actual_usd - prior_usd`; `pct_vs_prior = var_vs_prior / prior_usd` if denom != 0
- Thresholding
  - Flag exception if `abs(var_vs_budget) > threshold(entity)` or `abs(var_vs_prior) > threshold(entity)`
  - `threshold(entity)` from `materiality_thresholds_usd` or default 1,000 USD
- Optional deterministic summaries may describe largest driver

### AI

- None in this engine. AI narratives for flux are generated downstream and do not affect detection logic.

## Outputs

- Artifact path: `out/flux_analysis_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-08-22T20:45:00Z",
  "period": "2025-08",
  "prior": "2025-07",
  "entity_scope": "ALL",
  "rules": {
    "threshold_basis": "entity materiality (period_init)",
    "default_floor_usd": 1000.0
  },
  "rows": [
    {
      "entity": "ENT100",
      "account": "4000",
      "actual_usd": 9599488.0,
      "budget_amount": 9300000.0,
      "prior_usd": 9400000.0,
      "var_vs_budget": 299488.0,
      "var_vs_prior": 199488.0,
      "pct_vs_budget": 0.0322,
      "pct_vs_prior": 0.0212,
      "threshold_usd": 100000.0,
      "band_vs_budget": "within",
      "band_vs_prior": "above"
    }
  ],
  "exceptions": [
    {
      "entity": "ENT100",
      "account": "4000",
      "reason": "flux_budget_above_threshold",
      "actual_usd": 9599488.0,
      "budget_amount": 9300000.0,
      "variance_usd": 299488.0,
      "threshold_usd": 100000.0
    }
  ],
  "summary": {
    "rows": 120,
    "exceptions_count": 3,
    "by_entity_count": {"ENT100": 2, "ENT101": 1},
    "band_counts": {
      "budget": {"within": 95, "above": 25},
      "prior": {"within": 90, "above": 30}
    }
  }
}
```

- Metrics written to `state.metrics`
  - `flux_exceptions_count`, `flux_by_entity_count`, `flux_analysis_artifact`

## Controls

- Deterministic computation and thresholding
- Provenance: EvidenceRef for TB (current/prior) and Budget with `input_row_ids`
- DeterministicRun with parameters and output hash
- Data quality: numeric coercion, safe handling of zero denominators
- Audit signals: messages summarize counts, thresholds, and artifact path

\n---\n\n
# Auto Journal Creation Module

Engine: `src/r2r/engines/auto_journal_engine.py::auto_journal_creation(state, audit)`

## Purpose

Deterministically create and auto-approve journal entries for immaterial differences detected by upstream engines (FX Translation, Flux Analysis). Reduce net exception amounts for Gatekeeping and accelerate close.

## Where it runs in the graph sequence

- After: FX Translation, Flux Analysis
- Before: Gatekeeping & Close Reporting
- Node: `auto_journal_creation(state, audit)` (deterministic)

## Inputs

- Module inputs (from `state.metrics`)
  - `fx_translation_artifact`: path to FX artifact (rows with `diff_usd`)
  - `flux_analysis_artifact`: path to Flux artifact (rows with `var_vs_budget`, etc.)
  - `materiality_thresholds_usd` per entity; default threshold = 5,000 USD
  - `state.period`, `state.entity`

## Scope and filters

- Period scope: period of the inbound artifacts
- Entity scope: if `state.entity != "ALL"`, restrict to that entity
- FX: consider rows where `abs(diff_usd) > 0`
- Flux: consider rows where `abs(var_vs_budget) > 0` (and positive for accrual cases)

## Rules

### Deterministic

- FX translation adjustments
  - If `0 < abs(diff_usd) <= threshold(entity)`: propose JE via `JEEngine.propose_je(module="FX", scenario="translation_adjustment", ...)`
  - Auto-approve proposal and add `[DET]` rationale noting amount and threshold
- Flux accrual adjustments
  - If `0 < abs(var_vs_budget) <= threshold(entity)` and `var_vs_budget > 0`: propose JE via `JEEngine.propose_je(module="Flux", scenario="accrual_adjustment", ...)`
  - Auto-approve proposal and add `[DET]` rationale
- Summarize totals by module and overall

### AI

- None. Auto-creation is purely deterministic. Any narratives elsewhere do not affect this engineâ€™s logic.

## Outputs

- Artifact path: `out/auto_journals_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "auto_journals": [
    {
      "je_id": "46f055df-79a3-46c6-b9c2-43fb2007eb9f",
      "module": "FX",
      "scenario": "translation_adjustment",
      "entity": "ENT101",
      "amount_usd": 347.47,
      "description": "FX translation adjustment - EUR 347.47 (ENT101/1000)",
      "lines": [
        {"account": "1000", "description": "FX translation adjustment - EUR", "debit": 347.47, "credit": 0.0, "entity": "ENT101", "currency": "USD"},
        {"account": "7201", "description": "FX translation gain - EUR", "debit": 0.0, "credit": 347.47, "entity": "ENT101", "currency": "USD"}
      ],
      "deterministic_rationale": "[DET] Auto-created FX translation adjustment; amount below entity threshold.",
      "source_data": {"entity": "ENT101", "account": "1000", "currency": "EUR", "diff_usd": 347.47}
    }
  ],
  "summary": {
    "total_count": 12,
    "total_amount_usd": 2897.12,
    "by_module": {"FX": 9, "Flux": 3}
  },
  "materiality_thresholds": {"ENT101": 5000},
  "auto_journal_threshold": 5000
}
```

- Metrics written to `state.metrics`
  - `auto_journals_count`, `auto_journals_total_usd`, `auto_journals_by_module`, `auto_journals_artifact`

## Controls

- Deterministic creation bounded by entity thresholds; auto-approval only for immaterial amounts
- Provenance: upstream artifacts referenced; deterministic run recorded with output hash
- Data quality: resilient parsing of artifacts; numeric coercion and rounding for lines
- Audit signals: messages include counts and totals; [DET] rationales per auto-JE

---

# Journal Entry (JE) Module

## Overview

The Journal Entry module provides a generic, reusable workflow for proposing, reviewing, approving, and posting journal entries across all R2R financial close modules. It integrates seamlessly with FX Translation, Flux Analysis, and other modules to enable accountants to create adjusting entries directly from identified variances.

## Architecture

### Data Models

```python
class JEStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending" 
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"

@dataclass
class JELine:
    account: str
    description: str
    debit: float = 0.0
    credit: float = 0.0

@dataclass 
class JournalEntry:
    id: str
    module: str
    scenario: str
    entity: str
    period: str
    description: str
    lines: List[JELine]
    status: JEStatus
    source_data: Dict[str, Any]
    created_at: datetime
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    approver: Optional[str] = None
    comments: str = ""
```

### Backend Endpoints

#### `/je/propose` (POST)
- **Purpose**: Create and display a JE proposal modal
- **Input**: JSON with module, scenario, source_data, period, entity
- **Output**: JE proposal modal HTML with calculated entries
- **Business Logic**: 
  - Calls module-specific JE creation functions (`_create_fx_je`, `_create_flux_je`)
  - Generates appropriate debit/credit entries based on source data
  - Returns modal with JE details and workflow actions

#### `/je/submit/{je_id}` (POST)
- **Purpose**: Submit JE for approval
- **Input**: JE ID from URL path
- **Output**: Updated modal with "Pending" status
- **Business Logic**: Changes status from DRAFT â†’ PENDING

#### `/je/approve/{je_id}` (POST)
- **Purpose**: Approve or reject JE
- **Input**: JE ID and action (approve/reject) from form
- **Output**: Updated modal with approval status
- **Business Logic**: Changes status to APPROVED or REJECTED

#### `/je/post/{je_id}` (POST)
- **Purpose**: Post JE to GL system
- **Input**: JE ID from URL path
- **Output**: Updated modal with "Posted" status
- **Business Logic**: Changes status from APPROVED â†’ POSTED

### Module Integration

#### FX Translation
- **Trigger**: FX differences > $0.01
- **JE Logic**: Creates translation adjustment entries
  - Debit: Translation Adjustment Expense
  - Credit: Cumulative Translation Adjustment (CTA)
- **Account Mapping**: Uses entity-specific GL accounts

#### Flux Analysis
- **Trigger**: Variances exceeding threshold (severe = true)
- **JE Logic**: Creates variance explanation entries
  - Debit/Credit: Appropriate expense/revenue accounts
  - Contra: Accrual or reclassification accounts
- **Account Mapping**: Based on account type and variance direction

## UI Components

### JE Button (`partials/je_button.html`)
Generic button component that can be embedded in any table row:
```html
<button type="button" 
        class="inline-flex items-center px-2 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded border border-indigo-200 transition-colors"
        hx-post="/je/propose"
        hx-vals='{"module": "{{ module }}", "scenario": "{{ scenario }}", "source_data": {{ source_data | tojson }}, "period": "{{ period }}", "entity": "{{ entity }}"}'
        hx-target="body"
        hx-swap="beforeend">
  JE
</button>
```

### JE Proposal Modal (`partials/je_proposal_modal.html`)
Comprehensive modal displaying:
- JE header information (ID, module, entity, period)
- Debit/credit line items with account details
- Balance validation (ensures debits = credits)
- Source data reference
- Workflow action buttons based on current status
- Modal close functionality

## Business Logic Functions

### `_create_fx_je(source_data, period, entity)`
Creates journal entries for FX translation differences:
- Calculates adjustment amount from source_data
- Determines debit/credit direction based on difference sign
- Maps to appropriate GL accounts (Translation Adj, CTA)
- Returns JournalEntry object with calculated lines

### `_create_flux_je(source_data, period, entity)`  
Creates journal entries for flux analysis variances:
- Extracts variance amount and account from source_data
- Determines adjustment type (accrual, reclassification, etc.)
- Maps to appropriate GL accounts based on account type
- Returns JournalEntry object with variance entries

## Integration Points

### Module Integration
1. Add JE column header to table templates
2. Include JE button in table rows with conditional display
3. Pass module-specific data via `hx-vals` attribute
4. Implement module-specific JE creation logic

### Example Integration (FX Module):
```html
<!-- In fx.html table header -->
<th class="text-center px-2 py-2">JE</th>

<!-- In fx table row -->
<td class="px-2 py-2 text-center">
  {% if r.diff_usd|abs > 0.01 %}
  <button type="button" 
          class="inline-flex items-center px-2 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded border border-indigo-200 transition-colors"
          hx-post="/je/propose"
          hx-vals='{"module": "FX", "scenario": "fx_translation", "source_data": {{ r | tojson }}, "period": "{{ fx.period }}", "entity": "{{ r.entity }}"}'
          hx-target="body"
          hx-swap="beforeend">
    JE
  </button>
  {% endif %}
</td>
```

## Workflow States

1. **DRAFT**: JE created but not submitted
   - Actions: Submit for Approval, Edit, Cancel
   
2. **PENDING**: JE submitted and awaiting approval
   - Actions: Approve, Reject, View Details
   
3. **APPROVED**: JE approved and ready for posting
   - Actions: Post to GL, View Details
   
4. **POSTED**: JE posted to GL system
   - Actions: View Details only (read-only)
   
5. **REJECTED**: JE rejected by approver
   - Actions: Revise and Resubmit, Cancel

## Account Mapping Strategy

### FX Translation Entries
- **Translation Loss**: Dr. Translation Adjustment Expense, Cr. CTA
- **Translation Gain**: Dr. CTA, Cr. Translation Adjustment Income
- **Account Codes**: Entity-specific (e.g., 7820-Translation Adj, 3150-CTA)

### Flux Analysis Entries  
- **Revenue Variances**: Adjust revenue accounts with accrual contra
- **Expense Variances**: Adjust expense accounts with prepaid/accrual contra
- **Account Mapping**: Based on account type and GL structure

## Future Enhancements

1. **Persistent Storage**: Replace in-memory store with database
2. **User Authentication**: Add real user roles and permissions
3. **Audit Trail**: Enhanced logging and approval history
4. **Batch Processing**: Support for multiple JE creation
5. **GL Integration**: Real posting to external GL systems
6. **Workflow Customization**: Configurable approval routing
7. **Template Library**: Pre-defined JE templates by scenario

## Testing

### Manual Testing Steps
1. Navigate to FX or Flux analysis page
2. Identify rows with material differences/variances
3. Click "JE" button to open proposal modal
4. Review calculated entries and balance validation
5. Test complete workflow: Submit â†’ Approve â†’ Post
6. Verify status updates and action button changes

### Integration Testing
- Verify JE buttons appear conditionally based on thresholds
- Test modal functionality across different modules
- Validate account mappings and calculation logic
- Confirm HTMX interactions and modal behavior

## Security Considerations

- Input validation on all JE endpoints
- Authorization checks for approval actions
- Audit logging for all JE state changes
- Data sanitization for source_data JSON
- CSRF protection via HTMX headers

\n---\n\n
# Gatekeeping & Risk Aggregation Module

Engine: `src/r2r/engines/gatekeeping.py::gatekeeping_aggregate(state, audit)`

## Purpose

Deterministically aggregate exception signals and key controls to compute an overall risk level and a block/allow decision before final reporting. Provide a drill-through manifest of referenced artifacts for audit.

## Where it runs in the graph sequence

- After: Email Evidence
- Before: Metrics and Close Reporting
- Node: `gatekeeping_aggregate(state, audit)` (deterministic)

## Inputs

- Module inputs (from `state.metrics`) produced by earlier engines:
  - `fx_coverage_ok`
  - `tb_balanced_by_entity`, `tb_entity_sums_usd`
  - `bank_duplicates_count`
  - `ap_exceptions_count`, `ap_exceptions_total_abs`
  - `ar_exceptions_count`, `ar_exceptions_total_abs`
  - `ic_mismatch_count`, `ic_mismatch_total_diff_abs`
  - `accruals_exception_count`, `accruals_exception_total_usd`
  - `je_exceptions_count`, `je_exceptions_total_abs`
  - `flux_exceptions_count`
  - `auto_journals_created_count`, `auto_journals_total_amount`
- Referenced artifacts (evidence URIs)
  - Any metrics key ending with `_artifact` is included as a referenced artifact

## Scope and filters

- Period/entity come from `state`
- Categories include only known sources; auto-journal counts tracked but excluded from "sources_triggered"

## Rules

### Deterministic

- Count `sources_triggered = number of categories with count > 0` (excluding auto-journals)
- Compute exception magnitudes
  - `gross_exception_amount = sum(ap_total + ar_total + ic_total + accruals_total + je_total)`
  - `net_exception_amount = gross_exception_amount - auto_journals_total_amount`
- Policy thresholds (configurable in code)
  - `MATERIALITY_THRESHOLD = 50,000`, `HIGH_RISK_THRESHOLD = 250,000`
- Risk policy
  - High: `fx_coverage_ok is False` OR `tb_balanced_by_entity is False` OR `net_exception_amount > HIGH_RISK_THRESHOLD`
  - Medium: multiple-path branches (e.g., â‰¥3 sources but net â‰¤ materiality; or â‰¥2 sources with net > materiality)
  - Low: â‰¤2 sources AND net â‰¤ materiality
- Decision
  - `auto_close_eligible` true for low risk; sometimes medium when net â‰¤ materiality
  - `block_close = (risk_level == "high" or not auto_close_eligible)`
- Deterministic rationale summarizing the decision conditions and dollar amounts

### AI

- None in this engine. AI narratives for gatekeeping are generated downstream and do not affect the decision.

## Outputs

- Artifact path: `out/gatekeeping_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "inputs": {"fx_coverage_ok": null, "tb_balanced_by_entity": null, "tb_entity_sums_usd": null},
  "categories": {
    "bank_duplicates": 13, "ap_exceptions": 19, "ar_exceptions": 15, "ic_mismatches": 6,
    "accruals_exceptions": 9, "je_exceptions": 0, "flux_exceptions": 47, "auto_journals_created": 0
  },
  "totals": {
    "ap_exceptions_total_abs": 653977.7,
    "ar_exceptions_total_abs": 2586167.48,
    "ic_mismatch_total_diff_abs": 0.0,
    "accruals_exception_total_usd": 711808.57,
    "je_exceptions_total_abs": null,
    "auto_journals_total_amount": 0.0
  },
  "risk_level": "high",
  "block_close": true,
  "auto_close_eligible": false,
  "gross_exception_amount": 3951953.75,
  "auto_journal_amount": 0.0,
  "net_exception_amount": 3951953.75,
  "materiality_threshold": 50000,
  "deterministic_rationale": "Manual review required: Critical control failures or high-value net exceptions exceed risk tolerance.",
  "referenced_artifacts": {"bank_reconciliation_artifact": ".../bank_reconciliation_run_...json"}
}
```

- Metrics written to `state.metrics`
  - `gatekeeping_risk_level`, `gatekeeping_block_close`, `gatekeeping_auto_close_eligible`
  - `gatekeeping_sources_triggered_count`, `gatekeeping_net_exception_amount`
  - `gatekeeping_deterministic_rationale`, `gatekeeping_artifact`

## Controls

- Deterministic, policy-based decisioning with clear thresholds
- Provenance: EvidenceRef for each referenced artifact; deterministic run with output hash
- Data quality: numeric coercion, robust handling of missing totals
- Audit signals: deterministic rationale, counts, and artifact path captured in messages/tags

\n---\n\n
# Controls Mapping Module

Engine: `src/r2r/engines/controls_mapping.py::controls_mapping(state, audit)`

## Purpose

Deterministically map computed metrics to internal control IDs/families to support audit alignment, compliance narratives, and executive sign-off.

## Where it runs in the graph sequence

- After: Metrics aggregation
- Before: Close Reporting
- Node: `controls_mapping(state, audit)` (deterministic)

## Inputs

- Module inputs (from `state.metrics`)
  - Any computed value can be mapped; focus on TB balance, FX coverage, reconciliation counts, gatekeeping risk, and HITL activity
- Reference data (embedded in code)
  - Known control mappings: metric key -> `{control_id, description}`

## Scope and filters

- Period/entity derived from `state`
- Only known metric keys are included in mapping; unknown keys ignored

## Rules

### Deterministic

- For each known metric key present in `state.metrics`, add a mapping entry with:
  - `control_id`, `description`, `metric_key`, `metric_value`
- Compute `count = number of mapped controls`

### AI

- None in this engine. Any AI compliance narratives are generated downstream and do not affect mapping.

## Outputs

- Artifact path: `out/controls_mapping_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "mappings": [
    {
      "control_id": "TB-001",
      "description": "Trial balance balanced by entity",
      "metric_key": "tb_balanced_by_entity",
      "metric_value": true
    },
    {
      "control_id": "FX-001",
      "description": "FX coverage check completed",
      "metric_key": "fx_coverage_ok",
      "metric_value": true
    },
    {
      "control_id": "GK-001",
      "description": "Gatekeeping risk level",
      "metric_key": "gatekeeping_risk_level",
      "metric_value": "low"
    }
  ],
  "count": 3
}
```

- Metrics written to `state.metrics`
  - `controls_mapped_count`
  - `controls_mapping_artifact`

## Controls

- Deterministic mapping from predefined keys to control IDs
- Provenance: EvidenceRef for the mapping artifact; deterministic run with output hash
- Data quality: ignores unknown keys; includes only present metrics
- Audit signals: artifact path and count are recorded in messages/tags

\n---\n\n
# Close Reporting & Evidence Pack Module

Engine: `src/r2r/engines/close_reporting.py::close_reporting(state, audit)`

## Purpose

Deterministically assemble the period evidence pack: a manifest of all artifacts, an executive summary of status/risk, and an audit log reference. Final hand-off of a complete, drillable record of the close.

## Where it runs in the graph sequence

- After: Controls Mapping
- Final node: `close_reporting(state, audit)` (deterministic)

## Inputs

- Module inputs (from `state.metrics`)
  - Every metrics key ending with `_artifact` is collected as an evidence URI
  - Key status metrics to include in summary: `gatekeeping_risk_level`, `gatekeeping_block_close`, `tb_balanced_by_entity`, `fx_coverage_ok`, counts by module, open HITL cases
- Provenance inputs
  - Audit log path `out/audit_{run_id}.jsonl`

## Scope and filters

- Period/entity come from `state`
- Include only artifact metrics present in `state.metrics` at run completion

## Rules

### Deterministic

- Build `artifacts` by scanning `state.metrics` for keys ending with `_artifact`
- Build `summary` with period, entity, risk, and key module counts
- Emit JSON to `out/close_report_{run_id}.json`

### AI

- None in this engine. Any AI executive narratives are generated elsewhere and do not affect the manifest.

## Outputs

- Artifact path: `out/close_report_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "artifacts": {
    "bank_reconciliation_artifact": ".../bank_reconciliation_run_...json",
    "ap_reconciliation_artifact": ".../ap_reconciliation_run_...json",
    "ar_reconciliation_artifact": ".../ar_reconciliation_run_...json",
    "intercompany_reconciliation_artifact": ".../intercompany_reconciliation_run_...json",
    "accruals_artifact": ".../accruals_run_...json",
    "flux_analysis_artifact": ".../flux_analysis_run_...json",
    "auto_journals_artifact": ".../auto_journals_run_...json",
    "gatekeeping_artifact": ".../gatekeeping_run_...json",
    "controls_mapping_artifact": ".../controls_mapping_run_...json"
  },
  "summary": {
    "gatekeeping_risk_level": "low",
    "gatekeeping_block_close": false,
    "tb_balanced_by_entity": true,
    "fx_coverage_ok": true,
    "exceptions": {
      "bank": 2,
      "ap": 5,
      "ar": 3,
      "ic": 1,
      "accruals": 2,
      "flux": 7
    },
    "auto_journals_created": 4,
    "open_hitl_cases": 0
  },
  "audit_log": ".../audit_run_...jsonl"
}
```

- Metrics written to `state.metrics`
  - `close_report_artifact`

## Controls

- Deterministic manifest built from runtime metrics; no AI in the decision path
- Provenance: EvidenceRef for the report artifact; deterministic run with output hash
- Data quality: include-only present artifacts; tolerate missing optional modules
- Audit signals: executive summary captures close readiness and drill-through URIs

