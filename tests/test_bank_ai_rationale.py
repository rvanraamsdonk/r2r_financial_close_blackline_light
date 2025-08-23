import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PY = str(REPO_ROOT / ".venv/bin/python")
OUT = REPO_ROOT / "out"


def _ensure_run():
    files = list(OUT.glob("bank_reconciliation_*.json"))
    if not files:
        run = subprocess.run([PY, str(REPO_ROOT / "scripts/run_close.py")], capture_output=True, text=True)
        assert run.returncode == 0, f"run_close failed: {run.stderr}\n{run.stdout}"


def test_bank_exceptions_have_ai_narratives_and_classification():
    _ensure_run()
    artifacts = sorted(OUT.glob("bank_reconciliation_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert artifacts, "No bank_reconciliation_*.json found in out/"
    data = json.loads(artifacts[0].read_text())

    excs = data.get("exceptions", [])
    # if no exceptions in sample data, skip
    if not excs:
        return

    for e in excs:
        assert isinstance(e.get("ai_rationale"), str) and e["ai_rationale"].startswith("[DET]"), "exception.ai_rationale must be [DET]-labeled"
        assert e.get("classification") in {"error_duplicate", "timing_difference"}
        # minimal citation presence
        assert str(e.get("entity")) in e["ai_rationale"]
        assert str(e.get("bank_txn_id")) in e["ai_rationale"]
