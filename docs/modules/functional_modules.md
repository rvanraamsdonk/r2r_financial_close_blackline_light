# Functional Modules (Sequential)

Each module emits labeled outputs: [DET] deterministic, [AI] assistive, [HYBRID] mixed. All items include drill-through to evidence and lineage.

1. Period Initialization & Governance [DET]
   - Inputs: entities, COA, SOX controls, approval workflows, policy config
   - Actions: lock period/scope/currency; materiality by entity/account; run ID + config/code hash
   - Outputs: run config snapshot, control checklist, audit `run_started`

2. Data Ingestion & Validation [DET + AI]
   - Actions: schema/dtype, referential integrity, date windows, duplicates, FX coverage
   - [AI]: root-cause suggestions and remediation hints for validation exceptions

3. FX Translation [DET]
   - Policy: EOM for BS, average for P&L (configurable)
   - Outputs: reporting-currency TB/transactions; FX evidence; exceptions for gaps

4. TB Integrity & Rollups [DET]
   - Actions: Debits=Credits by entity; rollups/segments; integrity metrics

5. AP/AR Reconciliations [DET + AI]
   - Actions: GL control tie-outs; cutoff; duplicates; unmatched listings
   - [AI]: fuzzy match suggestions (confidence, citations) for unresolved items

6. Bank Reconciliations [DET + AI]
   - Actions: GL cash vs bank statements; timing items; unmatched register
   - [AI]: suggestions and timing vs error rationales

7. Intercompany Reconciliation [DET + AI]
   - Actions: rule-based matching; FX-consistent imbalances; deterministic true-up JE proposals with simulation
   - [AI]: match candidates and imbalance rationale (confidence, citations)

8. Accruals & Provisions [DET + AI]
   - Actions: recurring roll-forward + reversals; cutoff accruals from actuals; permitted estimates from patterns/budget variance
   - [AI]: JE narratives and management rationale (facts cited)

9. Flux Analysis (Budget & Prior) [DET + AI]
   - Actions: variance by account/entity; materiality banding; driver analysis
   - [AI]: grounded narratives citing computed variances and exact rows

10. Journal Entry Lifecycle [DET]
   - Actions: validate, simulate TB deltas, approvals (four-eyes, SoD), post, re-run controls
   
11. Gatekeeping & Risk Aggregation [DET + AI]
   - Actions: coverage/exception metrics; thresholds; readiness decision
   - [AI]: risk rationales and escalation recommendations

12. HITL Case Management [DET + AI]
   - Actions: cases with SLA, owner, evidence; re-tests after actions
   - [AI]: summarize evidence and propose next actions

13. Close Reporting & Evidence Pack [HYBRID]
   - [DET]: registers, dashboards, controls matrix, lineage graphs, code/config hash
   - [AI]: executive/variance narratives with citations and labels

14. Metrics & Controls Mapping [DET + AI]
   - [DET]: coverage %, exception $, recon statuses, IC netting, JE latency, AI cost/latency
   - [AI]: control owner summaries and residual-risk highlights
