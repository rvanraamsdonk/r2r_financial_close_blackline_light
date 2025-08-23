# Controls Mapping (Step 14)

Purpose: deterministically map computed metrics to internal control IDs/families to support audit alignment and compliance narratives.

Placement: the `controls_mapping` node runs after `metrics` and before `close_reporting` in the LangGraph workflow.

## Inputs

- From `state.metrics`: any computed values; mappings are created for known keys (TB, FX, reconciliations, gatekeeping, HITL).

## Logic

- For each known metric key present, add a mapping entry: control_id, description, and the metric value.
- Produces `out/controls_mapping_<runid>.json` with a `mappings` object and `count`.

## Outputs

- Artifact: `controls_mapping_<runid>.json` with mappings.
- Metrics: `controls_mapped_count`, `controls_mapping_artifact`.

## Provenance

- Appends `EvidenceRef` for the mapping artifact.
- Appends `DeterministicRun(function_name="controls_mapping")` with stable hash over payload.

## Usage

- Runs automatically as part of the workflow; no CLI flags required.
