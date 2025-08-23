# HITL AI Prompt Template

Objective: Summarize evidence and recommend next actions with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- counts: {{ counts | tojson }}

Output schema: HITLAI (see src/r2r/ai/schemas.py)
