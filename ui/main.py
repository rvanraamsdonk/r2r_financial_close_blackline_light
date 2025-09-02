from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from dataclasses import dataclass, field
import json
import os
import glob
import uuid

app = FastAPI(title="R2R Close – Dashboard UI (HTMX)")

# Mount static for future assets (css/js/images) if needed
import os
if os.path.exists("ui/static"):
    app.mount("/static", StaticFiles(directory="ui/static"), name="static")
elif os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

if os.path.exists("ui/templates"):
    templates = Jinja2Templates(directory="ui/templates")
else:
    templates = Jinja2Templates(directory="templates")


# ---- Journal Entry Data Models ---------------------------------------------

class JEStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"

@dataclass
class JELine:
    account: str
    description: str
    debit: float = 0.0
    credit: float = 0.0

@dataclass
class JournalEntry:
    id: str
    module: str
    scenario: str
    entity: str
    period: str
    description: str
    lines: List[JELine] = field(default_factory=list)
    status: JEStatus = JEStatus.DRAFT
    source_data: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    @property
    def total_debits(self) -> float:
        return sum(line.debit for line in self.lines)
    
    @property
    def total_credits(self) -> float:
        return sum(line.credit for line in self.lines)
    
    @property
    def is_balanced(self) -> bool:
        return abs(self.total_debits - self.total_credits) < 0.01

# In-memory JE storage (in production, this would be a database)
_je_store: Dict[str, JournalEntry] = {}


# ---- JE Business Logic ------------------------------------------------------

def _create_fx_je(entity: str, account: str, period: str, diff_usd: float, source_data: Dict[str, Any]) -> JournalEntry:
    """Create a journal entry for FX translation differences."""
    je_id = str(uuid.uuid4())[:8]
    
    # Determine accounts based on difference direction
    if diff_usd > 0:
        # Debit FX Gain/Loss, Credit the account
        lines = [
            JELine(account="7200", description="FX Translation Adjustment", debit=abs(diff_usd)),
            JELine(account=account, description=f"FX Revaluation - {entity}", credit=abs(diff_usd))
        ]
    else:
        # Credit FX Gain/Loss, Debit the account  
        lines = [
            JELine(account=account, description=f"FX Revaluation - {entity}", debit=abs(diff_usd)),
            JELine(account="7200", description="FX Translation Adjustment", credit=abs(diff_usd))
        ]
    
    description = f"FX translation adjustment for {entity} account {account} - ${diff_usd:.2f} difference"
    
    return JournalEntry(
        id=je_id,
        module="FX",
        scenario="fx_translation",
        entity=entity,
        period=period,
        description=description,
        lines=lines,
        source_data=source_data
    )

def _create_flux_je(entity: str, account: str, period: str, variance: float, basis: str, source_data: Dict[str, Any]) -> JournalEntry:
    """Create a journal entry for flux analysis variances."""
    je_id = str(uuid.uuid4())[:8]
    
    # Simple accrual/reclassification logic
    if variance > 0:
        # Debit the account, Credit accrual account
        lines = [
            JELine(account=account, description=f"Variance adjustment - {basis}", debit=abs(variance)),
            JELine(account="2300", description="Accrued Expenses", credit=abs(variance))
        ]
    else:
        # Credit the account, Debit accrual account
        lines = [
            JELine(account="2300", description="Accrued Expenses", debit=abs(variance)),
            JELine(account=account, description=f"Variance adjustment - {basis}", credit=abs(variance))
        ]
    
    description = f"Flux analysis adjustment for {entity} account {account} - {basis} variance ${variance:.2f}"
    
    return JournalEntry(
        id=je_id,
        module="Flux",
        scenario="variance_adjustment",
        entity=entity,
        period=period,
        description=description,
        lines=lines,
        source_data=source_data
    )


# ---- Mock data generator ----------------------------------------------------

