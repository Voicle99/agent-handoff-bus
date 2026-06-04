#!/usr/bin/env python3
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from agent_handoff_bus.auto_reply import process_once


def _run_reliable(env: dict[str, str], args: list[str], communicate_timeout: float) -> tuple[int, str, str, float]:
    started = time.monotonic()
    process = subprocess.Popen(
        [sys.executable, "-m", "agent_handoff_bus.reliable_send", *args],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=communicate_timeout)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate(timeout=2)
        return 124, stdout, stderr, time.monotonic() - started
    return int(process.returncode or 0), stdout, stderr, time.monotonic() - started


def _parse_json(stdout: str) -> dict[str, Any]:
    try:
        return json.loads(stdout)
    except json.JSONDecodeError:
        return {"status": "INVALID_JSON"}


def success_with_auto_reply(env: dict[str, str], timeout: float, interval: float) -> dict[str, Any]:
    args = [
        "--from",
        "benchmark-sender",
        "--to",
        "benchmark-receiver",
        "--title",
        "receipt benchmark success path",
        "--body",
        "Dummy local benchmark handoff. No credentials. No public action.",
        "--timeout",
        str(timeout),
        "--interval",
        str(interval),
        "--ack-receipt",
    ]
    started = time.monotonic()
    process = subprocess.Popen(
        [sys.executable, "-m", "agent_handoff_bus.reliable_send", *args],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    deadline = time.monotonic() + max(timeout + 5.0, 5.0)
    sent_receipts = 0
    while process.poll() is None and time.monotonic() < deadline:
        with contextlib.redirect_stdout(io.StringIO()):
            sent_receipts += process_once(["benchmark-receiver"], fallback_source="benchmark-sender")
        time.sleep(max(interval, 0.01))
    try:
        stdout, stderr = process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        process.kill()
        stdout, stderr = process.communicate(timeout=2)
        exit_code = 124
    else:
        exit_code = int(process.returncode or 0)
    payload = _parse_json(stdout)
    latency = round(time.monotonic() - started, 4)
    passed = exit_code == 0 and payload.get("status") == "PASS" and bool(payload.get("receipt_acked"))
    return {
        "name": "success_with_auto_reply",
        "status": "PASS" if passed else "FAIL",
        "exit_code": exit_code,
        "observed_status": payload.get("status"),
        "latency_seconds": latency,
        "sent_receipts": sent_receipts,
        "stderr_present": bool(stderr.strip()),
    }


def fail_closed_without_receiver(env: dict[str, str], timeout: float, interval: float) -> dict[str, Any]:
    exit_code, stdout, stderr, latency = _run_reliable(
        env,
        [
            "--from",
            "benchmark-sender",
            "--to",
            "missing-receiver",
            "--title",
            "receipt benchmark fail closed path",
            "--body",
            "Dummy local benchmark handoff. Receiver bridge is intentionally absent.",
            "--timeout",
            str(timeout),
            "--interval",
            str(interval),
        ],
        communicate_timeout=max(timeout + 5.0, 5.0),
    )
    payload = _parse_json(stdout)
    passed = exit_code == 3 and payload.get("status") == "BLOCKED_NO_AUTO_RECEIPT"
    return {
        "name": "fail_closed_without_receiver",
        "status": "PASS" if passed else "FAIL",
        "exit_code": exit_code,
        "observed_status": payload.get("status"),
        "latency_seconds": round(latency, 4),
        "stderr_present": bool(stderr.strip()),
    }


def run_benchmark(success_timeout: float, fail_timeout: float, interval: float, keep_home: bool = False) -> dict[str, Any]:
    temp = tempfile.TemporaryDirectory(prefix="agent-handoff-bus-benchmark-")
    home = Path(temp.name)
    env = os.environ.copy()
    env["AGENT_HANDOFF_HOME"] = str(home)
    old_home = os.environ.get("AGENT_HANDOFF_HOME")
    os.environ["AGENT_HANDOFF_HOME"] = str(home)
    try:
        checks = [
            success_with_auto_reply(env, timeout=success_timeout, interval=interval),
            fail_closed_without_receiver(env, timeout=fail_timeout, interval=interval),
        ]
    finally:
        if old_home is None:
            os.environ.pop("AGENT_HANDOFF_HOME", None)
        else:
            os.environ["AGENT_HANDOFF_HOME"] = old_home
    status = "PASS" if all(check["status"] == "PASS" for check in checks) else "FAIL"
    result: dict[str, Any] = {
        "status": status,
        "schema": "agent-handoff-bus/receipt-benchmark/v1",
        "network": "local-only",
        "dummy_data_only": True,
        "checks": checks,
    }
    if keep_home:
        result["home"] = str(home)
    else:
        temp.cleanup()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Benchmark local receipt latency and fail-closed behavior.")
    parser.add_argument("--success-timeout", type=float, default=2.0)
    parser.add_argument("--fail-timeout", type=float, default=0.05)
    parser.add_argument("--interval", type=float, default=0.01)
    parser.add_argument("--keep-home", action="store_true", help="keep and print the isolated AGENT_HANDOFF_HOME for debugging")
    args = parser.parse_args(argv)
    result = run_benchmark(
        success_timeout=max(args.success_timeout, 0.05),
        fail_timeout=max(args.fail_timeout, 0.01),
        interval=max(args.interval, 0.01),
        keep_home=args.keep_home,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
