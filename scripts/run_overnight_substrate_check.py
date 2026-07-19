"""Overnight/Globex substrate feasibility check (roadmap Phase 3, step P3-A).

Answers the two pre-registration feasibility questions for the overnight/Globex
forward expert (program_roadmap_2026-07-17.md Phase 3 first bullet; backfill
plan §3 forward-experts item; od_g setup plan §7 "Overnight/Globex substrate
check"):

(1) **ETH-bars check** — does the roll-adjusted evidence-bar store
    (``data/processed/vendor_legacy_1min_roll_adjusted``) carry the full CME
    Globex (ETH) session, or was it RTH-filtered at build time? Characterizes
    per-session coverage by segment on both the 1-minute substrate and the
    5-minute evidence grid (the H900 §3 aggregation rule reused verbatim from
    ``run_shadow_ledger_backfill.py``).
(2) **December/Globex blind-spot quantification** — from the provenance
    ``coverage_gaps`` register (defect ``DEC_ROLL_LATE_COMMIT``), the
    session-dates removed by the registered primary-analysis exclusions, by
    calendar year and gap kind, with bar counts. This is the input for the
    declared-blind-spot section of the overnight design.md (rule of record,
    2026-07-19: a conditional-grade overnight screen runs on the
    exclusion-filtered substrate with the blind spot declared; DR-1/DR-2 is
    prerequisite only for December-inclusive / confirmation-grade evidence —
    databento_pull_spec_cost_sheet_2026-07-18.md §2.1.4 / §5(c)).

Session segment definitions (exchange constants, not tunables):

- CME session date: ``skie_universe2.utils.sessions.cme_session_date_expr``
  (session D = 17:00 CT day D-1 → 16:00 CT day D; the shared ingest rule).
- RTH = local ``[09:30, 16:00)`` America/New_York (CME equity-index regular
  session; same constants as ``experts/orb_first_hour.py``).
- Overnight ETH = session bars with local time ≥ 18:00 (prior calendar day)
  or < 09:30 — the candidate competence window, bar-disjoint from RTH by
  construction.
- Post-RTH ETH = local ``[16:00, 17:00)`` tail; ``[17:00, 18:00)`` is the
  daily maintenance halt (bars here indicate schedule-variant sessions).

Read-only over the substrate. Writes ``reports/P3A_overnight_substrate/
overnight_substrate_check.json`` plus a ReproLog. No ledger partition is
written, no trial register incremented, no OOS span consumed (no signal is
evaluated — coverage characterization only).

Usage:
    uv run python scripts/run_overnight_substrate_check.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import polars as pl

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.features.regime_emissions import (  # noqa: E402
    apply_registered_exclusions,
    exclusion_windows_from_provenance,
)
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402
from skie_universe2.utils.sessions import (  # noqa: E402
    NY_TZ,
    SEGMENT_HALT_ANOMALY,
    SEGMENT_OVERNIGHT_ETH,
    SEGMENT_POST_RTH_ETH,
    SEGMENT_RTH,
    cme_session_date_expr,
    session_segment_expr,
)

# justify: registered project seed (H900/H001 lineage); no stochastic component here
SEED = 20260716
DATASET = "vendor_legacy_1min_roll_adjusted"
PROVENANCE_FILE = "vendor_legacy_1min_roll_adjusted_20260711.json"
INSTRUMENTS = ("ES", "NQ")  # justify: the registered §2 universe (H101/H103 precedent)
_SEGMENTS = (SEGMENT_OVERNIGHT_ETH, SEGMENT_RTH, SEGMENT_POST_RTH_ETH, SEGMENT_HALT_ANOMALY)


def _scan_symbol(paths: ProjectPaths, symbol: str) -> pl.LazyFrame:
    glob = str(paths.data_processed / DATASET / f"symbol={symbol}" / "**" / "*.parquet")
    return pl.scan_parquet(glob).select("ts_event", "volume", "pit_provisional")


def _provenance(paths: ProjectPaths) -> dict:
    return json.loads(
        (paths.data_processed / "_provenance" / PROVENANCE_FILE).read_text(encoding="utf-8")
    )


def _aggregate_5m(lf: pl.LazyFrame) -> pl.DataFrame:
    """The H900 §3 / backfill-driver 5-minute aggregation rule (timestamps only)."""
    return (
        lf.sort("ts_event")
        .group_by_dynamic("ts_event", every="5m", closed="left", label="left")
        .agg(volume=pl.col("volume").sum())
        .collect()
    )


def _per_session_segment_stats(frame: pl.DataFrame) -> dict:
    """Per-CME-session bar counts by segment → distributional summary."""
    per = (
        frame.lazy()
        .with_columns(
            cme_session_date_expr("ts_event").alias("session_date"),
            session_segment_expr("ts_event"),
        )
        .group_by("session_date", "segment")
        .agg(pl.len().alias("n_bars"))
        .collect()
        .pivot(values="n_bars", index="session_date", on="segment")
        .fill_null(0)
        .sort("session_date")
    )
    out: dict = {"n_sessions": per.height}
    for seg in _SEGMENTS:
        if seg not in per.columns:
            out[seg] = {"present": False}
            continue
        col = per.get_column(seg)
        out[seg] = {
            "present": True,
            "total_bars": int(col.sum()),
            "sessions_with_any": int((col > 0).sum()),
            "per_session_median": float(col.median()),
            # justify: 0.05/0.95 = conventional 90% central-coverage summary
            # quantiles (reporting-only descriptives, not decision thresholds)
            "per_session_p05": float(col.quantile(0.05)),
            "per_session_p95": float(col.quantile(0.95)),
            "per_session_min": int(col.min()),
            "per_session_max": int(col.max()),
        }
    return out


def _hour_histogram(frame: pl.DataFrame) -> dict[str, int]:
    hh = (
        frame.lazy()
        .with_columns(pl.col("ts_event").dt.convert_time_zone(NY_TZ).dt.hour().alias("h"))
        .group_by("h")
        .agg(pl.len().alias("n"))
        .collect()
        .sort("h")
    )
    return {
        str(int(h)): int(n) for h, n in zip(hh.get_column("h"), hh.get_column("n"), strict=True)
    }


def _blind_spot(paths: ProjectPaths, symbol: str, gaps: list[dict]) -> dict:
    """What the registered exclusions remove, by year and gap kind, in sessions and bars."""
    lf = _scan_symbol(paths, symbol)
    base = (
        lf.with_columns(
            cme_session_date_expr("ts_event").alias("session_date"),
            session_segment_expr("ts_event"),
        )
        .group_by("session_date", "segment")
        .agg(pl.len().alias("n_bars"), pl.col("pit_provisional").sum().alias("n_pit"))
        .collect()
    )
    mine = [g for g in gaps if g["symbol"] == symbol]
    windows = list(zip(mine, exclusion_windows_from_provenance(mine), strict=True))
    per_year: dict[str, dict] = {}
    totals = {"sessions": 0, "bars_total": 0, "bars_overnight_eth": 0}
    for gap, w in windows:
        hit = base.filter(pl.col("session_date").is_between(pl.lit(w.start), pl.lit(w.end)))
        sess = hit.get_column("session_date").unique()
        n_sessions = sess.len()
        n_bars = int(hit.get_column("n_bars").sum())
        n_on = int(
            hit.filter(pl.col("segment") == SEGMENT_OVERNIGHT_ETH).get_column("n_bars").sum()
        )
        year = str(w.start.year)
        rec = per_year.setdefault(year, {"late_committed_roll": None, "terminal_window": None})
        rec[gap["kind"]] = {
            "window": gap["expected_crossover_window"],
            "sessions_excluded": int(n_sessions),
            "bars_1min_excluded": n_bars,
            "overnight_eth_bars_1min_excluded": n_on,
            "first_session": str(sess.min()) if n_sessions else None,
            "last_session": str(sess.max()) if n_sessions else None,
        }
        totals["sessions"] += int(n_sessions)
        totals["bars_total"] += n_bars
        totals["bars_overnight_eth"] += n_on
    n_sessions_store = base.get_column("session_date").n_unique()
    return {
        "per_year": dict(sorted(per_year.items())),
        "totals": {
            **totals,
            "sessions_in_store": int(n_sessions_store),
            "excluded_session_share": totals["sessions"] / n_sessions_store,
        },
    }


def _characterize(paths: ProjectPaths, symbol: str, gaps: list[dict]) -> dict:
    lf = _scan_symbol(paths, symbol)
    pre = lf.collect()
    excl = apply_registered_exclusions(
        pre.lazy(),
        symbol=symbol,
        exclusions=exclusion_windows_from_provenance(gaps),
        exclude_pit_provisional=True,
        exclude_coverage_gaps=True,
    ).collect()
    pre_1m, post_1m = pre.height, excl.height
    post_5m = _aggregate_5m(excl.lazy())
    span = excl.get_column("ts_event")
    return {
        "rows_1min_pre_exclusion": pre_1m,
        "rows_1min_post_exclusion": post_1m,
        "rows_pit_provisional": int(pre.get_column("pit_provisional").sum()),
        "span_post_exclusion_utc": [str(span.min()), str(span.max())],
        "hour_histogram_local_post_exclusion": _hour_histogram(excl),
        "per_session_1min": _per_session_segment_stats(excl),
        "per_session_5min": _per_session_segment_stats(post_5m),
        "december_globex_blind_spot": _blind_spot(paths, symbol, gaps),
    }


def main() -> int:
    paths = ProjectPaths.discover()
    prov = _provenance(paths)
    gaps = prov["coverage_gaps"]

    log = reproducibility.capture(
        phase="p3a-overnight-substrate-check",
        hypothesis_id="n/a",  # pre-HID feasibility gate; no hypothesis object exists yet
        rng_seed=SEED,
        dataset_checksums={DATASET: prov["output_frame_sha256"]},
        config_resolved_sha256=None,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name}", flush=True)

    result: dict = {
        "run_id": log.run_id,
        "repro_log": log_path.name,
        "dataset": DATASET,
        "provenance_file": PROVENANCE_FILE,
        "exclusion_variant": "primary (pit_provisional + coverage_gaps excluded)",
        "segment_definitions": {
            "source": "skie_universe2.utils.sessions.session_segment_expr (single source of truth)",
            "rth": "[09:30, 16:00) America/New_York",
            "post_rth_eth": "[16:00, 17:00) America/New_York",
            "halt_anomaly": "[17:00, 18:00) America/New_York (daily maintenance halt)",
            "overnight_eth": ">= 18:00 or < 09:30 America/New_York",
            "session_date": "CME rule via utils.sessions.cme_session_date_expr",
        },
        "instruments": {},
    }
    for symbol in INSTRUMENTS:
        print(f"[{symbol}] characterizing...", flush=True)
        result["instruments"][symbol] = _characterize(paths, symbol, gaps)

    out_dir = paths.root / "reports" / "P3A_overnight_substrate"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "overnight_substrate_check.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}", flush=True)

    for symbol in INSTRUMENTS:
        r = result["instruments"][symbol]
        on5 = r["per_session_5min"]["overnight_eth"]
        print(
            f"[{symbol}] ETH present: {on5['present']}; "
            f"5-min overnight bars/session median {on5.get('per_session_median')}; "
            f"sessions {r['per_session_5min']['n_sessions']}; "
            f"excluded sessions {r['december_globex_blind_spot']['totals']['sessions']} "
            f"({r['december_globex_blind_spot']['totals']['excluded_session_share']:.2%})",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
