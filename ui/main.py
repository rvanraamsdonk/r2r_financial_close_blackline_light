from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum
from pydantic import BaseModel, Field
import json
import os
import glob
import uuid
from pathlib import Path
import traceback
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="R2R Close – Dashboard UI (HTMX)")

# Mount static for future assets (css/js/images) if needed
import os
if os.path.exists("ui/static"):
    app.mount("/static", StaticFiles(directory="ui/static"), name="static")
elif os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

def format_datetime_filter(value, format='%Y-%m-%d %H:%M:%S UTC'):
    """Format an ISO 8601 string to a more readable date and time."""
    if not value:
        return ""
    try:
        # Handle Z suffix for UTC
        if value.endswith('Z'):
            value = value[:-1] + '+00:00'
        dt_object = datetime.fromisoformat(value)
        return dt_object.strftime(format)
    except (ValueError, TypeError):
        return value

if os.path.exists("ui/templates"):
    templates = Jinja2Templates(directory="ui/templates")
else:
    templates = Jinja2Templates(directory="templates")

def format_currency_filter(value, currency='$'):
    """Formats a number into a currency string like $1,234."""
    if value is None:
        return ""
    try:
        return f"{currency}{value:,.0f}"
    except (ValueError, TypeError):
        return str(value)

templates.env.filters['format_datetime'] = format_datetime_filter
templates.env.filters['format_currency'] = format_currency_filter


# ---- HITL Data Models ------------------------------------------------------

class HITLCaseStatus(str, Enum):
    OPEN = "open"
    ASSIGNED = "assigned"
    RESOLVED = "resolved"

class HITLCase(BaseModel):
    case_id: str = Field(default_factory=lambda: f"case_{uuid.uuid4().hex[:8]}")
    module: str
    reason: str
    priority: str
    status: HITLCaseStatus = HITLCaseStatus.OPEN
    assignee: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    ai_summary: str
    raw_data: Dict[str, Any]

# In-memory HITL case storage (in production, this would be a database)
_hitl_store: Dict[str, HITLCase] = {}

# ---- Journal Entry Data Models ---------------------------------------------

class JEStatus(Enum):
    DRAFT = "draft"
    PENDING = "pending"
    APPROVED = "approved"
    POSTED = "posted"
    REJECTED = "rejected"

class JELine(BaseModel):
    account: str
    description: str
    debit: float = 0.0
    credit: float = 0.0

class JournalEntry(BaseModel):
    id: str
    module: str
    scenario: str
    entity: str
    period: str
    description: str
    lines: List[JELine] = Field(default_factory=list)
    status: JEStatus = JEStatus.DRAFT
    source_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    
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

def _create_flux_je(source_data: Dict[str, Any], period: str, entity: str) -> JournalEntry:
    """Create journal entry for flux analysis variance."""
    account = source_data.get("account", "Unknown")
    var_amount = float(source_data.get("var_vs_budget", 0.0))
    if var_amount == 0.0:
        var_amount = float(source_data.get("var_vs_prior", 0.0))
    
    lines = []
    if var_amount != 0.0:
        if var_amount > 0:  # Unfavorable variance - debit expense/asset
            lines.append(JELine(f"{account}-Variance", f"Flux variance adjustment for {account}", var_amount, 0.0))
            lines.append(JELine("2100-Accrued Liabilities", "Variance accrual", 0.0, var_amount))
        else:  # Favorable variance - credit revenue/reduce expense
            lines.append(JELine("2100-Accrued Liabilities", "Variance accrual reversal", abs(var_amount), 0.0))
            lines.append(JELine(f"{account}-Variance", f"Flux variance adjustment for {account}", 0.0, abs(var_amount)))
    
    return JournalEntry(
        id=str(uuid.uuid4()),
        module="Flux",
        scenario="variance_analysis",
        entity=entity,
        period=period,
        description=f"Flux variance adjustment for {entity}/{account}",
        lines=lines,
        status=JEStatus.DRAFT,
        source_data=source_data,
        created_at=datetime.now()
    )


def _create_bank_je(source_data: Dict[str, Any], period: str, entity: str) -> JournalEntry:
    """Create journal entry for bank reconciliation adjustment."""
    txn_id = source_data.get("bank_txn_id", "Unknown")
    amount = float(source_data.get("amount", 0.0))
    counterparty = source_data.get("counterparty", "Unknown")
    reason = source_data.get("reason", "adjustment")
    
    lines = []
    if amount != 0.0:
        if reason == "unusual_counterparty" or source_data.get("classification") == "forensic_risk":
            # Forensic adjustment - typically reverse suspicious transaction
            if amount > 0:  # Reverse credit (debit cash, credit suspense)
                lines.append(JELine("1010-Cash", f"Reverse suspicious transaction {txn_id}", 0.0, amount))
                lines.append(JELine("1200-Suspense Account", f"Hold for investigation - {counterparty}", amount, 0.0))
            else:  # Reverse debit (credit cash, debit suspense)
                lines.append(JELine("1010-Cash", f"Reverse suspicious transaction {txn_id}", abs(amount), 0.0))
                lines.append(JELine("1200-Suspense Account", f"Hold for investigation - {counterparty}", 0.0, abs(amount)))
        elif reason == "timing_difference":
            # Timing adjustment - typically accrual
            if amount > 0:  # Outstanding deposit
                lines.append(JELine("1020-Cash in Transit", f"Outstanding deposit {txn_id}", amount, 0.0))
                lines.append(JELine("1010-Cash", "Bank reconciliation adjustment", 0.0, amount))
            else:  # Outstanding check
                lines.append(JELine("1010-Cash", "Bank reconciliation adjustment", abs(amount), 0.0))
                lines.append(JELine("2010-Outstanding Checks", f"Outstanding check {txn_id}", 0.0, abs(amount)))
        else:
            # General bank adjustment
            if amount > 0:
                lines.append(JELine("1010-Cash", f"Bank adjustment {txn_id}", amount, 0.0))
                lines.append(JELine("6100-Bank Charges", "Bank reconciliation adjustment", 0.0, amount))
            else:
                lines.append(JELine("6100-Bank Charges", "Bank reconciliation adjustment", abs(amount), 0.0))
                lines.append(JELine("1010-Cash", f"Bank adjustment {txn_id}", 0.0, abs(amount)))
    
    return JournalEntry(
        id=str(uuid.uuid4()),
        module="Bank",
        scenario="bank_reconciliation",
        entity=entity,
        period=period,
        description=f"Bank reconciliation adjustment for {entity}/{txn_id}",
        lines=lines,
        status=JEStatus.DRAFT,
        source_data=source_data,
        created_at=datetime.now()
    )


# ---- Mock data generator ----------------------------------------------------

def _latest_run_id_from_path(path: str) -> Optional[str]:
    """Extracts the run ID (e.g., '20250903T101632Z') from a file path."""
    try:
        # Path(...).parts gives ('out', 'run_20250903T101632Z', 'gatekeeping_run_....json')
        run_dir_part = [part for part in Path(path).parts if part.startswith("run_")]
        if run_dir_part:
            return run_dir_part[0].replace("run_", "")
    except Exception:
        pass
    return None

