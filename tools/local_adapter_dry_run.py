#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any

from agent_handoff_bus.core import scan_sensitive

SCHEMA = "agent-handoff-bus/local-adapter-dry-run/v1"


def _read_body(args: argparse.Namespace) -> tuple[str, str | None]:
    if args.body_file:
        path = Path(args.body_file).expanduser().resolve()
        return path.read_text(encoding="utf-8", errors="replace"), str(path)
    return args.body or "", None


def _default_output_dir() -> Path:
    home = os.environ.get("AGENT_HANDOFF_HOME")
    if home:
        return Path(home).expanduser().resolve() / "adapters" / "dry-run"
    return Path(tempfile.mkdtemp(prefix="agent-handoff-bus-adapter-"))


def _write_artifact(output_dir: Path, task_id: str, title: str, body: str, source_file: str | None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    body_hash = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    artifact = output_dir / f"{task_id}.md"
    artifact.write_text(
        "\n".join(
            [
                f"# Local adapter dry run: {title}",
                "",
                "Status: PASS",
                "Adapter: local-dummy",
                f"Body SHA256: {body_hash}",
                f"Body bytes: {len(body.encode('utf-8', errors='replace'))}",
                f"Source file: {source_file or 'inline-body'}",
                "",
                "This artifact is summary-only. It does not quote the original handoff body.",
                "No public action, network call, OAuth/login, credential access, or paid API was performed.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return artifact


def run(args: argparse.Namespace) -> tuple[int, dict[str, Any]]:
    body, source_file = _read_body(args)
    task_id = args.task_id or f"adapter-dry-run-{uuid.uuid4().hex[:12]}"
    title = args.title or "Local adapter dry run"
    if not body.strip():
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": "body required",
            "artifacts": [],
            "public_action_taken": False,
            "next_action": "Provide --body or --body-file with dummy/local-only content.",
        }
    hits = scan_sensitive(body)
    if hits and not args.allow_sensitive:
        return 3, {
            "status": "BLOCKED",
            "schema": SCHEMA,
            "summary": "secret-like input blocked",
            "artifacts": [],
            "public_action_taken": False,
            "sensitive_scan_hits": hits,
            "next_action": "Remove secret-like material and rerun with dummy/local-only content.",
        }
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else _default_output_dir()
    artifact = _write_artifact(output_dir, task_id=task_id, title=title, body=body, source_file=source_file)
    return 0, {
        "status": "PASS",
        "schema": SCHEMA,
        "summary": "Local dummy adapter processed the handoff body summary-only.",
        "artifacts": [str(artifact)],
        "public_action_taken": False,
        "request": {
            "task_id": task_id,
            "source_session": args.source_session,
            "target_session": args.target_session,
            "handoff_id": args.handoff_id,
            "title": title,
            "body_path": source_file,
            "dry_run": True,
            "public_action_allowed": bool(args.public_action_allowed),
        },
        "next_action": "Human may inspect the local artifact before any public action.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-only dummy adapter dry run for agent-handoff-bus.")
    parser.add_argument("--task-id")
    parser.add_argument("--source-session", default="maintainer")
    parser.add_argument("--target-session", default="local-dummy-adapter")
    parser.add_argument("--handoff-id")
    parser.add_argument("--title", default="Local adapter dry run")
    parser.add_argument("--body")
    parser.add_argument("--body-file")
    parser.add_argument("--output-dir")
    parser.add_argument("--public-action-allowed", action="store_true", help="record caller intent only; this dry run still performs no public action")
    parser.add_argument("--allow-sensitive", action="store_true", help="bypass scanner for local debugging only; not recommended")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, payload = run(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
