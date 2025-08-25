# Close Reporting & Evidence Pack (Step 13)

Purpose: deterministically assemble a period evidence pack manifest with a concise summary for executives/auditors and references to all artifacts and the audit log.

Placement: the `close_reporting` node runs after `controls_mapping` as the final step of the LangGraph workflow.

## Inputs

- From `state.metrics`: collects every key ending with `_artifact` as evidence URIs.
- Key status metrics included in the summary: risk level, block_close, open HITL cases, TB balanced flag, FX coverage.

## Logic

- Build an `artifacts` map from metrics keys ending in `_artifact`.
- Create a `summary` section with period, entity, risk and key counts.
- Emit `out/close_report_<runid>.json` with `artifacts`, `summary`, and `audit_log`.

## Outputs

- Artifact: `close_report_<runid>.json` (manifest + executive summary).
- Metrics: `close_report_artifact` path.

## Provenance

- Appends `EvidenceRef` for the report artifact.
- Appends `DeterministicRun(function_name="close_reporting")` with stable hash.

## Usage

- Runs automatically in the workflow; no CLI flags required.
- Open the JSON to navigate artifacts and audit log.
