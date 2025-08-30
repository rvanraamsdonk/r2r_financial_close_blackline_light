# R2R Financial Close - HTMX Web UI

Simple, server-first web interface for R2R Financial Close system using FastAPI + HTMX + Tailwind.

## Features

- **Zero Build Complexity**: No npm, TypeScript, or client-side build pipeline
- **Direct Artifact Loading**: Reads existing JSON artifacts from `/out/` directory
- **Real-time Updates**: Server-Sent Events for workflow progress
- **Audit-Ready**: Complete provenance tracking and evidence drill-through
- **Professional UI**: Clean, modern interface suitable for Big 4 presentations

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python main.py

# Or with uvicorn directly
uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Open http://localhost:8080 to view the dashboard.

## Architecture

```
/web_ui/
├── main.py              # FastAPI server with artifact loading
├── templates/           # Jinja2 templates
│   ├── base.html       # Base template with HTMX/Tailwind
│   ├── dashboard.html  # Run overview and KPIs
│   ├── close_detail.html # Workflow progress
│   └── reconciliation.html # AP/AR/Bank/IC details
├── static/             # Static assets (HTMX via CDN)
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## Data Flow

```
/out/run_*/artifacts.json → FastAPI routes → Jinja templates → HTMX partials
```

## Technology Stack

- **Backend**: FastAPI (Python 3.11+)
- **Templates**: Jinja2 with server-side rendering
- **Interactivity**: HTMX for partial page updates
- **Styling**: Tailwind CSS (utility-first via CDN)
- **Real-time**: Server-Sent Events for progress updates

## API Endpoints

- `GET /` - Dashboard with run overview
- `GET /run/{timestamp}` - Close run detail view
- `GET /run/{timestamp}/reconciliation/{type}` - Reconciliation details
- `GET /run/{timestamp}/flux` - Flux analysis
- `GET /run/{timestamp}/cases` - HITL cases
- `GET /api/runs` - JSON API for runs list
- `GET /api/run/{timestamp}/artifact/{name}` - JSON API for artifacts

## Environment Variables

None required - system auto-discovers artifacts in `/out/` directory.

## Development

The UI is completely separate from backend scripts and requires no dependencies beyond FastAPI. All data is loaded read-only from existing JSON artifacts.

For development with auto-reload:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```
