# AP/AR AI Prompt Template

Objective: Suggest fuzzy matches and next actions with confidence and citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- unresolved_summary: {{ unresolved_summary | tojson }}
- citations: {{ citations | tojson }}

Output schema: APARAI (see src/r2r/ai/schemas.py)

.venv/bin/python scripts/run_close.py