def _load_automation_dashboard() -> Dict[str, Any]:
    """Load real automation metrics from latest gatekeeping run"""
    try:
        # Find latest gatekeeping file
        base_out = "out" if os.path.exists("out") else "../out" if os.path.exists("../out") else None
        if not base_out:
            return _fallback_automation_data()
        
        pattern = os.path.join(base_out, "run_*", "gatekeeping_run_*.json")
        candidates = glob.glob(pattern)
        if not candidates:
            return _fallback_automation_data()
        
        # Load latest gatekeeping data
        latest_file = sorted(candidates, reverse=True)[0]
        with open(latest_file, "r") as f:
            gatekeeping = json.load(f)
        
        # Calculate automation metrics
        categories = gatekeeping.get("categories", {})
        total_exceptions = sum(categories.values())
        
        # Estimate total items processed (from FX data as proxy)
        fx_data = _load_fx_data()
        total_items = len(fx_data.get("rows", [])) * 4  # Rough estimate across modules
        auto_closed = max(0, total_items - total_exceptions)
        
        auto_close_rate = (auto_closed / total_items * 100) if total_items > 0 else 0
        
        # Enhanced AI-first metrics
        risk_level = gatekeeping.get("risk_level", "unknown")
        block_close = gatekeeping.get("block_close", False)
        auto_close_eligible = gatekeeping.get("auto_close_eligible", False)
        ai_rationale = gatekeeping.get("ai_rationale", "No AI rationale available")
        confidence_score = float(gatekeeping.get("confidence_score", 0.0))
        materiality_threshold = gatekeeping.get("materiality_threshold", 50000)

        # Load auto journals summary from same run directory, if present
        auto_journals_count = 0
        auto_journals_amount = 0.0
        auto_journals_confidence = 0.0
        total_exception_amount = float(gatekeeping.get("total_exception_amount", 0.0))
        try:
            latest_run_dir = Path(latest_file).parent
            run_id = _latest_run_id_from_path(str(latest_file))
            aj_path = latest_run_dir / f"auto_journals_{run_id}.json"
            if aj_path.exists():
                with open(aj_path, "r") as f:
                    auto_journals_data = json.load(f)
                aj_summary = auto_journals_data.get("summary", {})
                auto_journals_count = int(aj_summary.get("total_count", 0))
                auto_journals_amount = float(aj_summary.get("total_amount_usd", 0.0))
                auto_journals_confidence = float(aj_summary.get("average_confidence", 0.0))
        except Exception:
            pass
        
        # Exception breakdown by severity
        critical_exceptions = []
        medium_exceptions = []
        
        for category, count in categories.items():
            if count > 0:
                severity = "critical" if count > 10 or category in ["bank_duplicates"] else "medium"
                exception_item = {
                    "category": category.replace("_", " ").title(),
                    "count": count,
                    "severity": severity
                }
                if severity == "critical":
                    critical_exceptions.append(exception_item)
                else:
                    medium_exceptions.append(exception_item)
        
        ai_confidence = [
            {"range": "90-100%", "count": int(auto_closed * 0.7) if confidence_score >= 0.9 else int(auto_closed * 0.4), "color": "bg-green-500"},
            {"range": "80-89%", "count": int(auto_closed * 0.25), "color": "bg-blue-500"},
            {"range": "70-79%", "count": auto_closed - int(auto_closed * 0.7) - int(auto_closed * 0.25), "color": "bg-yellow-500"},
            {"range": "<70%", "count": total_exceptions, "color": "bg-red-500"},
        ]
        
        exception_queue = []
        
        return {
            "generated_at": gatekeeping.get("generated_at"),
            "period": gatekeeping.get("period"),
            "automation_status": {
                "auto_closed_count": auto_closed,
                "total_items": total_items,
                "auto_close_rate": round(auto_close_rate, 1),
                "status": "success" if auto_close_eligible else "blocked",
                "risk_level": risk_level,
                "confidence_score": round(confidence_score * 100, 1) if confidence_score <= 1 else round(confidence_score, 1),
                "ai_rationale": ai_rationale,
                "total_exception_amount": total_exception_amount,
                "materiality_threshold": materiality_threshold,
                "auto_journals_count": auto_journals_count,
                "auto_journals_amount": auto_journals_amount,
                "auto_journals_confidence": round(auto_journals_confidence * 100, 1) if auto_journals_confidence > 0 else 0
            },
            "exceptions": {
                "critical": critical_exceptions,
                "medium": medium_exceptions,
                "total_count": total_exceptions
            },
            "ai_confidence": ai_confidence,
            "exception_queue": exception_queue
        }
    except Exception as e:
        print(f"Error loading automation dashboard: {e}")
        return _fallback_automation_data()


def _find_latest_hitl_file(base_out: str = None) -> Optional[str]:
    if base_out is None:
        base_out = "out" if os.path.exists("out") else "../out" if os.path.exists("../out") else None
        if not base_out:
            return None
    
    pattern = os.path.join(base_out, "run_*", "hitl_cases_run_*.jsonl")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


def _load_initial_hitl_cases():
    """Load initial HITL cases from the latest artifact file into the in-memory store."""
    global _hitl_store
    path = _find_latest_hitl_file()
    
    # Try to load from audit file first
    if path and os.path.exists(path):
        try:
            temp_cases = {}
            with open(path, "r") as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("type") == "hitl_case":
                        case = HITLCase(**data)
                        temp_cases[case.case_id] = case
            if temp_cases:
                _hitl_store = temp_cases
                print(f"Successfully loaded {len(_hitl_store)} HITL cases from audit file.")
                return
        except Exception as e:
            print(f"Error loading HITL cases from audit file: {e}")
    
    # Generate sample HITL cases from forensic scenarios if no real cases found
    print("No HITL cases found in audit file. Generating sample cases from forensic scenarios.")
    _generate_sample_hitl_cases()

def _generate_sample_hitl_cases():
    """Generate sample HITL cases from forensic scenarios in the data."""
    global _hitl_store
    sample_cases = []
    
    # Bank reconciliation forensic cases
    try:
        bank_data = _load_bank_reconciliation_data()
        for exception in bank_data.get("exceptions", [])[:3]:  # Take first 3
            if exception.get("classification") == "forensic_risk":
                case = HITLCase(
                    module="Bank Reconciliation",
                    reason=f"Forensic Risk: {exception.get('reason', '').replace('_', ' ').title()}",
                    priority="high",
                    ai_summary=exception.get("ai_rationale", "Forensic risk detected in bank reconciliation"),
                    raw_data=exception
                )
                sample_cases.append(case)
    except Exception:
        pass
    
    # Flux analysis forensic cases
    try:
        flux_data = _load_flux_data()
        for row in flux_data.get("rows", [])[:2]:  # Take first 2
            if row.get("ai_narrative") and "[FORENSIC]" in row.get("ai_narrative", ""):
                case = HITLCase(
                    module="Flux Analysis",
                    reason=f"Material Variance: {row.get('entity')}/{row.get('account')}",
                    priority="medium",
                    ai_summary=row.get("ai_narrative", "Material variance requiring explanation"),
                    raw_data=row
                )
                sample_cases.append(case)
    except Exception:
        pass
    
    # Convert to dict and store
    _hitl_store = {case.case_id: case for case in sample_cases}
    print(f"Generated {len(_hitl_store)} sample HITL cases.")


@app.on_event("startup")
async def startup_event():
    # In a real app, you might connect to a database, etc.
    print("Application startup")
    _load_initial_hitl_cases()


def _fallback_automation_data() -> Dict[str, Any]:
    """Fallback automation data when real data unavailable"""
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": "2025-08",
        "automation_status": {
            "auto_closed_count": 1184,
            "total_items": 1247,
            "auto_close_rate": 95.0,
            "status": "success",
            "risk_level": "low",
            "confidence_score": 95.0,
            "ai_rationale": "AI rationale",
            "total_exception_amount": 0,
            "materiality_threshold": 50000
        },
        "exceptions": {
            "critical": [
                {"category": "Bank Duplicates", "count": 3, "severity": "critical"},
                {"category": "Forensic Risk", "count": 2, "severity": "critical"}
            ],
            "medium": [
                {"category": "AP Exceptions", "count": 8, "severity": "medium"},
                {"category": "FX Variances", "count": 12, "severity": "medium"}
            ],
            "total_count": 4
        },
        "ai_confidence": [
            {"range": "90-100%", "count": 1156, "color": "bg-green-500"},
            {"range": "80-89%", "count": 28, "color": "bg-blue-500"},
            {"range": "70-79%", "count": 0, "color": "bg-yellow-500"},
            {"range": "<70%", "count": 63, "color": "bg-red-500"},
        ],
        "exception_queue": []
    }


