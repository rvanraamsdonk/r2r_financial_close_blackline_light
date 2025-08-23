from __future__ import annotations

import json
from datetime import datetime
from hashlib import sha256
from pathlib import Path
from typing import Any, Dict

from ..audit.log import AuditLogger
from ..schemas import EvidenceRef, DeterministicRun, OutputTag, MethodType
from ..state import R2RState


def _hash_payload(payload: Dict[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()


def controls_mapping(state: R2RState, audit: AuditLogger) -> R2RState:
    """
    Deterministic mapping of computed metrics to internal control IDs/families.
    Produces a JSON artifact with mappings to support audit and compliance alignment.
    """
    m = state.metrics or {}
    run_id = Path(audit.log_path).stem.replace("audit_", "")
    now = datetime.utcnow().isoformat() + "Z"

    # Simple static policy mapping based on known metric keys
    mapping: Dict[str, Dict[str, Any]] = {}

    def add_map(metric_key: str, control_id: str, description: str) -> None:
        if metric_key in m:
            mapping[metric_key] = {
                "control_id": control_id,
                "description": description,
                "value": m.get(metric_key),
            }

    add_map("tb_balanced_by_entity", "TB.BAL.001", "Entity-level TB balances to 0 in USD")
    add_map("fx_coverage_ok", "FX.COV.001", "FX rates coverage meets policy")
    add_map("bank_duplicates_count", "BANK.REC.002", "Bank duplicate detection exceptions count")
    add_map("ap_exceptions_count", "AP.REC.003", "AP reconciliation exceptions count")
    add_map("ar_exceptions_count", "AR.REC.004", "AR reconciliation exceptions count")
    add_map("ic_mismatch_count", "IC.REC.005", "Intercompany mismatches count")
    add_map("accruals_exception_count", "ACCR.REV.006", "Accruals exception count (incl. reversals)")
    add_map("je_exceptions_count", "JE.APP.007", "JE approval/reversal exceptions count")
    add_map("flux_exceptions_count", "FLUX.ANAL.008", "Flux analysis exception count across accounts")
    add_map("gatekeeping_risk_level", "GATE.RISK.009", "Gatekeeping overall risk level")
    add_map("gatekeeping_block_close", "GATE.BLOCK.010", "Gatekeeping block close flag")
    add_map("hitl_cases_open_count", "HITL.CASE.011", "Open HITL cases count")

    payload = {
        "generated_at": now,
        "period": state.period,
        "entity_scope": state.entity,
        "mappings": mapping,
        "count": len(mapping),
    }

    out_path = Path(audit.out_dir) / f"controls_mapping_{run_id}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Evidence and deterministic run
    ev = EvidenceRef(type="json", uri=str(out_path))
    state.evidence.append(ev)
    audit.append({
        "type": "evidence",
        "id": ev.id,
        "evidence_type": ev.type,
        "uri": ev.uri,
        "timestamp": ev.timestamp.isoformat() + "Z",
    })

    det = DeterministicRun(function_name="controls_mapping")
    det.params = {"period": state.period, "entity": state.entity}
    det.output_hash = _hash_payload(payload)
    state.det_runs.append(det)
    audit.append({
        "type": "deterministic",
        "fn": det.function_name,
        "output_hash": det.output_hash,
        "params": det.params,
        "artifact": str(out_path),
    })

    state.messages.append(f"[DET] Controls mapping: {len(mapping)} mapped -> {out_path}")
    state.tags.append(OutputTag(method_type=MethodType.DET, rationale="Controls mapping"))

    state.metrics.update({
        "controls_mapped_count": len(mapping),
        "controls_mapping_artifact": str(out_path),
    })

    return state
