from __future__ import annotations

from pathlib import Path
from typing import Dict, Any
import json

from ..state import R2RState


def compute_metrics(state: R2RState) -> R2RState:
    m: Dict[str, Any] = {}

    # FX coverage metric
    if state.fx_df is not None and state.entities_df is not None:
        needed = set(state.entities_df["home_currency"].unique().tolist())
        present = set(state.fx_df["currency"].unique().tolist())
        m["fx_coverage_ok"] = needed.issubset(present)
        m["fx_needed"] = sorted(list(needed))
        m["fx_present"] = sorted(list(present))

    # TB balanced per entity (USD)
    if state.tb_df is not None:
        by_ent = state.tb_df.groupby("entity")["balance_usd"].sum().round(2)
        m["tb_balanced_by_entity"] = all(abs(v) < 1e-9 for v in by_ent.to_dict().values())
        m["tb_entity_sums_usd"] = {k: float(v) for k, v in by_ent.to_dict().items()}

    state.metrics.update(m)
    return state


def export_metrics(state: R2RState) -> None:
    out_dir = Path(state.out_path)
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "metrics.json").open("w", encoding="utf-8") as f:
        json.dump(state.metrics, f, indent=2)
