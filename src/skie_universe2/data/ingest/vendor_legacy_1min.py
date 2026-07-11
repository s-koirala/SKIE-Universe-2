"""Vendor-legacy 1-minute ES/NQ/MCL/MGC/SIL ingest (Databento, machine-level store).

Port of SKIE-Universe 1.0 ``src/skie_ninja/data/ingest/vendor_legacy_1min.py``
(sibling repo). Parse/validate/write logic is preserved verbatim
(numerical-fidelity requirement); the **fetch stage is adapted** for the
ADR-0011 two-level layout: 1.0 fetched by *copying* CSVs from the
SKIE-Ninja research repo into the machine-level store
``~/datasets/vendor_skie_ninja_legacy/raw_1min/``; in 2.0 that store IS
the registered upstream (``vendor_skie_ninja_legacy_raw_1min`` in
[config/data_sources.yaml](../../../../config/data_sources.yaml)), so
fetch *locates* files in place and never writes into ``~/datasets``
(ADR-0011 Decision 1: data flows raw -> processed, one direction).

Fetch refuses to run when the source or any requested symbol is not
registered (ADR-0011 Decision 3), via
:func:`skie_universe2.data.sources.resolve_ingest_source`.

Source files (canonical list, mirroring the 1.0 store state):
  - ES/NQ per-year files 2015-2022 + 2025 + 2026 (2026 file spans H1;
    byte-identical to the ``*_2026H1_*`` alias in the store)
  - ES/NQ undated files (in-sample 2023-2024)
  - MCL/MGC/SIL single-file full-history pulls (+ MGC/SIL 2026)

Provenance: emits
``data/processed/_provenance/vendor_legacy_1min_{YYYYMMDD}.json`` with
per-source SHA256 + reproducibility-log attachment.

Conforms to the ``IngestJob`` protocol defined in ``_registry.py``.

Vendor chain: Databento GLBX.MDP3 ``ohlcv-1m`` -> machine-level store.
License status recorded in the registry entry (verified 2026-04-23,
1.0 audit trail).
"""

from __future__ import annotations

import contextlib
import json
import logging
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path

import polars as pl

from skie_universe2.data.ingest._registry import register
from skie_universe2.data.sources import (
    assert_symbols_registered,
    resolve_ingest_source,
)
from skie_universe2.data.validation.schema import VendorLegacy1minSchema
from skie_universe2.utils.hashing import file_sha256
from skie_universe2.utils.paths import portable_key
from skie_universe2.utils.runcontext import RunContext

_log = logging.getLogger(__name__)

# Dataset name + version registered in INGEST_REGISTRY.
_DATASET_NAME = "vendor_legacy_1min"
# 1.0 lineage: 0.1.0 (copy-based fetch). 2.0 bump: locate-in-place fetch
# gated by the ADR-0011 registry; parse/validate/write unchanged.
_DATASET_VERSION = "0.2.0"

# Registry key for the machine-level raw store (ADR-0011 Decision 3).
_SOURCE_REGISTRY_KEY = "vendor_skie_ninja_legacy_raw_1min"


@dataclass(frozen=True)
class _SourceFile:
    """One source CSV with its symbol, coverage label, and filename."""

    symbol: str
    coverage: str
    filename: str


