# Runbook & CLI

## Prerequisites
- Python 3.11+ (use project venv)
- Data available in `./data/lite/`

## Single-Command Run (planned)
```
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
