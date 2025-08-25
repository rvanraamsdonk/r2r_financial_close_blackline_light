from __future__ import annotations

from typing import Dict, Any
from hashlib import sha256

import pandas as pd

from ..schemas import OutputTag, MethodType, DeterministicRun, EvidenceRef
from ..audit.log import AuditLogger
from ..state import R2RState


def _hash_df(df: pd.DataFrame) -> str:
    # Simple stable hash of dataframe values
    data_bytes = pd.util.hash_pandas_object(df.fillna(""), index=True).values.tobytes()
    return sha256(data_bytes).hexdigest()


def validate_ingestion(state: R2RState, audit: AuditLogger) -> R2RState:
    """Deterministic validation: schema basics, referential integrity, duplicates, period consistency."""
    msgs = []
    det = DeterministicRun(function_name="validate_ingestion")

    # Basic presence
    assert state.entities_df is not None, "entities_df missing"
    assert state.coa_df is not None, "coa_df missing"
    assert state.tb_df is not None, "tb_df missing"

    tb = state.tb_df
    coa = state.coa_df
    ents = state.entities_df

    # Referential integrity: accounts exist
    # Convert to strings and filter out NaN values
    tb_accounts = set(str(x) for x in tb["account"].dropna().unique() if pd.notna(x))
    coa_accounts = set(str(x) for x in coa["account"].dropna().unique() if pd.notna(x))
    missing_accts = tb_accounts - coa_accounts
    if missing_accts:
        msgs.append(f"[DET] Missing accounts in COA: {sorted(list(missing_accts))[:5]} ...")
    else:
        msgs.append("[DET] COA coverage OK: all TB accounts present")

    # Referential integrity: entities exist
    tb_entities = set(str(x) for x in tb["entity"].dropna().unique() if pd.notna(x))
    ents_entities = set(str(x) for x in ents["entity"].dropna().unique() if pd.notna(x))
    missing_ents = tb_entities - ents_entities
    if missing_ents:
        msgs.append(f"[DET] Missing entities in master: {sorted(list(missing_ents))}")
    else:
        msgs.append("[DET] Entity coverage OK: all TB entities present")

    # Period consistency
    bad_period = tb[tb["period"] != state.period]
    if not bad_period.empty:
        msgs.append(f"[DET] TB rows with wrong period: {len(bad_period)}")
    else:
        msgs.append(f"[DET] TB period OK: {state.period}")

    # Duplicate keys
    dups = (
        tb.groupby(["period", "entity", "account"]).size().reset_index(name="n").query("n > 1")
    )
    if not dups.empty:
        msgs.append(f"[DET] Duplicates in TB by (period,entity,account): {len(dups)}")
    else:
        msgs.append("[DET] No duplicate TB keys detected")

    # Evidence and logging
    ev = EvidenceRef(type="csv", uri=str(state.data_path / f"trial_balance_{state.period}.csv"))
    state.evidence.append(ev)
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
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Ingestion validations"))
    return state
