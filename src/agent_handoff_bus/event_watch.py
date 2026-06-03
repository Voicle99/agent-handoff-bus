from __future__ import annotations

import os
import select
import time
from pathlib import Path
from typing import Iterable

Signature = tuple[tuple[str, int, int, int], ...]


def watched_paths(db_path: Path | str, extra_paths: Iterable[Path | str] = ()) -> list[Path]:
    db = Path(db_path)
    extras = [Path(p) for p in extra_paths]
    candidates = [*extras, db] if extras else [db]
    out: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if path.exists():
            out.append(path)
    return out


def handoff_db_signature(db_path: Path | str, extra_paths: Iterable[Path | str] = ()) -> Signature:
    rows: list[tuple[str, int, int, int]] = []
    for path in watched_paths(db_path, extra_paths=extra_paths):
        try:
            stat = path.stat()
        except FileNotFoundError:
            continue
        rows.append((str(path), int(stat.st_ino), int(stat.st_mtime_ns), int(stat.st_size)))
    return tuple(rows)


def _open_watch_fds(paths: Iterable[Path]) -> list[int]:
    fds: list[int] = []
    flags = getattr(os, "O_EVTONLY", os.O_RDONLY)
    for path in paths:
        try:
            fds.append(os.open(path, flags))
        except (FileNotFoundError, PermissionError, OSError):
            continue
    return fds


def wait_for_handoff_change(
    db_path: Path | str,
    timeout: float,
    previous_signature: Signature | None = None,
    extra_paths: Iterable[Path | str] = (),
) -> str:
    """Wait until the handoff DB/store changes, or timeout.

    Uses kqueue on macOS and sleep fallback elsewhere. The caller must always
    re-query after this function returns; events are only a wake signal.
    """
    timeout = max(float(timeout), 0.05)
    db = Path(db_path)
    if not hasattr(select, "kqueue"):
        time.sleep(timeout)
        return "SLEEP_FALLBACK"

    paths = watched_paths(db, extra_paths=extra_paths)
    if not paths:
        time.sleep(min(timeout, 0.5))
        return "NO_WATCH_PATH"

    kqueue = select.kqueue()
    fds = _open_watch_fds(paths)
    try:
        if not fds:
            time.sleep(min(timeout, 0.5))
            return "NO_WATCH_PATH"
        notes = select.KQ_NOTE_WRITE | select.KQ_NOTE_EXTEND | select.KQ_NOTE_RENAME | select.KQ_NOTE_DELETE
        changes = [
            select.kevent(fd, filter=select.KQ_FILTER_VNODE, flags=select.KQ_EV_ADD | select.KQ_EV_ENABLE | select.KQ_EV_CLEAR, fflags=notes)
            for fd in fds
        ]
        kqueue.control(changes, 0, 0)
        if previous_signature is not None and handoff_db_signature(db, extra_paths=extra_paths) != previous_signature:
            time.sleep(0.05)
            return "CHANGED_BEFORE_WAIT"
        events = kqueue.control(None, 1, timeout)
        if events:
            time.sleep(0.05)
            return "EVENT"
        return "TIMEOUT"
    finally:
        try:
            kqueue.close()
        except Exception:
            pass
        for fd in fds:
            try:
                os.close(fd)
            except OSError:
                pass
