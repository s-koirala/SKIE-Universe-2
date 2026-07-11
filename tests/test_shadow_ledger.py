"""Shadow-ledger writer tests (ADR-0003).

Covers: typed-schema validation on write (incl. session-date integrity
per the shared CME rule and the pre-registered covariate set), atomic
append-only refusal, cross-partition duplicate refusal, the deprecation
correction path, journaled two-phase commit, SHA-256 roll-up presence,
and ReproLog emission (13-field schema).
"""

from __future__ import annotations

import json
import os
import shutil
import threading
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import polars as pl
import pytest

from skie_universe2.ledger.shadow_ledger import (
    LedgerAppendOnlyError,
    LedgerSchemaError,
    ShadowLedgerWriter,
    _InterProcessLock,
)
from skie_universe2.utils.paths import ProjectPaths

# The 13-field ReproLog contract (CLAUDE.md reproducibility contract;
# emit-repro-log skill schema).
_REPRO_FIELDS = {
    "run_id",
    "phase",
    "hypothesis_id",
    "timestamp_utc",
    "git_head",
    "pip_freeze_sha256",
    "pip_freeze_path",
    "dataset_checksums",
    "rng_seed",
    "model_hash",
    "config_resolved_sha256",
    "host",
    "env_id",
}

# Fixture covariate registry: family toy_momentum_cov registers exactly
# one covariate; family toy_momentum registers none (so plain frames
# pass and covariate frames under the wrong family are refused).
_COVARIATES_YAML = """
schema_version: 1
expert_families:
  toy_momentum_cov:
    registered_at: "2026-07-10"
    covariates:
      - cov_realized_vol_60m
"""


def _ledger_frame(
    expert_id: str = "toy_momentum@1.0.0",
    asset: str = "ES",
    session_date: date = date(2025, 1, 6),
    n: int = 5,
    with_covariate: bool = False,
) -> pl.DataFrame:
    # 14:30 UTC = 08:30 CT -> CME session date == calendar date, so the
    # session-integrity check holds by construction for any weekday.
    base_ts = datetime(session_date.year, session_date.month, session_date.day, 14, 30, tzinfo=UTC)
    data = {
        "expert_id": [expert_id] * n,
        "asset": [asset] * n,
        "bar_ts": [base_ts + timedelta(minutes=i) for i in range(n)],
        "session_date": [session_date] * n,
        "ret_gross": [0.0001 * (i + 1) for i in range(n)],
        "ret_net": [0.0001 * (i + 1) - 0.00002 for i in range(n)],
        "cost_model_id": ["bar_cost_v0@0.1.0"] * n,
        "fidelity_tier": [0] * n,
    }
    schema = {
        "expert_id": pl.Utf8,
        "asset": pl.Utf8,
        "bar_ts": pl.Datetime("us", "UTC"),
        "session_date": pl.Date,
        "ret_gross": pl.Float64,
        "ret_net": pl.Float64,
        "cost_model_id": pl.Utf8,
        "fidelity_tier": pl.Int64,
    }
    if with_covariate:
        data["cov_realized_vol_60m"] = [0.01 + 0.001 * i for i in range(n)]
        schema["cov_realized_vol_60m"] = pl.Float64
    return pl.DataFrame(data, schema=schema)


@pytest.fixture()
def writer(tmp_path: Path) -> ShadowLedgerWriter:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "covariates.yaml").write_text(_COVARIATES_YAML, encoding="utf-8")
    return ShadowLedgerWriter(
        paths=ProjectPaths(root=tmp_path),
        update_manifest=False,  # temp root has no manifest builder
    )


