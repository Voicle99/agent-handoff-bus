#!/usr/bin/env python3
"""Build local release artifacts and checksums.

This script is local-only. It does not upload to PyPI, create GitHub releases,
tag commits, or perform public actions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build release artifacts and SHA256SUMS")
    parser.add_argument("--dist-dir", default="dist")
    parser.add_argument("--root", default=".")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    dist_dir = (root / args.dist_dir).resolve()
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    dist_dir.mkdir(parents=True, exist_ok=True)

    build = run([sys.executable, "-m", "build", "--outdir", str(dist_dir)], root)
    if build.returncode != 0:
        print(json.dumps({"status": "FAIL_BUILD", "stdout": build.stdout, "stderr": build.stderr}, ensure_ascii=False, indent=2))
        return build.returncode or 1

    artifacts = sorted(p for p in dist_dir.iterdir() if p.is_file() and p.name != "SHA256SUMS")
    if not artifacts:
        print(json.dumps({"status": "FAIL_NO_ARTIFACTS", "dist_dir": str(dist_dir)}, ensure_ascii=False, indent=2))
        return 1

    twine = run([sys.executable, "-m", "twine", "check", *map(str, artifacts)], root)
    if twine.returncode != 0:
        print(json.dumps({"status": "FAIL_TWINE_CHECK", "stdout": twine.stdout, "stderr": twine.stderr}, ensure_ascii=False, indent=2))
        return twine.returncode or 1

    checksum_lines = [f"{sha256(path)}  {path.name}" for path in artifacts]
    checksum_path = dist_dir / "SHA256SUMS"
    checksum_path.write_text("\n".join(checksum_lines) + "\n", encoding="utf-8")

    artifact_entries = [
        {"file": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)} for path in artifacts
    ]
    artifact_entries.append(
        {"file": checksum_path.name, "bytes": checksum_path.stat().st_size, "sha256": sha256(checksum_path)}
    )

    manifest = {
        "schema": "agent-handoff-bus/release-artifacts/v1",
        "status": "PASS",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "dist_dir": str(dist_dir),
        "public_action_taken": False,
        "artifacts": artifact_entries,
        "checksum_file": checksum_path.name,
        "manifest_file": "release-manifest.json",
    }
    manifest_path = dist_dir / "release-manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    manifest["manifest_file_sha256"] = sha256(manifest_path)
    print(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
