from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any

from .core import CreateInput, ack_handoff, create_handoff, db_path, ensure_db


def row_to_compact(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "source_session": row["source_session"],
        "target_session": row["target_session"],
        "workspace": row["workspace"],
        "title": row["title"],
        "body_path": row["body_path"],
        "priority": row["priority"],
        "status": row["status"],
        "acked_at": row["acked_at"],
        "sha256": row["sha256"],
    }


def find_receipt(original_id: str, source_session: str) -> dict[str, Any] | None:
    ensure_db()
    with sqlite3.connect(db_path()) as con:
        con.row_factory = sqlite3.Row
        rows = con.execute(
            """
            SELECT *
            FROM handoffs
            WHERE target_session=?
              AND source_session='auto-reply'
              AND status='PENDING'
            ORDER BY created_at DESC
            LIMIT 50
            """,
            (source_session,),
        ).fetchall()
    for row in rows:
        try:
            meta = json.loads(row["metadata_json"] or "{}")
        except Exception:
            meta = {}
        if meta.get("auto_reply_for") == original_id:
            item = row_to_compact(row)
            item["metadata"] = meta
            return item
    return None


def read_body(args: argparse.Namespace) -> tuple[str, str | None]:
    if args.file:
        path = Path(args.file).expanduser().resolve()
        return path.read_text(encoding="utf-8", errors="replace"), str(path)
    if args.body == "-":
        return sys.stdin.read(), None
    if args.body:
        return args.body, None
    raise SystemExit("one of --file or --body is required")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Reliable handoff send with auto-receipt wait")
    parser.add_argument("--to", default="agent-b")
    parser.add_argument("--from", dest="source_session", default=os.environ.get("AGENT_HANDOFF_SESSION") or "agent-a")
    parser.add_argument("--file")
    parser.add_argument("--body")
    parser.add_argument("--title", default="Reliable handoff")
    parser.add_argument("--workspace", default=os.getcwd())
    parser.add_argument("--priority", default="high", choices=["low", "normal", "high", "urgent"])
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--interval", type=float, default=0.5)
    parser.add_argument("--ack-receipt", action="store_true", help="ack the AUTO-RECEIVED handoff after observing it")
    args = parser.parse_args(argv)

    ensure_db()
    body, source_file = read_body(args)
    metadata: dict[str, Any] = {"reliable_send": True}
    if source_file:
        metadata["source_file"] = source_file
    original = create_handoff(
        CreateInput(
            target_session=args.to,
            title=args.title,
            body=body,
            source_session=args.source_session,
            workspace=args.workspace,
            priority=args.priority,
            metadata=metadata,
        )
    )
    original_id = original["id"]
    started = time.time()
    receipt = None
    while time.time() - started <= args.timeout:
        receipt = find_receipt(original_id, args.source_session)
        if receipt:
            break
        time.sleep(max(args.interval, 0.1))

    if not receipt:
        print(
            json.dumps(
                {
                    "status": "BLOCKED_NO_AUTO_RECEIPT",
                    "original_handoff": {
                        "id": original_id,
                        "target_session": args.to,
                        "source_session": args.source_session,
                        "body_path": original.get("body_path"),
                    },
                    "timeout_seconds": args.timeout,
                    "next_checks": [
                        "agent-handoff doctor",
                        "agent-handoff-auto-reply --sessions <receiver-session>",
                        "tail ${AGENT_HANDOFF_HOME:-~/.agent-handoff-bus}/log/auto_reply.jsonl",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 3

    acked = None
    if args.ack_receipt:
        acked = ack_handoff(receipt["id"], note=f"observed by reliable send for {original_id}")
    print(
        json.dumps(
            {
                "status": "PASS",
                "original_handoff": {
                    "id": original_id,
                    "target_session": args.to,
                    "source_session": args.source_session,
                    "body_path": original.get("body_path"),
                },
                "receipt_handoff": receipt,
                "latency_seconds": round(time.time() - started, 3),
                "receipt_acked": bool(acked),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
