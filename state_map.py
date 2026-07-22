#!/usr/bin/env python3
"""Environment state mapping — pre/post snapshots for Dante workflow replay."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_files(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not root.exists():
        return out
    for p in sorted(root.rglob("*")):
        if not p.is_file():
            continue
        if ".git" in p.parts:
            continue
        rel = str(p.relative_to(root))
        try:
            out[rel] = file_hash(p)
        except OSError:
            continue
    return out


def snapshot_processes() -> list[str]:
    try:
        proc = subprocess.run(
            ["ps", "-axo", "comm="], capture_output=True, text=True, check=False
        )
        names = sorted({line.strip() for line in proc.stdout.splitlines() if line.strip()})
        return names
    except OSError:
        return []


def make_snapshot(watch: Path) -> dict:
    return {
        "ts": utc_now(),
        "watch": str(watch.resolve()),
        "files": snapshot_files(watch),
        "processes": snapshot_processes(),
    }


def cmd_snapshot(args: argparse.Namespace) -> int:
    snap = make_snapshot(Path(args.watch))
    out = Path(args.out)
    out.write_text(json.dumps(snap, indent=2))
    print(f"wrote {out} ({len(snap['files'])} files, {len(snap['processes'])} processes)")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    a = json.loads(Path(args.before).read_text())
    b = json.loads(Path(args.after).read_text())
    fa, fb = a.get("files", {}), b.get("files", {})
    pa, pb = set(a.get("processes", [])), set(b.get("processes", []))

    report = {
        "created": sorted(set(fb) - set(fa)),
        "deleted": sorted(set(fa) - set(fb)),
        "changed": sorted(p for p in set(fa) & set(fb) if fa[p] != fb[p]),
        "process_added": sorted(pb - pa),
        "process_removed": sorted(pa - pb),
    }
    print(json.dumps(report, indent=2))
    divergent = any(report[k] for k in report)
    return 1 if divergent else 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="state_map")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("snapshot")
    s.add_argument("--watch", default=".")
    s.add_argument("--out", required=True)
    s.set_defaults(func=cmd_snapshot)

    s = sub.add_parser("diff")
    s.add_argument("before")
    s.add_argument("after")
    s.set_defaults(func=cmd_diff)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
