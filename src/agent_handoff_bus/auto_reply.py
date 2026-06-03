from __future__ import annotations

import argparse
import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .core import CreateInput, bus_home, create_handoff, db_path, ensure_db, store_dir
from .event_watch import handoff_db_signature, wait_for_handoff_change

DEFAULT_SESSIONS = "agent-b"
DEFAULT_INTERVAL = 30.0
DEFAULT_FALLBACK_SOURCE = "agent-a"
SKIP_SOURCE_SESSIONS = {"auto-reply", "dispatcher", "agent-handoff-auto-reply"}
SCANNER_HINTS = (
    "PRIVATE KEY",
    "BEGIN ",
    "api_key",
    "apikey",
    "access_token",
    "auth_token",
    "password",
    "Bearer ",
    "sk-",
)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def state_path() -> Path:
    return bus_home() / "state" / "auto_reply_seen.json"


def log_path() -> Path:
    return bus_home() / "log" / "auto_reply.jsonl"


def watch_paths(sessions: list[str]) -> list[Path]:
    return [store_dir() / session for session in sessions]


def load_seen() -> dict[str, Any]:
    path = state_path()
    if not path.exists():
        return {"version": 1, "seen": {}}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {"version": 1, "seen": {}}


def save_seen(data: dict[str, Any]) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    tmp.replace(path)


def append_log(event: dict[str, Any]) -> None:
    path = log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def rows_for_sessions(sessions: list[str]) -> list[dict[str, Any]]:
    ensure_db()
    if not db_path().exists():
        return []
    placeholders = ",".join("?" for _ in sessions)
    sql = f"""
      SELECT id, created_at, source_session, target_session, workspace, title,
             body_path, priority, status, acked_at, sha256
      FROM handoffs
      WHERE status='PENDING' AND target_session IN ({placeholders})
      ORDER BY created_at ASC
      LIMIT 100
    """
    with sqlite3.connect(db_path()) as con:
        con.row_factory = sqlite3.Row
        return [dict(row) for row in con.execute(sql, sessions).fetchall()]


def body_has_secret_hint(body_path: str | None) -> bool:
    if not body_path:
        return False
    try:
        text = Path(body_path).read_text(encoding="utf-8", errors="replace")[:20000]
    except Exception:
        return False
    lowered = text.lower()
    return any(hint.lower() in lowered for hint in SCANNER_HINTS)


def reply_target(item: dict[str, Any], fallback: str) -> str | None:
    source = (item.get("source_session") or "").strip()
    target = (item.get("target_session") or "").strip()
    if source and source != target:
        return source
    if fallback and fallback != target:
        return fallback
    return None


def build_receipt_body(item: dict[str, Any]) -> str:
    secret_hint = body_has_secret_hint(item.get("body_path"))
    safety = "BLOCKED_SECRET_HINT: body not quoted" if secret_hint else "safe-summary-only"
    return f"""Status: RECEIVED
Original handoff: {item.get('id')}
Original target: {item.get('target_session')}
Original source: {item.get('source_session') or 'unknown'}
Priority: {item.get('priority')}
Title: {item.get('title')}
Workspace: {item.get('workspace') or 'unknown'}
Body path: {item.get('body_path') or 'unknown'}
Safety: {safety}

Auto-receipt fired. This confirms the dispatch reached the local receiver inbox.
This is not completion, not approval, and not an ACK of the original task.
The receiver must still inspect the handoff, send a substantive REPLY/BLOCKED result,
and ACK the original only after that response.

No UI paste/focus steal. No public upload/post. No OAuth. No paid action authorized.
"""


