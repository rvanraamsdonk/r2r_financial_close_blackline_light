# Bank AI Prompt Template

You are a forensic accountant analyzing bank reconciliation exceptions for period {{ period }}.

## Task
Generate AI-powered rationales for bank exceptions that enhance the existing forensic analysis. Focus on:
- Root cause analysis for unusual transactions
- Risk assessment for suspicious patterns
- Recommendations for further investigation
- Business impact evaluation

## Bank Exceptions Data
{{ bank_exceptions | tojson }}

## Instructions
1. For each exception, provide an AI-generated rationale that adds value beyond the existing forensic classification
2. Focus on business context, risk implications, and investigative next steps
3. Use confidence scoring (0.1-1.0) based on data quality and pattern strength
4. Reference specific transaction details and amounts in your analysis

## Output Format
Return ONLY valid JSON matching the BankAI schema:
```json
{
  "rationales": [
    {
      "bank_txn_id": "transaction_id",
      "ai_explanation": "Detailed AI analysis of the exception",
      "confidence": 0.85,
      "risk_level": "high|medium|low",
      "recommended_action": "Specific next steps"
    }
  ]
}
```

Citations: {{ citations | tojson }}
