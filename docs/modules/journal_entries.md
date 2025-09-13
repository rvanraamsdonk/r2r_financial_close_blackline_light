# Auto Journal Creation Module

Engine: `src/r2r/engines/auto_journal_engine.py::auto_journal_creation(state, audit)`

## Purpose

Deterministically create and auto-approve journal entries for immaterial differences detected by upstream engines (FX Translation, Flux Analysis). Reduce net exception amounts for Gatekeeping and accelerate close.

## Where it runs in the graph sequence

- After: FX Translation, Flux Analysis
- Before: Gatekeeping & Close Reporting
- Node: `auto_journal_creation(state, audit)` (deterministic)

## Inputs

- Module inputs (from `state.metrics`)
  - `fx_translation_artifact`: path to FX artifact (rows with `diff_usd`)
  - `flux_analysis_artifact`: path to Flux artifact (rows with `var_vs_budget`, etc.)
  - `materiality_thresholds_usd` per entity; default threshold = 5,000 USD
  - `state.period`, `state.entity`

## Scope and filters

- Period scope: period of the inbound artifacts
- Entity scope: if `state.entity != "ALL"`, restrict to that entity
- FX: consider rows where `abs(diff_usd) > 0`
- Flux: consider rows where `abs(var_vs_budget) > 0` (and positive for accrual cases)

## Rules

### Deterministic

- FX translation adjustments
  - If `0 < abs(diff_usd) <= threshold(entity)`: propose JE via `JEEngine.propose_je(module="FX", scenario="translation_adjustment", ...)`
  - Auto-approve proposal and add `[DET]` rationale noting amount and threshold
- Flux accrual adjustments
  - If `0 < abs(var_vs_budget) <= threshold(entity)` and `var_vs_budget > 0`: propose JE via `JEEngine.propose_je(module="Flux", scenario="accrual_adjustment", ...)`
  - Auto-approve proposal and add `[DET]` rationale
- Summarize totals by module and overall

### AI

- None. Auto-creation is purely deterministic. Any narratives elsewhere do not affect this engine’s logic.

## Outputs

- Artifact path: `out/auto_journals_{run_id}.json`
- JSON schema with representative values:

```json
{
  "generated_at": "2025-09-12T19:10:16Z",
  "period": "2025-08",
  "entity_scope": "ALL",
  "auto_journals": [
    {
      "je_id": "46f055df-79a3-46c6-b9c2-43fb2007eb9f",
      "module": "FX",
      "scenario": "translation_adjustment",
      "entity": "ENT101",
      "amount_usd": 347.47,
      "description": "FX translation adjustment - EUR 347.47 (ENT101/1000)",
      "lines": [
        {"account": "1000", "description": "FX translation adjustment - EUR", "debit": 347.47, "credit": 0.0, "entity": "ENT101", "currency": "USD"},
        {"account": "7201", "description": "FX translation gain - EUR", "debit": 0.0, "credit": 347.47, "entity": "ENT101", "currency": "USD"}
      ],
      "deterministic_rationale": "[DET] Auto-created FX translation adjustment; amount below entity threshold.",
      "source_data": {"entity": "ENT101", "account": "1000", "currency": "EUR", "diff_usd": 347.47}
    }
  ],
  "summary": {
    "total_count": 12,
    "total_amount_usd": 2897.12,
    "by_module": {"FX": 9, "Flux": 3}
  },
  "materiality_thresholds": {"ENT101": 5000},
  "auto_journal_threshold": 5000
}
```

- Metrics written to `state.metrics`
  - `auto_journals_count`, `auto_journals_total_usd`, `auto_journals_by_module`, `auto_journals_artifact`

## Controls

- Deterministic creation bounded by entity thresholds; auto-approval only for immaterial amounts
- Provenance: upstream artifacts referenced; deterministic run recorded with output hash
- Data quality: resilient parsing of artifacts; numeric coercion and rounding for lines
- Audit signals: messages include counts and totals; [DET] rationales per auto-JE

---

# Journal Entry (JE) Module

## Overview

The Journal Entry module provides a generic, reusable workflow for proposing, reviewing, approving, and posting journal entries across all R2R financial close modules. It integrates seamlessly with FX Translation, Flux Analysis, and other modules to enable accountants to create adjusting entries directly from identified variances.

## Architecture

### Data Models

```python
class JEStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending" 
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"

@dataclass
class JELine:
    account: str
    description: str
    debit: float = 0.0
    credit: float = 0.0

@dataclass 
class JournalEntry:
    id: str
    module: str
    scenario: str
    entity: str
    period: str
    description: str
    lines: List[JELine]
    status: JEStatus
    source_data: Dict[str, Any]
    created_at: datetime
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    approver: Optional[str] = None
    comments: str = ""
```

### Backend Endpoints

#### `/je/propose` (POST)
- **Purpose**: Create and display a JE proposal modal
- **Input**: JSON with module, scenario, source_data, period, entity
- **Output**: JE proposal modal HTML with calculated entries
- **Business Logic**: 
  - Calls module-specific JE creation functions (`_create_fx_je`, `_create_flux_je`)
  - Generates appropriate debit/credit entries based on source data
  - Returns modal with JE details and workflow actions

#### `/je/submit/{je_id}` (POST)
- **Purpose**: Submit JE for approval
- **Input**: JE ID from URL path
- **Output**: Updated modal with "Pending" status
- **Business Logic**: Changes status from DRAFT → PENDING

#### `/je/approve/{je_id}` (POST)
- **Purpose**: Approve or reject JE
- **Input**: JE ID and action (approve/reject) from form
- **Output**: Updated modal with approval status
- **Business Logic**: Changes status to APPROVED or REJECTED

