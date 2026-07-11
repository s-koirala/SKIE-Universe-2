"""ADR-0011 Decision 3 registry-refusal behavior.

The ingest must refuse sources not registered in
``config/data_sources.yaml``, refuse reference-only kinds, and refuse
symbols outside a source's registered symbol set.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from skie_universe2.data.ingest.vendor_legacy_1min import (
    VendorLegacy1minIngestJob,
    _SourceFile,
)
from skie_universe2.data.sources import (
    UnregisteredSourceError,
    assert_symbols_registered,
    load_registry,
    resolve_ingest_source,
)
from skie_universe2.utils.paths import ProjectPaths


@pytest.fixture()
def registry_yaml(tmp_path: Path) -> Path:
    p = tmp_path / "data_sources.yaml"
    p.write_text(
        """
schema_version: 1
sources:
  vendor_skie_ninja_legacy_raw_1min:
    kind: vendor_raw
    location: "{store}"
    symbols: [ES, NQ]
  reference_only_entry:
    kind: sibling_repo_reference
    location: "{store}"
    usable_as_evidence: false
""".format(store=(tmp_path / "store").as_posix()),
        encoding="utf-8",
    )
    (tmp_path / "store").mkdir()
    return p


class TestRegistryResolution:
    def test_registered_source_resolves(self, registry_yaml: Path) -> None:
        rec = resolve_ingest_source("vendor_skie_ninja_legacy_raw_1min", config_path=registry_yaml)
        assert rec.kind == "vendor_raw"
        assert rec.symbols == ("ES", "NQ")

    def test_unregistered_source_refused(self, registry_yaml: Path) -> None:
        with pytest.raises(UnregisteredSourceError, match="not registered"):
            resolve_ingest_source("not_a_source", config_path=registry_yaml)

    def test_reference_only_kind_refused(self, registry_yaml: Path) -> None:
        """sibling_repo_reference entries are benchmarks, not ingest
        sources (ADR-0011 Decision 2)."""
        with pytest.raises(UnregisteredSourceError, match="not ingestable"):
            resolve_ingest_source("reference_only_entry", config_path=registry_yaml)

    def test_missing_registry_file_refused(self, tmp_path: Path) -> None:
        with pytest.raises(UnregisteredSourceError, match="registry not found|not found"):
            resolve_ingest_source(
                "vendor_skie_ninja_legacy_raw_1min",
                config_path=tmp_path / "absent.yaml",
            )

    def test_unregistered_symbol_refused(self, registry_yaml: Path) -> None:
        rec = resolve_ingest_source("vendor_skie_ninja_legacy_raw_1min", config_path=registry_yaml)
        with pytest.raises(UnregisteredSourceError, match="not registered for source"):
            assert_symbols_registered(rec, ("ES", "ZC"))


class TestFetchGate:
    def test_fetch_refuses_unregistered_symbol(self, registry_yaml: Path, tmp_path: Path) -> None:
        """End-to-end: the job's fetch() raises before touching any file
        when a requested symbol is not registered."""
        job = VendorLegacy1minIngestJob(
            symbols=("MGC",),  # in the canonical list but NOT in this registry
            registry_config_path=registry_yaml,
        )

        class _Ctx:
            paths = ProjectPaths(root=tmp_path)
            log = None

        with pytest.raises(UnregisteredSourceError, match="not registered for source"):
            job.fetch(date(2015, 1, 1), date(2025, 12, 31), _Ctx())

    def test_fetch_uses_project_registry(self) -> None:
        """The real project registry admits ES/NQ for the raw store."""
        sources = load_registry()
        assert "vendor_skie_ninja_legacy_raw_1min" in sources
        rec = resolve_ingest_source("vendor_skie_ninja_legacy_raw_1min")
        assert "ES" in rec.symbols
        assert "NQ" in rec.symbols

    def test_benchmark_entry_is_not_ingestable(self) -> None:
        """The registered 1.0 benchmark output must never be consumable
        as an ingest source (ADR-0011 Decision 2)."""
        with pytest.raises(UnregisteredSourceError, match="not ingestable"):
            resolve_ingest_source("skie_universe_1_processed_roll_adjusted")


class TestFetchFailClosed:
    """Round-1 audit CODE-1-5: missing canonical CSVs abort the fetch
    unless allow_missing_sources is set explicitly (and then the gaps
    are recorded for provenance)."""

    @staticmethod
    def _two_source_job(tmp_path: Path, registry_yaml: Path, **kwargs):
        store = tmp_path / "store"
        (store / "ES_2015_1min_databento.csv").write_text("x", encoding="utf-8")
        sources = (
            _SourceFile("ES", "backfill_2015", "ES_2015_1min_databento.csv"),
            _SourceFile("ES", "backfill_2016", "ES_2016_1min_databento.csv"),  # absent
        )
        return VendorLegacy1minIngestJob(
            source_root=store,
            sources=sources,
            symbols=("ES",),
            registry_config_path=registry_yaml,
            **kwargs,
        )

    def test_missing_source_raises_listing_all(self, registry_yaml: Path, tmp_path: Path) -> None:
        job = self._two_source_job(tmp_path, registry_yaml)

        class _Ctx:
            paths = ProjectPaths(root=tmp_path)
            log = None

        with pytest.raises(FileNotFoundError, match="ES_2016_1min_databento.csv"):
            job.fetch(date(2015, 1, 1), date(2016, 12, 31), _Ctx())

    def test_allow_missing_downgrades_and_records(
        self, registry_yaml: Path, tmp_path: Path
    ) -> None:
        job = self._two_source_job(tmp_path, registry_yaml, allow_missing_sources=True)

        class _Ctx:
            paths = ProjectPaths(root=tmp_path)
            log = None

        out = job.fetch(date(2015, 1, 1), date(2016, 12, 31), _Ctx())
        assert [p.name for p in out] == ["ES_2015_1min_databento.csv"]
        # The accepted gap is retained for the provenance record.
        assert len(job._last_missing_sources) == 1
        assert "ES_2016_1min_databento.csv" in job._last_missing_sources[0]
