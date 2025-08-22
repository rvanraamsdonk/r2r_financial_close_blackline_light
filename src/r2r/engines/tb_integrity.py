from __future__ import annotations

from hashlib import sha256
import pandas as pd

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState


def _hash_df(df: pd.DataFrame) -> str:
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def tb_checks(state: R2RState, audit: AuditLogger) -> R2RState:
    assert state.tb_df is not None, "tb_df missing"

    tb = state.tb_df
    msgs = []

    # Debits = Credits by entity in USD
    by_ent = tb.groupby("entity")["balance_usd"].sum().round(2)
    off = by_ent[by_ent != 0.0]
    if not off.empty:
        msgs.append(f"[DET] TB not balanced by entity (USD): {off.to_dict()}")
    else:
        msgs.append("[DET] TB balanced by entity (USD)")

    # Rollups: by account type if COA present
    if state.coa_df is not None:
        merged = tb.merge(state.coa_df, on="account", how="left")
        null_types = merged[merged["account_type"].isna()]["account"].unique()
        if len(null_types) > 0:
            msgs.append(f"[DET] Accounts missing type in COA: {sorted(list(map(str, null_types)))[:5]} ...")
        # Asset - Liability - Equity - P&L relation (informational)
        sums = merged.groupby("account_type")["balance_usd"].sum().round(2).to_dict()
        msgs.append(f"[DET] Rollup by account_type (USD): {sums}")

    # Evidence & run log
    ev = EvidenceRef(type="csv", uri=str(state.data_path / f"trial_balance_{state.period}.csv"))
    state.evidence.append(ev)

    det = DeterministicRun(function_name="tb_checks")
    det.params = {"period": state.period, "entity": state.entity}
    det.output_hash = _hash_df(tb)
    state.det_runs.append(det)

    audit.append({
        "type": "deterministic",
        "fn": det.function_name,
        "evidence_id": ev.id,
        "output_hash": det.output_hash,
        "params": det.params,
    })

    state.messages.extend(msgs)
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="TB integrity checks"))
    return state
