# HITL AI Prompt Template

Objective: Summarize evidence and recommend next actions with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- counts: {{ counts | tojson }}
- open_cases: {{ open_cases | tojson }}

Output schema: HITLAI (see src/r2r/ai/schemas.py)

Return ONLY strict JSON conforming to HITLAI. No prose or markdown.