class TestSchemaValidation:
    def test_valid_frame_writes(self, writer: ShadowLedgerWriter) -> None:
        results = writer.write_partitions(_ledger_frame(), rng_seed=42)
        assert len(results) == 1
        assert results[0].path.is_file()
        assert results[0].n_rows == 5

    def test_registered_covariate_columns_accepted(self, writer: ShadowLedgerWriter) -> None:
        results = writer.write_partitions(
            _ledger_frame(expert_id="toy_momentum_cov@1.0.0", with_covariate=True),
            rng_seed=42,
        )
        assert results[0].covariate_columns == ("cov_realized_vol_60m",)

    def test_unversioned_expert_id_rejected(self, writer: ShadowLedgerWriter) -> None:
        df = _ledger_frame(expert_id="toy_momentum")  # no @version
        with pytest.raises(LedgerSchemaError, match="versioned"):
            writer.write_partitions(df, rng_seed=42)

    def test_wrong_dtype_rejected(self, writer: ShadowLedgerWriter) -> None:
        df = _ledger_frame().with_columns(pl.col("fidelity_tier").cast(pl.Int32))
        with pytest.raises(LedgerSchemaError, match="dtype mismatch"):
            writer.write_partitions(df, rng_seed=42)

    def test_missing_column_rejected(self, writer: ShadowLedgerWriter) -> None:
        df = _ledger_frame().drop("cost_model_id")
        with pytest.raises(LedgerSchemaError, match="schema mismatch"):
            writer.write_partitions(df, rng_seed=42)

    def test_non_covariate_extra_column_rejected(self, writer: ShadowLedgerWriter) -> None:
        df = _ledger_frame().with_columns(pl.lit(1.0).alias("stray"))
        with pytest.raises(LedgerSchemaError, match="Non-covariate"):
            writer.write_partitions(df, rng_seed=42)

    def test_invalid_fidelity_tier_rejected(self, writer: ShadowLedgerWriter) -> None:
        df = _ledger_frame().with_columns(pl.lit(3).cast(pl.Int64).alias("fidelity_tier"))
        with pytest.raises(LedgerSchemaError, match="fidelity_tier"):
            writer.write_partitions(df, rng_seed=42)

    def test_null_values_rejected(self, writer: ShadowLedgerWriter) -> None:
        df = _ledger_frame().with_columns(
            pl.when(pl.arange(0, pl.len()) == 0)
            .then(None)
            .otherwise(pl.col("ret_net"))
            .alias("ret_net")
        )
        with pytest.raises(LedgerSchemaError, match="Null"):
            writer.write_partitions(df, rng_seed=42)

    def test_duplicate_bar_rejected(self, writer: ShadowLedgerWriter) -> None:
        df = _ledger_frame()
        dup = pl.concat([df, df.tail(1)])
        with pytest.raises(LedgerSchemaError, match="Duplicate"):
            writer.write_partitions(dup, rng_seed=42)

    def test_empty_frame_rejected(self, writer: ShadowLedgerWriter) -> None:
        with pytest.raises(LedgerSchemaError, match="empty"):
            writer.write_partitions(_ledger_frame().head(0), rng_seed=42)

    def test_session_date_mismatch_rejected(self, writer: ShadowLedgerWriter) -> None:
        """QUANT-1-6: session_date must equal the shared CME rule applied
        to bar_ts."""
        df = _ledger_frame().with_columns(pl.lit(date(2025, 1, 8)).alias("session_date"))
        with pytest.raises(LedgerSchemaError, match="session rule"):
            writer.write_partitions(df, rng_seed=42)

    def test_read_partition_roundtrip_validates(self, writer: ShadowLedgerWriter) -> None:
        writer.write_partitions(_ledger_frame(), rng_seed=42)
        frame = writer.read_partition("toy_momentum@1.0.0", "ES", date(2025, 1, 6))
        assert frame.height == 5
        assert frame["ret_net"].dtype == pl.Float64


