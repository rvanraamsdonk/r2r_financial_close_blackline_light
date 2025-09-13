# Intercompany Reconciliation Module

Engine: `src/r2r/engines/intercompany_recon.py::intercompany_reconciliation(state, audit)`

## Purpose

Identify intercompany mismatches and forensic risk patterns deterministically, applying entity-pair materiality thresholds. Emit assistive candidate hints and deterministic true-up proposals.

## Where it runs in the graph sequence

- After: AR reconciliation
- Before: Accruals and Flux Analysis
- Node: `intercompany_reconciliation(state, audit)` (deterministic)

## Inputs

- Data inputs
  - File(s): `data/subledgers/intercompany/ic_transactions_*.csv`
  - Loaded via: `load_intercompany(data_path, period)`
  - Required columns: `doc_id, entity_src, entity_dst, amount_src, amount_dst, currency, transaction_type, description, date`
- Module inputs (from `state.metrics`)
  - `materiality_thresholds_usd` by entity (optional)
  - Defaults: `$1,000` floor when thresholds missing
  - `state.period`
- Provenance inputs
  - Source CSV URI, `input_row_ids` = flagged `doc_id`s

## Scope and filters

- Period scope: loader filters to current `state.period`
- Entity pairs: all in file; optional src/dst filters can be added in loader if needed
- Deterministic normalization of numeric fields; safe string handling

## Rules

### Deterministic

- Mismatch detection
  - `diff_abs = |amount_src - amount_dst|`
  - Threshold per pair: `max(materiality[src], materiality[dst])` if available, else `$1,000`
  - Flag when `diff_abs > threshold` → `reason = ic_amount_mismatch_above_threshold`
- Forensic patterns
  - Round-dollar anomaly: `amount_src % 1000 == 0 and amount_src >= 10000` → `ic_round_dollar_anomaly`
  - Transfer pricing risk: `"management fee" in transaction_type.lower()` and `amount_src > 50000` → `ic_transfer_pricing_risk`
  - Structuring pattern: ≥3 small transactions (`amount_src < 10000`) from same pair on same `date` → `ic_structuring_pattern`
- Candidate hints (assistive only)
  - Up to 3 peers within same pair/currency with closest `diff_abs`, deterministically scored and sorted
- True-up proposals
  - For each exception, deterministic proposal adjusting destination to match source:
    - `proposal_type = "ic_true_up"`, `adjustment_usd`, `simulated_dst_after`, `balanced_after`, `narrative`
- Deterministic rationale per exception
  - `deterministic_rationale` labeled `[DET]` or `[FORENSIC]` with doc_id, entities, diffs, thresholds

### AI

- None in this engine. AI-based IC matching/elimination proposals are generated downstream and do not influence deterministic detection here.

## Outputs

- Artifact path: `out/intercompany_reconciliation_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "rules": {
    "mismatch_rule": "flag |amount_src-amount_dst| > max(materiality[src], materiality[dst])",
    "default_floor_usd": 1000.0
  },
  "exceptions": [
    {
      "doc_id": "IC-001",
      "entity_src": "ENT100",
      "entity_dst": "ENT101",
      "amount_src": 75000.0,
      "amount_dst": 75000.0,
      "diff_abs": 0.0,
      "threshold": 50034.04,
      "reason": "ic_round_dollar_anomaly",
      "deterministic_rationale": "[FORENSIC] Round dollar anomaly: IC-001 for $75,000 ENT100->ENT101"
    }
  ],
  "proposals": [
    {
      "proposal_type": "ic_true_up",
      "doc_id": "IC-002",
      "entity_src": "ENT200",
      "entity_dst": "ENT201",
      "adjustment_usd": -1500.0,
      "simulated_dst_after": 98500.0,
      "balanced_after": true,
      "narrative": "Adjust destination to match source (delta -1,500.00 USD)"
    }
  ],
  "summary": {
    "count": 6,
    "total_diff_abs": 125000.0,
    "by_pair_diff_abs": {"ENT100->ENT101": 75000.0},
    "proposal_count": 3
  }
}
```

- Metrics written to `state.metrics`
  - `ic_mismatch_count`, `ic_mismatch_total_diff_abs`, `ic_mismatch_by_pair`, `intercompany_reconciliation_artifact`

## Controls

- Deterministic mismatch and forensic rule set; thresholds governed by `period_init`
- Provenance: EvidenceRef with CSV URI and row-level `input_row_ids`
- DeterministicRun with parameters and output hash
- Assistive candidates are non-binding and clearly labeled
- Audit messages include counts and artifact path; [DET]/[FORENSIC] rationales for each exception
