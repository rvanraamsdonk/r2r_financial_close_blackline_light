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


def test_accruals_proposals_have_ai_narratives():
    _ensure_run()
    artifacts = sorted(OUT.glob("accruals_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert artifacts, "No accruals_*.json found in out/"
    data = json.loads(artifacts[0].read_text())

    proposals = data.get("proposals", [])
    # It's okay if no proposals exist; skip in that case
    if not proposals:
        return

    for p in proposals:
        assert isinstance(p.get("ai_narrative"), str) and p["ai_narrative"].startswith("[DET]"), "proposal.ai_narrative must be [DET]-labeled"
        # minimal citation presence
        assert str(p.get("entity")) in p["ai_narrative"]
        assert str(p.get("accrual_id")) in p["ai_narrative"]
        assert str(p.get("proposed_period")) in p["ai_narrative"]