class TestCovariateRegistry:
    """QUANT-1-7: exact-set equality against config/covariates.yaml."""

    def test_unregistered_covariate_refused(self, writer: ShadowLedgerWriter) -> None:
        # Family toy_momentum has no registered covariates.
        df = _ledger_frame(with_covariate=True)  # expert toy_momentum@1.0.0
        with pytest.raises(LedgerSchemaError, match="Covariate-set mismatch"):
            writer.write_partitions(df, rng_seed=42)

    def test_missing_registered_covariate_refused(self, writer: ShadowLedgerWriter) -> None:
        # Family toy_momentum_cov registers one covariate; frame has none.
        df = _ledger_frame(expert_id="toy_momentum_cov@1.0.0")
        with pytest.raises(LedgerSchemaError, match="Covariate-set mismatch"):
            writer.write_partitions(df, rng_seed=42)

    def test_missing_registry_file_refuses_covariates(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        w = ShadowLedgerWriter(paths=ProjectPaths(root=tmp_path), update_manifest=False)
        df = _ledger_frame(expert_id="toy_momentum_cov@1.0.0", with_covariate=True)
        with pytest.raises(LedgerSchemaError, match="Covariate-set mismatch"):
            w.write_partitions(df, rng_seed=42)


class TestAppendOnly:
    def test_rewrite_of_existing_partition_refused(self, writer: ShadowLedgerWriter) -> None:
        writer.write_partitions(_ledger_frame(), rng_seed=42)
        with pytest.raises(LedgerAppendOnlyError, match="append-only"):
            writer.write_partitions(_ledger_frame(), rng_seed=42)

    def test_residue_partition_dir_refused(self, writer: ShadowLedgerWriter) -> None:
        """An empty partition dir (crash residue) also refuses the write —
        the atomic mkdir claim cannot be re-acquired; recovery goes
        through the journal procedure."""
        writer.partition_dir("toy_momentum@1.0.0", "ES", date(2025, 1, 6)).mkdir(parents=True)
        with pytest.raises(LedgerAppendOnlyError):
            writer.write_partitions(_ledger_frame(), rng_seed=42)

    def test_refusal_precedes_any_write(self, writer: ShadowLedgerWriter) -> None:
        """A batch containing one pre-existing partition writes NOTHING
        (pre-check before journal/staging)."""
        writer.write_partitions(_ledger_frame(session_date=date(2025, 1, 6)), rng_seed=42)
        day2 = _ledger_frame(session_date=date(2025, 1, 7))
        batch = pl.concat([_ledger_frame(session_date=date(2025, 1, 6)), day2])
        with pytest.raises(LedgerAppendOnlyError):
            writer.write_partitions(batch, rng_seed=42)
        # Day-2 partition must NOT have been created by the failed batch.
        assert not writer.partition_dir("toy_momentum@1.0.0", "ES", date(2025, 1, 7)).exists()
        # And the failed batch left no staging residue.
        staging = writer.base_dir / "_staging"
        assert not staging.exists() or not any(staging.iterdir())

    def test_neighbor_duplicate_bar_ts_refused(self, writer: ShadowLedgerWriter) -> None:
        """QUANT-1-6 defense-in-depth: a bar_ts already present in a
        +-1-day neighbor partition (e.g. written under an older session
        rule) is refused. The neighbor is crafted manually to simulate a
        historical mislabeled partition."""
        df = _ledger_frame(session_date=date(2025, 1, 6))
        neighbor_dir = writer.partition_dir("toy_momentum@1.0.0", "ES", date(2025, 1, 5))
        neighbor_dir.mkdir(parents=True)
        # Historical partition mislabeled: carries a bar_ts that the CME
        # rule maps to 2025-01-06.
        df.write_parquet(neighbor_dir / "part-0000.parquet")
        with pytest.raises(LedgerAppendOnlyError, match="neighboring partition"):
            writer.write_partitions(df, rng_seed=42)

    def test_new_version_is_new_partition_family(self, writer: ShadowLedgerWriter) -> None:
        writer.write_partitions(_ledger_frame(expert_id="toy_momentum@1.0.0"), rng_seed=42)
        # Same asset/session under a bumped version is allowed.
        writer.write_partitions(_ledger_frame(expert_id="toy_momentum@1.0.1"), rng_seed=42)

    def test_deprecation_path(self, writer: ShadowLedgerWriter) -> None:
        writer.write_partitions(_ledger_frame(expert_id="toy_momentum@1.0.0"), rng_seed=42)
        writer.write_partitions(_ledger_frame(expert_id="toy_momentum@1.0.1"), rng_seed=42)
        writer.deprecate(
            expert_id="toy_momentum@1.0.0",
            asset="ES",
            session_date=date(2025, 1, 6),
            superseded_by_expert_id="toy_momentum@1.0.1",
            reason="unit-test correction flow",
        )
        assert writer.is_deprecated("toy_momentum@1.0.0", "ES", date(2025, 1, 6))
        # Deprecation never deletes bytes.
        assert (
            writer.partition_dir("toy_momentum@1.0.0", "ES", date(2025, 1, 6)) / "part-0000.parquet"
        ).is_file()
        # And still refuses overwrite of the deprecated partition.
        with pytest.raises(LedgerAppendOnlyError):
            writer.write_partitions(_ledger_frame(expert_id="toy_momentum@1.0.0"), rng_seed=42)

    def test_deprecate_requires_distinct_version(self, writer: ShadowLedgerWriter) -> None:
        writer.write_partitions(_ledger_frame(), rng_seed=42)
        with pytest.raises(LedgerSchemaError, match="own expert_id"):
            writer.deprecate(
                expert_id="toy_momentum@1.0.0",
                asset="ES",
                session_date=date(2025, 1, 6),
                superseded_by_expert_id="toy_momentum@1.0.0",
                reason="x",
            )


class TestJournalRollupsReproLog:
    def test_journal_begin_and_committed(self, writer: ShadowLedgerWriter) -> None:
        """CODE-1-3: every batch is journaled begin -> committed with one
        run_id shared by journal, roll-ups, and ReproLog filename."""
        writer.write_partitions(_ledger_frame(), rng_seed=42)
        journal_path = writer.base_dir / "_journal" / "journal.jsonl"
        records = [
            json.loads(line)
            for line in journal_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert [r["status"] for r in records] == ["begin", "committed"]
        assert records[0]["run_id"] == records[1]["run_id"]
        assert records[0]["partitions"] == [
            {"expert_id": "toy_momentum@1.0.0", "asset": "ES", "session_date": "2025-01-06"}
        ]
        run_id = records[0]["run_id"]
        rollups = [
            json.loads(line)
            for line in (writer.base_dir / "_rollups" / "rollups.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        assert rollups[0]["run_id"] == run_id
        assert (writer.paths.logs_reproducibility / f"repro_log_{run_id}.json").is_file()

    def test_staging_cleaned_after_commit(self, writer: ShadowLedgerWriter) -> None:
        writer.write_partitions(_ledger_frame(), rng_seed=42)
        staging = writer.base_dir / "_staging"
        assert not staging.exists() or not any(staging.iterdir())

    def test_rollup_records_present(self, writer: ShadowLedgerWriter) -> None:
        results = writer.write_partitions(
            _ledger_frame(expert_id="toy_momentum_cov@1.0.0", with_covariate=True),
            rng_seed=42,
        )
        rollup_path = writer.base_dir / "_rollups" / "rollups.jsonl"
        assert rollup_path.is_file()
        records = [
            json.loads(line)
            for line in rollup_path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert len(records) == 1
        rec = records[0]
        assert rec["file_sha256"] == results[0].file_sha256
        assert rec["frame_sha256"] == results[0].frame_sha256
        assert len(rec["file_sha256"]) == 64
        assert len(rec["frame_sha256"]) == 64
        assert rec["partition"] == {
            "expert_id": "toy_momentum_cov@1.0.0",
            "asset": "ES",
            "session_date": "2025-01-06",
        }
        assert rec["covariate_columns"] == ["cov_realized_vol_60m"]

    def test_rollups_append_across_writes(self, writer: ShadowLedgerWriter) -> None:
        writer.write_partitions(_ledger_frame(expert_id="a@1"), rng_seed=42)
        writer.write_partitions(_ledger_frame(expert_id="b@1"), rng_seed=42)
        rollup_path = writer.base_dir / "_rollups" / "rollups.jsonl"
        lines = [ln for ln in rollup_path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        assert len(lines) == 2

    def test_repro_log_emitted_with_13_fields(self, writer: ShadowLedgerWriter) -> None:
        results = writer.write_partitions(_ledger_frame(), rng_seed=7)
        log_dir = writer.paths.logs_reproducibility
        logs = sorted(log_dir.glob("repro_log_*.json"))
        assert len(logs) == 1
        payload = json.loads(logs[0].read_text(encoding="utf-8"))
        assert set(payload.keys()) == _REPRO_FIELDS
        assert payload["phase"] == "shadow_ledger_write"
        assert payload["rng_seed"] == 7
        # dataset_checksums carries the partition frame hash.
        assert list(payload["dataset_checksums"].values()) == [results[0].frame_sha256]

    def test_manifest_rebuild_records_partition_sha(self, tmp_path: Path) -> None:
        """With update_manifest=True and the real manifest builder copied
        into the temp root, the partition file SHA lands in
        data/_manifest.json (ADR-0011 Decision 4)."""
        repo_root = Path(__file__).resolve().parent.parent
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        (tmp_path / "scripts").mkdir()
        shutil.copy2(
            repo_root / "scripts" / "build_data_manifest.py",
            tmp_path / "scripts" / "build_data_manifest.py",
        )
        w = ShadowLedgerWriter(paths=ProjectPaths(root=tmp_path), update_manifest=True)
        results = w.write_partitions(_ledger_frame(), rng_seed=42)
        manifest = json.loads((tmp_path / "data" / "_manifest.json").read_text(encoding="utf-8"))
        rel = results[0].path.relative_to(tmp_path).as_posix()
        assert rel in manifest["files"]
        assert manifest["files"][rel]["sha256"] == results[0].file_sha256


class TestFailurePathsAndConcurrency:
    """Round-2 audit QUANT-2-3 + QUANT-2-5/REPRODUCIBILITY-2-3: the
    crash/rollback machinery and the JSONL lock are exercised, not just
    asserted in docstrings.

    Concurrency-test design choice (documented per the audit's explicit
    allowance): threads rather than ``subprocess.Popen`` — spawning
    Python subprocesses on this Windows box under the sandboxed test
    runner is slow and flaky, while threads exercise the identical
    ``_InterProcessLock`` code path (each acquisition opens its OWN
    file handle, and both msvcrt region locks and flock contend between
    handles regardless of which thread/process owns them), plus a
    direct held-lock contention test below.
    """

    @staticmethod
    def _three_day_batch() -> pl.DataFrame:
        return pl.concat(
            [
                _ledger_frame(session_date=date(2025, 1, 6)),
                _ledger_frame(session_date=date(2025, 1, 7)),
                _ledger_frame(session_date=date(2025, 1, 8)),
            ]
        )

    @staticmethod
    def _journal_statuses(writer: ShadowLedgerWriter) -> list[str]:
        path = writer.base_dir / "_journal" / "journal.jsonl"
        if not path.is_file():
            return []
        return [
            json.loads(line)["status"]
            for line in path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]

    def test_mid_promote_failure_rolls_back_claimed_dir_and_retries(
        self, writer: ShadowLedgerWriter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """QUANT-2-3 regression: os.replace fails on partition 2 of 3 ->
        partition 1 (fully promoted) is removed, partition 2's CLAIMED
        empty dir is removed, 'rolled_back' is journaled, and the SAME
        batch retries successfully afterwards."""
        batch = self._three_day_batch()
        real_replace = os.replace

        def failing_replace(src, dst, *args, **kwargs):
            d = str(dst)
            if "expert_id=" in d and "session_date=2025-01-07" in d and "_staging" not in d:
                raise RuntimeError("injected promote failure (QUANT-2-3 test)")
            return real_replace(src, dst, *args, **kwargs)

        with monkeypatch.context() as m:
            m.setattr(os, "replace", failing_replace)
            with pytest.raises(RuntimeError, match="injected promote failure"):
                writer.write_partitions(batch, rng_seed=42)

        # Partition 1 (promoted before the failure) fully removed.
        assert not writer.partition_dir("toy_momentum@1.0.0", "ES", date(2025, 1, 6)).exists()
        # Partition 2's claimed-but-unpromoted dir removed (the round-2 bug).
        assert not writer.partition_dir("toy_momentum@1.0.0", "ES", date(2025, 1, 7)).exists()
        # Partition 3 never claimed.
        assert not writer.partition_dir("toy_momentum@1.0.0", "ES", date(2025, 1, 8)).exists()
        assert self._journal_statuses(writer) == ["begin", "rolled_back"]
        # No roll-up records for the aborted run.
        assert not (writer.base_dir / "_rollups" / "rollups.jsonl").exists()

        # The SAME batch retries cleanly (nothing wedged).
        results = writer.write_partitions(batch, rng_seed=42)
        assert len(results) == 3
        assert self._journal_statuses(writer) == ["begin", "rolled_back", "begin", "committed"]

    def test_staging_failure_journals_rolled_back(
        self, writer: ShadowLedgerWriter, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Staging-phase exception -> 'rolled_back' journal record, no
        partition dirs created, staging cleaned."""
        real_write = pl.DataFrame.write_parquet

        def failing_write(self, file, *args, **kwargs):
            if "_staging" in str(file):
                raise RuntimeError("injected staging failure")
            return real_write(self, file, *args, **kwargs)

        with monkeypatch.context() as m:
            m.setattr(pl.DataFrame, "write_parquet", failing_write)
            with pytest.raises(RuntimeError, match="injected staging failure"):
                writer.write_partitions(_ledger_frame(), rng_seed=42)

        assert self._journal_statuses(writer) == ["begin", "rolled_back"]
        assert not writer.partition_dir("toy_momentum@1.0.0", "ES", date(2025, 1, 6)).exists()
        staging = writer.base_dir / "_staging"
        assert not staging.exists() or not any(staging.iterdir())

    def test_concurrent_writers_lose_no_records(self, writer: ShadowLedgerWriter) -> None:
        """Two writers appending simultaneously through the public API:
        every journal and roll-up record survives (locked single-write
        appends; round-1 CODE-1-4b machinery under actual contention)."""
        barrier = threading.Barrier(2)
        errors: list[BaseException] = []

        def run(expert_id: str) -> None:
            try:
                barrier.wait(timeout=30)
                writer.write_partitions(_ledger_frame(expert_id=expert_id), rng_seed=42)
            except BaseException as exc:  # noqa: BLE001 — surfaced via the errors list
                errors.append(exc)

        threads = [
            threading.Thread(target=run, args=("conc_a@1",)),
            threading.Thread(target=run, args=("conc_b@1",)),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=120)
        assert errors == []

        rollups = [
            json.loads(line)
            for line in (writer.base_dir / "_rollups" / "rollups.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
            if line.strip()
        ]
        assert sorted(r["partition"]["expert_id"] for r in rollups) == ["conc_a@1", "conc_b@1"]
        statuses = self._journal_statuses(writer)
        assert len(statuses) == 4
        assert sorted(statuses) == ["begin", "begin", "committed", "committed"]

    @pytest.mark.skipif(os.name != "nt", reason="msvcrt lock-timeout semantics are Windows-only")
    def test_held_lock_surfaces_oserror_not_corruption(self, writer: ShadowLedgerWriter) -> None:
        """Windows msvcrt.locking retries ~10x at 1 s intervals then
        raises OSError (documented in the module recovery procedure):
        a writer stalled behind a held lock FAILS LOUDLY and writes
        nothing — no partial JSONL line. Runtime ~10 s by design of the
        msvcrt retry loop."""
        rollup_path = writer.base_dir / "_rollups" / "rollups.jsonl"
        lock_path = rollup_path.with_suffix(rollup_path.suffix + ".lock")
        with _InterProcessLock(lock_path), pytest.raises(OSError):
            writer._append_jsonl(rollup_path, [{"probe": 1}])
        # Nothing was written under contention.
        assert not rollup_path.exists() or rollup_path.read_text(encoding="utf-8") == ""
