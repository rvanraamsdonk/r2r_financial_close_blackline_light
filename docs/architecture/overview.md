# Architecture Overview

- Orchestration: LangGraph DAG of agents (ingestion → FX → TB integrity → SL/Bank recs → IC → accruals → flux → JE lifecycle → gatekeeper/HITL → reporting)
- Deterministic engines: FX, tie-outs, bank rec, IC math, accrual math, flux
- AI services: reasoning, matching suggestions, narratives, risk summarization (assistive only)
- State: `R2RState` with datasets, exceptions, JE proposals, metrics, evidence
- Provenance: `EvidenceRef`, `DeterministicRun`, `PromptRun`, `LineageLink`, `OutputTag`
- Audit: append-only log; approvals; decisions; SLA timers; users
- Metrics: coverage, exceptions $, recon status, IC netting, JE latency, AI cost/latency, reproducibility
- CLI: simple flags with `ai_mode`; outputs labeled [DET]/[AI]/[HYBRID]

This design emphasizes reliability, policy alignment, and transparent AI assistance.
