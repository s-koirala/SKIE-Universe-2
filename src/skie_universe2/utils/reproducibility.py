"""ReproLog capture + atomic write.

Replicates the 13-field ReproLog schema of
``~/.claude/skills/emit-repro-log/assets/emit_repro_log.py`` (itself a
self-contained port of SKIE-Universe 1.0
``src/skie_ninja/utils/reproducibility.py``) exactly:

    run_id, phase, hypothesis_id, timestamp_utc, git_head,
    pip_freeze_sha256, pip_freeze_path, dataset_checksums,
    rng_seed, model_hash, config_resolved_sha256, host, env_id.

Records land at ``logs/reproducibility/repro_log_{run_id}.json`` per the
CLAUDE.md reproducibility contract.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import subprocess
import sys
import tempfile
import uuid
from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

from skie_universe2.utils.hashing import file_sha256
from skie_universe2.utils.paths import ProjectPaths

# Subprocess timeout for `git rev-parse` / `uv pip freeze`. Tunable via env
# var; 30 s default matches the emit-repro-log skill asset (operational I/O
# bound, no statistical content).
_SUBPROCESS_TIMEOUT_SEC = int(os.environ.get("SKIE_SUBPROCESS_TIMEOUT_SEC", "30"))


@dataclass(frozen=True)
class ReproLog:
    """13-field reproducibility record (schema frozen; see module docstring)."""

    run_id: str
    phase: str
    hypothesis_id: str
    timestamp_utc: str
    git_head: str
    pip_freeze_sha256: str
    pip_freeze_path: str
    dataset_checksums: dict[str, str]
    rng_seed: int
    model_hash: str | None
    config_resolved_sha256: str | None
    host: dict[str, str]
    env_id: str

    def to_dict(self) -> dict:
        return asdict(self)

    def write(self, path: Path) -> Path:
        """Atomic serialize: tempfile in destination dir -> fsync -> os.replace."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = json.dumps(self.to_dict(), sort_keys=True, indent=2, ensure_ascii=False).encode(
            "utf-8"
        )
        # Not a context manager on purpose: `delete=False` + manual
        # close BEFORE os.replace is required on Windows (an open
        # handle blocks the rename). Same idiom as the emit-repro-log
        # skill asset.
        tmp = tempfile.NamedTemporaryFile(  # noqa: SIM115
            mode="wb",
            dir=str(path.parent),
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        )
        tmp_path = Path(tmp.name)
        try:
            try:
                tmp.write(data)
                tmp.flush()
                os.fsync(tmp.fileno())
            finally:
                tmp.close()
            os.replace(tmp_path, path)
        except Exception:
            tmp_path.unlink(missing_ok=True)
            raise
        return path

    @staticmethod
    def read(path: Path) -> ReproLog:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        return ReproLog(**payload)


def _git_head(root: Path) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            timeout=_SUBPROCESS_TIMEOUT_SEC,
        )
        return out.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return "unknown"


def _pip_freeze_bytes() -> bytes:
    """Prefer `uv pip freeze` per project tooling default; fall back to pip."""
    for cmd in (["uv", "pip", "freeze"], [sys.executable, "-m", "pip", "freeze"]):
        try:
            out = subprocess.run(
                cmd,
                capture_output=True,
                check=True,
                timeout=_SUBPROCESS_TIMEOUT_SEC,
            )
            return out.stdout
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            continue
    return b""


def _host_info() -> dict[str, str]:
    return {
        "os": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "cpu": platform.machine(),
    }


def _posix(path: Path) -> str:
    return str(PurePosixPath(*Path(path).parts))


def capture(
    *,
    phase: str,
    hypothesis_id: str = "n/a",
    # rng_seed has NO default (round-2 audit CODE-2-8): the ReproLog
    # contract demands the seed of the run that produced the artifact,
    # and a silent 0 default would launder unseeded producers.
    rng_seed: int,
    dataset_checksums: dict[str, str] | None = None,
    model_hash: str | None = None,
    config_resolved_sha256: str | None = None,
    env_id: str | None = None,
    paths: ProjectPaths | None = None,
    run_id: str | None = None,
) -> ReproLog:
    """Build a ReproLog from the current process state.

    Pure w.r.t. inputs given identical git/pip state — successive calls
    differ only in ``timestamp_utc`` (and auto-generated ``run_id``).
    """
    paths = paths or ProjectPaths.discover()
    paths.ensure(paths.logs_reproducibility_env)

    freeze_bytes = _pip_freeze_bytes()
    freeze_sha = hashlib.sha256(freeze_bytes).hexdigest()
    freeze_path = paths.logs_reproducibility_env / f"{freeze_sha}.txt"
    if not freeze_path.exists():
        freeze_path.write_bytes(freeze_bytes)

    uv_lock = paths.root / "uv.lock"
    lock_id = file_sha256(uv_lock) if uv_lock.is_file() else "no-uv-lock"

    return ReproLog(
        run_id=run_id or uuid.uuid4().hex,
        phase=phase,
        hypothesis_id=hypothesis_id,
        timestamp_utc=datetime.now(tz=UTC).isoformat(timespec="microseconds"),
        git_head=_git_head(paths.root),
        pip_freeze_sha256=freeze_sha,
        pip_freeze_path=_posix(freeze_path.relative_to(paths.root)),
        dataset_checksums=dict(dataset_checksums or {}),
        rng_seed=rng_seed,
        model_hash=model_hash,
        config_resolved_sha256=config_resolved_sha256,
        host=_host_info(),
        env_id=env_id or lock_id,
    )


def with_model_hash(log: ReproLog, model_hash: str) -> ReproLog:
    return replace(log, model_hash=model_hash)