# ---- Pages ------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    logger.info("Request received for index page")
    try: 
    # Load automation dashboard data from latest run
        automation_data = _load_automation_dashboard()
        logger.info(f"Automation data loaded. Keys: {automation_data.keys()}")
    except Exception as e:
        logger.error(f"Error loading automation data: {e}", exc_info=True)
        automation_data = _fallback_automation_data()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "automation_data": automation_data
    })


# ---- API Endpoints for HITL -------------------------------------------------

class AssignRequest(BaseModel):
    assignee: str

@app.get("/api/hitl/cases", response_model=List[HITLCase])
async def get_hitl_cases(
    status: Optional[HITLCaseStatus] = None,
    priority: Optional[str] = None,
    module: Optional[str] = None,
    sort_by: str = 'priority',
    sort_order: str = 'asc',
):
    """
    API endpoint to get HITL cases with filtering and sorting.
    """
    cases = list(_hitl_store.values())

    # Filtering
    if status:
        cases = [case for case in cases if case.status == status]
    if priority:
        cases = [case for case in cases if case.priority.lower() == priority.lower()]
    if module:
        cases = [case for case in cases if case.module.lower() == module.lower()]

    # Sorting
    reverse = sort_order == 'desc'
    priority_map = {"high": 0, "medium": 1, "low": 2}
    
    if sort_by == 'priority':
        cases.sort(key=lambda c: (priority_map.get(c.priority, 3), c.created_at), reverse=reverse)
    elif sort_by == 'created_at':
        cases.sort(key=lambda c: c.created_at, reverse=reverse)
    
    return cases

@app.post("/api/hitl/cases/{case_id}/assign", response_model=HITLCase)
async def assign_hitl_case(case_id: str, payload: AssignRequest):
    if case_id not in _hitl_store:
        raise HTTPException(status_code=404, detail="Case not found")
    
    case = _hitl_store[case_id]
    case.assignee = payload.assignee
    case.status = HITLCaseStatus.ASSIGNED
    case.updated_at = datetime.utcnow().isoformat()
    _hitl_store[case_id] = case
    return case

@app.post("/api/hitl/cases/{case_id}/resolve", response_model=HITLCase)
async def resolve_hitl_case(case_id: str):
    if case_id not in _hitl_store:
        raise HTTPException(status_code=404, detail="Case not found")

    case = _hitl_store[case_id]
    case.status = HITLCaseStatus.RESOLVED
    case.updated_at = datetime.utcnow().isoformat()
    _hitl_store[case_id] = case
    return case


def _find_latest_ar_reconciliation_file(base_out: str = None) -> Optional[str]:
    if base_out is None:
        base_out = "out" if os.path.exists("out") else "../out" if os.path.exists("../out") else None
        if not base_out:
            return None
    
    pattern = os.path.join(base_out, "run_*", "ar_reconciliation_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]

def _load_ar_reconciliation_data() -> Dict[str, Any]:
    path = _find_latest_ar_reconciliation_file()
    if path and os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": "N/A",
        "exceptions": [],
        "summary": {"count": 0, "total_abs_amount": 0, "by_entity_abs_amount": {}},
    }

@app.get("/ar", response_class=HTMLResponse)
async def ar_page(request: Request):
    logger.info("Request received for AR page")
    ar_data = _load_ar_reconciliation_data()
    logger.info(f"AR data loaded. Found {len(ar_data.get('exceptions', []))} exceptions.")
    return templates.TemplateResponse("ar.html", {"request": request, "data": ar_data})


def _find_latest_ap_reconciliation_file(base_out: str = None) -> Optional[str]:
    if base_out is None:
        base_out = "out" if os.path.exists("out") else "../out" if os.path.exists("../out") else None
        if not base_out:
            return None
    
    pattern = os.path.join(base_out, "run_*", "ap_reconciliation_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]

def _load_ap_reconciliation_data() -> Dict[str, Any]:
    path = _find_latest_ap_reconciliation_file()
    if path and os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": "N/A",
        "exceptions": [],
        "summary": {"count": 0, "total_abs_amount": 0, "by_entity_abs_amount": {}},
    }

@app.get("/ap", response_class=HTMLResponse)
async def ap_page(request: Request):
    logger.info("Request received for AP page")
    ap_data = _load_ap_reconciliation_data()
    logger.info(f"AP data loaded. Found {len(ap_data.get('exceptions', []))} exceptions.")
    return templates.TemplateResponse("ap.html", {"request": request, "data": ap_data})


def _find_latest_bank_reconciliation_file(base_out: str = None) -> Optional[str]:
    if base_out is None:
        base_out = "out" if os.path.exists("out") else "../out" if os.path.exists("../out") else None
        if not base_out:
            return None
    
    pattern = os.path.join(base_out, "run_*", "bank_reconciliation_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]

def _load_bank_reconciliation_data() -> Dict[str, Any]:
    path = _find_latest_bank_reconciliation_file()
    if path and os.path.exists(path):
        logger.info(f"Found bank reconciliation file: {path}")
        try:
            with open(path, "r") as f:
                data = json.load(f)
                logger.info(f"Successfully loaded and parsed JSON from {path}")
                return data
        except Exception as e:
            logger.error(f"Error loading or parsing bank reconciliation data from {path}: {e}", exc_info=True)
    else:
        logger.warning("Could not find any bank reconciliation artifact file.")

    logger.warning("Returning fallback/empty bank reconciliation data.")
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": "N/A",
        "exceptions": [],
        "summary": {"count": 0, "total_abs_amount": 0, "by_entity_abs_amount": {}},
    }

def _find_latest_intercompany_file(base_out: str = None) -> Optional[str]:
    if base_out is None:
        base_out = "out" if os.path.exists("out") else "../out" if os.path.exists("../out") else None
        if not base_out:
            return None
    
    pattern = os.path.join(base_out, "run_*", "intercompany_reconciliation_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]

def _load_intercompany_data() -> Dict[str, Any]:
    path = _find_latest_intercompany_file()
    if path and os.path.exists(path):
        try:
            with open(path, "r") as f:
                data = json.load(f)
                
                # Transform data structure to match template expectations
                if 'summary' in data:
                    # Map by_pair_diff_abs to by_entity_abs_amount for template compatibility
                    if 'by_pair_diff_abs' in data['summary']:
                        data['summary']['by_entity_abs_amount'] = {}
                        for pair, amount in data['summary']['by_pair_diff_abs'].items():
                            entity = pair.split('->')[0] if '->' in pair else pair
                            data['summary']['by_entity_abs_amount'][entity] = amount
                    
                    # Add missing fields expected by template
                    if 'total_abs_amount' not in data['summary']:
                        data['summary']['total_abs_amount'] = data['summary'].get('total_diff_abs', 0)
                    if 'avg_confidence' not in data['summary']:
                        data['summary']['avg_confidence'] = None
                
                # Transform exceptions to match template field expectations
                if 'exceptions' in data:
                    for exception in data['exceptions']:
                        # Map fields for template compatibility
                        if 'entity_src' in exception and 'entity_amount' not in exception:
                            exception['entity_amount'] = exception.get('amount', 0)
                        if 'entity_dst' in exception and 'counterparty' not in exception:
                            exception['counterparty'] = exception['entity_dst']
                        if 'counterparty_amount' not in exception:
                            exception['counterparty_amount'] = exception.get('amount_dst', exception.get('amount', 0))
                        if 'difference' not in exception:
                            exception['difference'] = exception.get('diff_abs', 0)
                        if 'account' not in exception:
                            exception['account'] = exception.get('doc_id', 'N/A')
                        if 'status' not in exception:
                            exception['status'] = 'unmatched'
                        if 'confidence' not in exception:
                            exception['confidence'] = 'medium'
                        if 'id' not in exception:
                            exception['id'] = exception.get('doc_id', f"ic_{hash(str(exception))}")
                
                return data
        except Exception:
            pass
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": "N/A",
        "exceptions": [],
        "rows": [],
        "summary": {
            "count": 0, 
            "total_abs_amount": 0,
            "by_entity_abs_amount": {},
            "avg_confidence": None
        }
    }

