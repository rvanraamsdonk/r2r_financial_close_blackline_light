# Bank AI Prompt Template

Objective: Explain timing differences and error rationales with citations.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- citations: {{ citations | tojson }}
- bank_exceptions: {{ bank_exceptions | tojson }}

Output schema: BankAI (see src/r2r/ai/schemas.py)

Return ONLY strict JSON conforming to BankAI. No prose or markdown.
