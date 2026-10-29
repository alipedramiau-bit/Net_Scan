# Patch: dedupe_devices

Replace the entire `dedupe_devices` function in `backend/db.py` with the improved version from this repository path after applying the package, or copy from `artifacts/olom_scan_dedupe`.

## Behavior

When multiple devices share the same non-empty MikroTik identity (`device_name`):

1. **Prefer the row that has tags** (non-empty `tags`)
2. Else prefer more recent `last_seen`
3. Else higher `seen_count`
4. Else richer open-ports / detail fields

Tags, open ports, classification, and empty detail fields are **merged** from discarded rows into the kept row before deletion.

Names are matched case-insensitively with collapsed whitespace (`Router 1` == `router 1`).

Empty identity names are never treated as duplicates of each other.
