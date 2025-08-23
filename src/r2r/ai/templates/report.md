# Close Report AI Prompt Template

Objective: Create an executive summary with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- highlights: {{ highlights | tojson }}

Output schema: ReportAI (see src/r2r/ai/schemas.py)

Return ONLY strict JSON conforming to ReportAI. No prose or markdown.
