# Email Evidence Analysis

This page documents the deterministic email evidence step that extracts relevant messages from `supporting/emails.json`, emits an artifact for review, and records row-level provenance in the audit log.

## Overview

- Engine: `src/r2r/engines/email_evidence.py`
- Workflow position: runs after `accruals_check` and before metrics, see `src/r2r/graph.py`
- Deterministic: uses only static inputs and simple filters; outputs include a stable content hash in the audit log

## Data Source

- Path: `data/lite/supporting/emails.json`
- Schema (per item):
  - `email_id` (string)
  - `subject`, `from`, `to`, `timestamp`, `body`, `summary`
  - `linked_transactions` (array of strings)
  - `priority`, `category`, `requires_action` (bool)

## Logic

- Relevance criteria (any true):
  - `timestamp` falls within the run `period` (YYYY-MM)
  - `timestamp` is the first day of the next month (captures cutoff-related messages)
  - `requires_action` is true
- Produces:
  - Artifact: `out/email_evidence_<run_id>.json` with `items` and a rollup `summary`
  - Audit `evidence` record with `input_row_ids` = list of `email_id`
  - Audit `deterministic` record referencing the evidence and artifact

## Audit Records

Evidence:

```json
{
  "type": "evidence",
  "id": "ev-...",
  "evidence_type": "json",
  "uri": "/.../data/lite/supporting/emails.json",
  "input_row_ids": ["EMAIL-001", "EMAIL-002"],
  "timestamp": "2025-08-22T16:41:41Z",
  "ts": "2025-08-22T16:41:41Z"
}
```

Deterministic:

```json
{
  "type": "deterministic",
  "fn": "email_evidence",
  "evidence_id": "ev-...",
  "output_hash": "...",
  "params": {"period": "2025-08", "entity": "ALL"},
  "artifact": "/.../out/email_evidence_20250822T164141Z.json",
  "ts": "2025-08-22T16:41:41Z"
}
```

## Drill-through

Use the helper script to view the exact email records referenced by `input_row_ids`:

```bash
.venv/bin/python scripts/drill_through.py --fn email_evidence
```

The script selects the latest `out/audit_*.jsonl` by default; use `--audit` to specify a file.

## Running the Pipeline

Run the full workflow with venv Python to generate the artifact and audit entries:

```bash
.venv/bin/python scripts/run_close.py --period 2025-08
```

Relevant console output includes a deterministic message like:

```text
[DET] Email evidence: relevant=5 requires_action=4 -> .../out/email_evidence_<run_id>.json
```