# Removed duplicate bank endpoint - using the one with proper viewmodel below


@app.get("/intercompany", response_class=HTMLResponse)
async def intercompany_page(request: Request):
    # Load intercompany reconciliation data
    try:
        data = _load_intercompany_data()
        logger.info(f"Intercompany data loaded. Found {len(data.get('rows', []))} rows.")
    except Exception as e:
        logger.error(f"Error loading intercompany data: {e}")
        data = {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "period": "N/A",
            "rows": [],
            "summary": {"count": 0, "total_abs_amount": 0}
        }
    return templates.TemplateResponse("intercompany.html", {"request": request, "data": data})


@app.get("/hitl", response_class=HTMLResponse)
async def hitl_page(request: Request):
    # Convert store to list for template
    hitl_cases = list(_hitl_store.values()) 
    # Sort by priority (high > medium > low) and then by creation time
    priority_map = {"high": 0, "medium": 1, "low": 2}
    sorted_cases = sorted(
        hitl_cases, 
        key=lambda c: (priority_map.get(c.priority, 3), c.created_at)
    )
    
    return templates.TemplateResponse("hitl.html", {
        "request": request,
        "cases": sorted_cases,
        "case_count": len(sorted_cases)
    })
    

# ---- HTMX partials ----------------------------------------------------------


@app.get("/partials/kpis", response_class=HTMLResponse)
async def kpis_partial(request: Request):
    """Render KPI cards from latest run artifacts (metrics.json + gatekeeping)."""
    try:
        # Locate latest run directory by gatekeeping artifact
        base_out = "out" if os.path.exists("out") else "../out" if os.path.exists("../out") else None
        if not base_out:
            return Response(status_code=204)
        candidates = glob.glob(os.path.join(base_out, "run_*", "gatekeeping_run_*.json"))
        if not candidates:
            return Response(status_code=204)
        latest_gatekeeping = sorted(candidates, reverse=True)[0]
        run_dir = str(Path(latest_gatekeeping).parent)

        # Load metrics.json (primary) and gatekeeping (secondary)
        metrics_path = os.path.join(run_dir, "metrics.json")
        gatekeeping = {}
        metrics = {}
        try:
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
        except Exception:
            metrics = {}
        try:
            with open(latest_gatekeeping, "r") as f:
                gatekeeping = json.load(f)
        except Exception:
            gatekeeping = {}

        # Derive totals
        recs_total = int(metrics.get("bank_duplicates_count", 0)) + int(metrics.get("ic_mismatch_count", 0))
        tasks_total = int(metrics.get("ap_exceptions_count", 0)) + int(metrics.get("ar_exceptions_count", 0)) + int(metrics.get("accruals_exception_count", 0)) + int(metrics.get("flux_exceptions_count", 0))
        grand_total = recs_total + tasks_total

        # Compute state distribution heuristically
        block_close = bool(gatekeeping.get("block_close", metrics.get("gatekeeping_block_close", False)))
        auto_close_eligible = bool(gatekeeping.get("auto_close_eligible", metrics.get("gatekeeping_auto_close_eligible", False)))

        # Basic breakdown: if blocked -> most items not prepared; if eligible -> most completed; else in progress
        if grand_total == 0:
            not_prepared_recs = not_prepared_tasks = in_progress_recs = in_progress_tasks = completed_recs = completed_tasks = 0
        else:
            if block_close:
                not_prepared_recs = int(recs_total * 0.6)
                not_prepared_tasks = int(tasks_total * 0.6)
                completed_recs = int(recs_total * 0.1)
                completed_tasks = int(tasks_total * 0.1)
            elif auto_close_eligible:
                not_prepared_recs = int(recs_total * 0.05)
                not_prepared_tasks = int(tasks_total * 0.05)
                completed_recs = int(recs_total * 0.75)
                completed_tasks = int(tasks_total * 0.75)
            else:
                not_prepared_recs = int(recs_total * 0.2)
                not_prepared_tasks = int(tasks_total * 0.2)
                completed_recs = int(recs_total * 0.3)
                completed_tasks = int(tasks_total * 0.3)
            in_progress_recs = max(0, recs_total - not_prepared_recs - completed_recs)
            in_progress_tasks = max(0, tasks_total - not_prepared_tasks - completed_tasks)

        def pct(n: int, d: int) -> int:
            return int(round((n / d * 100))) if d > 0 else 0

        states = {
            "not_prepared": {
                "recs": not_prepared_recs,
                "tasks": not_prepared_tasks,
                "pct": pct(not_prepared_recs + not_prepared_tasks, grand_total)
            },
            "in_progress": {
                "recs": in_progress_recs,
                "tasks": in_progress_tasks,
                "pct": pct(in_progress_recs + in_progress_tasks, grand_total)
            },
            "completed": {
                "recs": completed_recs,
                "tasks": completed_tasks,
                "pct": pct(completed_recs + completed_tasks, grand_total)
            }
        }

        # Compute days remaining in close window based on period end
        period = gatekeeping.get("period") or metrics.get("period")
        days_remaining = 0
        try:
            if period:
                from calendar import monthrange
                year, month = map(int, period.split("-"))
                last_day = monthrange(year, month)[1]
                period_end = datetime(year, month, last_day)
                now = datetime.utcnow()
                days_remaining = max(0, (period_end - now).days)
        except Exception:
            days_remaining = 0

        data = {
            "close_clock_days_remaining": days_remaining,
            "totals": {"recs": recs_total, "tasks": tasks_total},
            "states": states
        }

        return templates.TemplateResponse("partials/kpis.html", {"request": request, "data": data})
    except Exception as e:
        print(f"[KPIs] Error: {e}")
        print(traceback.format_exc())
        return Response(status_code=204)


