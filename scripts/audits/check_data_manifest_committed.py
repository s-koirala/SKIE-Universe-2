#!/usr/bin/env python3
"""CI-scope drift check for data/_manifest.json on a fresh clone.

The full manifest inventories everything under data/ at materialization time
(ADR-0011 Decision 4), most of which is gitignored local data. On CI only the
committed subset exists, so `build_data_manifest.py --check` would report
every local-only artifact as drift. This checker applies clone-correct
semantics instead:

1. every manifest entry whose file IS present must match its recorded SHA-256;
2. every file present under data/ (except the manifest itself) must have a
   manifest entry;
3. manifest entries whose files are absent are allowed (gitignored local
   artifacts — the machine-local drift check remains the vendored
   `build_data_manifest.py --check`, run at materialization and pre-push).
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
DATA = ROOT / "data"
MANIFEST = DATA / "_manifest.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    if not MANIFEST.is_file():
        print(f"MISSING: {MANIFEST.relative_to(ROOT)}", file=sys.stderr)
        return 1
    payload = json.loads(MANIFEST.read_text(encoding="utf-8"))
    # keys are repo-relative POSIX paths with the "data/" prefix
    entries: dict[str, str] = {
        key: (value["sha256"] if isinstance(value, dict) else value)
        for key, value in payload.get("files", {}).items()
    }

    failures: list[str] = []
    present_checked = 0
    for rel, recorded in entries.items():
        fp = ROOT / rel
        if not fp.is_file():
            continue  # gitignored local artifact — allowed on a clone
        present_checked += 1
        actual = _sha256(fp)
        if actual != recorded:
            failures.append(f"SHA mismatch: {rel}: {actual} != {recorded}")

    for fp in sorted(DATA.rglob("*")):
        if not fp.is_file() or fp == MANIFEST or fp.name == ".gitkeep":
            continue
        rel = fp.relative_to(ROOT).as_posix()
        if rel not in entries:
            failures.append(f"unmanifested file present: {rel}")

    for line in failures:
        print(line, file=sys.stderr)
    print(
        f"checked {present_checked} present manifest entr(y/ies); "
        f"{len(entries) - present_checked} absent (local-only) allowed; "
        f"{len(failures)} failure(s)"
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
