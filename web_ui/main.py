#!/usr/bin/env python3
"""
R2R Financial Close - HTMX Web UI
FastAPI server that loads existing JSON artifacts from /out/ directory
100% separate from backend scripts - read-only artifact viewer
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import json
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import uvicorn

app = FastAPI(title="R2R Financial Close UI")

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUT_DIR = PROJECT_ROOT / "out"
TEMPLATES_DIR = Path(__file__).parent / "templates"
STATIC_DIR = Path(__file__).parent / "static"

# Setup templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

class ArtifactLoader:
    """Load and parse JSON artifacts from /out/ directory"""
    
    @staticmethod
    def get_available_runs() -> List[Dict[str, Any]]:
        """Get list of available run directories"""
        if not OUT_DIR.exists():
            return []
        
        runs = []
        for run_dir in OUT_DIR.iterdir():
            if run_dir.is_dir() and run_dir.name.startswith("run_"):
                timestamp = run_dir.name.replace("run_", "")
                try:
                    # Parse timestamp
                    dt = datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ")
                    
                    # Count artifacts
                    artifacts = list(run_dir.glob("*.json")) + list(run_dir.glob("*.jsonl"))
                    
                    runs.append({
                        "timestamp": timestamp,
                        "label": dt.strftime("%b %d, %Y %I:%M %p"),
                        "path": str(run_dir),
                        "artifacts_count": len(artifacts),
                        "created_at": dt.isoformat()
                    })
                except ValueError:
                    continue
        
        # Sort by timestamp, newest first
        runs.sort(key=lambda x: x["timestamp"], reverse=True)
        return runs
    
    @staticmethod
    def load_close_report(run_timestamp: str) -> Optional[Dict[str, Any]]:
        """Load close report for a specific run"""
        run_dir = OUT_DIR / f"run_{run_timestamp}"
        if not run_dir.exists():
            return None
        
        # Find close report file
        close_report_files = list(run_dir.glob("close_report_*.json"))
        if not close_report_files:
            return None
        
        try:
            with open(close_report_files[0], 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    
    @staticmethod
    def load_artifact(run_timestamp: str, artifact_name: str) -> Optional[Dict[str, Any]]:
        """Load specific artifact by name pattern"""
        run_dir = OUT_DIR / f"run_{run_timestamp}"
        if not run_dir.exists():
            return None
        
        # Search for artifact files matching pattern
        patterns = [
            f"{artifact_name}_*.json",
            f"{artifact_name}.json"
        ]
        
        for pattern in patterns:
            files = list(run_dir.glob(pattern))
            if files:
                try:
                    with open(files[0], 'r') as f:
                        return json.load(f)
                except (json.JSONDecodeError, FileNotFoundError):
                    continue
        
        # Check ai_cache subdirectory
        ai_cache_dir = run_dir / "ai_cache"
        if ai_cache_dir.exists():
            for pattern in patterns:
                files = list(ai_cache_dir.glob(pattern))
                if files:
                    try:
                        with open(files[0], 'r') as f:
                            return json.load(f)
                    except (json.JSONDecodeError, FileNotFoundError):
                        continue
        
        return None
    
    @staticmethod
    def get_run_metrics(run_timestamp: str) -> Optional[Dict[str, Any]]:
        """Load metrics.json for a run"""
        run_dir = OUT_DIR / f"run_{run_timestamp}"
        metrics_file = run_dir / "metrics.json"
        
        if not metrics_file.exists():
            return None
        
        try:
            with open(metrics_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard showing available runs"""
    runs = ArtifactLoader.get_available_runs()
    latest_run = runs[0] if runs else None
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "runs": runs,
        "latest_run": latest_run
    })

@app.get("/run/{run_timestamp}", response_class=HTMLResponse)
async def close_detail(request: Request, run_timestamp: str):
    """Detailed view of a specific close run"""
    close_report = ArtifactLoader.load_close_report(run_timestamp)
    if not close_report:
        raise HTTPException(status_code=404, detail="Run not found")
    
    metrics = ArtifactLoader.get_run_metrics(run_timestamp)
    
    return templates.TemplateResponse("close_detail.html", {
        "request": request,
        "run_timestamp": run_timestamp,
        "close_report": close_report,
        "metrics": metrics
    })

