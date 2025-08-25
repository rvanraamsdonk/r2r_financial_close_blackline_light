# Accountant’s High‑Level Close Journey

A concise, step‑by‑step view of what a financial close accountant experiences in the UI. For each step: what you see and what you can do. No technical details.

---

## 1) Open Close Dashboard

**What you see:**
- Period selector and entities list
- Overall readiness status and key metrics
- Exception counts and automation rates

**Sample Dashboard Overview (representative):**

| Metric | Value | Status | Notes |
|--------|-------|--------|-------|
| AP Exceptions | 119 | 🔴 High | From `ap_reconciliation_…json` |
| AR Exceptions | 150 | 🔴 High | From `ar_reconciliation_…json` |
| JE Approvals Pending | 3 | 🟡 Medium | From `je_lifecycle_…json` |
| Flux Variances | 127 | 🔴 High | From `flux_analysis_…json` |
| Bank Duplicates | 0 | 🟢 Low | From `bank_reconciliation_…json` |
| FX Translation Differences | 99 | 🔴 High | Total abs diff ≈ $38.53M |
| Automation Rate | 85%+ | 🟢 Good | Representative KPI |

**🤖 AI Executive Summary (sample):**
"AP and AR exceptions elevated this period (119/150). Flux variances concentrated in select expense accounts (127). FX translation shows differences across 99 rows; review rate application policy. Three JEs pending approval. Close remains blocked pending remediation of high‑risk items."

**You can:**
- Choose the period and entities
- Start or resume the close
- Navigate to specific exception areas
- Export executive summary

## 2) Briefing & Context

**What you see:**
- A short summary of scope, timelines, and responsibilities
- Any carry‑forward open items from the prior period
- Period governance and policy settings

**Sample Period Overview (representative):**

| Setting | Value | Status |
|---------|-------|--------|
| Period | August 2025 | ✅ Active |
| Entity Scope | ALL (ENT100, ENT101, ENT102) | ✅ Confirmed |
| Governance Status | Locked | 🔒 Secured |
| AI Mode | Assist | ⚙️ Enabled |
| Materiality Method | 0.5% of TB balance, $1K floor | ✅ Applied |
| Data Integrity | All datasets validated | ✅ Clean |

**You can:**
- Acknowledge the briefing
- Assign or reassign responsibilities
- Review materiality thresholds by entity
- Confirm period lock status

## 3) Trial Balance Check

**What you see:**
- High‑level pass/fail for each entity
- A small count of mappings or balance issues, if any
- Account-level imbalances and top contributing accounts

**Sample TB Diagnostics (representative):**

| Entity | Status | Imbalance (USD) | Top Issue Account | Balance | Type |
|--------|--------|-----------------|-------------------|---------|------|
| ENT100 | 🔴 Failed | $14,768,551.08 | 4300 | $10,774,512.68 | Revenue |
| ENT101 | 🔴 Failed | $34,187,114.57 | 4000 | $12,437,240.67 | Revenue |
| ENT102 | 🔴 Failed | $12,009,514.87 | 4000 | $17,081,231.64 | Revenue |

**You can:**
- Approve TB as clean
- Send issues to the mapping/GL owner to fix
- Review detailed account imbalances
- Export TB diagnostic reports

## 4) Cash / Bank Reconciliation

**What you see:**
- Match rate and exceptions by bank account
- Buckets for timing differences, duplicates, and unmatched items
- AI-generated reconciliation suggestions

**Sample Bank Reconciliation Items (representative):**

| Account | Transaction | Amount | Type | AI Analysis | Action Required |
|---------|-------------|--------|------|-------------|----------------|
| Operating-001 | Wire Transfer | $25,000.00 | Timing | Likely in-transit; expect clearing next period | Monitor |
| Payroll-002 | Check #1247 | $3,450.00 | Duplicate | No duplicates detected this period overall; example shown for illustration | Review |
| Treasury-003 | ACH Payment | $12,750.00 | Unmatched | No corresponding GL entry found | Investigate |

