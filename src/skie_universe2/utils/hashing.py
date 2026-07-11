"""Deterministic hashing helpers.

Ported from SKIE-Universe 1.0 ``src/skie_ninja/utils/hashing.py``
(sibling repo) minus ``model_sha256`` (no model artifacts in Phase C).
All hashes are SHA-256 hex digests. The chunk size for file reads
(1 MiB) is the common page-cache-friendly value used by ``hashlib``
examples in CPython docs and has no statistical content; it is an
I/O throughput tuning parameter only.

Environment pinning: ``frame_sha256`` uses polars string casting, so
hash stability is tied to the polars primitive-formatting contract.
polars is pinned ==1.40.0 in pyproject (matching the 1.0 reference
venv); on any polars upgrade, bump ``ReproLog.env_id`` so downstream
verifiers flag the boundary rather than silently accepting mismatches.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import polars as pl

_FILE_CHUNK_BYTES = 1 << 20  # 1 MiB; I/O-tuning only, no statistical meaning

# Canonical separators for frame canonicalization. NUL cannot appear
# inside a polars Utf8 value, so using it as the inter-cell delimiter
# makes the canonicalization prefix-free without escaping.
_CELL_SEP = b"\x00"
_ROW_SEP = b"\x00\x01"


def file_sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as fh:
        for chunk in iter(lambda: fh.read(_FILE_CHUNK_BYTES), b""):
            h.update(chunk)
    return h.hexdigest()


def _hash_polars_streaming(df: Any, sort_cols: list[str], hasher: Any) -> None:
    """Stream the canonical bytes of a polars DataFrame into ``hasher``.

    Canonicalization (byte-identical to the 1.0 implementation):

      1. Sort rows by ``sort_cols`` (deterministic, not maintain_order).
      2. Column order: sort columns first, then remaining columns in
         lexicographic order.
      3. Cast every column to Utf8 (Binary columns hex-encoded first).
      4. Header of ``{column}:{dtype}`` pairs, then rows; cells joined
         with NUL, rows with NUL+SOH; None encoded as ``\\x02NULL``.

    Streams one row of UTF-8 bytes at a time — bounded memory for
    multi-million-row substrates (1.0 P1-FRAME-SHA-STREAMING).
    """
    if isinstance(df, pl.LazyFrame):
        df = df.collect()
    sorted_df = df.sort(sort_cols, maintain_order=False)

    remaining = sorted(c for c in sorted_df.columns if c not in sort_cols)
    ordered_cols = list(sort_cols) + remaining
    sorted_df = sorted_df.select(ordered_cols)

    cast_exprs = []
    for name in ordered_cols:
        dtype = sorted_df.schema[name]
        if dtype == pl.Binary:
            cast_exprs.append(pl.col(name).bin.encode("hex").alias(name))
        else:
            cast_exprs.append(pl.col(name).cast(pl.Utf8).alias(name))
    str_df = sorted_df.with_columns(cast_exprs)

    header = "\x00".join(f"{c}:{sorted_df.schema[c]}" for c in ordered_cols).encode("utf-8")
    hasher.update(header)
    hasher.update(b"\x00\x03")

    for i, row in enumerate(str_df.iter_rows()):
        if i > 0:
            hasher.update(_ROW_SEP)
        for j, cell in enumerate(row):
            if j > 0:
                hasher.update(_CELL_SEP)
            if cell is None:
                hasher.update(b"\x02NULL")
            else:
                hasher.update(str(cell).encode("utf-8"))


def frame_sha256(df: Any, sort_cols: list[str]) -> str:
    """Hash a polars dataframe after stable-sorting by ``sort_cols``.

    Row permutations of the input yield the same hash; any value
    mutation changes the hash. Canonicalization is a column-wise Utf8
    cast (see ``_hash_polars_streaming``), not IPC/Arrow bytes, so
    hashes are stable across polars minor versions; bump
    ``ReproLog.env_id`` on polars upgrades regardless (float Utf8
    formatting is a polars-version surface).
    """
    if not sort_cols:
        raise ValueError("sort_cols must be non-empty for deterministic hashing")

    if not type(df).__module__.startswith("polars"):
        raise TypeError(f"Unsupported dataframe type: {type(df)!r}")

    hasher = hashlib.sha256()
    _hash_polars_streaming(df, sort_cols, hasher)
    return hasher.hexdigest()
