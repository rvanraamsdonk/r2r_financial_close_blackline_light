from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import json

import pandas as pd
from rich.console import Console

from .config import load_settings_with_env
from .state import R2RState
from .data import load_entities, load_coa, load_tb, load_fx
from .audit import AuditLogger
from .graph import build_graph
from .metrics import export_metrics
from .utils import run_id as gen_run_id


console = Console()


def _code_hash(repo_root: Path) -> str:
    # Simple hash of py files under src
    h = hashlib.sha256()
    for p in sorted((repo_root / "src").rglob("*.py")):
        try:
            h.update(p.read_bytes())
        except Exception:
            continue
    return h.hexdigest()[:12]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R2R Close with Visible AI")
    parser.add_argument("--period", default=None)
    parser.add_argument("--prior", default=None)
    parser.add_argument("--entity", default=None)
    parser.add_argument("--ai-mode", dest="ai_mode", default=None, choices=["off", "assist", "strict"])
    parser.add_argument("--data", dest="data_path", default=None)
    parser.add_argument("--out", dest="out_path", default=None)
    parser.add_argument("--show-prompts", action="store_true")
    parser.add_argument("--save-evidence", action="store_true")
    args = parser.parse_args(argv)

    # Load settings with .env from repo root
    overrides = {k: v for k, v in vars(args).items() if v not in (None, False)}
    settings = load_settings_with_env(**overrides)

    # Prepare run
    run_id = gen_run_id()
    run_dir = Path(settings.out_path) / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    audit = AuditLogger(run_dir, run_id)

    # Load datasets
    entities_df = load_entities(settings.data_path)
    coa_df = load_coa(settings.data_path)
    tb_df = load_tb(settings.data_path, settings.period, settings.entity)
    fx_df = load_fx(settings.data_path, settings.period)

    state = R2RState(
        period=settings.period,
        prior=settings.prior,
        entity=settings.entity,
        repo_root=settings.repo_root,
        data_path=settings.data_path,
        out_path=str(run_dir),
        entities_df=entities_df,
        coa_df=coa_df,
        tb_df=tb_df,
        fx_df=fx_df,
        ai_mode=settings.ai_mode,
        show_prompts=settings.show_prompts,
        save_evidence=settings.save_evidence,
    )

    # Code hash & policy header
    ch = _code_hash(settings.repo_root)
    policy_header = (
        f"Policy: ai_mode={settings.ai_mode} show_prompts={settings.show_prompts} save_evidence={settings.save_evidence}\n"
        f"Paths: data={settings.data_path} out={settings.out_path}\n"
        f"Hashes: code={ch}\n"
    )
    state.messages.append(f"[DET] {policy_header.strip()}")

    # Build & run graph
    graph = build_graph().compile()
    # Increase recursion limit to accommodate the full number of nodes including AI steps
    res = graph.invoke({"obj": state, "audit": audit}, config={"recursion_limit": 60})
    state = res["obj"]

    # Export metrics
    export_metrics(state)

    # Print labeled output
    console.print("\n[bold]Close Output[/bold]")
    for line in state.messages:
        console.print(line)

    # TB diagnostics summary (read from artifact)
    try:
        tb_diag_path = run_dir / f"tb_diagnostics_{run_id}.json"
        if tb_diag_path.exists():
            data = json.loads(tb_diag_path.read_text())
            diags = data.get("diagnostics", [])
            if diags:
                console.print("\n[bold]TB Diagnostics Summary[/bold]")
                for d in diags:
                    ent = d.get("entity")
                    imb = d.get("imbalance_usd")
                    tops = d.get("top_accounts", [])
                    # Ensure top-3 by absolute balance
                    tops = sorted(
                        tops,
                        key=lambda x: abs(float(x.get("balance_usd", 0.0))),
                        reverse=True,
                    )[:3]
                    tops_str = ", ".join(
                        f"{t.get('account')}: {float(t.get('balance_usd', 0.0)):.2f}"
                        for t in tops
                    )
                    console.print(
                        f"[DET] Entity {ent} imbalance={float(imb):.2f} USD | Top3: {tops_str}"
                    )
    except Exception as e:
        # Keep CLI robust; don't fail the run if summary can't be produced
        console.print(f"[DET] TB diagnostics summary unavailable: {e}")

    console.print("\n[bold]Metrics[/bold]")
    for k, v in state.metrics.items():
        console.print(f"[DET] {k} = {v}")

    console.print(f"\n[bold]Audit Log[/bold] -> {audit.log_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
