from .strings import safe_str
from .time import now_utc, now_iso_z, run_id, freeze_time, set_time_override
from ..data.static_loader import load_entities, load_coa, load_tb, load_fx

def compute_code_hash(repo_root):
    """Simple code hash for reproducibility."""
    import hashlib
    from pathlib import Path
    h = hashlib.sha256()
    for p in sorted((Path(repo_root) / "src").rglob("*.py")):
        try:
            h.update(p.read_bytes())
        except Exception:
            continue
    return h.hexdigest()[:12]

__all__ = [
    "safe_str",
    "now_utc",
    "now_iso_z",
    "run_id",
    "freeze_time",
    "set_time_override",
    "load_entities",
    "load_coa", 
    "load_tb",
    "load_fx",
    "compute_code_hash",
]