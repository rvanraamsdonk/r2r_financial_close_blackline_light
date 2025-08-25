# Brief: Visible AI + Deterministic Close

We build a deterministic, policy-aligned close with AI visibly assisting where it adds expert value. Every output indicates its method: [DET] (computed), [AI] (assistive), or [HYBRID]. All items link to evidence: source rows, FX rates, computations, prompts, model metrics, and configuration/code hashes. No hard-coded strings; everything is derived from real inputs under `data/lite/`.

- Framework: Python + LangGraph
- Simplicity: single-command CLI; comprehensive `/docs/`
- Governance: materiality by entity/account class; four-eyes approvals; SoD
- Reproducibility: immutable run ID, config snapshot, code hash; idempotent reruns

## Guardrails
- AI never sets balances; numbers are deterministic.
- AI used for explanations, fuzzy match suggestions, risk narratives, and reviewer aids.
- Policy toggles: `ai_mode` (off | assist | strict), redaction, allowlist of AI-eligible tasks.
- Full provenance exported with the Close Pack.
