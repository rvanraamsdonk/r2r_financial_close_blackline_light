# AP/AR AI Prompt Template

Objective: Suggest grounded fuzzy matches and next actions between AP bills and AR invoices, using the provided deterministic exception slices. Return JSON ONLY.

Inputs:

- period: {{ period }}
- entity: {{ entity }}
- unresolved_summary: {{ unresolved_summary | tojson }}
- citations: {{ citations | tojson }}
- ap_exceptions (top, compact): {{ ap_exceptions | tojson }}
- ar_exceptions (top, compact): {{ ar_exceptions | tojson }}

Response policy:

- Output strictly valid JSON with the following schema keys for APARAI:
  {
    "matches": [
      {
        "ap_bill_id": "...",
        "ar_invoice_id": "...",
        "confidence": 0.0,
        "reason": "short rationale citing fields (amount/date/vendor/customer)",
        "support": {"amount_delta": 0.0, "date_gap_days": 0, "signals": ["amount_close", "date_near", "same_entity"]}
      }
    ],
    "unresolved_summary": {"ap_exceptions": 0, "ar_exceptions": 0},
    "citations": {{ citations | tojson }}
  }

Guidance:

- Prefer matching within the same entity; amount should be very close; dates within ~30 days.
- If no strong match exists for an item, omit it from matches (do not fabricate).
- Keep matches concise (max 12 total). Use the deterministic candidates in each exception as hints only.
