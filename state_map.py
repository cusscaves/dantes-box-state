#!/usr/bin/env python3
"""Environment state mapping — pre/post snapshots for Dante workflow replay."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from dante_fs import diff_file_maps, make_snapshot


def cmd_snapshot(args: argparse.Namespace) -> int:
    snap = make_snapshot(Path(args.watch))
    out = Path(args.out)
    out.write_text(json.dumps(snap, indent=2))
    print(f"wrote {out} ({len(snap['files'])} files, {len(snap['processes'])} processes)")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    before_path, after_path = Path(args.before), Path(args.after)
    if not before_path.exists():
        print(f"missing before snapshot: {before_path}", file=sys.stderr)
        return 2
    if not after_path.exists():
        print(f"missing after snapshot: {after_path}", file=sys.stderr)
        return 2
    a = json.loads(before_path.read_text())
    b = json.loads(after_path.read_text())
    fa, fb = a.get("files", {}), b.get("files", {})
    files = diff_file_maps(fa, fb)
    if args.files_only:
        report = {**files, "process_added": [], "process_removed": []}
    else:
        pa, pb = set(a.get("processes", [])), set(b.get("processes", []))
        report = {
            **files,
            "process_added": sorted(pb - pa),
            "process_removed": sorted(pa - pb),
        }
    print(json.dumps(report, indent=2))
    return 1 if any(report[k] for k in report) else 0


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
    s.add_argument(
        "--files-only",
        action="store_true",
        help="ignore process list (stable CI diffs)",
    )
    s.set_defaults(func=cmd_diff)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
