from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path
from typing import Any

from .core import (
    DEFAULT_PORT,
    SCHEMA,
    CreateInput,
    ack_handoff,
    bus_home,
    compact_item,
    create_handoff,
    db_path,
    doctor,
    json_out,
    latest_handoff,
    list_handoffs,
    get_handoff,
    serve,
    store_dir,
)


def read_body_from_args(args: argparse.Namespace) -> tuple[str, str | None]:
    if getattr(args, "file", None):
        path = Path(args.file).expanduser().resolve()
        if not path.exists():
            raise SystemExit(f"file not found: {path}")
        return path.read_text(encoding="utf-8", errors="replace"), str(path)
    if getattr(args, "body", None) == "-":
        return sys.stdin.read(), None
    if getattr(args, "body", None):
        return args.body, None
    raise SystemExit("one of --file or --body is required")


def cmd_send(args: argparse.Namespace) -> int:
    body, source_file = read_body_from_args(args)
    metadata: dict[str, Any] = {}
    if source_file:
        metadata["source_file"] = source_file
    for item in args.meta:
        if "=" in item:
            key, value = item.split("=", 1)
            metadata[key] = value
    item = create_handoff(
        CreateInput(
            target_session=args.to,
            title=args.title or (Path(source_file).name if source_file else "Agent handoff"),
            body=body,
            source_session=args.source_session,
            workspace=args.workspace or os.getcwd(),
            priority=args.priority,
            metadata=metadata,
            allow_sensitive=args.allow_sensitive,
        )
    )
    json_out({"status": "SENT", "handoff": compact_item(item)})
    return 0


def cmd_latest(args: argparse.Namespace) -> int:
    item = latest_handoff(args.for_session, pending_only=args.pending_only)
    if not item:
        json_out({"status": "EMPTY", "target_session": args.for_session})
        return 1 if args.require else 0
    if args.plain:
        print(Path(item["body_path"]).read_text(encoding="utf-8", errors="replace"))
    else:
        json_out({"status": "FOUND", "handoff": item if args.full else compact_item(item)})
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    rows = list_handoffs(target_session=args.for_session, status=args.status, limit=args.limit)
    json_out({"status": "OK", "count": len(rows), "handoffs": [compact_item(row) for row in rows]})
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    item = get_handoff(args.id)
    if not item:
        json_out({"status": "NOT_FOUND", "id": args.id})
        return 1
    if args.plain:
        print(Path(item["body_path"]).read_text(encoding="utf-8", errors="replace"))
    else:
        json_out({"status": "FOUND", "handoff": item if args.full else compact_item(item)})
    return 0


def cmd_ack(args: argparse.Namespace) -> int:
    item = ack_handoff(args.id, note=args.note or "")
    json_out({"status": "ACKED", "handoff": compact_item(item)})
    return 0


def cmd_watch(args: argparse.Namespace) -> int:
    print({"status": "WATCHING", "target_session": args.for_session, "pending_only": True}, flush=True)
    seen = set() if args.include_existing else {row["id"] for row in list_handoffs(target_session=args.for_session, limit=100)}
    started = time.time()
    while True:
        rows = list_handoffs(target_session=args.for_session, status="PENDING", limit=20)
        emitted = False
        for item in reversed(rows):
            if item["id"] not in seen:
                seen.add(item["id"])
                emitted = True
                json_out({"status": "NEW", "handoff": compact_item(item)})
                if args.print_body:
                    print(Path(item["body_path"]).read_text(encoding="utf-8", errors="replace"), flush=True)
                if args.once:
                    return 0
        if args.once and args.timeout <= 0 and not emitted:
            return 1
        if args.timeout > 0 and time.time() - started >= args.timeout:
            return 0
        time.sleep(max(args.interval, 0.1))


def cmd_status(args: argparse.Namespace) -> int:
    latest = latest_handoff(args.session) if args.session else None
    pending = list_handoffs(target_session=args.session, status="PENDING", limit=1000) if args.session else list_handoffs(status="PENDING", limit=1000)
    json_out({"status": "OK", "home": str(bus_home()), "db": str(db_path()), "store": str(store_dir()), "session": args.session, "pending_count": len(pending), "latest": compact_item(latest)})
    return 0


def cmd_doctor(_args: argparse.Namespace) -> int:
    status, checks = doctor()
    json_out({"status": status, "schema": SCHEMA, "checks": checks})
    return 0 if status == "PASS" else 1


def cmd_serve(args: argparse.Namespace) -> int:
    serve(host=args.host, port=args.port, quiet=args.quiet)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Local-first handoff bus for AI agents")
    sub = parser.add_subparsers(dest="cmd", required=True)

    send = sub.add_parser("send", help="create a handoff")
    send.add_argument("--to", required=True, help="target session id")
    send.add_argument("--from", dest="source_session", help="source session id")
    send.add_argument("--file")
    send.add_argument("--body")
    send.add_argument("--title")
    send.add_argument("--workspace")
    send.add_argument("--priority", default="normal", choices=["low", "normal", "high", "urgent"])
    send.add_argument("--meta", action="append", default=[])
    send.add_argument("--allow-sensitive", action="store_true", help="bypass secret scanner; not recommended")
    send.set_defaults(func=cmd_send)

    latest = sub.add_parser("latest", help="show latest handoff for a session")
    latest.add_argument("--for", dest="for_session", required=True)
    latest.add_argument("--pending-only", action="store_true")
    latest.add_argument("--plain", action="store_true")
    latest.add_argument("--full", action="store_true")
    latest.add_argument("--require", action="store_true")
    latest.set_defaults(func=cmd_latest)

    list_cmd = sub.add_parser("list", help="list handoffs")
    list_cmd.add_argument("--for", dest="for_session")
    list_cmd.add_argument("--status")
    list_cmd.add_argument("--limit", type=int, default=20)
    list_cmd.set_defaults(func=cmd_list)

    show = sub.add_parser("show", help="show one handoff")
    show.add_argument("id")
    show.add_argument("--plain", action="store_true")
    show.add_argument("--full", action="store_true")
    show.set_defaults(func=cmd_show)

    ack = sub.add_parser("ack", help="acknowledge one handoff")
    ack.add_argument("id")
    ack.add_argument("--note", default="")
    ack.set_defaults(func=cmd_ack)

    watch = sub.add_parser("watch", help="poll for new pending handoffs")
    watch.add_argument("--for", dest="for_session", required=True)
    watch.add_argument("--once", action="store_true")
    watch.add_argument("--include-existing", action="store_true")
    watch.add_argument("--print-body", action="store_true")
    watch.add_argument("--interval", type=float, default=1.0)
    watch.add_argument("--timeout", type=float, default=0.0, help="0 means no timeout")
    watch.set_defaults(func=cmd_watch)

    status = sub.add_parser("status", help="bus or session status")
    status.add_argument("--session")
    status.set_defaults(func=cmd_status)

    doctor_cmd = sub.add_parser("doctor", help="verify local install")
    doctor_cmd.set_defaults(func=cmd_doctor)

    serve_cmd = sub.add_parser("serve", help="start localhost API server")
    serve_cmd.add_argument("--host", default="127.0.0.1")
    serve_cmd.add_argument("--port", type=int, default=DEFAULT_PORT)
    serve_cmd.add_argument("--quiet", action="store_true")
    serve_cmd.set_defaults(func=cmd_serve)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except BrokenPipeError:
        return 0
    except Exception as exc:
        json_out({"status": "ERROR", "error": str(exc)})
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
