import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PY = str(REPO_ROOT / ".venv/bin/python")
OUT = REPO_ROOT / "out"


def _ensure_run():
    files = list(OUT.glob("accruals_*.json"))
    if not files:
        run = subprocess.run([PY, str(REPO_ROOT / "scripts/run_close.py")], capture_output=True, text=True)
        assert run.returncode == 0, f"run_close failed: {run.stderr}\n{run.stdout}"


def test_accruals_rollforward_totals_and_by_entity():
    _ensure_run()
    artifacts = sorted(OUT.glob("accruals_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert artifacts, "No accruals_*.json found in out/"
    path = artifacts[0]
    data = json.loads(path.read_text())

    proposals = data.get("proposals", [])
    rf = data.get("summary", {}).get("roll_forward", {})

    # total equals sum of proposal amounts
    total_prop = round(sum(float(p.get("amount_usd", 0.0)) for p in proposals), 2)
    assert round(float(rf.get("proposed_reversals_total_usd", 0.0)), 2) == total_prop

    # by_entity equals grouped sums of proposals by entity
    by_ent_expected = {}
    for p in proposals:
        ent = str(p.get("entity"))
        by_ent_expected[ent] = round(by_ent_expected.get(ent, 0.0) + float(p.get("amount_usd", 0.0)), 2)

    by_ent_actual = {str(k): round(float(v), 2) for k, v in (rf.get("proposed_reversals_by_entity", {}) or {}).items()}
    assert by_ent_actual == by_ent_expected
