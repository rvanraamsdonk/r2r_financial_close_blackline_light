#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

# Ensure src/ is on sys.path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from r2r.app import main  # noqa: E402
from r2r.console_v6 import render_printable  # noqa: E402


def _pop_flag(argv: list[str], flag: str) -> tuple[list[str], bool]:
    present = False
    new_argv: list[str] = []
    for a in argv:
        if a == flag:
            present = True
            continue
        new_argv.append(a)
    return new_argv, present


def _strip_deprecated_flags(argv: list[str]) -> list[str]:
    """Remove deprecated flags that app.py no longer supports.

    Handles forms:
      --ai assist
      --ai=assist
      --show-prompts
    """
    out: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a.startswith("--ai"):
            # Skip this token, and also skip the next token if it's the value and not another flag
            if "=" not in a and i + 1 < len(argv) and not argv[i + 1].startswith("-"):
                i += 2
            else:
                i += 1
            continue
        if a == "--show-prompts":
            i += 1
            continue
        out.append(a)
        i += 1
    return out


if __name__ == "__main__":
    # Allow --print-v6 here; strip before delegating to r2r.app.main
    argv = sys.argv[1:]
    argv, do_print_v6 = _pop_flag(argv, "--print-v6")
    # Backward compatibility: ignore deprecated flags
    argv = _strip_deprecated_flags(argv)

    exit_code = main(argv)

    if do_print_v6:
        # Render printable v6 view from latest artifacts under out/
        out_dir = ROOT / "out"
        render_printable(out_dir)

    raise SystemExit(exit_code)
