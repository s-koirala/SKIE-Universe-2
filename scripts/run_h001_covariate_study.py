"""H001 covariate-information study — production run of the frozen design.

Executes research/01_hypothesis_register/H001/design.md (SHA in the emitted
ReproLog ``config_resolved_sha256``) PRIMARY analysis: does the small-n vol×trend
regime label ``S_vt`` carry non-redundant information about forward
reversion/continuation (the §4 self-normalizing variance-ratio proxy ``Y_h``)
BEYOND the registered H900 HMM covariate ``S_hmm`` and the project-standard
variance-ratio state ``S_vr`` (``Z = {S_hmm, S_vr}``)?

Per instrument (ES, NQ) × 15 rolling-origin windows (H900 §2, adopted by H001 §2):
  1. Fit the registered conditioning covariate S_hmm = 4-state diag-Gaussian HMM
     on standardized (ret_5m, log rvol_5m_24h) train emissions; causal
     warm-started filter → MAP state over train + eval.
  2. S_vr = causal Lo-MacKinlay variance-ratio trend/range state (per segment).
  3. Y_h = forward variance-ratio proxy (per segment), sign-labelled.
  4. For each of the 400 arms (trend_fam × vol_fam × n_t × n_v), emit S_vt with
     the leakage-safe fit(train)/transform contract, and compute on the eval
     (OOS) slice: Miller-Madow CMI I(Y;S_vt|Z), redundancy (adjusted Rand/AMI vs
     S_hmm, S_vr), and the nested train→eval predictive-information delta.
  5. BINDING pooled CMI = n-weighted average of PER-WINDOW Miller-Madow CMI
     (bias-corrected; labels stay within-window, comparable). For candidate arms
     (binding CMI > 0) compute the §8 stationary-bootstrap CI shifted onto the
     MM-corrected scale. The within-Z-cell permutation p-value is ILLUSTRATIVE
     ONLY (anti-conservative on the overlapping-window target) and not part of the
     decision.
  6. §10 decision: an arm meets H1 on an instrument/horizon iff its MM-corrected
     pooled CMI 95% CI lower bound > 0 AND its mean nested OOS delta_logloss > 0
     (precision gate §8). The discovery/FWER level is the DEFERRED project-wide
     screening_error_rate_target, so no arm is CERTIFIED — the scan is reported
     descriptively, and at ~N=1e5+ bars a negligible CMI trivially clears CI>0, so
     EFFECT MAGNITUDES (CMI nats, OOS delta) are the material read, not the H1 count.

Deviations (logged): (a) S_vr window/lag instantiated to repo scales (288/2) as
the project-standard covariate is not numerically pinned (variance_ratio_state.py
note); (b) train/eval purge = MAX_FEATURE_LOOKBACK_BARS (288), conservatively
exceeding the design §6 nominal max(max(n_v,n_t), h); (c) bootstrap CI computed
for candidate arms (binding MM-CMI > 0) only — a non-positive point estimate
cannot yield a positive CI lower bound, so no H1 arm is dropped; (d) the CMI gate
uses the Miller-Madow-corrected estimate, not the biased plug-in (QUANT-1-1); the
permutation is illustrative-only (QUANT-1-2).

Usage:
    uv run python scripts/run_h001_covariate_study.py [--out reports/H001]
        [--instruments ES,NQ] [--max-windows N] [--max-arms N] [--variant primary]
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.eval.windows import h900_windows  # noqa: E402
from skie_universe2.features.regime_emissions import (  # noqa: E402
    MAX_FEATURE_LOOKBACK_BARS,
    apply_registered_exclusions,
    compute_emissions,
    exclusion_windows_from_provenance,
    fit_moments,
    standardize,
)
from skie_universe2.features.variance_ratio_state import (  # noqa: E402
    VR_LAG_Q,
    VR_WINDOW_BARS,
    variance_ratio_state,
)
from skie_universe2.inference.bootstrap import politis_white_block_length  # noqa: E402
from skie_universe2.inference.covariate_information import (  # noqa: E402
    cmi_pointwise_contributions,
    conditional_mutual_information,
    forward_variance_ratio,
    nested_predictive_delta,
    partition_redundancy,
    stationary_bootstrap_mean_ci,
    stratified_permutation_pvalue,
    vr_sign_label,
)
from skie_universe2.models.regime.dwell import filtered_state_path  # noqa: E402
from skie_universe2.models.regime.hmm import GaussianHMM  # noqa: E402
from skie_universe2.signals.regime_covariate import (  # noqa: E402
    TREND_FAMILIES,
    VOL_FAMILIES,
    OHLCArrays,
    states_from_scalars,
    trend_scalar,
    vol_scalar,
)
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

# ---- registered run parameters (H001 frozen design) ----
SEED = 20260716  # justify: H001 design.md §11 pre-registered RNG seed
HMM_N_STATES = 4  # justify: registered regime_hmm_h900 covariate (conditioning_covariates.yaml)
HMM_COV = "diag"  # justify: registered regime_hmm_h900 covariate
N_RESTARTS = 5  # justify: H900 HMM toolkit restart convention (carried)
RESTART_SEEDS = [SEED + i for i in range(N_RESTARTS)]
WINDOW_GRID = (2, 3, 4, 5, 8)  # justify: H001 design.md §3 registered window grid
HORIZONS = (6, 12)  # justify: H001 design.md §4 registered horizons (h=12 primary)
PURGE_BARS = MAX_FEATURE_LOOKBACK_BARS  # justify: conservative boundary purge (deviation b)
ALPHA = 0.05  # justify: H001 design.md §8 descriptive-CI level
N_BOOTSTRAP = 300  # justify: pooled-CI bootstrap replication (Politis-Romano 1994)
N_PERMUTATIONS = 199  # justify: conditional restricted-permutation MC resolution (p >= 1/200)
PRECISION_HALF_WIDTH_FRAC = 0.25  # justify: H001 design.md §8 (H900-inherited precision gate)
SAMPLE_START = date(2015, 1, 2)  # justify: H001/H900 §2 sample start
SAMPLE_END = date(2025, 12, 31)  # justify: H001/H900 §2 sample end
# Structural floor: a window's usable eval sample must be large enough that the
# discrete CMI contingency table and the permutation null are non-degenerate.
# Not an analysis threshold — a guard skipping windows with almost no valid bars.
MIN_EVAL_BARS = 50  # justify: structural minimum for a non-degenerate discrete CMI
# The permutation p-value is ILLUSTRATIVE ONLY (anti-conservative on the
# overlapping-window target, QUANT-1-2); compute it for the K highest-CMI arms per
# instrument as a diagnostic exhibit rather than all H1 arms. Not a coverage cap
# on inference — the binding gate is the MM-corrected block-bootstrap CI.
PERM_TOP_K = 6  # justify: illustrative-diagnostic sample size, not an analysis threshold
DATASET = "vendor_legacy_1min_roll_adjusted"
PROVENANCE_FILE = "vendor_legacy_1min_roll_adjusted_20260711.json"


@dataclass
class ArmResult:
    """Pooled per-(arm, instrument, horizon) covariate-information record."""

    instrument: str
    horizon: int
    trend_family: str
    vol_family: str
    n_t: int
    n_v: int
    n_windows: int
    n_eval_bars: int
    cmi_point: float  # BINDING: n-weighted per-window Miller-Madow CMI, nats
    cmi_plugin: float  # pooled plug-in CMI (biased; reported for transparency), nats
    cmi_mm_mean: float  # unweighted mean of per-window Miller-Madow CMI, nats
    cmi_ci_low: float
    cmi_ci_high: float
    perm_pvalue: float
    mean_delta_logloss: float
    frac_windows_delta_pos: float
    mean_delta_mcfadden: float
    ari_vs_hmm: float
    ari_vs_vr: float
    ami_vs_hmm: float
    ami_vs_vr: float
    is_candidate: bool
    h1_met: bool
    precision_ok: bool


def _load_bars_1min(paths: ProjectPaths, symbol: str) -> pl.LazyFrame:
    glob = str(paths.data_processed / DATASET / f"symbol={symbol}" / "**" / "*.parquet")
    return pl.scan_parquet(glob).select(
        "ts_event", "open", "high", "low", "close", "volume", "pit_provisional"
    )


def _coverage_gaps(paths: ProjectPaths) -> list[dict]:
    payload = json.loads(
        (paths.data_processed / "_provenance" / PROVENANCE_FILE).read_text(encoding="utf-8")
    )
    return payload["coverage_gaps"]


def _dataset_checksums(paths: ProjectPaths) -> dict[str, str]:
    manifest = json.loads((paths.data / "_manifest.json").read_text(encoding="utf-8"))
    out = {k: e["sha256"] for k, e in manifest["files"].items() if DATASET in k}
    if not out:
        raise RuntimeError("no dataset checksums found in data/_manifest.json")
    return out


def _utc(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=None)


def _segment_ids(ts: np.ndarray, max_gap_days: float = 7.0) -> np.ndarray:
    """Contiguity segments: split where consecutive valid bars are > 7 days apart."""
    if ts.size == 0:
        return np.empty(0, dtype=np.int64)
    gaps = np.diff(ts.astype("datetime64[s]").astype(np.int64))
    breaks = gaps > max_gap_days * 86400.0
    return np.concatenate([[0], np.cumsum(breaks)]).astype(np.int64)


def _trailing_boundary_ok(seg: np.ndarray, lookback: int) -> np.ndarray:
    """True where a trailing ``lookback``-window does not cross a segment break."""
    n = seg.size
    ok = np.zeros(n, dtype=bool)
    ok[lookback - 1 :] = seg[lookback - 1 :] == seg[: n - lookback + 1]
    return ok


def _forward_boundary_ok(seg: np.ndarray, lookahead: int) -> np.ndarray:
    """True where a forward ``lookahead``-window does not cross a segment break."""
    n = seg.size
    ok = np.zeros(n, dtype=bool)
    ok[: n - lookahead] = seg[: n - lookahead] == seg[lookahead:]
    return ok


def _forward_target_labels(r: np.ndarray, seg: np.ndarray, h: int) -> np.ndarray:
    """Sign-labelled forward VR target, invalidated across segment breaks."""
    vr = forward_variance_ratio(r, h)
    lab = vr_sign_label(vr)
    lab[~_forward_boundary_ok(seg, h)] = -1  # forward window crosses a break
    return lab


def _svr_labels(r: np.ndarray, seg: np.ndarray) -> np.ndarray:
    """S_vr trend/range labels, invalidated where the trailing window crosses a break."""
    st = variance_ratio_state(r, window=VR_WINDOW_BARS, q=VR_LAG_Q)
    st[~_trailing_boundary_ok(seg, VR_WINDOW_BARS + VR_LAG_Q - 1)] = -1
    return st


def run_instrument(  # noqa: PLR0912, PLR0915 — single-pass scan orchestrator; splitting would scatter the registered protocol
    *,
    paths: ProjectPaths,
    symbol: str,
    variant: str,
    arms: list[tuple[str, str, int, int]],
    max_windows: int | None,
) -> list[ArmResult]:
    """Run the full covariate-information scan for one instrument."""
    exclude = variant == "primary"
    exclusions = exclusion_windows_from_provenance(_coverage_gaps(paths))
    lf = _load_bars_1min(paths, symbol).filter(
        pl.col("ts_event").is_between(
            pl.lit(_utc(SAMPLE_START)).dt.replace_time_zone("UTC"),
            pl.lit(_utc(SAMPLE_END) + timedelta(days=1)).dt.replace_time_zone("UTC"),
            closed="left",
        )
    )
    lf = apply_registered_exclusions(
        lf,
        symbol=symbol,
        exclusions=exclusions,
        exclude_pit_provisional=exclude,
        exclude_coverage_gaps=exclude,
    )
    bars_1m = lf.collect()
    bars_5m = (
        bars_1m.lazy()
        .sort("ts_event")
        .group_by_dynamic("ts_event", every="5m", closed="left", label="left")
        .agg(
            open=pl.col("open").first(),
            high=pl.col("high").max(),
            low=pl.col("low").min(),
            close=pl.col("close").last(),
            volume=pl.col("volume").sum(),
        )
        .collect()
    )
    feats = compute_emissions(bars_5m)
    valid = feats.filter(pl.col("emission_valid")).sort("ts_event")
    ts_all = valid.get_column("ts_event").to_numpy()
    seg_all = _segment_ids(ts_all)
    ohlc = OHLCArrays(
        open=valid.get_column("open").to_numpy(),
        high=valid.get_column("high").to_numpy(),
        low=valid.get_column("low").to_numpy(),
        close=valid.get_column("close").to_numpy(),
    )
    r_all = valid.get_column("ret_5m").to_numpy()
    x_emit = np.column_stack(
        [valid.get_column("ret_5m").to_numpy(), valid.get_column("log_rvol_5m_24h").to_numpy()]
    )
    print(
        f"[{variant}/{symbol}] {bars_1m.height} 1-min -> {valid.height} valid 5-min bars",
        flush=True,
    )

    windows = h900_windows()
    if max_windows is not None:
        windows = windows[:max_windows]

    # S_vr and forward targets are global causal series (segment-aware).
    svr_all = _svr_labels(r_all, seg_all)
    y_all = {h: _forward_target_labels(r_all, seg_all, h) for h in HORIZONS}

    # Accumulators keyed by (arm_index, horizon): pooled eval contributions/samples.
    pooled_contrib: dict = {}
    pooled_sample: dict = {}  # (y, svt, z) eval rows for permutation
    per_window_cmi: dict = {}
    per_window_delta: dict = {}
    per_window_redund: dict = {}
    n_eval_acc: dict = {}
    n_win_acc: dict = {}
    for ai in range(len(arms)):
        for h in HORIZONS:
            key = (ai, h)
            pooled_contrib[key] = []
            pooled_sample[key] = ([], [], [])
            per_window_cmi[key] = []
            per_window_delta[key] = []
            per_window_redund[key] = []
            n_eval_acc[key] = 0
            n_win_acc[key] = 0

    t0 = time.perf_counter()
    for w in windows:
        train_lo = int(np.searchsorted(ts_all, np.datetime64(_utc(w.train_start))))
        train_hi = int(np.searchsorted(ts_all, np.datetime64(_utc(w.origin))))
        eval_hi = int(np.searchsorted(ts_all, np.datetime64(_utc(w.eval_end))))
        fit_hi = train_hi - PURGE_BARS
        if fit_hi - train_lo < PURGE_BARS:
            raise RuntimeError(f"window {w.window_id}: training span too short")

        x_train = x_emit[train_lo:fit_hi]
        moments = fit_moments(x_train)
        z_train = standardize(x_train, moments)
        sel = politis_white_block_length(x_train[:, 0], bootstrap_type="stationary")
        embargo = int(np.ceil(sel.block_length))
        eval_lo = train_hi + embargo
        z_eval = standardize(x_emit[eval_lo:eval_hi], moments)

        # S_hmm: registered 4-state diag HMM, causal warm-started filter.
        model = GaussianHMM(n_states=HMM_N_STATES, covariance_type=HMM_COV)
        model.fit(z_train, seed=SEED, restart_seeds=RESTART_SEEDS)
        s_hmm_train = filtered_state_path(model.filter_states(z_train))
        prior = model.terminal_log_alpha(z_train)
        n_prop = int(eval_lo - fit_hi)
        s_hmm_eval = filtered_state_path(
            model.filter_states_from_prior(z_eval, prior, n_propagation_steps=n_prop)
        )

        # Shared covariates / targets on train (purged) and eval slices.
        svr_train = svr_all[train_lo:fit_hi]
        svr_eval = svr_all[eval_lo:eval_hi]

        # Precompute S_vt ONCE per arm per window (horizon-independent): the trend
        # and vol scalars depend only on (family, n), so compute the 20+20 distinct
        # scalars once (the expensive ema/kama loops) rather than per arm, fit the
        # 20 vol medians on the TRAIN slice, then combine into the 400 arm states.
        train_ohlc = OHLCArrays(
            ohlc.open[train_lo:fit_hi],
            ohlc.high[train_lo:fit_hi],
            ohlc.low[train_lo:fit_hi],
            ohlc.close[train_lo:fit_hi],
        )
        eval_ohlc = OHLCArrays(
            ohlc.open[eval_lo:eval_hi],
            ohlc.high[eval_lo:eval_hi],
            ohlc.low[eval_lo:eval_hi],
            ohlc.close[eval_lo:eval_hi],
        )
        trend_tr = {
            (tf, n): trend_scalar(train_ohlc, tf, n) for tf in TREND_FAMILIES for n in WINDOW_GRID
        }
        trend_ev = {
            (tf, n): trend_scalar(eval_ohlc, tf, n) for tf in TREND_FAMILIES for n in WINDOW_GRID
        }
        vol_tr = {
            (vf, n): vol_scalar(train_ohlc, vf, n) for vf in VOL_FAMILIES for n in WINDOW_GRID
        }
        vol_ev = {(vf, n): vol_scalar(eval_ohlc, vf, n) for vf in VOL_FAMILIES for n in WINDOW_GRID}
        vol_med = {
            k: float(np.median(v[np.isfinite(v)]))
            for k, v in vol_tr.items()
            if np.isfinite(v).any()
        }
        svt_tr_arm = [
            states_from_scalars(trend_tr[(tf, n_t)], vol_tr[(vf, n_v)], vol_med[(vf, n_v)])
            for (tf, vf, n_t, n_v) in arms
        ]
        svt_ev_arm = [
            states_from_scalars(trend_ev[(tf, n_t)], vol_ev[(vf, n_v)], vol_med[(vf, n_v)])
            for (tf, vf, n_t, n_v) in arms
        ]

        for h in HORIZONS:
            y_tr = y_all[h][train_lo:fit_hi]
            y_ev = y_all[h][eval_lo:eval_hi]
            z_tr = np.column_stack([s_hmm_train, svr_train])
            z_ev = np.column_stack([s_hmm_eval, svr_eval])
            # Analysis mask = valid forward target AND valid S_vr. S_vt (the
            # emitter) is not separately segment-masked, but its trailing lookback
            # is <= max(n_v,n_t) <= 8 bars, whereas the S_vr mask already drops the
            # first VR_WINDOW_BARS+q-2 (~289) bars after every segment break — which
            # strictly dominates the S_vt lookback, so any bar where S_vt could be
            # cross-break-contaminated is already excluded here (QUANT-1-4).
            base_tr_ok = (y_tr >= 0) & (svr_train >= 0)
            base_ev_ok = (y_ev >= 0) & (svr_eval >= 0)
            for ai in range(len(arms)):
                svt_tr = svt_tr_arm[ai]
                svt_ev = svt_ev_arm[ai]
                key = (ai, h)
                m_ev = base_ev_ok
                if m_ev.sum() < MIN_EVAL_BARS:
                    continue
                ye, xe, ze = y_ev[m_ev], svt_ev[m_ev], z_ev[m_ev]
                per_window_cmi[key].append(conditional_mutual_information(ye, xe, ze))
                pooled_contrib[key].append(cmi_pointwise_contributions(ye, xe, ze))
                pooled_sample[key][0].append(ye)
                pooled_sample[key][1].append(xe)
                pooled_sample[key][2].append(ze)
                per_window_redund[key].append(
                    (
                        partition_redundancy(xe, ze[:, 0]),
                        partition_redundancy(xe, ze[:, 1]),
                    )
                )
                n_eval_acc[key] += int(m_ev.sum())
                n_win_acc[key] += 1
                # Nested OOS delta — guard the estimator's documented precondition
                # (both target classes in train AND test) explicitly instead of
                # swallowing a broad ValueError that could mask an unrelated bug.
                m_tr = base_tr_ok
                y_tr_m, y_ev_m = y_tr[m_tr], y_ev[m_ev]
                both = {0, 1}
                if both.issubset(set(np.unique(y_tr_m))) and both.issubset(set(np.unique(y_ev_m))):
                    d = nested_predictive_delta(
                        y_tr_m,
                        z_tr[m_tr],
                        svt_tr[m_tr],
                        y_ev_m,
                        z_ev[m_ev],
                        svt_ev[m_ev],
                    )
                    per_window_delta[key].append((d.delta_logloss, d.delta_mcfadden))
        print(
            f"[{variant}/{symbol}] window {w.window_id} done ({time.perf_counter() - t0:.0f}s cum)",
            flush=True,
        )

    # ---- pool + candidate CIs/permutation ----
    rng = np.random.default_rng(SEED)
    # Pre-pass: the illustrative permutation runs only for the top-K arms by
    # binding MM-CMI (PERM_TOP_K per instrument).
    all_cmi = {}
    for ai in range(len(arms)):
        for h in HORIZONS:
            key = (ai, h)
            if n_win_acc[key] == 0:
                continue
            n_pw = np.array([c.size for c in pooled_contrib[key]], dtype=np.float64)
            mm_pw = np.array(per_window_cmi[key], dtype=np.float64)
            all_cmi[key] = float(np.sum(n_pw * mm_pw) / n_pw.sum())
    perm_keys = set(sorted(all_cmi, key=all_cmi.get, reverse=True)[:PERM_TOP_K])
    results: list[ArmResult] = []
    for ai, (tf, vf, n_t, n_v) in enumerate(arms):
        for h in HORIZONS:
            key = (ai, h)
            if n_win_acc[key] == 0:
                continue
            contribs = pooled_contrib[key]  # per-window plug-in pointwise arrays
            contrib = np.concatenate(contribs)
            n_per_win = np.array([c.size for c in contribs], dtype=np.float64)
            mm_per_win = np.array(per_window_cmi[key], dtype=np.float64)  # MM-corrected per window
            cmi_plugin = float(contrib.mean())  # n-weighted plug-in pooled CMI (biased)
            # Binding estimate: n-weighted average of PER-WINDOW Miller-Madow CMI.
            # Per-window keeps S_hmm labels comparable (label-switching makes them
            # non-comparable across windows) and inherits the MM bias correction that
            # the plug-in gate lacked (QUANT-1-1 / QUANT-1-3).
            cmi_point = float(np.sum(n_per_win * mm_per_win) / n_per_win.sum())
            cmi_correction = cmi_point - cmi_plugin  # deterministic MM bias shift
            cmi_mm_mean = float(mm_per_win.mean())  # unweighted per-window MM mean (reported)
            deltas = per_window_delta[key]
            mean_dll = float(np.mean([d[0] for d in deltas])) if deltas else float("nan")
            frac_pos = float(np.mean([d[0] > 0 for d in deltas])) if deltas else float("nan")
            mean_dmcf = float(np.mean([d[1] for d in deltas])) if deltas else float("nan")
            reds = per_window_redund[key]
            ari_h = float(np.mean([rr[0].adjusted_rand for rr in reds]))
            ari_v = float(np.mean([rr[1].adjusted_rand for rr in reds]))
            ami_h = float(np.mean([rr[0].adjusted_mutual_info for rr in reds]))
            ami_v = float(np.mean([rr[1].adjusted_mutual_info for rr in reds]))

            is_cand = cmi_point > 0.0  # MM-corrected gate
            ci_low = ci_high = float("nan")
            pval = float("nan")
            precision_ok = False
            h1 = False
            if is_cand:
                bl = politis_white_block_length(contrib, bootstrap_type="stationary").block_length
                ci = stationary_bootstrap_mean_ci(
                    contrib,
                    block_length=max(bl, 1.0),
                    rng=rng,
                    n_bootstrap=N_BOOTSTRAP,
                    alpha=ALPHA,
                )
                # Shift the plug-in bootstrap CI onto the MM-corrected scale by the
                # deterministic bias offset (the bootstrap gives the sampling width;
                # MM removes the location bias). Blocks may wrap disjoint eval spans
                # (QUANT-1-5) — a negligible edge effect at block≪window length.
                ci_low = ci.ci_low + cmi_correction
                ci_high = ci.ci_high + cmi_correction
                half = (ci_high - ci_low) / 2.0
                precision_ok = bool(cmi_point > 0 and half < PRECISION_HALF_WIDTH_FRAC * cmi_point)
                # Binding inference is the MM-corrected block-bootstrap CI above.
                # The permutation p-value is ILLUSTRATIVE ONLY: the within-Z-cell
                # shuffle assumes Y exchangeable within cells, violated by the
                # overlapping-window forward target (anti-conservative; QUANT-1-2),
                # and pools non-comparable across-window S_hmm labels (QUANT-1-3).
                # Run for the CI+delta-gated set only; not used in the H1 decision.
                if ci_low > 0.0 and mean_dll > 0.0:
                    h1 = True  # H1 = MM CI lower bound > 0 AND mean OOS delta > 0
                    if key in perm_keys:  # illustrative permutation for top-K only
                        ye = np.concatenate(pooled_sample[key][0])
                        xe = np.concatenate(pooled_sample[key][1])
                        ze = np.concatenate(pooled_sample[key][2])
                        pval = stratified_permutation_pvalue(
                            ye, xe, ze, rng=rng, n_permutations=N_PERMUTATIONS
                        )
            results.append(
                ArmResult(
                    instrument=symbol,
                    horizon=h,
                    trend_family=tf,
                    vol_family=vf,
                    n_t=n_t,
                    n_v=n_v,
                    n_windows=n_win_acc[key],
                    n_eval_bars=n_eval_acc[key],
                    cmi_point=cmi_point,
                    cmi_plugin=cmi_plugin,
                    cmi_mm_mean=cmi_mm_mean,
                    cmi_ci_low=ci_low,
                    cmi_ci_high=ci_high,
                    perm_pvalue=pval,
                    mean_delta_logloss=mean_dll,
                    frac_windows_delta_pos=frac_pos,
                    mean_delta_mcfadden=mean_dmcf,
                    ari_vs_hmm=ari_h,
                    ari_vs_vr=ari_v,
                    ami_vs_hmm=ami_h,
                    ami_vs_vr=ami_v,
                    is_candidate=is_cand,
                    h1_met=h1,
                    precision_ok=precision_ok,
                )
            )
    return results


def main() -> int:  # noqa: PLR0915 — linear ReproLog→scan→verdict→provenance driver
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/H001")
    parser.add_argument("--instruments", default="ES,NQ")
    parser.add_argument("--variant", default="primary", choices=["primary", "inclusive"])
    parser.add_argument("--max-windows", type=int, default=None)
    parser.add_argument("--max-arms", type=int, default=None, help="DEV: cap the arm grid")
    args = parser.parse_args()

    paths = ProjectPaths.discover()
    out_dir = paths.root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    instruments = tuple(s.strip() for s in args.instruments.split(","))

    arms = [
        (tf, vf, n_t, n_v)
        for tf, vf, n_t, n_v in itertools.product(
            TREND_FAMILIES, VOL_FAMILIES, WINDOW_GRID, WINDOW_GRID
        )
    ]
    if args.max_arms is not None:
        arms = arms[: args.max_arms]
    print(
        f"H001 scan: {len(arms)} arms × {len(HORIZONS)} horizons × {len(instruments)} instruments",
        flush=True,
    )

    # ReproLog first (ADR-0008).
    design_path = paths.root / "research/01_hypothesis_register/H001/design.md"
    design_sha = hashlib.sha256(design_path.read_bytes()).hexdigest()
    log = reproducibility.capture(
        phase="h001-covariate-information-production",
        hypothesis_id="H001",
        rng_seed=SEED,
        dataset_checksums=_dataset_checksums(paths),
        config_resolved_sha256=design_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (design SHA {design_sha[:12]}...)", flush=True)

    all_rows: list[ArmResult] = []
    for symbol in instruments:
        all_rows.extend(
            run_instrument(
                paths=paths,
                symbol=symbol,
                variant=args.variant,
                arms=arms,
                max_windows=args.max_windows,
            )
        )

    df = pl.DataFrame([r.__dict__ for r in all_rows])
    scan_path = out_dir / f"h001_scan_{args.variant}.parquet"
    df.write_parquet(scan_path)
    df.write_csv(out_dir / f"h001_scan_{args.variant}.csv")

    # §10 verdict.
    h1_rows = df.filter(pl.col("h1_met"))
    verdict = "GO" if h1_rows.height > 0 else "NO-GO"
    top = df.filter(pl.col("is_candidate")).sort("cmi_point", descending=True).head(20).to_dicts()
    blob = {
        "hypothesis_id": "H001",
        "variant": args.variant,
        "verdict": verdict,
        "decision_rule": (
            "GO iff >=1 arm has pooled CMI 95% CI lower bound > 0 AND mean nested "
            "OOS delta_logloss > 0 on >=1 instrument/horizon (design §10). Screening/"
            "FWER level DEFERRED (screening_error_rate_target null) -> descriptive; "
            "no arm CERTIFIED as a discovery."
        ),
        "n_arms": len(arms),
        "horizons": list(HORIZONS),
        "instruments": list(instruments),
        "n_h1_arms": h1_rows.height,
        "n_candidate_arms": int(df.filter(pl.col("is_candidate")).height),
        "seed": SEED,
        "alpha": ALPHA,
        "top20_by_cmi_point": top,
    }
    (out_dir / f"h001_verdict_{args.variant}.json").write_text(
        json.dumps(blob, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )

    # model_hash over the TEXT artifacts (csv + json) only — parquet byte
    # encoding varies with the polars/pyarrow version, so hashing it would make
    # the provenance digest non-cross-platform-stable (REPRODUCIBILITY-1-3). The
    # csv carries the same scan values.
    hasher = hashlib.sha256()
    for ext in ("csv", "json"):
        for f in sorted(out_dir.glob(f"h001_*_{args.variant}.{ext}")):
            hasher.update(f.name.encode())
            hasher.update(f.read_bytes())
    reproducibility.with_model_hash(log, hasher.hexdigest()).write(log_path)
    print(
        f"[{args.variant}] VERDICT: {verdict} ({h1_rows.height} H1 arms, "
        f"{blob['n_candidate_arms']} candidates). ReproLog {log_path.name}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
