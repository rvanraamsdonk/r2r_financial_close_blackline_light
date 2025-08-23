# Flux AI Prompt Template

Objective: Generate grounded narratives for variances with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- counts: {{ counts | tojson }}

Output schema: FluxAI (see src/r2r/ai/schemas.py)