#### `/je/post/{je_id}` (POST)
- **Purpose**: Post JE to GL system
- **Input**: JE ID from URL path
- **Output**: Updated modal with "Posted" status
- **Business Logic**: Changes status from APPROVED → POSTED

### Module Integration

#### FX Translation
- **Trigger**: FX differences > $0.01
- **JE Logic**: Creates translation adjustment entries
  - Debit: Translation Adjustment Expense
  - Credit: Cumulative Translation Adjustment (CTA)
- **Account Mapping**: Uses entity-specific GL accounts

#### Flux Analysis
- **Trigger**: Variances exceeding threshold (severe = true)
- **JE Logic**: Creates variance explanation entries
  - Debit/Credit: Appropriate expense/revenue accounts
  - Contra: Accrual or reclassification accounts
- **Account Mapping**: Based on account type and variance direction

## UI Components

### JE Button (`partials/je_button.html`)
Generic button component that can be embedded in any table row:
```html
<button type="button" 
        class="inline-flex items-center px-2 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded border border-indigo-200 transition-colors"
        hx-post="/je/propose"
        hx-vals='{"module": "{{ module }}", "scenario": "{{ scenario }}", "source_data": {{ source_data | tojson }}, "period": "{{ period }}", "entity": "{{ entity }}"}'
        hx-target="body"
        hx-swap="beforeend">
  JE
</button>
```

### JE Proposal Modal (`partials/je_proposal_modal.html`)
Comprehensive modal displaying:
- JE header information (ID, module, entity, period)
- Debit/credit line items with account details
- Balance validation (ensures debits = credits)
- Source data reference
- Workflow action buttons based on current status
- Modal close functionality

## Business Logic Functions

### `_create_fx_je(source_data, period, entity)`
Creates journal entries for FX translation differences:
- Calculates adjustment amount from source_data
- Determines debit/credit direction based on difference sign
- Maps to appropriate GL accounts (Translation Adj, CTA)
- Returns JournalEntry object with calculated lines

### `_create_flux_je(source_data, period, entity)`  
Creates journal entries for flux analysis variances:
- Extracts variance amount and account from source_data
- Determines adjustment type (accrual, reclassification, etc.)
- Maps to appropriate GL accounts based on account type
- Returns JournalEntry object with variance entries

## Integration Points

### Module Integration
1. Add JE column header to table templates
2. Include JE button in table rows with conditional display
3. Pass module-specific data via `hx-vals` attribute
4. Implement module-specific JE creation logic

### Example Integration (FX Module):
```html
<!-- In fx.html table header -->
<th class="text-center px-2 py-2">JE</th>

<!-- In fx table row -->
<td class="px-2 py-2 text-center">
  {% if r.diff_usd|abs > 0.01 %}
  <button type="button" 
          class="inline-flex items-center px-2 py-1 text-xs font-medium text-indigo-600 bg-indigo-50 hover:bg-indigo-100 rounded border border-indigo-200 transition-colors"
          hx-post="/je/propose"
          hx-vals='{"module": "FX", "scenario": "fx_translation", "source_data": {{ r | tojson }}, "period": "{{ fx.period }}", "entity": "{{ r.entity }}"}'
          hx-target="body"
          hx-swap="beforeend">
    JE
  </button>
  {% endif %}
</td>
```

## Workflow States

1. **DRAFT**: JE created but not submitted
   - Actions: Submit for Approval, Edit, Cancel
   
2. **PENDING**: JE submitted and awaiting approval
   - Actions: Approve, Reject, View Details
   
3. **APPROVED**: JE approved and ready for posting
   - Actions: Post to GL, View Details
   
4. **POSTED**: JE posted to GL system
   - Actions: View Details only (read-only)
   
5. **REJECTED**: JE rejected by approver
   - Actions: Revise and Resubmit, Cancel

## Account Mapping Strategy

### FX Translation Entries
- **Translation Loss**: Dr. Translation Adjustment Expense, Cr. CTA
- **Translation Gain**: Dr. CTA, Cr. Translation Adjustment Income
- **Account Codes**: Entity-specific (e.g., 7820-Translation Adj, 3150-CTA)

### Flux Analysis Entries  
- **Revenue Variances**: Adjust revenue accounts with accrual contra
- **Expense Variances**: Adjust expense accounts with prepaid/accrual contra
- **Account Mapping**: Based on account type and GL structure

## Future Enhancements

1. **Persistent Storage**: Replace in-memory store with database
2. **User Authentication**: Add real user roles and permissions
3. **Audit Trail**: Enhanced logging and approval history
4. **Batch Processing**: Support for multiple JE creation
5. **GL Integration**: Real posting to external GL systems
6. **Workflow Customization**: Configurable approval routing
7. **Template Library**: Pre-defined JE templates by scenario

## Testing

### Manual Testing Steps
1. Navigate to FX or Flux analysis page
2. Identify rows with material differences/variances
3. Click "JE" button to open proposal modal
4. Review calculated entries and balance validation
5. Test complete workflow: Submit → Approve → Post
6. Verify status updates and action button changes

### Integration Testing
- Verify JE buttons appear conditionally based on thresholds
- Test modal functionality across different modules
- Validate account mappings and calculation logic
- Confirm HTMX interactions and modal behavior

## Security Considerations

- Input validation on all JE endpoints
- Authorization checks for approval actions
- Audit logging for all JE state changes
- Data sanitization for source_data JSON
- CSRF protection via HTMX headers
