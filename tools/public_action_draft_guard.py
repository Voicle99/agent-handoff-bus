#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import _bootstrap  # noqa: F401 - adds local src/ to sys.path for direct tool runs
from typing import Any

from agent_handoff_bus.core import scan_sensitive

SCHEMA = "agent-handoff-bus/public-action-draft-guard/v1"
APPROVAL_PREFIX = "APPROVED_PUBLIC_ACTION:"

PRIVATE_DATA_PATTERNS = [
    (
        "personal_local_path",
        re.compile(r"(?<![A-Za-z0-9_])(?:/Users|/home)/[A-Za-z0-9._-]+/[^\s`'\"<>)]*"),
    ),
    ("windows_user_path", re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+\\[^\s`'\"<>)]*")),
    ("github_oauth_token", re.compile(r"gho_[A-Za-z0-9_]{20,}")),
    ("github_fine_grained_pat", re.compile(r"github_pat_[A-Za-z0-9_]{20,}")),
    ("private_transcript_marker", re.compile(r"(?i)BEGIN PRIVATE (CHAT )?TRANSCRIPT|PRIVATE TRANSCRIPT START")),
    ("browser_cookie_dump", re.compile(r"(?i)\b(cookie|session)_dump\b|BEGIN BROWSER COOKIES")),
]

APPROVAL_ACTION_WORDS = (
    "comment",
    "create issue",
    "close issue",
    "update issue",
    "push commit",
    "open pr",
    "open pull request",
    "review",
)
VAGUE_APPROVALS = {
    "approved",
    "looks good",
    "lgtm",
    "ship it",
    "handle it",
    "do it",
    "go ahead",
}


def _read_text_file(path_text: str) -> tuple[Path, str]:
    path = Path(path_text).expanduser().resolve()
    return path, path.read_text(encoding="utf-8", errors="replace")


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _scan_private_data(path: Path, text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for kind, pattern in PRIVATE_DATA_PATTERNS:
        for match in pattern.finditer(text):
            hits.append(
                {
                    "kind": kind,
                    "file": str(path),
                    "line": _line_number(text, match.start()),
                }
            )
    return hits


def _read_approval(args: argparse.Namespace) -> str:
    if args.approval_file:
        _, approval = _read_text_file(args.approval_file)
        return approval.strip()
    return (args.approval_text or "").strip()


def _approval_check(approval: str) -> dict[str, Any]:
    if not approval:
        return {
            "present": False,
            "specific": False,
            "reason": "missing exact approval text",
        }
    first_line = approval.splitlines()[0].strip()
    if not first_line.startswith(APPROVAL_PREFIX):
        return {
            "present": True,
            "specific": False,
            "reason": f"approval must start with {APPROVAL_PREFIX}",
        }
    action = first_line[len(APPROVAL_PREFIX) :].strip()
    normalized = re.sub(r"\s+", " ", action.lower()).strip(" .")
    if normalized in VAGUE_APPROVALS or len(normalized) < 12:
        return {
            "present": True,
            "specific": False,
            "reason": "approval is too vague",
        }
    if not any(word in normalized for word in APPROVAL_ACTION_WORDS):
        return {
            "present": True,
            "specific": False,
            "reason": "approval does not name a concrete public action",
        }
    return {
        "present": True,
        "specific": True,
        "reason": "exact approval text present",
        "action": action,
    }


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    if not args.draft:
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": "at least one --draft file is required",
            "public_action_taken": False,
            "next_action": "Provide one or more local draft files to inspect.",
        }

    drafts: list[dict[str, Any]] = []
    sensitive_hits: set[str] = set()
    private_hits: list[dict[str, Any]] = []
    for draft_path in args.draft:
        try:
            path, text = _read_text_file(draft_path)
        except OSError as exc:
            return 2, {
                "status": "ERROR",
                "schema": SCHEMA,
                "summary": "could not read draft file",
                "draft": draft_path,
                "error": str(exc),
                "public_action_taken": False,
                "next_action": "Check the draft path and rerun the local guard.",
            }
        drafts.append({"path": str(path), "bytes": len(text.encode("utf-8", errors="replace"))})
        sensitive_hits.update(scan_sensitive(text))
        private_hits.extend(_scan_private_data(path, text))

    if sensitive_hits or private_hits:
        return 3, {
            "status": "BLOCKED_PRIVATE_DATA",
            "schema": SCHEMA,
            "summary": "draft contains secret-like or private material",
            "drafts": drafts,
            "public_action_taken": False,
            "sensitive_scan_hits": sorted(sensitive_hits),
            "private_data_hits": private_hits,
            "next_action": "Remove real secrets/private data, replace with dummy values, then rerun.",
        }

    approval = _approval_check(_read_approval(args))
    if not approval["specific"]:
        return 4, {
            "status": "BLOCKED_PUBLIC_ACTION_REQUIRES_APPROVAL",
            "schema": SCHEMA,
            "summary": "draft is locally clean, but no exact public-action approval was provided",
            "drafts": drafts,
            "public_action_taken": False,
            "approval": approval,
            "next_action": (
                f"Provide --approval-text '{APPROVAL_PREFIX} <exact action and target>' "
                "after a human reviews the final public text."
            ),
        }

    return 0, {
        "status": "PASS_PUBLIC_ACTION_READY",
        "schema": SCHEMA,
        "summary": "draft is locally clean and exact approval text is present",
        "drafts": drafts,
        "public_action_taken": False,
        "approval": approval,
        "next_action": "This guard performed no public action; a human or separate approved command must still execute it.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Local-only guard for GitHub issue/PR/public-action draft files."
    )
    parser.add_argument(
        "--draft",
        action="append",
        default=[],
        help="Local draft file to inspect. May be passed more than once.",
    )
    parser.add_argument("--approval-text", help=f"Exact approval line starting with {APPROVAL_PREFIX}")
    parser.add_argument("--approval-file", help="File containing exact approval text.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, payload = run(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
