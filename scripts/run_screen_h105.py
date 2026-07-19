"""RC-H105-1 — ADR-0014 SCREEN of the overnight/Globex session-drift expert.

Executes the FROZEN H105 protocol
(research/01_hypothesis_register/H105/design.md §5) on the canonical k1.0
shadow ledger (`expert_id=overnight_session_drift_k1.0@1.0.0`). The
statistical spine — S-c Romano-Wolf StepM at the ENACTED runtime level,
S-d DSR/PBO with runtime-derived bounds and the matched-surface dispersion,
S-e, the §8 exhibits (KPSS, primary-cell CI + precision, Lo-2002 SE), the
disposition logic, and the ReproLog scaffold — lives in the packaged module
:mod:`skie_universe2.screening.screen_spine` (single source of truth; the
RC-*-2 harness stages, extracted per the pre-freeze audit CODE-1-1/2).

This script supplies only the H105-specific pieces (design §§3-5):

- the per-session estimand loader (overnight gross from the H105 ledger),
- the §3 conditioning covariates: ``rvol_entry`` at the overnight entry bar
  and ``prior_rth_sign`` (prior session's RTH log-return via the
  09:25/15:55 label closes; NULLED when the prior available session is more
  than the registered 4-calendar-day gap back — design §3(ii)),
- the §3 cells: unconditional (PRIMARY), high_vol/low_vol via the CERTIFIED
  leakage-clean per-origin train-window-CDF tercile construction
  (screen_spine.per_origin_percentile — never full-sample), prior_rth_up /
  prior_rth_down,
- the S-a prefix-invariance canary on the H105 expert,
- the frozen ScreenSpec (seed 20260719; N_TRIALS_GATE 30 with the matched
  dispersion families rc-h101-2 + rc-h103-2; ETH dwell 186 bars/session).

Usage:
    uv run python scripts/run_screen_h105.py [--out reports/H105]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import warnings
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.experts.base import BarWindow, assert_prefix_invariant  # noqa: E402
from skie_universe2.experts.overnight_drift import OvernightSessionDriftExpert  # noqa: E402
from skie_universe2.features.regime_emissions import (  # noqa: E402
    BAR_MINUTES,
    apply_registered_exclusions,
    compute_emissions,
    exclusion_windows_from_provenance,
)
from skie_universe2.screening import screen_spine as spine  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402
from skie_universe2.utils.sessions import (  # noqa: E402
    NY_TZ,
    RTH_CLOSE,
    RTH_OPEN,
    SEGMENT_OVERNIGHT_ETH,
    cme_session_date_expr,
    session_segment_expr,
)

# justify: design §11 registered scan seed (fresh H105 family, date-derived).
SEED_SC = 20260719
# justify: design §8 — the register's full distinct instrument x cell screen
# surface after rc-h105-1 registers (rc-h101-2 10 + rc-h103-2 10 +
# rc-h105-1 10); raw count binds, matched dispersion per screen_spine.
N_TRIALS_GATE = 30
# justify: overnight ETH segment on the 5-minute grid: 18:00-09:30 NY =
# 15.5 h x 12 = 186 bars (design §2; median 186 on both instruments per the
# P3-A substrate check — ES p05 = p95 = 186; NQ p05 = 185).
ETH_BARS_PER_SESSION = 186
_CELL_ORDER = ("unconditional", "high_vol", "low_vol", "prior_rth_up", "prior_rth_down")
_SIGMA_CELLS = ("high_vol", "low_vol", "prior_rth_up", "prior_rth_down")
_PRIMARY_CELL = "unconditional"  # justify: design §3 — the documented headline effect
LEDGER_EXPERT_ID = "overnight_session_drift_k1.0@1.0.0"
# justify: max ordinary CME weekend+single-holiday session spacing
# (Friday -> Tuesday); a longer gap marks an excluded span whose stale
# prior-RTH value is nulled (design §3(ii); pre-freeze audit QUANT-1-6).
_MAX_PRIOR_SESSION_GAP_DAYS = 4
# justify: derived — design §3 prior_rth_sign label endpoints on the
# 5-minute grid: the last pre-RTH label (09:25; its close = the RTH open)
# and the last RTH label (15:55; its close ≈ the RTH close). Both derived
# from the registered exchange constants + bar grid; sessions lacking
# either label carry undefined sign (design §3(i)).
_RTH_RET_START = datetime.combine(date.min, RTH_OPEN) - timedelta(minutes=BAR_MINUTES)
_RTH_RET_END = datetime.combine(date.min, RTH_CLOSE) - timedelta(minutes=BAR_MINUTES)
_RTH_RET_START_LABEL_H, _RTH_RET_START_LABEL_M = _RTH_RET_START.hour, _RTH_RET_START.minute
_RTH_RET_END_LABEL_H, _RTH_RET_END_LABEL_M = _RTH_RET_END.hour, _RTH_RET_END.minute
# justify: structural observation lag per RULE-BASED cell, in ETH bars: all
# §3 cells are decided at the entry bar's close (design §3 S-e; lag 0).
_CELL_OBSERVATION_LAG_BARS = {c: 0.0 for c in _CELL_ORDER}


def _load_h101_harness():
    """RC-H101-1 harness import (dataset-name constants only; the statistical
    helpers formerly reached through here now live in screen_spine)."""
    if "rc_h101_harness" in sys.modules:
        return sys.modules["rc_h101_harness"]
    harness_path = _ROOT / "scripts" / "run_rc_h101_1_scan.py"
    spec = importlib.util.spec_from_file_location("rc_h101_harness", harness_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load the RC-H101-1 harness at {harness_path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["rc_h101_harness"] = mod
    spec.loader.exec_module(mod)
    return mod


_RC1 = _load_h101_harness()
# Reused from the RC-H101-1 harness (no re-declared literals): the
# substrate/provenance names cannot drift (audit REPRODUCIBILITY-1-3).
DATASET = _RC1.DATASET
PROVENANCE_FILE = _RC1.PROVENANCE_FILE


def _valid_5m_features(paths: ProjectPaths, symbol: str) -> pl.DataFrame:
    """Exclusion-filtered 5-min bars + emissions + session/segment labels.

    Identical pipeline to the backfill driver's `_load_valid_bars`
    (exclusions -> 5-min aggregation -> emissions -> emission_valid), so the
    screen's covariates and the backfilled expert see the same bar sequence
    by construction.
    """
    glob = str(paths.data_processed / DATASET / f"symbol={symbol}" / "**" / "*.parquet")
    lf = pl.scan_parquet(glob).select(
        "ts_event", "open", "high", "low", "close", "volume", "unadjusted_close", "pit_provisional"
    )
    gaps = json.loads(
        (paths.data_processed / "_provenance" / PROVENANCE_FILE).read_text(encoding="utf-8")
    )["coverage_gaps"]
    lf = apply_registered_exclusions(
        lf,
        symbol=symbol,
        exclusions=exclusion_windows_from_provenance(gaps),
        exclude_pit_provisional=True,
        exclude_coverage_gaps=True,
    )
    bars_5m = (
        lf.sort("ts_event")
        .group_by_dynamic("ts_event", every="5m", closed="left", label="left")
        .agg(
            open=pl.col("open").first(),
            high=pl.col("high").max(),
            low=pl.col("low").min(),
            close=pl.col("close").last(),
            volume=pl.col("volume").sum(),
            unadjusted_close=pl.col("unadjusted_close").last(),
        )
        .collect()
    )
    feats = compute_emissions(bars_5m).filter(pl.col("emission_valid")).sort("ts_event")
    return feats.with_columns(
        cme_session_date_expr("ts_event").alias("cme_session_date"),
        session_segment_expr("ts_event"),
        pl.col("ts_event").dt.convert_time_zone(NY_TZ).dt.hour().alias("ny_h"),
        pl.col("ts_event").dt.convert_time_zone(NY_TZ).dt.minute().alias("ny_m"),
    )


def _session_covariates(paths: ProjectPaths, symbol: str) -> pl.DataFrame:
    """Per-session §3 covariates: rvol_entry + gap-guarded prior RTH return."""
    feats = _valid_5m_features(paths, symbol)
    entry = (
        feats.filter(pl.col("segment") == SEGMENT_OVERNIGHT_ETH)
        .group_by("cme_session_date")
        .agg(rvol_entry=pl.col("rvol_5m_24h").sort_by("ts_event").first())
    )
    rth_ret = (
        feats.group_by("cme_session_date")
        .agg(
            c_open=pl.col("close")
            .filter(
                (pl.col("ny_h") == _RTH_RET_START_LABEL_H)
                & (pl.col("ny_m") == _RTH_RET_START_LABEL_M)
            )
            .first(),
            c_close=pl.col("close")
            .filter(
                (pl.col("ny_h") == _RTH_RET_END_LABEL_H) & (pl.col("ny_m") == _RTH_RET_END_LABEL_M)
            )
            .first(),
        )
        .with_columns(rth_ret=(pl.col("c_close") / pl.col("c_open")).log())
        .sort("cme_session_date")
        .with_columns(
            prior_rth_ret=pl.when(
                (pl.col("cme_session_date") - pl.col("cme_session_date").shift(1)).dt.total_days()
                <= _MAX_PRIOR_SESSION_GAP_DAYS
            )
            .then(pl.col("rth_ret").shift(1))
            .otherwise(None)
        )
    )
    return (
        entry.join(rth_ret, on="cme_session_date", how="left")
        .rename({"cme_session_date": "session_date"})
        .select("session_date", "rvol_entry", "prior_rth_ret")
        .sort("session_date")
    )


def _canary(paths: ProjectPaths, symbol: str) -> dict:
    """S-a: prefix-invariance canary on the evaluation substrate (H105 expert)."""
    glob = str(paths.data_processed / DATASET / f"symbol={symbol}" / "**" / "*.parquet")
    lf = pl.scan_parquet(glob).select("ts_event", "open", "high", "low", "close", "volume")
    bars_5m = (
        lf.sort("ts_event")
        .group_by_dynamic("ts_event", every="5m", closed="left", label="left")
        .agg(
            open=pl.col("open").first(),
            high=pl.col("high").max(),
            low=pl.col("low").min(),
            close=pl.col("close").last(),
            volume=pl.col("volume").sum(),
        )
        .tail(20_000)  # justify: canary substrate = recent ~1y (RC-*-2 screen rule)
        .collect()
    )
    window = BarWindow(
        ts=np.array(bars_5m.get_column("ts_event").to_list(), dtype=object),
        open=bars_5m.get_column("open").to_numpy().astype(np.float64),
        high=bars_5m.get_column("high").to_numpy().astype(np.float64),
        low=bars_5m.get_column("low").to_numpy().astype(np.float64),
        close=bars_5m.get_column("close").to_numpy().astype(np.float64),
        volume=bars_5m.get_column("volume").to_numpy().astype(np.float64),
    )
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert_prefix_invariant(OvernightSessionDriftExpert(), window)
    return {"instrument": symbol, "n_bars": int(bars_5m.height), "pass": True}


def _prepare_instrument(paths: ProjectPaths, symbol: str) -> spine.InstrumentData:
    """Load sessions + covariates, build the §3 cells, run the S-a canary."""
    ledger = spine.ledger_sessions(paths, LEDGER_EXPERT_ID, symbol)
    covs = _session_covariates(paths, symbol)
    vol = spine.per_origin_percentile(covs, "rvol_entry")
    df = (
        ledger.join(covs, on="session_date", how="inner")
        .join(vol, on="session_date", how="left")
        .sort("session_date")
    )
    dates = df.get_column("session_date").to_list()
    gross = df.get_column("gross").to_numpy().astype(np.float64)
    entered = (df.get_column("n_active").to_numpy() > 0) & np.isfinite(gross)
    prior = df.get_column("prior_rth_ret").to_numpy().astype(np.float64)
    pct = df.get_column("rvol_entry_pct").to_numpy().astype(np.float64)
    with np.errstate(invalid="ignore"):
        cells = {
            "unconditional": entered,
            # Leakage-clean per-origin tercile bands (design §3; the H103
            # RC-2 certified construction); unlabeled (pre-origin) sessions
            # belong to neither vol cell.
            "high_vol": entered & np.isfinite(pct) & (pct >= spine.VOL_TERCILE_HI),
            "low_vol": entered & np.isfinite(pct) & (pct <= spine.VOL_TERCILE_LO),
            "prior_rth_up": entered & np.isfinite(prior) & (prior > 0),
            "prior_rth_down": entered & np.isfinite(prior) & (prior < 0),
        }
    return spine.InstrumentData(
        instrument=symbol,
        dates=dates,
        gross=gross,
        entered=entered,
        cells=cells,
        canary=_canary(paths, symbol),
    )


SPEC = spine.ScreenSpec(
    scan_id="RC-H105-1",
    hid="H105",
    seed=SEED_SC,
    n_trials_gate=N_TRIALS_GATE,
    dwell_bars_per_session=float(ETH_BARS_PER_SESSION),
    cell_order=_CELL_ORDER,
    sigma_cells=_SIGMA_CELLS,
    primary_cell=_PRIMARY_CELL,
    ledger_expert_id=LEDGER_EXPERT_ID,
    observation_lag_bars=_CELL_OBSERVATION_LAG_BARS,
    dispersion_register_families=("rc-h101-2", "rc-h103-2"),
    prepare_instrument=_prepare_instrument,
    design_relpath="research/01_hypothesis_register/H105/design.md",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/H105")
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    return spine.run_main(paths, SPEC, DATASET, paths.root / args.out)


if __name__ == "__main__":
    raise SystemExit(main())
