"""Data ingest CLI entry point.

Ported from SKIE-Universe 1.0 ``scripts/ingest.py`` (sibling repo) with
the dataset set reduced to the Phase C substrate and a ``--symbols``
flag so non-ES/NQ symbols are a later rerun (Phase C materializes ES
and NQ only — the Phase A dwell-time study substrate).

Usage:
    uv run python scripts/ingest.py --dataset vendor_legacy_1min \\
        --start 2015-01-01 --end 2025-12-31 --symbols ES NQ
    uv run python scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted \\
        --start 2015-01-01 --end 2025-12-31 --symbols ES NQ

Idempotent: re-run overwrites only if source SHA256 changed (unless
--force). ``--dry-run`` enumerates without side effects.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import UTC, date, datetime
from pathlib import Path

# Script-bootstrap sys.path shim so the script works before any editable
# install (this repo is uv `package = false`).
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent / "src"))

import polars as pl  # noqa: E402

from skie_universe2.data.ingest import INGEST_REGISTRY  # noqa: E402
from skie_universe2.data.ingest.vendor_legacy_1min import (  # noqa: E402
    VendorLegacy1minIngestJob,
)
from skie_universe2.data.ingest.vendor_legacy_1min_roll_adjusted import (  # noqa: E402
    VendorLegacy1minRollAdjustedIngestJob,
)
from skie_universe2.data.validation.schema import (  # noqa: E402
    VendorLegacy1minRollAdjustedSchema,
    VendorLegacy1minSchema,
)
from skie_universe2.utils.hashing import file_sha256  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths, portable_key  # noqa: E402
from skie_universe2.utils.runcontext import RunContext  # noqa: E402

_log = logging.getLogger(__name__)

_DATASET_CHOICES = (
    "vendor_legacy_1min",
    "vendor_legacy_1min_roll_adjusted",
)

_SCHEMA_MAP: dict[str, type] = {
    "vendor_legacy_1min": VendorLegacy1minSchema,
    "vendor_legacy_1min_roll_adjusted": VendorLegacy1minRollAdjustedSchema,
}

# Phase C scope: ES + NQ only (ADR-0004 dwell-time study substrate);
# other registered symbols are a later rerun via --symbols.
_DEFAULT_SYMBOLS = ("ES", "NQ")


def _parse_date(value: str) -> date:
    """Parse an ISO-8601 date string (YYYY-MM-DD)."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"Invalid date {value!r}; expected YYYY-MM-DD.") from exc


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ingest.py",
        description="Fetch, parse, validate, and write processed ingest datasets.",
    )
    p.add_argument("--dataset", required=True, choices=_DATASET_CHOICES, help="Dataset to ingest.")
    p.add_argument(
        "--start", required=True, type=_parse_date, help="Start date (YYYY-MM-DD), inclusive."
    )
    p.add_argument(
        "--end", required=True, type=_parse_date, help="End date (YYYY-MM-DD), inclusive."
    )
    p.add_argument(
        "--symbols",
        nargs="+",
        default=list(_DEFAULT_SYMBOLS),
        help=(
            "Root symbols to materialize (default: ES NQ — the Phase C "
            "scope). Symbols must be registered for the source in "
            "config/data_sources.yaml (ADR-0011 Decision 3)."
        ),
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Enumerate what would be fetched/written without side effects.",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="Overwrite processed output even if source SHA256 is unchanged.",
    )
    p.add_argument(
        "--seed",
        type=int,
        default=42,
        help=(
            "RNG seed for RunContext (default: 42, the 1.0 CLI default; "
            "the ingest path is deterministic — no RNG is consumed — the "
            "seed is recorded in the ReproLog for contract completeness)."
        ),
    )
    p.add_argument(
        "--allow-missing",
        action="store_true",
        help=(
            "Accept gaps in the canonical source list (vendor_legacy_1min "
            "only). Fetch is fail-closed by default — any missing canonical "
            "CSV aborts the run; this opt-in downgrades to WARNING and "
            "records the accepted gaps in provenance (audit CODE-1-5)."
        ),
    )
    return p


def _make_job(dataset: str, symbols: tuple[str, ...], allow_missing: bool):
    """Instantiate the requested job with the symbol scope applied."""
    if dataset == "vendor_legacy_1min":
        return VendorLegacy1minIngestJob(symbols=symbols, allow_missing_sources=allow_missing)
    if dataset == "vendor_legacy_1min_roll_adjusted":
        return VendorLegacy1minRollAdjustedIngestJob(symbols=symbols)
    raise ValueError(f"Unknown dataset {dataset!r}")


def _resolved_config_sha256(dataset: str, paths: ProjectPaths) -> str:
    """SHA-256 of the config file that parameterizes this dataset's run.

    Recorded into the ReproLog's ``config_resolved_sha256`` (audit A /
    REPRODUCIBILITY-1-4: previously null). The roll-adjusted derivation
    is parameterized by config/instruments.yaml (roll_rule per symbol);
    the raw-stage job by config/data_sources.yaml (source registry).
    Strict: the file must exist — a run without its config is refused.
    """
    config_file = (
        paths.config / "instruments.yaml"
        if dataset == "vendor_legacy_1min_roll_adjusted"
        else paths.config / "data_sources.yaml"
    )
    if not config_file.is_file():
        raise FileNotFoundError(
            f"Resolved config for dataset {dataset!r} not found at {config_file}; "
            f"refusing to run without it (fail-closed, audit finding A)."
        )
    return file_sha256(config_file)


