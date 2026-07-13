"""Unit tests for the Kelly geometric-growth reference estimator (kelly_growth.py).

These tests ARE the reproducible demonstration of the frozen estimator's
properties (referenced by the method-freeze memo
``docs/methodology/kelly_growth_concavity_ruin_2026-07-12.md`` in lieu of
embedded ad-hoc numbers). Coverage maps to the derivation sections:

- (a) D1 interior-maximum benchmark: even-money Kelly coin recovers the
  closed-form full-Kelly stake ``f* = 2p - 1`` (Kelly 1956; Breiman 1961).
- (b) D3/D5 ``-inf`` propagation under the absorbing barrier.
- (c) D5 cap-vs-absorbing monotone divergence (capping biases g up at leverage).
- (d) D1 concavity + single interior peak on a real fat-tailed ES 1-min slice.
- (e) D3 ruin-barrier closed form ``f_max = -1/(b* min R)``.

Plus: analytic g'/g'' identity, D4 zero-growth crossing vs the 2x-Kelly
thin-tailed benchmark (Thorp 2006), the Busseti-Ryu-Boyd full-Kelly risk
exponent (== 1), and the D2 rolling-origin plumbing.

All randomness uses a fixed seed.
"""

from __future__ import annotations

import pathlib

import numpy as np
import pandas as pd
import pytest

from skie_universe2.inference import kelly_growth as kg

# Fixed seed for every stochastic path in this module (reproducibility).
SEED = 20260712

ES_PARQUET = (
    "data/processed/vendor_legacy_1min_roll_adjusted/" "symbol=ES/year=2015/part-0000.parquet"
)
# Deterministic favourable slice (positive-drift window with fat 1-min tails).
ES_SLICE = slice(0, 50000)

# The ES parquet lives in the gitignored machine-level data store; a fresh CI
# clone (see .github/workflows/ci.yml) has no data-provisioning step, so the
# three real-fat-tail demonstrations skip gracefully where it is absent. Each
# ES-gated demonstration has a data-independent synthetic twin (D1 via the
# even-money coin and finite-difference derivative checks; D2 via
# test_rolling_origin_synthetic_happy_path_selects_grid_member; D3 via the
# closed-form f_max and absorbing-barrier tests), so D1/D2/D3 success paths are
# reproduced on a portable substrate and the fresh-clone contract stays green.
requires_es_data = pytest.mark.skipif(
    not pathlib.Path(ES_PARQUET).exists(),
    reason="machine-level data store absent (gitignored ES parquet)",
)


# ---------------------------------------------------------------------------
# (a) D1 interior-maximum benchmark — even-money Kelly coin
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("p", [0.51, 0.55, 0.60, 0.75, 0.90])
def test_full_kelly_coin_closed_form(p: float) -> None:
    """Even-money bet: full-Kelly stake f* = 2p - 1 (Kelly 1956)."""
    returns = np.array([1.0, -1.0])
    weights = np.array([p, 1.0 - p])
    b_star = kg.full_kelly_leverage(returns, weights=weights)
    assert b_star == pytest.approx(2.0 * p - 1.0, abs=1e-8)


def test_unfavourable_bet_returns_zero_leverage() -> None:
    """E[R] <= 0 has no positive growth-optimal leverage."""
    returns = np.array([1.0, -1.0])
    weights = np.array([0.4, 0.6])
    assert kg.full_kelly_leverage(returns, weights=weights) == 0.0


def test_growth_curve_peaks_at_full_kelly() -> None:
    """g(f) on the coin measure peaks at f = 1 (g'(1) ~ 0, g''(1) < 0)."""
    p = 0.6
    returns = np.array([1.0, -1.0])
    weights = np.array([p, 1.0 - p])
    b_star = kg.full_kelly_leverage(returns, weights=weights)
    assert kg.growth_derivative(returns, b_star, 1.0, weights=weights) == pytest.approx(
        0.0, abs=1e-8
    )
    assert kg.growth_second_derivative(returns, b_star, 1.0, weights=weights) < 0.0


# ---------------------------------------------------------------------------
# (b) D3/D5 -inf propagation under the absorbing barrier
# ---------------------------------------------------------------------------


