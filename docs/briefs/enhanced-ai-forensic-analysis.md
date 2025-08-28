# Enhanced AI-Powered Forensic Analysis System

## Executive Summary
This document defines how we evolve from mostly deterministic rules to an AI-dominant forensic detection approach. Target split: ~30% deterministic signal extraction, ~70% AI pattern analysis, risk scoring, and narratives. The design keeps explainability, provenance, and reproducibility suitable for Big 4 scrutiny.

## Objectives
- Replace brittle rule flags with AI-driven pattern recognition.
- Provide calibrated confidence, risk levels, and business impact.
- Preserve auditability: inputs hash, prompts, outputs, and citations.
- Minimize false positives via context-aware analysis.

## Current State (Baseline)
- Deterministic checks in `src/r2r/engines/ap_ar_recon.py` detect simple patterns (duplicates, round-dollar, weekends, split txns, channel stuffing, credit memo abuse, related party).
- AI currently used mostly for rationale text.

Limitations: binary thresholds, low context, limited sequence/statistical analysis, no calibrated confidence.

## Target Architecture (AI-Dominant)
- Deterministic layer (signals): fast, local computations to extract structured features per transaction/batch.
- AI layer (analysis): LLM+templates evaluate multi-factor evidence, context, and history to classify, score risk, and generate rationales and next actions.
- Evidence & provenance: store feature snapshots, input shards, prompts, model metadata, output JSON, token/cost metrics.

### Layer 1: Deterministic Signal Extraction (~30%)
Extract features that are objective and cheap to compute:
- Amount features: round-dollar flags, clustering stats, sigma from peer group.
- Temporal: weekend/holiday, period-end proximity, inter-transaction gaps.
- Counterparty: new vendor age, payment velocity, name similarity candidates.
- Sequence: splitting heuristics, approval path changes, invoice sequencing.
- Ledger context: GL coding consistency, entity/currency, IC patterns.

Output: compact feature frames per transaction with stable IDs and citations to source rows.

### Layer 2: AI Forensic Analysis (~70%)
LLM consumes batches of feature-enriched transactions:
- Multi-signal reasoning across time and counterparties.
- Context-aware risk (industry norms, vendor history, approval workflows).
- Confidence calibration and risk level assignment.
- Narrative with cited evidence and recommended actions.

## AI Response Schema (JSON)
```json
{
  "forensic_findings": [
    {
      "transaction_id": "AP_001234",
      "risk_category": "duplicate_payment|round_dollar|vendor_fraud|timing_anomaly|split_transaction|channel_stuffing|credit_memo_abuse|related_party|bank_kiting",
      "confidence_score": 0.0,
      "risk_level": "low|medium|high|critical",
      "evidence": {
        "primary_indicators": ["..."],
        "supporting_factors": ["..."],
        "statistical_deviation": "..."
      },
      "business_impact": {
        "financial_exposure": 0.0,
        "compliance_risk": "low|medium|high",
        "audit_attention_required": true
      },
      "narrative": "...",
      "recommended_actions": ["..."],
      "similar_patterns": ["..."]
    }
  ],
  "batch_summary": {
    "total_transactions_analyzed": 0,
    "high_risk_count": 0,
    "total_financial_exposure": 0.0,
    "pattern_clusters": ["..."],
    "overall_risk_assessment": "low|medium|high|critical"
  },
  "methodology": {
    "analysis_techniques": ["LLM pattern reasoning", "statistical baselines"],
    "confidence_factors": ["signal strength", "consistency", "context fit"],
    "limitations": ["data gaps", "ambiguous counterparties"]
  }
}
```

## Detection Categories and AI Enhancements
- Duplicate payments: fuzzy vendor similarity, amount clustering, temporal proximity, approval path sameness.
- Round dollar: deviation from peer distributions, threshold-avoidance patterns, context (contract vs expense).
- Vendor fraud: new vendor velocity curves, related-party signals, address/IBAN overlaps, abnormal GL coding.
- Timing anomalies: weekend/holiday justification, period-end clustering, manual-entry fingerprints.
- Split transactions: amount decomposition and sequence timing near approval limits.
- AR patterns: channel stuffing (EOM spikes + extended terms), credit memo abuse (negative clusters + memo semantics), related party.
- Bank: kiting (round-trip timing, self-transfers), counterparty risk, velocity spikes.

## Prompting and Templates
- New template: `src/r2r/ai/templates/forensic_analysis.md` (rendered by `src/r2r/ai/infra.py` via Jinja) with strict JSON policy.
- Inputs: period, entity, compact feature frames, citations.
- Guardrails: small, bounded batches; temperature ~0.2; schema validation.

## Governance & Explainability
- Cache with inputs hash (see `src/r2r/ai/infra.py:compute_inputs_hash`).
- Persist prompts/outputs with run IDs; include model, token counts, and cost.
- Deterministic replays via fixed seeds and frozen feature snapshots.

## Rollout Plan
1. Add feature extraction utilities (deterministic) in `src/r2r/engines/common/features.py` and call from AP/AR/Bank engines.
2. Add forensic AI module entrypoint `ForensicAIAnalyzer` in `src/r2r/ai/modules.py` with caching and JSON schema validation.
3. Wire engines to send compact batches to AI and merge findings back into exceptions with confidence and narratives.
4. Surface in GUI: confidence badges, risk levels, evidence chips, exposure totals.

## Metrics & Targets
- False positive reduction vs rules: >70%.
- High-confidence precision: >95%.
- Coverage: 100% of transactions scored; top-N prioritized.
- Latency: <2s per 50-transaction batch on default model.

## Security & Cost
- Use repo `.env` for API config; default non-zero rate to ensure real calls.
- Rate-limit and batch to control spend; persist cache to reuse.

## Appendix: Deterministic Signals (non-exhaustive)
- round_dollar_flag, round_dollar_magnitude
- amount_sigma, peer_group_mean/var
- is_weekend, days_to_period_end, eom_spike_bucket
- vendor_age_days, payments_30d, velocity_index
- name_similarity_candidates, approver_overlap
- split_candidate_group_id, split_gap_seconds
- credit_memo_cluster_size, related_party_hint
- bank_counterparty_risk_score, self_transfer_cycle_hint
