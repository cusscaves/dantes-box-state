"""Shared filesystem snapshot helpers for Dante state + workflow.

Canonical home: dantes-box-state. Workflow imports from sibling checkout.
"""

from __future__ import annotations

import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

# Paths/names never hashed into a workspace snapshot
DEFAULT_SKIP_NAMES = frozenset(
    {
        ".session_state.json",
        ".DS_Store",
    }
)
DEFAULT_SKIP_DIR_NAMES = frozenset(
    {
        ".git",
        "recordings",
        "__pycache__",
        "inbox",
        ".venv",
        "node_modules",
    }
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_hash(path: Path) -> str | None:
    if not path.is_file():
        return None
    h = hashlib.sha256()
    try:
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
    except OSError:
        return None
    return h.hexdigest()


def snapshot_files(
    root: Path,
    *,
    skip_names: frozenset[str] = DEFAULT_SKIP_NAMES,
    skip_dir_names: frozenset[str] = DEFAULT_SKIP_DIR_NAMES,
) -> dict[str, str]:
    """Map relative path → sha256 for files under root."""
    out: dict[str, str] = {}
    root = Path(root)
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if any(part in skip_dir_names for part in p.parts):
            continue
        if p.name in skip_names:
            continue
        rel = str(p.relative_to(root))
        digest = file_hash(p)
        if digest:
            out[rel] = digest
    return out


def snapshot_processes() -> list[str]:
    try:
        proc = subprocess.run(
            ["ps", "-axo", "comm="],
            capture_output=True,
            text=True,
            check=False,
        )
        return sorted({line.strip() for line in proc.stdout.splitlines() if line.strip()})
    except OSError:
        return []


def make_snapshot(watch: Path) -> dict:
    watch = Path(watch)
    return {
        "ts": utc_now(),
        "watch": str(watch.resolve()),
        "files": snapshot_files(watch),
        "processes": snapshot_processes(),
    }


def diff_file_maps(before: dict[str, str], after: dict[str, str]) -> dict[str, list[str]]:
    return {
        "created": sorted(set(after) - set(before)),
        "deleted": sorted(set(before) - set(after)),
        "changed": sorted(p for p in set(before) & set(after) if before[p] != after[p]),
    }
