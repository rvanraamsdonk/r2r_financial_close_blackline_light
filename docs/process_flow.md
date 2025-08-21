# R2R Close Process Flow

This document explains the end-to-end Record-to-Report (R2R) close flow implemented in this repository, focusing on the process sequence, inputs/outputs, and key controls. The flow is deterministic by design.

- Orchestration: `src/r2r/graph.py`
- CLI entrypoint: `scripts/run_close.py`
- State models: `src/r2r/state.py`
- Console output: `src/r2r/console.py`
- AI integration (stub/live): `src/r2r/llm/azure.py`

## High-level sequence

```mermaid
flowchart LR
    A[Orchestrate] --> B[Ingest]
    B --> C[Reconcile]
    C --> D[Match]
    D --> E[Journals]
    E --> F[Variance]
    F --> G[Intercompany]
    G --> H[Gatekeeper]
    H --> I[Compliance]
    I --> J[Audit]
```

The graph runs strictly in sequence to avoid race conditions or result ordering differences between runs. This makes tests stable and output reproducible.

## Node-by-node details

- __Orchestrate (`node_orchestrate`)__
  - Purpose: Initialize the close plan and period context, including simple task scaffolding.
  - Inputs: `CloseState` with `period` and `policy`.
  - Outputs: Populates orchestration metadata (e.g., task list) in state.

- __Ingest (`node_ingest`)__
  - Purpose: Generate deterministic synthetic datasets for entities and accounts via `r2r.data.repo.DataRepo`.
  - Inputs: Policy and requested entities/seed (via CLI or defaults).
  - Outputs: DataFrames/records for balance, AR/AP, bank, intercompany documents stored in state.

- __Reconcile (`node_reconcile`)__
  - Purpose: Run account reconciliations (e.g., cash, AR, AP) against policy thresholds.
  - Inputs: Ingested balances and transactions.
  - Outputs: `ReconResult` entries and evidence references; governance cases are raised later.

- __Match (`node_match`)__
  - Purpose: Perform simple transaction matching (AR to bank) to assess clearing status.
  - Inputs: AR subledger and bank transactions.
  - Outputs: `MatchResult` summary (cleared vs residual) in state.

- __Journals (`node_journals`)__
  - Purpose: Draft journal entries for recurring/known adjustments; generate short descriptions.
  - AI: Uses Azure OpenAI if `R2R_ALLOW_NETWORK=1` and valid `.env` credentials are provided; otherwise returns a deterministic stub.
  - Outputs: `Journal` items queued for approval.

- __Variance (`node_flux`)__
  - Purpose: Flux analysis vs prior period; flag material variances and generate short narratives.
  - AI: Stub/live behavior same as Journals.
  - Outputs: `FluxAlert` items with account deltas and materiality flags.

- __Intercompany (`node_intercompany`)__
  - Purpose: Evaluate intercompany document readiness and netting indicators.
  - Outputs: `ICItem` metrics (e.g., document counts, netting readiness).

- __Gatekeeper (`node_gatekeeper`)__
  - Purpose: Governance and HITL maker/checker approvals across reconciliation certifications and journal postings.
  - Inputs: Reconciliation results and drafted journals.
  - Outputs: `HITLCase` approvals/decisions recorded; `AuditEvent` entries appended.

- __Compliance (`node_compliance`)__
  - Purpose: Period attestation and summary roll-up.
  - Outputs: Compliance attestation event in `AuditEvent` log.

- __Audit (`node_audit`)__
  - Purpose: Finalize the audit trail with counts and key metadata.
  - Outputs: Final audit summary event and termination of the run.

## State and determinism

- __State model__: `CloseState` aggregates lists of domain objects (e.g., recon results, matches, journals, flux alerts, IC metrics, HITL cases, audit events). Models are Pydantic-based and use `Field(default_factory=...)` for lists/dicts to avoid shared mutable defaults.
- __Deterministic execution__: The `StateGraph` in `src/r2r/graph.py` enforces a single linear path to eliminate nondeterminism. Synthetic data generation also uses a seed to make outputs reproducible.

## Inputs and configuration

- __CLI flags__ (optional): `--period`, `--prior`, `--entities`, `--seed` (see `scripts/run_close.py`).
- __Environment__: A root `.env` is always loaded automatically.
  - `AZURE_OPENAI_ENDPOINT`
  - `AZURE_OPENAI_API_KEY`
  - `AZURE_OPENAI_API_VERSION` (e.g., `2024-06-01`)
  - `AZURE_OPENAI_CHAT_DEPLOYMENT`
  - `AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT`
  - `R2R_ALLOW_NETWORK=1` to enable live AI calls (otherwise deterministic stubs)

## Outputs and artifacts

- Console transcript of each step with structured markers (AGENT, MODE, action, details).
- In-memory state with domain objects capturing results and approvals (suitable for serialization if needed).
- Audit trail events summarizing governance and compliance outcomes.

## Happy path vs exceptions

- __Happy path__: Reconciliations produce actionable diffs, matching runs, journals are drafted, flux alerts generated, approvals are granted, compliance attested, and audit finalized.
- __Exceptions__ (simulated): If AI/network is disabled, stubbed outputs are used. Governance still executes with deterministic approvals. In a real system, rejections or threshold breaches would block downstream steps; here they are modeled as approvals to keep the demo flowing.

## Extensibility

- Add a node:
  1. Implement `node_newstage(state, console=...)` in `src/r2r/agents/`.
  2. Register it in `build_graph()` in `src/r2r/graph.py` and insert an edge where appropriate.
  3. Extend `CloseState` in `src/r2r/state.py` if new outputs are required.
  4. Add tests in `tests/` for the new behavior.

## Running the flow

```bash
.venv/bin/python scripts/run_close.py --period 2025-08 --prior 2025-07 --entities 6 --seed 42
```

Tests (deterministic, offline by default):

```bash
.venv/bin/python -m pytest -q
```
