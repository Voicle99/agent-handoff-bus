#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "agent-handoff-bus/worktree-health-check/v1"

REQUIRED_PATHS = (
    "README.md",
    "pyproject.toml",
    "src/agent_handoff_bus/core.py",
    "tests/test_core.py",
    "tools/maintainer_check.py",
    "docs/MAINTENANCE_LOG.md",
    ".github/workflows/ci.yml",
)


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _parse_porcelain_path(line: str) -> str:
    if line.startswith("?? "):
        return line[3:]
    if len(line) >= 4 and line[2] == " ":
        return line[3:]
    if len(line) >= 3 and line[1] == " ":
        return line[2:]
    return line.strip()


def _git_stdout(root: Path, args: list[str]) -> tuple[str | None, str | None]:
    result = _run_git(root, args)
    if result.returncode != 0:
        return None, result.stderr.strip() or result.stdout.strip() or "git command failed"
    return result.stdout.strip(), None


def check_worktree(root: Path, require_clean: bool = False, expected_origin_contains: str | None = None) -> tuple[int, dict[str, Any]]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": "repository root not found",
            "root": str(root),
            "public_action_taken": False,
        }

    findings: list[dict[str, Any]] = []
    top_level_text, top_level_error = _git_stdout(root, ["rev-parse", "--show-toplevel"])
    if top_level_error:
        findings.append({"kind": "invalid_git_worktree", "detail": top_level_error})
        return 1, {
            "status": "FAIL_WORKTREE_HEALTH",
            "schema": SCHEMA,
            "summary": "root is not a valid git worktree",
            "root": str(root),
            "findings": findings,
            "public_action_taken": False,
            "next_action": "Use a complete git checkout before running maintainer workflows.",
        }

    top_level = Path(top_level_text or "").resolve()
    if top_level != root:
        findings.append({"kind": "root_not_git_toplevel", "expected": str(top_level), "actual": str(root)})

    for rel in REQUIRED_PATHS:
        path = root / rel
        if not path.is_file():
            findings.append({"kind": "missing_required_file", "path": rel})

    head, head_error = _git_stdout(root, ["rev-parse", "HEAD"])
    branch, _ = _git_stdout(root, ["rev-parse", "--abbrev-ref", "HEAD"])
    origin_url, origin_error = _git_stdout(root, ["remote", "get-url", "origin"])
    if origin_error:
        findings.append({"kind": "missing_origin_remote", "detail": origin_error})
    elif expected_origin_contains and expected_origin_contains not in (origin_url or ""):
        findings.append(
            {
                "kind": "unexpected_origin_remote",
                "expected_contains": expected_origin_contains,
                "origin_url": origin_url,
            }
        )

    status_text, status_error = _git_stdout(root, ["status", "--porcelain=v1"])
    dirty_paths: list[str] = []
    if status_error:
        findings.append({"kind": "git_status_failed", "detail": status_error})
    else:
        dirty_paths = [_parse_porcelain_path(line) for line in (status_text or "").splitlines() if line.strip()]
        if require_clean and dirty_paths:
            findings.append({"kind": "dirty_worktree", "dirty_count": len(dirty_paths), "sample": dirty_paths[:20]})

    base_payload: dict[str, Any] = {
        "schema": SCHEMA,
        "root": str(root),
        "git_top_level": str(top_level),
        "branch": branch,
        "head": head,
        "origin_url": origin_url,
        "required_paths": list(REQUIRED_PATHS),
        "dirty_count": len(dirty_paths),
        "dirty_paths_sample": dirty_paths[:20],
        "require_clean": require_clean,
        "public_action_taken": False,
    }

    if findings:
        return 1, {
            **base_payload,
            "status": "FAIL_WORKTREE_HEALTH",
            "summary": "worktree health check failed",
            "findings": findings,
            "next_action": "Repair or reclone the checkout, then rerun local maintainer checks.",
        }

    return 0, {
        **base_payload,
        "status": "PASS",
        "summary": "git worktree and required project files are present",
        "findings": [],
        "next_action": "Proceed with local checks; public actions still require separate approval.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-only health check for the agent-handoff-bus checkout.")
    parser.add_argument("--root", default=".", help="Repository root to check.")
    parser.add_argument("--require-clean", action="store_true", help="Fail if git status has local modifications.")
    parser.add_argument("--expected-origin-contains", help="Optional substring expected in the origin remote URL.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, payload = check_worktree(
        Path(args.root),
        require_clean=bool(args.require_clean),
        expected_origin_contains=args.expected_origin_contains,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
