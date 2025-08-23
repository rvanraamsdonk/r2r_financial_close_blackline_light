import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PY = str(REPO_ROOT / ".venv/bin/python")
OUT = REPO_ROOT / "out"


def _ensure_run():
    files = list(OUT.glob("flux_analysis_*.json"))
    if not files:
        run = subprocess.run([PY, str(REPO_ROOT / "scripts/run_close.py")], capture_output=True, text=True)
        assert run.returncode == 0, f"run_close failed: {run.stderr}\n{run.stdout}"


def test_flux_band_counts_match_rows():
    _ensure_run()
    artifacts = sorted(OUT.glob("flux_analysis_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert artifacts, "No flux_analysis_*.json found in out/"
    path = artifacts[0]
    data = json.loads(path.read_text())

    rows = data.get("rows", [])
    band_counts = {"budget": {"within": 0, "above": 0}, "prior": {"within": 0, "above": 0}}
    for r in rows:
        band_counts["budget"][str(r.get("band_vs_budget"))] += 1
        band_counts["prior"][str(r.get("band_vs_prior"))] += 1

    summary_counts = data.get("summary", {}).get("band_counts", {})
    assert summary_counts == band_counts
