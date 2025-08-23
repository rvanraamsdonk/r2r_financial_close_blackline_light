# Validation AI Prompt Template

Objective: Summarize validation issues, root causes, and remediations with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- counts: {{ counts | tojson }}
- citations: {{ citations | tojson }}
- categories: {{ categories | tojson }}
- totals: {{ totals | tojson }}

Output schema: ValidationAI (see src/r2r/ai/schemas.py)

Return ONLY strict JSON conforming to ValidationAI. No prose or markdown.
