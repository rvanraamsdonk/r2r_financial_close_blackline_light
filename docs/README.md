# R2R Financial Close (Light) — Documentation Index

This documentation describes a deterministic, policy-aligned financial close enhanced with visible AI assistance. All numbers are computed; AI assists with explanations, matching suggestions, and risk narratives. No hard-coded strings; all outputs are derived from the real data in `data/lite/`.

- Quickstart (venv-friendly)

```bash
python3 -m venv .venv
. .venv/bin/activate
.venv/bin/pip install -r requirements.txt

# Run the close (defaults from .env)
.venv/bin/python scripts/run_close.py --period 2025-08

# Verify provenance (latest audit)
.venv/bin/python scripts/smoke_test.py
```

- CLI flags summary
  - `--period` YYYY-MM
  - `--prior` prior period YYYY-MM (optional)
  - `--entity` entity code or ALL
  - `--ai-mode` off | assist | strict
  - `--data` input data path (default `data/lite`)
  - `--out` output path (default `out`)
  - `--show-prompts` include prompts in evidence pack
  - `--save-evidence` export provenance JSON and artifacts

- Overview brief: `brief.md`
- Functional modules (end-to-end sequence): `functional_modules.md`
- AI transparency and labeling ([DET]/[AI]/[HYBRID]): `ai_transparency.md`
- Provenance and evidence schema: `provenance_schema.md`
- Email evidence engine and drill-through: `email_evidence.md`
- Demo script (skeptic-proof): `demo_script.md`
- Metrics and controls mapping: `metrics_and_controls.md`
- Data dictionary (files and semantics): `data_dictionary.md`
- Runbook & CLI usage: `runbook_cli.md`
- Architecture overview: `architecture.md`

See the repository root `README.md` for project-level details.
