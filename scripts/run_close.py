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


if __name__ == "__main__":
    # Allow --print-v6 here; strip before delegating to r2r.app.main
    argv = sys.argv[1:]
    argv, do_print_v6 = _pop_flag(argv, "--print-v6")

    exit_code = main(argv)

    if do_print_v6:
        # Render printable v6 view from latest artifacts under out/
        out_dir = ROOT / "out"
        render_printable(out_dir)

    raise SystemExit(exit_code)
