# Gatekeeping & Risk Aggregation

Purpose: deterministically aggregate exception signals and key controls to compute a simple overall risk level and a block/allow flag before final metrics and reporting.

Placement: the `gatekeeping` node runs after unstructured `email_evidence` and before `metrics` in the LangGraph workflow.

## Inputs

- From `state.metrics` (produced by earlier deterministic engines):
  - fx_coverage_ok
  - tb_balanced_by_entity, tb_entity_sums_usd
  - bank_duplicates_count
  - ap_exceptions_count, ap_exceptions_total_abs
  - ar_exceptions_count, ar_exceptions_total_abs
  - ic_mismatch_count, ic_mismatch_total_diff_abs
  - accruals_exception_count, accruals_exception_total_usd
  - je_exceptions_count, je_exceptions_total_abs
  - flux_exceptions_count

- Referenced artifacts: any metrics key ending with `_artifact` (URIs to JSON/CSV outputs).

## Logic

- Count how many exception categories have count > 0.
- Risk policy:
  - High if: fx_coverage_ok is False OR tb_balanced_by_entity is False OR sources_triggered >= 3
  - Medium if: sources_triggered in {1, 2}
  - Low if: sources_triggered == 0
- Block close when risk_level == "high".

## Outputs

- Artifact: `out/gatekeeping_<runid>.json` containing:
  - generated_at, period, entity_scope
  - inputs snapshot (coverage and TB status)
  - categories (per-category exception counts)
  - totals (optional absolute totals where available)
  - risk_level (low|medium|high)
  - block_close (bool)
  - referenced_artifacts (URIs used as evidence)

## Provenance

- For each referenced artifact, append an `EvidenceRef` (type=json, uri=`artifact path`).
- Append a `DeterministicRun(function_name="gatekeeping_aggregate")` with output hash over the payload.
- Add a deterministic message and tag for audit readability.

## Metrics Enriched

- gatekeeping_risk_level
- gatekeeping_block_close
- gatekeeping_sources_triggered_count
- gatekeeping_artifact

## Usage

- Runs automatically in the LangGraph workflow, no CLI flags required.
- See `out/gatekeeping_<runid>.json` for the aggregated view and drill-through URIs.
