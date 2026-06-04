from __future__ import annotations

import hashlib
from contextlib import closing
import http.server
import json
import os
import re
import shutil
import signal
import sqlite3
import sys
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

SCHEMA = "agent-handoff-bus/v1"
DEFAULT_PORT = 8791
LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
DEFAULT_HOME_ENV = "AGENT_HANDOFF_HOME"
DEFAULT_SESSION_ENV = "AGENT_HANDOFF_SESSION"

SECRET_PATTERNS = [
    ("openai_api_key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
    ("aws_access_key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("private_key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("github_token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{20,}")),
    ("bearer_token", re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]{24,}", re.I)),
    (
        "generic_secret_assignment",
        re.compile(r"(?i)(api[_-]?key|secret|access[_-]?token|auth[_-]?token|password)\s*[:=]\s*['\"]?[^\s'\"]{16,}"),
    ),
]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def bus_home() -> Path:
    return Path(os.environ.get(DEFAULT_HOME_ENV) or Path.home() / ".agent-handoff-bus").expanduser().resolve()


def db_path(home: Path | None = None) -> Path:
    return (home or bus_home()) / "state" / "handoffs.sqlite"


def store_dir(home: Path | None = None) -> Path:
    return (home or bus_home()) / "store"


def log_dir(home: Path | None = None) -> Path:
    return (home or bus_home()) / "log"


def safe_session(value: str) -> str:
    session = (value or "unassigned").strip()
    session = re.sub(r"[^A-Za-z0-9_.:-]+", "-", session).strip("-")
    return session or "unassigned"


def short_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8", errors="replace")).hexdigest()


def scan_sensitive(text: str) -> list[str]:
    hits: list[str] = []
    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            hits.append(name)
    return sorted(set(hits))


def ensure_db(home: Path | None = None) -> Path:
    home = home or bus_home()
    (home / "state").mkdir(parents=True, exist_ok=True)
    store_dir(home).mkdir(parents=True, exist_ok=True)
    log_dir(home).mkdir(parents=True, exist_ok=True)
    path = db_path(home)
    with closing(sqlite3.connect(path)) as con:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS handoffs (
              id TEXT PRIMARY KEY,
              schema TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              source_session TEXT,
              target_session TEXT NOT NULL,
              workspace TEXT,
              title TEXT NOT NULL,
              body TEXT NOT NULL,
              body_path TEXT NOT NULL,
              body_format TEXT NOT NULL,
              priority TEXT NOT NULL,
              status TEXT NOT NULL,
              acked_at TEXT,
              ack_note TEXT,
              metadata_json TEXT NOT NULL,
              sha256 TEXT NOT NULL
            )
            """
        )
        con.execute("CREATE INDEX IF NOT EXISTS idx_handoffs_target_created ON handoffs(target_session, created_at DESC)")
        con.execute("CREATE INDEX IF NOT EXISTS idx_handoffs_status ON handoffs(status)")
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
              event_id TEXT PRIMARY KEY,
              handoff_id TEXT NOT NULL,
              ts TEXT NOT NULL,
              event TEXT NOT NULL,
              data_json TEXT NOT NULL
            )
            """
        )
        con.commit()
    return path


def connect(home: Path | None = None) -> sqlite3.Connection:
    ensure_db(home)
    con = sqlite3.connect(db_path(home))
    con.row_factory = sqlite3.Row
    return con


def add_event(con: sqlite3.Connection, handoff_id: str, event: str, data: dict[str, Any]) -> None:
    con.execute(
        "INSERT INTO events(event_id, handoff_id, ts, event, data_json) VALUES(?,?,?,?,?)",
        (str(uuid.uuid4()), handoff_id, utc_now(), event, json.dumps(data, ensure_ascii=False, sort_keys=True)),
    )


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    data = dict(row)
    try:
        data["metadata"] = json.loads(data.pop("metadata_json") or "{}")
    except json.JSONDecodeError:
        data["metadata"] = {}
    return data


def compact_item(item: dict[str, Any] | None) -> dict[str, Any] | None:
    if item is None:
        return None
    keys = [
        "id",
        "created_at",
        "source_session",
        "target_session",
        "workspace",
        "title",
        "body_path",
        "priority",
        "status",
        "acked_at",
        "sha256",
    ]
    return {k: item.get(k) for k in keys}


