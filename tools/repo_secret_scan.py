#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from typing import Any

import _bootstrap  # noqa: F401 - adds local src/ to sys.path for direct tool runs

from agent_handoff_bus.core import scan_sensitive

SCHEMA = "agent-handoff-bus/repo-secret-scan/v1"

PRIVATE_DATA_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "personal_local_path",
        re.compile(r"(?<![A-Za-z0-9_])(?:/Users|/home)/[A-Za-z0-9._-]+/[^\s`'\"<>)]*"),
    ),
    ("windows_user_path", re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+\\[^\s`'\"<>)]*")),
    ("github_fine_grained_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("private_transcript_marker", re.compile(r"(?i)BEGIN PRIVATE (CHAT )?TRANSCRIPT|PRIVATE TRANSCRIPT START")),
    ("browser_cookie_dump", re.compile(r"(?i)\b(cookie|session)_dump\b|BEGIN BROWSER COOKIES")),
)

# The repository intentionally keeps a few fake private-path fixtures in tests
# to prove the public-action and handoff-policy guards fail closed. Do not allow
# broad fixture text; only these exact dummy paths are ignored.
ALLOWED_FIXTURE_PRIVATE_PATHS = {
    "tests/test_core.py": (
        "/Users/" "alice/project/private.log",
        "/Users/" "alice/project/.venv/bin/python",
        "/Users/" "bob/private.log",
    )
}

# Some local-only config files are intentionally ignored by git because they can
# contain machine-specific connector URLs, bearer tokens, or personal paths.
# Ignoring them prevents accidental commits, but the maintainer scan should still
# fail closed if those files are present in the checkout. Keep this list narrow.
SENSITIVE_IGNORED_FILENAMES = (".mcp.json",)


def _json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)


def _git_files(root: Path, include_untracked: bool) -> list[str]:
    args = ["git", "-C", str(root), "ls-files", "--cached"]
    if include_untracked:
        args.extend(["--others", "--exclude-standard"])
    result = subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=15,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return sorted(path for path in result.stdout.splitlines() if path)



def _sensitive_ignored_files(root: Path, existing_paths: set[str]) -> list[str]:
    paths: list[str] = []
    for rel_path in SENSITIVE_IGNORED_FILENAMES:
        path = root / rel_path
        if path.is_file() and rel_path not in existing_paths:
            paths.append(rel_path)
    return paths


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _allowed_fixture_hit(rel_path: str, kind: str, line: str) -> bool:
    if kind != "personal_local_path":
        return False
    allowed_values = ALLOWED_FIXTURE_PRIVATE_PATHS.get(rel_path, ())
    return any(value in line for value in allowed_values)


def _scan_file(root: Path, rel_path: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], bool]:
    path = root / rel_path
    data = path.read_bytes()
    if b"\0" in data:
        return [], [], True
    text = data.decode("utf-8", errors="replace")

    findings: list[dict[str, Any]] = []
    allowed: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        secret_hits = sorted(scan_sensitive(line))
        for kind in secret_hits:
            findings.append({"kind": kind, "file": rel_path, "line": line_number})
        if "re.compile(" in line:
            continue
        for kind, pattern in PRIVATE_DATA_PATTERNS:
            for match in pattern.finditer(line):
                hit = {"kind": kind, "file": rel_path, "line": line_number}
                if _allowed_fixture_hit(rel_path, kind, line):
                    allowed.append(hit)
                else:
                    findings.append(hit)
    return findings, allowed, False


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": "repository root not found",
            "root": str(root),
            "public_action_taken": False,
        }

    try:
        candidate_paths = _git_files(root, include_untracked=not args.tracked_only)
        sensitive_ignored_paths: list[str] = []
        if not args.tracked_only:
            sensitive_ignored_paths = _sensitive_ignored_files(root, set(candidate_paths))
            candidate_paths = sorted([*candidate_paths, *sensitive_ignored_paths])
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": "could not list tracked/untracked candidate files",
            "root": str(root),
            "error": str(exc),
            "public_action_taken": False,
            "next_action": "Run from a git checkout or pass --root to the repository root.",
        }

    findings: list[dict[str, Any]] = []
    allowed_fixture_hits: list[dict[str, Any]] = []
    skipped_binary: list[str] = []
    scanned_files = 0
    for rel_path in candidate_paths:
        path = root / rel_path
        if not path.is_file():
            continue
        try:
            file_findings, file_allowed, binary = _scan_file(root, rel_path)
        except OSError as exc:
            findings.append({"kind": "unreadable_file", "file": rel_path, "line": None, "error": str(exc)})
            continue
        if binary:
            skipped_binary.append(rel_path)
            continue
        scanned_files += 1
        findings.extend(file_findings)
        allowed_fixture_hits.extend(file_allowed)

    base: dict[str, Any] = {
        "schema": SCHEMA,
        "root": str(root),
        "candidate_files": len(candidate_paths),
        "scanned_files": scanned_files,
        "skipped_binary_files": skipped_binary,
        "allowed_fixture_hits": allowed_fixture_hits,
        "sensitive_ignored_files": sensitive_ignored_paths,
        "public_action_taken": False,
    }
    if findings:
        return 3, {
            **base,
            "status": "BLOCKED_SECRET_OR_PRIVATE_DATA",
            "summary": "tracked, untracked, or sensitive ignored candidate files contain secret-like or private material",
            "findings": findings,
            "next_action": "Remove real secrets/private data or add a narrow fake fixture allowance with tests.",
        }
    return 0, {
        **base,
        "status": "PASS",
        "summary": "tracked, untracked, and sensitive ignored candidate files contain no high-confidence secret/private findings",
        "next_action": "Use this as one local gate; Bumblebee and human review are still separate checks.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Dependency-free local scan for repo secret/private-data candidates."
    )
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    parser.add_argument(
        "--tracked-only",
        action="store_true",
        help="Scan only tracked files instead of tracked plus untracked non-ignored candidates.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, payload = run(args)
    print(_json_dumps(payload))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
