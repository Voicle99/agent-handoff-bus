#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
import _bootstrap  # noqa: F401 - adds local src/ to sys.path for direct tool runs
from typing import Any

from agent_handoff_bus.core import scan_sensitive

SCHEMA = "agent-handoff-bus/service-template-guard/v1"

REQUIRED_TEMPLATES: dict[str, tuple[str, ...]] = {
    "launchd-auto-reply.plist.template": (
        "${PYTHON_BIN}",
        "${HOME}/.agent-handoff-bus",
        "agent_handoff_bus.auto_reply",
        "--sessions",
        "--fallback-source",
    ),
    "systemd-auto-reply.service.template": (
        "${PYTHON_BIN}",
        "%h/.agent-handoff-bus",
        "agent_handoff_bus.auto_reply",
        "NoNewPrivileges=true",
        "PrivateTmp=true",
    ),
}

RENDERED_SERVICE_NAMES = (
    ".plist",
    ".service",
)

PRIVATE_PATH_PATTERNS = [
    ("macos_user_path", re.compile(r"(?<![A-Za-z0-9_])/(?:Users)/[A-Za-z0-9._-]+/[^\s`'\"<>)]*")),
    ("linux_user_path", re.compile(r"(?<![A-Za-z0-9_])/(?:home)/[A-Za-z0-9._-]+/[^\s`'\"<>)]*")),
    ("windows_user_path", re.compile(r"(?i)\b[A-Z]:\\Users\\[^\\\s]+\\[^\s`'\"<>)]*")),
]


def _line_number(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


def _is_rendered_service_file(path: Path) -> bool:
    if path.name.endswith(".template"):
        return False
    return path.name.endswith(RENDERED_SERVICE_NAMES)


def _scan_private_paths(path: Path, text: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for kind, pattern in PRIVATE_PATH_PATTERNS:
        for match in pattern.finditer(text):
            findings.append({"kind": kind, "file": str(path), "line": _line_number(text, match.start())})
    return findings


def check_examples_dir(examples_dir: Path) -> tuple[int, dict[str, Any]]:
    examples_dir = examples_dir.expanduser().resolve()
    if not examples_dir.is_dir():
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": "examples directory not found",
            "examples_dir": str(examples_dir),
            "public_action_taken": False,
        }

    findings: list[dict[str, Any]] = []
    checked_files: list[str] = []

    for template_name, required_strings in REQUIRED_TEMPLATES.items():
        path = examples_dir / template_name
        if not path.exists():
            findings.append({"kind": "missing_template", "file": str(path)})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        checked_files.append(str(path))
        for required in required_strings:
            if required not in text:
                findings.append({"kind": "missing_required_text", "file": str(path), "required": required})
        for secret_kind in scan_sensitive(text):
            findings.append({"kind": "secret_like_content", "file": str(path), "secret_kind": secret_kind})
        findings.extend(_scan_private_paths(path, text))

    for path in sorted(examples_dir.iterdir()):
        if not path.is_file():
            continue
        if path.name in REQUIRED_TEMPLATES:
            continue
        inspect_content = path.name.endswith(RENDERED_SERVICE_NAMES) or path.suffix.lower() in {".md", ".txt"}
        if _is_rendered_service_file(path):
            findings.append(
                {
                    "kind": "rendered_service_file",
                    "file": str(path),
                    "next_action": "Keep rendered launchd/systemd files local and untracked; commit only .template files.",
                }
            )
        if not inspect_content:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        checked_files.append(str(path))
        for secret_kind in scan_sensitive(text):
            findings.append({"kind": "secret_like_content", "file": str(path), "secret_kind": secret_kind})
        findings.extend(_scan_private_paths(path, text))

    if findings:
        return 1, {
            "status": "FAIL_SERVICE_TEMPLATE_GUARD",
            "schema": SCHEMA,
            "summary": "service templates/examples need cleanup before commit",
            "examples_dir": str(examples_dir),
            "checked_files": sorted(set(checked_files)),
            "findings": findings,
            "public_action_taken": False,
        }

    return 0, {
        "status": "PASS",
        "schema": SCHEMA,
        "summary": "service templates retain required placeholders and no rendered service/private material was found",
        "examples_dir": str(examples_dir),
        "checked_files": sorted(set(checked_files)),
        "public_action_taken": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-only guard for launchd/systemd service templates.")
    parser.add_argument("--examples-dir", default="examples", help="Directory containing example templates.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, payload = check_examples_dir(Path(args.examples_dir))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
