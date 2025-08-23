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


def test_ic_candidates_and_det_summary():
    _ensure_run()
    artifacts = sorted(OUT.glob("intercompany_reconciliation_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert artifacts, "No intercompany_reconciliation_*.json found in out/"
    data = json.loads(artifacts[0].read_text())

    excs = data.get("exceptions", [])
    if not excs:
        return

    for e in excs:
        cands = e.get("candidates", [])
        assert isinstance(cands, list)
        assert len(cands) <= 3
        for c in cands:
            assert {"doc_id", "entity_src", "entity_dst", "diff_abs", "det_score"}.issubset(c.keys())
            assert 0.0 <= float(c["det_score"]) <= 1.0
        summary = e.get("det_candidate_summary", "")
        if cands:
            assert isinstance(summary, str) and summary.startswith("[DET]")
            assert str(e.get("doc_id")) in summary
            assert e.get("assistive_hint") is True
