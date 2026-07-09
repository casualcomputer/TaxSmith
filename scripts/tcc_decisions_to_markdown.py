#!/usr/bin/env python3
"""Compatibility wrapper for the multi-court decision harvester."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from court_decisions_to_markdown import main  # noqa: E402


if __name__ == "__main__":
    argv = sys.argv[1:]
    has_court = any(arg == "--court" or arg.startswith("--court=") for arg in argv)
    if not has_court and "--all-courts" not in argv:
        argv = ["--court", "tcc", *argv]
    raise SystemExit(main(argv))
