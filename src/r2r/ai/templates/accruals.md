# Accruals AI Prompt Template

Objective: Draft JE narratives and rationales with evidence citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}

Output schema: AccrualsAI (see src/r2r/ai/schemas.py)
