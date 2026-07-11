"""Upstream data-source registry gate (ADR-0011 Decision 3).

Every external source consumed by this project must be registered in
``config/data_sources.yaml`` before ingest; ingest modules resolve their
source through :func:`resolve_ingest_source` and refuse to run when the
source is absent, or registered only as a non-ingestable kind (e.g.
``sibling_repo_reference``, which ADR-0011 Decision 2 restricts to
read-only benchmark/reference use).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from skie_universe2.utils.paths import ProjectPaths

# Registry kinds an ingest job may consume. ``sibling_repo_reference``
# is deliberately excluded: ADR-0011 Decision 2 forbids cross-repo
# processed imports; those entries exist only as benchmarks.
_INGESTABLE_KINDS: frozenset[str] = frozenset({"vendor_raw"})


class UnregisteredSourceError(ValueError):
    """Raised when an ingest job requests a source that is not registered
    in ``config/data_sources.yaml`` (or is registered as reference-only).
    Adding a data source without registering it there is an integrity
    violation under ADR-0008 (via ADR-0011)."""


@dataclass(frozen=True)
class SourceRecord:
    """One resolved registry entry."""

    name: str
    kind: str
    location: Path
    symbols: tuple[str, ...]
    raw: dict[str, Any]


def registry_path(paths: ProjectPaths | None = None) -> Path:
    paths = paths or ProjectPaths.discover()
    return paths.config / "data_sources.yaml"


def load_registry(config_path: Path | None = None) -> dict[str, Any]:
    """Load and shape-check the registry YAML."""
    path = config_path or registry_path()
    if not path.is_file():
        raise UnregisteredSourceError(
            f"Data-source registry not found at {path}; ADR-0011 Decision 3 "
            f"requires every source to be registered before ingest."
        )
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or "sources" not in payload:
        raise UnregisteredSourceError(
            f"Registry {path} malformed: top-level 'sources' mapping required."
        )
    sources = payload["sources"]
    if not isinstance(sources, dict):
        raise UnregisteredSourceError(f"Registry {path} malformed: 'sources' must be a mapping.")
    return sources


def resolve_ingest_source(
    name: str,
    *,
    config_path: Path | None = None,
) -> SourceRecord:
    """Resolve a registry entry for ingest, refusing unregistered or
    reference-only sources.

    Raises
    ------
    UnregisteredSourceError
        If ``name`` is not in the registry, or its ``kind`` is not an
        ingestable kind, or it lacks a ``location``.
    """
    sources = load_registry(config_path)
    entry = sources.get(name)
    if entry is None:
        raise UnregisteredSourceError(
            f"Source {name!r} is not registered in config/data_sources.yaml; "
            f"registered sources: {sorted(sources)}. Register it before "
            f"ingest (ADR-0011 Decision 3)."
        )
    kind = str(entry.get("kind", ""))
    if kind not in _INGESTABLE_KINDS:
        raise UnregisteredSourceError(
            f"Source {name!r} has kind={kind!r}, which is not ingestable "
            f"(allowed: {sorted(_INGESTABLE_KINDS)}). Reference-only entries "
            f"cannot feed data/processed/ (ADR-0011 Decision 2)."
        )
    location = entry.get("location")
    if not location:
        raise UnregisteredSourceError(f"Source {name!r} is registered without a 'location'.")
    symbols = tuple(str(s) for s in entry.get("symbols", []))
    return SourceRecord(
        name=name,
        kind=kind,
        location=Path(str(location)).expanduser(),
        symbols=symbols,
        raw=dict(entry),
    )


def assert_symbols_registered(record: SourceRecord, symbols: tuple[str, ...]) -> None:
    """Refuse symbols absent from the source's registered symbol set."""
    unregistered = [s for s in symbols if s not in record.symbols]
    if unregistered:
        raise UnregisteredSourceError(
            f"Symbols {unregistered} are not registered for source "
            f"{record.name!r} (registered: {list(record.symbols)}); update "
            f"config/data_sources.yaml before ingesting them (ADR-0011 "
            f"Decision 3)."
        )