@app.get("/partials/recon-progress", response_class=HTMLResponse)
async def recon_progress_partial(request: Request):
    """Render reconciliation progress bar and stats from latest run artifacts.

    Expects template `partials/recon_progress.html` to receive context:
    { "data": { "reconciliations": { completion_pct, completed, count, segments[], cards[] } } }
    """
    try:
        # Locate latest run via gatekeeping artifact
        base_out = "out" if os.path.exists("out") else "../out" if os.path.exists("../out") else None
        if not base_out:
            return Response(status_code=204)
        candidates = glob.glob(os.path.join(base_out, "run_*", "gatekeeping_run_*.json"))
        if not candidates:
            return Response(status_code=204)
        latest_gatekeeping = sorted(candidates, reverse=True)[0]
        run_dir = str(Path(latest_gatekeeping).parent)

        # Load metrics (primary) and gatekeeping (secondary)
        metrics_path = os.path.join(run_dir, "metrics.json")
        metrics = {}
        gatekeeping = {}
        try:
            with open(metrics_path, "r") as f:
                metrics = json.load(f)
        except Exception:
            metrics = {}
        try:
            with open(latest_gatekeeping, "r") as f:
                gatekeeping = json.load(f)
        except Exception:
            gatekeeping = {}

        # Reconciliation scope: bank + intercompany as primary recon modules
        bank_ex = int(metrics.get("bank_duplicates_count", 0))
        ic_ex = int(metrics.get("ic_mismatch_count", 0))

        # Attempt to get totals if provided; otherwise estimate using gatekeeping context
        # Prefer explicit totals if available in metrics
        total_bank = int(metrics.get("bank_total_items", 0))
        total_ic = int(metrics.get("intercompany_total_items", 0))

        # If totals missing, estimate using fx rows proxy (same heuristic as dashboard)
        if (total_bank + total_ic) == 0:
            fx_proxy = _load_fx_data()
            proxy_rows = len(fx_proxy.get("rows", []))
            # Heuristic split across modules
            total_bank = max(0, int(proxy_rows * 1.5))
            total_ic = max(0, int(proxy_rows * 1.0))

        total_recons = max(0, total_bank + total_ic)
        total_ex = max(0, bank_ex + ic_ex)
        completed = max(0, total_recons - total_ex)

        # Derive state distribution influenced by gatekeeping signals
        block_close = bool(gatekeeping.get("block_close", metrics.get("gatekeeping_block_close", False)))
        auto_close_eligible = bool(gatekeeping.get("auto_close_eligible", metrics.get("gatekeeping_auto_close_eligible", False)))

        # Split completed/in-progress/not-started
        if total_recons == 0:
            comp = ip = ns = 0
        else:
            comp = completed
            # Heuristic: exceptions imply in-progress; remaining are not-started
            ip = min(total_ex, max(0, total_recons - comp))
            ns = max(0, total_recons - comp - ip)
            # If blocked, bias more towards not-started
            if block_close:
                shift = int(ns * 0.1)
                ns = min(total_recons, ns + shift)
                comp = max(0, comp - shift)
            # If eligible, bias towards completed
            elif auto_close_eligible:
                boost = int(max(1, total_recons * 0.05))
                moved = min(boost, ns)
                comp += moved
                ns -= moved

        def pct(n: int, d: int) -> int:
            return int(round((n / d * 100))) if d > 0 else 0

        segments = [
            {"label": "Completed", "count": comp, "pct": pct(comp, total_recons), "color": "bg-green-500"},
            {"label": "In Progress", "count": ip, "pct": pct(ip, total_recons), "color": "bg-yellow-400"},
            {"label": "Not Started", "count": ns, "pct": pct(ns, total_recons), "color": "bg-gray-300"},
        ]

        cards = [
            {"title": "Bank Exceptions", "value": bank_ex},
            {"title": "Intercompany Exceptions", "value": ic_ex},
            {"title": "Blocked to Close", "value": "Yes" if block_close else "No"},
            {"title": "Auto-Close Eligible", "value": "Yes" if auto_close_eligible else "No"},
        ]

        reconciliations = {
            "completion_pct": pct(comp, total_recons),
            "completed": comp,
            "count": total_recons,
            "segments": segments,
            "cards": cards,
        }

        data = {"reconciliations": reconciliations}
        return templates.TemplateResponse("partials/recon_progress.html", {"request": request, "data": data})
    except Exception as e:
        print(f"[Recon-Progress] Error: {e}")
        print(traceback.format_exc())
        return Response(status_code=204)


@app.get("/partials/clock", response_class=HTMLResponse)
async def clock_partial(request: Request):
    now = datetime.utcnow().isoformat() + "Z"
    return templates.TemplateResponse(
        "partials/clock.html",
        {"request": request, "ts": now}
    )


@app.get("/partials/tab/close-ops", response_class=HTMLResponse)
async def tab_close_ops(request: Request):
    return Response(status_code=204)


@app.get("/partials/tab/my-work", response_class=HTMLResponse)
async def tab_my_work(request: Request):
    return Response(status_code=204)


@app.get("/partials/tab/analytics", response_class=HTMLResponse)
async def tab_analytics(request: Request):
    return Response(status_code=204)


@app.get("/health")
async def health():
    return {"status": "ok", "ts": datetime.utcnow().isoformat() + "Z"}



# ---- TB Diagnostics -----------------------------------------------------------

def _find_latest_tb_diagnostics_file(base_out: str = None) -> Optional[str]:
    if base_out is None:
        base_out = "out" if os.path.exists("out") else "../out" if os.path.exists("../out") else None
        if not base_out:
            return None
    
    pattern = os.path.join(base_out, "run_*", "tb_diagnostics_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


def _load_tb_diagnostics_data() -> Dict[str, Any]:
    path = _find_latest_tb_diagnostics_file()
    if path and os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "period": "2025-08",
        "diagnostics": [],
        "summary": {"material_imbalances": 0, "auto_approved_entities": 0, "average_confidence_score": 0},
    }

def _tb_diagnostics_viewmodel(raw: Dict[str, Any]) -> Dict[str, Any]:
    diagnostics = raw.get("diagnostics", [])
    rollups = raw.get("rollups", {})

    # Safely add derived fields to diagnostics
    for diag in diagnostics:
        # For deterministic calculations, confidence is always 100%
        diag["confidence_score"] = 1.0
        diag["confidence_score_pct"] = 100.0
        diag["is_balanced"] = abs(diag.get("imbalance_usd", 0)) < 0.01
        
        # Add confidence scores to top accounts as well
        for account in diag.get("top_accounts", []):
            account["confidence_score"] = 1.0
            account["confidence_score_pct"] = 100.0

    # Calculate summary metrics from rollups
    entity_balanced_map = rollups.get("entity_balanced", {})
    material_imbalances = sum(1 for is_balanced in entity_balanced_map.values() if not is_balanced)
    auto_approved_entities = sum(1 for is_balanced in entity_balanced_map.values() if is_balanced)

    # If confidence scores are ever added, this would calculate the average
    avg_confidence = sum(d.get("confidence_score", 0) for d in diagnostics)
    avg_confidence_score = (avg_confidence / len(diagnostics)) if diagnostics else 0

    summary = {
        "material_imbalances": material_imbalances,
        "auto_approved_entities": auto_approved_entities,
        "average_confidence_score": round(avg_confidence_score * 100, 1)
    }

    return {
        "generated_at": raw.get("generated_at"),
        "period": raw.get("period"),
        "diagnostics": diagnostics,
        "summary": summary
    }


@app.get("/tb", response_class=HTMLResponse)
async def tb_page(request: Request):
    raw_data = _load_tb_diagnostics_data()
    view_model = _tb_diagnostics_viewmodel(raw_data)
    return templates.TemplateResponse("tb.html", {
        "request": request,
        "data": view_model
    })


# ---- AP/AR Reconciliation -----------------------------------------------------



