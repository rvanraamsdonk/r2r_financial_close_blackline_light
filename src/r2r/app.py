from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from .audit import AuditLogger
from .config import load_settings_with_env
from .simple_console import SimpleConsole
from .ai_synthesis import AICloseSynthesis
from .graph import build_graph
from .state import R2RState
from .utils import load_entities, load_coa, load_tb, load_fx, compute_code_hash
from .metrics import export_metrics
from .utils import run_id as gen_run_id


def _code_hash(repo_root: Path) -> str:
    # Use the existing compute_code_hash function
    return compute_code_hash(repo_root)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="R2R Close with Professional Console Output")
    parser.add_argument("--period", default=None)
    parser.add_argument("--prior", default=None)
    parser.add_argument("--entity", default=None)
    # AI is always enabled - no switches needed
    parser.add_argument("--data", dest="data_path", default=None)
    parser.add_argument("--out", dest="out_path", default=None)
    # Removed --show-prompts - not needed with post-run AI
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
        chart_of_accounts_df=coa_df,
        tb_df=tb_df,
        fx_df=fx_df,
        ai_mode="assist",
        save_evidence=settings.save_evidence,
        run_id=run_id,
    )

    # Initialize simple console
    console = SimpleConsole(
        period=settings.period,
        entity=settings.entity,
        ai_mode="assist",
        run_id=run_id
    )
    console.header()

    # Attach console to state for engines to use
    state.console = console

    # Start execution
    start_time = time.time()
    
    try:
        # Build and run the graph
        graph = build_graph().compile()
        res = graph.invoke({"obj": state, "audit": audit}, config={"recursion_limit": 60})
        
        # Extract final state
        final_state = res["obj"]
        
        execution_time = time.time() - start_time
        console.footer(Path(audit.out_dir), Path(audit.log_path))
        
        # Generate comprehensive AI analysis
        print("\n" + "=" * 80)
        print("  GENERATING AI CLOSE ANALYSIS...")
        print("=" * 80)
        
        ai_synthesis = AICloseSynthesis(
            output_dir=Path(audit.out_dir),
            period=settings.period,
            entity=settings.entity
        )
        
        analysis_file = ai_synthesis.save_analysis()
        executive_summary = ai_synthesis.generate_executive_summary()
        
        print(executive_summary)
        print(f"\nDetailed analysis saved: {analysis_file.name}")
        
        return 0
        
    except Exception as e:
        execution_time = time.time() - start_time
        console.footer(Path(audit.out_dir), Path(audit.log_path))
        raise


if __name__ == "__main__":
    raise SystemExit(main())
