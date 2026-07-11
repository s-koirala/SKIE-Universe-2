"""Run context manager.

Ported from SKIE-Universe 1.0 ``src/skie_ninja/utils/runcontext.py``
minus the torch branch (no torch in this project) and the structured
logging binder (2.0 uses stdlib logging directly).

Single entry point for any script that produces artifacts. Guarantees a
ReproLog is written to
``logs/reproducibility/repro_log_{run_id}.json`` even if the run
crashes (atexit + context-manager ``__exit__`` both flush). Seeds
python ``random`` and numpy.
"""

from __future__ import annotations

import atexit
import logging
import os
import random
from dataclasses import replace
from pathlib import Path
from types import TracebackType
from typing import Self

from skie_universe2.utils.paths import ProjectPaths
from skie_universe2.utils.reproducibility import ReproLog, capture

_log = logging.getLogger(__name__)


def _seed_all(seed: int) -> None:
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        # Deferred so RunContext stays importable in envs without the
        # `data` extra (1.0 defensive-import behavior preserved).
        import numpy as np  # noqa: PLC0415

        np.random.seed(seed)
    except ImportError:
        pass


class RunContext:
    """Open a run; guarantee a ReproLog is flushed to disk."""

    def __init__(
        self,
        *,
        phase: str,
        hypothesis_id: str,
        rng_seed: int,
        dataset_checksums: dict[str, str] | None = None,
        config_resolved_sha256: str | None = None,
        paths: ProjectPaths | None = None,
    ) -> None:
        self.paths = paths or ProjectPaths.discover()
        self._phase = phase
        self._hypothesis_id = hypothesis_id
        self._rng_seed = rng_seed
        self._dataset_checksums = dataset_checksums or {}
        self._config_resolved_sha256 = config_resolved_sha256
        self._flushed = False
        self.log: ReproLog | None = None

    def __enter__(self) -> Self:
        _seed_all(self._rng_seed)
        self.log = capture(
            phase=self._phase,
            hypothesis_id=self._hypothesis_id,
            rng_seed=self._rng_seed,
            dataset_checksums=self._dataset_checksums,
            config_resolved_sha256=self._config_resolved_sha256,
            paths=self.paths,
        )
        atexit.register(self._flush)
        return self

    def set_model_hash(self, model_hash: str) -> None:
        if self.log is None:
            raise RuntimeError("RunContext not entered")
        self.log = replace(self.log, model_hash=model_hash)

    def add_dataset_checksum(self, name: str, sha256: str) -> None:
        if self.log is None:
            raise RuntimeError("RunContext not entered")
        updated = dict(self.log.dataset_checksums)
        updated[name] = sha256
        self.log = replace(self.log, dataset_checksums=updated)

    @property
    def output_path(self) -> Path:
        if self.log is None:
            raise RuntimeError("RunContext not entered")
        return self.paths.logs_reproducibility / f"repro_log_{self.log.run_id}.json"

    def _flush(self) -> None:
        if self._flushed or self.log is None:
            return
        try:
            self.log.write(self.output_path)
            self._flushed = True
        except Exception as exc:  # last-resort; the whole point is flush-on-crash
            _log.error("ReproLog flush failed: %s", exc)

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self._flush()