# ---- Bank Reconciliation --------------------------------------------------------


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
    # Load auto-journals data if available
    auto_journals_data = {}
    try:
        latest_run_dir = Path(path).parent
        run_id = _latest_run_id_from_path(latest_run_dir)
        auto_journals_artifact = latest_run_dir / f"auto_journals_{run_id}.json"
        if auto_journals_artifact.exists():
            with open(auto_journals_artifact, "r") as f:
                auto_journals_data = json.load(f)
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
    entities = sorted({r.get("entity") for r in rows})
    currencies = sorted({r.get("currency") for r in rows if r.get("currency") != "USD"})
    
    # Filter
    if entity:
        rows = [r for r in rows if r.get("entity") == entity]
    if currency:
        rows = [r for r in rows if r.get("currency") == currency]
    
    # Process AI insights for each row - deterministic calculations have 100% confidence
    for r in rows:
        r['confidence_score'] = 1.0
        r['confidence_score_pct'] = 100.0
        # Add materiality flag based on diff amount
        diff_abs = abs(float(r.get("diff_usd", 0.0)))
        r['is_material'] = diff_abs > raw.get("policy", {}).get("tolerance_usd", 0.01)
        r['auto_approved'] = not r['is_material']

    # Sort by absolute diff desc
    rows_sorted = sorted(rows, key=lambda r: abs(float(r.get("diff_usd", 0.0))), reverse=True)
    
    # Calculate metrics
    total_diff = sum(abs(float(r.get("diff_usd", 0.0))) for r in rows)
    material_rows = [r for r in rows if r.get('is_material', False)]
    
    summary = raw.get("summary", {})
    summary['average_confidence_score'] = 1.0
    summary['average_confidence_score_pct'] = 100.0

    # Create proper summary metrics
    summary_metrics = {
        "material_diff_count": len(material_rows),
        "auto_approved_count": len([r for r in rows if r.get('auto_approved', False)]),
        "average_confidence_score_pct": 100.0,
        "total_abs_diff_usd": total_diff,
    }

    return {
        "period": raw.get("period"),
        "generated_at": raw.get("generated_at"),
        "entities": entities,
        "currencies": currencies,
        "selected_entity": entity or "",
        "selected_currency": currency or "",
        "rows": rows_sorted,
        "count_filtered": len(rows_sorted),
        "total_diff": total_diff,
        "material_count": len(material_rows),
        "policy": raw.get("policy", {}),
        "summary": summary_metrics,
    }


def _find_latest_flux_file(base_out: str = None) -> Optional[str]:
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
        except Exception as e:
            raise RuntimeError(f"Failed to load flux data from {path}: {e}")
    else:
        raise RuntimeError("No flux analysis artifacts found. Run the close process first.")


def _flux_viewmodel(raw: Dict[str, Any], entity: Optional[str], min_abs: Optional[float]) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = raw.get("rows", [])
    entities = sorted({r.get("entity") for r in rows})
    
    # Filter
    filtered_rows = rows
    if entity:
        filtered_rows = [r for r in filtered_rows if r.get("entity") == entity]
    if min_abs is not None:
        filtered_rows = [r for r in filtered_rows if abs(float(r.get("var_vs_budget", 0.0))) >= min_abs]
    
    # Sort by absolute variance vs budget desc (since var_vs_prior is mostly 0)
    rows_sorted = sorted(filtered_rows, key=lambda r: abs(float(r.get("var_vs_budget", 0.0))), reverse=True)
    
    # Calculate metrics from filtered rows using budget variance
    total_variance = sum(abs(float(r.get("var_vs_budget", 0.0))) for r in rows_sorted)
    
    return {
        "period": raw.get("period"),
        "prior": raw.get("prior"),
        "entities": entities,
        "selected_entity": entity or "",
        "min_abs": min_abs or "",
        "rows": rows_sorted,
        "count_filtered": len(rows_sorted),
        "total_variance": total_variance,
        "rules": raw.get("rules", {"threshold_basis": "default", "default_floor_usd": 1000.0}),
    }


def _select_ap_row(period: Optional[str], entity: Optional[str], bill_id: Optional[str]) -> Dict[str, Any]:
    raw = _load_ap_data()
    exception = next((e for e in raw.get("exceptions", []) if (not period or raw.get("period") == period) and e.get("entity") == entity and e.get("bill_id") == bill_id), None)
    
    # Generate AI analysis for AP exceptions
    ai_analysis = {}
    if exception:
        reason = exception.get("reason", "unknown")
        amount = exception.get("amount_usd", 0.0)
        vendor = exception.get("vendor_name", "Unknown")
        age_days = exception.get("age_days", 0)
        
        ai_analysis = {
            "narrative": f"[AI] AP exception detected: {reason.replace('_', ' ').title()} for bill {bill_id} with {vendor}. Amount: ${amount:,.2f}. Age: {age_days} days.",
            "business_driver": "Payment processing delay" if reason == "overdue" else "Aging management" if reason == "aged_over_60" else "Duplicate control",
            "confidence": 0.85 if reason == "potential_duplicate" else 0.75,
            "risk_level": "High" if age_days > 90 else "Medium" if age_days > 60 else "Low"
        }
    
    return {
        "module": "AP",
        "artifact_path": _find_latest_ap_file(),
        "run_id": _latest_run_id_from_path(_find_latest_ap_file()) if _find_latest_ap_file() else "mock",
        "header": {"period": period or raw.get("period"), "entity": entity, "bill_id": bill_id, "basis": "ap_exception"},
        "metrics": exception or {},
        "threshold": 0.0,
        "evidence": _gather_email_evidence(entity, None, period or raw.get("period")),
        "ai_narrative": ai_analysis,
        "provenance": {"model": "LangGraph Close Agents", "prompt": None, "run_id": "mock"},
    }


def _select_ar_row(period: Optional[str], entity: Optional[str], invoice_id: Optional[str]) -> Dict[str, Any]:
    raw = _load_ar_data()
    exception = next((e for e in raw.get("exceptions", []) if (not period or raw.get("period") == period) and e.get("entity") == entity and e.get("invoice_id") == invoice_id), None)
    
    # Generate AI analysis for AR exceptions
    ai_analysis = {}
    if exception:
        reason = exception.get("reason", "unknown")
        amount = exception.get("amount_usd", 0.0)
        customer = exception.get("customer_name", "Unknown")
        age_days = exception.get("age_days", 0)
        
        ai_analysis = {
            "narrative": f"[AI] AR exception detected: {reason.replace('_', ' ').title()} for invoice {invoice_id} with {customer}. Amount: ${amount:,.2f}. Age: {age_days} days.",
            "business_driver": "Collection management" if reason == "overdue" else "Credit risk" if reason == "aged_over_60" else "Customer relations",
            "confidence": 0.80,
            "risk_level": "Critical" if age_days > 120 else "High" if age_days > 90 else "Medium"
        }
    
    return {
        "module": "AR",
        "artifact_path": _find_latest_ar_file(),
        "run_id": _latest_run_id_from_path(_find_latest_ar_file()) if _find_latest_ar_file() else "mock",
        "header": {"period": period or raw.get("period"), "entity": entity, "invoice_id": invoice_id, "basis": "ar_exception"},
        "metrics": exception or {},
        "threshold": 0.0,
        "evidence": _gather_email_evidence(entity, None, period or raw.get("period")),
        "ai_narrative": ai_analysis,
        "provenance": {"model": "LangGraph Close Agents", "prompt": None, "run_id": "mock"},
    }


def _select_fx_row(period: Optional[str], entity: Optional[str], account: Optional[str]) -> Dict[str, Any]:
    raw = _load_fx_data()
    row = next((r for r in raw.get("rows", []) if (not period or raw.get("period") == period) and r.get("entity") == entity and r.get("account") == account), None)
    
    # Generate AI analysis for FX differences
    ai_analysis = {}
    if row:
        diff_usd = row.get("diff_usd", 0.0)
        currency = row.get("currency", "USD")
        rate = row.get("rate", 1.0)
        
        ai_analysis = {
            "narrative": f"[AI] FX translation difference detected for {entity} account {account} in {currency}. Computed vs reported variance: ${diff_usd:,.2f}. Rate: {rate}.",
            "business_driver": "FX rate fluctuation" if abs(diff_usd) > 1000 else "Rounding difference",
            "confidence": 0.90 if abs(diff_usd) > 5000 else 0.75,
            "risk_level": "High" if abs(diff_usd) > 10000 else "Medium" if abs(diff_usd) > 1000 else "Low"
        }
    
    return {
        "module": "FX",
        "artifact_path": _find_latest_fx_file(),
        "run_id": _latest_run_id_from_path(_find_latest_fx_file()) if _find_latest_fx_file() else "mock",
        "header": {"period": period or raw.get("period"), "entity": entity, "account": account, "basis": "fx_translation"},
        "metrics": row or {},
        "threshold": raw.get("policy", {}).get("tolerance_usd", 0.01),
        "evidence": _gather_email_evidence(entity, None, period or raw.get("period")),
        "ai_narrative": ai_analysis,
        "provenance": {"model": "LangGraph Close Agents", "prompt": None, "run_id": "mock"},
    }


