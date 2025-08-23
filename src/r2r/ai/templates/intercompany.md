# Intercompany AI Prompt Template

Objective: Propose match rationale and JE proposals with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- counts: {{ counts | tojson }}

Output schema: ICAI (see src/r2r/ai/schemas.py)