def test_absorbing_barrier_inf_propagation() -> None:
    """A bar with 1 + leverage*R <= 0 makes absorbing mean-log-growth -inf."""
    b_star = 1.0
    leverage = 1.0
    # -1/(leverage*b_star) = -1; a return at/below -1 breaches the barrier.
    returns = np.array([0.2, -1.0, 0.3])  # 1 + 1*(-1) = 0 -> ruin
    assert kg.growth_rate(returns, leverage * b_star, barrier="absorbing") == -np.inf
    returns_below = np.array([0.2, -1.5, 0.3])  # multiplier strictly negative
    assert kg.growth_rate(returns_below, leverage * b_star, barrier="absorbing") == -np.inf


def test_absorbing_finite_below_barrier() -> None:
    """Below the barrier the absorbing estimator is finite."""
    returns = np.array([0.2, -0.9, 0.3, 0.1])
    val = kg.growth_rate(returns, 1.0, barrier="absorbing")
    assert np.isfinite(val)


def test_capping_finite_where_absorbing_infinite() -> None:
    """Capping replaces -inf with a finite (upward-biased) value — sensitivity."""
    returns = np.array([0.2, -1.5, 0.3])
    cap = kg.growth_rate(returns, 1.0, barrier="cap", cap_floor=1e-4)
    assert np.isfinite(cap)
    assert kg.growth_rate(returns, 1.0, barrier="absorbing") == -np.inf


# ---------------------------------------------------------------------------
# (c) D5 cap-vs-absorbing monotone divergence
# ---------------------------------------------------------------------------


def test_cap_minus_absorbing_gap_monotone_in_f() -> None:
    """(cap - absorbing) growth gap is non-decreasing in f (capping bias).

    Below the ruin barrier both estimators are finite; capping floors the
    small-but-positive worst-bar multiplier, so the upward bias grows with
    leverage and never shrinks.
    """
    returns = np.array([-0.9, -0.3, 0.1, 0.2, 0.5, 0.4, -0.2, 0.6])
    b_star = 1.0
    f_max = kg.effective_domain_fmax(returns, b_star)
    # Fine grid strictly inside the effective domain so absorbing stays finite.
    fractions = np.linspace(0.1, f_max * 0.98, 30)
    cap_floor = 0.4  # moderate floor so capping bites on near-barrier bars
    gap = np.array(
        [
            kg.growth_rate(returns, f * b_star, barrier="cap", cap_floor=cap_floor)
            - kg.growth_rate(returns, f * b_star, barrier="absorbing")
            for f in fractions
        ]
    )
    assert np.all(np.isfinite(gap))
    assert np.all(np.diff(gap) >= -1e-12)
    assert gap[0] == pytest.approx(0.0, abs=1e-12)  # no capping at low leverage
    assert gap[-1] > 0.0  # strict upward bias near the barrier


# ---------------------------------------------------------------------------
# (d) D1 concavity + single interior peak on a real fat-tailed ES slice
# ---------------------------------------------------------------------------


def _es_log_returns() -> np.ndarray:
    df = pd.read_parquet(ES_PARQUET)
    close = df["close"].to_numpy(dtype=np.float64)
    return np.diff(np.log(close))[ES_SLICE]


@requires_es_data
def test_es_slice_is_fat_tailed() -> None:
    """Sanity: the substrate is fat-tailed (excess kurtosis >> 0)."""
    r = _es_log_returns()
    z = (r - r.mean()) / r.std()
    excess_kurtosis = float(np.mean(z**4) - 3.0)
    assert excess_kurtosis > 3.0  # heavy tails vs the Gaussian (=0)


@requires_es_data
def test_es_growth_curve_concave_single_peak() -> None:
    """On real ES 1-min returns g is strictly concave with a unique interior peak."""
    r = _es_log_returns()
    b_star = kg.full_kelly_leverage(r)
    assert b_star > 0.0
    f_max = kg.effective_domain_fmax(r, b_star)
    assert np.isfinite(f_max) and f_max > 1.0

    grid = np.linspace(0.05, 1.5, 40)
    g2 = np.array([kg.growth_second_derivative(r, b_star, f) for f in grid])
    assert np.all(g2 < 0.0)  # strict concavity everywhere on the domain

    g = kg.growth_curve(r, b_star, grid)
    peak_f = grid[int(np.argmax(g))]
    assert peak_f == pytest.approx(1.0, abs=0.1)  # interior max at full Kelly
    # Unimodal: g' > 0 below the peak, g' < 0 above it.
    assert kg.growth_derivative(r, b_star, 0.5) > 0.0
    assert kg.growth_derivative(r, b_star, 1.2) < 0.0


