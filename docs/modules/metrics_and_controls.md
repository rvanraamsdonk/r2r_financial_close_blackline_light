# Metrics & Controls Mapping

This document presents the metrics and controls framework in a form suitable for senior audit (SOX/COSO) and Controllership audiences. It defines the KPIs, calculation methods, thresholds/targets, and the evidence trail that enables independent re-performance.

Aligned with engine docs in `docs/modules/`, this framework combines deterministic controls with assistive AI narratives while preserving auditability.

## One‑pager summary and quick links

- Start with the KPI snapshot: `docs/briefs/kpi_dashboard.md`
- How a run unfolds: `docs/modules/functional_modules.md`
- Engine docs quick links: [FX Translation](./fx_translation.md) · [Bank](./bank_reconciliation.md) · [AP/AR](./ap_ar_reconciliation.md) · [Intercompany](./intercompany_reconciliation.md) · [Accruals](./accruals.md) · [JE Lifecycle](./je_lifecycle.md) · [Flux](./flux_analysis.md) · [Gatekeeping](./gatekeeping.md) · [Controls Mapping](./controls_mapping.md) · [Close Reporting](./close_reporting.md)

## 1) Executive KPIs (targets and tolerances)

- fx_translation_diff_count — Target: 0; Tolerance: ≤ entity materiality (USD)
- bank_duplicates_count — Target: 0; Red flag if > 0 for high-risk entities/accounts
- ap_exceptions_count / ar_exceptions_count — Target: within tolerance by entity; trends decreasing
- ic_mismatch_total_diff_abs — Target: 0; Floor-based thresholding per entity pair
- accruals_exception_total_usd — Target: decreasing trend; flagged reversals corrected next period
- je_exceptions_count — Target: 0; je_approval_latency_p95_days — Target: ≤ 2 business days
- flux_exceptions_count — Target: within entity materiality band; explanations attached
- gatekeeping_risk_level — Target: low; block_close — Target: false; auto_close_eligible — Target: true
- auto_journals_count / auto_journals_total_usd — Target: immaterial and bounded (below thresholds)
- hitl_open_cases / hitl_sla_breaches — Target: 0
- ai_cost_usd / ai_latency_ms — Target: within budget and SLOs; assistive only
- reproducibility_hash (code/config) — Target: stable across reruns with same inputs

## 2) Metric dictionary (definitions and evidence)

For each metric, we specify key, definition, formula, scope, target/threshold, frequency, owner, and evidence. Evidence always includes the artifact path and row-level `input_row_ids` when applicable.

### 2.1 fx_translation_diff_count
- Definition: Number of TB rows where abs(computed_usd - reported_usd) > tolerance (default $0.01). See engine: [FX Translation](./fx_translation.md)
- Formula: count of `rows[].is_exception == true` in `out/fx_translation_{run_id}.json`
- Scope: period = `state.period`, entity = `state.entity|ALL`
- Target/Threshold: Target 0; tolerance ≤ entity materiality for presentation
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
- Target/Threshold: je_exceptions_count = 0; p95 latency ≤ 2 business days
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
  - Medium risk if: multiple exception sources with net > materiality (but ≤ high risk)
  - Low risk if: ≤ 2 sources and net ≤ materiality
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
- Exception waterfall: gross → auto-JE net → gatekeeping net
- JE approval latency distribution (p50/p95)
- Coverage dashboards and quarter-over-quarter trends
