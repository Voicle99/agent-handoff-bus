from __future__ import annotations

import os
import tempfile
import threading
import time
import unittest
from pathlib import Path

from agent_handoff_bus.auto_reply import process_once
from agent_handoff_bus.core import CreateInput, ack_handoff, create_handoff, latest_handoff, scan_sensitive
from agent_handoff_bus.reliable_send import find_receipt


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

    def test_send_latest_ack(self) -> None:
        item = create_handoff(CreateInput(target_session="agent-b", source_session="agent-a", title="Hello", body="Review this."))
        self.assertEqual(item["status"], "PENDING")
        latest = latest_handoff("agent-b", pending_only=True)
        self.assertIsNotNone(latest)
        self.assertEqual(latest["id"], item["id"])
        acked = ack_handoff(item["id"], note="done")
        self.assertEqual(acked["status"], "ACKED")

    def test_secret_scanner_blocks(self) -> None:
        self.assertIn("openai_api_key", scan_sensitive("sk-" + "a" * 30))
        with self.assertRaises(ValueError):
            create_handoff(CreateInput(target_session="agent-b", title="bad", body="sk-" + "a" * 30))

    def test_auto_reply_receipt(self) -> None:
        item = create_handoff(CreateInput(target_session="agent-b", source_session="agent-a", title="Critical", body="Please receive."))
        sent = process_once(["agent-b"], fallback_source="agent-a")
        self.assertEqual(sent, 1)
        receipt = find_receipt(item["id"], "agent-a")
        self.assertIsNotNone(receipt)
        self.assertEqual(receipt["source_session"], "auto-reply")

    def test_body_file_written(self) -> None:
        item = create_handoff(CreateInput(target_session="agent-b", title="File", body="content"))
        path = Path(item["body_path"])
        self.assertTrue(path.exists())
        self.assertIn("content", path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
