# Intercompany AI Prompt Template

Objective: Propose match rationale and JE proposals with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- counts: {{ counts | tojson }}
- ic_exceptions: {{ ic_exceptions | tojson }}

Output schema: ICAI (see src/r2r/ai/schemas.py)

Return ONLY strict JSON conforming to ICAI. No prose or markdown.
