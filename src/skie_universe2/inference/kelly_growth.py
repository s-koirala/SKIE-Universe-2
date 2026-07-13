"""Kelly geometric-growth curve, concavity, ruin barrier and ruin-consistent
estimator (method freeze for `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`).

Status (BLOCKING per ADR-0013 Decision 9)
-----------------------------------------

This module is the *frozen reference estimator* that gates any empirical
selection of a swept Kelly fraction on geometric (compounded / log-wealth)
growth. The METHOD is frozen here on a representative fat-tailed substrate;
the NUMERIC on-ledger instantiation (the actual full-Kelly bet ``b*``, the
grid-point growth curve, ``f**``, ``P(ruin)`` and the over-betting crossing
``f_0`` on the ADR-0003 shadow ledger) is DEFERRED to the post-step-4 ledger
backfill because the shadow ledger is not yet populated. No Kelly fraction is
selected by this module.

Estimand
--------

Let ``f`` be the swept Kelly *fraction* over the registered grid
``{0.5, 0.75, 1.0, 1.25}`` (ADR-0013 Decision 3; 1.0 = full Kelly, 1.25 =
over-betting, 0.5 = under-betting), ``b*`` the growth-optimal (full-Kelly)
bet — the leverage that maximises the log-growth on the empirical measure —
and ``R`` the per-bar fat-tailed return. The geometric growth of fraction
``f`` is

    g(f) = E[ log(1 + f * b* * R) ]                                    (D1)

computed on the empirical (discrete) measure ``{(R_i, w_i)}`` with weights
``w_i`` summing to one (uniform ``w_i = 1/n`` by default).

Derivation summary (see the companion memo
``docs/methodology/kelly_growth_concavity_ruin_2026-07-12.md``)
--------------------------------------------------------------

- **D1 concavity / unique interior max.** With ``m_i = b* * R_i``,

      g'(f)  = sum_i w_i * m_i / (1 + f * m_i)
      g''(f) = -sum_i w_i * m_i^2 / (1 + f * m_i)^2  <  0

  on the effective domain ``f in [0, f_max)``, so ``g`` is strictly concave
  wherever a losing bar exists (some ``m_i != 0``); ``g'(0) = b* * E[R] > 0``
  for a favourable bet, giving a unique interior argmax. Because ``b*`` is the
  growth-optimal leverage on the same measure, that argmax is exactly the
  full-Kelly fraction ``f = 1``. The binding regularity condition under fat
  tails is a finite LOG-moment ``E|log(1 + f b* R)| < inf`` (Algoet & Cover
  1988), NOT finite variance — heavy tails in ``R`` are admissible.
- **D2 estimation-error-adjusted optimum.** :func:`nested_rolling_origin_growth`
  estimates ``b*`` on purged/embargoed training folds (plug-in) and *evaluates*
  ``g`` out-of-sample, yielding an OOS-optimal fraction ``f** <= 1``
  (Chopra & Ziemba 1993 ~11:1 mean-error dominance explains plug-in
  over-betting; Rujeerapaiboon, Kuhn & Wiesemann 2016 conservatism direction).
  Whether the 0.5 grid floor brackets ``f**`` from below is an OUTPUT of the
  ledger run, not asserted here.
- **D3 single-period ruin barrier.** ``f_max = -1 / (b* * min_i R_i)`` (when a
  losing bar exists); at ``f >= f_max`` some ``1 + f b* R_i <= 0`` so
  ``g(f) = -inf`` (the ``-inf`` convention; capping is rejected).
- **D4 over-betting zero-growth crossing.** :func:`zero_growth_fraction` solves
  ``g(f_0) = 0`` for ``f_0 > 1``; the thin-tailed benchmark is ``f_0 = 2``
  (twice Kelly, Thorp 2006), and fat tails push ``f_0`` below 2. Whether 1.25
  sits inside the positive-growth region (``1.25 < f_0``) is a ledger OUTPUT.
- **D5 ruin-consistent estimator.** The frozen primary estimator is the
  ABSORBING barrier (``1 + f b* R <= 0 -> -inf``; a bootstrap path that hits it
  is dead) plus a first-class ``P(ruin)``, the Busseti, Ryu & Boyd 2016
  drawdown bound, and stationary-bootstrap CIs (reusing
  :mod:`skie_universe2.inference.bootstrap`). CAPPING (flooring the wealth
  multiplier) is kept ONLY as a sensitivity and is explicitly labelled: it
  biases ``g``-hat UPWARD at the leveraged grid points, manufacturing
  survivable over-betting. The cap-vs-absorbing gap widening monotonically in
  ``f`` is guarded by a unit test.

Zero-magic-number register
--------------------------

Every tunable is a named module constant or a documented function default with
a cited/derived rationale; see the memo appendix. Constants:

- ``KELLY_FRACTION_GRID`` — ADR-0013 Decision 3 registered sweep.
- ``DEFAULT_N_BOOTSTRAP`` — H900 §8 / SKIE-Universe 1.0 H052a replication
  convention for the stationary bootstrap (Politis & Romano 1994).
- ``DEFAULT_CI_ALPHA`` — two-sided nominal 95% coverage (reporting convention).
- ``DEFAULT_EMBARGO_FRACTION`` / ``DEFAULT_MIN_TRAIN_FRACTION`` /
  ``DEFAULT_N_SPLITS`` — walk-forward evaluation-design choices (purged/embargoed
  rolling origin, Lopez de Prado 2018 ch. 7); registered per-ledger, not tuned
  to the objective. The numeric instantiation is deferred with the ledger.
- ``DEFAULT_CAP_FLOOR`` — the retained-wealth fraction at a ruinous bar for the
  CAPPING SENSITIVITY only. It is *deliberately arbitrary*: capping has no
  canonical floor, and that arbitrariness is the methodological reason capping
  is rejected as the primary estimator.

References
----------

- Kelly, J. L. Jr. 1956. "A New Interpretation of Information Rate". *Bell
  System Technical Journal* 35(4): 917-926.
  https://doi.org/10.1002/j.1538-7305.1956.tb03809.x
- Breiman, L. 1961. "Optimal Gambling Systems for Favorable Games". *Proc.
  Fourth Berkeley Symposium on Math. Statistics and Probability*, Vol. 1,
  pp. 65-78. University of California Press.
- Algoet, P. H. & Cover, T. M. 1988. "Asymptotic Optimality and Asymptotic
  Equipartition Properties of Log-Optimum Investment". *Annals of Probability*
  16(2): 876-898. https://doi.org/10.1214/aop/1176991793
- Thorp, E. O. 2006. "The Kelly Criterion in Blackjack, Sports Betting, and the
  Stock Market". In *Handbook of Asset and Liability Management*, Vol. 1,
  ch. 9, pp. 385-428. Elsevier. https://doi.org/10.1016/S1872-0978(06)01009-X
- Chopra, V. K. & Ziemba, W. T. 1993. "The Effect of Errors in Means,
  Variances, and Covariances on Optimal Portfolio Choice". *Journal of
  Portfolio Management* 19(2): 6-11. https://doi.org/10.3905/jpm.1993.409440
- Rujeerapaiboon, N.; Kuhn, D. & Wiesemann, W. 2016. "Robust Growth-Optimal
  Portfolios". *Management Science* 62(7): 2090-2109.
  https://doi.org/10.1287/mnsc.2015.2228
- Busseti, E.; Ryu, E. K. & Boyd, S. 2016. "Risk-Constrained Kelly Gambling".
  *Journal of Investing* 25(3): 118-134. https://doi.org/10.3905/joi.2016.25.3.118
- Politis, D. N. & Romano, J. P. 1994. "The Stationary Bootstrap". *JASA*
  89(428): 1303-1313. https://doi.org/10.1080/01621459.1994.10476870
- Lopez de Prado, M. 2018. *Advances in Financial Machine Learning*, ch. 7
  (purged / embargoed cross-validation). Wiley.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy.optimize import brentq, minimize_scalar

from skie_universe2.inference.bootstrap import (
    BlockLengthSelection,
    choose_block_length,
    stationary_bootstrap_indices,
)

__all__ = [
    "DEFAULT_CAP_FLOOR",
    "DEFAULT_CI_ALPHA",
    "DEFAULT_EMBARGO_FRACTION",
    "DEFAULT_MIN_TRAIN_FRACTION",
    "DEFAULT_N_BOOTSTRAP",
    "DEFAULT_N_SPLITS",
    "KELLY_FRACTION_GRID",
    "DrawdownBound",
    "GridPointRuin",
    "KellyGrowthReport",
    "RollingOriginGrowth",
    "drawdown_probability_bound",
    "effective_domain_fmax",
    "full_kelly_leverage",
    "growth_curve",
    "growth_derivative",
    "growth_rate",
    "growth_second_derivative",
    "nested_rolling_origin_growth",
    "single_bar_ruin_probability",
    "bootstrap_single_bar_ruin",
    "zero_growth_fraction",
]


# ---------------------------------------------------------------------------
# Registered defaults (each cited; see module docstring "Zero-magic-number
# register" and the companion memo appendix).
# ---------------------------------------------------------------------------

# ADR-0013 Decision 3 registered Kelly-fraction sweep.
KELLY_FRACTION_GRID: tuple[float, ...] = (0.5, 0.75, 1.0, 1.25)

# Stationary-bootstrap replications — H900 §8 / SKIE-Universe 1.0 H052a
# replication convention (Politis & Romano 1994). # bootstrap: H900 convention
DEFAULT_N_BOOTSTRAP: int = 2000

# Two-sided nominal 95% coverage (reporting convention). # ref: standard 95% CI
DEFAULT_CI_ALPHA: float = 0.05

# Embargo as a fraction of the sample (Lopez de Prado 2018 §7.4 ~1%). # ref: LdP-2018
DEFAULT_EMBARGO_FRACTION: float = 0.01

# Walk-forward warm-up: initial training span as a fraction of the sample. This
# is an evaluation-design choice registered per-ledger, not tuned to growth.
DEFAULT_MIN_TRAIN_FRACTION: float = 0.5

# Walk-forward folds (evaluation design; registered per-ledger, not tuned).
DEFAULT_N_SPLITS: int = 5

# CAPPING SENSITIVITY ONLY. Retained-wealth fraction imposed at a ruinous bar
# so the log is finite instead of -inf. Deliberately arbitrary: capping has no
# canonical floor, which is precisely why it is rejected as the primary
# estimator (it biases g upward at leverage). Never used by the absorbing path.
DEFAULT_CAP_FLOOR: float = 1.0e-4

_EPS: float = float(np.finfo(np.float64).eps)

# Upper-bracket doubling cap for monotone root searches. 64 doublings spans the
# full float64 exponent range, so it never constrains a finite root; it only
# bounds a pathological non-terminating search.
_MAX_BRACKET_DOUBLINGS: int = 64

# Fraction of the ruin barrier used as the closed search bracket so the solver
# stays strictly inside the effective domain where g / g' are finite.
_BARRIER_BRACKET_SHRINK: float = 1.0 - 1.0e-9

# Minimum bars needed to fit a full-Kelly bet / form a usable training fold
# (a degenerate 1-bar sample admits no interior optimum).
_MIN_FIT_BARS: int = 2


# ---------------------------------------------------------------------------
# Input hygiene
# ---------------------------------------------------------------------------


def _clean_returns(returns: npt.ArrayLike) -> np.ndarray:
    r = np.asarray(returns, dtype=np.float64).ravel()
    if r.size == 0:
        raise ValueError("returns is empty.")
    if not np.all(np.isfinite(r)):
        raise ValueError("returns contains non-finite values (NaN or inf).")
    return r


def _normalized_weights(weights: npt.ArrayLike | None, n: int) -> np.ndarray:
    if weights is None:
        return np.full(n, 1.0 / n, dtype=np.float64)
    w = np.asarray(weights, dtype=np.float64).ravel()
    if w.size != n:
        raise ValueError(f"weights length {w.size} != returns length {n}.")
    if np.any(w < 0.0) or not np.all(np.isfinite(w)):
        raise ValueError("weights must be finite and non-negative.")
    total = float(w.sum())
    if total <= _EPS:
        raise ValueError("weights sum to zero.")
    return w / total


# ---------------------------------------------------------------------------
# D3 — effective domain / ruin barrier
# ---------------------------------------------------------------------------


def effective_domain_fmax(
    returns: npt.ArrayLike,
    b_star: float,
    *,
    weights: npt.ArrayLike | None = None,
) -> float:
    """Single-period ruin barrier ``f_max = -1 / (b* * min_i R_i)`` (D3).

    The wealth multiplier ``1 + f * b* * R_i`` stays positive for every atom
    with positive weight iff ``f < f_max``. When no adverse bet exists
    (``min_i b* R_i >= 0``) there is no single-bar ruin and the barrier is
    ``+inf``.

    Parameters
    ----------
    returns
        Per-bar returns ``R_i``.
    b_star
        Growth-optimal (full-Kelly) bet; see :func:`full_kelly_leverage`.
    weights
        Empirical-measure weights (uniform by default). Atoms with zero weight
        do not constrain the barrier.
    """
    r = _clean_returns(returns)
    w = _normalized_weights(weights, r.size)
    m = float(b_star) * r
    active = m[w > 0.0]
    m_min = float(active.min()) if active.size else 0.0
    if m_min >= 0.0:
        return float(np.inf)
    return -1.0 / m_min


# ---------------------------------------------------------------------------
# D1 — growth curve, analytic first / second derivative
# ---------------------------------------------------------------------------


def growth_rate(
    returns: npt.ArrayLike,
    leverage: float,
    *,
    weights: npt.ArrayLike | None = None,
    barrier: str = "absorbing",
    cap_floor: float = DEFAULT_CAP_FLOOR,
) -> float:
    """Mean log-growth ``E[log(1 + leverage * R)]`` on the empirical measure.

    ``leverage`` is the applied bet ``f * b*`` (not the fraction ``f``).

    Parameters
    ----------
    barrier
        ``"absorbing"`` (FROZEN PRIMARY, D5): any positive-weight atom with
        ``1 + leverage * R_i <= 0`` is ruin, so the mean log-growth is
        ``-inf`` (the ``-inf`` convention; a path hitting it is dead).
        ``"cap"`` (SENSITIVITY ONLY): the wealth multiplier is floored at
        ``cap_floor`` so the log is finite. This biases the estimate UPWARD at
        leverage and must never be used as the primary estimator.
    cap_floor
        Retained-wealth fraction used only when ``barrier == "cap"``.
    """
    r = _clean_returns(returns)
    w = _normalized_weights(weights, r.size)
    mult = 1.0 + float(leverage) * r
    if barrier == "absorbing":
        if np.any((mult <= 0.0) & (w > 0.0)):
            return float(-np.inf)
        return float(np.sum(w * np.log(mult)))
    if barrier == "cap":
        if not (cap_floor > 0.0):
            raise ValueError("cap_floor must be strictly positive.")
        capped = np.maximum(mult, float(cap_floor))
        return float(np.sum(w * np.log(capped)))
    raise ValueError(f"unknown barrier {barrier!r}; use 'absorbing' or 'cap'.")


def growth_derivative(
    returns: npt.ArrayLike,
    b_star: float,
    f: float,
    *,
    weights: npt.ArrayLike | None = None,
) -> float:
    """Analytic ``g'(f) = sum_i w_i m_i / (1 + f m_i)`` with ``m_i = b* R_i`` (D1).

    Returns ``nan`` if ``f`` is at or beyond the ruin barrier (some
    ``1 + f m_i <= 0``), where the derivative is undefined.
    """
    r = _clean_returns(returns)
    w = _normalized_weights(weights, r.size)
    m = float(b_star) * r
    denom = 1.0 + float(f) * m
    if np.any((denom <= 0.0) & (w > 0.0)):
        return float(np.nan)
    return float(np.sum(w * m / denom))


def growth_second_derivative(
    returns: npt.ArrayLike,
    b_star: float,
    f: float,
    *,
    weights: npt.ArrayLike | None = None,
) -> float:
    """Analytic ``g''(f) = -sum_i w_i m_i^2 / (1 + f m_i)^2`` (D1).

    Strictly negative wherever a non-degenerate bet exists (some ``m_i != 0``),
    establishing strict concavity on the effective domain. Returns ``nan`` at
    or beyond the ruin barrier.
    """
    r = _clean_returns(returns)
    w = _normalized_weights(weights, r.size)
    m = float(b_star) * r
    denom = 1.0 + float(f) * m
    if np.any((denom <= 0.0) & (w > 0.0)):
        return float(np.nan)
    return float(-np.sum(w * (m / denom) ** 2))


def growth_curve(
    returns: npt.ArrayLike,
    b_star: float,
    fractions: npt.ArrayLike = KELLY_FRACTION_GRID,
    *,
    weights: npt.ArrayLike | None = None,
    barrier: str = "absorbing",
    cap_floor: float = DEFAULT_CAP_FLOOR,
) -> np.ndarray:
    """Vector of ``g(f)`` over the Kelly-fraction grid (D1).

    Each entry is :func:`growth_rate` at ``leverage = f * b*``. Grid points at
    or beyond the ruin barrier return ``-inf`` under the absorbing barrier.
    """
    fr = np.asarray(fractions, dtype=np.float64).ravel()
    return np.array(
        [
            growth_rate(
                returns,
                float(f) * float(b_star),
                weights=weights,
                barrier=barrier,
                cap_floor=cap_floor,
            )
            for f in fr
        ],
        dtype=np.float64,
    )


# ---------------------------------------------------------------------------
# Interior-maximum solver — the growth-optimal (full-Kelly) bet b*
# ---------------------------------------------------------------------------


def full_kelly_leverage(
    returns: npt.ArrayLike,
    *,
    weights: npt.ArrayLike | None = None,
) -> float:
    """Growth-optimal leverage ``b*`` = unique interior root of ``g'(lambda)=0``.

    Solves ``sum_i w_i R_i / (1 + lambda R_i) = 0`` on ``(0, lambda_max)`` where
    ``lambda_max = -1 / min_i R_i`` is the leverage ruin barrier. Because
    ``g''<0`` the objective ``g(lambda) = E[log(1 + lambda R)]`` is strictly
    concave, so the root is unique and is the argmax (Kelly 1956; Breiman 1961).

    Benchmark: an even-money bet with win probability ``p`` (``R in {+1, -1}``,
    weights ``{p, 1-p}``) returns the closed-form full-Kelly stake ``2p - 1``.

    Returns ``0.0`` when the bet is unfavourable (``E[R] <= 0``): no positive
    growth-optimal leverage exists.
    """
    r = _clean_returns(returns)
    w = _normalized_weights(weights, r.size)

    def gprime(lam: float) -> float:
        return float(np.sum(w * r / (1.0 + lam * r)))

    slope_at_zero = float(np.sum(w * r))  # g'(0) = E[R]
    if slope_at_zero <= 0.0:
        return 0.0

    active = r[w > 0.0]
    r_min = float(active.min())
    if r_min >= 0.0:
        # No losing bar: g' stays positive, growth unbounded in leverage. There
        # is no interior optimum; report +inf as the (degenerate) barrier limit.
        return float(np.inf)

    lam_barrier = -1.0 / r_min
    hi = lam_barrier * _BARRIER_BRACKET_SHRINK
    # g'(0+) > 0 by construction; g'(hi) -> -inf near the barrier, so a sign
    # change brackets the unique root.
    if gprime(hi) >= 0.0:
        return float(hi)
    return float(brentq(gprime, _EPS, hi))


# ---------------------------------------------------------------------------
# D4 — over-betting zero-growth crossing f_0
# ---------------------------------------------------------------------------


def zero_growth_fraction(
    returns: npt.ArrayLike,
    b_star: float,
    *,
    weights: npt.ArrayLike | None = None,
) -> float:
    """Over-betting zero-growth crossing ``f_0 > 1`` with ``g(f_0) = 0`` (D4).

    On the effective domain ``g`` is concave with its interior max at ``f = 1``
    (``g(1) > 0``) and ``g(f) -> -inf`` as ``f -> f_max``; hence it crosses zero
    exactly once at some ``f_0 in (1, f_max)``. The thin-tailed benchmark is
    ``f_0 = 2`` (twice Kelly gives zero growth, Thorp 2006); fat tails push
    ``f_0`` below 2. Returns ``+inf`` when no finite ruin barrier exists (no
    losing bar), i.e. over-betting never drives growth to zero.
    """
    f_max = effective_domain_fmax(returns, b_star, weights=weights)
    if not np.isfinite(f_max):
        return float(np.inf)

    def g(f: float) -> float:
        return growth_rate(returns, float(f) * float(b_star), weights=weights, barrier="absorbing")

    g_one = g(1.0)
    if not np.isfinite(g_one) or g_one <= 0.0:
        # Degenerate: full Kelly already non-positive growth on this measure.
        return float(np.nan)
    hi = f_max * _BARRIER_BRACKET_SHRINK
    lo = 1.0
    g_hi = g(hi)
    if np.isfinite(g_hi) and g_hi > 0.0:
        # Near-barrier fat-tailed regime: g stays finite-and-positive across the
        # whole search interval and only dives to -inf within float-epsilon of
        # f_max. The zero crossing is therefore pinned to the barrier itself, so
        # f_0 = f_max to machine precision. Stepping inward (as the bracketing
        # loop below does) only increases g and can never obtain a negative
        # endpoint, so returning here is required to avoid a silent nan on
        # exactly the regime D4 exists to flag (grid-top over-betting into the
        # ruin barrier; Thorp 2006 twice-Kelly benchmark,
        # DOI 10.1016/S1872-0978(06)01009-X).
        return float(f_max)
    # g(hi) -> -inf near barrier; brentq needs a finite negative endpoint, so
    # step inward until g is finite and negative.
    f_hi = hi
    for _ in range(_MAX_BRACKET_DOUBLINGS):
        val = g(f_hi)
        if np.isfinite(val) and val < 0.0:
            return float(brentq(g, lo, f_hi))
        # Move the upper endpoint back toward 1 (halving the gap above lo).
        f_hi = lo + 0.5 * (f_hi - lo)
        if f_hi - lo < _EPS:
            break
    return float(np.nan)


# ---------------------------------------------------------------------------
# D3 / D5 — ruin probability
# ---------------------------------------------------------------------------


def single_bar_ruin_probability(
    returns: npt.ArrayLike,
    leverage: float,
    *,
    weights: npt.ArrayLike | None = None,
) -> float:
    """Single-bar ruin probability ``P(1 + leverage * R <= 0)`` (D3).

    Weighted fraction of the empirical measure that breaches the barrier in one
    bar. ``leverage = f * b*``.
    """
    r = _clean_returns(returns)
    w = _normalized_weights(weights, r.size)
    breach = (1.0 + float(leverage) * r) <= 0.0
    return float(np.sum(w[breach]))


def bootstrap_single_bar_ruin(
    returns: npt.ArrayLike,
    leverage: float,
    *,
    rng: np.random.Generator,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    block_length: float | None = None,
    ci_alpha: float = DEFAULT_CI_ALPHA,
) -> tuple[float, float, float, BlockLengthSelection]:
    """Stationary-bootstrap point estimate and CI for single-bar ruin (D3/D5).

    Reuses the project block-length machinery (Politis & White 2004, PPW 2009
    corrected) and the stationary bootstrap (Politis & Romano 1994). Returns
    ``(point, ci_low, ci_high, selection)`` where ``point`` is the full-sample
    single-bar ruin probability and the CI is the ``1 - ci_alpha`` percentile
    interval across resamples.

    Parameters
    ----------
    rng
        Caller-supplied NumPy Generator (reproducibility log traces the seed).
    """
    r = _clean_returns(returns)
    n = r.size
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}.")
    if not (0.0 < ci_alpha < 1.0):
        raise ValueError(f"ci_alpha must be in (0, 1), got {ci_alpha}.")

    if block_length is None:
        selection = choose_block_length(r, bootstrap_type="stationary")
        bl = selection.block_length
    else:
        selection = BlockLengthSelection(
            method="fixed",
            block_length=float(block_length),
            bootstrap_type="stationary",
            notes="caller-specified fixed block length.",
        )
        bl = float(block_length)

    point = single_bar_ruin_probability(r, leverage)
    breach = (1.0 + float(leverage) * r) <= 0.0
    reps = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n, block_length=bl, rng=rng)
        reps[b] = float(np.mean(breach[idx]))
    lo = float(np.quantile(reps, ci_alpha / 2.0))
    hi = float(np.quantile(reps, 1.0 - ci_alpha / 2.0))
    return point, lo, hi, selection


# ---------------------------------------------------------------------------
# D5 — Busseti-Ryu-Boyd drawdown bound
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DrawdownBound:
    """Busseti-Ryu-Boyd 2016 drawdown-probability bound for one grid point.

    ``exponent`` is the risk exponent ``lam* > 0`` solving ``E[W^{-lam}] = 1``
    with ``W = 1 + leverage * R``; ``prob_bound`` is ``drawdown_level ** lam*``,
    an upper bound on ``P(min_t W_t <= drawdown_level)``. ``valid`` is ``False``
    when no positive exponent exists (unfavourable bet) or the bet can ruin
    (``W <= 0`` with positive weight), in which case the bound is vacuous.
    """

    drawdown_level: float
    exponent: float
    prob_bound: float
    valid: bool


def drawdown_probability_bound(
    returns: npt.ArrayLike,
    leverage: float,
    drawdown_level: float,
    *,
    weights: npt.ArrayLike | None = None,
) -> DrawdownBound:
    """Busseti, Ryu & Boyd 2016 drawdown bound (D5).

    For a target drawdown fraction ``a = drawdown_level in (0, 1)``, find the
    risk exponent ``lam* > 0`` with ``E[W^{-lam*}] = 1`` (``W = 1 + leverage*R``,
    the per-bar wealth multiplier). Then

        P(min_t W_t <= a) <= a ** lam*.

    Equivalently, for any desired probability bound ``b in (0, 1)``, setting
    ``lam = log(b) / log(a)`` and checking ``E[W^{-lam}] <= 1`` certifies
    ``P(W_min < a) < b``. This routine returns the largest certified bound by
    solving for ``lam*`` directly.

    Requires ``W > 0`` for every positive-weight atom (leverage below the ruin
    barrier); otherwise the bound is vacuous and ``valid = False``.
    """
    if not (0.0 < drawdown_level < 1.0):
        raise ValueError(f"drawdown_level must be in (0, 1), got {drawdown_level}.")
    r = _clean_returns(returns)
    w = _normalized_weights(weights, r.size)
    mult = 1.0 + float(leverage) * r
    if np.any((mult <= 0.0) & (w > 0.0)):
        return DrawdownBound(float(drawdown_level), float(np.nan), 1.0, valid=False)

    log_w = np.log(mult)
    # h(lam) = E[W^{-lam}] - 1 = E[exp(-lam log W)] - 1. h(0)=0,
    # h'(0) = -E[log W] = -g < 0 for a favourable bet, and h -> +inf as
    # lam -> +inf when a losing bar (log W < 0) exists. The unique positive
    # root lam* is the risk exponent.
    growth = float(np.sum(w * log_w))
    if growth <= 0.0 or not np.any(log_w < 0.0):
        return DrawdownBound(float(drawdown_level), 0.0, 1.0, valid=False)

    # phi(lam) = E[W^{-lam}] is convex with phi(0) = 1, phi'(0) = -g < 0, so it
    # dips below 1 and (a losing bar exists) rises back through 1 at the unique
    # nonzero risk exponent lam*. h(lam) = phi(lam) - 1 has a spurious root at 0
    # too; brackets must sit ABOVE the convex minimum to isolate lam*.
    def phi(lam: float) -> float:
        return float(np.sum(w * np.exp(-lam * log_w)))

    def h(lam: float) -> float:
        return phi(lam) - 1.0

    hi = 1.0
    for _ in range(_MAX_BRACKET_DOUBLINGS):
        if h(hi) > 0.0:
            break
        hi *= 2.0
    else:
        return DrawdownBound(float(drawdown_level), float(np.nan), 1.0, valid=False)

    # Locate the convex minimum lam_m in (0, hi); it lies strictly below lam*.
    lam_m = float(minimize_scalar(phi, bounds=(0.0, hi), method="bounded").x)
    # sqrt(eps) separates lam_m from the trivial root at 0 without cancellation.
    if phi(lam_m) >= 1.0 - np.sqrt(_EPS) or lam_m <= np.sqrt(_EPS):
        # Curve never meaningfully dips below 1 (barely favourable): vacuous.
        return DrawdownBound(float(drawdown_level), 0.0, 1.0, valid=False)

    lam_star = float(brentq(h, lam_m, hi))
    bound = float(drawdown_level) ** lam_star
    return DrawdownBound(float(drawdown_level), lam_star, min(bound, 1.0), valid=True)


# ---------------------------------------------------------------------------
# D2 — nested rolling-origin (purge + embargo) out-of-sample f**
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RollingOriginGrowth:
    """Out-of-sample geometric-growth curve from purged/embargoed rolling origin.

    ``fractions`` is the evaluated Kelly-fraction grid; ``oos_growth`` is the
    across-fold mean OOS ``g(f)`` per fraction (``-inf`` at a fraction means
    some fold ruined out-of-sample at that leverage); ``per_fold_growth`` is the
    ``(n_folds, n_fractions)`` matrix; ``f_star_oos`` is the OOS-argmax
    fraction; ``b_star_folds`` records the per-fold plug-in full-Kelly bet.
    """

    fractions: np.ndarray
    oos_growth: np.ndarray
    per_fold_growth: np.ndarray
    f_star_oos: float
    b_star_folds: np.ndarray
    n_folds: int
    notes: str


def nested_rolling_origin_growth(
    returns: npt.ArrayLike,
    *,
    fractions: npt.ArrayLike = KELLY_FRACTION_GRID,
    n_splits: int = DEFAULT_N_SPLITS,
    purge: int = 0,
    embargo_fraction: float = DEFAULT_EMBARGO_FRACTION,
    min_train_fraction: float = DEFAULT_MIN_TRAIN_FRACTION,
    barrier: str = "absorbing",
) -> RollingOriginGrowth:
    """Estimation-error-adjusted OOS growth via purged/embargoed rolling origin (D2).

    Expanding-window walk-forward: fold ``k`` estimates the full-Kelly bet
    ``b*_k`` on the training span (plug-in), then EVALUATES ``g`` on a disjoint
    forward test window at each fraction ``f`` (leverage ``f * b*_k``). A
    ``purge`` gap and an ``embargo`` (fraction of the sample) separate train
    from test to defeat leakage across the return horizon (Lopez de Prado 2018
    ch. 7). The OOS-optimal fraction ``f**`` is the argmax of the across-fold
    mean OOS growth.

    Because the plug-in ``b*_k`` inherits estimation error (dominated by the
    mean, Chopra & Ziemba 1993), the OOS optimum satisfies ``f** <= 1`` in
    expectation and the robust growth-optimal allocation is materially lower
    leverage (Rujeerapaiboon, Kuhn & Wiesemann 2016). Whether the 0.5 grid
    floor brackets ``f**`` from below is an OUTPUT of the on-ledger run, not
    asserted by this routine.

    Parameters
    ----------
    purge
        Bars dropped from the end of each training span (return-label horizon
        minus one; ``0`` for a one-bar return). Named, no magic default.
    embargo_fraction
        Bars embargoed after each test window, as a fraction of the sample
        (Lopez de Prado 2018 §7.4).
    min_train_fraction
        Initial training span as a fraction of the sample (walk-forward
        warm-up).
    """
    r = _clean_returns(returns)
    n = r.size
    if n_splits < 1:
        raise ValueError(f"n_splits must be >= 1, got {n_splits}.")
    if purge < 0:
        raise ValueError(f"purge must be >= 0, got {purge}.")
    if not (0.0 <= embargo_fraction < 1.0):
        raise ValueError(f"embargo_fraction must be in [0, 1), got {embargo_fraction}.")
    if not (0.0 < min_train_fraction < 1.0):
        raise ValueError(f"min_train_fraction must be in (0, 1), got {min_train_fraction}.")

    fr = np.asarray(fractions, dtype=np.float64).ravel()
    embargo = int(np.floor(embargo_fraction * n))
    min_train = int(np.floor(min_train_fraction * n))
    if min_train < _MIN_FIT_BARS:
        raise ValueError("min_train too small; need at least 2 training bars.")

    remaining = n - min_train
    if remaining < n_splits:
        raise ValueError(
            f"not enough data: {remaining} test bars for {n_splits} splits "
            f"(min_train={min_train}, n={n})."
        )
    test_size = remaining // n_splits

    fold_rows: list[np.ndarray] = []
    b_folds: list[float] = []
    for k in range(n_splits):
        test_start = min_train + k * test_size
        test_end = n if k == n_splits - 1 else test_start + test_size
        train_end = test_start - purge - embargo
        if train_end < _MIN_FIT_BARS or test_end <= test_start:
            continue
        train = r[:train_end]
        test = r[test_start:test_end]
        b_k = full_kelly_leverage(train)
        if not np.isfinite(b_k):
            # No interior optimum on this training fold (unbounded / unfavourable);
            # skip — it carries no information about the fraction ranking.
            continue
        row = np.array(
            [growth_rate(test, float(f) * b_k, barrier=barrier) for f in fr],
            dtype=np.float64,
        )
        fold_rows.append(row)
        b_folds.append(float(b_k))

    if not fold_rows:
        raise ValueError("no usable folds produced (check purge/embargo/min_train).")

    per_fold = np.vstack(fold_rows)
    oos = per_fold.mean(axis=0)
    if np.all(~np.isfinite(oos)):
        f_star = float("nan")
    else:
        f_star = float(fr[int(np.nanargmax(np.where(np.isfinite(oos), oos, -np.inf)))])

    return RollingOriginGrowth(
        fractions=fr,
        oos_growth=oos,
        per_fold_growth=per_fold,
        f_star_oos=f_star,
        b_star_folds=np.asarray(b_folds, dtype=np.float64),
        n_folds=len(fold_rows),
        notes=(
            f"expanding walk-forward; n={n}, min_train={min_train}, "
            f"test_size={test_size}, purge={purge}, embargo={embargo}, "
            f"folds_used={len(fold_rows)}/{n_splits}."
        ),
    )


# ---------------------------------------------------------------------------
# D5 — grid-point ruin summary + full report bundle
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class GridPointRuin:
    """Per-grid-point ruin diagnostics (D3/D5)."""

    fraction: float
    leverage: float
    growth_absorbing: float
    growth_cap_sensitivity: float
    distance_to_barrier: float
    single_bar_ruin_prob: float
    ruin_ci_low: float
    ruin_ci_high: float
    drawdown_bound: DrawdownBound


@dataclass(frozen=True)
class KellyGrowthReport:
    """Frozen reference-estimator bundle (D1-D5) for one return series.

    All numbers computed here on a REPRESENTATIVE substrate are illustrative;
    the binding on-ledger instantiation is deferred to the step-4 backfill. No
    Kelly fraction is selected by constructing this report.
    """

    b_star: float
    f_max: float
    f_zero: float
    fractions: np.ndarray
    grid: tuple[GridPointRuin, ...]
    block_length: BlockLengthSelection
    notes: str


def kelly_growth_report(
    returns: npt.ArrayLike,
    *,
    rng: np.random.Generator,
    fractions: npt.ArrayLike = KELLY_FRACTION_GRID,
    drawdown_level: float | None = None,
    n_bootstrap: int = DEFAULT_N_BOOTSTRAP,
    ci_alpha: float = DEFAULT_CI_ALPHA,
    weights: npt.ArrayLike | None = None,
    cap_floor: float = DEFAULT_CAP_FLOOR,
) -> KellyGrowthReport:
    """Assemble the full D1-D5 reference-estimator report for a return series.

    This is the object the ledger backfill will populate with shadow-ledger
    returns. On any other substrate every field is illustrative-only.

    Parameters
    ----------
    drawdown_level
        Target drawdown fraction ``a`` for the Busseti-Ryu-Boyd bound. Defaults
        to ``ci_alpha`` (i.e. a drawdown to the same tail level as the CI), a
        reporting-symmetry choice, not a tuned risk budget.
    """
    r = _clean_returns(returns)
    b_star = full_kelly_leverage(r, weights=weights)
    f_max = effective_domain_fmax(r, b_star, weights=weights)
    f_zero = zero_growth_fraction(r, b_star, weights=weights)
    a = ci_alpha if drawdown_level is None else drawdown_level

    fr = np.asarray(fractions, dtype=np.float64).ravel()
    selection = choose_block_length(r, bootstrap_type="stationary")

    grid: list[GridPointRuin] = []
    for f in fr:
        lev = float(f) * b_star
        point, lo, hi, _ = bootstrap_single_bar_ruin(
            r,
            lev,
            rng=rng,
            n_bootstrap=n_bootstrap,
            block_length=selection.block_length,
            ci_alpha=ci_alpha,
        )
        grid.append(
            GridPointRuin(
                fraction=float(f),
                leverage=lev,
                growth_absorbing=growth_rate(r, lev, weights=weights, barrier="absorbing"),
                growth_cap_sensitivity=growth_rate(
                    r, lev, weights=weights, barrier="cap", cap_floor=cap_floor
                ),
                distance_to_barrier=(f_max - float(f)) if np.isfinite(f_max) else float(np.inf),
                single_bar_ruin_prob=point,
                ruin_ci_low=lo,
                ruin_ci_high=hi,
                drawdown_bound=drawdown_probability_bound(r, lev, a, weights=weights),
            )
        )

    return KellyGrowthReport(
        b_star=b_star,
        f_max=f_max,
        f_zero=f_zero,
        fractions=fr,
        grid=tuple(grid),
        block_length=selection,
        notes=(
            "ILLUSTRATIVE on the supplied substrate; on-ledger numeric "
            "instantiation deferred to the step-4 shadow-ledger backfill "
            "(P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE)."
        ),
    )


__all__.append("kelly_growth_report")
