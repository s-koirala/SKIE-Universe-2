"""Phase C numerical cross-validation: 2.0 ported ingest vs 1.0 reference.

Committed evidence script for
docs/audits/benchmark_comparison_phaseC_ingest_2026-07-10.md (round-1
audit REPRODUCIBILITY-1-1/QUANT-1-9: the comparison must be re-runnable
from the repo, not a scratchpad artifact).

Compares this repo's ``data/processed/vendor_legacy_1min_roll_adjusted``
against the reference output registered as
``skie_universe_1_processed_roll_adjusted`` in config/data_sources.yaml
(reference-only entry per ADR-0011 Decision 2 — resolved here read-only,
never through the ingest path).

Comparison is restricted to the SHARED column set: the 2.0 output adds
metadata columns absent from the 1.0 reference (currently
``pit_provisional``, round-1 audit QUANT-1-2); 2.0-only columns are
reported but never compared. Exactness is required on every shared
column (the methodology is deterministic; see the benchmark doc), and
is gated on ZERO nulls (all shared columns) and ZERO NaNs (shared
float columns) on BOTH sides — null-skipping arithmetic can otherwise
mask discrepancies (round-2 audit REPRODUCIBILITY-2-2).

Usage:
    uv run python scripts/audits/compare_benchmark_phaseC.py [--symbols ES NQ]

Exit code 0 iff every symbol is bit-exact on the shared columns over the
full overlapping ts_event range; 1 otherwise (the JSON report is printed
either way).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Script-bootstrap sys.path shim (repo is uv `package = false`).
_SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_SCRIPT_DIR.parent.parent / "src"))

import polars as pl  # noqa: E402
import yaml  # noqa: E402

from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

_BENCHMARK_REGISTRY_KEY = "skie_universe_1_processed_roll_adjusted"
_DATASET = "vendor_legacy_1min_roll_adjusted"

# Columns whose values must agree exactly (floats compared by abs dev;
# exact zero required). Utf8/bool columns compared by mismatch count.
_FLOAT_COLS = ("open", "high", "low", "close", "adjustment_factor", "unadjusted_close")
_INT_COLS = ("volume",)
_LABEL_COLS = ("front_contract_symbol", "roll_flag")


def _benchmark_root(paths: ProjectPaths) -> Path:
    registry = yaml.safe_load((paths.config / "data_sources.yaml").read_text(encoding="utf-8"))
    entry = registry["sources"].get(_BENCHMARK_REGISTRY_KEY)
    if entry is None:
        raise SystemExit(
            f"Benchmark entry {_BENCHMARK_REGISTRY_KEY!r} not registered in "
            f"config/data_sources.yaml."
        )
    if entry.get("kind") != "sibling_repo_reference" or entry.get("usable_as_evidence"):
        raise SystemExit(
            f"Benchmark entry {_BENCHMARK_REGISTRY_KEY!r} must be a "
            f"reference-only sibling_repo_reference (ADR-0011 Decision 2)."
        )
    return Path(str(entry["location"])).expanduser()


def _compare_symbol(new_root: Path, ref_root: Path, sym: str) -> dict:
    new = pl.read_parquet(new_root / f"symbol={sym}" / "**" / "*.parquet").sort("ts_event")
    ref = pl.read_parquet(ref_root / f"symbol={sym}" / "**" / "*.parquet").sort("ts_event")

    shared = [c for c in new.columns if c in set(ref.columns)]
    rec: dict = {
        "new_rows": new.height,
        "ref_rows": ref.height,
        "shared_columns": shared,
        "new_only_columns": [c for c in new.columns if c not in set(ref.columns)],
        "ref_only_columns": [c for c in ref.columns if c not in set(new.columns)],
        "shared_dtypes_equal": all(str(new.schema[c]) == str(ref.schema[c]) for c in shared),
        "new_span": [str(new["ts_event"].min()), str(new["ts_event"].max())],
        "ref_span": [str(ref["ts_event"].min()), str(ref["ts_event"].max())],
    }

    lo = max(new["ts_event"].min(), ref["ts_event"].min())
    hi = min(new["ts_event"].max(), ref["ts_event"].max())
    n_o = new.filter(pl.col("ts_event").is_between(lo, hi)).select(shared)
    r_o = ref.filter(pl.col("ts_event").is_between(lo, hi)).select(shared)
    rec["overlap_span"] = [str(lo), str(hi)]
    rec["overlap_rows_new"] = n_o.height
    rec["overlap_rows_ref"] = r_o.height

    joined = n_o.join(r_o, on="ts_event", how="inner", suffix="_ref")
    rec["overlap_joined_rows"] = joined.height
    rec["ts_only_in_new"] = n_o.height - joined.height
    rec["ts_only_in_ref"] = r_o.height - joined.height

    # Null/NaN integrity gate (round-2 audit REPRODUCIBILITY-2-2): the
    # deviation arithmetic below is null-skipping ((a-b) propagates
    # null, .sum() ignores it) and naive != comparisons propagate
    # nulls, so null-vs-value or NaN differences would count as
    # agreement. Require ZERO nulls on every shared column of BOTH
    # frames and ZERO NaNs on every shared float column before any
    # value comparison; violations are reported per column per side and
    # fail exactness outright.
    null_counts = {
        side: {c: int(frame[c].null_count()) for c in shared}
        for side, frame in (("new", n_o), ("ref", r_o))
    }
    nan_counts = {
        side: {c: int(frame[c].is_nan().sum()) for c in _FLOAT_COLS if c in shared}
        for side, frame in (("new", n_o), ("ref", r_o))
    }
    rec["null_counts_nonzero"] = {
        side: {c: n for c, n in cols.items() if n > 0} for side, cols in null_counts.items()
    }
    rec["nan_counts_nonzero"] = {
        side: {c: n for c, n in cols.items() if n > 0} for side, cols in nan_counts.items()
    }
    clean = all(n == 0 for cols in null_counts.values() for n in cols.values()) and all(
        n == 0 for cols in nan_counts.values() for n in cols.values()
    )

    agreement: dict = {}
    exact = (
        rec["shared_dtypes_equal"]
        and joined.height == n_o.height == r_o.height
        and joined.height > 0
        and clean
    )
    for c in _FLOAT_COLS:
        d = (joined[c] - joined[f"{c}_ref"]).abs()
        n_nonzero = int((d > 0).sum())
        agreement[c] = {
            "max_abs_dev": float(d.max()) if joined.height else None,
            "n_nonzero": n_nonzero,
        }
        exact = exact and n_nonzero == 0
    for c in _INT_COLS:
        d = (joined[c] - joined[f"{c}_ref"]).abs()
        n_nonzero = int((d > 0).sum())
        agreement[c] = {
            "max_abs_dev": int(d.max()) if joined.height else None,
            "n_nonzero": n_nonzero,
        }
        exact = exact and n_nonzero == 0
    for c in _LABEL_COLS:
        # eq_missing: null-safe equality (null == null is True,
        # null == value is False), so a null-vs-value discrepancy
        # counts as a mismatch instead of propagating to null and
        # being silently dropped by the sum.
        n_mismatch = int((~joined[c].eq_missing(joined[f"{c}_ref"])).sum())
        agreement[c] = {"n_mismatch": n_mismatch}
        exact = exact and n_mismatch == 0

    rec["value_agreement"] = agreement
    rec["bit_exact_on_shared_columns"] = exact
    return rec


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--symbols",
        nargs="+",
        default=["ES", "NQ"],
        help="Symbols to compare (default: ES NQ — the Phase C scope).",
    )
    args = parser.parse_args(argv)

    paths = ProjectPaths.discover(_SCRIPT_DIR)
    new_root = paths.data_processed / _DATASET
    ref_root = _benchmark_root(paths)

    report = {
        "benchmark_registry_key": _BENCHMARK_REGISTRY_KEY,
        "note": (
            "Shared-column comparison only; 2.0-only metadata columns "
            "(e.g. pit_provisional) are listed, not compared. Bit-exactness "
            "is a PORT-FIDELITY claim; both sides share the "
            "DEC_ROLL_LATE_COMMIT substrate defect (see "
            "config/data_sources.yaml substrate_defects)."
        ),
        "symbols": {sym: _compare_symbol(new_root, ref_root, sym) for sym in args.symbols},
    }
    json.dump(report, sys.stdout, indent=2)
    print()

    ok = all(rec["bit_exact_on_shared_columns"] for rec in report["symbols"].values())
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
