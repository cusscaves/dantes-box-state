#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SM = ROOT / "state_map.py"


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="dantes-state-"))
    try:
        watch = tmp / "w"
        watch.mkdir()
        (watch / "a.txt").write_text("one")
        before = tmp / "before.json"
        after = tmp / "after.json"
        r = subprocess.run(
            [sys.executable, str(SM), "snapshot", "--watch", str(watch), "--out", str(before)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr
        (watch / "a.txt").write_text("two")
        (watch / "b.txt").write_text("new")
        r = subprocess.run(
            [sys.executable, str(SM), "snapshot", "--watch", str(watch), "--out", str(after)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stderr
        r = subprocess.run(
            [sys.executable, str(SM), "diff", str(before), str(after), "--files-only"],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 1, r.stderr
        report = json.loads(r.stdout)
        assert "b.txt" in report["created"]
        assert "a.txt" in report["changed"]

        # Loop2: identical snapshots → exit 0
        r = subprocess.run(
            [sys.executable, str(SM), "diff", str(after), str(after), "--files-only"],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 0, r.stdout

        # Loop2: missing file fails loud
        r = subprocess.run(
            [sys.executable, str(SM), "diff", "nope.json", str(after)],
            capture_output=True,
            text=True,
        )
        assert r.returncode == 2

        print("ALL TESTS PASSED")
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
