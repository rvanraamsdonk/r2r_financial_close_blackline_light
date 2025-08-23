# Validation AI Prompt Template

Objective: Summarize validation issues, root causes, and remediations with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- counts: {{ counts | tojson }}
- citations: {{ citations | tojson }}

Output schema: ValidationAI (see src/r2r/ai/schemas.py)
