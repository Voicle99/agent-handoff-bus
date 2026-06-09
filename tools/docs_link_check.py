#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse

SCHEMA = "agent-handoff-bus/docs-link-check/v1"

LINK_RE = re.compile(r"!?\[[^\]\n]*\]\(([^)\n]+)\)")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
SKIP_DIRS = {
    ".agent-handoff-bus",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "dist",
    "venv",
}


def _iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts):
            continue
        files.append(path)
    return sorted(files)


def _strip_optional_title(raw_target: str) -> str:
    target = raw_target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")].strip()
    return target.split()[0] if target.split() else ""


def _is_external_or_generated(target: str) -> bool:
    if not target or target.startswith("//"):
        return True
    parsed = urlparse(target)
    if parsed.scheme:
        return True
    return False


def _split_target(target: str) -> tuple[str, str]:
    without_query = target.split("?", 1)[0]
    path_part, marker, anchor = without_query.partition("#")
    return unquote(path_part), unquote(anchor) if marker else ""


def _slugify_heading(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"[`*_~]", "", text).strip().lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text


def _heading_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8", errors="replace")
    anchors: set[str] = set()
    seen: dict[str, int] = {}
    in_fence = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        match = HEADING_RE.match(line)
        if not match:
            continue
        base = _slugify_heading(match.group(2))
        if not base:
            continue
        count = seen.get(base, 0)
        seen[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def _iter_links(path: Path) -> list[dict[str, Any]]:
    links: list[dict[str, Any]] = []
    in_fence = False
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for match in LINK_RE.finditer(line):
            raw_target = match.group(1)
            target = _strip_optional_title(raw_target)
            if _is_external_or_generated(target):
                continue
            links.append({"line": line_number, "raw": raw_target, "target": target})
    return links


def _safe_relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def check_docs_links(root: Path) -> tuple[int, dict[str, Any]]:
    root = root.expanduser().resolve()
    if not root.is_dir():
        return 2, {
            "status": "ERROR",
            "schema": SCHEMA,
            "summary": "root directory not found",
            "root": str(root),
            "public_action_taken": False,
        }

    markdown_files = _iter_markdown_files(root)
    findings: list[dict[str, Any]] = []
    checked_links = 0
    anchor_cache: dict[Path, set[str]] = {}

    for source in markdown_files:
        for link in _iter_links(source):
            checked_links += 1
            path_part, anchor = _split_target(link["target"])
            target_path = source if not path_part else (source.parent / path_part).resolve()
            base_finding = {
                "source": _safe_relative(source, root),
                "line": link["line"],
                "link": link["target"],
            }

            try:
                target_path.relative_to(root)
            except ValueError:
                findings.append({**base_finding, "kind": "target_outside_repo", "target": str(target_path)})
                continue

            if not target_path.exists():
                findings.append(
                    {**base_finding, "kind": "missing_target", "target": _safe_relative(target_path, root)}
                )
                continue

            if anchor:
                if not target_path.is_file() or target_path.suffix.lower() != ".md":
                    findings.append(
                        {**base_finding, "kind": "anchor_target_not_markdown", "target": _safe_relative(target_path, root)}
                    )
                    continue
                anchors = anchor_cache.setdefault(target_path, _heading_anchors(target_path))
                if anchor.lower() not in anchors:
                    findings.append(
                        {
                            **base_finding,
                            "kind": "missing_anchor",
                            "target": _safe_relative(target_path, root),
                            "anchor": anchor,
                        }
                    )

    if findings:
        return 1, {
            "status": "FAIL_DOCS_LINK_CHECK",
            "schema": SCHEMA,
            "summary": "one or more local markdown links are broken",
            "root": str(root),
            "checked_files": [_safe_relative(path, root) for path in markdown_files],
            "checked_links": checked_links,
            "findings": findings,
            "public_action_taken": False,
        }

    return 0, {
        "status": "PASS",
        "schema": SCHEMA,
        "summary": "local markdown links and anchors resolve",
        "root": str(root),
        "checked_files": [_safe_relative(path, root) for path in markdown_files],
        "checked_links": checked_links,
        "public_action_taken": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dependency-free local Markdown relative-link checker.")
    parser.add_argument("--root", default=".", help="Repository root to scan.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code, payload = check_docs_links(Path(args.root))
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
