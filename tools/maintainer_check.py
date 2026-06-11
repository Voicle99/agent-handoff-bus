#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SCHEMA = "agent-handoff-bus/maintainer-check/v1"

CHECKS = (
    "docs_link",
    "service_template",
    "handoff_policy",
    "local_adapter",
    "receipt_benchmark",
    "release_notes",
    "py_compile",
)

EXPECTED_STATUSES: dict[str, set[str]] = {
    "docs_link": {"PASS"},
    "service_template": {"PASS"},
    "handoff_policy": {"PASS_LOW_RISK"},
    "local_adapter": {"PASS"},
    "receipt_benchmark": {"PASS"},
    "release_notes": {"PASS"},
    "py_compile": {"PASS"},
}


class CheckError(RuntimeError):
    pass


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _python_env() -> dict[str, str]:
    env = os.environ.copy()
    src = str(_project_root() / "src")
    existing = env.get("PYTHONPATH")
    env["PYTHONPATH"] = src if not existing else f"{src}{os.pathsep}{existing}"
    return env


def _json_from_stdout(stdout: str) -> dict[str, Any] | None:
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _run_json_check(name: str, command: list[str], root: Path) -> dict[str, Any]:
    started = time.monotonic()
    result = subprocess.run(
        command,
        cwd=str(root),
        env=_python_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )
    payload = _json_from_stdout(result.stdout)
    observed_status = payload.get("status") if payload else None
    passed = result.returncode == 0 and observed_status in EXPECTED_STATUSES[name]
    return {
        "name": name,
        "status": "PASS" if passed else "FAIL",
        "exit_code": result.returncode,
        "observed_status": observed_status,
        "command": " ".join(command),
        "summary": payload.get("summary") if payload else "command did not emit JSON object",
        "duration_seconds": round(time.monotonic() - started, 4),
        "stderr_present": bool(result.stderr.strip()),
        "public_action_taken": bool(payload.get("public_action_taken")) if payload else False,
    }


def _run_py_compile(root: Path) -> dict[str, Any]:
    started = time.monotonic()
    files: list[Path] = []
    for pattern in ("src/agent_handoff_bus/*.py", "tests/*.py", "tools/*.py"):
        files.extend(sorted(root.glob(pattern)))
    command = [sys.executable, "-m", "py_compile", *[str(path) for path in files]]
    if not files:
        return {
            "name": "py_compile",
            "status": "FAIL",
            "exit_code": 2,
            "observed_status": "ERROR",
            "command": " ".join(command),
            "summary": "no Python files found for compile check",
            "duration_seconds": round(time.monotonic() - started, 4),
            "stderr_present": False,
            "public_action_taken": False,
        }
    result = subprocess.run(
        command,
        cwd=str(root),
        env=_python_env(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=30,
        check=False,
    )
    passed = result.returncode == 0
    return {
        "name": "py_compile",
        "status": "PASS" if passed else "FAIL",
        "exit_code": result.returncode,
        "observed_status": "PASS" if passed else "FAIL_PY_COMPILE",
        "command": " ".join(command[:3] + [f"<{len(files)} files>"]),
        "checked_files": [_safe_rel(path, root) for path in files],
        "summary": "Python files compile" if passed else "Python compile check failed",
        "duration_seconds": round(time.monotonic() - started, 4),
        "stderr_present": bool(result.stderr.strip()),
        "public_action_taken": False,
    }


def _command_for_check(name: str, root: Path, temp_dir: Path, args: argparse.Namespace) -> list[str]:
    scripts = _project_root() / "tools"
    if name == "docs_link":
        return [sys.executable, str(scripts / "docs_link_check.py"), "--root", str(root)]
    if name == "service_template":
        return [sys.executable, str(scripts / "service_template_guard.py"), "--examples-dir", str(root / "examples")]
    if name == "handoff_policy":
        return [
            sys.executable,
            str(scripts / "handoff_policy_check.py"),
            "--body",
            "Review this local patch. Do not push, post, release, or access credentials.",
        ]
    if name == "local_adapter":
        return [
            sys.executable,
            str(scripts / "local_adapter_dry_run.py"),
            "--task-id",
            "maintainer-check",
            "--source-session",
            "maintainer-check",
            "--target-session",
            "local-dummy-adapter",
            "--title",
            "Maintainer check local adapter dry run",
            "--body",
            "Dummy local-only maintainer check. No credentials. No public action.",
            "--output-dir",
            str(temp_dir / "adapter-dry-run"),
        ]
    if name == "receipt_benchmark":
        return [
            sys.executable,
            str(scripts / "receipt_benchmark.py"),
            "--success-timeout",
            str(args.receipt_success_timeout),
            "--fail-timeout",
            str(args.receipt_fail_timeout),
            "--interval",
            str(args.receipt_interval),
        ]
    if name == "release_notes":
        return [
            sys.executable,
            str(scripts / "release_notes_dry_run.py"),
            "--root",
            str(root),
            "--limit",
            str(args.release_notes_limit),
        ]
    raise CheckError(f"unknown check: {name}")


def _selected_checks(args: argparse.Namespace) -> list[str]:
    checks = list(args.check or CHECKS)
    if args.skip_receipt_benchmark:
        checks = [check for check in checks if check != "receipt_benchmark"]
    unknown = sorted(set(checks) - set(CHECKS))
    if unknown:
        raise CheckError(f"unknown check(s): {', '.join(unknown)}")
    return checks


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
        checks_to_run = _selected_checks(args)
    except CheckError as exc:
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": str(exc),
            "root": str(root),
            "public_action_taken": False,
        }

    check_results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="agent-handoff-bus-maintainer-check-") as tmp:
        temp_dir = Path(tmp)
        for check in checks_to_run:
            if check == "py_compile":
                result = _run_py_compile(root)
            else:
                command = _command_for_check(check, root, temp_dir, args)
                result = _run_json_check(check, command, root)
            check_results.append(result)

    failed = [check for check in check_results if check["status"] != "PASS"]
    public_actions = [check for check in check_results if check.get("public_action_taken")]
    if failed or public_actions:
        return 1, {
            "status": "FAIL_MAINTAINER_CHECK",
            "schema": SCHEMA,
            "summary": "one or more local maintainer checks failed",
            "root": str(root),
            "checks": check_results,
            "failed_checks": [check["name"] for check in failed],
            "public_action_taken": bool(public_actions),
        }

    return 0, {
        "status": "PASS",
        "schema": SCHEMA,
        "summary": "all selected local maintainer checks passed",
        "root": str(root),
        "checks": check_results,
        "public_action_taken": False,
        "next_action": "Review the diff before any separate public action such as push, comment, release, or package upload.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run local-only maintainer checks for agent-handoff-bus.")
    parser.add_argument("--root", default=".", help="Repository root to check.")
    parser.add_argument(
        "--check",
        action="append",
        choices=CHECKS,
        help="Check to run. May be passed more than once. Defaults to all checks.",
    )
    parser.add_argument("--skip-receipt-benchmark", action="store_true", help="Skip the local receipt benchmark.")
    parser.add_argument("--receipt-success-timeout", type=float, default=2.0)
    parser.add_argument("--receipt-fail-timeout", type=float, default=0.05)
    parser.add_argument("--receipt-interval", type=float, default=0.01)
    parser.add_argument("--release-notes-limit", type=int, default=5, help="Commit limit for the release-notes dry-run check.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, payload = run(args)
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
