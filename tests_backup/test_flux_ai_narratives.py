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


def test_flux_ai_narratives_present_and_cited():
    _ensure_run()
    artifacts = sorted(OUT.glob("flux_analysis_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert artifacts, "No flux_analysis_*.json found in out/"
    path = artifacts[0]
    data = json.loads(path.read_text())

    rows = data.get("rows", [])
    assert rows, "flux rows should not be empty for narrative validation"

    # Validate each row has ai_narrative and ai_basis consistent with the larger abs variance
    for r in rows:
        basis = r.get("ai_basis")
        assert basis in ("budget", "prior"), "ai_basis must be 'budget' or 'prior'"
        var_b = float(r.get("var_vs_budget", 0.0))
        var_p = float(r.get("var_vs_prior", 0.0))
        chosen = var_b if basis == "budget" else var_p
        assert abs(chosen) >= min(abs(var_b), abs(var_p)), "ai_basis should select the larger abs variance"
        narr = r.get("ai_narrative")
        assert isinstance(narr, str) and narr.startswith("[AI]"), "ai_narrative must be [AI]-labeled string"
        # Ensure citations include entity/account and period phrase
        assert str(r.get("entity")) in narr and str(r.get("account")) in narr, "narrative should cite entity/account"
        assert "period=" in narr, "narrative should cite period"

    # Summary ai_highlights
    highlights = data.get("summary", {}).get("ai_highlights", {})
    assert set(highlights.keys()) == {"top_variances", "count_above_budget", "count_above_prior"}
    top = highlights.get("top_variances", [])
    for t in top:
        assert set(t.keys()) == {"entity", "account", "basis", "variance_usd", "variance_abs"}
