# Flux AI Prompt Template

Objective: Generate grounded narratives for variances with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- counts: {{ counts | tojson }}
- top_variances: {{ top_variances | tojson }}

Output schema: FluxAI (see src/r2r/ai/schemas.py)

Return ONLY strict JSON conforming to FluxAI. No prose or markdown.
