import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PY = str(REPO_ROOT / ".venv/bin/python")
OUT = REPO_ROOT / "out"


def _ensure_run():
    files = list(OUT.glob("intercompany_reconciliation_*.json"))
    if not files:
        run = subprocess.run([PY, str(REPO_ROOT / "scripts/run_close.py")], capture_output=True, text=True)
        assert run.returncode == 0, f"run_close failed: {run.stderr}\n{run.stdout}"


def test_ic_proposal_simulation_and_balance():
    _ensure_run()
    artifacts = sorted(OUT.glob("intercompany_reconciliation_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert artifacts, "No intercompany_reconciliation_*.json found in out/"
    path = artifacts[0]
    data = json.loads(path.read_text())

    exc_by_doc = {e["doc_id"]: e for e in data.get("exceptions", [])}
    for p in data.get("proposals", []):
        doc_id = p.get("doc_id")
        e = exc_by_doc.get(doc_id)
        assert e, f"Missing exception for proposal doc_id={doc_id}"
        amt_dst = float(e["amount_dst"])  # from exception
        adj = float(p["adjustment_usd"])  # proposal adjustment
        simulated = float(p["simulated_dst_after"])  # proposed dst after
        assert abs(simulated - (amt_dst + adj)) < 1e-6, "simulated_dst_after must equal amount_dst + adjustment"
        # balanced_after = simulated equals amount_src
        amt_src = float(e["amount_src"])  # source
        expect_balanced = abs(simulated - amt_src) < 1e-6
        assert bool(p["balanced_after"]) == expect_balanced, "balanced_after must reflect equality with source"
