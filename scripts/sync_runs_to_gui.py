#!/usr/bin/env python3
"""
Sync Runs to GUI Manifest

Scans the `out` directory for completed runs and updates the `gui/public/runs_manifest.json`
file that the frontend uses to display the list of available runs.

This script is necessary because the core `run_close.py` process outputs to a unique
directory but does not handle updating the UI's knowledge of that run.
"""

import json
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
OUT_DIR = PROJECT_ROOT / "out"
GUI_MANIFEST_PATH = PROJECT_ROOT / "gui" / "public" / "runs_manifest.json"

def get_run_details(run_dir: Path) -> dict | None:
    """Extracts metadata from a run directory."""
    try:
        timestamp = run_dir.name.replace("run_", "")
        
        # Basic validation of timestamp format
        datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ")

        # Count artifacts recursively
        artifacts = list(run_dir.rglob("*.json")) + list(run_dir.rglob("*.jsonl"))
        
        # Try to get more details from a summary file if it exists
        # This is a placeholder for future enhancement
        return {
            "timestamp": timestamp,
            "label": datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ").strftime("%b %d, %Y %I:%M %p"),
            "status": "completed",
            "entity": "ALL",
            "period": "2025-08",
            "created_at": datetime.fromtimestamp(run_dir.stat().st_ctime).isoformat() + "Z",
            "duration_seconds": 0,  # Placeholder
            "artifacts_count": len(artifacts)
        }
    except (ValueError, FileNotFoundError):
        return None

def sync_runs():
    """Scans the output directory and updates the GUI manifest."""
    print(f"🔍 Scanning for runs in: {OUT_DIR}")
    
    if not OUT_DIR.exists():
        print("Output directory not found. No runs to sync.")
        return

    run_dirs = [d for d in OUT_DIR.iterdir() if d.is_dir() and d.name.startswith("run_")]
    
    all_runs = []
    for run_dir in run_dirs:
        details = get_run_details(run_dir)
        if details:
            all_runs.append(details)
    
    if not all_runs:
        print("No valid run directories found.")
        return

    # Sort runs by timestamp, newest first
    all_runs.sort(key=lambda x: x["timestamp"], reverse=True)
    
    latest_run = all_runs[0]["timestamp"] if all_runs else None
    
    manifest = {
        "runs": all_runs,
        "latest": latest_run
    }
    
    # Write to the GUI manifest file
    GUI_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(GUI_MANIFEST_PATH, 'w') as f:
        json.dump(manifest, f, indent=2)
        
    print(f"✅ Successfully synced {len(all_runs)} runs to {GUI_MANIFEST_PATH}")
    print(f"Latest run set to: {latest_run}")

if __name__ == "__main__":
    sync_runs()
