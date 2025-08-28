Generate an executive summary for the financial close report for period {{ period }}.

Based on the close data, provide a concise executive summary covering:
- Overall close status and key metrics  
- Material exceptions and their business impact
- Risk assessment and recommendations
- Next steps for period closure

Required JSON output format:
{
  "generated_at": "{{ generated_at }}",
  "period": "{{ period }}",
  "entity_scope": "{{ entity }}",
  "executive_summary": "The {{ period }} financial close identified 47 flux exceptions totaling $X across 3 entities. Key findings include...",
  "citations": {{ citations | tojson }}
}
