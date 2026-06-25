"""Local checkout import bootstrap for repository tools.

This module lets tools run directly from a source checkout without requiring
contributors to remember PYTHONPATH=src first. It only changes this process's
module search path and performs no network, public, credential, or filesystem
mutation outside sys.path.
"""
from __future__ import annotations

import sys
from pathlib import Path


def ensure_src_on_path() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    src_dir = repo_root / "src"
    if not src_dir.is_dir():
        return
    src_path = str(src_dir)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)


ensure_src_on_path()
