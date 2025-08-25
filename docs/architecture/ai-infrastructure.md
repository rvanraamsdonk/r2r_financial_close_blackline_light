# AI Infrastructure

This document summarizes the AI infra used across modules.

## Caching and Input Hashing

- Inputs are summarized into a stable dict and hashed with SHA256 via `src/r2r/ai/infra.py:compute_inputs_hash()`.
- Artifacts are cached in `out/ai_cache/` using `<kind>_<run_id>_<hash>.json` via `with_cache()`.

## Latency Metrics

- Execution time is measured with `time_call()` and recorded as `ai_<kind>_latency_ms`.

## Provenance

- Every AI helper records a prompt run entry into `state.prompt_runs` and audit log with artifact URI, hash, and cached flag.

## Strict Schema Validation

- Pydantic models in `src/r2r/ai/schemas.py` define expected payloads for each AI helper.
- When `state.ai_mode == "strict"`, payloads are validated; warnings are appended on failure.

## Prompt Templates

- Placeholder prompt templates live in `src/r2r/ai/templates/` for each AI helper.
- These are non-executing documentation aids to standardize prompting.

## Token & Cost Metrics

- Token estimation is provider-agnostic: `estimate_tokens(payload_bytes)` divides JSON byte length by 4 as a heuristic.
- Cost estimation defaults to 0.0 USD in offline mode; hook in provider rates when integrating real APIs via `estimate_cost_usd(tokens, rate_per_1k)`.
- Environment-driven rate: set `R2R_AI_RATE_PER_1K` to apply a USD cost per 1,000 tokens across all AI helpers. If unset/invalid, cost remains `0.0`.
- Per-AI helper metrics are recorded in `state.metrics` and audit log as:
  - `ai_<kind>_tokens`
  - `ai_<kind>_cost_usd`
  - `ai_<kind>_latency_ms`
- Audit log writes paired records for each AI call:
  - `{"type": "ai_output", "kind": "<kind>", "artifact": "...", "generated_at": "..."}`
  - `{"type": "ai_metrics", "kind": "<kind>", "tokens": N, "cost_usd": X}`

## CLI: Inspect AI Artifacts and Metrics

Use `scripts/drill_through.py list-ai` to list AI artifacts and associated metrics from the audit log.

Examples (run from repo root, in venv):

```bash
.venv/bin/python scripts/drill_through.py list-ai
.venv/bin/python scripts/drill_through.py list-ai --json
.venv/bin/python scripts/drill_through.py list-ai --run 20250823T090910Z
```

JSON output includes enriched fields per entry: `ai_<kind>_tokens`, `ai_<kind>_cost_usd`.

### Aggregated totals (`--sum`)

To report aggregate tokens and cost across the run:

```bash
.venv/bin/python scripts/drill_through.py list-ai --sum
.venv/bin/python scripts/drill_through.py list-ai --json --sum
```

- Text mode appends a total line: `"[AI] TOTAL tokens=<N> cost_usd=<X>"`.
- JSON `--sum` returns an object: `{ "artifacts": [...], "summary": { "total_tokens": N, "total_cost_usd": X } }`.

Example to set a non-zero cost rate during a run:

```bash
export R2R_AI_RATE_PER_1K=0.5
.venv/bin/python scripts/run_close.py
.venv/bin/python scripts/drill_through.py list-ai --sum
```