**You can:**
- Mark timing differences as acceptable for this period
- Confirm duplicates and request/record corrections
- Mark accounts as reconciled when comfortable
- Export reconciliation reports

## 5) Accounts Payable Review

**What you see:**
- Variances between AP subledger and GL by vendor
- Categories such as cut‑off, missing, or duplicate
- AI-generated rationales and matching suggestions

**Sample AP Exceptions:**

| Vendor | Bill ID | Amount | Status | AI Analysis | Next Action | Priority |
|--------|---------|--------|--------|-------------|-------------|----------|
| Acme Corp | BILL-2025-001 | $15,420.50 | Unmatched | **Timing Issue**: Invoice dated 8/29, received 9/2. Historical pattern shows Acme invoices 2-3 days after month-end. **Recommendation**: Accrue in August, reverse in September. | Auto-accrue | 🟡 Medium |
| Global Tech Solutions | BILL-2025-089 | $8,750.00 | Duplicate Risk | **Pattern Match**: 98.5% similarity to BILL-2025-087 ($8,750.00, same date). **Risk Factors**: Same vendor, amount, GL code. **Evidence**: Different invoice numbers (089 vs 087). **Recommendation**: Flag for manual review. | Manual review | 🔴 High |
| Office Supplies Inc | BILL-2025-156 | $2,340.25 | Missing PO | **Process Gap**: No PO in system. **Historical Context**: 15 prior invoices from this vendor, all had POs. **Business Context**: Amount exceeds $2K approval threshold. **Recommendation**: Contact procurement for PO creation or expense reclassification. | Contact procurement | 🟡 Medium |

**🤖 AI Insights:**
*"AP exceptions down 20% from July due to improved vendor onboarding. Key risk: Global Tech duplicate requires immediate attention - potential $8.7K overstatement. Acme Corp timing pattern suggests need for automated accrual rule. Office Supplies exception indicates possible procurement process breakdown."*

**You can:**
- Accept cut‑off explanations
- Request an accrual or reversal
- Assign follow‑ups to owners
- Accept or reject AI matching suggestions

## 6) Accounts Receivable Review

**What you see:**
- Customer invoice exceptions and aging analysis
- Overdue items flagged for collection
- AI-generated collection strategies

**Sample AR Exceptions:**

| Customer | Invoice ID | Amount | Days Overdue | AI Collection Strategy | Risk Score | Recommended Action |
|----------|------------|--------|--------------|----------------------|------------|--------------------|
| TechCorp Ltd | INV-2025-445 | $12,850.00 | 45 | **Payment Pattern**: Historically pays 30-60 days late but always pays. **Credit Score**: 720 (Good). **Recent Activity**: 3 invoices paid in last 30 days. **Strategy**: Gentle reminder with payment plan option. | 🟡 Medium | Send payment reminder + offer 30-day extension |
| Global Manufacturing | INV-2025-389 | $8,200.00 | 15 | **Payment Pattern**: Consistent 30-day payer. **Seasonal Factor**: Q3 typically slower due to plant shutdowns. **Relationship**: 5-year customer, $2M annual revenue. **Strategy**: Monitor, no action needed. | 🟢 Low | Monitor - no action required |
| Retail Solutions Inc | INV-2025-501 | $5,750.00 | 60 | **Red Flags**: No payments in 90 days, 3 disputed invoices this quarter. **Financial Health**: Credit score dropped to 580. **Legal History**: 2 collection cases filed. **Strategy**: Immediate escalation to legal. | 🔴 High | Escalate to legal department immediately |

**🤖 AI Collection Insights:**
*"AR aging improving overall - average DSO down 3 days to 42. TechCorp represents 23% of overdue balance but low risk based on payment history. Retail Solutions shows distress signals - recommend credit hold and legal action. Seasonal patterns suggest Global Manufacturing will pay by month-end."*

**You can:**
- Approve collection actions
- Mark disputes for investigation
- Adjust aging categories
- Export collection reports

## 7) Intercompany Balances

**What you see:**
- Net differences by counterparty and entity
- Materiality highlights and exception counts
- AI-generated matching proposals