def send_receipt(item: dict[str, Any], fallback_source: str, dry_run: bool = False) -> dict[str, Any]:
    to_session = reply_target(item, fallback_source)
    if not to_session:
        return {"status": "SKIPPED", "reason": "no_reply_target"}
    title = f"AUTO-RECEIVED: {item.get('title') or item.get('id')}"
    body = build_receipt_body(item)
    if dry_run:
        return {"status": "DRY_RUN", "to": to_session, "title": title, "body": body}
    created = create_handoff(
        CreateInput(
            target_session=to_session,
            title=title,
            body=body,
            source_session="auto-reply",
            workspace=str(bus_home()),
            priority="high" if item.get("priority") in {"high", "urgent"} else "normal",
            metadata={
                "auto_reply_for": item.get("id"),
                "auto_reply_kind": "RECEIVED",
                "auto_reply_contract": "not-completion-not-ack",
            },
        )
    )
    return {"status": "SENT", "to": to_session, "receipt_handoff_id": created.get("id"), "receipt_body_path": created.get("body_path")}


def process_once(sessions: list[str], fallback_source: str, dry_run: bool = False, mark_seen: bool = True) -> int:
    state = load_seen()
    seen: dict[str, Any] = state.setdefault("seen", {})
    sent = 0
    for item in rows_for_sessions(sessions):
        handoff_id = item["id"]
        if handoff_id in seen:
            continue
        if (item.get("source_session") or "").strip() in SKIP_SOURCE_SESSIONS:
            result = {"status": "SKIPPED", "reason": "self-or-dispatcher-source"}
        else:
            result = send_receipt(item, fallback_source=fallback_source, dry_run=dry_run)
        event = {"ts": now(), "event": "auto_reply", "handoff": item, "result": result}
        append_log(event)
        print(json.dumps(event, ensure_ascii=False, sort_keys=True), flush=True)
        if dry_run or result.get("status") in {"SENT", "SKIPPED"}:
            if mark_seen:
                seen[handoff_id] = {
                    "ts": now(),
                    "target_session": item.get("target_session"),
                    "source_session": item.get("source_session"),
                    "title": item.get("title"),
                    "result_status": result.get("status"),
                    "receipt_handoff_id": result.get("receipt_handoff_id"),
                }
                save_seen(state)
            if result.get("status") == "SENT":
                sent += 1
    return sent


def suppress_existing(sessions: list[str]) -> None:
    state = load_seen()
    seen: dict[str, Any] = state.setdefault("seen", {})
    changed = False
    for item in rows_for_sessions(sessions):
        if item["id"] not in seen:
            seen[item["id"]] = {
                "ts": now(),
                "target_session": item.get("target_session"),
                "source_session": item.get("source_session"),
                "title": item.get("title"),
                "startup_suppressed": True,
            }
            changed = True
    if changed:
        save_seen(state)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Auto RECEIVED reply bridge for agent-handoff-bus")
    parser.add_argument("--sessions", default=DEFAULT_SESSIONS, help="comma-separated target sessions to monitor")
    parser.add_argument("--fallback-source", default=DEFAULT_FALLBACK_SOURCE, help="reply target when source_session is empty")
    parser.add_argument("--interval", type=float, default=DEFAULT_INTERVAL)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--include-existing", action="store_true", help="send receipts for existing pending handoffs not in seen state")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--watch-mode", choices=("event", "poll"), default="event")
    args = parser.parse_args(argv)

    sessions = [session.strip() for session in args.sessions.split(",") if session.strip()]
    if not sessions:
        raise SystemExit("no sessions configured")

    ensure_db()
    if not args.include_existing and not state_path().exists():
        suppress_existing(sessions)

    while True:
        extra = watch_paths(sessions) if args.watch_mode == "event" else []
        pre_sig = handoff_db_signature(db_path(), extra_paths=extra) if extra else None
        process_once(sessions, fallback_source=args.fallback_source, dry_run=args.dry_run)
        if args.once:
            return 0
        if args.watch_mode == "event":
            post_sig = handoff_db_signature(db_path(), extra_paths=extra)
            if pre_sig is not None and post_sig != pre_sig:
                time.sleep(0.05)
                continue
            wait_for_handoff_change(db_path(), timeout=max(args.interval, 0.5), previous_signature=post_sig, extra_paths=extra)
        else:
            time.sleep(max(args.interval, 0.5))


if __name__ == "__main__":
    raise SystemExit(main())
