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
    doctor,
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

    def test_cli_source_session_alias_and_catchup_inbox(self) -> None:
        env = {**os.environ, "PYTHONPATH": "src"}
        send = subprocess.run(
            [
                sys.executable,
                "-m",
                "agent_handoff_bus",
                "send",
                "--source-session",
                "agent-a",
                "--to",
                "agent-b",
                "--title",
                "CLI alias",
                "--body",
                "Catch up on this portable operator command.",
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(send.returncode, 0, send.stderr)
        sent = json.loads(send.stdout)
        self.assertEqual(sent["status"], "SENT")
        self.assertEqual(sent["handoff"]["source_session"], "agent-a")

        catchup = subprocess.run(
            [sys.executable, "-m", "agent_handoff_bus", "catchup", "agent-b"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(catchup.returncode, 0, catchup.stderr)
        payload = json.loads(catchup.stdout)
        self.assertEqual(payload["status"], "OK")
        self.assertEqual(payload["target_session"], "agent-b")
        self.assertEqual(payload["pending_count"], 1)

        inbox = subprocess.run(
            [sys.executable, "-m", "agent_handoff_bus", "inbox", "--for", "agent-b", "--plain"],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(inbox.returncode, 0, inbox.stderr)
        self.assertIn("Catch up on this portable operator command.", inbox.stdout)

    def test_pyproject_declares_handoff_bus_entrypoint(self) -> None:
        text = Path("pyproject.toml").read_text(encoding="utf-8")
        self.assertIn('handoff-bus = "agent_handoff_bus.cli:main"', text)

    def test_ci_workflow_uses_node24_actions(self) -> None:
        text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("actions/checkout@v6", text)
        self.assertIn("actions/setup-python@v6", text)
        self.assertNotIn("actions/checkout@v4", text)
        self.assertNotIn("actions/setup-python@v5", text)

    def test_doctor_accepts_handoff_bus_console_script_alias(self) -> None:
        old_path = os.environ.get("PATH", "")
        with tempfile.TemporaryDirectory() as tmp:
            alias = Path(tmp) / "handoff-bus"
            alias.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
            alias.chmod(0o755)
            os.environ["PATH"] = tmp
            try:
                status, checks = doctor()
            finally:
                os.environ["PATH"] = old_path
        self.assertEqual(status, "PASS")
        cli_check = next(check for check in checks if check["id"] == "cli_available")
        self.assertEqual(cli_check["status"], "PASS")
        self.assertEqual(cli_check["commands"]["handoff-bus"], str(alias))

    def test_ai_assisted_install_guide_has_bounded_prompt(self) -> None:
        text = Path("docs/AI_ASSISTED_5_MIN_INSTALL.md").read_text(encoding="utf-8")
        self.assertIn("AI-assisted 5-minute install", text)
        self.assertIn("INSTALL_READY", text)
        self.assertIn("BLOCKED_INSTALL_PREREQ", text)
        self.assertIn("Do not ask for or read secrets", text)
        self.assertIn("handoff-bus doctor", text)
        self.assertIn("handoff-bus inbox --for agent-b --plain", text)

    def test_commercial_readiness_docs_exist(self) -> None:
        required = {
            "TERMS.md": ["No implicit authority", "refund", "MIT License"],
            "PRIVACY.md": ["Telemetry", "local files", "Data deletion"],
            "SUPPORT.md": ["Refund and cancellation policy", "Response targets", "Bug report checklist"],
            "CHANGELOG.md": ["v0.2.0", "AI-assisted 5-minute install"],
            "docs/PRICING_AND_OFFER.md": ["Guided install pilot", "Managed operator setup", "Do not promise"],
            "docs/DEMO_AND_FAQ.md": ["Two-minute demo script", "Demo checklist", "FAQ"],
        }
        for filename, markers in required.items():
            with self.subTest(filename=filename):
                text = Path(filename).read_text(encoding="utf-8")
                for marker in markers:
                    self.assertIn(marker, text)

    def test_release_artifact_helper_is_local_only(self) -> None:
        text = Path("tools/build_release_artifacts.py").read_text(encoding="utf-8")
        self.assertIn("does not upload to PyPI", text)
        self.assertIn("SHA256SUMS", text)
        self.assertIn("public_action_taken", text)

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

    def test_receipt_benchmark_script_passes(self) -> None:
        env = os.environ.copy()
        env["PYTHONPATH"] = "src"
        result = subprocess.run(
            [
                sys.executable,
                "tools/receipt_benchmark.py",
                "--success-timeout",
                "2",
                "--fail-timeout",
                "0.01",
                "--interval",
                "0.01",
            ],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual([check["status"] for check in payload["checks"]], ["PASS", "PASS"])
        self.assertEqual(payload["network"], "local-only")
        self.assertTrue(payload["dummy_data_only"])

    def test_local_adapter_dry_run_script_passes_and_writes_summary_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/local_adapter_dry_run.py",
                    "--task-id",
                    "adapter-test",
                    "--title",
                    "Adapter test",
                    "--body",
                    "Dummy adapter body that must not be quoted in the artifact.",
                    "--output-dir",
                    tmp,
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertFalse(payload["public_action_taken"])
            artifact = Path(payload["artifacts"][0])
            self.assertTrue(artifact.exists())
            artifact_text = artifact.read_text(encoding="utf-8")
            self.assertIn("summary-only", artifact_text)
            self.assertNotIn("Dummy adapter body", artifact_text)

    def test_local_adapter_dry_run_blocks_secret_like_input(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/local_adapter_dry_run.py",
                "--body",
                "sk-" + "a" * 30,
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 3, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "BLOCKED")
        self.assertFalse(payload["public_action_taken"])
        self.assertIn("openai_api_key", payload["sensitive_scan_hits"])

    def test_public_action_draft_guard_requires_exact_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "issue-comment.md"
            draft.write_text(
                "Dummy public comment draft.\nNo credentials. No public action yet.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/public_action_draft_guard.py",
                    "--draft",
                    str(draft),
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 4, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "BLOCKED_PUBLIC_ACTION_REQUIRES_APPROVAL")
            self.assertFalse(payload["public_action_taken"])

    def test_public_action_draft_guard_passes_with_specific_approval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "issue-comment.md"
            draft.write_text(
                "Dummy public comment draft.\nValidation: py_compile and unittest pass.\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/public_action_draft_guard.py",
                    "--draft",
                    str(draft),
                    "--approval-text",
                    "APPROVED_PUBLIC_ACTION: comment on issue #123 with reviewed draft file",
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "PASS_PUBLIC_ACTION_READY")
            self.assertFalse(payload["public_action_taken"])

    def test_public_action_draft_guard_blocks_secret_or_private_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            draft = Path(tmp) / "bad-comment.md"
            draft.write_text(
                "Do not post this: sk-" + "a" * 30 + "\nLocal path: /Users/alice/project/private.log\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/public_action_draft_guard.py",
                    "--draft",
                    str(draft),
                    "--approval-text",
                    "APPROVED_PUBLIC_ACTION: comment on issue #123 with reviewed draft file",
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 3, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "BLOCKED_PRIVATE_DATA")
            self.assertFalse(payload["public_action_taken"])
            self.assertIn("openai_api_key", payload["sensitive_scan_hits"])
            self.assertEqual(payload["private_data_hits"][0]["kind"], "personal_local_path")

    def test_repo_secret_scan_passes_current_repo_with_fake_fixtures(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/repo_secret_scan.py",
                "--root",
                ".",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["public_action_taken"])
        self.assertGreaterEqual(payload["scanned_files"], 1)
        self.assertGreaterEqual(len(payload["allowed_fixture_hits"]), 1)

    def test_repo_secret_scan_blocks_untracked_secret_or_private_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(
                ["git", "init"],
                cwd=root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            (root / "leak.txt").write_text(
                "Do not commit sk-" + "a" * 30 + " or /Users/bob/private.log\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/repo_secret_scan.py",
                    "--root",
                    str(root),
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 3, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "BLOCKED_SECRET_OR_PRIVATE_DATA")
            self.assertFalse(payload["public_action_taken"])
            self.assertEqual(payload["candidate_files"], 1)
            kinds = {finding["kind"] for finding in payload["findings"]}
            self.assertIn("openai_api_key", kinds)
            self.assertIn("personal_local_path", kinds)

    def test_gitignore_excludes_local_mcp_config(self) -> None:
        gitignore = Path(".gitignore").read_text(encoding="utf-8").splitlines()
        self.assertIn(".mcp.json", gitignore)

    def test_service_template_guard_passes_current_examples(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/service_template_guard.py",
                "--examples-dir",
                "examples",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["public_action_taken"])

    def test_service_template_guard_blocks_rendered_private_service(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            examples_dir = Path(tmp)
            (examples_dir / "launchd-auto-reply.plist.template").write_text(
                "${PYTHON_BIN} ${HOME}/.agent-handoff-bus agent_handoff_bus.auto_reply --sessions --fallback-source",
                encoding="utf-8",
            )
            (examples_dir / "systemd-auto-reply.service.template").write_text(
                "${PYTHON_BIN} %h/.agent-handoff-bus agent_handoff_bus.auto_reply NoNewPrivileges=true PrivateTmp=true",
                encoding="utf-8",
            )
            (examples_dir / "agent-handoff-auto-reply.service").write_text(
                "ExecStart=/Users/alice/project/.venv/bin/python -m agent_handoff_bus.auto_reply",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/service_template_guard.py",
                    "--examples-dir",
                    str(examples_dir),
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL_SERVICE_TEMPLATE_GUARD")
            self.assertFalse(payload["public_action_taken"])
            kinds = {finding["kind"] for finding in payload["findings"]}
            self.assertIn("rendered_service_file", kinds)
            self.assertIn("macos_user_path", kinds)

    def test_docs_link_check_passes_current_docs(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/docs_link_check.py",
                "--root",
                ".",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["public_action_taken"])
        self.assertGreater(payload["checked_links"], 0)

    def test_docs_link_check_blocks_missing_relative_link_and_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text(
                "# Demo\n\n[missing](docs/nope.md)\n[bad anchor](docs/guide.md#missing-heading)\n",
                encoding="utf-8",
            )
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("# Existing heading\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/docs_link_check.py",
                    "--root",
                    str(root),
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL_DOCS_LINK_CHECK")
            self.assertFalse(payload["public_action_taken"])
            kinds = {finding["kind"] for finding in payload["findings"]}
            self.assertIn("missing_target", kinds)
            self.assertIn("missing_anchor", kinds)

    def test_worktree_health_check_passes_current_repo(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/worktree_health_check.py",
                "--root",
                ".",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["public_action_taken"])
        self.assertEqual(payload["findings"], [])
        self.assertGreater(len(payload["head"]), 10)

    def test_worktree_health_check_fails_closed_for_non_git_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/worktree_health_check.py",
                    "--root",
                    tmp,
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL_WORKTREE_HEALTH")
            self.assertFalse(payload["public_action_taken"])
            self.assertEqual(payload["findings"][0]["kind"], "invalid_git_worktree")

    def test_release_notes_dry_run_passes_current_repo(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/release_notes_dry_run.py",
                "--limit",
                "3",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["public_action_taken"])
        self.assertGreater(payload["commit_count"], 0)
        self.assertIn("Draft release notes", payload["markdown"])
        self.assertIn("Public action: not taken.", payload["markdown"])

    def test_release_notes_dry_run_fails_closed_for_non_git_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/release_notes_dry_run.py",
                    "--root",
                    tmp,
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL_RELEASE_NOTES_DRY_RUN")
            self.assertFalse(payload["public_action_taken"])

    def test_tools_help_direct_run_without_pythonpath(self) -> None:
        env = os.environ.copy()
        env.pop("PYTHONPATH", None)
        tool_paths = sorted(path for path in Path("tools").glob("*.py") if not path.name.startswith("_"))
        self.assertGreater(tool_paths, [])
        for tool_path in tool_paths:
            with self.subTest(tool=str(tool_path)):
                result = subprocess.run(
                    [sys.executable, str(tool_path), "--help"],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=10,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("usage:", result.stdout.lower())

    def test_maintainer_check_passes_selected_current_checks(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/maintainer_check.py",
                "--check",
                "worktree_health",
                "--check",
                "docs_link",
                "--check",
                "service_template",
                "--check",
                "handoff_policy",
                "--check",
                "repo_secret_scan",
                "--check",
                "release_notes",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=20,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertFalse(payload["public_action_taken"])
        self.assertEqual(
            [check["name"] for check in payload["checks"]],
            ["worktree_health", "docs_link", "service_template", "handoff_policy", "repo_secret_scan", "release_notes"],
        )

    def test_maintainer_check_writes_output_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "nested" / "maintainer-check.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/maintainer_check.py",
                    "--check",
                    "worktree_health",
                    "--check",
                    "docs_link",
                    "--output",
                    str(output_path),
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertTrue(output_path.is_file())
            stdout_payload = json.loads(result.stdout)
            file_payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(file_payload, stdout_payload)
            self.assertEqual(file_payload["status"], "PASS")
            self.assertEqual(file_payload["public_summary"]["status"], "PASS")
            self.assertTrue(file_payload["public_summary"]["local_paths_omitted"])
            self.assertTrue(file_payload["public_summary"]["raw_commands_omitted"])
            public_summary_json = json.dumps(file_payload["public_summary"])
            self.assertNotIn(str(Path.home()), public_summary_json)
            self.assertNotIn("tools/", public_summary_json)
            self.assertNotIn("root", public_summary_json)
            self.assertFalse(file_payload["public_action_taken"])
            self.assertEqual([check["name"] for check in file_payload["checks"]], ["worktree_health", "docs_link"])

    def test_maintainer_check_writes_failed_output_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "not-a-git-repo"
            root.mkdir()
            output_path = Path(tmp) / "failed" / "maintainer-check.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/maintainer_check.py",
                    "--root",
                    str(root),
                    "--check",
                    "worktree_health",
                    "--output",
                    str(output_path),
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertTrue(output_path.is_file())
            stdout_payload = json.loads(result.stdout)
            file_payload = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(file_payload, stdout_payload)
            self.assertEqual(file_payload["status"], "FAIL_MAINTAINER_CHECK")
            self.assertEqual(file_payload["public_summary"]["status"], "FAIL_MAINTAINER_CHECK")
            self.assertTrue(file_payload["public_summary"]["local_paths_omitted"])
            public_summary_json = json.dumps(file_payload["public_summary"])
            self.assertNotIn(str(Path.home()), public_summary_json)
            self.assertNotIn("tools/", public_summary_json)
            self.assertNotIn("root", public_summary_json)
            self.assertEqual(file_payload["failed_checks"], ["worktree_health"])
            self.assertFalse(file_payload["public_action_taken"])

    def test_maintainer_check_fails_closed_on_broken_docs_link(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("# Demo\n\n[missing](docs/nope.md)\n", encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    "tools/maintainer_check.py",
                    "--root",
                    str(root),
                    "--check",
                    "docs_link",
                ],
                env={**os.environ, "PYTHONPATH": "src"},
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=20,
                check=False,
            )
            self.assertEqual(result.returncode, 1, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL_MAINTAINER_CHECK")
            self.assertFalse(payload["public_action_taken"])
            self.assertEqual(payload["failed_checks"], ["docs_link"])

    def test_handoff_policy_check_passes_low_risk_local_review(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/handoff_policy_check.py",
                "--body",
                "Review this local patch. Do not push, post, release, or access credentials.",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS_LOW_RISK")
        self.assertFalse(payload["public_action_taken"])
        self.assertEqual(payload["risk_hits"], [])

    def test_handoff_policy_check_blocks_high_risk_without_approval(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/handoff_policy_check.py",
                "--body",
                "Please post this comment to issue #123 and close issue #123.",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 4, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "BLOCKED_HIGH_RISK_HANDOFF_REQUIRES_APPROVAL")
        self.assertFalse(payload["public_action_taken"])
        self.assertEqual(payload["risk_hits"][0]["kind"], "public_action")

    def test_handoff_policy_check_blocks_imperative_without_approval_wording(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/handoff_policy_check.py",
                "--body",
                "Publish a release and upload the package without approval.",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 4, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "BLOCKED_HIGH_RISK_HANDOFF_REQUIRES_APPROVAL")
        self.assertFalse(payload["public_action_taken"])
        self.assertEqual(payload["risk_hits"][0]["kind"], "public_action")

    def test_handoff_policy_check_passes_high_risk_with_exact_approval(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/handoff_policy_check.py",
                "--body",
                "Please post this comment to issue #123 and close issue #123.",
                "--approval-text",
                "APPROVED_HIGH_RISK_HANDOFF: comment on issue #123 and close issue #123 after CI passes",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS_HIGH_RISK_APPROVED")
        self.assertFalse(payload["public_action_taken"])
        self.assertTrue(payload["approval"]["specific"])

    def test_handoff_policy_check_blocks_private_or_secret_data(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "tools/handoff_policy_check.py",
                "--body",
                "Use sk-" + "a" * 30 + " and inspect /Users/alice/project/private.log",
                "--approval-text",
                "APPROVED_HIGH_RISK_HANDOFF: comment on issue #123 with reviewed text",
            ],
            env={**os.environ, "PYTHONPATH": "src"},
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            check=False,
        )
        self.assertEqual(result.returncode, 3, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "BLOCKED_PRIVATE_OR_SECRET_DATA")
        self.assertFalse(payload["public_action_taken"])
        self.assertIn("openai_api_key", payload["sensitive_scan_hits"])
        self.assertEqual(payload["private_data_hits"][0]["kind"], "personal_local_path")

    def test_body_file_written(self) -> None:
        item = create_handoff(CreateInput(target_session="agent-b", title="File", body="content"))
        path = Path(item["body_path"])
        self.assertTrue(path.exists())
        self.assertIn("content", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