def mock_close_data() -> Dict[str, Any]:
    # Simple, deterministic mock data similar to the example screenshot
    total_recs = 1235
    total_tasks = 111

    segments = [
        {"label": "Not prepared", "pct": 50, "count": 619, "color": "bg-rose-400"},
        {"label": "<1%", "pct": 1, "count": 5, "color": "bg-gray-300"},
        {"label": "Rejected", "pct": 1, "count": 9, "color": "bg-red-500"},
        {"label": "System decertified", "pct": 2, "count": 24, "color": "bg-yellow-500"},
        {"label": "Prepared", "pct": 3, "count": 35, "color": "bg-orange-400"},
        {"label": "In review", "pct": 1, "count": 8, "color": "bg-blue-300"},
        {"label": "Manually completed", "pct": 2, "count": 24, "color": "bg-emerald-500"},
        {"label": "Auto-certified", "pct": 42, "count": 520, "color": "bg-green-600"},
    ]

    return {
        "now": datetime.utcnow().isoformat() + "Z",
        "close_clock_days_remaining": 20,
        "totals": {
            "recs": total_recs,
            "tasks": total_tasks,
        },
        "states": {
            "not_prepared": {"pct": 52, "recs": 694, "tasks": 75},
            "in_progress": {"pct": 7, "recs": 96, "tasks": 24},
            "completed": {"pct": 41, "recs": 556, "tasks": 12},
        },
        "reconciliations": {
            "count": total_recs,
            "completion_pct": 44,
            "completed": 544,
            "segments": segments,
            "cards": [
                {"title": "Rejected", "value": "<1%", "count": 5},
                {"title": "Past due", "value": "56%", "count": 691},
                {"title": "Unidentified Difference", "value": "1.93B USD"},
                {"title": "Auto-certified", "value": "42%", "count": 520},
            ],
        },
    }


# ---- Pages ------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    data = mock_close_data()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "data": data}
    )


# ---- HTMX partials ----------------------------------------------------------

@app.get("/partials/kpis", response_class=HTMLResponse)
async def kpis_partial(request: Request):
    data = mock_close_data()
    return templates.TemplateResponse(
        "partials/kpis.html",
        {"request": request, "data": data}
    )


@app.get("/partials/recon-progress", response_class=HTMLResponse)
async def recon_progress_partial(request: Request):
    data = mock_close_data()
    return templates.TemplateResponse(
        "partials/recon_progress.html",
        {"request": request, "data": data}
    )


@app.get("/partials/clock", response_class=HTMLResponse)
async def clock_partial(request: Request):
    data = mock_close_data()
    return templates.TemplateResponse(
        "partials/clock.html",
        {"request": request, "ts": data["now"]}
    )


@app.get("/partials/tab/close-ops", response_class=HTMLResponse)
async def tab_close_ops(request: Request):
    data = mock_close_data()
    return templates.TemplateResponse(
        "partials/close_ops.html",
        {"request": request, "data": data}
    )


@app.get("/partials/tab/my-work", response_class=HTMLResponse)
async def tab_my_work(request: Request):
    data = mock_close_data()
    return templates.TemplateResponse(
        "partials/my_work.html",
        {"request": request, "data": data}
    )


@app.get("/partials/tab/analytics", response_class=HTMLResponse)
async def tab_analytics(request: Request):
    data = mock_close_data()
    return templates.TemplateResponse(
        "partials/analytics.html",
        {"request": request, "data": data}
    )


@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat() + "Z"}


# ---- FX Analysis ------------------------------------------------------------

