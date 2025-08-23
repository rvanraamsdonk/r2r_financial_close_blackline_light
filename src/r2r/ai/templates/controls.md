# Controls AI Prompt Template

Objective: Summarize control-owners and residual risks with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}

Output schema: ControlsAI (see src/r2r/ai/schemas.py)
