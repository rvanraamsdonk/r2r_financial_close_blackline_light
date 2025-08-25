# Optimum Financial Close Application – Senior Accountant Interaction Design

Each phase of the close is described using a consistent structure:  
- **Purpose**  
- **Inputs**  
- **Actions** (realistic accountant interactions)  
- **Outputs**  
- **Evidence / Provenance** (artifacts available via drill-through)

---

## 1. Close Control Tower (Home)

**Purpose**  
Central command center to monitor overall period progress and unblock the close.

**Inputs**  
- Period calendar and SLAs  
- Entity-level close statuses  
- Exception queues from sub-ledgers, JEs, reconciliations, intercompany, flux  
- Automation proposals waiting for approval  

**Actions**  
- Accountant opens period “Jul-2025,” sees readiness at 72%.  
- Reviews open items by workstream (e.g., IC differences, incomplete reconciliations).  
- Approves system-proposed reversals for prior-period accruals.  
- Assigns overdue tasks to backup owner and escalates critical issues.  
- Drills into a variance exception to see underlying JEs.  

**Outputs**  
- Updated readiness % by entity and workstream  
- Approved automation entries routed to JE Workbench  
- Escalated items with new ownership logged  

**Evidence / Provenance**  
- Drill-through to specific JE, reconciliation, or IC item causing status flag  
- Audit log of who opened/closed periods and approvals given  
- Task evidence files attached (e.g., email, reconciliations)  

---

## 2. Close Calendar & Playbook

**Purpose**  
Structured view of all tasks, dependencies, and required evidence for the close.

**Inputs**  
- Task library with dependencies, RACI, control IDs  
- Assigned owners per task  
- Evidence requirements (type and format)  

**Actions**  
- Accountant reviews their task list for Day 1.  
- Starts “Payroll accrual validation” task, attaches HR extract.  
- Completes task and marks control execution.  
- If a dependency is late (e.g., FX rates not loaded), requests Control Tower to shift downstream tasks.  

**Outputs**  
- Task updated to “Complete”  
- SLA metrics recalculated  
- Dependencies re-sequenced  

**Evidence / Provenance**  
- Attached support documents (extracts, confirmations, statements)  
- Task certification record with owner/date/sign-off  
- Drill-through: Task → evidence → resulting JE or reconciliation  

---

## 3. Data Hub & Trial Balance Staging

**Purpose**  
Ingest sub-ledgers and trial balances, validate, and map to group COA.

**Inputs**  
- Sub-ledger extracts (AP, AR, FA, Payroll, Inventory, Projects, Bank)  
- Local trial balances  
- Mapping rules to group COA  
- FX rates  

**Actions**  
- Accountant monitors ingestion run; system highlights missing mappings.  
- Reviews AI-suggested account mapping for a new supplier expense code, accepts it.  
- Reclassifies out-of-period posting by generating a JE.  
- Re-posts validated batch into GL.  

**Outputs**  
- Validated and mapped trial balances ready for consolidation  
- Reclass JEs created and routed to Workbench  
- Exception log for missing/invalid data  

**Evidence / Provenance**  
- Lineage view from source transaction → mapped group account  
- Exception log with timestamps and resolution  
- Drill-through: TB balance → batch → sub-ledger transaction → source document  

---

## 4. Journal Entry Workbench

**Purpose**  
Centralized hub to create, approve, and post journal entries with policy guardrails.

**Inputs**  
- Draft JEs (from automation, accruals, reconciliations)  
- JE templates for common entries  
- Supporting attachments (HR file, vendor statement, etc.)  

**Actions**  
- Accountant reviews system-generated payroll accrual JE, verifies amounts against HR extract, approves.  
- Prepares manual JE for FX fee, attaches bank statement, and routes for approval.  
- Reviews risk score on a large revenue reclass; requests justification from preparer before approval.  

**Outputs**  
- Approved and posted JEs in GL  
- Parked/rejected JEs with commentary  
- Scheduled reversal entries  

**Evidence / Provenance**  
- Linked support files  
- JE policy reference and preparer/approver trail  
- Drill-through: JE → line items → recon item or source document  

