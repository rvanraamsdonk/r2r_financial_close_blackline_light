# AI vs Deterministic Transparency

We make AI participation explicit, measurable, and auditable.

## Labels
- [DET]: produced by deterministic computation only
- [AI]: produced by an AI assistant (no balances set)
- [HYBRID]: deterministic core + AI narrative/assist

## Provenance
- EvidenceRef: id, type, uri/hash, input_row_ids, timestamp
- DeterministicRun: function_name, code_hash, params, input_row_ids, output_hash
- PromptRun: prompt_id/hash, model/version, temperature, tokens_in/out, latency_ms, cost, redaction, confidence, citation_row_ids
- LineageLink: output_id → input_row_ids, fx_rate_ids, je_ids, prompt_ids
- OutputTag: method_type ∈ {DET, AI, HYBRID}, rationale, materiality_band

## Policy Toggles
- `ai_mode`: off | assist | strict
- Redaction: on by default with reversible de-redaction for evidence review
- Allowlist: AI-eligible tasks (matching suggestions, narratives, risk/scoping explanations)

## Display & Drill-through
- Every line item shows [DET]/[AI]/[HYBRID]
- Evidence links open data rows, rates, computations, prompts, model metrics
- Prompts stored with hashes; model name/version, cost, latency, confidence always displayed for [AI]
