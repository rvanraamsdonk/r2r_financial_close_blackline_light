# Period Initialization & Governance [DET]

Purpose: deterministically lock scope and snapshot governance for the run with audit-ready evidence.

Key actions:

- Load `data/lite/entities.csv` and `data/lite/chart_of_accounts.csv`; load period TB if present
- Compute materiality thresholds by entity: 0.5% of absolute TB sum with $1,000 floor
- Persist run snapshot JSON with dataset hashes, scope, policy flags, and thresholds
- Log evidence references and deterministic run with output hash

Function: `r2r.engines.period.period_init(state, audit)`

Inputs:

- `state.period` (YYYY-MM), `state.entity` (scope), `state.ai_mode`
- CSVs: `entities.csv`, `chart_of_accounts.csv`, `trial_balance_<YYYY_MM>.csv` (optional)

Outputs:

- Artifact: `out/period_init_<run_id>.json`
- Evidence: URIs for entities, COA, and TB (if present)
- Deterministic log with `output_hash` = hash(snapshot)
- Messages/tags: `[DET] Period initialized ...` and DET tag rationale
- Metrics: `period_locked`, `materiality_thresholds_usd`, `period_init_artifact`

Audit/provenance:

- Evidence is appended with timestamps; deterministic run recorded with parameters and artifact path
- No AI influence; pure deterministic setup step

Notes:

- Materiality method kept simple and transparent; can be replaced/configured in future
- Works seamlessly with the existing LangGraph flow; executes first
