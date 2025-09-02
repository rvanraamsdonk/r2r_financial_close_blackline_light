# R2R Financial Close Dashboard UI (HTMX)

This UI is a lightweight, read-only dashboard that renders mock close data similar to the BlackLine example. It is isolated under `ui/` and does not modify or depend on the core system.

- Stack: FastAPI + Jinja2 templates + HTMX + Tailwind (CDN)
- Location: `ui/`
- Entry point: `ui/main.py`
- Templates: `ui/templates/` (with `partials/`)
- Static files: `ui/static/`

## Run (venv)

```bash
# From repo root, always use the project venv
. .venv/bin/activate
python -m pip install -r ui/requirements.txt
uvicorn ui.main:app --reload --port 8000
```

Open: http://127.0.0.1:8000/

## Structure

- `ui/main.py`: FastAPI app, mock data provider, endpoints for page and partials
- `ui/templates/base.html`: Base template (Tailwind, HTMX)
- `ui/templates/index.html`: Dashboard page with HTMX regions
- `ui/templates/partials/kpis.html`: KPI tiles (clock, totals, prepared/completed)
- `ui/templates/partials/recon_progress.html`: Segmented progress bar + cards

## Notes

- All numbers are deterministic mocks; replace `mock_close_data()` with live reads from `/out/` artifacts later.
- HTMX auto-refreshes KPIs and reconciliation progress every 60s.
- Tailwind is included via CDN for zero-build simplicity.