# Canonical list — mirrors the 1.0 ``_CANONICAL_SOURCES`` (Phase O.8
# state) against the current store contents. The SHA256 idempotency
# guard in scripts/ingest.py means unchanged files are not re-processed.
_CANONICAL_SOURCES: tuple[_SourceFile, ...] = (
    _SourceFile("ES", "backfill_2015", "ES_2015_1min_databento.csv"),
    _SourceFile("ES", "backfill_2016", "ES_2016_1min_databento.csv"),
    _SourceFile("ES", "backfill_2017", "ES_2017_1min_databento.csv"),
    _SourceFile("ES", "backfill_2018", "ES_2018_1min_databento.csv"),
    _SourceFile("ES", "backfill_2019", "ES_2019_1min_databento.csv"),
    _SourceFile("ES", "oos_2020", "ES_2020_1min_databento.csv"),
    _SourceFile("ES", "oos_2021", "ES_2021_1min_databento.csv"),
    _SourceFile("ES", "oos_2022", "ES_2022_1min_databento.csv"),
    _SourceFile("ES", "in_sample_2023_2024", "ES_1min_databento.csv"),
    _SourceFile("ES", "forward_2025", "ES_2025_1min_databento.csv"),
    _SourceFile("ES", "forward_2026_h1", "ES_2026_1min_databento.csv"),
    _SourceFile("NQ", "backfill_2015", "NQ_2015_1min_databento.csv"),
    _SourceFile("NQ", "backfill_2016", "NQ_2016_1min_databento.csv"),
    _SourceFile("NQ", "backfill_2017", "NQ_2017_1min_databento.csv"),
    _SourceFile("NQ", "backfill_2018", "NQ_2018_1min_databento.csv"),
    _SourceFile("NQ", "backfill_2019", "NQ_2019_1min_databento.csv"),
    _SourceFile("NQ", "oos_2020", "NQ_2020_1min_databento.csv"),
    _SourceFile("NQ", "oos_2021", "NQ_2021_1min_databento.csv"),
    _SourceFile("NQ", "oos_2022", "NQ_2022_1min_databento.csv"),
    _SourceFile("NQ", "in_sample_2023_2024", "NQ_1min_databento.csv"),
    _SourceFile("NQ", "forward_2025", "NQ_2025_1min_databento.csv"),
    _SourceFile("NQ", "forward_2026_h1", "NQ_2026_1min_databento.csv"),
    # Metals/energy: single-file-per-symbol full-window pulls. NOT
    # materialized in the Phase C run (ES/NQ only per the dwell-time
    # study scope); listed so a later rerun is a --symbols flag away.
    _SourceFile("MCL", "full_2015_2025", "MCL_1min_databento.csv"),
    _SourceFile("MGC", "full_2015_2025", "MGC_1min_databento.csv"),
    _SourceFile("SIL", "full_2015_2025", "SIL_1min_databento.csv"),
    _SourceFile("MGC", "forward_2026_h1", "MGC_2026_1min_databento.csv"),
    _SourceFile("SIL", "forward_2026_h1", "SIL_2026_1min_databento.csv"),
)


