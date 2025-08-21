# R2R Agentic Close (LangGraph, Python, Console)

Console-first, agentic Record-to-Report close scaffold with synthetic datasets, HITL gates, and Azure OpenAI stubs.

## Setup
1) Python 3.10+ recommended.
2) `pip install -r requirements.txt`
3) Optional: copy `.env.example` to `.env` and set Azure OpenAI values. By default, AI calls are stubbed.

## Run
```bash
python scripts/run_close.py --period 2025-08 --prior 2025-07 --entities 6 --seed 42
```

## Tests
```bash
pytest -q
```

## Azure OpenAI
- Uses deployment names (not model IDs).
- Toggle live calls with `R2R_ALLOW_NETWORK=1` in `.env`.
