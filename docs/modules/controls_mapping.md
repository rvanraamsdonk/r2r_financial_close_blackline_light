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