def _source_unchanged(dataset: str, raw_paths: list[Path], paths: ProjectPaths) -> bool:
    """Return True if raw-file checksums match the existing provenance record.

    Keys use ``portable_key`` (repo-/~-relative POSIX), matching the
    emit_provenance key scheme.
    """
    raw_checksums: dict[str, str] = {}
    for rp in raw_paths:
        if rp.is_file():
            raw_checksums[portable_key(rp, paths.root)] = file_sha256(rp)

    today_str = datetime.now(tz=UTC).strftime("%Y%m%d")  # UTC to match provenance filename
    prov_path = paths.data_processed / "_provenance" / f"{dataset}_{today_str}.json"
    if not prov_path.is_file():
        return False
    try:
        existing_prov = json.loads(prov_path.read_text(encoding="utf-8"))
        return raw_checksums == existing_prov.get("source_checksums", {})
    except (json.JSONDecodeError, KeyError):
        _log.debug("Could not read existing provenance at %s; proceeding.", prov_path)
        return False


def _post_write_validate(dataset: str, output_path: Path) -> None:
    """Read back processed parquet and run schema validation.

    Raises on failure. (The 1.0 distribution-drift comparison is not
    ported: it compared new vs prior parquet snapshots inside one
    output tree, and on a fresh 2.0 materialization there is no prior
    snapshot by construction; the cross-repo drift check is the
    benchmark comparison in docs/audits/.)
    """
    schema_cls = _SCHEMA_MAP.get(dataset)
    if schema_cls is None or not output_path.is_dir():
        return

    parquet_files = list(output_path.rglob("*.parquet"))
    if not parquet_files:
        return

    readback = pl.concat([pl.read_parquet(pf) for pf in parquet_files])
    schema_cls.validate(readback)
    _log.info("Post-write schema validation passed (%d files).", len(parquet_files))


def run(argv: list[str] | None = None) -> int:  # noqa: PLR0911 — one return per pipeline stage failure mode, mirroring the 1.0 CLI exit-code contract
    """CLI entry point. Returns POSIX exit code."""
    args = _build_parser().parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    dataset: str = args.dataset
    start: date = args.start
    end: date = args.end
    dry_run: bool = args.dry_run
    force: bool = args.force
    seed: int = args.seed
    symbols: tuple[str, ...] = tuple(args.symbols)
    allow_missing: bool = args.allow_missing

    if start > end:
        _log.error("--start (%s) is after --end (%s).", start, end)
        return 1

    if allow_missing and dataset != "vendor_legacy_1min":
        _log.error("--allow-missing is only valid for --dataset vendor_legacy_1min.")
        return 1

    if dataset not in INGEST_REGISTRY:
        _log.error(
            "Dataset %r not found in INGEST_REGISTRY. Available: %s",
            dataset,
            ", ".join(sorted(INGEST_REGISTRY)) or "(none)",
        )
        return 1

    job = _make_job(dataset, symbols, allow_missing)
    paths = ProjectPaths.discover(_SCRIPT_DIR)

    with RunContext(
        phase="ingest",
        hypothesis_id=f"ingest_{dataset}",
        rng_seed=seed,
        config_resolved_sha256=_resolved_config_sha256(dataset, paths),
        paths=paths,
    ) as ctx:
        _log.info(
            "Ingest started: dataset=%s, start=%s, end=%s, symbols=%s, "
            "dry_run=%s, force=%s, allow_missing=%s",
            dataset,
            start,
            end,
            symbols,
            dry_run,
            force,
            allow_missing,
        )

        # Step 1: fetch (registry-gated per ADR-0011 Decision 3).
        raw_paths = job.fetch(start, end, ctx)
        _log.info("Fetch returned %d path(s).", len(raw_paths))

        if dry_run:
            _log.info("[dry-run] Would process %d file(s):", len(raw_paths))
            for p in raw_paths:
                _log.info("[dry-run]   %s", p)
            _log.info("[dry-run] Stopping before parse.")
            return 0

        # Idempotency: SHA256 change detection.
        if not force and _source_unchanged(dataset, raw_paths, paths):
            _log.info(
                "Skipping %s: source checksums unchanged. Use --force to override.",
                dataset,
            )
            return 0

        # Step 2: parse
        _log.info("Parsing %d raw file(s).", len(raw_paths))
        lf = job.parse(raw_paths, ctx)

        # Step 3: validate
        _log.info("Validating parsed data.")
        try:
            job.validate(lf)
        except Exception as exc:
            _log.error("Validation failed: %s", exc)
            return 2

        # Step 4: write processed
        _log.info("Writing processed output.")
        output_path = job.write_processed(lf, ctx)
        _log.info("Processed data written to %s.", output_path)

        # Step 4b: post-write validation.
        _log.info("Running post-write validation on processed output.")
        try:
            _post_write_validate(dataset, output_path)
        except Exception as exc:
            _log.error("Post-write validation failed: %s", exc)
            return 3

        # Step 5: emit provenance
        _log.info("Emitting provenance record.")
        prov_path = job.emit_provenance(ctx, raw_paths, output_path)
        _log.info("Provenance written to %s.", prov_path)

    _log.info("Ingest complete: %s.", dataset)
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
