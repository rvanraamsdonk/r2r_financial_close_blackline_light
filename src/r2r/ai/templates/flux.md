You are analyzing financial variance data for period {{ period }}.

Key variances to explain:
{% for variance in top_variances %}
- {{ variance.entity }}/{{ variance.account }}: Budget variance {{ variance.var_vs_budget }} USD ({{ variance.band_vs_budget }})
{% endfor %}

Generate explanatory narratives for the top variances. Each narrative should:
- Explain the business reason for the variance
- Reference specific accounts and amounts
- Suggest potential root causes

Required JSON output format:
{
  "generated_at": "{{ generated_at }}",
  "period": "{{ period }}",
  "entity_scope": "{{ entity }}",
  "narratives": [
    {
      "entity": "ENT100",
      "account": "1000", 
      "narrative": "Account 1000 shows a budget variance of $195K due to...",
      "confidence": "high",
      "root_cause": "seasonal_adjustment"
    }
  ],
  "citations": {{ citations | tojson }}
}
