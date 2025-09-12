# Forensic Scenarios: Data Embedding, Deterministic Detection, and AI Assist

This document explains the forensic scenarios embedded in the sample data and how the platform deterministically surfaces them across AP, AR, Bank, Intercompany, Flux, and TB Diagnostics. It also clarifies what is strictly deterministic versus where AI is used for assistive rationale only, and maps the approach to Big 4 managed service accounting best practices.

## Summary
- The data contains seeded forensic patterns across subledgers and supporting datasets.
- Engines apply deterministic rules to detect exceptions; all decisioning is rule-/threshold-based with reproducible output hashes.
- AI is used for narrative, hints, confidence scoring annotation, and UI summaries; it does not make final decisions nor override thresholds.
- Materiality and policy drive auto-approval; forensic-risk patterns never auto-approve by design.

---

## 1) Where forensic scenarios are embedded in data

Source scripts embed realistic patterns. Seeds are fixed for reproducibility (`random.seed(42)`, `np.random.seed(42)`).

- AP patterns
  - Duplicate payments: near-identical vendor, amount (±$50), within 7 days.
  - Round-dollar anomalies: suspiciously round amounts (e.g., $10k, $25k, $50k, $100k).
  - Suspicious new vendors: vendor names containing urgency/speed keywords with large payments.
  - Weekend entries: invoice dates on Sat/Sun.
  - Split transactions: large invoices split into 2–3 parts same day.
- AR patterns
  - Channel stuffing: month-end spike with extended payment terms (Net 90/120/180).
  - Credit memo abuse: significant negative invoices flagged as credit memos.
  - Related party: invoices to affiliate-like names with unusual pricing.
- Bank patterns
  - Kiting: transfer-out followed by near-equal transfer-in 1–3 days later.
  - Unusual counterparties: loan/cash-advance style entities with large amounts.
  - Velocity anomaly: multiple same-day transactions to the same counterparty.
- Intercompany patterns
  - Transfer pricing/arm’s-length: management fees inflated/deflated; round-dollar.
  - Structuring: multiple small same-day movements between entity pairs.
  - Documentation gaps: vague descriptions/references.
- Trial balance and accruals
  - TB: balance manipulation, expense shifting, reserve manipulation, classification errors.
  - Accruals/JE: earnings management, cookie-jar reserves, period-end manipulation, unauthorized entries, SoD violations.

---

## 2) How the engines deterministically surface scenarios

All engines implement deterministic detection with explicit rules, thresholds, and artifact generation. Each run logs `EvidenceRef` and `DeterministicRun` entries to the audit log (`out/run_*/audit_*.jsonl`).

### AP — `src/r2r/engines/ap_ar_recon.py::ap_reconciliation()`
Deterministic rules:
- Overdue or `age_days > 60`.
- Notes contain "duplicate".
- Forensic pattern detection (deterministic heuristics):
  - Duplicate payment pattern: same vendor, similar amount (≤ $50), dates within 7 days.
  - Round-dollar anomalies: multiples of $500/$1,000/$10,000 thresholds.
  - Suspicious new vendor: urgency/speed keyword + large payment (> $25k).
  - Weekend entry: bill date Saturday/Sunday.
  - Split transactions: multiple invoices same vendor same day.
Outputs:
- Artifact: `out/run_*/ap_reconciliation_*.json` with `exceptions`, `summary`, deterministic `rules`, and per-exception `ai_rationale` notes.
- Evidence: CSV path and `input_row_ids` for drill-through.
- Deterministic output hash via `_hash_df()` for reproducibility.
Policy:
- Materiality threshold = $50k.
- Auto-approval allowed only for immaterial, clear duplicate/split patterns. Forensic-risk heuristics above materiality never auto-approve.

### AR — `src/r2r/engines/ap_ar_recon.py::ar_reconciliation()`
Deterministic rules:
- Overdue or `age_days > 60`.
- Forensic patterns:
  - Channel stuffing: large invoices near month-end plus extended terms.
  - Credit memo abuse: significant negative amounts labeled credit.
  - Related party: affiliate-like names with large amounts.
  - Weekend revenue recognition: weekend invoices > $25k.
Policy:
- Materiality = $50k.
- No auto-approval for AR forensic patterns.
Artifact/Evidence:
- `out/run_*/ar_reconciliation_*.json`, evidence links, deterministic hash.