**Sample Intercompany Status (representative):**

| Entity Pair | Net Difference | Materiality | Status | AI Analysis |
|-------------|----------------|-------------|--------|-------------|
| ENT100 ↔ ENT101 | $0.00 | $1,000 | ✅ Balanced | No mismatches detected |
| ENT100 ↔ ENT102 | $0.00 | $1,000 | ✅ Balanced | No mismatches detected |
| ENT101 ↔ ENT102 | $0.00 | $1,000 | ✅ Balanced | No mismatches detected |

**Summary Metrics (from artifacts):**
- Total IC Mismatches: 0
- Total Absolute Difference: $0.00
- Proposals Generated: 0

**You can:**
- Assign differences to counterparties to resolve
- Approve immaterial items
- Review detailed transaction matching
- Export IC reconciliation reports

## 8) Accruals & Reversals

**What you see:**
- List of period accruals with expected reversals
- Flags for missing or incorrect reversals
- Journal entry approval status

**Sample Journal Entry Review (representative):**

| JE ID | Entity | Amount | Type | Status | Approver | Issue |
|-------|--------|--------|------|--------|----------|-------|
| JE-2025-08-001 | ENT100 | $29,408.57 | Manual | Pending | Controller | Approval required |
| JE-2025-08-004 | ENT101 | $15,000.00 | Manual | Pending | IC Controller | Approval required |
| JE-2025-08-001 | ENT100 | $29,408.57 | Reversal | Flagged | - | Reversal detected |

**You can:**
- Approve accrual outcomes
- Trigger adjustments or open a task to post
- Review and approve pending journal entries
- Flag reversals for investigation

## 9) FX & Translation Review

**What you see:**
- Summary of rates used and translated balances by entity
- Any unusual movements highlighted
- Translation differences and policy compliance

**Sample FX Translation Results (representative):**

| Entity | Account | Currency | Local Balance | Rate | Computed USD | Reported USD | Difference |
|--------|---------|----------|---------------|------|--------------|--------------|------------|
| ENT100 | 1000 - Cash | USD | $506,054 | 1.0075 | $509,849 | $506,054 | $3,795 |
| ENT100 | 1100 - A/R | USD | $273,600 | 1.0075 | $275,652 | $273,600 | $2,052 |
| ENT100 | 1200 - Inventory | USD | $177,448 | 1.0075 | $178,779 | $177,448 | $1,331 |

**Translation Summary (from artifacts):**
- Total Rows Processed: 99
- Differences Found: 99
- Total Absolute Difference: ~$38,529,394
- Policy Tolerance: $0.01

**You can:**
- Acknowledge translation as reasonable
- Add notes where movements require explanation
- Review rate sources and methodology
- Export FX impact analysis

## 10) Variance vs Budget/Forecast

**What you see:**
- Accounts or groups that exceed variance thresholds
- Quick view of favorable/unfavorable trends
- AI-generated variance explanations

**Sample Variance Analysis:**

| Entity | Account | Actual | Budget | Variance | % Var | AI Root Cause Analysis | Business Impact | Recommendation |
|--------|---------|--------|--------|----------|-------|----------------------|-----------------|----------------|
| ENT100 | Travel Expenses | $45,200 | $32,000 | $13,200 | 41.3% | **Primary Driver**: Q3 trade show season (3 major events vs 1 budgeted). **Secondary**: New client acquisition travel (+$4.2K). **Pattern**: 85% of variance in weeks 35-38. **ROI Context**: Generated $180K in new pipeline. | **Positive**: 4.0x ROI on incremental spend. New client meetings resulted in 2 signed contracts worth $95K. | **Accept variance** - strong ROI justifies overspend. Consider increasing Q3 travel budget for next year. |
| ENT101 | Professional Fees | $28,500 | $25,000 | $3,500 | 14.0% | **Primary Driver**: M&A legal fees for acquisition due diligence ($2.8K). **Secondary**: Employment law consultation ($700). **Timing**: 90% of overage in final 2 weeks of month. **Context**: Unplanned acquisition opportunity. | **Strategic**: Legal spend directly supports $2M acquisition target. Employment issue resolved without litigation risk. | **Accept variance** - strategic investment. Establish separate M&A legal budget line for future deals. |
| ENT102 | Marketing | $18,750 | $22,000 | ($3,250) | -14.8% | **Primary Driver**: Digital campaign delayed from August to September due to creative review cycle. **Secondary**: Trade publication ad cancelled ($800). **Opportunity**: Vendor offered 15% discount for Q4 commitment. | **Mixed**: Campaign delay may impact Q3 lead generation. However, Q4 discount creates cost savings opportunity. | **Monitor impact** - track Q3 lead metrics. Consider accelerating Q4 campaign to capture discount. |

