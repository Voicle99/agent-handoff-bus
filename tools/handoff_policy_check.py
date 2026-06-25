#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import _bootstrap  # noqa: F401 - adds local src/ to sys.path for direct tool runs
from typing import Any

from agent_handoff_bus.core import scan_sensitive

SCHEMA = "agent-handoff-bus/handoff-policy-check/v1"
APPROVAL_PREFIX = "APPROVED_HIGH_RISK_HANDOFF:"

PRIVATE_DATA_PATTERNS = [
    (
        "personal_local_path",
        re.compile(r"(?<![A-Za-z0-9_])(?:/Users|/home)/[A-Za-z0-9._-]+/[^\s`'\"<>)]*"),
    ),
    ("windows_user_path", re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+\\[^\s`'\"<>)]*")),
    ("private_transcript_marker", re.compile(r"(?i)BEGIN PRIVATE (CHAT )?TRANSCRIPT|PRIVATE TRANSCRIPT START")),
    ("browser_cookie_dump", re.compile(r"(?i)\b(cookie|session)_dump\b|BEGIN BROWSER COOKIES")),
]

NEGATION_HINTS = (
    "do not",
    "don't",
    "never",
    "no public action",
    "no paid action",
    "not authorized",
    "not allowed",
    "without approval",
    "requires approval",
    "human-gated",
    "human gated",
)

RISK_PATTERNS = [
    (
        "public_action",
        re.compile(
            r"(?i)\b(post|publish|upload|deploy|release|tag|merge|comment|reply|send email|email|dm|create issue|close issue|open pr|open pull request)\b"
        ),
    ),
    (
        "paid_or_purchase",
        re.compile(r"(?i)\b(paid api|purchase|buy|subscribe|billing|charge|payment|credits?)\b"),
    ),
    (
        "oauth_or_login",
        re.compile(r"(?i)\b(oauth|login|log in|sign in|passkey|2fa|mfa|account permission|account access)\b"),
    ),
    (
        "credential_access",
        re.compile(r"(?i)\b(credential|credentials|keychain|keyring|browser cookie|cookies|\.env|token store|password|api key)\b"),
    ),
    (
        "public_network_bind",
        re.compile(r"(?i)\b(0\.0\.0\.0|public bind|public interface|non-loopback|internet-facing)\b"),
    ),
]

APPROVAL_ACTION_WORDS = (
    "post",
    "publish",
    "upload",
    "deploy",
    "release",
    "tag",
    "merge",
    "comment",
    "reply",
    "email",
    "dm",
    "create issue",
    "close issue",
    "open pr",
    "open pull request",
    "oauth",
    "login",
    "paid api",
    "purchase",
    "credential",
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


def _read_text(args: argparse.Namespace) -> tuple[str, str]:
    if args.body_file:
        path = Path(args.body_file).expanduser().resolve()
        return path.read_text(encoding="utf-8", errors="replace"), str(path)
    return args.body or "", "inline-body"


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _is_negated(line: str) -> bool:
    lowered = line.lower()
    return any(hint in lowered for hint in NEGATION_HINTS)


def _scan_private_data(source: str, text: str) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for kind, pattern in PRIVATE_DATA_PATTERNS:
        for match in pattern.finditer(text):
            hits.append({"kind": kind, "source": source, "line": _line_number(text, match.start())})
    return hits


def _scan_high_risk(source: str, text: str) -> list[dict[str, Any]]:
    risks: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), 1):
        if _is_negated(line):
            continue
        for kind, pattern in RISK_PATTERNS:
            if pattern.search(line):
                risks.append({"kind": kind, "source": source, "line": line_number})
    return risks


def _read_approval(args: argparse.Namespace) -> str:
    if args.approval_file:
        path = Path(args.approval_file).expanduser().resolve()
        return path.read_text(encoding="utf-8", errors="replace").strip()
    return (args.approval_text or "").strip()


def _approval_check(approval: str) -> dict[str, Any]:
    if not approval:
        return {"present": False, "specific": False, "reason": "missing exact high-risk approval"}
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
        return {"present": True, "specific": False, "reason": "approval is too vague"}
    if not any(word in normalized for word in APPROVAL_ACTION_WORDS):
        return {
            "present": True,
            "specific": False,
            "reason": "approval does not name a concrete high-risk action",
        }
    return {"present": True, "specific": True, "reason": "exact high-risk approval present", "action": action}


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    body, source = _read_text(args)
    if not body.strip():
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": "handoff body required",
            "public_action_taken": False,
            "next_action": "Provide --body or --body-file with local handoff text.",
        }

    sensitive_hits = sorted(scan_sensitive(body))
    private_hits = _scan_private_data(source, body)
    if sensitive_hits or private_hits:
        return 3, {
            "status": "BLOCKED_PRIVATE_OR_SECRET_DATA",
            "schema": SCHEMA,
            "summary": "handoff contains secret-like or private material",
            "source": source,
            "public_action_taken": False,
            "sensitive_scan_hits": sensitive_hits,
            "private_data_hits": private_hits,
            "next_action": "Remove real secrets/private data or replace with dummy values before sending this handoff.",
        }

    risks = _scan_high_risk(source, body)
    if not risks:
        return 0, {
            "status": "PASS_LOW_RISK",
            "schema": SCHEMA,
            "summary": "handoff text is locally low-risk under the current policy hints",
            "source": source,
            "public_action_taken": False,
            "risk_hits": [],
            "next_action": "Proceed with local coordination only; public/paid/OAuth/credential actions still need separate approval.",
        }

    approval = _approval_check(_read_approval(args))
    if not approval["specific"]:
        return 4, {
            "status": "BLOCKED_HIGH_RISK_HANDOFF_REQUIRES_APPROVAL",
            "schema": SCHEMA,
            "summary": "handoff requests high-risk action without exact approval",
            "source": source,
            "public_action_taken": False,
            "risk_hits": risks,
            "approval": approval,
            "next_action": (
                f"Provide --approval-text '{APPROVAL_PREFIX} <exact action and target>' "
                "only after a human approves that high-risk action."
            ),
        }

    return 0, {
        "status": "PASS_HIGH_RISK_APPROVED",
        "schema": SCHEMA,
        "summary": "high-risk handoff text is locally clean and exact approval text is present",
        "source": source,
        "public_action_taken": False,
        "risk_hits": risks,
        "approval": approval,
        "next_action": "This checker performed no public/paid/OAuth/credential action; execute separately only within the approved boundary.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-only high-risk policy checker for handoff text.")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--body", help="Inline handoff text to inspect.")
    source.add_argument("--body-file", help="Local file containing handoff text to inspect.")
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