# ---------------------------------------------------------------------------
# (e) D3 ruin-barrier closed form
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("returns", "b_star"),
    [
        (np.array([-0.9, -0.3, 0.1, 0.5]), 1.0),
        (np.array([-0.4, 0.2, 0.6]), 2.5),
        (np.array([-0.05, 0.01, 0.03, -0.02]), 5.0),
    ],
)
def test_effective_domain_fmax_closed_form(returns: np.ndarray, b_star: float) -> None:
    """f_max = -1 / (b* * min_i R_i)."""
    f_max = kg.effective_domain_fmax(returns, b_star)
    expected = -1.0 / (b_star * returns.min())
    assert f_max == pytest.approx(expected, rel=1e-12)


def test_fmax_infinite_without_losing_bar() -> None:
    """No adverse bet -> no single-bar ruin -> barrier at +inf."""
    returns = np.array([0.1, 0.2, 0.3])
    assert kg.effective_domain_fmax(returns, 1.0) == np.inf


# ---------------------------------------------------------------------------
# Analytic derivative identity (finite-difference cross-check)
# ---------------------------------------------------------------------------


def test_analytic_first_derivative_matches_finite_difference() -> None:
    """g'(f) closed form agrees with a central finite difference."""
    rng = np.random.default_rng(SEED)
    returns = rng.normal(0.002, 0.03, 500)
    b_star = kg.full_kelly_leverage(returns)
    f0 = 0.7
    eps = 1e-6
    fd = (
        kg.growth_rate(returns, (f0 + eps) * b_star) - kg.growth_rate(returns, (f0 - eps) * b_star)
    ) / (2.0 * eps)
    analytic = kg.growth_derivative(returns, b_star, f0)
    assert analytic == pytest.approx(fd, rel=1e-4)


def test_second_derivative_matches_finite_difference() -> None:
    """g''(f) closed form agrees with a finite difference of g'."""
    rng = np.random.default_rng(SEED + 1)
    returns = rng.normal(0.002, 0.03, 500)
    b_star = kg.full_kelly_leverage(returns)
    f0 = 0.7
    eps = 1e-5
    fd = (
        kg.growth_derivative(returns, b_star, f0 + eps)
        - kg.growth_derivative(returns, b_star, f0 - eps)
    ) / (2.0 * eps)
    analytic = kg.growth_second_derivative(returns, b_star, f0)
    assert analytic == pytest.approx(fd, rel=1e-3)


# ---------------------------------------------------------------------------
# D4 — over-betting zero-growth crossing vs the thin-tailed 2x benchmark
# ---------------------------------------------------------------------------


def test_zero_growth_crossing_thin_tailed_two_times_kelly() -> None:
    """Thin-tailed (small-bet Gaussian) benchmark: f_0 ~ 2 (Thorp 2006)."""
    rng = np.random.default_rng(SEED + 2)
    returns = rng.normal(0.001, 0.02, 40000)  # small bets -> diffusion limit
    b_star = kg.full_kelly_leverage(returns)
    f_zero = kg.zero_growth_fraction(returns, b_star)
    assert f_zero == pytest.approx(2.0, abs=0.05)


def test_zero_growth_crossing_above_full_kelly() -> None:
    """f_0 lies strictly above full Kelly (over-betting region)."""
    returns = np.array([-0.9, -0.2, 0.1, 0.3, 0.5, 0.4, -0.3, 0.6])
    b_star = kg.full_kelly_leverage(returns)
    f_zero = kg.zero_growth_fraction(returns, b_star)
    f_max = kg.effective_domain_fmax(returns, b_star)
    assert 1.0 < f_zero < f_max