### Bank — `src/r2r/engines/bank_recon.py::bank_reconciliation()`
Deterministic rules:
- Duplicate candidates: exact signature match on `[entity,date,amount,currency,counterparty,transaction_type]` (stable tie-breaker).
- Timing differences: same signature except date within window days (default 3).
- Forensic patterns:
  - Unusual counterparty: cash-advance/loan keyword + > $25k.
  - Velocity anomaly: ≥3 transactions same counterparty same day.
  - Kiting pattern: transfer-out matched by near-equal transfer-in 1–3 days later.
Policy:
- Materiality = $50k.
- Auto-approval only for immaterial duplicates/timing differences.
- Forensic-risk classification (`forensic_risk`) never auto-approves.
Artifact/Evidence:
- `out/run_*/bank_reconciliation_*.json` with `exceptions`, summary, evidence, deterministic hash.

### Intercompany — `src/r2r/engines/intercompany_recon.py::intercompany_reconciliation()`
Deterministic rules:
- Amount mismatch: `|amount_src - amount_dst| > max(materiality[src], materiality[dst])`, default floor $1,000.
- Forensic patterns (deterministic heuristics):
  - Round-dollar anomalies ≥ $10k.
  - Large management fees -> transfer pricing risk.
  - Structuring: ≥3 sub-$10k transactions same day for a pair.
Policy:
- No auto-approval for intercompany exceptions.
Artifact/Evidence:
- `out/run_*/intercompany_reconciliation_*.json` (see current sample run). Evidence includes `input_row_ids` (e.g., IC doc IDs) and deterministic hash.

### Flux analysis — `src/r2r/engines/flux_analysis.py::flux_analysis()`
Deterministic rules:
- Variances vs budget and prior are computed and flagged if abs variance > entity materiality (min $1,000 default floor).
- Provides deterministic AI narrative strings with cited fields; still rule-based.
Artifact/Evidence:
- `out/run_*/flux_analysis_*.json` with `rows`, `exceptions`, `summary`, and evidence references to TB, prior TB, and budget.

### TB Diagnostics — `src/r2r/engines/tb_diagnostics.py::tb_diagnostics()`
Deterministic rules:
- Compute per-entity imbalance and compare to entity-level threshold (e.g., 0.01% of entity size, min $1,000).
- Provide suggestions based on deterministic cues (suspense/clearing, single-driver misposting).
Artifact/Evidence:
- `out/run_*/tb_diagnostics_*.json` with drill-through `input_row_ids` for the entity’s rows and deterministic hash.

---

## 3) Deterministic vs AI-generated outcomes

- Deterministic:
  - All exception detection logic, thresholds, materiality, candidate matching and sorting, auto-approval decisions, and artifact contents are computed deterministically in code.
  - Each engine records a `DeterministicRun` with `output_hash` to support reproducibility and audit.
  - Evidence captures `uri` and `input_row_ids` pointing to exact source rows used.
- AI-generated (assistive only):
  - Per-exception `ai_rationale` strings summarizing why the deterministic rule triggered.
  - Confidence scores attached as annotations; they do not override thresholds but help prioritization.
  - Auto-approval policies are deterministic and checked against materiality and reason/classification.
  - UI/summary narratives and case summaries under `ui/main.py` rely on artifacts and add human-readable AI text. AI cache artifacts are stored under `out/run_*/ai_cache/` in some flows.

Example: Intercompany sample artifact `out/run_20250912T124418Z/intercompany_reconciliation_run_20250912T124418Z.json` shows exceptions with reasons like `ic_round_dollar_anomaly` and `ic_structuring_pattern`, `confidence_score`, and `ai_rationale`. Auto-approval remains `false` for all IC entries by policy.

---

## 4) Surfacing in the UI and HITL

- UI endpoints — `ui/main.py`:
  - `/bank`, `/ap`, `/ar`, `/intercompany` pages load latest artifacts from `out/run_*/` via helper functions (e.g., `_load_bank_reconciliation_data()`, `_load_ap_reconciliation_data()`).
  - Compatibility mapping ensures Intercompany artifacts align with the shared UI template fields.