def _find_latest_fx_file(base_out: str = None) -> Optional[str]:
    # Auto-detect out directory location
    if base_out is None:
        if os.path.exists("out"):
            base_out = "out"
        elif os.path.exists("../out"):
            base_out = "../out"
        else:
            return None
    
    # Find latest fx_translation_run_*.json in out/run_*/
    pattern = os.path.join(base_out, "run_*", "fx_translation_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    # Sort by run timestamp embedded in parent dir name
    candidates.sort(reverse=True)
    return candidates[0]


def _load_fx_data() -> Dict[str, Any]:
    path = _find_latest_fx_file()
    if path and os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Fallback mock structure matching artifact keys
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": "2025-08",
        "entity_scope": "ALL",
        "policy": {"rate_basis": "period_rate (dataset)", "tolerance_usd": 0.01},
        "summary": {"rows": 3, "diff_count": 3, "total_abs_diff_usd": 123456.78},
        "rows": [
            {"period": "2025-08", "entity": "ENT100", "account": "4000", "currency": "EUR", "balance_local": 0.0, "rate": 1.0891, "computed_usd": 0.0, "reported_usd": -200000.0, "diff_usd": 200000.0},
            {"period": "2025-08", "entity": "ENT101", "account": "5000", "currency": "GBP", "balance_local": 0.0, "rate": 1.2815, "computed_usd": 0.0, "reported_usd": 120000.0, "diff_usd": -120000.0},
            {"period": "2025-08", "entity": "ENT102", "account": "6000", "currency": "USD", "balance_local": 0.0, "rate": 1.0, "computed_usd": 0.0, "reported_usd": -3456.78, "diff_usd": 3456.78},
        ],
    }


