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
- FX translation differences (count): 47  | Target: 0 (≤ entity materiality tolerance)
- Bank duplicate/timing items (count): 2  | Target: 0
- AP/AR exceptions (count): 34             | Target: within tolerance by entity
- Intercompany residuals (total USD): 0.00 | Target: 0 (pair thresholds)
- Accruals exceptions (total USD): 711,808.57 | Target: decreasing trend
- JE exceptions (count): 2                 | Target: 0; p95 approval latency ≤ 2 days
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
