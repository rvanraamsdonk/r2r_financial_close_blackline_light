Generate an executive summary for the financial close report for period {{ period }}.

Based on the close data, provide a concise executive summary covering:
- Overall close status and key metrics  
- Material exceptions and their business impact
- Risk assessment and recommendations
- Next steps for period closure

{% if highlights.risk_level %}
IMPORTANT: Use the deterministic risk assessment from gatekeeping:
- Risk Level: {{ highlights.risk_level }}
- Block Close: {{ highlights.block_close }}
{% endif %}

Required JSON output format:
{
  "generated_at": "{{ generated_at }}",
  "period": "{{ period }}",
  "entity_scope": "{{ entity }}",
  "executive_summary": "The {{ period }} financial close identified 47 flux exceptions totaling $X across 3 entities. Key findings include...{% if highlights.risk_level %} Risk assessment indicates a {{ highlights.risk_level }} risk level{% if highlights.block_close %}, requiring close to be blocked pending resolution of critical issues{% endif %}.{% endif %}",
  {% if highlights.risk_level %}"risk_level": "{{ highlights.risk_level }}",{% endif %}
  {% if highlights.block_close is not none %}"block_close": {{ highlights.block_close | tojson }},{% endif %}
  "citations": {{ citations | tojson }}
}
