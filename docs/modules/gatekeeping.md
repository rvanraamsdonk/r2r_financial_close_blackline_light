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
  - Medium: multiple-path branches (e.g., ≥3 sources but net ≤ materiality; or ≥2 sources with net > materiality)
  - Low: ≤2 sources AND net ≤ materiality
- Decision
  - `auto_close_eligible` true for low risk; sometimes medium when net ≤ materiality
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
