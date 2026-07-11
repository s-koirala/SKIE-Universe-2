"""Shadow-ledger writer (ADR-0003).

Append-only writer for counterfactual net-of-cost expert returns —
"every arsenal expert x every universe asset x every bar, traded or
not" (ADR-0003 Decision 1). This module implements the storage
contract of ADR-0003 Decision 2 and the immutability contract of
Decision 3:

- **Storage:** partitioned parquet under
  ``data/processed/shadow_ledger/`` with partition keys
  ``expert_id={id}/asset={A}/session_date={YYYY-MM-DD}``, one
  ``part-0000.parquet`` per partition, typed schema validated on
  write (the 1.0 ``WalkForwardEngine`` run-ledger conventions: fixed
  column tuple, centralized ``{column: dtype}`` map, exact
  column-and-dtype match enforced on read-back, atomic tmp +
  ``os.replace`` writes).
- **Append-only:** a write into an existing (expert_id, asset,
  session_date) partition is refused with
  :class:`LedgerAppendOnlyError`. The partition claim is ATOMIC
  (``mkdir(exist_ok=False)``), so two concurrent writers cannot both
  claim a partition (round-1 audit CODE-1-4/QUANT-1-5). Corrections
  follow the ADR-0003 Decision 3 path: bump the expert version (a new
  ``expert_id@version`` is a new partition family) and record a
  deprecation of the old partitions via
  :meth:`ShadowLedgerWriter.deprecate` — an append-only JSONL record;
  bytes on disk are never mutated or deleted.
- **Batch write protocol (two-phase commit + intent journal, round-1
  audit CODE-1-3/REPRODUCIBILITY-1-2):**

  1. validate the frame (schema, session-date integrity, covariate
     registry, cross-partition duplicate check);
  2. append an intent record (``status="begin"``, run_id, planned
     partitions) to ``_journal/journal.jsonl``;
  3. stage every partition file under ``_staging/{run_id}/``;
  4. promote: atomically claim each final partition dir and move the
     staged file in; on any mid-promote failure, partitions promoted
     by THIS run are removed again (nothing has referenced them — no
     roll-up, no ReproLog — so this is abort-of-uncommitted-work, not
     mutation of committed evidence) and a ``rolled_back`` journal
     record is appended;
  5. emit the ReproLog, append the SHA-256 roll-ups, append a
     ``committed`` journal record, clean staging, rebuild the data
     manifest.

  **Guarantee:** a partition is committed evidence if and only if it
  has a roll-up record; the journal makes every other on-disk state
  attributable. This is crash-safe-with-recovery, not all-or-nothing
  under arbitrary crashes.

  **Crash recovery procedure:** a ``begin`` journal record without a
  matching terminal record (``committed`` / ``rolled_back`` /
  ``failed_partial``) marks an interrupted run. For each partition
  listed in that record: if it exists on disk but has NO entry in
  ``_rollups/rollups.jsonl``, it is uncommitted residue and may be
  deleted — this includes an EMPTY partition directory with no parquet
  file (a claim whose promote never ran; round-2 audit QUANT-2-3);
  then append a ``rolled_back`` record with the same run_id. Never
  touch a partition that has a roll-up record. ``_staging/``
  subdirectories of interrupted runs may always be deleted.
- **Concurrency:** partition claims are atomic (above); all JSONL
  side-files (journal, roll-ups, deprecations) are appended via
  ``open(path, "ab")`` single-write calls under an OS file lock
  (``msvcrt.locking`` on Windows / ``fcntl.flock`` on POSIX; see
  :class:`_InterProcessLock`), so concurrent appends cannot lose
  records (round-1 audit CODE-1-4b). Windows lock-timeout behavior
  (round-2 audit item 5.4): ``msvcrt.locking(LK_LOCK)`` retries the
  lock once per second for ~10 attempts and then raises ``OSError`` —
  a writer stalled behind a held lock for >~10 s therefore FAILS
  LOUDLY (the batch aborts and journals ``rolled_back``; no partial
  line is ever written) rather than corrupting the JSONL. POSIX
  ``flock`` blocks indefinitely instead. If an OSError from a lock
  timeout aborts a batch, simply retry after the holder releases.
- **SHA-256 roll-up:** per partition, both the parquet file SHA-256 and
  the canonical frame SHA-256 (``frame_sha256``, the 1.0 roll-up
  idiom) are appended to
  ``data/processed/shadow_ledger/_rollups/rollups.jsonl`` and recorded
  in ``data/_manifest.json`` by re-running the project manifest builder
  (``scripts/build_data_manifest.py``, ADR-0011 Decision 4).
- **ReproLog:** every ``write_partitions`` call emits a 13-field
  ReproLog (ADR-0008 Decision 3) at
  ``logs/reproducibility/repro_log_{run_id}.json`` with the partition
  frame hashes in ``dataset_checksums``; the ReproLog ``run_id`` IS the
  journaled batch id, so journal, roll-ups, and ReproLog cross-reference
  one identifier.

Schema (ADR-0003 Decisions 2/6, ADR-0006 Decision 5)
----------------------------------------------------

Core columns (all non-nullable):

- ``expert_id`` (Utf8) — versioned expert identifier; MUST contain
  ``@`` (``{name}@{version}``) because version bumps are new
  identities under Decision 3.
- ``asset`` (Utf8) — root symbol (matches the evidence-bar substrate).
- ``bar_ts`` (Datetime us, UTC) — the bar the counterfactual return
  accrues over; unique within a partition and not present in the two
  neighboring session partitions of the same (expert_id, asset)
  (round-1 audit QUANT-1-6 defense-in-depth).
- ``session_date`` (Date) — CME session date of ``bar_ts`` (partition
  key; carried in-file so a single partition file is self-describing).
  Recomputed from ``bar_ts`` on validation via the shared
  :func:`skie_universe2.utils.sessions.cme_session_date_expr` rule —
  mismatches are refused.
- ``ret_gross`` (Float64) — counterfactual pre-cost log-return of the
  expert's position over the bar.
- ``ret_net`` (Float64) — ``ret_gross`` minus the bar-level cost drag
  (ADR-0008 Decision 2: costs applied as log-return drag at the bar
  level, never flat-dollar at horizon).
- ``cost_model_id`` (Utf8) — identifier + version of the cost model
  that produced ``ret_net`` (part of the provenance chain, ADR-0003
  Consequences).
- ``fidelity_tier`` (Int64) — execution-simulation tier per ADR-0006
  (0 bar-close / 1 intrabar OHLC-path / 2 tick-queue-latency). A
  recorded column because mixed-tier comparisons are prohibited within
  a single evidence table (ADR-0006 Decision 5).

Covariate columns (ADR-0003 Decision 6 + ADR-0008 Decision 4): zero or
more additional Float64 columns prefixed ``cov_`` carrying the
PRE-REGISTERED conditioning covariates as wide columns, so
conditional-edge scans are reproducible joins. The registered set per
expert family lives in ``config/covariates.yaml`` (round-1 audit
QUANT-1-7); a frame's ``cov_`` columns must exactly equal the
registered set for every expert family it contains — free-form
covariates and cross-partition covariate drift are refused. Wide
columns rather than a serialized map: parquet-native predicate
pushdown and dtype enforcement apply per covariate, and the ``cov_``
prefix keeps the core schema closed while the registered set grows per
family without a schema migration. The covariate set present in a
partition is recorded in the roll-up record.

Look-ahead note: this writer stores rows keyed by the bar they accrue
over; producing ``ret_*`` from signals computable only at t (using
data <= t) is the *producer's* obligation, enforced by the ADR-0008
PIT canary suite at expert admission — the ledger records, it does
not recompute.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from types import TracebackType
from typing import Any

import polars as pl
import yaml

from skie_universe2.utils.hashing import file_sha256, frame_sha256
from skie_universe2.utils.paths import ProjectPaths
from skie_universe2.utils.reproducibility import ReproLog, capture
from skie_universe2.utils.sessions import cme_session_date_expr

if os.name == "nt":
    import msvcrt
else:
    import fcntl

_log = logging.getLogger(__name__)

_DATASET_NAME = "shadow_ledger"
_LEDGER_SCHEMA_VERSION = "1.1.0"  # 1.1.0: journaled two-phase commit + covariate registry

# Fixed core column tuple — the WalkForwardEngine `_LEDGER_COLUMNS`
# idiom: emission and read-back validation share one source of truth.
_CORE_COLUMNS: tuple[str, ...] = (
    "expert_id",
    "asset",
    "bar_ts",
    "session_date",
    "ret_gross",
    "ret_net",
    "cost_model_id",
    "fidelity_tier",
)

# Covariate columns are wide Float64 columns with this prefix
# (ADR-0003 Decision 6; see module docstring).
_COVARIATE_PREFIX = "cov_"

# Execution fidelity tiers per ADR-0006 Decision 1 (0 bar-close,
# 1 intrabar OHLC-path, 2 tick/queue/latency). Closed set.
_VALID_FIDELITY_TIERS: frozenset[int] = frozenset({0, 1, 2})


def _core_schema() -> dict[str, Any]:
    """Canonical ``{column: polars-dtype}`` map for the core columns."""
    return {
        "expert_id": pl.Utf8,
        "asset": pl.Utf8,
        "bar_ts": pl.Datetime("us", "UTC"),
        "session_date": pl.Date,
        "ret_gross": pl.Float64,
        "ret_net": pl.Float64,
        "cost_model_id": pl.Utf8,
        "fidelity_tier": pl.Int64,
    }


class LedgerSchemaError(ValueError):
    """Raised when a frame offered to the ledger violates the typed schema,
    the session-date rule, or the registered covariate set."""


class LedgerAppendOnlyError(RuntimeError):
    """Raised on any attempt to write into an existing
    (expert_id, asset, session_date) partition, or to re-insert a bar_ts
    already present in a neighboring session partition. Rows are never
    mutated (ADR-0003 Decision 3); corrections require a new
    ``expert_id@version`` plus a deprecation record
    (:meth:`ShadowLedgerWriter.deprecate`)."""


class _InterProcessLock:
    """Minimal cross-platform exclusive file lock (round-1 audit CODE-1-4b).

    Locks a dedicated ``*.lock`` sidecar (never the data file itself, so
    the lock file's own bytes are irrelevant). Windows: ``msvcrt.locking``
    on the first byte (blocking-with-retry per CPython semantics: ~10
    attempts at 1 s intervals, then OSError). POSIX: ``fcntl.flock``
    exclusive (blocking).
    """

    def __init__(self, path: Path) -> None:
        self._path = Path(path)
        self._fh = None

    def __enter__(self) -> _InterProcessLock:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fh = open(self._path, "a+b")  # noqa: SIM115 — held across the with-block, closed in __exit__
        try:
            if os.name == "nt":
                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_LOCK, 1)
            else:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        except Exception:
            self._fh.close()
            self._fh = None
            raise
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._fh is None:
            return
        try:
            if os.name == "nt":
                self._fh.seek(0)
                msvcrt.locking(self._fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        finally:
            self._fh.close()
            self._fh = None


def _load_covariate_registry(path: Path) -> dict[str, frozenset[str]]:
    """Load ``config/covariates.yaml`` -> {expert_family: covariate set}.

    A missing file yields an EMPTY registry (fail-closed for covariates:
    every ``cov_`` column is then refused) with a WARNING — never a
    silent allowance (round-1 audit QUANT-1-7).
    """
    if not path.is_file():
        _log.warning(
            "Covariate registry not found at %s; treating every expert "
            "family's registered set as empty (all cov_ columns refused).",
            path,
        )
        return {}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:  # round-2 audit CODE-2-2: wrap in module error type
        raise LedgerSchemaError(f"Covariate registry {path} is not valid YAML: {exc}") from exc
    if not isinstance(payload, dict):
        raise LedgerSchemaError(f"Covariate registry {path} malformed: mapping required.")
    families = payload.get("expert_families") or {}
    if not isinstance(families, dict):
        raise LedgerSchemaError(
            f"Covariate registry {path} malformed: 'expert_families' must be a mapping."
        )
    out: dict[str, frozenset[str]] = {}
    for family, entry in families.items():
        covs = (entry or {}).get("covariates", []) if isinstance(entry, dict) else []
        covset = frozenset(str(c) for c in covs)
        bad = [c for c in covset if not c.startswith(_COVARIATE_PREFIX)]
        if bad:
            raise LedgerSchemaError(
                f"Covariate registry {path}: family {family!r} registers "
                f"non-'{_COVARIATE_PREFIX}'-prefixed columns {bad!r}."
            )
        out[str(family)] = covset
    return out


@dataclass(frozen=True)
class PartitionWriteResult:
    """Audit record for one written partition."""

    expert_id: str
    asset: str
    session_date: date
    path: Path
    n_rows: int
    file_sha256: str
    frame_sha256: str
    covariate_columns: tuple[str, ...] = field(default=())


class ShadowLedgerWriter:
    """Append-only writer for ``data/processed/shadow_ledger/``.

    Parameters
    ----------
    paths:
        Project path resolver; injectable for tests.
    update_manifest:
        When True (production default), re-runs
        ``scripts/build_data_manifest.py`` after a successful write so
        every partition's SHA-256 lands in ``data/_manifest.json``
        (ADR-0011 Decision 4). Tests running against a temp root
        disable this.
    covariates_config_path:
        Override for ``config/covariates.yaml`` (tests).
    """

    def __init__(
        self,
        paths: ProjectPaths | None = None,
        *,
        update_manifest: bool = True,
        covariates_config_path: Path | None = None,
    ) -> None:
        self.paths = paths or ProjectPaths.discover()
        self._update_manifest = update_manifest
        self._covariates_config_path = (
            covariates_config_path
            if covariates_config_path is not None
            else self.paths.config / "covariates.yaml"
        )

    # ------------------------------------------------------------------
    # Path helpers
    # ------------------------------------------------------------------

    @property
    def base_dir(self) -> Path:
        return self.paths.data_processed / _DATASET_NAME

    def partition_dir(self, expert_id: str, asset: str, session_date: date) -> Path:
        return (
            self.base_dir
            / f"expert_id={expert_id}"
            / f"asset={asset}"
            / f"session_date={session_date.isoformat()}"
        )

    @property
    def _rollup_path(self) -> Path:
        return self.base_dir / "_rollups" / "rollups.jsonl"

    @property
    def _journal_path(self) -> Path:
        return self.base_dir / "_journal" / "journal.jsonl"

    @property
    def _deprecation_path(self) -> Path:
        return self.base_dir / "_deprecations" / "deprecations.jsonl"

    # ------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------

    def validate_frame(self, df: pl.DataFrame) -> None:
        """Validate a candidate ledger frame against the typed schema.

        Enforces: exact core column set + dtypes (leading, in order),
        ``cov_``-prefixed Float64-only extras matching the registered
        covariate set of every expert family present
        (config/covariates.yaml, QUANT-1-7), no nulls, versioned
        expert_id, fidelity_tier in the ADR-0006 closed set, unique
        (expert_id, asset, bar_ts), and session_date == the shared CME
        session rule applied to bar_ts (QUANT-1-6).
        """
        cols = tuple(df.columns)
        if cols[: len(_CORE_COLUMNS)] != _CORE_COLUMNS:
            raise LedgerSchemaError(
                f"Ledger schema mismatch. Expected leading columns "
                f"{_CORE_COLUMNS!r}; got {cols!r}."
            )
        extras = cols[len(_CORE_COLUMNS) :]
        bad_extras = [c for c in extras if not c.startswith(_COVARIATE_PREFIX)]
        if bad_extras:
            raise LedgerSchemaError(
                f"Non-covariate extra columns {bad_extras!r}; additional "
                f"columns must be '{_COVARIATE_PREFIX}'-prefixed covariates "
                f"(ADR-0003 Decision 6)."
            )

        expected = _core_schema()
        for name, dtype in expected.items():
            if df.schema[name] != dtype:
                raise LedgerSchemaError(
                    f"Ledger dtype mismatch for {name!r}: expected {dtype!r}, "
                    f"got {df.schema[name]!r}."
                )
        for name in extras:
            if df.schema[name] != pl.Float64:
                raise LedgerSchemaError(
                    f"Covariate column {name!r} must be Float64, got {df.schema[name]!r}."
                )

        if df.height == 0:
            raise LedgerSchemaError("Refusing to write an empty ledger partition.")

        null_counts = {c: int(df[c].null_count()) for c in df.columns}
        nulled = {c: n for c, n in null_counts.items() if n > 0}
        if nulled:
            raise LedgerSchemaError(f"Null values are not allowed in ledger rows: {nulled}.")

        # expert_id must carry an explicit version: version bumps are
        # new identities under ADR-0003 Decision 3.
        unversioned = df.filter(~pl.col("expert_id").str.contains("@", literal=True))
        if unversioned.height > 0:
            raise LedgerSchemaError(
                f"expert_id must be versioned as '{{name}}@{{version}}' "
                f"(ADR-0003 Decision 3); offending: "
                f"{unversioned['expert_id'].unique().to_list()[:5]}."
            )

        bad_tier = df.filter(~pl.col("fidelity_tier").is_in(sorted(_VALID_FIDELITY_TIERS)))
        if bad_tier.height > 0:
            raise LedgerSchemaError(
                f"fidelity_tier outside ADR-0006 tier set "
                f"{sorted(_VALID_FIDELITY_TIERS)}: "
                f"{bad_tier['fidelity_tier'].unique().to_list()}."
            )

        dup = (
            df.group_by(["expert_id", "asset", "bar_ts"])
            .agg(pl.len().alias("_n"))
            .filter(pl.col("_n") > 1)
        )
        if dup.height > 0:
            raise LedgerSchemaError(
                f"Duplicate (expert_id, asset, bar_ts) rows: {dup.head(3).to_dicts()}."
            )

        # Session-date integrity (QUANT-1-6): the partition key must be
        # the deterministic function of bar_ts — the same shared rule
        # the roll-adjusted ingest uses.
        mismatch = df.with_columns(cme_session_date_expr("bar_ts").alias("_expected_sd")).filter(
            pl.col("_expected_sd") != pl.col("session_date")
        )
        if mismatch.height > 0:
            raise LedgerSchemaError(
                f"session_date does not match the CME session rule applied "
                f"to bar_ts on {mismatch.height} row(s); first: "
                f"{mismatch.head(1).to_dicts()}."
            )

        self._validate_covariate_registry(df, extras)

    def _validate_covariate_registry(self, df: pl.DataFrame, cov_cols: tuple[str, ...]) -> None:
        """Exact-set covariate enforcement per expert family (QUANT-1-7)."""
        registry = _load_covariate_registry(self._covariates_config_path)
        frame_covs = frozenset(cov_cols)
        families = sorted({str(e).split("@", 1)[0] for e in df["expert_id"].unique().to_list()})
        for family in families:
            registered = registry.get(family, frozenset())
            if frame_covs != registered:
                raise LedgerSchemaError(
                    f"Covariate-set mismatch for expert family {family!r}: "
                    f"frame carries {sorted(frame_covs)}, registered set in "
                    f"config/covariates.yaml is {sorted(registered)}. "
                    f"Covariate sets are pre-registered (ADR-0008 Decision 4) "
                    f"and exact-equality enforced (no drift, QUANT-1-7)."
                )

    # ------------------------------------------------------------------
    # Write path (two-phase commit + intent journal)
    # ------------------------------------------------------------------

    def write_partitions(  # noqa: PLR0915 — the journaled two-phase commit is deliberately one linear, auditable sequence (validate -> journal -> stage -> promote -> roll-up); splitting it would scatter the failure-path invariants the round-1 audit mandated
        self,
        df: pl.DataFrame,
        *,
        rng_seed: int,
        hypothesis_id: str = "n/a",
        cost_model_config_sha256: str | None = None,
    ) -> list[PartitionWriteResult]:
        """Validate ``df`` and write it as one parquet file per
        (expert_id, asset, session_date) partition.

        Protocol and guarantees: see the module docstring "Batch write
        protocol" — journaled two-phase commit (stage -> atomic-claim
        promote -> roll-up), with rollback of this run's uncommitted
        promotions on mid-batch failure and a deterministic crash
        recovery procedure.

        ``rng_seed`` is required (not defaulted) so the caller's seed
        discipline is explicit — the ReproLog contract demands the seed
        of the run that produced the returns, and a silent default here
        would launder unseeded producers.
        """
        self.validate_frame(df)

        run_id = uuid.uuid4().hex
        groups = df.group_by(["expert_id", "asset", "session_date"], maintain_order=True)
        planned: list[tuple[str, str, date, pl.DataFrame]] = []
        for (expert_id, asset, session_date), part in groups:
            target = self.partition_dir(expert_id, asset, session_date)
            # Fast pre-check (the authoritative claim is the atomic
            # mkdir at promote time; this just fails the whole batch
            # before any staging I/O).
            if target.exists():
                raise LedgerAppendOnlyError(
                    f"Partition already exists (or is residue of an "
                    f"interrupted run — see journal recovery procedure in "
                    f"the module docstring): {target}. The shadow ledger is "
                    f"append-only (ADR-0003 Decision 3); corrections require "
                    f"a new expert_id@version plus a deprecation record "
                    f"(ShadowLedgerWriter.deprecate)."
                )
            self._assert_no_neighbor_duplicates(expert_id, asset, session_date, part)
            planned.append((expert_id, asset, session_date, part.sort("bar_ts")))

        # Intent journal BEFORE any file lands (crash attributability).
        self._append_journal(
            run_id,
            "begin",
            partitions=[
                {"expert_id": e, "asset": a, "session_date": s.isoformat()}
                for e, a, s, _ in planned
            ],
        )

        staging_root = self.base_dir / "_staging" / run_id
        try:
            staged: list[tuple[str, str, date, pl.DataFrame, Path]] = []
            for expert_id, asset, session_date, part in planned:
                sp = (
                    staging_root
                    / f"expert_id={expert_id}"
                    / f"asset={asset}"
                    / f"session_date={session_date.isoformat()}"
                    / "part-0000.parquet"
                )
                sp.parent.mkdir(parents=True, exist_ok=True)
                part.write_parquet(sp)
                staged.append((expert_id, asset, session_date, part, sp))
        except Exception:
            self._append_journal(run_id, "rolled_back", note="staging failed")
            _rmtree(staging_root)
            raise

        # Promote with atomic per-partition claim.
        # ``claimed`` records every dir the atomic mkdir succeeded on —
        # appended IMMEDIATELY after the claim, before os.replace, so a
        # failure between claim and promote still rolls the empty
        # claimed dir back (round-2 audit QUANT-2-3: the previous
        # version tracked only fully promoted partitions, leaving an
        # empty claimed dir behind that wedged every retry).
        claimed: list[Path] = []
        results: list[PartitionWriteResult] = []
        try:
            for expert_id, asset, session_date, part, sp in staged:
                target = self.partition_dir(expert_id, asset, session_date)
                try:
                    # Atomic claim (CODE-1-4a): exist_ok=False makes the
                    # leaf-dir creation the linearization point; a
                    # concurrent writer loses with FileExistsError and
                    # nothing is overwritten.
                    target.mkdir(parents=True, exist_ok=False)
                except FileExistsError as exc:
                    raise LedgerAppendOnlyError(
                        f"Partition claimed concurrently or already exists: "
                        f"{target}. The shadow ledger is append-only "
                        f"(ADR-0003 Decision 3)."
                    ) from exc
                claimed.append(target)
                final = target / "part-0000.parquet"
                os.replace(sp, final)
                covs = tuple(c for c in part.columns if c.startswith(_COVARIATE_PREFIX))
                results.append(
                    PartitionWriteResult(
                        expert_id=expert_id,
                        asset=asset,
                        session_date=session_date,
                        path=final,
                        n_rows=part.height,
                        file_sha256=file_sha256(final),
                        frame_sha256=frame_sha256(part, sort_cols=["expert_id", "asset", "bar_ts"]),
                        covariate_columns=covs,
                    )
                )
        except Exception:
            # Abort uncommitted work: dirs claimed by THIS run (whether
            # or not their parquet landed) have no roll-up/ReproLog yet,
            # so removing them is not a mutation of committed evidence
            # (module docstring, step 4).
            rollback_failed: list[str] = []
            for claimed_dir in claimed:
                try:
                    (claimed_dir / "part-0000.parquet").unlink(missing_ok=True)
                    claimed_dir.rmdir()
                except OSError as rb_exc:  # pragma: no cover — env-specific
                    rollback_failed.append(f"{claimed_dir}: {rb_exc}")
            if rollback_failed:
                self._append_journal(run_id, "failed_partial", note="; ".join(rollback_failed))
                _log.error(
                    "Shadow ledger rollback incomplete for run %s: %s — "
                    "apply the journal recovery procedure.",
                    run_id,
                    rollback_failed,
                )
            else:
                self._append_journal(run_id, "rolled_back")
            _rmtree(staging_root)
            raise

        # Commit: ReproLog -> roll-ups -> journal committed.
        repro_log = self._emit_repro_log(
            results,
            run_id=run_id,
            rng_seed=rng_seed,
            hypothesis_id=hypothesis_id,
            cost_model_config_sha256=cost_model_config_sha256,
        )
        self._append_rollups(results, run_id=repro_log.run_id)
        self._append_journal(run_id, "committed")
        _rmtree(staging_root)
        if self._update_manifest:
            self._rebuild_data_manifest()

        _log.info("Shadow ledger: wrote %d partition(s), run_id=%s", len(results), run_id)
        return results

    def _assert_no_neighbor_duplicates(
        self, expert_id: str, asset: str, session_date: date, part: pl.DataFrame
    ) -> None:
        """Refuse bar_ts values already present in the +-1-day session
        partitions of the same (expert_id, asset) (QUANT-1-6).

        Defense-in-depth: with session_date enforced as a deterministic
        function of bar_ts, a duplicate bar can only land in the same
        partition — unless a historical partition was written under a
        different (buggy or pre-1.1.0) session rule. +-1 day bounds the
        reach of any session-attribution rule (the CME shift moves a
        timestamp across at most one calendar-date boundary).
        """
        new_ts = part["bar_ts"]
        for delta in (-1, 1):
            neighbor = self.partition_dir(expert_id, asset, session_date + timedelta(days=delta))
            nb_file = neighbor / "part-0000.parquet"
            if not nb_file.is_file():
                continue
            existing_ts = pl.read_parquet(nb_file, columns=["bar_ts"])["bar_ts"]
            overlap = new_ts.filter(new_ts.is_in(existing_ts.implode()))
            if overlap.len() > 0:
                raise LedgerAppendOnlyError(
                    f"{overlap.len()} bar_ts value(s) for ({expert_id!r}, "
                    f"{asset!r}, {session_date}) already exist in the "
                    f"neighboring partition {neighbor} — duplicate bars "
                    f"across session partitions are refused (append-only "
                    f"uniqueness, QUANT-1-6). First: {overlap.head(1).to_list()}."
                )

    # ------------------------------------------------------------------
    # Deprecation path (ADR-0003 Decision 3 correction flow)
    # ------------------------------------------------------------------

    def deprecate(
        self,
        *,
        expert_id: str,
        asset: str,
        session_date: date,
        superseded_by_expert_id: str,
        reason: str,
    ) -> Path:
        """Record that a partition is superseded by a new expert version.

        Appends an immutable JSONL record; the deprecated partition's
        bytes are untouched (ADR-0003 Decision 3: corrections are new
        partitions plus a deprecation record, never in-place edits).
        ``superseded_by_expert_id`` must be a *different* versioned id.
        """
        if "@" not in superseded_by_expert_id:
            raise LedgerSchemaError(
                "superseded_by_expert_id must be versioned as '{name}@{version}'."
            )
        if superseded_by_expert_id == expert_id:
            raise LedgerSchemaError(
                "A partition cannot be superseded by its own expert_id; "
                "bump the version (ADR-0003 Decision 3)."
            )
        target = self.partition_dir(expert_id, asset, session_date)
        if not (target.exists() and any(target.glob("*.parquet"))):
            raise FileNotFoundError(f"No ledger partition to deprecate at {target}.")

        record = {
            "deprecated_partition": {
                "expert_id": expert_id,
                "asset": asset,
                "session_date": session_date.isoformat(),
            },
            "superseded_by_expert_id": superseded_by_expert_id,
            "reason": reason,
            "timestamp_utc": datetime.now(tz=UTC).isoformat(),
        }
        self._append_jsonl(self._deprecation_path, [record])
        _log.info(
            "Shadow ledger: deprecated %s/%s/%s in favor of %s",
            expert_id,
            asset,
            session_date,
            superseded_by_expert_id,
        )
        return self._deprecation_path

    def is_deprecated(self, expert_id: str, asset: str, session_date: date) -> bool:
        """True if a deprecation record exists for the partition."""
        path = self._deprecation_path
        if not path.is_file():
            return False
        key = {
            "expert_id": expert_id,
            "asset": asset,
            "session_date": session_date.isoformat(),
        }
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("deprecated_partition") == key:
                    return True
        return False

    # ------------------------------------------------------------------
    # Read-back (schema-checked, WalkForwardEngine read_run_ledger idiom)
    # ------------------------------------------------------------------

    def read_partition(self, expert_id: str, asset: str, session_date: date) -> pl.DataFrame:
        """Read one partition, enforcing exact column/dtype match so
        silent schema drift surfaces as an error."""
        path = self.partition_dir(expert_id, asset, session_date) / "part-0000.parquet"
        frame = pl.read_parquet(path)
        self.validate_frame(frame)
        return frame

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _emit_repro_log(
        self,
        results: list[PartitionWriteResult],
        *,
        run_id: str,
        rng_seed: int,
        hypothesis_id: str,
        cost_model_config_sha256: str | None,
    ) -> ReproLog:
        """Emit the 13-field ReproLog for this write (ADR-0008 Decision 3).

        ``dataset_checksums`` carries each partition's canonical frame
        SHA-256 keyed by its repo-relative partition path. ``run_id`` is
        the journaled batch id, so journal, roll-ups, and ReproLog
        cross-reference one identifier.
        """
        checksums = {self._relpath(r.path): r.frame_sha256 for r in results}
        log = capture(
            phase="shadow_ledger_write",
            hypothesis_id=hypothesis_id,
            rng_seed=rng_seed,
            dataset_checksums=checksums,
            config_resolved_sha256=cost_model_config_sha256,
            paths=self.paths,
            run_id=run_id,
        )
        out = self.paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
        log.write(out)
        return log

    def _append_journal(
        self,
        run_id: str,
        status: str,
        *,
        partitions: list[dict[str, str]] | None = None,
        note: str | None = None,
    ) -> None:
        record: dict[str, Any] = {
            "run_id": run_id,
            "status": status,
            "timestamp_utc": datetime.now(tz=UTC).isoformat(),
        }
        if partitions is not None:
            record["partitions"] = partitions
        if note is not None:
            record["note"] = note
        self._append_jsonl(self._journal_path, [record])

    def _append_rollups(self, results: list[PartitionWriteResult], *, run_id: str) -> None:
        records = [
            {
                "schema_version": _LEDGER_SCHEMA_VERSION,
                "partition": {
                    "expert_id": r.expert_id,
                    "asset": r.asset,
                    "session_date": r.session_date.isoformat(),
                },
                "path": self._relpath(r.path),
                "n_rows": r.n_rows,
                "file_sha256": r.file_sha256,
                "frame_sha256": r.frame_sha256,
                "covariate_columns": list(r.covariate_columns),
                "run_id": run_id,
                "timestamp_utc": datetime.now(tz=UTC).isoformat(),
            }
            for r in results
        ]
        self._append_jsonl(self._rollup_path, records)

    def _relpath(self, path: Path) -> str:
        try:
            return path.relative_to(self.paths.root).as_posix()
        except ValueError:
            return path.as_posix()

    @staticmethod
    def _append_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
        """Append-only JSONL write: single ``open('ab')`` write under an
        exclusive OS file lock (round-1 audit CODE-1-4b) — concurrent
        appenders serialize on the ``*.lock`` sidecar and cannot lose
        each other's records. Existing bytes are never rewritten.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        data = b"".join(
            (json.dumps(rec, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")
            for rec in records
        )
        with _InterProcessLock(path.with_suffix(path.suffix + ".lock")), open(path, "ab") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())

    def _rebuild_data_manifest(self) -> None:
        """Re-run the project manifest builder so every ledger partition's
        SHA-256 lands in ``data/_manifest.json`` (ADR-0011 Decision 4)."""
        script = self.paths.root / "scripts" / "build_data_manifest.py"
        if not script.is_file():
            _log.warning("Manifest builder not found at %s; skipping.", script)
            return
        subprocess.run(
            [sys.executable, str(script), "--root", str(self.paths.root)],
            check=True,
            capture_output=True,
            timeout=600,
        )


def _rmtree(path: Path) -> None:
    """Best-effort recursive removal of a staging tree (files then dirs)."""
    if not path.is_dir():
        return
    for child in sorted(path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
        try:
            if child.is_file():
                child.unlink()
            elif child.is_dir():
                child.rmdir()
        except OSError:  # pragma: no cover — best-effort cleanup
            _log.debug("Could not remove staging entry %s", child)
    try:
        path.rmdir()
    except OSError:  # pragma: no cover
        _log.debug("Could not remove staging root %s", path)