def test_zero_growth_crossing_pinned_to_barrier_near_full_kelly() -> None:
    """Near-barrier fat-tailed regime: f_0 pins to f_max, not a silent nan (F-1-1).

    Construction (per the D4 regime the memo freezes it for): one large-loss
    atom carrying tiny weight ``1/n`` plus many small favourable atoms, so the
    ruin barrier ``f_max`` sits just above full Kelly. There ``g`` stays
    finite-and-positive across the entire search interval ``(1, f_max*(1-1e-9)]``
    and only dives to ``-inf`` within float-epsilon of ``f_max``; the zero
    crossing is therefore pinned to the barrier. The estimator must return
    ``f_0 = f_max`` (to machine precision), the verdict D4 exists to deliver
    (grid-top over-betting into the ruin barrier), not nan. Thorp 2006.
    """
    returns = np.array([-0.7] + [0.01] * 3000)
    b_star = kg.full_kelly_leverage(returns)
    f_max = kg.effective_domain_fmax(returns, b_star)
    assert np.isfinite(f_max) and 1.0 < f_max < 1.25  # barrier just above Kelly
    # Whole interior interval is finite-and-positive: the pathological bracket.
    hi = f_max * (1.0 - 1e-9)
    g_hi = kg.growth_rate(returns, hi * b_star, barrier="absorbing")
    assert np.isfinite(g_hi) and g_hi > 0.0
    f_zero = kg.zero_growth_fraction(returns, b_star)
    assert np.isfinite(f_zero)
    assert f_zero == pytest.approx(f_max, rel=1e-12)
    # Safety-critical verdict: the grid top over-bets past zero-growth.
    assert f_zero < 1.25


# ---------------------------------------------------------------------------
# D5 — Busseti-Ryu-Boyd drawdown bound
# ---------------------------------------------------------------------------


def test_full_kelly_drawdown_exponent_is_one() -> None:
    """At full Kelly the BRB risk exponent is exactly 1 (E[W^{-1}] = 1).

    Consequence: P(wealth ever halves) <= 0.5 at full Kelly (Kelly's own
    self-financing property; Busseti, Ryu & Boyd 2016).
    """
    p = 0.6
    returns = np.array([1.0, -1.0])
    weights = np.array([p, 1.0 - p])
    b_star = kg.full_kelly_leverage(returns, weights=weights)
    bound = kg.drawdown_probability_bound(returns, b_star, 0.5, weights=weights)
    assert bound.valid
    assert bound.exponent == pytest.approx(1.0, abs=1e-6)
    assert bound.prob_bound == pytest.approx(0.5, abs=1e-6)


def test_fractional_kelly_has_larger_drawdown_exponent() -> None:
    """Under-betting (half Kelly) raises the risk exponent -> smaller bound."""
    p = 0.6
    returns = np.array([1.0, -1.0])
    weights = np.array([p, 1.0 - p])
    b_star = kg.full_kelly_leverage(returns, weights=weights)
    half = kg.drawdown_probability_bound(returns, 0.5 * b_star, 0.5, weights=weights)
    full = kg.drawdown_probability_bound(returns, b_star, 0.5, weights=weights)
    assert half.exponent > full.exponent
    assert half.prob_bound < full.prob_bound


# ---------------------------------------------------------------------------
# D3/D5 — bootstrap single-bar ruin probability
# ---------------------------------------------------------------------------


def test_bootstrap_single_bar_ruin_point_and_ci() -> None:
    """Point estimate equals the empirical breach fraction; CI brackets it."""
    # leverage chosen so exactly the -0.9 bar breaches at leverage > 1/0.9.
    returns = np.array([-0.9, -0.2, 0.1, 0.3, 0.5, -0.4, 0.2, 0.6])
    leverage = 1.2  # 1 + 1.2*(-0.9) = -0.08 < 0 -> that bar ruins
    rng = np.random.default_rng(SEED + 3)
    point, lo, hi, selection = kg.bootstrap_single_bar_ruin(
        returns, leverage, rng=rng, n_bootstrap=500
    )
    assert point == pytest.approx(1.0 / len(returns), abs=1e-12)
    assert 0.0 <= lo <= point <= hi <= 1.0
    assert selection.block_length >= 1.0


def test_single_bar_ruin_zero_below_barrier() -> None:
    returns = np.array([-0.9, -0.2, 0.1, 0.3])
    # leverage below barrier -1/(min R) = 1/0.9 ~ 1.111
    assert kg.single_bar_ruin_probability(returns, 1.0) == 0.0


# ---------------------------------------------------------------------------
# D2 — nested rolling-origin plumbing
# ---------------------------------------------------------------------------