def _select_flux_row(period: Optional[str], entity: Optional[str], account: Optional[str]) -> Dict[str, Any]:
    raw = _load_flux_data()
    row = next((r for r in raw.get("rows", []) if (not period or raw.get("period") == period) and r.get("entity") == entity and r.get("account") == account), None)
    
    # Generate AI analysis for flux variances
    ai_analysis = {}
    if row:
        variance = row.get("variance", 0.0)
        variance_pct = row.get("variance_pct", 0.0)
        account_name = row.get("account_name", "Unknown")
        
        ai_analysis = {
            "narrative": f"[AI] Budget variance detected for {entity} {account_name}. Variance: ${variance:,.2f} ({variance_pct:.1f}%). Requires management explanation.",
            "business_driver": "Operational variance" if abs(variance_pct) < 20 else "Significant business change",
            "confidence": 0.85,
            "risk_level": "High" if abs(variance_pct) > 25 else "Medium" if abs(variance_pct) > 10 else "Low"
        }
    
    return {
        "module": "FLUX",
        "artifact_path": _find_latest_flux_file(),
        "run_id": _latest_run_id_from_path(_find_latest_flux_file()) if _find_latest_flux_file() else "mock",
        "header": {"period": period or raw.get("period"), "entity": entity, "account": account, "basis": "flux_variance"},
        "metrics": row or {},
        "threshold": raw.get("policy", {}).get("materiality_usd", 5000.0),
        "evidence": _gather_email_evidence(entity, None, period or raw.get("period")),
        "ai_narrative": ai_analysis,
        "provenance": {"model": "LangGraph Close Agents", "prompt": None, "run_id": "mock"},
    }


def _select_bank_row(period: Optional[str], entity: Optional[str], bank_txn_id: Optional[str]) -> Dict[str, Any]:
    raw = _load_bank_data()
    exception = next((e for e in raw.get("exceptions", []) if (not period or raw.get("period") == period) and e.get("entity") == entity and e.get("bank_txn_id") == bank_txn_id), None)
    
    # Generate AI analysis for bank exceptions
    ai_analysis = {}
    if exception:
        reason = exception.get("reason", "unknown")
        amount = exception.get("amount", 0.0)
        counterparty = exception.get("counterparty", "Unknown")
        classification = exception.get("classification", "unknown")
        
        ai_analysis = {
            "narrative": f"[AI] Bank exception detected: {reason.replace('_', ' ').title()} for transaction {bank_txn_id} with {counterparty}. Amount: ${amount:,.2f}. Classification: {classification}.",
            "business_driver": "Forensic risk" if classification == "forensic_risk" else "Timing difference" if reason == "timing_difference" else "Operational issue",
            "confidence": 0.95 if classification == "forensic_risk" else 0.80,
            "risk_level": "Critical" if classification == "forensic_risk" else "Medium"
        }
    
    return {
        "module": "BANK",
        "artifact_path": _find_latest_bank_file(),
        "run_id": _latest_run_id_from_path(_find_latest_bank_file()) if _find_latest_bank_file() else "mock",
        "header": {"period": period or raw.get("period"), "entity": entity, "bank_txn_id": bank_txn_id, "basis": "bank_exception"},
        "metrics": exception or {},
        "threshold": 0.0,
        "evidence": _gather_email_evidence(entity, None, period or raw.get("period")),
        "ai_narrative": ai_analysis,
        "provenance": {"model": "LangGraph Close Agents", "prompt": None, "run_id": "mock"},
    }


def _latest_run_id_from_path(path: Optional[str]) -> Optional[str]:
    """Extract run ID from artifact path"""
    if not path:
        return None
    # Extract from path like "out/run_20250902T170019Z/fx_translation_run_20250902T170019Z.json"
    import re
    match = re.search(r'run_(\d{8}T\d{6}Z)', path)
    return match.group(1) if match else "mock"


def _gather_email_evidence(entity: Optional[str], account: Optional[str], period: Optional[str]) -> List[Dict[str, Any]]:
    """Mock email evidence for details drawer"""
    return [
        {
            "subject": f"RE: {entity} Month-end inquiry",
            "sender": "controller@techcorp.com",
            "date": "2025-08-31",
            "confidence": 0.85,
            "relevance": "High",
            "snippet": f"Following up on the {entity} reconciliation items..."
        }
    ]


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


@app.get("/bank-table", response_class=HTMLResponse)
async def bank_table_partial(request: Request, entity: Optional[str] = None, classification: Optional[str] = None):
    raw = _load_bank_data()
    vm = _bank_viewmodel(raw, entity, classification)
    return templates.TemplateResponse(
        "partials/bank_table.html",
        {"request": request, "bank": vm}
    )


def _ap_viewmodel(raw: Dict[str, Any], entity: Optional[str], reason: Optional[str]) -> Dict[str, Any]:
    exceptions: List[Dict[str, Any]] = raw.get("exceptions", [])
    entities = sorted({e.get("entity") for e in exceptions})
    reasons = sorted({e.get("reason") for e in exceptions})
    
    # Filter
    if entity:
        exceptions = [e for e in exceptions if e.get("entity") == entity]
    if reason:
        exceptions = [e for e in exceptions if e.get("reason") == reason]
    
    # Sort by amount desc (absolute value)
    exceptions_sorted = sorted(exceptions, key=lambda e: abs(float(e.get("amount_usd", 0.0))), reverse=True)
    
    # Calculate metrics
    total_amount = sum(abs(float(e.get("amount_usd", 0.0))) for e in exceptions)
    overdue_exceptions = [e for e in exceptions if e.get("reason") == "overdue"]
    overdue_amount = sum(abs(float(e.get("amount_usd", 0.0))) for e in overdue_exceptions)
    
    return {
        "period": raw.get("period"),
        "entities": entities,
        "reasons": reasons,
        "selected_entity": entity or "",
        "selected_reason": reason or "",
        "exceptions": exceptions_sorted,
        "count_filtered": len(exceptions_sorted),
        "total_amount": total_amount,
        "overdue_count": len(overdue_exceptions),
        "overdue_amount": overdue_amount,
    }


def _ar_viewmodel(raw: Dict[str, Any], entity: Optional[str], reason: Optional[str]) -> Dict[str, Any]:
    exceptions: List[Dict[str, Any]] = raw.get("exceptions", [])
    entities = sorted({e.get("entity") for e in exceptions})
    reasons = sorted({e.get("reason") for e in exceptions})
    
    # Filter
    if entity:
        exceptions = [e for e in exceptions if e.get("entity") == entity]
    if reason:
        exceptions = [e for e in exceptions if e.get("reason") == reason]
    
    # Sort by amount desc (absolute value)
    exceptions_sorted = sorted(exceptions, key=lambda e: abs(float(e.get("amount_usd", 0.0))), reverse=True)
    
    # Calculate metrics
    total_amount = sum(abs(float(e.get("amount_usd", 0.0))) for e in exceptions)
    overdue_exceptions = [e for e in exceptions if e.get("reason") == "overdue"]
    overdue_amount = sum(abs(float(e.get("amount_usd", 0.0))) for e in overdue_exceptions)
    
    return {
        "period": raw.get("period"),
        "entities": entities,
        "reasons": reasons,
        "selected_entity": entity or "",
        "selected_reason": reason or "",
        "exceptions": exceptions_sorted,
        "count_filtered": len(exceptions_sorted),
        "total_amount": total_amount,
        "overdue_count": len(overdue_exceptions),
        "overdue_amount": overdue_amount,
    }


