# Runbook & CLI

## Prerequisites

- Python 3.11+ (use project venv)
- Data available in `./data/lite/`

## Single-Command Run (planned)

```bash
python -m r2r.app --period 2025-08 --entity ALL --ai-mode assist --data ./data/lite --out ./out
```

### Flags (minimal)

- `--period`: YYYY-MM
- `--entity`: entity code or ALL
- `--ai-mode`: off | assist | strict
- `--show-prompts`: include prompts in evidence pack
- `--save-evidence`: export provenance JSON and artifacts

## Outputs

- Close Pack: registers, controls matrix, metrics, narratives ([DET]/[AI] labeled)
- Evidence bundle: inputs, computations, prompts, model metrics, code/config hash

## Operational Notes

- Idempotent: safe to re-run; postings trigger re-checks automatically
- Materiality thresholds and policies are read from config & inputs
- All narratives and suggestions are grounded in computed facts; no hard-coded text

---

## Current Run Command (venv)

Use the project venv’s Python directly:

```bash
.venv/bin/python scripts/run_close.py --period 2025-08
```

Notes:
- Period format is `YYYY-MM`.
- Environment variables are loaded from root `.env` (via python-dotenv `find_dotenv`).

## Verify Provenance (row-level lineage)

Verify that `tb_diagnostics`, `accruals_check`, and `email_evidence` all have non-empty `input_row_ids`:

```bash
.venv/bin/python scripts/verify_provenance.py
```

Behavior:
- Always prints the audit path in use and a PASS/FAIL line.
- Example PASS output:

```text
[DET] Using audit: out/audit_YYYYmmddTHHMMSSZ.jsonl
[DET] Provenance verification PASSED: input_row_ids present for tb_diagnostics, accruals_check, and email_evidence
[DET] Verification completed successfully.
```

Optionally target a specific audit:

```bash
.venv/bin/python scripts/verify_provenance.py --audit out/audit_YYYYmmddTHHMMSSZ.jsonl
```

## Smoke Test (quick check)

Run a lightweight smoke test that reuses the verification logic on the latest audit:

```bash
.venv/bin/python scripts/smoke_test.py
```

Optional: specify an audit file explicitly:

```bash
.venv/bin/python scripts/smoke_test.py --audit out/audit_YYYYmmddTHHMMSSZ.jsonl
```

## Drill-Through to Source Data

Show the exact source rows referenced by the audit evidence for a given function:

```bash
.venv/bin/python scripts/drill_through.py --fn {tb_diagnostics|accruals_check|email_evidence}
```

Use a specific audit file (optional):

```bash
.venv/bin/python scripts/drill_through.py --fn tb_diagnostics --audit out/audit_YYYYmmddTHHMMSSZ.jsonl
```

Optional output controls:

- Limit number of rows printed:

```bash
.venv/bin/python scripts/drill_through.py --fn tb_diagnostics --limit 10
```

- Print JSON instead of CSV:

```bash
.venv/bin/python scripts/drill_through.py --fn accruals_check --format json
```

Notes:
- TB evidence file uses underscore period format `trial_balance_YYYY_MM.csv` (standardized at the source). The script also tolerates older hyphenated URIs.
- Accruals source: `data/lite/supporting/accruals.csv` keyed by `entity|accrual_id`.
- Email evidence: `data/lite/supporting/emails.json` keyed by `email_id`.
