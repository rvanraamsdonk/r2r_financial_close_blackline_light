"""
Simple Flask API for R2R Financial Close
Handles run management and triggering close processes
"""

from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
import subprocess
import json
import os
import threading
from datetime import datetime
from pathlib import Path
import time

app = Flask(__name__)
CORS(app)  # Enable CORS for GUI access

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
OUT_DIR = PROJECT_ROOT / "out"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

def generate_timestamp():
    """Generate timestamp in format YYYYMMDDTHHMMSSZ"""
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")

def update_runs_manifest(timestamp, status="running", progress=None, duration=None):
    """Update the runs manifest file"""
    manifest_path = OUT_DIR / "runs_manifest.json"
    
    # Load existing manifest
    if manifest_path.exists():
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
    else:
        manifest = {"runs": [], "latest": None}
    
    # Find existing run or create new one
    run_entry = None
    for run in manifest["runs"]:
        if run["timestamp"] == timestamp:
            run_entry = run
            break
    
    if not run_entry:
        run_entry = {
            "timestamp": timestamp,
            "label": datetime.strptime(timestamp, "%Y%m%dT%H%M%SZ").strftime("%b %d, %Y %I:%M %p"),
            "status": status,
            "entity": "ALL",
            "period": "2025-08",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "duration_seconds": 0,
            "artifacts_count": 0
        }
        manifest["runs"].append(run_entry)
    else:
        run_entry["status"] = status
    
    # Update progress if provided
    if progress:
        run_entry["progress"] = progress
    elif status != "running":
        # Remove progress when not running
        run_entry.pop("progress", None)
    
    # Update duration if provided
    if duration is not None:
        run_entry["duration_seconds"] = duration
    
    # Update latest if completed
    if status == "completed":
        manifest["latest"] = timestamp
        # Count artifacts
        run_dir = OUT_DIR / f"run_{timestamp}"
        if run_dir.exists():
            artifacts = list(run_dir.glob("*.json")) + list(run_dir.glob("*.jsonl"))
            run_entry["artifacts_count"] = len(artifacts)
    
    # Sort runs by timestamp (newest first)
    manifest["runs"].sort(key=lambda x: x["timestamp"], reverse=True)
    
    # Save manifest
    with open(manifest_path, 'w') as f:
        json.dump(manifest, f, indent=2)

