"""RC-H101-2 / RC-H103-2 — ADR-0014 SCREEN re-runs (screen -> provisional pool).

Executes the FROZEN screen protocols
(research/01_hypothesis_register/H101/screen_addendum_2026-07-17.md,
research/01_hypothesis_register/H103/screen_addendum_2026-07-17.md) on the
canonical k1.0 shadow ledger. The estimand and conditioning sets are those of
the frozen 2026-07-16 designs; the screen adds the ADR-0014 gates:

  S-a  interface / prefix-invariance canary (re-run, 16 default cuts),
  S-b  the frozen conditioning cells (H103: the CERTIFIED leakage-clean
       per-rolling-origin stress construction — 24-month train window, first
       origin 2017-01-01, train-window HMM occupancy cutoff + train-window
       rvol percentile CDF, purge 288 bars),
  S-c  conditional gross edge: Romano-Wolf StepM per instrument over the
       5-cell family (seed 20260716, the design §11 registered seed;
       N_bootstrap 1000); PASS iff mean gross > 0 AND adjusted p <
       screening_error_rate_target (READ from config/multipletest_family.yaml
       — the level enacted by the discovery-alpha numeric instantiation,
       never hard-coded here),
  S-d  window persistence: DSR >= 1 - level at GATE trial count N=20 (raw
       register surface; correlation-adjusted N_eff reported), PBO <= level
       via CSCV S=16 on the per-instrument T x 5 masked contribution matrix,
       plus the per-cell rolling-origin growth series (stage seed 20260717),
  S-e  ex-ante selectability (amended rule, screen addenda at freeze): the
       1c emission returned latent-state latency UNATTAINABLE (no accurate
       operating point), so latent-state cells fail S-e outright; every
       H101/H103 cell is a RULE-BASED CAUSAL covariate whose S-e latency is
       its structural observation lag in RTH bars (0 for session-start
       cells, 12 = the opening-range window for first-hour-sign cells);
       PASS = median consecutive-session membership run x 78 RTH
       bars/session >= the lag. The supervised CUSUM value stays FORBIDDEN;
       the UNATTAINABLE verdict is recorded on every cell.

Disposition (ADR-0009/0014): >= 1 cell passing all five gates -> screen PASS
(pool entry; STOP before any set-level VERDICT); else
archive-no-persistent-window (sub-reason no-gross-edge iff S-c empty).
NOTHING is certified by this scan; pool entry is a queue position.

Usage:
    uv run python scripts/run_screen_h101_h103.py --hid H101 [--out reports/H101]
    uv run python scripts/run_screen_h101_h103.py --hid H103 [--out reports/H103]
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import polars as pl
import yaml

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.eval.windows import h900_windows  # noqa: E402
from skie_universe2.experts.base import BarWindow, assert_prefix_invariant  # noqa: E402
from skie_universe2.experts.orb_first_hour import OrbFirstHourExpert  # noqa: E402
from skie_universe2.features.regime_emissions import (  # noqa: E402
    apply_registered_exclusions,
    compute_emissions,
    emission_matrix,
    exclusion_windows_from_provenance,
    fit_moments,
    standardize,
)
from skie_universe2.inference.bootstrap import politis_white_block_length  # noqa: E402
from skie_universe2.inference.deflated_sharpe import deflated_sharpe_ratio  # noqa: E402
from skie_universe2.inference.pbo import probability_of_backtest_overfitting  # noqa: E402
from skie_universe2.inference.romano_wolf import romano_wolf_stepm  # noqa: E402
from skie_universe2.models.regime.hmm import GaussianHMM  # noqa: E402
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

# justify: design §11 registered scan seed (bit-identical S-c re-run commitment).
# The S-d / S-e stages are fully DETERMINISTIC (closed-form DSR, combinatorial
# CSCV, run-length medians) — no stage seed exists for them (round-2 audit
# QUANT-2-7/REPRODUCIBILITY-2-4).
SEED_SC = 20260716
# justify: H900 §11 / H103 design §3 registered HMM seed + 5 restarts.
HMM_SEED = 20260710
HMM_N_RESTARTS = 5
# justify: H900 registered winning family (4-state diagonal Gaussian).
HMM_N_STATES = 4
# justify: scan convention (RC-H101-1/RC-H103-1).
N_BOOTSTRAP = 1000
# justify: frozen pbo.py CSCV default (Bailey et al. 2017 S=16).
PBO_SPLITS = 16
# justify: screen-addendum GATE trial count = the register's full distinct
# instrument x cell surface (RC-H103-1 §3.3 convention; raw count binds, the
# correlation-adjusted N_eff is reported).
N_TRIALS_GATE = 20
# justify: RTH session length on the 5-minute grid: 09:30-16:00 NY = 78 bars.
RTH_BARS_PER_SESSION = 78
# justify: design §6 purge = MAX_FEATURE_LOOKBACK_BARS (288 five-min bars).
PURGE_BARS = 288
_MIN_CELL_N = 2  # justify: ddof=1 minimum; structural
_EPS = 1e-12  # justify: structural div-by-zero guard
_CELL_ORDER_H101 = ("unconditional", "high_vol", "low_vol", "first_hour_up", "first_hour_down")
_CELL_ORDER_H103 = ("unconditional", "stress", "non_stress", "first_hour_up", "first_hour_down")
_SIGMA_CELLS_H101 = ("high_vol", "low_vol", "first_hour_up", "first_hour_down")
_SIGMA_CELLS_H103 = ("stress", "non_stress", "first_hour_up", "first_hour_down")


def _load_h101_harness():
    """Import the RC-H101-1 harness (single source of truth for ledger/covariates).

    File-path import of a scripts/ module (not a package; pyproject
    ``package = false``); registered in sys.modules and guarded so a moved or
    renamed harness fails loudly (round-2 audit CODE-2-5).
    """
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


def _screen_level(paths: ProjectPaths) -> float:
    """Read the enacted screening_error_rate_target (single source of truth)."""
    cfg = yaml.safe_load((paths.config / "multipletest_family.yaml").read_text(encoding="utf-8"))
    level = cfg.get("screening_error_rate_target")
    if not isinstance(level, int | float) or not (0.0 < level < 1.0):
        raise RuntimeError(
            "screening_error_rate_target is not enacted in config/multipletest_family.yaml"
        )
    return float(level)


# justify: structural observation lag per RULE-BASED cell, in RTH bars: the
# session-start cells (trailing-rvol percentile, stress band, unconditional)
# are computed from data ending at/before the open (lag 0); the
# first-hour-sign cells resolve at the end of the opening-range window
# (n_or = 12 bars), before any ORB entry decision.
_CELL_OBSERVATION_LAG_BARS = {
    "unconditional": 0.0,
    "high_vol": 0.0,
    "low_vol": 0.0,
    "stress": 0.0,
    "non_stress": 0.0,
    "first_hour_up": 12.0,
    "first_hour_down": 12.0,
}


def _s_e_latency(paths: ProjectPaths) -> dict:
    """Read the S-e emission (P1-2.0-H900-BOCPD-WHITENED reproducible output).

    STOPS if the reproducible on-ledger artifact is absent — the
    supervised-CUSUM latency is FORBIDDEN and no placeholder is substituted
    (ADR-0014 S-e). Returns the emission block (latent-state attainability
    verdict + per-instrument values, null when unattainable).
    """
    p = paths.root / "reports" / "H900_whitened_roc" / "h900_whitened_roc.json"
    if not p.is_file():
        raise RuntimeError(
            "S-e latency input missing: reports/H900_whitened_roc/h900_whitened_roc.json "
            "(run scripts/run_h900_whitened_roc.py first; no placeholder is substituted)"
        )
    blob = json.loads(p.read_text(encoding="utf-8"))
    emission = blob.get("s_e_unsupervised_detection_latency")
    if not emission:
        raise RuntimeError("S-e emission block empty in the whitened-ROC artifact")
    return emission


def _canary(paths: ProjectPaths, harness, symbol: str) -> dict:
    """S-a: prefix-invariance canary re-run on the evaluation substrate.

    Rebuilds the 5-minute RTH bar window for one instrument from the same
    substrate pipeline the covariates use and asserts the expert's causal
    prefix invariance at the default 16 cuts.
    """
    # Rebuild the bar window from the same substrate the covariates use
    # (aggregation identical to the backfill) and assert causality on it.
    glob = str(paths.data_processed / harness.DATASET / f"symbol={symbol}" / "**" / "*.parquet")
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
        .tail(20_000)  # justify: canary substrate = the most recent ~1y of 5-min
        # bars (16 cuts need a representative window, not the full decade; the
        # canary property is per-bar causal and does not depend on span length)
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
    expert = OrbFirstHourExpert()
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        assert_prefix_invariant(expert, window)  # raises on violation
    return {"instrument": symbol, "n_bars": int(bars_5m.height), "pass": True}


def _h103_stress_labels(
    paths: ProjectPaths, harness, symbol: str
) -> tuple[pl.DataFrame, list[dict]]:
    """Leakage-clean per-origin stress labels (H103 addendum S-b).

    Per h900 rolling window (24-month train, 6-month step, first origin
    2017-01-01): fit the H900 HMM (4-state diag, seed 20260710, 5 restarts) on
    the TRAIN span's standardized emissions (train-window moments only; purge
    288 bars before the origin), take p-hat = the stationary occupancy of the
    max-log-rvol-mean state, and label an EVAL session stress iff its
    pre-session rvol percentile — scored against the TRAIN-window empirical
    CDF of session rvol — is >= (1 - p-hat).

    Returns (per-session frame: session_date, stress (bool), window_id) for
    eval spans only, plus the per-window fit diagnostics.
    """
    # Bar-level emissions for the HMM (harness substrate, exclusions applied;
    # rebuilt here because the harness exposes only per-session covariates).
    glob = str(paths.data_processed / harness.DATASET / f"symbol={symbol}" / "**" / "*.parquet")
    lf5 = pl.scan_parquet(glob).select(
        "ts_event", "open", "high", "low", "close", "volume", "unadjusted_close", "pit_provisional"
    )
    gaps = json.loads(
        (paths.data_processed / "_provenance" / harness.PROVENANCE_FILE).read_text("utf-8")
    )["coverage_gaps"]
    lf5 = apply_registered_exclusions(
        lf5,
        symbol=symbol,
        exclusions=exclusion_windows_from_provenance(gaps),
        exclude_pit_provisional=True,
        exclude_coverage_gaps=True,
    )
    bars_5m = (
        lf5.sort("ts_event")
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
    # Per-session rvol at RTH open (harness covariate) for percentile scoring.
    covs = harness._session_covariates(paths, symbol)  # session_date, rvol, fh_sign

    windows = h900_windows()
    rows: list[dict] = []
    diags: list[dict] = []
    for w in windows:
        # Expr-only boundary filter (round-2/3 audit CODE-2-4/CODE-3-5:
        # Series-vs-Expr reflected comparison is version-sensitive at a
        # leakage-critical cut; pl.col keeps the whole predicate in Expr space).
        t0 = pl.datetime(
            w.train_start.year, w.train_start.month, w.train_start.day, time_zone="UTC"
        )
        t1 = pl.datetime(w.origin.year, w.origin.month, w.origin.day, time_zone="UTC")
        train_feats = feats.filter((pl.col("ts_event") >= t0) & (pl.col("ts_event") < t1))
        if train_feats.height <= PURGE_BARS + _MIN_CELL_N:
            continue
        train_feats = train_feats.head(train_feats.height - PURGE_BARS)  # purge before origin
        x_train = emission_matrix(train_feats)
        moments = fit_moments(x_train)
        z_train = standardize(x_train, moments)
        model = GaussianHMM(n_states=HMM_N_STATES, covariance_type="diag").fit(
            z_train,
            seed=HMM_SEED,
            restart_seeds=[HMM_SEED + i for i in range(HMM_N_RESTARTS)],
        )
        means = model.params_.means
        stress_state = int(np.argmax(means[:, 1]))  # max log-rvol emission mean
        # Stationary occupancy of the stress state (Perron vector of transmat).
        tm = np.exp(model.params_.log_transmat)
        eigvals, eigvecs = np.linalg.eig(tm.T)
        k = int(np.argmin(np.abs(eigvals - 1.0)))
        pi = np.real(eigvecs[:, k])
        pi = np.abs(pi) / np.abs(pi).sum()
        p_hat = float(pi[stress_state])

        # Train-window session rvol CDF -> eval-session percentile >= 1 - p_hat.
        train_sessions = covs.filter(
            (pl.col("session_date") >= w.train_start) & (pl.col("session_date") < w.origin)
        )
        eval_sessions = covs.filter(
            (pl.col("session_date") >= w.origin) & (pl.col("session_date") < w.eval_end)
        )
        if train_sessions.height < _MIN_CELL_N or eval_sessions.height == 0:
            continue
        train_rvol = np.sort(train_sessions.get_column("rvol").to_numpy())
        ev_rvol = eval_sessions.get_column("rvol").to_numpy()
        pct = np.searchsorted(train_rvol, ev_rvol, side="right") / train_rvol.size
        stress = pct >= (1.0 - p_hat)
        ev_dates = eval_sessions.get_column("session_date").to_list()
        for d, s_flag in zip(ev_dates, stress, strict=True):
            rows.append({"session_date": d, "stress": bool(s_flag), "window_id": w.window_id})
        diags.append(
            {
                "window_id": w.window_id,
                "p_hat": p_hat,
                "stress_state": stress_state,
                "n_train_sessions": int(train_sessions.height),
                "n_eval_sessions": int(eval_sessions.height),
                "stress_fraction_eval": float(np.mean(stress)),
                "loglik": float(model.fit_result_.best_log_likelihood),
            }
        )
    return pl.DataFrame(rows), diags


def _member_only_sharpe(sub: np.ndarray) -> np.ndarray:
    """Per-column Sharpe over MEMBER (non-NaN) sessions of a CSCV submatrix.

    Columns with fewer than _MIN_CELL_N member rows in the submatrix score
    -inf (rank last deterministically; ddof=1 needs two observations).
    """
    n_cols = sub.shape[1]
    out = np.full(n_cols, -np.inf, dtype=np.float64)
    for j in range(n_cols):
        v = sub[:, j]
        v = v[np.isfinite(v)]
        if v.size < _MIN_CELL_N:
            continue
        sd = v.std(ddof=1)
        if sd > _EPS:
            out[j] = float(v.mean() / sd)
    return out


def _consecutive_run_median(members: np.ndarray) -> float:
    """Median run length (sessions) of consecutive TRUE membership."""
    if members.size == 0 or not members.any():
        return 0.0
    padded = np.concatenate(([False], members, [False]))
    starts = np.flatnonzero(padded[1:].astype(int) - padded[:-1].astype(int) == 1)
    ends = np.flatnonzero(padded[1:].astype(int) - padded[:-1].astype(int) == -1)
    runs = ends - starts
    return float(np.median(runs))


def _rolling_growth(gross: np.ndarray, dates: list, mask: np.ndarray) -> list[float]:
    """Mean gross over the cell's member sessions per REGISTERED eval window.

    Buckets are the design §6 / h900_windows() evaluation windows (15 per
    instrument, first origin 2017-01-01) — not calendar bins anchored at the
    first ledger session (round-2 audit QUANT-2-8); sessions outside the
    registered eval spans do not enter the vector.
    """
    if not dates:
        return []
    out = []
    for w in h900_windows():
        sel = mask & np.array([(w.origin <= d < w.eval_end) for d in dates])
        vals = gross[sel]
        vals = vals[np.isfinite(vals)]
        out.append(float(vals.mean()) if vals.size else float("nan"))
    return out


def run_screen(paths: ProjectPaths, hid: str) -> dict:  # noqa: PLR0912, PLR0915 — one linear, auditable screen sequence (S-a..S-e -> disposition); splitting would scatter the gate conjunction
    """Execute the frozen screen protocol for one HID."""
    harness = _load_h101_harness()
    level = _screen_level(paths)
    latency = _s_e_latency(paths)
    cell_order = _CELL_ORDER_H101 if hid == "H101" else _CELL_ORDER_H103
    sigma_cells = _SIGMA_CELLS_H101 if hid == "H101" else _SIGMA_CELLS_H103

    instruments_out = []
    for symbol in ("ES", "NQ"):
        ledger = harness._kelly1_gross_ledger(paths, symbol)
        covs = harness._session_covariates(paths, symbol)
        df = ledger.join(covs, on="session_date", how="inner").sort("session_date")
        dates = df.get_column("session_date").to_list()
        gross = df.get_column("gross").to_numpy().astype(np.float64)
        entered = (df.get_column("n_active").to_numpy() > 0) & np.isfinite(gross)
        rvol = df.get_column("rvol").to_numpy().astype(np.float64)
        fh = df.get_column("fh_sign").to_numpy().astype(np.float64)

        stress_diags = None
        if hid == "H101":
            cells = harness._cells(entered, rvol, fh)
        else:
            labels, stress_diags = _h103_stress_labels(paths, harness, symbol)
            # Order-safe join (round-2 audit QUANT-2-3): polars does not
            # guarantee output row order without maintain_order; every
            # per-session array is re-extracted from the JOINED frame so the
            # leakage-clean labels cannot misalign against gross/covariates.
            lab = df.join(labels, on="session_date", how="left", maintain_order="left")
            if lab.height != df.height:
                raise RuntimeError(
                    f"[{symbol}] H103 label join changed row count "
                    f"({df.height} -> {lab.height}); duplicate session labels?"
                )
            dates = lab.get_column("session_date").to_list()
            gross = lab.get_column("gross").to_numpy().astype(np.float64)
            entered = (lab.get_column("n_active").to_numpy() > 0) & np.isfinite(gross)
            rvol = lab.get_column("rvol").to_numpy().astype(np.float64)
            fh = lab.get_column("fh_sign").to_numpy().astype(np.float64)
            stress_col = lab.get_column("stress").to_numpy()
            labeled = np.array([s is not None for s in stress_col])
            stress_mask = np.array([bool(s) for s in stress_col.tolist()], dtype=bool) & labeled
            # Design-faithful cells: unconditional and the first-hour-sign
            # cells span ALL entered sessions (frozen design §3); only the
            # stress/non_stress pair is restricted to the leakage-clean
            # labeled span (sessions >= the first origin) — the certified
            # construction the screen addendum enacts.
            cells = {
                "unconditional": entered,
                "stress": entered & stress_mask,
                "non_stress": entered & labeled & ~stress_mask,
                "first_hour_up": entered & (fh > 0),
                "first_hour_down": entered & (fh < 0),
            }

        # ---- S-a canary ----
        canary = _canary(paths, harness, symbol)

        # ---- S-c Romano-Wolf at the enacted level ----
        masks = np.vstack([cells[c] for c in cell_order])
        rng = np.random.default_rng(SEED_SC)
        bl = max(politis_white_block_length(gross, bootstrap_type="stationary").block_length, 1.0)
        rw = romano_wolf_stepm(
            gross,
            masks,
            block_length=bl,
            rng=rng,
            n_bootstrap=N_BOOTSTRAP,
            alpha=level,
            min_n=_MIN_CELL_N,
        )

        # Per-cell metrics.
        def _sharpe(v: np.ndarray) -> float:
            v = v[np.isfinite(v)]
            if v.size < _MIN_CELL_N:
                return float("nan")
            sd = v.std(ddof=1)
            return float(v.mean() / sd) if sd > _EPS else float("nan")

        per_cell = []
        pooled_sr = []
        for i, c in enumerate(cell_order):
            v = gross[cells[c]]
            v = v[np.isfinite(v)]
            sr = _sharpe(gross[cells[c]])
            if c in sigma_cells and np.isfinite(sr):
                pooled_sr.append(sr)
            per_cell.append(
                {
                    "cell": c,
                    "n": int(cells[c].sum()),
                    "mean_gross": float(v.mean()) if v.size else float("nan"),
                    "sharpe": sr,
                    "stat": float(rw.stat[i]),
                    "rw_adj_pvalue": float(rw.adjusted_pvalue[i]),
                    "s_c_pass": bool(
                        v.size >= _MIN_CELL_N
                        and float(v.mean()) > 0.0
                        and float(rw.adjusted_pvalue[i]) < level
                    ),
                }
            )
        instruments_out.append(
            {
                "instrument": symbol,
                "canary": canary,
                "block_length": float(bl),
                "cells": per_cell,
                "gross": gross,
                "cells_masks": cells,
                "dates": dates,
                "entered": entered,
                "stress_diags": stress_diags,
            }
        )

    # ---- S-d: DSR + PBO + growth series (pooled sigma across instruments) ----
    pooled = []
    for inst in instruments_out:
        for c in inst["cells"]:
            if c["cell"] in sigma_cells and np.isfinite(c["sharpe"]):
                pooled.append(c["sharpe"])
    sr_std = float(np.std(pooled, ddof=1)) if len(pooled) > 1 else float("nan")

    for inst in instruments_out:
        gross = inst["gross"]
        cells = inst["cells_masks"]
        dates = inst["dates"]
        # PBO on the NaN-masked T x 5 matrix with a MEMBER-ONLY Sharpe scorer
        # (round-2 audit QUANT-2-4: zero-filled masking shrinks each column's
        # Sharpe by sqrt(member density), so cross-column ranks are NOT
        # preserved when densities differ; scoring each column on its member
        # sessions only within each CSCV split removes the density distortion).
        mat = np.column_stack([np.where(cells[c], gross, np.nan) for c in cell_order])
        pbo_res = probability_of_backtest_overfitting(
            mat, s_splits=PBO_SPLITS, score_fn=_member_only_sharpe
        )
        inst["pbo"] = {
            "pbo": float(pbo_res.pbo),
            "s_splits": PBO_SPLITS,
            "n_combinations": int(pbo_res.n_combinations),
            "construction": (
                "NaN-masked T x 5 per-session matrix, member-only Sharpe "
                "score_fn (screen addendum S-d as remediated in audit round 2)"
            ),
        }
        # Correlation-adjusted effective trial count (reported; gate binds at
        # raw N). Pairwise-COMPLETE correlations (round-3 audit CODE-3-2:
        # np.corrcoef on the NaN-masked matrix NaNs out every pair touching a
        # conditional column, silently voiding the registered diagnostic):
        # each pair is estimated on sessions where BOTH cells are members
        # (>= _MIN_CELL_N overlap required; disjoint pairs are skipped).
        pair_rhos: list[float] = []
        n_cols = mat.shape[1]
        for a in range(n_cols):
            for b in range(a + 1, n_cols):
                both = np.isfinite(mat[:, a]) & np.isfinite(mat[:, b])
                if int(both.sum()) < _MIN_CELL_N:
                    continue
                va, vb = mat[both, a], mat[both, b]
                if va.std(ddof=1) <= _EPS or vb.std(ddof=1) <= _EPS:
                    continue
                pair_rhos.append(float(np.corrcoef(va, vb)[0, 1]))
        if pair_rhos:
            rho_bar = float(np.mean(pair_rhos))
            n_eff_corr = N_TRIALS_GATE / (1.0 + (N_TRIALS_GATE - 1) * max(rho_bar, 0.0))
        else:
            rho_bar = None
            n_eff_corr = None
        inst["cell_dependence"] = {
            "rho_bar_pairwise_complete": rho_bar,
            "n_estimable_pairs": len(pair_rhos),
            "note": (
                "pairwise-complete member-overlap correlations; disjoint cell "
                "pairs (no >= 2-session overlap) are not estimable and are "
                "skipped; null when no pair is estimable"
            ),
        }
        for c in inst["cells"]:
            mask = cells[c["cell"]]
            v = gross[mask]
            v = v[np.isfinite(v)]
            if v.size < _MIN_CELL_N or not np.isfinite(sr_std) or sr_std <= _EPS:
                c["s_d"] = {"dsr": float("nan"), "pass": False, "reason": "degenerate"}
                continue
            vif = harness._hac_variance_inflation(v)
            n_eff = max(int(round(v.size / vif)), _MIN_CELL_N)
            sd = v.std()
            skew = float(((v - v.mean()) ** 3).mean() / (sd**3 + _EPS))
            kurt = float(((v - v.mean()) ** 4).mean() / (sd**4 + _EPS))
            dsr = deflated_sharpe_ratio(
                c["sharpe"], n_eff, N_TRIALS_GATE, sr_std, skew=skew, kurtosis=kurt
            )
            growth_series = _rolling_growth(gross, dates, mask)
            finite = [g for g in growth_series if np.isfinite(g)]
            c["s_d"] = {
                "dsr": float(dsr.dsr),
                "dsr_bound": 1.0 - level,
                "dsr_pass": bool(dsr.dsr >= 1.0 - level),
                "pbo": inst["pbo"]["pbo"],
                "pbo_bound": level,
                "pbo_pass": bool(inst["pbo"]["pbo"] <= level),
                "n_eff_hac": n_eff,
                "hac_vif": float(vif),
                "n_trials_gate": N_TRIALS_GATE,
                "n_eff_corr_adjusted_reported": (
                    float(n_eff_corr) if n_eff_corr is not None else None
                ),
                "per_window_growth": growth_series,
                "positive_window_fraction": (
                    float(np.mean([g > 0 for g in finite])) if finite else float("nan")
                ),
                "pass": bool(dsr.dsr >= 1.0 - level and inst["pbo"]["pbo"] <= level),
            }
        # ---- S-e (amended rule: rule-based cells use their structural
        # observation lag; latent-state latency is UNATTAINABLE per the 1c
        # emission and is recorded as the standing reason latent-state
        # conditioning cannot pass this gate) ----
        latent_attainable = bool(latency.get("latent_state_latency_attainable", False))
        for c in inst["cells"]:
            mask = cells[c["cell"]]
            med_run = _consecutive_run_median(mask[inst["entered"]])
            dwell_bars = med_run * RTH_BARS_PER_SESSION
            obs_lag = _CELL_OBSERVATION_LAG_BARS.get(c["cell"])
            c["s_e"] = {
                "median_membership_run_sessions": med_run,
                "cell_dwell_bars": dwell_bars,
                "cell_mechanism": "rule-based-causal-covariate",
                "observation_lag_bars": obs_lag,
                "latent_state_latency_attainable": latent_attainable,
                "latent_state_note": (
                    "latent-state unsupervised latency UNATTAINABLE on the "
                    "reproducible 1c emission; a latent-state cell would FAIL "
                    "this gate outright"
                ),
                "pass": bool(obs_lag is not None and dwell_bars >= obs_lag),
            }
        # Gate conjunction per cell.
        for c in inst["cells"]:
            c["screen_pass"] = bool(
                inst["canary"]["pass"]
                and c["s_c_pass"]
                and c.get("s_d", {}).get("pass", False)
                and c.get("s_e", {}).get("pass", False)
            )
        # Drop numpy internals before serialization.
        inst.pop("gross")
        inst.pop("cells_masks")
        inst.pop("dates")
        inst.pop("entered")

    any_pass = any(c["screen_pass"] for inst in instruments_out for c in inst["cells"])
    any_sc = any(c["s_c_pass"] for inst in instruments_out for c in inst["cells"])
    if any_pass:
        disposition = (
            "screen-pass -> provisional pool (pool-hold-reconsider eligible; "
            "VERDICT deferred, |arsenal| = 0)"
        )
    elif any_sc:
        disposition = (
            "archive-no-persistent-window (gross edge present in >= 1 cell but "
            "persistence/selectability gates fail)"
        )
    else:
        disposition = (
            "archive-no-persistent-window (sub-reason: archive-no-gross-edge — "
            "no S-c pass in any cell)"
        )

    return {
        "scan": f"RC-{hid}-2",
        "hypothesis_id": hid,
        "screen_level": level,
        "s_e_emission": latency,
        "seed_s_c": SEED_SC,
        "s_d_s_e_stages": "deterministic (no RNG consumed)",
        "n_bootstrap": N_BOOTSTRAP,
        "disposition": disposition,
        "decision_rule": (
            "ADR-0014 SCREEN: a cell passes iff S-a canary AND mean gross > 0 AND "
            f"RW-adjusted p < {level} (S-c) AND DSR >= {1 - level:.4f} AND PBO <= "
            f"{level} (S-d) AND cell dwell >= the unsupervised detection latency "
            "(S-e). >= 1 passing cell -> pool entry; else "
            "archive-no-persistent-window. NOTHING certified; VERDICT deferred."
        ),
        "instruments": instruments_out,
    }


def _json_sanitize(obj):
    """RFC 8259-safe serialization: NaN -> null, +/-inf -> string sentinels.

    NaN maps to JSON null (the canonical missing-value encoding — typed
    consumers of numeric arrays, e.g. the pool-ledger growth vectors, read
    null natively; Phase-2 audit CODE-1-2/REPRODUCIBILITY-1-2). Signed
    infinities keep string sentinels (they are verdict-bearing values, not
    missing data).
    """
    if isinstance(obj, dict):
        return {k: _json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_json_sanitize(v) for v in obj]
    if isinstance(obj, float) and not np.isfinite(obj):
        # nan compares False on both > and < -> falls through to None (null)
        return "inf" if obj > 0 else ("-inf" if obj < 0 else None)
    return obj


def main() -> int:
    """ReproLog -> screen -> JSON artifact -> console summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hid", required=True, choices=("H101", "H103"))
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    out_dir = paths.root / (args.out or f"reports/{args.hid}")
    out_dir.mkdir(parents=True, exist_ok=True)

    addendum = (
        paths.root / "research/01_hypothesis_register" / args.hid / "screen_addendum_2026-07-17.md"
    )
    addendum_sha = hashlib.sha256(addendum.read_bytes()).hexdigest()
    roc = paths.root / "reports/H900_whitened_roc/h900_whitened_roc.json"
    # Bind the EVALUATION SUBSTRATE (round-2 audit REPRODUCIBILITY-2-2): the
    # vendor substrate checksums from data/_manifest.json (the RC-H101-1
    # rule, reused) + the level-supplying config + the addendum + the S-e
    # emission artifact.
    harness = _load_h101_harness()
    checksums = dict(harness._dataset_checksums(paths))
    checksums[f"research/01_hypothesis_register/{args.hid}/screen_addendum_2026-07-17.md"] = (
        addendum_sha
    )
    checksums["config/multipletest_family.yaml"] = hashlib.sha256(
        (paths.config / "multipletest_family.yaml").read_bytes()
    ).hexdigest()
    if roc.is_file():
        checksums["reports/H900_whitened_roc/h900_whitened_roc.json"] = hashlib.sha256(
            roc.read_bytes()
        ).hexdigest()
    log = reproducibility.capture(
        phase=f"rc-{args.hid.lower()}-2-screen",
        hypothesis_id=args.hid,
        rng_seed=SEED_SC,
        dataset_checksums=checksums,
        config_resolved_sha256=addendum_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (addendum SHA {addendum_sha[:12]}...)", flush=True)

    result = run_screen(paths, args.hid)
    result["repro_log"] = log_path.name
    result["screen_addendum_sha256"] = addendum_sha
    out_path = out_dir / f"rc_{args.hid.lower()}_2_screen.json"
    out_path.write_text(
        json.dumps(_json_sanitize(result), indent=2, sort_keys=True, default=str, allow_nan=False),
        encoding="utf-8",
    )
    print(f"[{result['scan']}] disposition: {result['disposition']}", flush=True)
    for inst in result["instruments"]:
        for c in inst["cells"]:
            if c["s_c_pass"] or c["screen_pass"]:
                sd = c.get("s_d", {})
                se = c.get("s_e", {})
                print(
                    f"  {inst['instrument']}/{c['cell']}: S-c p={c['rw_adj_pvalue']:.3f} "
                    f"DSR={sd.get('dsr', float('nan')):.3f} PBO={sd.get('pbo', float('nan')):.3f} "
                    f"dwell={se.get('cell_dwell_bars', float('nan')):.0f} "
                    f"lag={se.get('observation_lag_bars', float('nan'))} "
                    f"PASS={c['screen_pass']}",
                    flush=True,
                )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
