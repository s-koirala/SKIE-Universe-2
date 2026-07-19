"""RC-H106-1 — ADR-0014 SCREEN of the variance-ratio range-state reversal expert.

Executes the FROZEN H106 protocol
(research/01_hypothesis_register/H106/design.md §5) on the canonical k1.0
shadow ledger (`expert_id=vr_range_reversal_k1.0@1.0.0`). The statistical
spine is the packaged module :mod:`skie_universe2.screening.screen_spine`
(single source of truth, shared with RC-H105-1; extracted per the
pre-freeze audit CODE-1-1/2 — no copy-pasted stages, no private-name
reach-through). This script supplies only the H106-specific pieces
(design §§3-5):

- the per-session estimand loader (reversal gross from the H106 ledger),
- the §3 conditioning covariates, both evaluated at the close of the
  session's first overnight-segment bar (the entry decision point):
  ``rvol_entry`` and ``vr_state_at_open`` — the trailing variance-ratio
  state (registered constants window 288 / q 2) computed on the SAME
  exclusion-filtered emission_valid bar sequence the backfilled expert
  consumes (both pipelines share `_valid_5m_features` / `_load_valid_bars`
  construction, so the state sequences coincide by construction),
- the §3 cells: unconditional, vr_range_at_open (PRIMARY),
  vr_trend_at_open, high_vol/low_vol via the CERTIFIED leakage-clean
  per-origin train-window-CDF tercile construction (never full-sample),
- the registered §8 pairwise contrast (vr_range_at_open vs
  vr_trend_at_open, Ledoit-Wolf 2008 on the cell-masked paired series),
- the S-a prefix-invariance canary on the H106 expert,
- the frozen ScreenSpec (seed 20260720; N_TRIALS_GATE 40 with matched
  dispersion families rc-h101-2 + rc-h103-2 + rc-h105-1; session dwell
  273 bars).

Usage:
    uv run python scripts/run_screen_h106.py [--out reports/H106]
"""

from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import numpy as np
import polars as pl

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.experts.base import BarWindow, assert_prefix_invariant  # noqa: E402
from skie_universe2.experts.vr_range_reversal import VrRangeReversalExpert  # noqa: E402
from skie_universe2.features.variance_ratio_state import (  # noqa: E402
    VR_LAG_Q,
    VR_WINDOW_BARS,
    VarianceRatioState,
    variance_ratio_state,
)
from skie_universe2.screening import screen_spine as spine  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402
from skie_universe2.utils.sessions import SEGMENT_OVERNIGHT_ETH  # noqa: E402

# The H105 script provides the shared substrate loader `_valid_5m_features`
# (same pipeline as the backfill driver). Deliberate module-internal reuse
# of a script-level helper (round-3 audit CODE-3-2: the STATISTICAL spine is
# screen_spine; this is the substrate loader only, and promoting it to a
# packaged public name is a logged residual, not done here).
sys.path.insert(0, str(_ROOT / "scripts"))
import run_screen_h105 as h105_script  # noqa: E402

# justify: design §11 registered scan seed (fresh H106 family, date-derived,
# distinct from H105's so the two scans' bootstrap draws are independent).
SEED_SC = 20260720
# justify: design §5 — the register's full distinct instrument x cell screen
# surface after rc-h106-1 registers (rc-h101-2 10 + rc-h103-2 10 +
# rc-h105-1 10 + rc-h106-1 10); raw count binds, matched dispersion per
# screen_spine (families below).
N_TRIALS_GATE = 40
# justify: median full-session bar count on the 5-minute grid (P3-A
# per-session medians: 186 overnight + 78 RTH + 9 post-RTH; design §3).
SESSION_BARS_MEDIAN = 273
_CELL_ORDER = ("unconditional", "vr_range_at_open", "vr_trend_at_open", "high_vol", "low_vol")
_SIGMA_CELLS = ("vr_range_at_open", "vr_trend_at_open", "high_vol", "low_vol")
_PRIMARY_CELL = "vr_range_at_open"  # justify: design §3 — the mechanism's own state
LEDGER_EXPERT_ID = "vr_range_reversal_k1.0@1.0.0"
# justify: structural observation lag per RULE-BASED cell: all §3 cells are
# decided at the entry bar's close (design §3 S-e; lag 0).
_CELL_OBSERVATION_LAG_BARS = {c: 0.0 for c in _CELL_ORDER}
DATASET = h105_script.DATASET


