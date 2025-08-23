# Controls AI Prompt Template

Objective: Summarize control-owners and residual risks with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- controls_notable: {{ controls_notable | tojson }}

Output schema: ControlsAI (see src/r2r/ai/schemas.py)

Return ONLY strict JSON conforming to ControlsAI. No prose or markdown.
