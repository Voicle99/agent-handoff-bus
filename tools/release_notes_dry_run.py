#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "agent-handoff-bus/release-notes-dry-run/v1"

CATEGORIES = (
    "Features",
    "Fixes",
    "Documentation",
    "Tests",
    "Tooling and maintenance",
    "Other changes",
)


def _category(subject: str) -> str:
    lowered = subject.lower().strip()
    if lowered.startswith(("feat:", "feature:")):
        return "Features"
    if lowered.startswith(("fix:", "bug:")):
        return "Fixes"
    if lowered.startswith(("docs:", "doc:", "readme", "documentation")) or lowered.startswith("docs"):
        return "Documentation"
    if lowered.startswith(("test:", "tests:", "testing:")) or lowered.startswith("test"):
        return "Tests"
    if lowered.startswith(("tools:", "tool:", "ci:", "chore:", "examples:", "build:")):
        return "Tooling and maintenance"
    return "Other changes"


def _run_git(root: Path, args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=20,
        check=False,
    )


def _commit_range(args: argparse.Namespace) -> tuple[list[str], str]:
    head = args.head_ref
    if args.base_ref:
        return [f"{args.base_ref}..{head}"], f"{args.base_ref}..{head}"
    return ["--max-count", str(args.limit), head], f"last {args.limit} commits ending at {head}"


def _collect_commits(root: Path, args: argparse.Namespace) -> tuple[int, list[dict[str, str]], str]:
    range_args, range_label = _commit_range(args)
    result = _run_git(root, ["log", "--format=%H%x00%h%x00%s", *range_args])
    if result.returncode != 0:
        return result.returncode, [], result.stderr.strip() or "git log failed"
    commits: list[dict[str, str]] = []
    for line in result.stdout.splitlines():
        parts = line.split("\x00", 2)
        if len(parts) != 3:
            continue
        full_hash, short_hash, subject = parts
        commits.append(
            {
                "hash": full_hash,
                "short_hash": short_hash,
                "subject": subject,
                "category": _category(subject),
            }
        )
    return 0, commits, range_label


def _render_markdown(commits: list[dict[str, str]], range_label: str) -> str:
    lines = [
        "# Draft release notes",
        "",
        f"Range: {range_label}",
        "Status: local draft only; review before any public release.",
        "Public action: not taken.",
        "",
    ]
    grouped: dict[str, list[dict[str, str]]] = {category: [] for category in CATEGORIES}
    for commit in commits:
        grouped.setdefault(commit["category"], []).append(commit)
    for category in CATEGORIES:
        entries = grouped.get(category, [])
        if not entries:
            continue
        lines.append(f"## {category}")
        lines.append("")
        for commit in entries:
            lines.append(f"- {commit['subject']} (`{commit['short_hash']}`)")
        lines.append("")
    lines.extend(
        [
            "## Validation before public release",
            "",
            "- Run `PYTHONPATH=src python3 tools/maintainer_check.py`.",
            "- Run the project test suite and review CI.",
            "- Keep release, tag, package upload, OAuth, paid API, and credential actions human-approved.",
            "",
        ]
    )
    return "\n".join(lines)


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
    if args.limit < 1 or args.limit > 100:
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": "limit must be between 1 and 100",
            "root": str(root),
            "public_action_taken": False,
        }

    exit_code, commits, range_label_or_error = _collect_commits(root, args)
    if exit_code != 0:
        return 1, {
            "status": "FAIL_RELEASE_NOTES_DRY_RUN",
            "schema": SCHEMA,
            "summary": "could not read local git commit summaries",
            "root": str(root),
            "git_error": range_label_or_error,
            "public_action_taken": False,
            "next_action": "Run from a git checkout or pass --root pointing at one.",
        }
    if not commits:
        return 1, {
            "status": "FAIL_RELEASE_NOTES_DRY_RUN",
            "schema": SCHEMA,
            "summary": "no commits found for the requested range",
            "root": str(root),
            "range": range_label_or_error,
            "public_action_taken": False,
            "next_action": "Use a different --base-ref, --head-ref, or --limit.",
        }

    markdown = _render_markdown(commits, range_label_or_error)
    output_path: str | None = None
    if args.output:
        output = Path(args.output).expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(markdown, encoding="utf-8")
        output_path = str(output)

    return 0, {
        "status": "PASS",
        "schema": SCHEMA,
        "summary": "local release-notes draft generated from git commit summaries",
        "root": str(root),
        "range": range_label_or_error,
        "commit_count": len(commits),
        "commits": commits,
        "markdown": markdown,
        "output_path": output_path,
        "public_action_taken": False,
        "next_action": "Review the draft before any separate release, tag, package upload, or public post.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate local-only draft release notes from git commit summaries.")
    parser.add_argument("--root", default=".", help="Repository root to read git commits from.")
    parser.add_argument("--base-ref", help="Optional base ref. When set, uses base..head range.")
    parser.add_argument("--head-ref", default="HEAD", help="Head ref for release note range.")
    parser.add_argument("--limit", type=int, default=20, help="Max commits when --base-ref is not set. 1-100.")
    parser.add_argument("--output", help="Optional local markdown output path. No public action is performed.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, payload = run(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
