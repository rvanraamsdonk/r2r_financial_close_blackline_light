# Accruals AI Prompt Template

Objective: Draft JE narratives and rationales with evidence citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- accruals_exceptions: {{ accruals_exceptions | tojson }}
- accruals_proposals: {{ accruals_proposals | tojson }}

Output schema: AccrualsAI (see src/r2r/ai/schemas.py)

Return ONLY strict JSON conforming to AccrualsAI. No prose or markdown.
