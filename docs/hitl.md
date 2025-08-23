# HITL Case Management

Purpose: deterministically open Human-In-The-Loop (HITL) cases for categories that require manual review based on prior deterministic findings and Gatekeeping policy.

Placement: the `hitl` node runs after `gatekeeping` and before `metrics` in the LangGraph workflow.

## Inputs

- From `state.metrics`:
  - gatekeeping_block_close (bool)
  - Counts and artifacts for exception categories:
    - bank_duplicates_count, bank_reconciliation_artifact
    - ap_exceptions_count, ap_reconciliation_artifact
    - ar_exceptions_count, ar_reconciliation_artifact
    - ic_mismatch_count, intercompany_reconciliation_artifact
    - accruals_exception_count, accruals_artifact
    - je_exceptions_count, je_lifecycle_artifact
    - flux_exceptions_count, flux_analysis_artifact

## Logic

- Open one case per category with count > 0.
- Severity heuristic:
  - high if gatekeeping_block_close is True
  - medium if any category has count > 0
  - low otherwise
- If block_close is True and no specific category had count > 0, open a general Gatekeeping case referencing all artifacts.

## Outputs

- cases file: `out/cases_<runid>.json` with a list of case objects
- manifest: `out/cases_manifest_<runid>.json` with run context and cases URI
- Each case fields: id, created_at, period, entity, source, severity, title, description, evidence_uris, status, assignee, resolution_notes, resolved_at

## Provenance

- Append `EvidenceRef` for the cases file
- Append `DeterministicRun(function_name="open_hitl_cases")` with a stable hash over payload
- Add deterministic message and tag for audit readability

## Metrics Enriched

- hitl_cases_open_count
- hitl_cases_artifact
- hitl_manifest_artifact

## Usage

- Runs automatically; no CLI flags required
- Review cases JSON and drill into `evidence_uris` for supporting artifacts