---

## 5. Accruals & Schedules

**Purpose**  
Automate recurring and calculated accruals and prepayments.

**Inputs**  
- Basis data (HR extracts, purchase commitments, contracts)  
- Existing accrual schedules  
- JE templates  

**Actions**  
- Accountant reviews auto-calculated bonus accrual based on HR file, compares to prior trend.  
- Adjusts input file when new headcount is received.  
- System schedules reversal for next period.  

**Outputs**  
- Accrual JEs posted to Workbench  
- Updated schedules for future periods  

**Evidence / Provenance**  
- Basis data attached (e.g., HR or vendor files)  
- Accrual calculation report (system-generated)  
- Drill-through: Schedule → JE → source file  

---

## 6. Intercompany Hub

**Purpose**  
Match, confirm, and settle intercompany transactions.

**Inputs**  
- Intercompany invoices, memos, balances  
- Counterparty assignments  
- FX rates and tolerances  

**Actions**  
- Accountant reviews unmatched items with counterparty.  
- Accepts AI-suggested match despite description mismatch.  
- Confirms balances with counterparties; disputes 3 items via workflow.  
- Approves netting proposal to settle balances.  

**Outputs**  
- Cleared intercompany balances  
- Dispute log created  
- Settlement JEs posted  

**Evidence / Provenance**  
- Matched/unmatched transaction pairs  
- Dispute communication logs  
- Drill-through: IC item → counterparty record → invoice → JE  

---

## 7. Account Reconciliations & Substantiation

**Purpose**  
Certify GL balances with supporting evidence and rollforwards.

**Inputs**  
- GL balance  
- Sub-ledger or bank balances  
- Recon templates with rollforward logic  

**Actions**  
- Accountant opens suspense account recon; system auto-clears immaterial items.  
- Reviews two aged items, generates clearing JE from recon.  
- Attaches bank confirmation for cash account.  
- Certifies reconciliations for low-risk accounts.  

**Outputs**  
- Certified reconciliations by account  
- JE proposals for clearing items  
- Recon exception log  

**Evidence / Provenance**  
- Rollforward schedule  
- Support files (bank statements, sub-ledger extracts)  
- Drill-through: Recon → item → original transaction  

---

## 8. Cash & Bank Recs

**Purpose**  
Match bank statements to GL cash transactions.

**Inputs**  
- Bank statements (BAI2, CAMT, CSV)  
- GL postings for cash  
- Lockbox and payment files  

**Actions**  
- Accountant reviews auto-matched items.  
- Approves residual posting for bank fee.  
- Uses fuzzy match to confirm payer identity for unmatched item.  

**Outputs**  
- Cleared bank recs  
- Residual JE postings (bank charges, FX fees)  

**Evidence / Provenance**  
- Bank statement line items  
- Matching rule IDs  
- Drill-through: Statement line → GL transaction → JE  

---

## 9. Fixed Assets

**Purpose**  
Manage fixed assets and depreciation.

**Inputs**  
- Asset master data (cost, location, useful life, method)  
- Additions, disposals, transfers  

**Actions**  
- Accountant runs depreciation; system posts entries.  
- Reviews flagged exception where depreciation swing > threshold.  
- Approves disposal entry, attaches asset sale contract.  

**Outputs**  
- Depreciation JEs  
- Updated asset sub-ledger  
- Exception log  

**Evidence / Provenance**  
- Asset master record  
- Disposal/sale contract  
- Drill-through: Asset → event → JE  

---

## 10. Inventory & Costing

**Purpose**  
Reconcile inventory balances and calculate reserves.

**Inputs**  
- Inventory sub-ledger quantities and values  
- Costing data and variances  

**Actions**  
- Accountant reviews obsolescence reserve proposal from AI.  
- Approves reserve JE for slow-moving stock.  
- Reconciles perpetual to GL balance.  

**Outputs**  
- Inventory reserves posted  
- Reconciled balances  

**Evidence / Provenance**  
- Inventory aging report  
- Reserve calculation file  
- Drill-through: Inventory item → reserve JE  

---

## 11. Revenue & AR (RevRec)

