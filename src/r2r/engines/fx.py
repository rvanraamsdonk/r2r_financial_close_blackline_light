from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pandas as pd

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def compute_fx_coverage(state: R2RState, audit: AuditLogger) -> R2RState:
    assert state.fx_df is not None, "fx_df missing"
    assert state.entities_df is not None, "entities_df missing"

    fx = state.fx_df
    ents = state.entities_df

    # Coverage: all entity currencies present for period
    needed = sorted(ents["home_currency"].unique().tolist())
    present = sorted(fx["currency"].unique().tolist())
    missing = [c for c in needed if c not in present]

    msgs = []
    if missing:
        msgs.append(f"[DET] FX coverage incomplete for period {state.period}: missing {missing}")
    else:
        msgs.append(f"[DET] FX coverage OK for {state.period}: currencies {present}")

    # Evidence & run log
    ev = EvidenceRef(type="csv", uri=str(Path(state.data_path) / "fx_rates.csv"))
    state.evidence.append(ev)

    det = DeterministicRun(function_name="compute_fx_coverage")
    det.params = {"period": state.period}
    det.output_hash = _hash_df(fx)
    state.det_runs.append(det)

    audit.append({
        "type": "deterministic",
        "fn": det.function_name,
        "evidence_id": ev.id,
        "output_hash": det.output_hash,
        "params": det.params,
    })

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="FX coverage checks"))
    return state
