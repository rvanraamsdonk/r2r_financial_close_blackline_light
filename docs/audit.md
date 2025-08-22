# Audit Logging and Provenance

This document explains how the R2R system writes audit records, how evidence provenance is captured at row level, and how to verify it.

## Architecture and Modules

- **`src/r2r/audit/log.py`**: `AuditLogger.append()` writes a single JSON object per line to `out/audit_<run_id>.jsonl`, automatically adding a UTC timestamp field `ts`.
- **`src/r2r/schemas.py`**: Defines provenance models:
  - `EvidenceRef` (fields: `id`, `type`, `uri`, `input_row_ids`, `timestamp`, `hash`)
  - `DeterministicRun` (fields: `id`, `function_name`, `code_hash`, `params`, `row_ids`, `output_hash`, `timestamp`)
- **Engines** (where evidence is emitted):
  - `src/r2r/engines/tb_diagnostics.py`: writes an `evidence` record referencing `trial_balance_<period>.csv` with `input_row_ids` per TB row.
  - `src/r2r/engines/accruals.py`: writes an `evidence` record referencing `supporting/accruals.csv` with `input_row_ids` for exception rows.
  - `src/r2r/engines/email_evidence.py`: writes an `evidence` record referencing `supporting/emails.json` with `input_row_ids` of `email_id` values.

## Audit File Location and Naming

- Directory: `out/`
- File pattern: `audit_<run_id>.jsonl`, where `<run_id>` encodes the run timestamp.
- Each line is a standalone JSON object; consumers should read the file as JSONL.

## Record Types

Two primary record types are written by engines:

- `type: "evidence"`
  - Fields: `id`, `evidence_type`, `uri`, `input_row_ids`, `timestamp` (ISO 8601, Zulu), plus global `ts` added by logger.
  - Purpose: capture row-level lineage from source data to outputs.

- `type: "deterministic"`
  - Fields: `fn`, `evidence_id`, `output_hash`, `params`, `artifact`, plus global `ts`.
  - Purpose: record function execution, configuration, and a stable hash of the output for reproducibility.

The deterministic record references the evidence via `evidence_id` for traceability.

## Row-level Provenance (input_row_ids)

- **TB Diagnostics** (`tb_diagnostics`)
  - `uri`: `data/lite/trial_balance_<period>.csv`
  - `input_row_ids` format: `"<period>|<entity>|<account>"` per trial balance row included in diagnostics.

- **Accruals** (`accruals_check`)
  - `uri`: `data/lite/supporting/accruals.csv`
  - `input_row_ids` format: typically `"<entity>|<accrual_id>"` for rows that triggered exceptions.

- **Email Evidence** (`email_evidence`)
  - `uri`: `data/lite/supporting/emails.json`
  - `input_row_ids` format: `"<email_id>"` for each relevant email captured.

These identifiers enable drill-through from audit to the exact CSV rows.

## Minimal Examples

Evidence (TB Diagnostics):

```json
{
  "ts": "2025-08-22T15:03:09.871Z",
  "type": "evidence",
  "id": "ev-...",
  "evidence_type": "csv",
  "uri": "/.../data/lite/trial_balance_2025-08.csv",
  "input_row_ids": ["2025-08|ENT100|1000", "2025-08|ENT100|1100"],
  "timestamp": "2025-08-22T15:03:09.871Z"
}
```

Deterministic (TB Diagnostics):

```json
{
  "ts": "2025-08-22T15:03:09.872Z",
  "type": "deterministic",
  "fn": "tb_diagnostics",
  "evidence_id": "ev-...",
  "output_hash": "...",
  "params": {"period": "2025-08", "entity": "ALL"},
  "artifact": "/.../out/tb_diagnostics_20250822T150309Z.json"
}
```

Evidence (Accruals):

```json
{
  "ts": "2025-08-22T15:03:09.874Z",
  "type": "evidence",
  "id": "ev-...",
  "evidence_type": "csv",
  "uri": "/.../data/lite/supporting/accruals.csv",
  "input_row_ids": ["ENT100|ACR-2025-08-ENT100-001"],
  "timestamp": "2025-08-22T15:03:09.873Z"
}
```

## Verifying Provenance

A helper script validates that required evidence is present and wired to deterministic runs:

- Script: `scripts/verify_provenance.py`
- Usage (venv):

```bash
.venv/bin/python scripts/verify_provenance.py  # auto-picks latest audit
# or
.venv/bin/python scripts/verify_provenance.py --audit out/audit_YYYYmmddTHHMMSSZ.jsonl
```

Expected success output:

```text
[DET] Provenance verification PASSED: input_row_ids present for tb_diagnostics, accruals_check, and email_evidence
```

If failures occur, the script lists missing/invalid sections.

## Drill-through Utility

Use the helper script to display the exact source rows referenced by `input_row_ids` in the latest audit log:

```bash
.venv/bin/python scripts/drill_through.py --fn tb_diagnostics
.venv/bin/python scripts/drill_through.py --fn accruals_check
.venv/bin/python scripts/drill_through.py --fn email_evidence
```

The script auto-selects the latest `out/audit_*.jsonl` if `--audit` is not provided.

## Design Notes

- The logger injects `ts` on every record; engines may also include their own event timestamps (e.g., `EvidenceRef.timestamp`).
- Deterministic `output_hash` is derived from the exported artifact content to allow reproducibility checks.
- Evidence is appended before the deterministic record to ensure `evidence_id` references resolve sequentially in the log.
