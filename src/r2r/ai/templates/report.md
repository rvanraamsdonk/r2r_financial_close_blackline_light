# Close Report AI Prompt Template

Objective: Create an executive summary with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}

Output schema: ReportAI (see src/r2r/ai/schemas.py)