def run_close_process(timestamp):
    """Run the close process in background with real script execution"""
    start_time = datetime.utcnow()
    
    try:
        print(f"Starting close process for timestamp: {timestamp}")
        
        # Create run directory
        run_dir = OUT_DIR / f"run_{timestamp}"
        run_dir.mkdir(exist_ok=True)
        
        # Set environment variable for timestamp
        env = os.environ.copy()
        env['R2R_TIMESTAMP'] = timestamp
        
        # Update with initial progress
        update_runs_manifest(timestamp, "running", {
            "current_step": "Initializing close process",
            "completed_steps": 0,
            "total_steps": 8,
            "percentage": 0
        })
        
        # Run the actual close script using .venv python (streaming stdout for progress)
        venv_python = PROJECT_ROOT / '.venv' / 'bin' / 'python'
        proc = subprocess.Popen(
            [
                str(venv_python), 'run_close.py',
                '--out', str(run_dir),
                '--period', '2025-08',
                '--entity', 'ALL'
            ],
            cwd=PROJECT_ROOT / 'scripts',
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        # Lightweight heartbeat to keep UI responsive if no explicit progress is printed
        stop_heartbeat = threading.Event()
        hb_state = {
            'percentage': 0,
            'completed_steps': 0,
            'total_steps': 8,
            'current_step': 'Processing close'
        }

        def _heartbeat():
            try:
                while not stop_heartbeat.is_set():
                    # Increment up to 95% to avoid claiming completion
                    next_pct = min(hb_state['percentage'] + 3, 95)
                    hb_state['percentage'] = next_pct
                    progress = {
                        'current_step': hb_state['current_step'],
                        'completed_steps': hb_state['completed_steps'],
                        'total_steps': hb_state['total_steps'],
                        'percentage': hb_state['percentage']
                    }
                    update_runs_manifest(timestamp, 'running', progress)
                    # Sleep a bit between heartbeats
                    stop_heartbeat.wait(2)
            except Exception:
                # Heartbeat must never crash the server
                pass

        hb_thread = threading.Thread(target=_heartbeat, daemon=True)
        hb_thread.start()

        # Read output lines and look for progress markers without failing if absent
        collected_output_lines = []
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                line = line.rstrip('\n')
                collected_output_lines.append(line)
                # Expected progress marker format: "PROGRESS {json}"
                if line.startswith('PROGRESS '):
                    payload = line[len('PROGRESS '):].strip()
                    try:
                        progress = json.loads(payload)
                        # defensively validate fields
                        if isinstance(progress, dict) and {
                            'current_step', 'completed_steps', 'total_steps', 'percentage'
                        }.issubset(progress.keys()):
                            # Sync heartbeat state to real progress to avoid regressions
                            hb_state['current_step'] = str(progress.get('current_step', hb_state['current_step']))
                            hb_state['completed_steps'] = int(progress.get('completed_steps', hb_state['completed_steps']))
                            hb_state['total_steps'] = int(progress.get('total_steps', hb_state['total_steps']))
                            hb_state['percentage'] = int(progress.get('percentage', hb_state['percentage']))
                            update_runs_manifest(timestamp, 'running', progress)
                    except json.JSONDecodeError:
                        # Ignore malformed progress payloads
                        pass
        finally:
            # Ensure process completion
            result_code = proc.wait(timeout=300)
            stop_heartbeat.set()
            try:
                hb_thread.join(timeout=2)
            except Exception:
                pass

        # Calculate duration
        end_time = datetime.utcnow()
        duration = int((end_time - start_time).total_seconds())
        
        if result_code == 0:
            print(f"Close process completed successfully for {timestamp}")
            try:
                print("Output:\n" + "\n".join(collected_output_lines[-200:]))  # limit log volume
            except Exception:
                pass
            update_runs_manifest(timestamp, "completed", None, duration)
        else:
            print(f"Close process failed for {timestamp}")
            try:
                print("Output:\n" + "\n".join(collected_output_lines[-200:]))
            except Exception:
                pass
            update_runs_manifest(timestamp, "failed", None, duration)
            
    except subprocess.TimeoutExpired:
        print(f"Close process timed out for {timestamp}")
        duration = int((datetime.utcnow() - start_time).total_seconds())
        update_runs_manifest(timestamp, "failed", None, duration)
    except Exception as e:
        print(f"Error running close process for {timestamp}: {str(e)}")
        duration = int((datetime.utcnow() - start_time).total_seconds())
        update_runs_manifest(timestamp, "failed", None, duration)

@app.route('/api/runs', methods=['GET'])
def get_runs():
    """Get all available runs"""
    manifest_path = OUT_DIR / "runs_manifest.json"
    
    if not manifest_path.exists():
        return jsonify({"runs": [], "latest": None})
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    return jsonify(manifest)

@app.route('/api/runs/start', methods=['POST'])
def start_run():
    """Start a new close run"""
    try:
        # Get parameters from request
        data = request.get_json() or {}
        entity = data.get('entity', 'ALL')
        period = data.get('period', '2025-08')
        
        # Generate timestamp
        timestamp = generate_timestamp()
        
        # Update manifest with running status
        update_runs_manifest(timestamp, "running")
        
        # Start close process in background
        thread = threading.Thread(target=run_close_process, args=(timestamp,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "timestamp": timestamp,
            "message": f"Close run started for {entity} - {period}"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/runs/<timestamp>/status', methods=['GET'])
def get_run_status(timestamp):
    """Get status of specific run"""
    manifest_path = OUT_DIR / "runs_manifest.json"
    
    if not manifest_path.exists():
        return jsonify({"error": "No runs found"}), 404
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    for run in manifest["runs"]:
        if run["timestamp"] == timestamp:
            return jsonify(run)
    
    return jsonify({"error": "Run not found"}), 404

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.utcnow().isoformat()})

@app.route('/api/runs/<timestamp>/artifact/<path:artifact_name>', methods=['GET'])
def get_artifact(timestamp, artifact_name):
    """Serve an artifact by canonical name, resolving timestamped filenames.
    Examples:
      - artifact_name: 'close_report.json' resolves to 'close_report_*.json'
      - artifact_name: 'ap_reconciliation.json' resolves to 'ap_reconciliation_*.json'
      - artifact_name: 'ai_cache/flux_ai_narratives.json' resolves to 'ai_cache/flux_ai_narratives_*.json'
    """
    run_dir = OUT_DIR / timestamp
    if not run_dir.exists():
        return jsonify({"error": "Run not found"}), 404

    # Allow nested paths and search recursively
    requested_path = Path(artifact_name)
    base = requested_path.name
    if '.' not in base:
        return jsonify({"error": "Artifact must include extension"}), 400
    stem, ext = base.rsplit('.', 1)

    # Search recursively for the file, preferring exact match then timestamped variant
    # Pattern matches files like 'ap_reconciliation.json' or 'ap_reconciliation_..._....json'
    pattern = f"**/{stem}*.{ext}"
    candidates = list(run_dir.rglob(pattern))

    if not candidates:
        return jsonify({"error": f"Artifact '{artifact_name}' not found with pattern '{pattern}'"}), 404

    # Sort by modification time to get the latest one
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    chosen = candidates[0]

    return send_from_directory(chosen.parent, chosen.name)

    return jsonify({"error": "Artifact not found"}), 404

@app.route('/out/<path:filename>', methods=['GET'])
def serve_out_artifact(filename):
    """Serve artifact files from the OUT directory."""
    # send_from_directory safely serves files under OUT_DIR
    return send_from_directory(OUT_DIR, filename)

if __name__ == '__main__':
    # Ensure out directory exists
    OUT_DIR.mkdir(exist_ok=True)
    
    print("Starting R2R Financial Close API server...")
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Output directory: {OUT_DIR}")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
