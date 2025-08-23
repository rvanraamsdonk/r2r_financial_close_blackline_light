import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PY = str(REPO_ROOT / ".venv/bin/python")
OUT = REPO_ROOT / "out"


def _ensure_run():
    files = list(OUT.glob("ap_reconciliation_*.json")) + list(OUT.glob("ar_reconciliation_*.json"))
    if not files:
        run = subprocess.run([PY, str(REPO_ROOT / "scripts/run_close.py")], capture_output=True, text=True)
        assert run.returncode == 0, f"run_close failed: {run.stderr}\n{run.stdout}"


def _load_latest(pattern: str):
    artifacts = sorted(OUT.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    assert artifacts, f"No {pattern} found in out/"
    return json.loads(artifacts[0].read_text())


def test_ap_ai_rationale_and_candidates_schema():
    _ensure_run()
    data = _load_latest("ap_reconciliation_*.json")
    for e in data.get("exceptions", []):
        narr = e.get("ai_rationale")
        assert isinstance(narr, str) and narr.startswith("[DET] "), "AP ai_rationale must start with [DET]"
        # candidates optional
        cand = e.get("candidates")
        if cand is not None:
            assert isinstance(cand, list)
            for c in cand:
                assert {"bill_id", "vendor_name", "bill_date", "amount", "score"}.issubset(c.keys())
                assert 0.0 <= float(c["score"]) <= 1.0


def test_ar_ai_rationale_and_candidates_schema():
    _ensure_run()
    data = _load_latest("ar_reconciliation_*.json")
    for e in data.get("exceptions", []):
        narr = e.get("ai_rationale")
        assert isinstance(narr, str) and narr.startswith("[DET] "), "AR ai_rationale must start with [DET]"
        cand = e.get("candidates")
        if cand is not None:
            assert isinstance(cand, list)
            for c in cand:
                assert {"invoice_id", "customer_name", "invoice_date", "amount", "score"}.issubset(c.keys())
                assert 0.0 <= float(c["score"]) <= 1.0
