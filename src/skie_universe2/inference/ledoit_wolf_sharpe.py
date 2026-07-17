"""Ledoit-Wolf (2008) studentized bootstrap test for the difference of two Sharpe ratios.

ADR-0007 confirmation-ladder differential statistic. The anti-gate for the H103
stress-state scan compares the stress-cell Sharpe against the complement-cell
Sharpe. The two cells partition the same shadow-ledger periods, so the two
per-period return series are **paired** and their Sharpe estimates are
algebraically dependent — a paired studentized comparison that respects the
cross-series (and serial) dependence is required, not two independent
single-Sharpe intervals.

Ground truth
------------

Numerical-fidelity implementation of the studentized time-series bootstrap of
[Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002) (Olivier
Ledoit & Michael Wolf, "Robust performance hypothesis testing with the Sharpe
ratio", *Journal of Empirical Finance* 15(5):850-859), robust to heavy tails
and serial dependence, testing ``H0: Delta = SR_a - SR_b = 0``.

- **Point estimate.** ``Delta_hat = SR_a - SR_b`` with per-period
  ``SR = mean / std`` (``ddof=1`` sample std, the project Sharpe convention).
- **Delta-method gradient (LW08 eq. 4).** Writing each Sharpe as a smooth
  function of the moment vector ``v = (mu_a, mu_b, gamma_a, gamma_b)`` with
  ``gamma = E[r^2]`` and ``s^2 = gamma - mu^2`` the population variance, the
  gradient of ``Delta`` is
  ``nabla f = ( gamma_a/s_a^3, -gamma_b/s_b^3, -mu_a/(2 s_a^3), mu_b/(2 s_b^3) )``.
  The asymptotic variance of ``sqrt(T) Delta_hat`` is ``nabla f' Psi nabla f``
  where ``Psi`` is the long-run covariance of
  ``y_t = (r_{a,t}-mu_a, r_{b,t}-mu_b, r_{a,t}^2-gamma_a, r_{b,t}^2-gamma_b)``.
  Because ``nabla f' Psi nabla f`` is the long-run variance of the scalar
  influence series ``u_t = nabla f' y_t``, the HAC estimate collapses to a
  one-dimensional kernel long-run-variance estimate of ``u_t`` — the form used
  here.
- **HAC standard error (LW08 eq. 5).** ``s(Delta_hat) = sqrt(LRV_hac(u) / T)``
  with ``LRV_hac`` the Bartlett-kernel (Newey-West) HAC estimate of the long-run
  variance of ``u_t`` and a data-dependent truncation lag chosen by the
  [Newey & West 1994](https://doi.org/10.2307/2297912) automatic-bandwidth rule
  (the paper sanctions Andrews 1991 / Newey-West 1994 automatic bandwidths; the
  Bartlett kernel is the project HAC default, ``rules/quant-project.md``). A
  ``T/(T-4)`` small-sample degrees-of-freedom factor (offsetting estimation of the
  4-vector ``v``) is applied — this is a SELF-CHOSEN cosmetic adjustment, NOT part
  of LW08 (the paper applies no d.o.f. correction to Psi_hat); it is provably INERT
  to every reported output (identical ``T`` makes it cancel in both the studentized
  p-value comparison and the CI product), so it changes no result.
- **Studentized bootstrap (LW08 §3.2.2, eq. 7 + eq. 9).** The two paired series
  are resampled with a **common** block index (the stationary bootstrap of
  [Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870);
  LW08 footnote 10 adopts the stationary bootstrap for the same construction) so
  the resample preserves both the cross-series and serial dependence. On each
  resample the difference ``Delta_hat*`` and its own HAC SE ``s(Delta_hat*)`` are
  recomputed (an *individual* SE per resample — LW08 Remark 3.3 flags a common
  SE as incorrect), and the centered studentized statistic
  ``d*_m = |Delta_hat*_m - Delta_hat| / s(Delta_hat*_m)`` is formed. With the
  observed statistic ``d = |Delta_hat| / s(Delta_hat)`` the two-sided p-value is
  ``PV = (#{ d*_m >= d } + 1) / (M + 1)`` (eq. 9) and the symmetric
  ``1 - alpha`` confidence interval is
  ``Delta_hat +/- z*_{|.|,1-alpha} * s(Delta_hat)`` (eq. 7) where
  ``z*_{|.|,1-alpha}`` is the ``1 - alpha`` quantile of ``{d*_m}``. The interval
  excludes zero iff ``PV < alpha`` (both are ``|.|``-based), so the p-value and
  the CI agree by construction.

Units / convention note
------------------------

The reported Sharpe point estimates (``sharpe_a``, ``sharpe_b``,
``sharpe_diff``) use the ``ddof=1`` sample std; the delta-method gradient and the
HAC ``Psi`` use population second moments (``gamma = mean(r^2)``,
``s^2 = gamma - mu^2``). The two conventions differ only at ``O(1/T)`` and are
asymptotically equivalent; the studentized bootstrap does not require the SE to
be exact, only that ``Delta_hat`` and ``Delta_hat*`` be studentized identically
(they are). Returns are per-period; the caller fixes the log-vs-arithmetic
convention upstream.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from skie_universe2.inference.bootstrap import (
    politis_white_block_length,
    stationary_bootstrap_indices,
)

# Numerical floor on variances / standard errors (float64 ULP), matching the
# degeneracy guard in :mod:`skie_universe2.inference.bootstrap`.
_EPS = float(np.finfo(np.float64).eps)

# Newey & West 1994 automatic-bandwidth constants for the Bartlett (q=1) kernel.
# Pilot truncation lag  m = floor(NW94_PILOT_C * (T / NW94_PILOT_SCALE)^NW94_PILOT_EXP);
# bandwidth  L = floor(BARTLETT_C_GAMMA * (s1/s0)^2 ^ BW_EXP * T^BW_EXP) with
# BW_EXP = 1/(2q+1) = 1/3. Constants are the published NW94 / Andrews 1991
# Table-I values (BARTLETT_C_GAMMA = 1.1447 is the Bartlett kernel constant),
# not tunable analysis parameters.
NW94_PILOT_C = 4.0
NW94_PILOT_SCALE = 100.0
NW94_PILOT_EXP = 2.0 / 9.0  # Bartlett-kernel pilot growth rate (NW94)
BARTLETT_C_GAMMA = 1.1447  # Andrews 1991 Table I, Bartlett kernel
BARTLETT_BW_EXP = 1.0 / 3.0  # 1/(2q+1), q=1 for Bartlett
# Self-chosen small-sample d.o.f. factor T/(T - HAC_DF_ADJ) offsetting the estimation of
# the 4-vector v (= (mu_a, mu_b, gamma_a, gamma_b)). NOT from LW08 (which applies no such
# correction); provably inert to all reported outputs (identical T cancels it).
HAC_DF_ADJ = 4


@dataclass(frozen=True)
class SharpeDiffResult:
    """Ledoit-Wolf 2008 studentized-bootstrap test for ``SR_a - SR_b``.

    Attributes
    ----------
    sharpe_a, sharpe_b : float
        Per-period Sharpe ratios (``mean/std``, ``ddof=1``) of the two series.
    sharpe_diff : float
        ``sharpe_a - sharpe_b`` = the tested difference ``Delta_hat``.
    studentized_stat : float
        Signed observed studentized statistic ``Delta_hat / s(Delta_hat)`` (the
        two-sided p-value uses its absolute value).
    p_value : float
        Two-sided studentized-bootstrap p-value for ``H0: Delta = 0`` (LW08
        eq. 9), ``(#{d*_m >= d} + 1) / (M + 1)``.
    ci_low, ci_high : float
        Symmetric ``1 - alpha`` studentized-bootstrap CI for ``Delta`` (LW08
        eq. 7). Excludes zero iff ``p_value < alpha``.
    alpha : float
        Nominal two-sided level of the CI.
    block_length : float
        Stationary-bootstrap expected block length actually used (the
        Politis-White auto-selection when the caller passed ``None``).
    n_bootstrap : int
        Number of bootstrap resamples ``M`` that produced a finite studentized
        statistic (degenerate zero-SE resamples are dropped).
    """

    sharpe_a: float
    sharpe_b: float
    sharpe_diff: float
    studentized_stat: float
    p_value: float
    ci_low: float
    ci_high: float
    alpha: float
    block_length: float
    n_bootstrap: int


def _as_paired(
    returns_a: NDArray[np.float64], returns_b: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Validate + coerce the two paired series to clean equal-length 1-D arrays."""
    a = np.asarray(returns_a, dtype=np.float64).ravel()
    b = np.asarray(returns_b, dtype=np.float64).ravel()
    if a.size != b.size:
        raise ValueError(f"returns_a and returns_b must be equal length; got {a.size} and {b.size}")
    if a.size < 2:  # justify: sample std / paired Sharpe need >= 2 observations
        raise ValueError(f"need >= 2 paired observations, got {a.size}")
    if not (np.all(np.isfinite(a)) and np.all(np.isfinite(b))):
        raise ValueError("inputs contain non-finite values (NaN or inf).")
    return a, b


def _influence_and_diff(
    a: NDArray[np.float64], b: NDArray[np.float64]
) -> tuple[float, float, float, NDArray[np.float64]]:
    """Return ``(sharpe_a, sharpe_b, sharpe_diff, u_t)`` for the Sharpe difference.

    ``u_t = nabla f' y_t`` is the scalar delta-method influence series whose
    long-run variance equals ``nabla f' Psi nabla f`` (LW08 eq. 4). Sharpe point
    estimates use ``ddof=1``; the gradient uses population second moments.
    """
    mu_a = float(a.mean())
    mu_b = float(b.mean())
    gamma_a = float(np.mean(a * a))
    gamma_b = float(np.mean(b * b))
    var_a = gamma_a - mu_a * mu_a  # population variance
    var_b = gamma_b - mu_b * mu_b
    if var_a <= _EPS or var_b <= _EPS:
        raise ValueError("a return series has (near-)zero variance; Sharpe difference undefined")

    s_a = np.sqrt(var_a)
    s_b = np.sqrt(var_b)
    s_a3 = s_a * s_a * s_a
    s_b3 = s_b * s_b * s_b

    # ddof=1 reported Sharpe ratios.
    sr_a = mu_a / float(a.std(ddof=1))
    sr_b = mu_b / float(b.std(ddof=1))
    diff = sr_a - sr_b

    # Delta-method gradient (LW08 eq. 4) w.r.t. v = (mu_a, mu_b, gamma_a, gamma_b).
    g_mu_a = gamma_a / s_a3
    g_mu_b = -gamma_b / s_b3
    g_gamma_a = -mu_a / (2.0 * s_a3)
    g_gamma_b = mu_b / (2.0 * s_b3)

    u = (
        g_mu_a * (a - mu_a)
        + g_mu_b * (b - mu_b)
        + g_gamma_a * (a * a - gamma_a)
        + g_gamma_b * (b * b - gamma_b)
    )
    return sr_a, sr_b, diff, u


def _nw94_bartlett_bandwidth(u: NDArray[np.float64]) -> int:
    """Newey-West 1994 automatic Bartlett-kernel truncation lag for a scalar series."""
    n = u.size
    uc = u - u.mean()
    m = int(NW94_PILOT_C * (n / NW94_PILOT_SCALE) ** NW94_PILOT_EXP)
    m = max(0, min(m, n - 1))
    g0 = float(uc @ uc) / n
    if g0 <= _EPS:
        return 0
    s0 = g0
    s1 = 0.0
    for j in range(1, m + 1):
        gj = float(uc[j:] @ uc[:-j]) / n
        s0 += 2.0 * gj
        s1 += 2.0 * j * gj
    if s0 <= _EPS:
        # Non-positive long-run-variance pilot: fall back to the truncated
        # (iid) estimate rather than a spurious bandwidth.
        return 0
    gamma_hat = BARTLETT_C_GAMMA * ((s1 / s0) ** 2) ** BARTLETT_BW_EXP
    lag = int(gamma_hat * n**BARTLETT_BW_EXP)
    return max(0, min(lag, n - 1))


def _bartlett_lrv(u: NDArray[np.float64], lag: int) -> float:
    """Bartlett-kernel HAC long-run variance of a scalar series (floored at 0)."""
    n = u.size
    uc = u - u.mean()
    lrv = float(uc @ uc) / n
    for j in range(1, lag + 1):
        gj = float(uc[j:] @ uc[:-j]) / n
        w = 1.0 - j / (lag + 1.0)
        lrv += 2.0 * w * gj
    return max(lrv, 0.0)  # Bartlett kernel is PSD; floor guards float round-off


def _hac_se(u: NDArray[np.float64], *, bandwidth: int | None) -> tuple[float, int]:
    """HAC standard error ``sqrt(T/(T-4) * LRV_hac(u) / T)`` and the lag used.

    LRV_hac and ``sqrt(LRV/T)`` are LW08 eq. 5; the ``T/(T-4)`` factor is a self-chosen
    inert small-sample adjustment (not LW08). See the module docstring.
    """
    n = u.size
    lag = _nw94_bartlett_bandwidth(u) if bandwidth is None else int(bandwidth)
    lag = max(0, min(lag, n - 1))
    lrv = _bartlett_lrv(u, lag)
    df_factor = n / (n - HAC_DF_ADJ) if n > HAC_DF_ADJ else 1.0
    se = float(np.sqrt(df_factor * lrv / n))
    return se, lag


def sharpe_diff_hac_se(
    returns_a: NDArray[np.float64],
    returns_b: NDArray[np.float64],
    *,
    bandwidth: int | None = None,
) -> tuple[float, float, int]:
    """Sharpe difference and its HAC standard error (LW08 eqs. 4-5).

    Convenience/inspection entry point returning ``(sharpe_diff, se, lag)``.
    ``bandwidth=None`` selects the Newey-West 1994 automatic Bartlett lag;
    ``bandwidth=0`` gives the i.i.d. (truncated-kernel) standard error.
    """
    a, b = _as_paired(returns_a, returns_b)
    _, _, diff, u = _influence_and_diff(a, b)
    se, lag = _hac_se(u, bandwidth=bandwidth)
    return diff, se, lag


def sharpe_ratio_difference_test(
    returns_a: NDArray[np.float64],
    returns_b: NDArray[np.float64],
    *,
    block_length: float | None = None,
    rng: np.random.Generator,
    n_bootstrap: int,
    alpha: float = 0.05,
) -> SharpeDiffResult:
    """Studentized time-series bootstrap test for ``SR_a - SR_b`` (Ledoit-Wolf 2008).

    Parameters
    ----------
    returns_a, returns_b : 1-D float arrays
        Paired per-period return series of equal length (same periods); e.g. the
        stress-cell and complement-cell realized returns. ``ValueError`` on a
        length mismatch, ``< 2`` observations, non-finite values, or a
        (near-)zero-variance series.
    block_length : float or None
        Stationary-bootstrap expected block length. ``None`` (default)
        auto-selects it via :func:`politis_white_block_length` on the influence
        series ``u_t`` (falling back to ``1.0`` when ``T < 4``).
    rng : numpy.random.Generator
        Seeded generator — deterministic output for a fixed seed.
    n_bootstrap : int
        Number of studentized bootstrap resamples ``M`` (``>= 1``).
    alpha : float
        Two-sided nominal level of the returned confidence interval.

    Returns
    -------
    SharpeDiffResult
        The two Sharpes, their difference, the signed studentized statistic, the
        LW08 eq. 9 two-sided p-value, and the LW08 eq. 7 symmetric ``1 - alpha``
        studentized-bootstrap confidence interval.
    """
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}")
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")

    a, b = _as_paired(returns_a, returns_b)
    n = a.size
    sr_a, sr_b, diff, u = _influence_and_diff(a, b)
    se, _ = _hac_se(u, bandwidth=None)
    if se <= _EPS:
        raise ValueError("degenerate (zero) HAC standard error; studentized statistic undefined")

    if block_length is None:
        bl = 1.0 if n < HAC_DF_ADJ else politis_white_block_length(u).block_length
    else:
        if block_length < 1.0:
            raise ValueError(f"block_length must be >= 1, got {block_length}")
        bl = float(block_length)

    stat = diff / se  # signed observed statistic; p-value uses |stat|
    d_obs = abs(stat)

    # Studentized bootstrap: COMMON block index across the paired series so the
    # resample preserves both cross-series and serial dependence.
    d_star: list[float] = []
    for _ in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n, block_length=bl, rng=rng)
        ab = a[idx]
        bb = b[idx]
        try:
            _, _, diff_b, u_b = _influence_and_diff(ab, bb)
        except ValueError:
            continue  # degenerate resample (constant series) — drop
        se_b, _ = _hac_se(u_b, bandwidth=None)
        if se_b <= _EPS:
            continue
        d_star.append(abs(diff_b - diff) / se_b)

    if not d_star:
        raise ValueError(
            "all bootstrap resamples were degenerate; cannot form a studentized distribution"
        )
    d_arr = np.asarray(d_star, dtype=np.float64)
    m_eff = d_arr.size

    # LW08 eq. 9 two-sided p-value.
    p_value = float((np.sum(d_arr >= d_obs) + 1.0) / (m_eff + 1.0))

    # LW08 eq. 7 symmetric studentized 1-alpha interval.
    z_abs = float(np.quantile(d_arr, 1.0 - alpha))
    ci_low = diff - z_abs * se
    ci_high = diff + z_abs * se

    return SharpeDiffResult(
        sharpe_a=float(sr_a),
        sharpe_b=float(sr_b),
        sharpe_diff=float(diff),
        studentized_stat=float(stat),
        p_value=p_value,
        ci_low=float(ci_low),
        ci_high=float(ci_high),
        alpha=float(alpha),
        block_length=float(bl),
        n_bootstrap=int(m_eff),
    )


__all__ = [
    "SharpeDiffResult",
    "sharpe_diff_hac_se",
    "sharpe_ratio_difference_test",
]