def _fx_viewmodel(raw: Dict[str, Any], entity: Optional[str], currency: Optional[str]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = raw.get("rows", [])
    if entity:
        rows = [r for r in rows if r.get("entity") == entity]
    if currency:
        rows = [r for r in rows if r.get("currency") == currency]
    # Sort by absolute diff desc, but show ALL rows (not just large differences)
    rows_sorted = sorted(rows, key=lambda r: abs(float(r.get("diff_usd", 0.0))), reverse=True)
    # Build distinct lists
    entities = sorted({r.get("entity") for r in raw.get("rows", [])})
    currencies = sorted({r.get("currency") for r in raw.get("rows", [])})
    total_abs = sum(abs(float(r.get("diff_usd", 0.0))) for r in rows)
    return {
        "period": raw.get("period"),
        "policy": raw.get("policy", {}),
        "summary": raw.get("summary", {}),
        "entities": entities,
        "currencies": currencies,
        "selected_entity": entity or "",
        "selected_currency": currency or "",
        "rows": rows_sorted,  # Show ALL rows, not capped at 200
        "total_abs_diff_filtered": total_abs,
        "count_filtered": len(rows_sorted),
    }


@app.get("/fx", response_class=HTMLResponse)
async def fx_analysis(request: Request, entity: Optional[str] = None, currency: Optional[str] = None):
    raw = _load_fx_data()
    vm = _fx_viewmodel(raw, entity, currency)
    return templates.TemplateResponse(
        "fx.html",
        {"request": request, "fx": vm}
    )


@app.get("/fx-table", response_class=HTMLResponse)
async def fx_table_partial(request: Request, entity: Optional[str] = None, currency: Optional[str] = None):
    raw = _load_fx_data()
    vm = _fx_viewmodel(raw, entity, currency)
    return templates.TemplateResponse(
        "partials/fx_table.html",
        {"request": request, "fx": vm}
    )


# ---- Flux Analysis -----------------------------------------------------------

def _find_latest_flux_file(base_out: str = None) -> Optional[str]:
    # Auto-detect out directory location
    if base_out is None:
        if os.path.exists("out"):
            base_out = "out"
        elif os.path.exists("../out"):
            base_out = "../out"
        else:
            return None
    
    pattern = os.path.join(base_out, "run_*", "flux_analysis_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


def _load_flux_data() -> Dict[str, Any]:
    path = _find_latest_flux_file()
    if path and os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    # Fallback mock following artifact schema
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": "2025-08",
        "prior": "2025-07",
        "entity_scope": "ALL",
        "rules": {"threshold_basis": "default", "default_floor_usd": 1000.0},
        "rows": [
            {"entity": "ENT100", "account": "4000", "actual_usd": -1200000.0, "prior_usd": -900000.0, "budget_amount": -300000.0, "var_vs_budget": -900000.0, "var_vs_prior": -300000.0, "pct_vs_budget": 3.0, "pct_vs_prior": 0.3333, "threshold_usd": 50000.0, "band_vs_budget": "above", "band_vs_prior": "above"},
            {"entity": "ENT101", "account": "5000", "actual_usd": 800000.0, "prior_usd": 600000.0, "budget_amount": 0.0, "var_vs_budget": 800000.0, "var_vs_prior": 200000.0, "pct_vs_budget": None, "pct_vs_prior": 0.3333, "threshold_usd": 42000.0, "band_vs_budget": "above", "band_vs_prior": "above"},
        ],
    }


def _find_latest_flux_ai_narratives_file(base_out: str = None) -> Optional[str]:
    # Auto-detect out directory location
    if base_out is None:
        if os.path.exists("out"):
            base_out = "out"
        elif os.path.exists("../out"):
            base_out = "../out"
        else:
            return None
    
    pattern = os.path.join(base_out, "run_*", "ai_cache", "flux_ai_narratives_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


def _load_flux_ai_narratives_map() -> Dict[str, Dict[str, Any]]:
    """Return a map keyed by "ENTITY|ACCOUNT" -> narrative dict from latest run.
    Expected schema: {"narratives": [{entity, account, narrative, business_driver, ...}, ...]}
    """
    path = _find_latest_flux_ai_narratives_file()
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            payload = json.load(f)
        items = payload.get("narratives") if isinstance(payload, dict) else None
        if not isinstance(items, list):
            return {}
        out: Dict[str, Dict[str, Any]] = {}
        for it in items:
            key = f"{it.get('entity')}|{it.get('account')}"
            out[key] = it
        return out
    except Exception:
        return {}


def _flux_viewmodel(raw: Dict[str, Any], entity: Optional[str], min_abs: Optional[float]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = raw.get("rows", [])
    entities = sorted({r.get("entity") for r in rows})
    # Filter
    if entity:
        rows = [r for r in rows if r.get("entity") == entity]
    if min_abs is not None:
        rows = [r for r in rows if abs(float(r.get("var_vs_budget", 0.0))) >= float(min_abs)]
    # Sort by abs var_vs_budget desc (fallback to abs var_vs_prior)
    def _key(r):
        v = r.get("var_vs_budget")
        if v is None:
            v = r.get("var_vs_prior", 0.0)
        try:
            return abs(float(v))
        except Exception:
            return 0.0
    rows_sorted = sorted(rows, key=_key, reverse=True)
    total_abs = sum(abs(float((r.get("var_vs_budget") if r.get("var_vs_budget") is not None else r.get("var_vs_prior", 0.0)))) for r in rows)
    return {
        "period": raw.get("period"),
        "prior": raw.get("prior"),
        "rules": raw.get("rules", {}),
        "entities": entities,
        "selected_entity": entity or "",
        "min_abs": min_abs if min_abs is not None else "",
        "rows": rows_sorted,  # Show ALL rows, not capped at 200
        "count_filtered": len(rows_sorted),
        "total_abs_filtered": total_abs,
    }


@app.get("/flux", response_class=HTMLResponse)
async def flux_analysis(request: Request, entity: Optional[str] = None, min_abs: Optional[int] = None):
    raw = _load_flux_data()
    vm = _flux_viewmodel(raw, entity, min_abs)
    return templates.TemplateResponse(
        "flux.html",
        {"request": request, "flux": vm}
    )


@app.get("/flux-table", response_class=HTMLResponse)
async def flux_table_partial(request: Request, entity: Optional[str] = None, min_abs: Optional[int] = None):
    raw = _load_flux_data()
    vm = _flux_viewmodel(raw, entity, min_abs)
    return templates.TemplateResponse(
        "partials/flux_table.html",
        {"request": request, "flux": vm}
    )


# ---- Exceptions Workbench ----------------------------------------------------

def _exceptions_from_fx(raw_fx: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for r in raw_fx.get("rows", []):
        try:
            amt = float(r.get("diff_usd", 0.0))
        except Exception:
            amt = 0.0
        rows.append({
            "module": "FX",
            "period": r.get("period"),
            "entity": r.get("entity"),
            "account": r.get("account"),
            "amount_usd": amt,
            "variance_basis": "fx_diff",
            "threshold_usd": (raw_fx.get("policy", {}) or {}).get("tolerance_usd", 0.0),
            "band": "above" if abs(amt) >= float((raw_fx.get("policy", {}) or {}).get("tolerance_usd", 0.0)) else "within",
            "status": "New",
            "assignee": "-",
            "evidence_count": 0,
        })
    return rows


def _exceptions_from_flux(raw_flux: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = []
    for r in raw_flux.get("rows", []):
        v = r.get("var_vs_budget")
        if v is None:
            v = r.get("var_vs_prior", 0.0)
        try:
            amt = float(v)
        except Exception:
            amt = 0.0
        thr = float(r.get("threshold_usd", 0.0))
        rows.append({
            "module": "Flux",
            "period": raw_flux.get("period"),
            "entity": r.get("entity"),
            "account": r.get("account"),
            "amount_usd": amt,
            "variance_basis": "vs_budget" if r.get("var_vs_budget") is not None else "vs_prior",
            "threshold_usd": thr,
            "band": "above" if abs(amt) >= thr else "within",
            "status": "New",
            "assignee": "-",
            "evidence_count": 0,
        })
    return rows


def _exceptions_viewmodel(entity: Optional[str], module: Optional[str], account: Optional[str], status: Optional[str], min_abs: Optional[int]) -> Dict[str, Any]:
    raw_fx = _load_fx_data()
    raw_flux = _load_flux_data()
    rows = _exceptions_from_fx(raw_fx) + _exceptions_from_flux(raw_flux)
    # Filters
    if entity:
        rows = [r for r in rows if r.get("entity") == entity]
    if module:
        rows = [r for r in rows if r.get("module") == module]
    if account:
        rows = [r for r in rows if r.get("account") == account]
    if status:
        rows = [r for r in rows if r.get("status") == status]
    if min_abs is not None:
        rows = [r for r in rows if abs(float(r.get("amount_usd", 0.0))) >= float(min_abs)]
    # Sort by abs amount desc
    rows_sorted = sorted(rows, key=lambda r: abs(float(r.get("amount_usd", 0.0))), reverse=True)
    entities = sorted({r.get("entity") for r in rows_sorted})
    modules = ["FX", "Flux"]
    accounts = sorted({r.get("account") for r in rows_sorted})
    statuses = ["New", "In review", "Ready", "Signed"]
    total_abs = sum(abs(float(r.get("amount_usd", 0.0))) for r in rows_sorted)
    above_cnt = sum(1 for r in rows_sorted if r.get("band") == "above")
    return {
        "period": raw_flux.get("period") or raw_fx.get("period"),
        "entities": entities,
        "modules": modules,
        "accounts": accounts,
        "statuses": statuses,
        "selected_entity": entity or "",
        "selected_module": module or "",
        "selected_account": account or "",
        "selected_status": status or "",
        "min_abs": min_abs if min_abs is not None else "",
        "rows": rows_sorted[:300],
        "count_filtered": len(rows_sorted),
        "total_abs_filtered": total_abs,
        "above_threshold_count": above_cnt,
    }


@app.get("/exceptions", response_class=HTMLResponse)
async def exceptions_workbench(request: Request, entity: Optional[str] = None, module: Optional[str] = None, account: Optional[str] = None, status: Optional[str] = None, min_abs: Optional[int] = None):
    vm = _exceptions_viewmodel(entity, module, account, status, min_abs)
    return templates.TemplateResponse(
        "exceptions.html",
        {"request": request, "ex": vm}
    )


@app.get("/exceptions-table", response_class=HTMLResponse)
async def exceptions_table_partial(request: Request, entity: Optional[str] = None, module: Optional[str] = None, account: Optional[str] = None, status: Optional[str] = None, min_abs: Optional[int] = None):
    vm = _exceptions_viewmodel(entity, module, account, status, min_abs)
    return templates.TemplateResponse(
        "partials/exceptions_table.html",
        {"request": request, "ex": vm}
    )


# ---- Generic Details Drawer --------------------------------------------------

def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default


def _latest_run_id_from_path(path: Optional[str]) -> str:
    if not path:
        return ""
    # Expect .../out/run_YYYY.../filename.json
    parts = os.path.normpath(path).split(os.sep)
    for p in parts:
        if p.startswith("run_"):
            return p
    return ""


def _latest_run_dir() -> Optional[str]:
    # Auto-detect out directory location
    if os.path.exists("out"):
        out_dir = "out"
    elif os.path.exists("../out"):
        out_dir = "../out"
    else:
        return None
        
    if not os.path.isdir(out_dir):
        return None
    candidates = [d for d in os.listdir(out_dir) if d.startswith("run_")]
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return os.path.join(out_dir, candidates[0])


def _load_run_email_evidence_items() -> List[Dict[str, Any]]:
    """Load items from the latest run's email evidence file if available."""
    run_dir = _latest_run_dir()
    if not run_dir:
        return []
    # find email_evidence_run_*.json
    try:
        files = [f for f in os.listdir(run_dir) if f.startswith("email_evidence_run_") and f.endswith('.json')]
        if not files:
            return []
        files.sort(reverse=True)
        path = os.path.join(run_dir, files[0])
        with open(path, "r") as f:
            payload = json.load(f)
        if isinstance(payload, dict):
            return payload.get("items", [])
        if isinstance(payload, list):
            return payload
    except Exception:
        return []
    return []


def _gather_email_evidence(entity: Optional[str], account: Optional[str], period: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return up to 20 evidence emails relevant to the entity/account.

    Adapts to the actual schema of data/supporting/emails.json where items live
    under the 'items' key and timestamps are under 'timestamp'.

    Matching strategy:
    - Primary: entity token (e.g., ENT101) found in subject/body OR account code appears.
    - Secondary: if nothing matches, choose recent emails within the same period (YYYY-MM) as contextual evidence.
    """
    # Prefer latest run evidence; fallback to supporting file
    items = _load_run_email_evidence_items()
    if not items:
        path = os.path.join("data", "supporting", "emails.json")
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r") as f:
                payload = json.load(f)
            if isinstance(payload, dict):
                items = payload.get("items", [])
            elif isinstance(payload, list):
                items = payload
        except Exception:
            return []

    matches: List[Dict[str, Any]] = []
    ent_tok = (entity or "").lower().strip()
    acc_tok = str(account) if account is not None else None

    # Pass 1: require BOTH entity and account if both provided
    strict_matches: List[Dict[str, Any]] = []
    for e in items:
        subj = (e.get("subject") or "").lower()
        body = (e.get("body") or "").lower()
        has_entity = bool(ent_tok and ent_tok in (subj + body))
        has_account = bool(acc_tok and acc_tok in (subj + body))
        if ent_tok and acc_tok and has_entity and has_account:
            strict_matches.append({
                "type": "email",
                "source": e.get("from"),
                "ts": e.get("timestamp"),
                "confidence": e.get("confidence", 0.8),
                "snippet": (body[:160] + "…") if body else subj,
                "href": e.get("email_id") and f"#email-{e.get('email_id')}" or None,
            })

    if strict_matches:
        return strict_matches[:20]

    # Pass 2: relaxed OR matching if strict found nothing
    for e in items:
        subj = (e.get("subject") or "").lower()
        body = (e.get("body") or "").lower()
        has_entity = bool(ent_tok and ent_tok in (subj + body))
        has_account = bool(acc_tok and acc_tok in (subj + body))
        if has_entity or has_account:
            matches.append({
                "type": "email",
                "source": e.get("from"),
                "ts": e.get("timestamp"),
                "confidence": e.get("confidence", 0.75),
                "snippet": (body[:160] + "…") if body else subj,
                "href": e.get("email_id") and f"#email-{e.get('email_id')}" or None,
            })

    # If no direct matches, use period-aware fallback: pick the 3 most recent in the period
    if not matches and period:
        ym = period[:7]  # YYYY-MM
        def _ts(e):
            return e.get("timestamp") or ""
        period_items = [e for e in items if (e.get("timestamp") or "").startswith(ym)]
        # sort desc by timestamp
        period_items.sort(key=lambda x: x.get("timestamp") or "", reverse=True)
        for e in period_items[:3]:
            body = (e.get("body") or "")
            subj = (e.get("subject") or "")
            matches.append({
                "type": "email",
                "source": e.get("from"),
                "ts": e.get("timestamp"),
                "confidence": 0.5,  # contextual
                "snippet": (body[:160] + "…") if body else subj,
                "href": e.get("email_id") and f"#email-{e.get('email_id')}" or None,
            })

    return matches[:20]


def _select_fx_row(period: Optional[str], entity: Optional[str], account: Optional[str]) -> Dict[str, Any]:
    raw = _load_fx_data()
    row = next((r for r in raw.get("rows", []) if (not period or r.get("period") == period) and r.get("entity") == entity and str(r.get("account")) == str(account)), None)
    return {
        "module": "FX",
        "artifact_path": _find_latest_fx_file(),
        "run_id": _latest_run_id_from_path(_find_latest_fx_file()),
        "header": {"period": period or raw.get("period"), "entity": entity, "account": account, "basis": "fx_diff"},
        "metrics": row or {},
        "threshold": (raw.get("policy", {}) or {}).get("tolerance_usd", 0.0),
        "evidence": _gather_email_evidence(entity, account, period or raw.get("period")),
        "provenance": {"model": "LangGraph Close Agents", "prompt": None, "run_id": _latest_run_id_from_path(_find_latest_fx_file())},
    }


def _select_flux_row(period: Optional[str], entity: Optional[str], account: Optional[str], basis: Optional[str]) -> Dict[str, Any]:
    raw = _load_flux_data()
    # Choose row by entity/account; period is top-level in artifact
    rows = [r for r in raw.get("rows", []) if r.get("entity") == entity and str(r.get("account")) == str(account)]
    row = rows[0] if rows else None
    # Decide basis
    selected_basis = basis
    if not selected_basis and row:
        vb = row.get("var_vs_budget")
        vp = row.get("var_vs_prior")
        selected_basis = "budget" if abs(_safe_float(vb)) >= abs(_safe_float(vp)) else "prior"
    # Attach AI narrative if available
    narr_map = _load_flux_ai_narratives_map()
    ai_narr = narr_map.get(f"{entity}|{account}") if entity and account else None
    return {
        "module": "Flux",
        "artifact_path": _find_latest_flux_file(),
        "run_id": _latest_run_id_from_path(_find_latest_flux_file()),
        "header": {"period": period or raw.get("period"), "entity": entity, "account": account, "basis": selected_basis},
        "metrics": row or {},
        "threshold": (row or {}).get("threshold_usd", 0.0),
        "evidence": _gather_email_evidence(entity, account, period or raw.get("period")),
        "ai_narrative": ai_narr or {},
        "provenance": {"model": "LangGraph Close Agents", "prompt": None, "run_id": _latest_run_id_from_path(_find_latest_flux_file())},
    }


@app.get("/details", response_class=HTMLResponse)
async def details_drawer(
    request: Request,
    module: str,
    period: Optional[str] = None,
    entity: Optional[str] = None,
    account: Optional[str] = None,
    basis: Optional[str] = None,
    content_only: Optional[str] = None,
):
    module = (module or "").strip()
    if module == "FX":
        payload = _select_fx_row(period, entity, account)
    elif module == "Flux":
        payload = _select_flux_row(period, entity, account, basis)
    else:
        payload = {"module": module, "header": {"period": period, "entity": entity, "account": account, "basis": basis}, "metrics": {}, "evidence": [], "provenance": {}}
    
    # If content_only is requested, return just the drawer content with header update
    if content_only:
        # Return content with out-of-band header update
        header_html = templates.TemplateResponse(
            "partials/drawer_header.html",
            {"request": request, "d": payload}
        ).body.decode('utf-8')
        
        content_html = templates.TemplateResponse(
            "partials/drawer_content.html",
            {"request": request, "d": payload}
        ).body.decode('utf-8')
        
        # Return content with out-of-band header update
        response_html = f'<div hx-swap-oob="innerHTML:#drawer-header">{header_html}</div>{content_html}'
        return HTMLResponse(content=response_html)
    else:
        # Return full drawer
        return templates.TemplateResponse(
            "partials/details_drawer.html",
            {"request": request, "d": payload}
        )


@app.get("/partials/close-drawer", response_class=HTMLResponse)
async def close_drawer():
    return HTMLResponse(content="")


# ---- Journal Entry Endpoints -----------------------------------------------

@app.post("/je/propose", response_class=HTMLResponse)
async def propose_je(request: Request, module: str = Form(), scenario: str = Form(), 
                    source_data: str = Form(), period: str = Form(), entity: str = Form()):
    """Create a new journal entry proposal."""
    try:
        source_dict = json.loads(source_data)
    except:
        source_dict = {"raw": source_data}
    
    # Create JE based on module
    if module == "FX":
        diff_usd = float(source_dict.get("diff_usd", 0.0))
        account = source_dict.get("account", "1000")
        je = _create_fx_je(entity, account, period, diff_usd, source_dict)
    elif module == "Flux":
        variance = float(source_dict.get("var_vs_budget", source_dict.get("var_vs_prior", 0.0)))
        account = source_dict.get("account", "4000")
        basis = source_dict.get("basis", "budget")
        je = _create_flux_je(entity, account, period, variance, basis, source_dict)
    else:
        # Generic JE for other modules
        je = JournalEntry(
            id=str(uuid.uuid4())[:8],
            module=module,
            scenario=scenario,
            entity=entity,
            period=period,
            description=f"{module} adjustment for {entity}",
            source_data=source_dict
        )
    
    # Store the JE
    _je_store[je.id] = je
    
    # Return modal
    return templates.TemplateResponse(
        "partials/je_proposal_modal.html",
        {"request": request, "je": je, "workflow_status": None, "can_approve": True}
    )

@app.post("/je/submit/{je_id}", response_class=HTMLResponse)
async def submit_je(request: Request, je_id: str):
    """Submit JE for approval."""
    if je_id not in _je_store:
        return HTMLResponse(content="<div>JE not found</div>", status_code=404)
    
    je = _je_store[je_id]
    je.status = JEStatus.PENDING
    
    return templates.TemplateResponse(
        "partials/je_proposal_modal.html",
        {"request": request, "je": je, "workflow_status": None, "can_approve": True}
    )

@app.post("/je/approve/{je_id}", response_class=HTMLResponse)
async def approve_je(request: Request, je_id: str, action: str = Form()):
    """Approve or reject JE."""
    if je_id not in _je_store:
        return HTMLResponse(content="<div>JE not found</div>", status_code=404)
    
    je = _je_store[je_id]
    
    if action == "approve":
        je.status = JEStatus.APPROVED
    elif action == "reject":
        je.status = JEStatus.REJECTED
    
    return templates.TemplateResponse(
        "partials/je_proposal_modal.html",
        {"request": request, "je": je, "workflow_status": None, "can_approve": True}
    )

@app.post("/je/post/{je_id}", response_class=HTMLResponse)
async def post_je(request: Request, je_id: str):
    """Post JE to GL system."""
    if je_id not in _je_store:
        return HTMLResponse(content="<div>JE not found</div>", status_code=404)
    
    je = _je_store[je_id]
    je.status = JEStatus.POSTED
    
    return templates.TemplateResponse(
        "partials/je_proposal_modal.html",
        {"request": request, "je": je, "workflow_status": None, "can_approve": True}
    )