@requires_es_data
def test_rolling_origin_runs_and_selects_grid_member() -> None:
    """D2 machinery runs, respects purge/embargo, returns a grid member as f**."""
    r = _es_log_returns()
    result = kg.nested_rolling_origin_growth(r, n_splits=5, purge=0)
    assert result.n_folds >= 1
    assert result.oos_growth.shape == (len(kg.KELLY_FRACTION_GRID),)
    assert result.f_star_oos in kg.KELLY_FRACTION_GRID
    assert result.b_star_folds.size == result.n_folds


def test_rolling_origin_synthetic_happy_path_selects_grid_member() -> None:
    """D2 success path on a seeded synthetic substrate (fresh-clone portable).

    The ES-gated ``test_rolling_origin_runs_and_selects_grid_member`` demonstrates
    the same contract on a real fat-tailed slice but skips wherever the gitignored
    parquet is absent (any fresh clone / CI). This data-independent twin exercises
    the OOS-growth computation and grid-member selection to completion so the D2
    estimator is reproduced on a portable substrate, and audits that each fold's
    training span ends strictly before its test window begins (purge + embargo
    gap honoured), the leakage guard the estimator exists to enforce.
    """
    rng = np.random.default_rng(SEED + 5)
    # Favourable low-vol series: interior full-Kelly bet exists, bets stay well
    # above the ruin barrier so OOS growth is finite (grid member selectable).
    returns = rng.normal(0.002, 0.02, 6000)
    purge = 5
    n_splits = kg.DEFAULT_N_SPLITS
    result = kg.nested_rolling_origin_growth(returns, n_splits=n_splits, purge=purge)

    assert result.n_folds >= 1
    assert result.oos_growth.shape == (len(kg.KELLY_FRACTION_GRID),)
    assert result.f_star_oos in kg.KELLY_FRACTION_GRID
    assert result.b_star_folds.size == result.n_folds

    # Train/test index audit: reconstruct the fold geometry with the estimator's
    # own integer arithmetic and assert the purge+embargo gap is honoured, i.e.
    # every train span ends strictly before its test window starts.
    n = returns.size
    embargo = int(np.floor(kg.DEFAULT_EMBARGO_FRACTION * n))
    min_train = int(np.floor(kg.DEFAULT_MIN_TRAIN_FRACTION * n))
    test_size = (n - min_train) // n_splits
    audited = 0
    for k in range(n_splits):
        test_start = min_train + k * test_size
        test_end = n if k == n_splits - 1 else test_start + test_size
        train_end = test_start - purge - embargo
        if train_end < 2 or test_end <= test_start:
            continue
        assert train_end < test_start  # purge + embargo gap present
        assert test_start - train_end == purge + embargo  # exact gap width
        audited += 1
    assert audited == result.n_folds


def test_rolling_origin_rejects_infeasible_split() -> None:
    """Too few test bars for the requested splits raises rather than fabricates."""
    returns = np.linspace(-0.01, 0.02, 20)
    with pytest.raises(ValueError):
        kg.nested_rolling_origin_growth(returns, n_splits=50, min_train_fraction=0.9)


# ---------------------------------------------------------------------------
# Fat-tail validity — finite log-moment, not finite variance
# ---------------------------------------------------------------------------


def test_growth_finite_under_infinite_variance_returns() -> None:
    """Heavy-tailed (infinite-variance) returns still yield finite growth.

    A Student-t with 1.5 dof has infinite variance but the log-growth is finite
    as long as the bet stays below the ruin barrier (Algoet & Cover 1988: the
    binding condition is a finite log-moment, not finite variance).
    """
    rng = np.random.default_rng(SEED + 4)
    # dof = 1.5 -> infinite variance; scale small and center positive so a
    # favourable, below-barrier bet exists.
    raw = rng.standard_t(1.5, size=20000)
    returns = 0.002 + 0.01 * raw
    returns = returns[returns > -0.99]  # keep strictly above total-loss
    b_star = kg.full_kelly_leverage(returns)
    if b_star == 0.0:
        pytest.skip("draw produced a non-favourable sample")
    # A modest sub-barrier leverage yields finite growth despite infinite var.
    f_max = kg.effective_domain_fmax(returns, b_star)
    lev = 0.25 * min(1.0, f_max) * b_star
    assert np.isfinite(kg.growth_rate(returns, lev, barrier="absorbing"))