**🤖 AI Variance Insights:**
*"Overall variance performance strong with 2 of 3 variances showing positive business rationale. Travel overspend delivered 4x ROI through new client acquisition. Marketing underspend creates Q4 opportunity but may impact Q3 pipeline. Recommend establishing M&A budget category to better track strategic investments."*

**You can:**
- Add short explanations
- Flag items for management review
- Approve variance rationales
- Export variance reports

## 11) Forensic Highlights

**What you see:**
- A small set of notable patterns prioritized by significance
- Forensic findings with confidence scores and impact analysis
- Risk categorization and recommended actions

**Sample Forensic Findings (representative):**

| Category | Finding | Confidence | Impact | Recommendation |
|----------|---------|------------|--------|-----------------|
| Timing Differences | No material bank duplicates; monitor 0 open items | - | Low | Acknowledge |
| Duplicate Risk | AP duplicates not detected this period | - | Low | Monitor |
| FX Impact | ~$38.53M translation differences across 99 rows | - | High | Review rate methodology |
| Pattern Analysis | Expense variances concentrated in select accounts | - | Medium | Add explanations |

**You can:**
- Accept categorizations
- Convert highlights into follow‑up tasks or notes
- Export forensic analysis reports
- Escalate high-risk findings

## 12) Evidence & Notes

**What you see:**
- A consolidated area for supporting notes and references tied to exceptions
- Document attachments and evidence links
- Reviewer comments and audit trail

**Sample Evidence Repository:**

| Exception ID | Type | Evidence | Reviewer | Status | Notes |
|--------------|------|----------|----------|--------|---------|
| AP-001 | Invoice | email_evidence_001.pdf | J.Smith | ✅ Complete | Vendor confirmation received |
| AR-445 | Collection | customer_dispute_445.docx | M.Jones | 🟡 Pending | Awaiting legal review |
| BANK-025 | Wire Transfer | wire_confirmation_025.pdf | T.Wilson | ✅ Complete | Bank confirmed in-transit |
| JE-001 | Manual Entry | supporting_calc_001.xlsx | Controller | 🟡 Review | Requires CFO approval |

**Document Summary:**
- Total Evidence Items: 47
- Pending Reviews: 8
- Complete: 39
- Average Resolution Time: 2.3 days

**You can:**
- Attach or link evidence
- Add reviewer notes and conclusions
- Track evidence completion status
- Export evidence packages

## 13) Human Review Queue

**What you see:**
- Items awaiting action with clear owners and due dates
- Status: approved, pending, needs info
- Priority levels and case categories

**Sample HITL Cases:**

| Case ID | Category | Severity | Title | Owner | Status |
|---------|----------|----------|-------|-------|--------|
| HITL-001 | Bank Reconciliation | High | Unmatched wire transfer $25K | Treasury | Pending |
| HITL-002 | Journal Entry | Medium | Manual accrual requires approval | Controller | Review |
| HITL-003 | Intercompany | Low | Minor IC balance difference | IC Team | Approved |

**You can:**
- Approve/Reject with a comment
- Reassign or escalate
- Add supporting documentation
- Set follow-up reminders

## 14) Sign‑Offs

**What you see:**
- Entity‑level and consolidated sign‑off statuses
- Checklist completion for required controls
- SOX compliance validation status

**Sample Sign-Off Status (representative):**