@app.get("/ap", response_class=HTMLResponse)
async def ap_reconciliation(request: Request, entity: Optional[str] = None, reason: Optional[str] = None):
    raw = _load_ap_data()
    vm = _ap_viewmodel(raw, entity, reason)
    return templates.TemplateResponse(
        "ap.html",
        {"request": request, "ap": vm}
    )


@app.get("/ap-table", response_class=HTMLResponse)
async def ap_table_partial(request: Request, entity: Optional[str] = None, reason: Optional[str] = None):
    raw = _load_ap_data()
    vm = _ap_viewmodel(raw, entity, reason)
    return templates.TemplateResponse(
        "partials/ap_table.html",
        {"request": request, "ap": vm}
    )


@app.get("/ar", response_class=HTMLResponse)
async def ar_reconciliation(request: Request, entity: Optional[str] = None, reason: Optional[str] = None):
    raw = _load_ar_data()
    vm = _ar_viewmodel(raw, entity, reason)
    return templates.TemplateResponse(
        "ar.html",
        {"request": request, "ar": vm}
    )


@app.get("/ar-table", response_class=HTMLResponse)
async def ar_table_partial(request: Request, entity: Optional[str] = None, reason: Optional[str] = None):
    raw = _load_ar_data()
    vm = _ar_viewmodel(raw, entity, reason)
    return templates.TemplateResponse(
        "partials/ar_table.html",
        {"request": request, "ar": vm}
    )


@app.get("/flux", response_class=HTMLResponse)
async def flux_page(
    request: Request,
    entity: Optional[str] = None,
    min_abs: Optional[float] = None,
):
    """Flux analysis page, showing variances vs prior and budget."""
    try:
        raw_data = _load_flux_data()
        view_model = _flux_viewmodel(raw_data, entity, min_abs)
        return templates.TemplateResponse("flux.html", {
            "request": request,
            "flux": view_model
        })
    except Exception as e:
        # Handle case where flux data isn't generated yet
        return templates.TemplateResponse("flux.html", {
            "request": request,
            "flux": None,
            "error": str(e)
        })


@app.get("/bank", response_class=HTMLResponse)
async def bank_reconciliation(request: Request, entity: Optional[str] = None, classification: Optional[str] = None):
    raw = _load_bank_reconciliation_data()
    vm = _bank_viewmodel(raw, entity, classification)
    return templates.TemplateResponse(
        "bank.html",
        {"request": request, "bank": vm}
    )


@app.get("/flux-table", response_class=HTMLResponse)
async def flux_table_partial(request: Request, entity: Optional[str] = None, account: Optional[str] = None):
    raw = _load_flux_data()
    vm = _flux_viewmodel(raw, entity, account)
    return templates.TemplateResponse(
        "partials/flux_table.html",
        {"request": request, "flux": vm}
    )


@app.get("/details", response_class=HTMLResponse)
async def details_drawer(request: Request, module: str, period: Optional[str] = None, entity: Optional[str] = None, 
                        bank_txn_id: Optional[str] = None, bill_id: Optional[str] = None, 
                        invoice_id: Optional[str] = None, account: Optional[str] = None):
    """Details drawer for exception drill-through"""
    
    if module == "BANK":
        details = _select_bank_row(period, entity, bank_txn_id)
    elif module == "AP":
        details = _select_ap_row(period, entity, bill_id)
    elif module == "AR":
        details = _select_ar_row(period, entity, invoice_id)
    elif module == "FX":
        details = _select_fx_row(period, entity, account)
    elif module == "FLUX":
        details = _select_flux_row(period, entity, account)
    else:
        details = {"error": f"Unknown module: {module}"}
    
    return templates.TemplateResponse(
        "partials/details_drawer.html",
        {"request": request, "d": details}
    )


# ---- Bank Reconciliation ----------------------------------------------------

def _find_latest_bank_file(base_out: str = None) -> Optional[str]:
    # Auto-detect out directory location
    if base_out is None:
        if os.path.exists("out"):
            base_out = "out"
        elif os.path.exists("../out"):
            base_out = "../out"
        else:
            return None
    
    pattern = os.path.join(base_out, "run_*", "bank_reconciliation_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


def _find_latest_ap_file() -> Optional[str]:
    base_out = None
    if os.path.exists("out"):
        base_out = "out"
    elif os.path.exists("../out"):
        base_out = "../out"
    else:
        return None
    
    pattern = os.path.join(base_out, "run_*", "ap_reconciliation_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


def _find_latest_ar_file() -> Optional[str]:
    base_out = None
    if os.path.exists("out"):
        base_out = "out"
    elif os.path.exists("../out"):
        base_out = "../out"
    else:
        return None
    
    pattern = os.path.join(base_out, "run_*", "ar_reconciliation_run_*.json")
    candidates = glob.glob(pattern)
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0]


def _load_bank_data() -> Dict[str, Any]:
    path = _find_latest_bank_file()
    if path and os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load bank data from {path}: {e}")
    else:
        raise RuntimeError("No bank reconciliation artifacts found. Run the close process first.")


def _bank_viewmodel(raw: Dict[str, Any], entity: Optional[str], classification: Optional[str]) -> Dict[str, Any]:
    exceptions: List[Dict[str, Any]] = raw.get("exceptions", [])
    entities = sorted({e.get("entity") for e in exceptions})
    classifications = sorted({e.get("classification") for e in exceptions})
    
    # Filter
    if entity:
        exceptions = [e for e in exceptions if e.get("entity") == entity]
    if classification:
        exceptions = [e for e in exceptions if e.get("classification") == classification]
    
    # Sort by amount desc (absolute value)
    exceptions_sorted = sorted(exceptions, key=lambda e: abs(float(e.get("amount", 0.0))), reverse=True)
    
    # Calculate metrics
    total_amount = sum(abs(float(e.get("amount", 0.0))) for e in exceptions)
    forensic_exceptions = [e for e in exceptions if e.get("classification") == "forensic_risk"]
    forensic_amount = sum(abs(float(e.get("amount", 0.0))) for e in forensic_exceptions)
    
    return {
        "period": raw.get("period"),
        "entities": entities,
        "classifications": classifications,
        "selected_entity": entity or "",
        "selected_classification": classification or "",
        "exceptions": exceptions_sorted,
        "count_filtered": len(exceptions_sorted),
        "total_amount": total_amount,
        "forensic_count": len(forensic_exceptions),
        "forensic_amount": forensic_amount,
        "rules": raw.get("rules", {}),
        "summary": raw.get("summary", {}),
    }


def _load_ap_data() -> Dict[str, Any]:
    path = _find_latest_ap_file()
    if path and os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load AP data from {path}: {e}")
    else:
        raise RuntimeError("No AP reconciliation artifacts found. Run the close process first.")


def _load_ar_data() -> Dict[str, Any]:
    path = _find_latest_ar_file()
    if path and os.path.exists(path):
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            raise RuntimeError(f"Failed to load AR data from {path}: {e}")
    else:
        raise RuntimeError("No AR reconciliation artifacts found. Run the close process first.")


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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)
