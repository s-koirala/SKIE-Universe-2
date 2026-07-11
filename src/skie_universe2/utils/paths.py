"""Project path resolver.

Single source of truth for filesystem layout, ported from SKIE-Universe
1.0 ``src/skie_ninja/utils/paths.py`` (sibling repo) with the property
set trimmed to what the 2.0 Phase C substrate consumes. No module under
``skie_universe2`` may hard-code absolute paths outside this module.

Root discovery: walk up from this file until a directory containing
``pyproject.toml`` is found — portable across developer machines, CI
runners, and Windows/POSIX hosts.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _discover_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "pyproject.toml").is_file():
            return candidate
    raise RuntimeError(f"Could not locate project root (pyproject.toml) walking up from {start}")


@dataclass(frozen=True)
class ProjectPaths:
    """Resolved project directories.

    Construct via ``ProjectPaths.discover()`` or inject ``root`` directly
    for tests. Nothing is auto-created; callers that need a directory to
    exist call ``.ensure()`` explicitly.
    """

    root: Path

    @classmethod
    def discover(cls, start: Path | None = None) -> ProjectPaths:
        origin = (start or Path(__file__)).resolve()
        return cls(root=_discover_root(origin))

    # Data
    @property
    def data(self) -> Path:
        return self.root / "data"

    @property
    def data_raw(self) -> Path:
        return self.data / "raw"

    @property
    def data_interim(self) -> Path:
        return self.data / "interim"

    @property
    def data_processed(self) -> Path:
        return self.data / "processed"

    @property
    def config(self) -> Path:
        return self.root / "config"

    # Logs
    @property
    def logs(self) -> Path:
        return self.root / "logs"

    @property
    def logs_reproducibility(self) -> Path:
        return self.logs / "reproducibility"

    @property
    def logs_reproducibility_env(self) -> Path:
        return self.logs_reproducibility / "env"

    # Machine-level shared data store (ADR-0011 Decision 1).
    # Resolution order: SKIE_SHARED_DATA env var > ~/datasets fallback —
    # same contract as 1.0 ``ProjectPaths.shared_data``.
    @property
    def shared_data(self) -> Path:
        """Shared machine-wide data root for vendor raw datasets."""
        env = os.environ.get("SKIE_SHARED_DATA")
        if env:
            return Path(env).expanduser().resolve()
        return Path.home() / "datasets"

    @property
    def shared_vendor_skie_ninja_legacy(self) -> Path:
        """Vendor-namespaced machine-level store for the Databento-sourced
        legacy 1-minute CSVs (registered as
        ``vendor_skie_ninja_legacy_raw_1min`` in config/data_sources.yaml).
        """
        return self.shared_data / "vendor_skie_ninja_legacy"

    def ensure(self, path: Path) -> Path:
        path.mkdir(parents=True, exist_ok=True)
        return path


def portable_key(path: Path, root: Path | None = None) -> str:
    """Identity-hygiene-safe POSIX key for a filesystem path.

    Committed artifacts (provenance JSON, ReproLogs) must not embed the
    OS username (publishing rules; round-1 audit finding L). Resolution
    order: repo-relative if under ``root``; ``~``-relative if under the
    user home; absolute POSIX otherwise (last resort — flagged by the
    format auditor if it ever appears in a committed file).
    """
    p = Path(path)
    if root is not None:
        try:
            return p.relative_to(Path(root)).as_posix()
        except ValueError:
            pass
    try:
        return "~/" + p.relative_to(Path.home()).as_posix()
    except ValueError:
        return p.as_posix()
