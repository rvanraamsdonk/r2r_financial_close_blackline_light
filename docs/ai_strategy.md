# AI Strategy

This system is AI-first: AI is used for explanation, summarization, and reasoning, while deterministic (DET) code is used for core, reliability-critical calculations.

## Principles

- AI-first for narratives, suggestions, and reasoning.
- Ground all AI to computed data and artifacts with explicit citations.
- Record visible provenance for each AI call.
- Enforce JSON schemas where possible; degrade gracefully on failures.
- Track cost/latency, never block the run on AI failure.

## Cross-cutting Infrastructure

- Modes: `ai_mode`: off | assist | strict.
- Provenance: append `prompt_runs` with inputs hash, timestamps, artifact URI.
- Evidence: write AI artifacts to `out/` and log `EvidenceRef` in audit.
- Metrics: `ai_*_artifact` keys per step; optional cost/latency in future.

## Module AI Artifacts (Phase 1)

- Validation: `validation_ai_<runid>.json` (root_causes, remediations, citations).
- AP/AR: `ap_ar_ai_suggestions_<runid>.json` (matches, unresolved_summary, citations).
- Intercompany: `ic_ai_match_proposals_<runid>.json` (candidate_pairs, je_proposals, citations).
- Flux: `flux_ai_narratives_<runid>.json` (narratives, citations).
- HITL: `hitl_ai_case_summaries_<runid>.json` (case_summaries, next_actions, citations).

## Workflow Integration

AI nodes are placed immediately after their corresponding deterministic nodes in `src/r2r/graph.py`:

- validate -> ai_validation -> fx
- ar_recon -> ai_ap_ar -> ic_recon
- ic_recon -> ai_ic -> accruals
- flux_analysis -> ai_flux -> email_evidence
- hitl -> ai_hitl -> metrics

FX has an existing AI narrative node `ai_fx` after `fx` and before `fx_translation`.

## Guardrails & Credibility

- No compliance claims (e.g., SOX) unless explicitly computed/validated.
- All narratives must include citations to artifacts (URIs) and metrics.
- Strict mode requires schema-valid outputs; otherwise log a warning and continue.

## Next Steps

- Add prompt templates, external LLM integration, caching, and cost/latency tracking.
- Extend docs with per-module AI sections and examples.