| Control Area | Control ID | Description | Status | Preparer | Reviewer | Date |
|--------------|------------|-------------|--------|----------|----------|---------|
| TB Balance | TB.BAL.001 | Entity TB balances to 0 | 🔴 Failed | - | - | - |
| FX Coverage | FX.COV.001 | FX rates coverage policy | ✅ Passed | A.Chen | B.Davis | 2025-08-23 |
| Bank Rec | BANK.REC.002 | Bank duplicate detection | ✅ Passed | C.Miller | D.Taylor | 2025-08-23 |
| AP Rec | AP.REC.003 | AP reconciliation exceptions | 🟡 Review | E.Johnson | - | - |
| AR Rec | AR.REC.004 | AR reconciliation exceptions | 🟡 Review | F.Brown | - | - |

**Overall Status:**
- Controls Passed: 2/8 (25%)
- Controls Failed: 1/8 (12.5%)
- Controls Pending: 5/8 (62.5%)
- **Close Status: BLOCKED** (gatekeeping high risk)

**You can:**
- Provide preparer and reviewer sign‑offs
- Lock sections when complete
- Override controls with justification
- Export compliance reports

## 15) Close Package & Export

**What you see:**
- A clean list of final artifacts and a summary of what’s included
- Package completeness status and file inventory
- Export options and delivery methods

**Sample Close Package Contents:**

| Artifact | File | Size | Status | Last Updated |
|----------|------|------|--------|--------------|
| Close Report | close_report_20250823.json | 2.1 KB | ✅ Ready | 2025-08-23 13:59 |
| AP Reconciliation | ap_reconciliation_20250823.json | 45.2 KB | ✅ Ready | 2025-08-23 13:59 |
| AR Reconciliation | ar_reconciliation_20250823.json | 42.8 KB | ✅ Ready | 2025-08-23 13:59 |
| Variance Analysis | flux_analysis_20250823.json | 38.9 KB | ✅ Ready | 2025-08-23 13:59 |
| HITL Cases | cases_20250823.json | 3.4 KB | ✅ Ready | 2025-08-23 13:59 |
| Controls Mapping | controls_mapping_20250823.json | 1.8 KB | ✅ Ready | 2025-08-23 13:59 |
| Audit Log | audit_20250823.jsonl | 15.7 KB | ✅ Ready | 2025-08-23 13:59 |

**Package Summary:**
- Total Files: 26
- Total Size: 234.8 KB
- Completeness: 100%
- Ready for Export: Yes

**You can:**
- Export/download the package for audit
- Share a summary with stakeholders
- Schedule automated delivery
- Generate executive summary

## 16) Wrap‑Up & Next Period Prep

**What you see:**
- A short post‑close summary: what went well, what to improve
- Any items carried forward to next period
- Performance metrics and automation insights

**Sample Close Performance Summary:**

| Metric | Current Period | Prior Period | Trend |
|--------|----------------|--------------|-------|
| Total Exceptions | 47 | 42 | ↑ +5 |
| Resolution Time | 2.3 days avg | 2.8 days avg | ↓ -0.5 days |
| Automation Rate | 85.2% | 83.1% | ↑ +2.1% |
| Manual Interventions | 7 | 12 | ↓ -5 |
| Controls Passed | 25% | 78% | ↓ -53% |
| Close Duration | 3.2 days | 4.1 days | ↓ -0.9 days |

**Carry-Forward Items:**

| Item | Owner | Due Date | Priority |
|------|-------|----------|----------|
| TB imbalance resolution | GL Team | 2025-09-05 | High |
| AP duplicate control enhancement | Process Team | 2025-09-15 | Medium |
| FX rate methodology review | Treasury | 2025-09-10 | High |

**You can:**
- Record lessons learned
- Set reminders and responsibilities for next close
- Archive current period data
- Initialize next period setup

---

This journey is intentionally high‑level and maps to a standard accountant’s experience: select scope, validate TB, reconcile key ledgers, review variances, document evidence, complete HITL reviews, sign off, and export the close package.