- HITL case generation — `ui/main.py::_generate_sample_hitl_cases()`:
  - Pulls first forensic-risk exceptions (e.g., bank `classification == 'forensic_risk'`) and [FORENSIC] flux narratives to seed example HITL cases.
  - HITL API supports assignment and resolution; in production replace in-memory with DB.

---

## 5) Materiality, policy and control alignment

- Entity-level thresholds are used in multiple engines (e.g., intercompany pair max threshold, flux threshold per entity).
- Gatekeeping aggregates exceptions and sets an overall close decision with risk level and rationale (`out/run_*/gatekeeping_run_*.json`).
- Auto-approval policies:
  - AP: immaterial duplicate/split patterns may auto-approve; other forensic patterns require review.
  - AR: no auto-approval for forensic patterns.
  - Bank: immaterial duplicates/timing candidates may auto-approve; forensic-risk never auto-approves.
  - Intercompany: no auto-approval.
- Each exception carries fields enabling audit sampling and drill-through.

---

## 6) Big 4 managed service accounting best practices mapping

- Governance and auditability
  - Deterministic rules with explicit thresholds provide defensible, explainable outcomes.
  - `EvidenceRef` with `uri` + `input_row_ids` enables item-level traceability and re-performance.
  - `DeterministicRun` with `output_hash` supports reproducibility and tamper-evidence.
- Controls alignment (SOX/ICFR)
  - Duplicate detection, timing differences, and intercompany true-up proposals align with standard close controls.
  - Forensic-risk patterns route to HITL instead of auto-approving, ensuring appropriate review and authorization.
  - Materiality-based auto-approve is policy-gated and conservative; configurable per entity.
- Segregation of duties and approvals
  - Auto-approval limited to immaterial, low-risk categories; forensic items require analyst review.
  - HITL endpoints provide assignment and resolution flows; journal entry generation remains DRAFT pending approval in `ui/main.py` logic.
- Sampling and evidence
  - Artifacts include counts, by-entity rollups, and exception lists to support sampling frameworks.
  - Confidence scores aid prioritization but do not substitute control criteria.
- Change management
  - Rules reside in version-controlled engine modules; modifications are code-reviewed and testable under `tests/`.

---

## 7) Operational notes and reproducibility

- Random seeds in scenario-generation scripts ensure consistent patterns in demo data.
- Engines are pure-deterministic on the same inputs, yielding the same artifacts and `output_hash`.
- AI cache files do not influence exception inclusion/exclusion; they store assistive narratives only.

---

## 8) Quick reference: files and functions

- Data seeding
  - `scripts/create_forensic_patterns.py`
  - `scripts/add_forensic_scenarios.py`
- Engines (deterministic detection)
  - AP/AR: `src/r2r/engines/ap_ar_recon.py::{ap_reconciliation, ar_reconciliation}`
  - Bank: `src/r2r/engines/bank_recon.py::bank_reconciliation`
  - Intercompany: `src/r2r/engines/intercompany_recon.py::intercompany_reconciliation`
  - Flux: `src/r2r/engines/flux_analysis.py::flux_analysis`
  - TB: `src/r2r/engines/tb_diagnostics.py::tb_diagnostics`
- Audit trail and artifacts
  - Run audit log: `out/run_*/audit_*.jsonl`
  - Engine artifacts: `out/run_*/<module>_*_run_*.json`
  - AI cache (assistive): `out/run_*/ai_cache/*.json`

---

## 9) Example: Intercompany artifact snapshot

From `out/run_20250912T124418Z/intercompany_reconciliation_run_20250912T124418Z.json`:

- Exceptions include reasons `ic_round_dollar_anomaly` and `ic_structuring_pattern` with `confidence_score` annotations and `auto_approve: false` by policy.
- `rules` section cites the mismatch rule and default floor.
- `summary` includes `count`, `total_diff_abs`, and `by_pair_diff_abs` with no true-up proposals when mismatches are zero but patterns merit review.

---

## 10) Deployment and environment (for local runs)

- Use a project-local virtual environment to ensure isolation on Windows.
- Recommended: Python 3.11.x, venv at `.venv` in the repo root.
- Activate and run as needed (e.g., API/UI) ensuring dependencies from `requirements.txt` are installed locally (not globally).

This approach yields explainable, auditable, and reproducible outcomes aligned to Big 4 managed service standards while leveraging AI strictly as an assistive layer for rationale and prioritization.
