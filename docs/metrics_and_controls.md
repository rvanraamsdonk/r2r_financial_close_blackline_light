# Metrics & Controls Mapping

## Core Metrics
- Coverage % by control area (AP/AR, bank, IC, flux)
- Exceptions: count and $ by class and materiality band
- IC netting and residual imbalances
- Recon statuses by account
- JE lifecycle: counts, amounts, approval latency, reversals scheduled
- AI metrics: cost, tokens, latency, confidence; usage by task
- Reproducibility: code/config hash, rerun stability

## Controls Mapping (SOX alignment)
- Bank reconciliation: pass/fail + evidence
- Subledger reconciliations (AP/AR): tie-outs, unmatched listings, cutoff tests
- Intercompany reconciliation: match policy, imbalances, eliminations/true-ups
- Flux review: materiality thresholds, explanations with citations
- Journal entries: four-eyes approvals, SoD, simulation, posting evidence
- Period close gatekeeping: readiness thresholds and rationale

Each control line item links to evidence (rows, computations, prompts) and displays [DET]/[AI] tags.