class VendorLegacy1minIngestJob:
    """Ingest job for the vendor_skie_ninja_legacy raw 1-minute CSVs."""

    name: str = _DATASET_NAME
    version: str = _DATASET_VERSION

    def __init__(
        self,
        source_root: Path | None = None,
        sources: tuple[_SourceFile, ...] | None = None,
        symbols: tuple[str, ...] | None = None,
        registry_config_path: Path | None = None,
        allow_missing_sources: bool = False,
    ) -> None:
        """``symbols`` filters the canonical list (Phase C: ES/NQ only).

        ``source_root`` / ``registry_config_path`` exist for tests; the
        production path resolves both through the ADR-0011 registry.

        ``allow_missing_sources``: fetch is fail-closed by default
        (round-1 audit CODE-1-5) — a missing canonical CSV raises
        ``FileNotFoundError`` listing every absent file, because a
        silently partial substrate materializes holes into evidence.
        Setting True (CLI ``--allow-missing``) downgrades to WARNING and
        records the accepted gaps in provenance
        (``allow_missing_sources`` + ``missing_sources``).
        """
        self._source_root_override = Path(source_root) if source_root else None
        self._sources = sources if sources is not None else _CANONICAL_SOURCES
        self._symbols = tuple(symbols) if symbols is not None else None
        self._registry_config_path = registry_config_path
        self._allow_missing_sources = allow_missing_sources
        # Populated by fetch(); consumed by emit_provenance so accepted
        # gaps are part of the provenance record.
        self._last_missing_sources: list[str] = []

    def _selected_sources(self) -> tuple[_SourceFile, ...]:
        if self._symbols is None:
            return self._sources
        return tuple(s for s in self._sources if s.symbol in self._symbols)

    # ------------------------------------------------------------------
    # fetch: locate CSVs in the registered machine-level store
    # ------------------------------------------------------------------

    def fetch(self, start: date, end: date, ctx: RunContext) -> list[Path]:
        """Locate source CSVs in the registered machine-level store.

        The date range is accepted for CLI-parity but does not slice —
        the canonical file list is all-or-nothing per symbol (each file
        is one coverage slice already). Refuses to run if the source or
        any requested symbol is unregistered (ADR-0011 Decision 3).
        """
        del start, end  # unused; kept for IngestJob protocol parity

        record = resolve_ingest_source(_SOURCE_REGISTRY_KEY, config_path=self._registry_config_path)
        selected = self._selected_sources()
        requested_symbols = tuple(sorted({s.symbol for s in selected}))
        assert_symbols_registered(record, requested_symbols)

        source_root = self._source_root_override or record.location
        if not source_root.is_dir():
            raise FileNotFoundError(
                f"Registered raw store not found at {source_root} "
                f"(registry entry {_SOURCE_REGISTRY_KEY!r})."
            )

        out: list[Path] = []
        missing: list[str] = []
        for src_spec in selected:
            src = source_root / src_spec.filename
            if not src.is_file():
                missing.append(
                    f"{src_spec.filename} (symbol={src_spec.symbol}, "
                    f"coverage={src_spec.coverage})"
                )
                continue
            out.append(src)
            _log.info(
                "Located: %s (symbol=%s coverage=%s)",
                src.name,
                src_spec.symbol,
                src_spec.coverage,
            )

        # Fail-closed on gaps (round-1 audit CODE-1-5): a partial
        # canonical list silently materializes a substrate with holes.
        # The 1.0 log-and-skip behavior is available only via the
        # explicit allow_missing_sources opt-in, which is recorded in
        # provenance.
        self._last_missing_sources = list(missing)
        if missing:
            if not self._allow_missing_sources:
                raise FileNotFoundError(
                    f"{len(missing)} canonical source file(s) missing from "
                    f"{source_root}: {missing}. Refusing a partial "
                    f"materialization; pass --allow-missing (recorded in "
                    f"provenance) to accept the gaps explicitly."
                )
            for m in missing:
                _log.warning("Source missing (accepted via allow_missing_sources): %s", m)

        _log.info(
            "Fetch summary: %d located, %d missing of %d selected canonical "
            "sources (symbols=%s)",
            len(out),
            len(missing),
            len(selected),
            requested_symbols,
        )
        return out

    # ------------------------------------------------------------------
    # parse: CSV -> LazyFrame (normalized schema, concatenated)
    # ------------------------------------------------------------------

    def parse(self, raw_paths: list[Path], ctx: RunContext) -> pl.LazyFrame:
        """Read all raw CSVs and concatenate into one validated LazyFrame.

        Enforces UTC tz on ``ts_event`` and Float64/Int64 dtypes per
        ``VendorLegacy1minSchema``. Empty input yields an empty
        schema-conformant frame (contract-preserving). Verbatim from 1.0.
        """
        del ctx  # unused
        if not raw_paths:
            return _empty_frame().lazy()

        frames: list[pl.LazyFrame] = []
        for rp in raw_paths:
            lf = pl.scan_csv(rp, try_parse_dates=False).with_columns(
                # Databento emits ISO-8601 with "+00:00"; parse
                # explicitly rather than letting try_parse_dates
                # coerce to naive.
                pl.col("ts_event").str.to_datetime(time_unit="us", time_zone="UTC"),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
                pl.col("volume").cast(pl.Int64),
                pl.col("rtype").cast(pl.Int64),
                pl.col("publisher_id").cast(pl.Int64),
                pl.col("instrument_id").cast(pl.Int64),
                # Preserve the raw contract code (e.g., ESH0) and
                # derive the root symbol. CME mini roots are 2 char
                # (ES, NQ) but micros are 3 char (MES, MNQ, MCL, MGC,
                # SIL); a naive first-2 slice corrupts MES -> 'ME' and
                # MCL -> 'MC'. Explicit prefix mapping with 3-char
                # branches FIRST so the 2-char branches don't shadow.
                pl.col("symbol").cast(pl.Utf8).alias("contract_symbol"),
                pl.when(pl.col("symbol").cast(pl.Utf8).str.starts_with("MES"))
                .then(pl.lit("MES"))
                .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("MNQ"))
                .then(pl.lit("MNQ"))
                .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("MCL"))
                .then(pl.lit("MCL"))
                .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("MGC"))
                .then(pl.lit("MGC"))
                .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("SIL"))
                .then(pl.lit("SIL"))
                .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("ES"))
                .then(pl.lit("ES"))
                .when(pl.col("symbol").cast(pl.Utf8).str.starts_with("NQ"))
                .then(pl.lit("NQ"))
                .otherwise(pl.col("symbol").cast(pl.Utf8))
                .alias("symbol"),
            )
            frames.append(lf)

        # Concatenation across CSVs can interleave contract_symbols
        # non-monotonically. Sort here so the downstream validate()
        # monotonicity check holds by construction, not by input-file
        # ordering luck. Verbatim from 1.0.
        return pl.concat(frames, how="vertical").sort(["contract_symbol", "ts_event"])

    # ------------------------------------------------------------------
    # validate: schema + OHLC consistency (verbatim from 1.0)
    # ------------------------------------------------------------------

    def validate(self, df: pl.LazyFrame) -> None:
        """Validate against VendorLegacy1minSchema + OHLC + monotonicity."""
        collected = df.collect()
        VendorLegacy1minSchema.validate(collected)

        # OHLC consistency: catches high < open/close/low and
        # low > open/close/high.
        violations = collected.filter(
            (pl.col("low") > pl.col("open"))
            | (pl.col("low") > pl.col("close"))
            | (pl.col("low") > pl.col("high"))
            | (pl.col("high") < pl.col("open"))
            | (pl.col("high") < pl.col("close"))
        )
        if violations.height > 0:
            raise ValueError(
                f"OHLC consistency violated on {violations.height} rows; "
                f"first: {violations.head(1).to_dicts()}"
            )

        # Monotonicity within each contract_symbol: ts_event must be
        # non-decreasing. Required for look-ahead-free feature
        # computation downstream (rules/quant-project.md §Time-series
        # integrity). Schema declares unique (contract_symbol, ts_event)
        # which forbids equal timestamps, so non-decreasing ≡ strictly
        # increasing here.
        sort_check = collected.sort(["contract_symbol", "ts_event"])
        if not collected.equals(sort_check):
            raise ValueError(
                "ts_event is not monotonically increasing within each "
                "contract_symbol group; sort upstream before validation."
            )

        _log.info(
            "Schema + OHLC + monotonicity validation passed (rows=%d, symbols=%s)",
            collected.height,
            sorted(collected["symbol"].unique().to_list()),
        )

    # ------------------------------------------------------------------
    # write_processed: partitioned parquet under symbol/year (verbatim)
    # ------------------------------------------------------------------

    def write_processed(self, df: pl.LazyFrame, ctx: RunContext) -> Path:
        """Write partitioned parquet: ``symbol={SYM}/year={YYYY}/part-0000.parquet``.

        Two-phase commit: write to ``_staging``, validate each file,
        then rename to final location. Verbatim from 1.0.
        """
        paths = ctx.paths
        base_dir = paths.data_processed / _DATASET_NAME
        staging_dir = paths.data_processed / "_staging" / _DATASET_NAME
        paths.ensure(staging_dir)

        collected = df.collect().with_columns(
            pl.col("ts_event").dt.year().alias("_year"),
        )

        staged: list[tuple[Path, Path]] = []
        for (symbol, year), part_df in collected.group_by(["symbol", "_year"]):
            part_out = part_df.drop("_year")
            part_dir_final = base_dir / f"symbol={symbol}" / f"year={year}"
            part_dir_stage = staging_dir / f"symbol={symbol}" / f"year={year}"
            part_dir_stage.mkdir(parents=True, exist_ok=True)
            staging_path = part_dir_stage / "part-0000.parquet"
            final_path = part_dir_final / "part-0000.parquet"
            part_out.write_parquet(staging_path)
            staged.append((staging_path, final_path))

        # Re-validate each staged file against the schema.
        for sp, _fp in staged:
            try:
                VendorLegacy1minSchema.validate(pl.read_parquet(sp))
            except Exception:
                for bad_sp, _bad_fp in staged:
                    bad_sp.unlink(missing_ok=True)
                _rmtree_empty(staging_dir)
                raise

        # Promote.
        for sp, fp in staged:
            fp.parent.mkdir(parents=True, exist_ok=True)
            sp.replace(fp)
        _rmtree_empty(staging_dir)

        _log.info("Wrote %d partitions to %s", len(staged), base_dir)
        return base_dir

    # ------------------------------------------------------------------
    # emit_provenance
    # ------------------------------------------------------------------

    def emit_provenance(
        self,
        ctx: RunContext,
        source_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Write provenance JSON with per-source SHA256 + repro-log attach."""
        prov_dir = ctx.paths.data_processed / "_provenance"
        ctx.paths.ensure(prov_dir)

        # Populate RunContext.dataset_checksums so the ReproLog carries
        # the canonical hashes (1.0 F-1-6 remediation preserved).
        # portable_key: committed ReproLogs must not embed the OS
        # username (identity hygiene, audit L).
        if hasattr(ctx, "add_dataset_checksum"):
            for sp in source_paths:
                ctx.add_dataset_checksum(portable_key(sp, ctx.paths.root), file_sha256(sp))

        timestamp = datetime.now(tz=UTC).isoformat()
        payload = {
            "dataset": self.name,
            "version": self.version,
            "vendor": "Databento GLBX.MDP3 ohlcv-1m (machine-level store, ADR-0011)",
            "source_registry_key": _SOURCE_REGISTRY_KEY,
            "license_status": "verified",
            "tier": "raw",
            # evidence_bar_eligible intentionally False at raw tier: the
            # raw 1-min series concatenates successive front-month
            # contracts without roll adjustment, so returns computed on
            # this series cross uncompensated roll boundaries — the
            # futures analog of the "adjust for corporate actions before
            # return calc" requirement in rules/quant-project.md
            # §Time-series integrity. The downstream roll-adjusted
            # derivative is the proper evidence-bar input.
            "evidence_bar_eligible": False,
            "roll_adjustment": "none (front-month concatenation only)",
            # Fail-closed fetch record (round-1 audit CODE-1-5): gaps in
            # the canonical list are either a hard error or an explicit,
            # provenance-recorded acceptance.
            "allow_missing_sources": self._allow_missing_sources,
            "missing_sources": list(self._last_missing_sources),
            # Known substrate defect registered on the upstream entry in
            # config/data_sources.yaml (substrate_defects): per-year
            # files carry only same-year-expiry contracts, so December
            # Z->H front-month crossovers are invisible until January
            # (QUANT-1-1; repair follow-up
            # P1-2.0-DATABENTO-DEC-ROLL-REPULL, operator-gated).
            "substrate_defects_reference": (
                "config/data_sources.yaml: " "vendor_skie_ninja_legacy_raw_1min.substrate_defects"
            ),
            "timestamp_utc": timestamp,
            # Keys use portable_key (repo-/~-relative POSIX) to match
            # the CLI's _source_unchanged idempotency contract without
            # embedding the OS username in a committed file.
            "source_checksums": {
                portable_key(sp, ctx.paths.root): file_sha256(sp) for sp in source_paths
            },
            "output_path": portable_key(output_path, ctx.paths.root),
            "run_id": ctx.log.run_id if ctx.log else None,
            "repro_log": ctx.log.to_dict() if ctx.log else None,
        }

        date_str = datetime.now(tz=UTC).strftime("%Y%m%d")
        prov_path = prov_dir / f"{self.name}_{date_str}.json"
        prov_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        _log.info("Wrote provenance: %s", prov_path)
        return prov_path


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _empty_frame() -> pl.DataFrame:
    """Empty schema-conformant frame for the no-input path."""
    return pl.DataFrame(
        schema={
            "ts_event": pl.Datetime("us", "UTC"),
            "rtype": pl.Int64,
            "publisher_id": pl.Int64,
            "instrument_id": pl.Int64,
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "volume": pl.Int64,
            "contract_symbol": pl.Utf8,
            "symbol": pl.Utf8,
        }
    )


def _rmtree_empty(path: Path) -> None:
    """Remove a directory tree if all leaves are empty."""
    if not path.is_dir():
        return
    for child in path.iterdir():
        if child.is_dir():
            _rmtree_empty(child)
    with contextlib.suppress(OSError):
        path.rmdir()


# Self-register at import time.
register(VendorLegacy1minIngestJob())
