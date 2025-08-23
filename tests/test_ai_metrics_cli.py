import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PY = str(REPO_ROOT / ".venv/bin/python")


def test_run_produces_ai_metrics_and_cli_outputs():
    # 1) Run the full close to generate outputs and audit log
    run = subprocess.run([PY, str(REPO_ROOT / "scripts/run_close.py")], capture_output=True, text=True)
    assert run.returncode == 0, f"run_close failed: {run.stderr}\n{run.stdout}"

    # 2) Find latest audit log in out/
    out_dir = REPO_ROOT / "out"
    audits = sorted(out_dir.glob("audit_*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    assert audits, "No audit_*.jsonl found in out/ after running close"
    audit_path = audits[0]

    # 3) Read audit and verify ai_output + ai_metrics pairs exist
    kinds_seen = set()
    metrics_by_kind = {}
    with audit_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if rec.get("type") == "ai_output":
                kinds_seen.add(rec.get("kind"))
            elif rec.get("type") == "ai_metrics":
                metrics_by_kind[rec.get("kind")] = (rec.get("tokens"), rec.get("cost_usd"))

    assert kinds_seen, "No ai_output records found in audit log"
    missing_metrics = [k for k in kinds_seen if k not in metrics_by_kind]
    assert not missing_metrics, f"Missing ai_metrics for kinds: {missing_metrics}"

    # 4) CLI: text output
    cli_txt = subprocess.run([PY, str(REPO_ROOT / "scripts/drill_through.py"), "list-ai"], capture_output=True, text=True)
    assert cli_txt.returncode == 0, f"list-ai text failed: {cli_txt.stderr}\n{cli_txt.stdout}"
    out_text = cli_txt.stdout
    # Expect at least one line like: [AI] kind=report ... tokens=...
    assert "[DET] AI artifacts for run:" in out_text
    assert "kind=" in out_text and "tokens=" in out_text and "cost_usd=" in out_text

    # 5) CLI: JSON output
    cli_json = subprocess.run([PY, str(REPO_ROOT / "scripts/drill_through.py"), "list-ai", "--json"], capture_output=True, text=True)
    assert cli_json.returncode == 0, f"list-ai --json failed: {cli_json.stderr}\n{cli_json.stdout}"
    data = json.loads(cli_json.stdout)
    assert isinstance(data, list) and len(data) > 0, "list-ai --json did not return a non-empty list"
    # Check enriched fields present for at least one entry
    sample = data[0]
    k = sample.get("kind")
    assert k, "Missing kind in list-ai --json entry"
    assert f"ai_{k}_tokens" in sample and f"ai_{k}_cost_usd" in sample, "Enriched ai_* metrics missing in JSON output"