def _session_covariates(paths: ProjectPaths, symbol: str) -> pl.DataFrame:
    """Per-session §3 covariates: rvol_entry + vr_state_at_open.

    Both evaluated at the close of the session's FIRST overnight-segment
    bar. The VR state is computed on the contiguous valid-bar return
    sequence (design §3 continuous-sequence convention) of the SAME
    pipeline the backfilled expert consumes.
    """
    feats = h105_script._valid_5m_features(paths, symbol)
    close = feats.get_column("close").to_numpy().astype(np.float64)
    r = np.log(close[1:] / close[:-1])
    state_r = variance_ratio_state(r, window=VR_WINDOW_BARS, q=VR_LAG_Q)
    # state at bar t (t >= 1) = trailing state through return r[t-1] (the
    # return OVER bar t); bar 0 has no return -> UNDETERMINED.
    state_bar = np.concatenate(([VarianceRatioState.UNDETERMINED], state_r))
    feats = feats.with_columns(pl.Series("vr_state", state_bar))
    entry = (
        feats.filter(pl.col("segment") == SEGMENT_OVERNIGHT_ETH)
        .group_by("cme_session_date")
        .agg(
            rvol_entry=pl.col("rvol_5m_24h").sort_by("ts_event").first(),
            vr_state_at_open=pl.col("vr_state").sort_by("ts_event").first(),
        )
    )
    return (
        entry.rename({"cme_session_date": "session_date"})
        .select("session_date", "rvol_entry", "vr_state_at_open")
        .sort("session_date")
    )


def _canary(paths: ProjectPaths, symbol: str) -> dict:
    """S-a: prefix-invariance canary on the evaluation substrate (H106 expert).

    Bounded sample: causality is per-bar; the VR warm-up (~289 bars) plus
    several sessions suffice, and the 16-cut sweep re-signals the window
    each cut with an O(n) VR pass (backfill-driver bounded-canary rule).
    """
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
        # justify: VR warm-up (289) + ~17 sessions; bounded-canary rule.
        .tail(5_000)
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
        assert_prefix_invariant(VrRangeReversalExpert(), window)
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
    vr_state = df.get_column("vr_state_at_open").to_numpy().astype(np.int64)
    pct = df.get_column("rvol_entry_pct").to_numpy().astype(np.float64)
    with np.errstate(invalid="ignore"):
        cells = {
            "unconditional": entered,
            "vr_range_at_open": entered & (vr_state == VarianceRatioState.RANGE),
            "vr_trend_at_open": entered & (vr_state == VarianceRatioState.TREND),
            # Leakage-clean per-origin tercile bands (design §3; never
            # full-sample); unlabeled (pre-origin) sessions in neither cell.
            "high_vol": entered & np.isfinite(pct) & (pct >= spine.VOL_TERCILE_HI),
            "low_vol": entered & np.isfinite(pct) & (pct <= spine.VOL_TERCILE_LO),
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
    scan_id="RC-H106-1",
    hid="H106",
    seed=SEED_SC,
    n_trials_gate=N_TRIALS_GATE,
    dwell_bars_per_session=float(SESSION_BARS_MEDIAN),
    cell_order=_CELL_ORDER,
    sigma_cells=_SIGMA_CELLS,
    primary_cell=_PRIMARY_CELL,
    ledger_expert_id=LEDGER_EXPERT_ID,
    observation_lag_bars=_CELL_OBSERVATION_LAG_BARS,
    dispersion_register_families=("rc-h101-2", "rc-h103-2", "rc-h105-1"),
    prepare_instrument=_prepare_instrument,
    design_relpath="research/01_hypothesis_register/H106/design.md",
    pairwise_contrast=("vr_range_at_open", "vr_trend_at_open"),
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/H106")
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    return spine.run_main(paths, SPEC, DATASET, paths.root / args.out)


if __name__ == "__main__":
    raise SystemExit(main())
