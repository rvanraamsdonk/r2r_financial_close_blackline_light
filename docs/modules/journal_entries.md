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
