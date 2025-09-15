#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import sys

# Ensure src/ is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from r2r.engines import ap_ar_recon, accruals  # type: ignore
from r2r.engines.je_lifecycle import _safe_str as je_safe_str  # type: ignore


def assert_eq(actual, expected, msg: str = ""):
    if actual != expected:
        raise AssertionError(f"{msg} (actual={actual!r}, expected={expected!r})")


def helper_module_safe_str(mod, name: str):
    f = getattr(mod, "_safe_str")
    assert callable(f), f"_safe_str missing in {name}"
    # Core behaviors
    assert_eq(f(None), "", f"None should become empty in {name}")
    assert_eq(f(float("nan")), "", f"NaN should become empty in {name}")
    assert_eq(f("  x  "), "x", f"strip should trim in {name}")
    assert_eq(f(123), "123", f"non-strings should stringify in {name}")


def main():
    failures = 0
    for mod, nm in [
        (ap_ar_recon, "ap_ar_recon"),
        (accruals, "accruals"),
    ]:
        try:
            helper_module_safe_str(mod, nm)
            print(f"[OK] {nm}._safe_str")
        except Exception as e:
            failures += 1
            print(f"[FAIL] {nm}: {e}")

    # Test je_lifecycle helper directly
    try:
        assert callable(je_safe_str)
        assert_eq(je_safe_str(None), "", "None should become empty in je_lifecycle")
        assert_eq(je_safe_str(float("nan")), "", "NaN should become empty in je_lifecycle")
        assert_eq(je_safe_str("  x  "), "x", "strip should trim in je_lifecycle")
        assert_eq(je_safe_str(123), "123", "non-strings should stringify in je_lifecycle")
        print("[OK] je_lifecycle._safe_str")
    except Exception as e:
        failures += 1
        print(f"[FAIL] je_lifecycle: {e}")
    if failures:
        print(f"NaN-safe string tests failed: {failures} module(s)")
        raise SystemExit(1)
    print("All NaN-safe string tests passed.")


if __name__ == "__main__":
    main()
