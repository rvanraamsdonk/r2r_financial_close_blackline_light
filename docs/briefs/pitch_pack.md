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

- FX Translation — `docs/modules/fx_translation.md`
- Bank Reconciliation — `docs/modules/bank_reconciliation.md`
- AP & AR Reconciliation — `docs/modules/ap_ar_reconciliation.md`
- Intercompany Reconciliation — `docs/modules/intercompany_reconciliation.md`
- Accruals — `docs/modules/accruals.md`
- JE Lifecycle — `docs/modules/je_lifecycle.md`
- Flux Analysis — `docs/modules/flux_analysis.md`
- Auto Journal Creation — `docs/modules/journal_entries.md`
- Gatekeeping — `docs/modules/gatekeeping.md`
- Controls Mapping — `docs/modules/controls_mapping.md`
- Close Reporting — `docs/modules/close_reporting.md`

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

- JE Platform & UI workflows — `docs/modules/journal_entries.md` (appendix section)
- Data paths (inputs/outputs) — `data/` and `out/` tree; see artifacts listed within each engine doc
- Testing — unit/integration tests under `tests/`

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
