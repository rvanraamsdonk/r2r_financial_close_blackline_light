# Bank AI Prompt Template

Objective: Explain timing differences and error rationales with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}

Output schema: BankAI (see src/r2r/ai/schemas.py)