@app.get("/run/{run_timestamp}/reconciliation/{recon_type}", response_class=HTMLResponse)
async def reconciliation_detail(request: Request, run_timestamp: str, recon_type: str):
    """Detailed view of reconciliation (ap, ar, bank, intercompany)"""
    artifact_name = f"{recon_type}_reconciliation"
    recon_data = ArtifactLoader.load_artifact(run_timestamp, artifact_name)
    
    if not recon_data:
        raise HTTPException(status_code=404, detail=f"Reconciliation {recon_type} not found")
    
    # Transform data to match template expectations
    if recon_data and "exceptions" in recon_data:
        exceptions_count = len(recon_data.get("exceptions", []))
        recon_data["summary"] = {
            "exceptions_count": exceptions_count,
            "total_items": len(recon_data.get("exceptions", [])),
            "clean": exceptions_count == 0
        }
    
    # Load AI insights if available
    ai_artifact_name = f"{recon_type}_ai" if recon_type != "bank" else "bank_ai_rationales"
    ai_data = ArtifactLoader.load_artifact(run_timestamp, ai_artifact_name)
    
    return templates.TemplateResponse("reconciliation.html", {
        "request": request,
        "run_timestamp": run_timestamp,
        "recon_type": recon_type,
        "recon_data": recon_data,
        "ai_data": ai_data
    })

@app.get("/run/{run_timestamp}/flux", response_class=HTMLResponse)
async def flux_analysis(request: Request, run_timestamp: str):
    """Flux analysis view"""
    flux_data = ArtifactLoader.load_artifact(run_timestamp, "flux_analysis")
    if not flux_data:
        raise HTTPException(status_code=404, detail="Flux analysis not found")
    
    # Load AI narratives
    ai_data = ArtifactLoader.load_artifact(run_timestamp, "flux_ai_narratives")
    
    return templates.TemplateResponse("flux_analysis.html", {
        "request": request,
        "run_timestamp": run_timestamp,
        "flux_data": flux_data,
        "ai_data": ai_data
    })

@app.get("/run/{run_timestamp}/hitl", response_class=HTMLResponse)
async def hitl_cases(request: Request, run_timestamp: str):
    """HITL cases view"""
    cases_data = ArtifactLoader.load_artifact(run_timestamp, "cases")
    if not cases_data:
        raise HTTPException(status_code=404, detail="HITL cases not found")
    
    # Load AI case summaries
    ai_data = ArtifactLoader.load_artifact(run_timestamp, "hitl_ai_case_summaries")
    
    return templates.TemplateResponse("hitl_cases.html", {
        "request": request,
        "run_timestamp": run_timestamp,
        "cases_data": cases_data,
        "ai_data": ai_data
    })

@app.get("/api/runs")
async def api_runs():
    """API endpoint for runs list"""
    runs = ArtifactLoader.get_available_runs()
    return {"runs": runs}

@app.get("/api/run/{run_timestamp}/artifacts")
async def api_artifacts(run_timestamp: str):
    """API endpoint for run artifacts list"""
    run_dir = OUT_DIR / f"run_{run_timestamp}"
    if not run_dir.exists():
        raise HTTPException(status_code=404, detail="Run not found")
    
    artifacts = []
    for file_path in run_dir.glob("*.json"):
        artifacts.append({
            "name": file_path.stem,
            "path": str(file_path),
            "size": file_path.stat().st_size
        })
    
    # Check ai_cache subdirectory
    ai_cache_dir = run_dir / "ai_cache"
    if ai_cache_dir.exists():
        for file_path in ai_cache_dir.glob("*.json"):
            artifacts.append({
                "name": file_path.stem,
                "path": str(file_path),
                "size": file_path.stat().st_size,
                "ai_cache": True
            })
    
    return {"artifacts": artifacts}

@app.get("/api/run/{run_timestamp}/artifact/{artifact_name}")
async def api_artifact(run_timestamp: str, artifact_name: str):
    """API endpoint for specific artifact"""
    data = ArtifactLoader.load_artifact(run_timestamp, artifact_name)
    if not data:
        raise HTTPException(status_code=404, detail="Artifact not found")
    return data

if __name__ == "__main__":
    print("Starting R2R Financial Close HTMX UI...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Output directory: {OUT_DIR}")
    print(f"Templates directory: {TEMPLATES_DIR}")
    
    uvicorn.run(app, host="0.0.0.0", port=8080, reload=True)
