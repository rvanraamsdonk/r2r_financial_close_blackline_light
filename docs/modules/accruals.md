# Accruals Module

Engine: `src/r2r/engines/accruals.py`

## Purpose

Detect accruals that should reverse and those with missing or misaligned reversal dates in the next period. Emit a deterministic exceptions artifact with reversal proposals and auditable metrics for downstream gatekeeping and reporting.

## Where it runs in the graph sequence

- After: `tb_diagnostics`
- Before: `metrics`
- Node: `accruals(state, audit)` (deterministic)

## Inputs

- Data inputs
  - File: `data/supporting/accruals.csv`
  - Columns:
    - `entity`: string
    - `accrual_id`: string
    - `description`: string
    - `amount_local`: number
    - `amount_usd`: number
    - `currency`: string
    - `status`: string (e.g., `Active`, `Should Reverse`)
    - `accrual_date`: `YYYY-MM-DD`
    - `reversal_date`: `YYYY-MM-DD` (may be blank)
    - `notes`: string
- Module inputs (from `state` / other nodes)
  - `state.period` (e.g., `2025-08`)
  - `state.entity` (e.g., `ALL` or specific entity)
- Provenance inputs
  - Source CSV URI
  - `input_row_ids` constructed as `<entity>|<accrual_id>` for flagged rows

## Scope and filters

- Period scope: rows where `accrual_date` starts with `state.period` (`YYYY-MM`)
- Entity scope: if `state.entity != "ALL"`, filter to that entity
- Robust parsing:
  - Treat empty/NaN text as empty strings before string ops
  - Coerce invalid dates to `None`
- Next period is computed deterministically from `state.period` (`YYYY-MM` → `YYYY-MM`)

## Rules

### Deterministic

- Reverse-required
  - If `status == "Should Reverse"` → `reason = explicit_should_reverse`
- Missing/misaligned reversal date
  - If `status in {"Active", "Should Reverse"}` AND `reversal_date` not in next period → `reason = missing_or_misaligned_reversal_date`
- Proposal generation (deterministic)
  - For every exception, emit proposal:
    - `proposal_type = "accrual_reversal"`
    - `proposed_period = next_period`
    - `amount_usd = -amount_usd` (rounded)
    - `narrative`: concise description
    - `deterministic_rationale`: `[DET] Reverse {accrual_id} for {entity} in {next_period}: amount_usd={amt}`

### AI

- None. The accruals engine is fully deterministic. Any AI commentary occurs in downstream AI modules and does not affect calculations.

## Outputs

- Artifact path: `out/accruals_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "next_period": "2025-09",
  "entity_scope": "ALL",
  "exceptions": [
    {
      "entity": "ENT100",
      "accrual_id": "A-123",
      "description": "Payroll accrual",
      "amount_usd": 1200.0,
      "currency": "USD",
      "status": "Should Reverse",
      "accrual_date": "2025-08-28",
      "reversal_date": "",
      "notes": "",
      "reason": "explicit_should_reverse"
    },
    {
      "entity": "ENT200",
      "accrual_id": "A-456",
      "description": "Utilities accrual",
      "amount_usd": 800.0,
      "currency": "USD",
      "status": "Active",
      "accrual_date": "2025-08-10",
      "reversal_date": "2025-10-01",
      "notes": "",
      "reason": "missing_or_misaligned_reversal_date"
    }
  ],
  "proposals": [
    {
      "proposal_type": "accrual_reversal",
      "entity": "ENT100",
      "accrual_id": "A-123",
      "proposed_period": "2025-09",
      "amount_usd": -1200.0,
      "narrative": "Reverse A-123 in 2025-09 to offset August accrual.",
      "deterministic_rationale": "[DET] Reverse A-123 for ENT100 in 2025-09: amount_usd=-1200.00."
    }
  ],
  "summary": {
    "count": 2,
    "total_usd": 2000.0,
    "by_entity": {
      "ENT100": 1200.0,
      "ENT200": 800.0
    },
    "proposal_count": 1,
    "roll_forward": {
      "next_period": "2025-09",
      "proposed_reversals_total_usd": -1200.0,
      "proposed_reversals_by_entity": {
        "ENT100": -1200.0
      }
    }
  }
}
```

- Metrics written to `state.metrics`
  - `accruals_exception_count`: integer
  - `accruals_exception_total_usd`: number
  - `accruals_exception_by_entity`: map
  - `accruals_artifact`: string (artifact path)

## Controls

- Deterministic and reproducible
  - Fixed period/entity scoping and next-period calculation
  - No AI influence on logic or amounts
- Provenance and drill-through
  - `EvidenceRef` captures CSV URI and `input_row_ids` for flagged rows
  - Deterministic run record with output hash and parameters
- Data quality safeguards
  - NaN-safe string handling and date parsing
  - Explicit numeric coercion for amounts
- Audit signals
  - Messages include exception and proposal counts
  - Artifact is referenced in the audit log
- Segregation of duties
  - Proposals are suggestions; posting occurs via JE workflow or human review