def write_handoff_file(home: Path, handoff_id: str, target_session: str, title: str, body: str) -> Path:
    target = safe_session(target_session)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = store_dir(home) / target
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"{timestamp}-{handoff_id[:8]}.md"
    out.write_text(f"# {title}\n\n{body.rstrip()}\n", encoding="utf-8")
    return out


@dataclass
class CreateInput:
    target_session: str
    title: str
    body: str
    source_session: str | None = None
    workspace: str | None = None
    body_format: str = "markdown"
    priority: str = "normal"
    metadata: dict[str, Any] | None = None
    allow_sensitive: bool = False


def create_handoff(inp: CreateInput) -> dict[str, Any]:
    if not inp.target_session.strip():
        raise ValueError("target_session required")
    if not inp.body.strip():
        raise ValueError("body required")
    hits = scan_sensitive(inp.body)
    if hits and not inp.allow_sensitive:
        raise ValueError(f"sensitive material detected: {', '.join(hits)}")

    home = bus_home()
    ensure_db(home)
    handoff_id = str(uuid.uuid4())
    now = utc_now()
    title = inp.title.strip() or "Agent handoff"
    body_hash = short_hash(inp.body)
    body_path = write_handoff_file(home, handoff_id, inp.target_session, title, inp.body)
    metadata = inp.metadata or {}
    metadata.setdefault("sensitive_scan_hits", hits)

    with closing(connect(home)) as con:
        con.execute(
            """
            INSERT INTO handoffs(id, schema, created_at, updated_at, source_session, target_session,
              workspace, title, body, body_path, body_format, priority, status, acked_at, ack_note,
              metadata_json, sha256)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                handoff_id,
                SCHEMA,
                now,
                now,
                inp.source_session,
                inp.target_session,
                inp.workspace,
                title,
                inp.body,
                str(body_path),
                inp.body_format,
                inp.priority,
                "PENDING",
                None,
                None,
                json.dumps(metadata, ensure_ascii=False, sort_keys=True),
                body_hash,
            ),
        )
        add_event(con, handoff_id, "created", {"target_session": inp.target_session, "title": title})
        con.commit()
        row = con.execute("SELECT * FROM handoffs WHERE id=?", (handoff_id,)).fetchone()
    return row_to_dict(row)


def list_handoffs(target_session: str | None = None, status: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
    ensure_db()
    clauses: list[str] = []
    params: list[Any] = []
    if target_session:
        clauses.append("target_session=?")
        params.append(target_session)
    if status:
        clauses.append("status=?")
        params.append(status)
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    params.append(max(1, min(int(limit), 1000)))
    with closing(connect()) as con:
        rows = con.execute(f"SELECT * FROM handoffs{where} ORDER BY created_at DESC LIMIT ?", params).fetchall()
    return [row_to_dict(row) for row in rows]


def get_handoff(handoff_id: str) -> dict[str, Any] | None:
    ensure_db()
    with closing(connect()) as con:
        row = con.execute("SELECT * FROM handoffs WHERE id=?", (handoff_id,)).fetchone()
    return row_to_dict(row) if row else None


def latest_handoff(target_session: str, pending_only: bool = False) -> dict[str, Any] | None:
    rows = list_handoffs(target_session=target_session, status="PENDING" if pending_only else None, limit=1)
    return rows[0] if rows else None


def ack_handoff(handoff_id: str, note: str = "") -> dict[str, Any]:
    ensure_db()
    now = utc_now()
    with closing(connect()) as con:
        row = con.execute("SELECT * FROM handoffs WHERE id=?", (handoff_id,)).fetchone()
        if not row:
            raise ValueError(f"handoff not found: {handoff_id}")
        con.execute(
            "UPDATE handoffs SET status='ACKED', acked_at=?, ack_note=?, updated_at=? WHERE id=?",
            (now, note, now, handoff_id),
        )
        add_event(con, handoff_id, "acked", {"note": note})
        con.commit()
        row2 = con.execute("SELECT * FROM handoffs WHERE id=?", (handoff_id,)).fetchone()
    return row_to_dict(row2)


def json_out(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2))


class HandoffHTTPHandler(http.server.BaseHTTPRequestHandler):
    server_version = "AgentHandoffBus/0.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        if not getattr(self.server, "quiet", False):
            sys.stderr.write("%s - - [%s] %s\n" % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def _json(self, code: int, obj: Any) -> None:
        payload = json.dumps(obj, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid json: {exc}") from exc

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        qs = parse_qs(parsed.query)
        try:
            if parsed.path == "/health":
                self._json(200, {"status": "OK", "schema": SCHEMA, "home": str(bus_home()), "db": str(db_path()), "store": str(store_dir())})
                return
            if parsed.path == "/handoffs":
                rows = list_handoffs(qs.get("target_session", [None])[0], qs.get("status", [None])[0], int(qs.get("limit", [20])[0]))
                self._json(200, {"handoffs": [compact_item(row) for row in rows]})
                return
            if parsed.path == "/handoffs/latest":
                target = qs.get("target_session", [""])[0]
                if not target:
                    self._json(400, {"error": "target_session required"})
                    return
                item = latest_handoff(target, pending_only=qs.get("pending_only", ["false"])[0].lower() == "true")
                self._json(200, {"handoff": item})
                return
            if parsed.path.startswith("/handoffs/"):
                handoff_id = parsed.path.split("/", 2)[2]
                item = get_handoff(handoff_id)
                self._json(200 if item else 404, {"handoff": item} if item else {"error": "not found"})
                return
            if parsed.path.startswith("/sessions/") and parsed.path.endswith("/status"):
                target = parsed.path.split("/")[2]
                pending = list_handoffs(target_session=target, status="PENDING", limit=100)
                latest = latest_handoff(target_session=target)
                self._json(200, {"session": target, "pending_count": len(pending), "latest": compact_item(latest)})
                return
            self._json(404, {"error": "not found"})
        except Exception as exc:  # defensive API surface
            self._json(500, {"error": str(exc)})

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/handoffs":
                data = self._read_json()
                body = data.get("body")
                source_file = data.get("file") or data.get("body_path")
                if body is None and source_file:
                    path = Path(str(source_file)).expanduser().resolve()
                    body = path.read_text(encoding="utf-8", errors="replace")
                    data.setdefault("metadata", {})["source_file"] = str(path)
                item = create_handoff(
                    CreateInput(
                        target_session=str(data.get("target_session") or ""),
                        title=str(data.get("title") or "Agent handoff"),
                        body=str(body or ""),
                        source_session=data.get("source_session"),
                        workspace=data.get("workspace"),
                        body_format=str(data.get("body_format") or "markdown"),
                        priority=str(data.get("priority") or "normal"),
                        metadata=data.get("metadata") or {},
                        allow_sensitive=bool(data.get("allow_sensitive")),
                    )
                )
                self._json(201, {"handoff": compact_item(item)})
                return
            if parsed.path.startswith("/handoffs/") and parsed.path.endswith("/ack"):
                handoff_id = parsed.path.split("/")[2]
                data = self._read_json()
                item = ack_handoff(handoff_id, note=str(data.get("note") or ""))
                self._json(200, {"handoff": compact_item(item)})
                return
            self._json(404, {"error": "not found"})
        except Exception as exc:
            self._json(400, {"error": str(exc)})


class ThreadingHTTPServer(http.server.ThreadingHTTPServer):
    quiet: bool = False


def serve(host: str = "127.0.0.1", port: int = DEFAULT_PORT, quiet: bool = False) -> None:
    if host not in LOOPBACK_HOSTS:
        raise ValueError(f"refusing non-loopback host: {host}")
    ensure_db()
    server = ThreadingHTTPServer((host, int(port)), HandoffHTTPHandler)
    server.quiet = quiet

    def stop(_signum: int, _frame: Any) -> None:
        server.shutdown()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    print(json.dumps({"status": "SERVING", "url": f"http://{host}:{port}", "schema": SCHEMA, "home": str(bus_home())}, ensure_ascii=False), flush=True)
    server.serve_forever()


def doctor() -> tuple[str, list[dict[str, Any]]]:
    path = ensure_db()
    checks: list[dict[str, Any]] = [
        {"id": "home_exists", "status": "PASS" if bus_home().exists() else "BLOCKED", "path": str(bus_home())},
        {"id": "db_exists", "status": "PASS" if path.exists() else "BLOCKED", "path": str(path)},
        {"id": "store_exists", "status": "PASS" if store_dir().exists() else "BLOCKED", "path": str(store_dir())},
        {"id": "cli_available", "status": "PASS" if shutil.which("agent-handoff") else "HOLD", "path": shutil.which("agent-handoff")},
        {"id": "secret_scanner", "status": "PASS" if not scan_sensitive("hello safe handoff") else "BLOCKED"},
    ]
    status = "PASS" if all(c["status"] in {"PASS", "HOLD"} for c in checks) else "BLOCKED"
    return status, checks
