# Static Financial Close Dataset

## Overview
This dataset represents a realistic month-end close for **TechCorp Holdings** (3 entities) for **August 2025**, with comparative data from July 2025. All amounts are designed to demonstrate common reconciliation challenges while maintaining a balanced trial balance.

## Dataset Structure

### Core Financial Data
```
data/
├── entities.csv              # Entity master data
├── chart_of_accounts.csv     # COA with account classifications
├── trial_balance_aug.csv     # Current period TB (pre-adjustments)
├── trial_balance_jul.csv     # Prior period TB (for variance analysis)
├── budget_aug.csv            # Budget vs actual analysis
└── fx_rates.csv              # Multi-currency exchange rates
```

### Subledger Details
```
data/subledgers/
├── ar_detail_aug.csv         # AR aging with customer details
├── ap_detail_aug.csv         # AP aging with vendor details
├── bank_statements/
│   ├── ent100_aug.csv        # Bank statement for Entity 100
│   ├── ent101_aug.csv        # Bank statement for Entity 101
│   └── ent102_aug.csv        # Bank statement for Entity 102
└── intercompany/
    ├── ic_transactions.csv   # Intercompany transaction details
    └── ic_eliminations.csv   # Required elimination entries
```

### Supporting Documents
```
data/supporting/
├── invoices_sample.csv       # Sample customer invoices
├── vendor_bills_sample.csv   # Sample vendor bills
├── journal_entries.csv       # Standard recurring entries
├── accruals.csv             # Month-end accrual calculations
└── reconciliations/
    ├── cash_rec_template.csv # Bank reconciliation format
    ├── ar_rec_template.csv   # AR reconciliation format
    └── ap_rec_template.csv   # AP reconciliation format
```

## Embedded Forensic Scenarios

### 1. Timing Differences (Solvable)
- **Issue**: $45K in AR appears unmatched to bank receipts
- **Root Cause**: Customer payments received Aug 31, recorded Sep 1
- **Solution**: Cut-off adjustment entry

### 2. Duplicate Transactions (Auto-correctable)
- **Issue**: $12.5K duplicate vendor payment in AP
- **Root Cause**: Same invoice processed twice (different reference numbers)
- **Solution**: Reverse duplicate entry

### 3. FX Revaluation (Calculable)
- **Issue**: €850K intercompany balance needs revaluation
- **Root Cause**: EUR/USD rate changed from 1.085 to 1.092
- **Solution**: FX gain/loss journal entry

### 4. Accrual Reversal (Predictable)
- **Issue**: $28K July accrual not reversed in August
- **Root Cause**: Automated reversal failed
- **Solution**: Manual reversal entry

### 5. Intercompany Mismatch (Reconcilable)
- **Issue**: $15K difference in IC balances between entities
- **Root Cause**: Timing difference in booking
- **Solution**: Align booking dates

## Trial Balance Integrity

**Pre-Close Balance**: $0 (balanced)
**Expected Adjustments**: ~$125K total
**Post-Close Balance**: $0 (remains balanced)

All scenarios are designed to:
- Have identifiable root causes
- Be solvable through standard accounting procedures
- Demonstrate realistic month-end challenges
- Support automated analysis and correction recommendations

## Demo Flow
1. Load static data → Identify discrepancies
2. Run forensic analysis → Determine root causes  
3. Generate recommendations → Auto-correct where possible
4. Present final balanced trial balance