**Purpose**  
Apply revenue recognition rules and tie AR balances.

**Inputs**  
- Customer contracts and schedules  
- Billing and cash data  

**Actions**  
- Accountant reviews performance obligations per contract.  
- Confirms revenue recognition per system’s rule engine.  
- Adjusts recognition if milestone not met, posts JE.  

**Outputs**  
- Recognized revenue JEs  
- Updated contract schedules  

**Evidence / Provenance**  
- Contract documents  
- Billing schedules  
- Drill-through: Contract → POB → JE  

---

## 12. FX & Rates

**Purpose**  
Manage FX rates and remeasurement.

**Inputs**  
- Rate tables by type (average, closing, historical)  
- Source system feed  

**Actions**  
- Accountant reviews system-loaded rate set, validates against tolerance.  
- Approves remeasurement JE created by system.  
- Investigates FX impact variance flagged by AI.  

**Outputs**  
- Approved rate set locked for period  
- Remeasurement JEs  

**Evidence / Provenance**  
- Rate feed file  
- Rate variance report  
- Drill-through: FX JE → rate source  

---

## 13. Consolidation & Ownership

**Purpose**  
Perform eliminations, translations, and consolidation.

**Inputs**  
- Entity ownership %  
- Local trial balances  
- Elimination rules  

**Actions**  
- Accountant runs consolidation engine.  
- Reviews elimination JE log.  
- Approves top-side adjustment for minority interest.  

**Outputs**  
- Consolidated TB  
- Elimination entries  
- Minority interest adjustments  

**Evidence / Provenance**  
- Ownership matrix  
- Elimination log  
- Drill-through: Consolidated balance → entity contribution → elimination JE  

---

## 14. Variance & Flux Analysis

**Purpose**  
Analyze variances and produce narratives.

**Inputs**  
- Period, prior period, budget, forecast  
- FX-neutral views  
- Materiality thresholds  

**Actions**  
- Accountant reviews variance report, system flags COGS > threshold.  
- AI drafts narrative splitting driver into price vs volume.  
- Accountant edits narrative, assigns line to Ops controller.  

**Outputs**  
- Flux explanations by account/entity  
- Variance log completed  

**Evidence / Provenance**  
- Variance decomposition  
- Linked JEs and schedules  
- Drill-through: Variance → drivers → source JE  

---

## 15. Disclosure & External Reporting

**Purpose**  
Assemble financial statements and disclosures.

**Inputs**  
- Consolidated TB  
- Disclosure templates  
- XBRL taxonomy  

**Actions**  
- Accountant refreshes disclosure note with updated TB data.  
- Validates XBRL tags.  
- Reviews AI-generated MD&A draft, edits narrative.  

**Outputs**  
- Finalized financial statements  
- Tagged XBRL output  
- Published reports  

**Evidence / Provenance**  
- Disclosure template versions  
- Sign-off log  
- Drill-through: Disclosure line → TB source → JE  

---

## 16. Controls, SOX, and Audit Binder

**Purpose**  
Collect evidence for auditors and certify control execution.

**Inputs**  
- Control library with IDs and frequencies  
- PBC request list  
- Evidence attachments  

**Actions**  
- Accountant certifies controls by attaching evidence.  
- Responds to auditor request with system-compiled PBC package.  
- Approves sample selections generated automatically.  

**Outputs**  
- Completed certifications  
- PBC binder with artifacts  
- Auditor access logs  

**Evidence / Provenance**  
- Control execution logs  
- Evidence files with hashes  
- Drill-through: Control → evidence → JE/recon → source document  

---

## 17. Settings & Master Data (Admin)

**Purpose**  
Define rules, mappings, and guardrails.

**Inputs**  
- Chart of accounts  
- Mapping rules  
- Posting policies  
- Approval hierarchies  

**Actions**  
- Admin updates mapping rule for new account.  
- Runs simulation on last period’s data before go-live.  
- Locks rule set for period.  

**Outputs**  
- Updated and locked rule library  
- Simulation log  

**Evidence / Provenance**  
- Rule change history  
- Simulation report  
- Drill-through: Rule → impacted JEs → TB balances  

---