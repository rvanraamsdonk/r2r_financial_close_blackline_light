from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Tuple, Callable


def compute_inputs_hash(data: Dict[str, Any]) -> str:
    """Stable SHA256 over canonical JSON for caching/provenance."""
    blob = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def ensure_cache_dir(out_dir: Path) -> Path:
    cache_dir = Path(out_dir) / "ai_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def with_cache(
    *,
    out_dir: Path,
    kind: str,
    run_id: str,
    inputs_hash: str,
    build_payload: Callable[[], Dict[str, Any]],
) -> Tuple[Path, Dict[str, Any], bool]:
    """Reads cached artifact if present, else builds and writes it.

    Returns: (artifact_path, payload, was_cached)
    """
    cache_dir = ensure_cache_dir(out_dir)
    artifact = cache_dir / f"{kind}_{run_id}_{inputs_hash[:12]}.json"
    if artifact.exists():
        payload = json.loads(artifact.read_text(encoding="utf-8"))
        return artifact, payload, True
    payload = build_payload()
    artifact.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return artifact, payload, False


def time_call(fn: Callable[[], Any]) -> Tuple[Any, float]:
    t0 = time.perf_counter()
    res = fn()
    dt_ms = (time.perf_counter() - t0) * 1000.0
    return res, dt_ms


def estimate_tokens(payload: Dict[str, Any]) -> int:
    """Very rough token estimate: 1 token ~= 4 bytes of JSON text.

    This avoids vendor coupling and gives a consistent relative metric.
    """
    try:
        blob = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        return max(1, int(len(blob) / 4))
    except Exception:
        return 0


def estimate_cost_usd(tokens: int, rate_per_1k: float = 0.0) -> float:
    """Compute approximate USD cost given tokens and $/1k rate. Default 0 for offline mode."""
    try:
        return round((tokens / 1000.0) * float(rate_per_1k), 6)
    except Exception:
        return 0.0
