from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Iterator, Optional

# Module-level override to enable deterministic time in tests/demos
_OVERRIDE_UTC_NOW: Optional[datetime] = None


def now_utc() -> datetime:
    """Return a timezone-aware UTC datetime.

    If an override is set (via freeze_time/set_time_override), return that value.
    """
    if _OVERRIDE_UTC_NOW is not None:
        return _OVERRIDE_UTC_NOW
    return datetime.now(timezone.utc)


def now_iso_z() -> str:
    """UTC ISO8601 with trailing 'Z', second precision: YYYY-MM-DDTHH:MM:SSZ"""
    return now_utc().strftime("%Y-%m-%dT%H:%M:%SZ")


def run_id() -> str:
    """Deterministic run_id format: YYYYMMDDTHHMMSSZ (UTC)"""
    return now_utc().strftime("%Y%m%dT%H%M%SZ")


def set_time_override(dt_utc: Optional[datetime]) -> None:
    """Set or clear the override for UTC now.

    dt_utc must be timezone-aware UTC when provided.
    """
    global _OVERRIDE_UTC_NOW
    _OVERRIDE_UTC_NOW = dt_utc


@contextmanager
def freeze_time(dt_utc: datetime) -> Iterator[None]:
    """Context manager to freeze time to a specific UTC datetime.

    Example:
        from datetime import datetime, timezone
        with freeze_time(datetime(2025, 8, 23, 11, 4, 25, tzinfo=timezone.utc)):
            ...
    """
    if dt_utc.tzinfo != timezone.utc:
        raise ValueError("freeze_time expects a UTC-aware datetime")
    prev = _OVERRIDE_UTC_NOW
    try:
        set_time_override(dt_utc)
        yield
    finally:
        set_time_override(prev)
