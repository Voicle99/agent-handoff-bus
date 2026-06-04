from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from agent_handoff_bus.auto_reply import build_receipt_body, process_once
from agent_handoff_bus.core import (
    CreateInput,
    HandoffHTTPHandler,
    ThreadingHTTPServer,
    ack_handoff,
    create_handoff,
    get_handoff,
    latest_handoff,
    scan_sensitive,
    serve,
)
from agent_handoff_bus.reliable_send import find_receipt, main as reliable_send_main


class HandoffBusTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.old_home = os.environ.get("AGENT_HANDOFF_HOME")
        os.environ["AGENT_HANDOFF_HOME"] = self.tmp.name

    def tearDown(self) -> None:
        if self.old_home is None:
            os.environ.pop("AGENT_HANDOFF_HOME", None)
        else:
            os.environ["AGENT_HANDOFF_HOME"] = self.old_home
        self.tmp.cleanup()

    def _start_http_server(self) -> str:
        server = ThreadingHTTPServer(("127.0.0.1", 0), HandoffHTTPHandler)
        server.quiet = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(thread.join, 2)
        self.addCleanup(server.shutdown)
        host, port = server.server_address
        return f"http://{host}:{port}"

    def _get_json(self, url: str) -> dict[str, object]:
        with urlopen(url, timeout=5) as response:
            self.assertEqual(response.status, 200)
            return json.loads(response.read().decode("utf-8"))

    def _post_json(self, url: str, payload: dict[str, object], expected_status: int = 200) -> dict[str, object]:
        request = Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=5) as response:
            self.assertEqual(response.status, expected_status)
            return json.loads(response.read().decode("utf-8"))

    def test_send_latest_ack(self) -> None:
        item = create_handoff(CreateInput(target_session="agent-b", source_session="agent-a", title="Hello", body="Review this."))
        self.assertEqual(item["status"], "PENDING")
        latest = latest_handoff("agent-b", pending_only=True)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["id"], item["id"])
        acked = ack_handoff(item["id"], note="done")
        self.assertEqual(acked["status"], "ACKED")

    def test_reliable_send_passes_and_optionally_acks_receipt(self) -> None:
        env = os.environ.copy()
        env["AGENT_HANDOFF_HOME"] = self.tmp.name
        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "agent_handoff_bus.reliable_send",
                "--from",
                "agent-a",
                "--to",
                "agent-b",
                "--title",
                "Needs receipt",
                "--body",
                "Auto-reply worker should receive this.",
                "--timeout",
                "2",
                "--interval",
                "0.01",
                "--ack-receipt",
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        def kill_if_running() -> None:
            if process.poll() is None:
                process.kill()

        self.addCleanup(kill_if_running)

        deadline = time.time() + 5
        while process.poll() is None and time.time() < deadline:
            with redirect_stdout(io.StringIO()):
                process_once(["agent-b"], fallback_source="agent-a")
            time.sleep(0.01)

        stdout, stderr = process.communicate(timeout=1)
        self.assertEqual(process.returncode, 0, stderr)
        payload = json.loads(stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertTrue(payload["receipt_acked"])
        receipt = get_handoff(payload["receipt_handoff"]["id"])
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["status"], "ACKED")

    def test_secret_scanner_blocks(self) -> None:
        self.assertIn("openai_api_key", scan_sensitive("sk-" + "a" * 30))
        with self.assertRaises(ValueError):
            create_handoff(CreateInput(target_session="agent-b", title="bad", body="sk-" + "a" * 30))

    def test_secret_scanner_fixture_matrix_uses_fake_values(self) -> None:
        cases = [
            ("openai_api_key", "sk-" + "a" * 30),
            ("github_token", "ghp_" + "a" * 24),
            ("aws_access_key", "AKIA" + "A" * 16),
            ("private_key", "-----BEGIN " + "PRIVATE KEY-----\nfake\n-----END " + "PRIVATE KEY-----"),
            ("bearer_token", "Bearer " + "a" * 24),
            ("generic_secret_assignment", "api_key=" + "a" * 16),
        ]
        for expected, body in cases:
            with self.subTest(expected=expected):
                self.assertIn(expected, scan_sensitive(body))

    def test_secret_scanner_does_not_block_short_obvious_placeholders(self) -> None:
        self.assertEqual(scan_sensitive("password=short token=example api_key=dummy"), [])

    def test_auto_reply_with_secret_hint_never_quotes_original_body(self) -> None:
        sentinel = "DO_NOT_QUOTE_THIS_SENTINEL"
        item = create_handoff(
            CreateInput(
                target_session="agent-b",
                source_session="agent-a",
                title="Sensitive looking body",
                body=("sk-" + "a" * 30 + f"\n{sentinel}"),
                allow_sensitive=True,
            )
        )
        receipt_body = build_receipt_body(item)
        self.assertIn("BLOCKED_SECRET_HINT: body not quoted", receipt_body)
        self.assertNotIn("sk-" + "a" * 30, receipt_body)
        self.assertNotIn(sentinel, receipt_body)

    def test_auto_reply_receipt(self) -> None:
        item = create_handoff(CreateInput(target_session="agent-b", source_session="agent-a", title="Critical", body="Please receive."))
        sent = process_once(["agent-b"], fallback_source="agent-a")
        self.assertEqual(sent, 1)
        receipt = find_receipt(item["id"], "agent-a")
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["source_session"], "auto-reply")

    def test_reliable_send_times_out_fail_closed(self) -> None:
        out = io.StringIO()
        with redirect_stdout(out):
            exit_code = reliable_send_main(
                [
                    "--from",
                    "agent-a",
                    "--to",
                    "agent-b",
                    "--title",
                    "Needs receipt",
                    "--body",
                    "No auto-reply worker is running.",
                    "--timeout",
                    "0.01",
                    "--interval",
                    "0.01",
                ]
            )
        payload = json.loads(out.getvalue())
        self.assertEqual(exit_code, 3)
        self.assertEqual(payload["status"], "BLOCKED_NO_AUTO_RECEIPT")
        self.assertEqual(payload["original_handoff"]["target_session"], "agent-b")
        self.assertIn("agent-handoff-auto-reply --sessions <receiver-session>", payload["next_checks"])

    def test_http_api_send_latest_ack_status(self) -> None:
        base_url = self._start_http_server()
        health = self._get_json(f"{base_url}/health")
        self.assertEqual(health["status"], "OK")

        created = self._post_json(
            f"{base_url}/handoffs",
            {
                "target_session": "agent-b",
                "source_session": "agent-a",
                "title": "HTTP handoff",
                "body": "Review this via the localhost API.",
            },
            expected_status=201,
        )
        handoff = created["handoff"]
        self.assertEqual(handoff["target_session"], "agent-b")
        self.assertEqual(handoff["status"], "PENDING")

        query = urlencode({"target_session": "agent-b", "pending_only": "true"})
        latest = self._get_json(f"{base_url}/handoffs/latest?{query}")
        self.assertEqual(latest["handoff"]["id"], handoff["id"])

        acked = self._post_json(f"{base_url}/handoffs/{handoff['id']}/ack", {"note": "handled"})
        self.assertEqual(acked["handoff"]["status"], "ACKED")

        session = self._get_json(f"{base_url}/sessions/agent-b/status")
        self.assertEqual(session["pending_count"], 0)
        self.assertEqual(session["latest"]["status"], "ACKED")

    def test_http_api_rejects_secret_like_body(self) -> None:
        base_url = self._start_http_server()
        request = Request(
            f"{base_url}/handoffs",
            data=json.dumps(
                {
                    "target_session": "agent-b",
                    "title": "bad",
                    "body": "sk-" + "a" * 30,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as ctx:
            urlopen(request, timeout=5)
        self.assertEqual(ctx.exception.code, 400)
        payload = json.loads(ctx.exception.read().decode("utf-8"))
        ctx.exception.close()
        self.assertIn("sensitive material detected", payload["error"])

    def test_serve_refuses_non_loopback_host_before_binding(self) -> None:
        with self.assertRaises(ValueError):
            serve(host="0.0.0.0", port=0, quiet=True)

    def test_body_file_written(self) -> None:
        item = create_handoff(CreateInput(target_session="agent-b", title="File", body="content"))
        path = Path(item["body_path"])
        self.assertTrue(path.exists())
        self.assertIn("content", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
