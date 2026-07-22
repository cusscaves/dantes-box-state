# Dante's Box — Environment State Mapping

Pre-flight ("set the stage") and post-flight ("check the finish") snapshots.

## Status

v0.1 — filesystem + process snapshot + diff. Subsystem for workflow capture.

## What this is

Genus 3 from the Dante's Box split — not a standalone product. Feeds Genus 2 replay.

## Quick start

```bash
python state_map.py snapshot --out before.json
# ... do work ...
python state_map.py snapshot --out after.json
python state_map.py diff before.json after.json
```

## Success criteria

1. Snapshot captures file hashes under a watch root + running process names
2. Diff reports created / deleted / changed / process_added / process_removed
3. Exit code 0 on empty diff, 1 on any divergence
