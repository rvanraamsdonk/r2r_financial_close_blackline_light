# R2R Console UI v6 – Printable Spec

This spec defines a clean, professional, and audit-ready console format optimized for senior Big 4 accountants. It favors full visibility, no truncation, minimal visual noise, and strong AI explainability with clear provenance and evidence.

## 0. Global Principles
- Full lists by default. No hidden exceptions.
- Minimal separators. No box borders. Clear section headers with stats.
- Stable columns. Avoid jitter. Keep first line compact and scannable.
- AI transparency. Rationale + confidence clearly separated from the main row.
- Clickthroughs via terminal hyperlinks (OSC-8) with absolute-path fallback.
- Persistent, stable IDs to support drill-through and audit trails.

## 1. Section Header Format

```text
N. SECTION NAME  —  items=X open=Y resolved=Z  •  eta_auto=Mm  eta_manual=Hh  •  run=RUN_ID  model=MODEL@VER
--------------------------------------------------------------------------------
```
- N: integer section number
- Compact stats: items/open/resolved
- Time: automation and manual estimates, unit-appropriate
- Footer attributes may also appear here for convenience: run, model@ver

## 2. Row Format (Four-line block)
- Line 1: Key columns + action
- Line 2: Recommendation with confidence tag
- Line 3: WHY (rationale only)
- Line 4: Evidence (multi-link)
- Line 5: Provenance (with item IDs)

Example:

```text
ID=AP-001  Vendor=Google  Inv=INV-94421  Amt=-$12,500  Due=2025-09-05  Owner=AP_Team
AI recommends: Write-off duplicate payment [Conf; 89%]
WHY: Payment matched 2 bank debits for same invoice; vendor confirms overpay
Evidence: file:///abs/path/evidence/email_123.eml  file:///abs/path/bank/2025-08.csv#L219-223
Provenance: ap_reconciliation_20250823T143836Z.json:item_id=AP-001
```

Notes:
- IDs are stable across runs when source identity is stable.
- Confidence shown on the recommendation line: `[Conf; NN%]`.
- WHY line contains rationale only.
- Multi-evidence: space-separated links. Use OSC-8 where terminals support it.
- Provenance always includes artifact filename and `item_id`.

## 3. Hyperlinking Strategy
- Primary: ANSI OSC-8 hyperlinks `\x1b]8;;URL\x1b\\label\x1b]8;;\x1b\\`
- Fallback: print absolute file paths (clickable in most terminals).
- Prefer explicit anchors (e.g., `#L123-130`) when meaningful.

## 4. Sections and Artifacts
- AP Reconciliation → `ap_reconciliation_YYYYmmddTHHMMSSZ.json`
- AR Reconciliation → `ar_reconciliation_YYYYmmddTHHMMSSZ.json`
- Flux Analysis → `flux_analysis_YYYYmmddTHHMMSSZ.json`
- Bank Reconciliation → `bank_reconciliation_YYYYmmddTHHMMSSZ.json`
- JE Lifecycle → `je_lifecycle_YYYYmmddTHHMMSSZ.json`
- Accruals → `accruals_YYYYmmddTHHMMSSZ.json`

For each item, expect fields:
- Identity: `id` (or construct from domain keys, e.g., `AP-<invoice_no>`)
- Ownership & timing: `owner`, `due_date`, `sla`
- Amounts/direction: signed amounts, currency
- AI: `ai.recommended_action`, `ai.rationale_short`, `ai.confidence` (0–1)
- Evidence: list of paths/URLs
- Provenance: `artifact_path`, `item_id`

## 5. Footer
At end of the report:
```text
—
AI: Model=MODEL@VER  Policy=assist  ShowPrompts=false  SaveEvidence=true
Paths: data=... out=...
Run: RUN_ID  CodeHash=abcdef123456
```

## 6. Style Cues
- Use modest color only for section titles if available (e.g., cyan, bold headers). Body remains neutral.
- No ASCII boxes. Use a single thin rule per section.
- Keep to 100–120 col where possible; wrap only the WHY line if needed.

## 7. Drill-through Compatibility
- IDs are numeric- or code-typed and stable.
- Evidence links openable via terminal click.
- Provenance item IDs allow `scripts/drill_through.py` to retrieve details.

## 8. Example (AP)

```text
1. AP RECONCILIATION  —  items=12 open=3 resolved=9  •  eta_auto=3m  eta_manual=0.8h  •  run=20250823T143836Z  model=gpt-4o@2025-08
--------------------------------------------------------------------------------
ID=AP-001  Vendor=Google  Inv=INV-94421  Amt=-$12,500  Due=2025-09-05  Owner=AP_Team
AI recommends: Write-off duplicate payment [Conf; 89%]
WHY: Payment matched 2 bank debits for same invoice; vendor confirms overpay
Evidence: file:///abs/path/evidence/email_123.eml  file:///abs/path/bank/2025-08.csv#L219-223
Provenance: ap_reconciliation_20250823T143836Z.json:item_id=AP-001
```

## 9. Implementation Notes
- Renderer will scan `out/` for latest timestamp and render available sections.
- Where `id` is absent, derive stabilized key from domain fields (e.g., AP: invoice_no or hash of vendor+inv+amt).
- Confidence formatting: `pct = round(confidence*100)`. Show on the recommendation line.
- Evidence: print both OSC-8 hyperlinks and absolute paths for resilience.
