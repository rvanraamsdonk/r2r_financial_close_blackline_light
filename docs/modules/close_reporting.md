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
