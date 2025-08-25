# Provenance & Evidence Schema

This schema ensures every artifact is traceable.

## EvidenceRef
- `id`: stable identifier
- `type`: {file, table, prompt, chart, calc}
- `uri_or_hash`: path or content hash
- `input_row_ids`: list of source row identifiers (if applicable)
- `timestamp`: ISO8601

## DeterministicRun
- `function_name`: e.g., engines.fx.translate_balances
- `code_hash`: git/file hash snapshot
- `params`: json of the inputs/thresholds used
- `input_row_ids`: rows that fed the computation
- `output_hash`: hash of computed result

## PromptRun
- `prompt_id`: stable id + content hash
- `model`: name/version
- `temperature`: numeric
- `tokens_in` / `tokens_out`: integers
- `latency_ms`: integer
- `cost`: numeric
- `redaction`: on|off (fields redacted)
- `confidence`: numeric [0..1] or band
- `citation_row_ids`: rows cited in the response

## LineageLink
- `output_id` → references `input_row_ids`, `fx_rate_ids`, `je_ids`, `prompt_ids`

## OutputTag
- `method_type`: DET | AI | HYBRID
- `rationale`: human-readable summary
- `materiality_band`: below | near | above (threshold)

All structures will be exported in JSON alongside the Close Pack for independent verification.
