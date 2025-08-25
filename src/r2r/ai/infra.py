from __future__ import annotations

import hashlib
import json
import time
import os
from pathlib import Path
from typing import Any, Dict, Tuple, Callable, Optional

# Prompt rendering and OpenAI client (optional until installed)
from jinja2 import Environment, FileSystemLoader, select_autoescape
try:  # OpenAI v1 SDK
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover
    OpenAI = None  # type: ignore

from ..config import load_settings_with_env


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


# -----------------------------
# OpenAI integration helpers
# -----------------------------
_template_env: Optional[Environment] = None


def _templates_dir() -> Path:
    return Path(__file__).parent / "templates"


def _get_template_env() -> Environment:
    global _template_env
    if _template_env is None:
        _template_env = Environment(
            loader=FileSystemLoader(str(_templates_dir())),
            autoescape=select_autoescape(disabled_extensions=(".md", ".txt")),
            trim_blocks=True,
            lstrip_blocks=True,
        )
    return _template_env


def render_template(name: str, context: Dict[str, Any]) -> str:
    env = _get_template_env()
    tmpl = env.get_template(name)
    return tmpl.render(**context)


def openai_enabled() -> bool:
    s = load_settings_with_env()
    return bool(s.r2r_allow_network and (s.openai_api_key))


def _make_openai_client():
    s = load_settings_with_env()
    if not s.r2r_allow_network:
        raise RuntimeError("Networking not allowed (R2R_ALLOW_NETWORK is False)")
    if s.openai_api_key:
        if OpenAI is None:
            raise RuntimeError("openai package not installed. Add 'openai' to requirements and install.")
        return OpenAI(api_key=s.openai_api_key)
    raise RuntimeError("No OpenAI credentials found (OPENAI_API_KEY)")


def call_openai_json(prompt: str, *, system: Optional[str] = None, model_env_var: str = "OPENAI_MODEL") -> Dict[str, Any]:
    """Call OpenAI chat and parse a JSON object from the response.

    Uses OPENAI_MODEL env var or defaults to 'gpt-4o-mini'.
    """
    client = _make_openai_client()
    model = os.getenv(model_env_var, "gpt-4o-mini").strip() or "gpt-4o-mini"
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    # Use responses API with JSON mode if available; fall back to chat.completions
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.2,
            response_format={"type": "json_object"},
        )
        content = resp.choices[0].message.content or "{}"
    except Exception:
        # Fallback to an empty JSON to avoid crashes if provider unavailable
        content = "{}"
    try:
        return json.loads(content)
    except Exception:
        # Try to extract JSON substring
        import re
        m = re.search(r"\{[\s\S]*\}", content)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                return {}
        return {}



def default_rate_per_1k_from_env(env_var: str = "R2R_AI_RATE_PER_1K") -> float:
    """Fetch a default $/1k token rate from environment; returns 0.01 if unset/invalid.

    Example: export R2R_AI_RATE_PER_1K=0.5
    Default: 0.01 (reasonable rate for gpt-4o-mini)
    """
    try:
        v = os.getenv(env_var, "").strip()
        if v:
            return float(v)
        # Default to reasonable rate for gpt-4o-mini if not set
        return 0.01
    except Exception:
        return 0.01
