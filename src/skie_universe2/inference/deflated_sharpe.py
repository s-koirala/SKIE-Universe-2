"""Deflated Sharpe Ratio (DSR) — ADR-0008 confirmation-ladder reference estimator.

Non-waivable overfitting/multiplicity control per
[docs/decisions/ADR-0008-integrity-non-negotiables.md](docs/decisions/ADR-0008-integrity-non-negotiables.md)
Decision 6: the family-wise trial register carries the per-trial Sharpe and
clustering metadata *because* the DSR needs the effective trial count ``N`` and
the cross-trial Sharpe dispersion ``sigma_SR`` — neither computable from a raw
count. This module is the estimator those fields feed.

Ground truth
------------

- :func:`sharpe_standard_error` — the Sharpe-ratio standard error adjusted for
  non-normality (skewness ``gamma3``, kurtosis ``gamma4``) and estimation
  variance, per [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453) (Andrew W.
  Lo, "The Statistics of Sharpe Ratios", Financial Analysts Journal 58(4):36-52)
  with the Mertens non-normal correction:
  ``SE(SR) = sqrt((1 - gamma3*SR + (gamma4-1)/4 * SR^2) / (n-1))``.
- :func:`expected_max_sharpe` — the expected maximum Sharpe under ``N``
  independent zero-skill trials via the false-strategy theorem of
  [Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094)
  ("The Deflated Sharpe Ratio", Journal of Portfolio Management 40(5):94-107):
  ``E[max] ~ sigma_SR * ((1-g) * Z^-1[1 - 1/N] + g * Z^-1[1 - 1/(N*e)])`` with
  ``g`` the Euler-Mascheroni constant and ``sigma_SR`` the cross-trial Sharpe
  standard deviation. This is the deflated (selection-bias-corrected) benchmark.
- :func:`deflated_sharpe_ratio` — the DSR itself:
  ``DSR = Z[ (SR_obs - SR_benchmark) / SE(SR) ]`` — the probability that the
  strategy's true Sharpe exceeds the deflated benchmark, i.e. the post-deflation
  p-value that the true Sharpe is positive after correcting for selection bias,
  backtest overfitting, and non-normality.

Units convention (binding)
---------------------------

All Sharpe inputs (``sr_observed``, ``sr_std``) and the returned ``sr_benchmark``
/ ``se_sr`` are in **per-observation** units at the same sampling frequency as
the ``n_obs`` return observations — NOT annualized. The false-strategy theorem
and the Lo/Mertens SE are both stated in that frequency; annualizing ``SR`` and
``sigma_SR`` by the same ``sqrt(periods)`` factor leaves the standardized DSR
z-score invariant, so the DSR is frequency-agnostic as long as the three Sharpe
inputs share one frequency. Skewness/kurtosis are the returns' non-excess
moments (Gaussian ``gamma4 = 3``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy.stats import norm

# Gaussian (non-excess) kurtosis. Structural default for the SE correction: at
# gamma4 = 3, gamma3 = 0 the Lo/Mertens SE collapses to the classic
# sqrt((1 + SR^2/2)/(n-1)) normal-returns Sharpe SE.
NORMAL_KURTOSIS = 3.0  # justify: Gaussian kurtosis, the null of the non-normality correction


def sharpe_standard_error(
    sr: float,
    n_obs: int,
    *,
    skew: float = 0.0,
    kurtosis: float = NORMAL_KURTOSIS,
) -> float:
    """Non-normality-adjusted Sharpe-ratio standard error (Lo 2002 / Mertens).

    ``SE(SR) = sqrt((1 - gamma3*SR + (gamma4-1)/4 * SR^2) / (n-1))`` where
    ``gamma3`` is the return skewness and ``gamma4`` the non-excess kurtosis. At
    ``gamma3 = 0``, ``gamma4 = 3`` this reduces to the i.i.d.-normal Sharpe SE
    ``sqrt((1 + SR^2/2)/(n-1))`` ([Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453)
    eq. for the normal case; the non-normal terms are the Mertens correction Lo
    cites). Negative skew and excess kurtosis both inflate the SE.

    Parameters
    ----------
    sr : float
        Observed Sharpe ratio in per-observation units (mean / std of the
        return series at its native frequency).
    n_obs : int
        Number of return observations (``>= 2``).
    skew : float, optional
        Return skewness ``gamma3`` (default ``0.0``, symmetric).
    kurtosis : float, optional
        Return non-excess kurtosis ``gamma4`` (default ``3.0``, Gaussian).

    Returns
    -------
    float
        The standard error of the Sharpe estimate.

    Raises
    ------
    ValueError
        If ``n_obs < 2``, or if the variance term is non-positive (an
        inadmissible skew/kurtosis/SR combination for the delta-method SE).
    """
    if n_obs < 2:  # justify: SE requires n-1 >= 1 degree of freedom
        raise ValueError(f"n_obs must be >= 2, got {n_obs}")
    variance_term = 1.0 - skew * sr + (kurtosis - 1.0) / 4.0 * sr * sr
    if variance_term <= 0.0:
        raise ValueError(
            f"non-positive Sharpe variance term ({variance_term:.6g}); "
            "the skew/kurtosis/SR combination is inadmissible for the delta-method SE"
        )
    return float(np.sqrt(variance_term / (n_obs - 1)))


def expected_max_sharpe(n_trials: int, sr_std: float) -> float:
    """Expected maximum Sharpe under ``N`` independent null trials (false-strategy theorem).

    Implements the [Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094)
    approximation ``E[max_N] ~ sigma_SR * ((1-g) * Z^-1[1 - 1/N] + g * Z^-1[1 - 1/(N*e)])``
    where ``g`` is the Euler-Mascheroni constant and ``sigma_SR`` the standard
    deviation of the Sharpe estimates across the ``N`` trials. It is the
    order-statistic expectation of the maximum of ``N`` i.i.d. standard-normal
    Sharpe estimates scaled by ``sigma_SR``; it grows with ``N``, so a larger
    trial family raises the benchmark the observed Sharpe must clear.

    A single trial (``N = 1``) carries no selection bias, so the benchmark is
    ``0`` (the null expected Sharpe of a zero-skill strategy); the ``N -> 1``
    limit of the theorem is singular (``Z^-1[0] = -inf``) and is handled as this
    no-deflation special case.

    Parameters
    ----------
    n_trials : int
        Effective number of independent trials ``N`` (``>= 1``).
    sr_std : float
        Cross-trial standard deviation of the Sharpe estimates (per-observation
        units); ``>= 0``.

    Returns
    -------
    float
        The deflated benchmark Sharpe (per-observation units).
    """
    if n_trials < 1:  # justify: at least one trial must exist to select from
        raise ValueError(f"n_trials must be >= 1, got {n_trials}")
    if sr_std < 0.0:
        raise ValueError(f"sr_std must be >= 0, got {sr_std}")
    if n_trials == 1:  # justify: single trial ⇒ no selection bias ⇒ zero benchmark
        return 0.0
    gamma = float(np.euler_gamma)
    n = float(n_trials)
    z1 = norm.ppf(1.0 - 1.0 / n)
    z2 = norm.ppf(1.0 - 1.0 / (n * np.e))
    return float(sr_std * ((1.0 - gamma) * z1 + gamma * z2))


@dataclass(frozen=True)
class DeflatedSharpe:
    """Deflated Sharpe Ratio result (Bailey & López de Prado 2014).

    Attributes
    ----------
    dsr : float
        The deflated Sharpe ratio in ``[0, 1]`` — the probability the strategy's
        true Sharpe exceeds the deflated benchmark (post-deflation p-value that
        the true Sharpe is positive).
    sr_observed : float
        The observed per-observation Sharpe.
    sr_benchmark : float
        The deflated (expected-max-under-null) benchmark Sharpe.
    se_sr : float
        The non-normality-adjusted Sharpe standard error.
    n_trials : int
        Effective number of independent trials used to deflate.
    skew : float
        Return skewness fed to the SE correction.
    kurtosis : float
        Return non-excess kurtosis fed to the SE correction.
    """

    dsr: float
    sr_observed: float
    sr_benchmark: float
    se_sr: float
    n_trials: int
    skew: float
    kurtosis: float


def deflated_sharpe_ratio(
    sr_observed: float,
    n_obs: int,
    n_trials: int,
    sr_std: float,
    *,
    skew: float = 0.0,
    kurtosis: float = NORMAL_KURTOSIS,
) -> DeflatedSharpe:
    """Deflated Sharpe Ratio (Bailey & López de Prado 2014).

    Combines the false-strategy-theorem benchmark (:func:`expected_max_sharpe`)
    and the non-normality-adjusted SE (:func:`sharpe_standard_error`) into
    ``DSR = Z[ (SR_obs - SR_benchmark) / SE(SR) ]`` — the probability, correcting
    for selection bias (``N`` trials), backtest overfitting (the higher
    benchmark), and non-normality (skew/kurtosis in the SE), that the strategy's
    true Sharpe is positive.

    All three Sharpe quantities (``sr_observed``, ``sr_std``, and the returned
    ``sr_benchmark``) must be in the same per-observation frequency as ``n_obs``.

    Parameters
    ----------
    sr_observed : float
        Observed per-observation Sharpe of the candidate strategy.
    n_obs : int
        Number of return observations backing ``sr_observed`` (``>= 2``).
    n_trials : int
        Effective number of independent trials in the selection family
        (``>= 1``); ``1`` performs no deflation.
    sr_std : float
        Cross-trial Sharpe standard deviation ``sigma_SR`` (per-observation
        units); ``>= 0``.
    skew : float, optional
        Return skewness (default ``0.0``).
    kurtosis : float, optional
        Return non-excess kurtosis (default ``3.0``, Gaussian).

    Returns
    -------
    DeflatedSharpe
        Frozen result carrying the DSR, its inputs, the benchmark, and the SE.
    """
    se = sharpe_standard_error(sr_observed, n_obs, skew=skew, kurtosis=kurtosis)
    benchmark = expected_max_sharpe(n_trials, sr_std)
    z = (sr_observed - benchmark) / se
    dsr = float(norm.cdf(z))
    return DeflatedSharpe(
        dsr=dsr,
        sr_observed=float(sr_observed),
        sr_benchmark=float(benchmark),
        se_sr=float(se),
        n_trials=int(n_trials),
        skew=float(skew),
        kurtosis=float(kurtosis),
    )


def sharpe_moments(returns: NDArray[np.float64]) -> tuple[float, float, float, float]:
    """Per-observation Sharpe and its plug-in moments from a return series.

    Convenience helper returning ``(sr, n, skew, kurtosis)`` for feeding
    :func:`deflated_sharpe_ratio`: the per-observation Sharpe ``mean/std`` (with
    the ``ddof=1`` sample std), the sample size, the sample skewness, and the
    sample non-excess kurtosis. Non-finite returns are dropped first.

    Parameters
    ----------
    returns : 1-D float array
        Per-bar return (arithmetic or log; the caller fixes the convention).

    Returns
    -------
    tuple[float, float, float, float]
        ``(sr, n_obs, skew, kurtosis)`` with ``kurtosis`` non-excess.

    Raises
    ------
    ValueError
        If fewer than two finite observations remain, or the std is zero.
    """
    r = np.asarray(returns, dtype=np.float64).ravel()
    r = r[np.isfinite(r)]
    n = r.size
    if n < 2:  # justify: sample std / higher moments need >= 2 observations
        raise ValueError(f"need >= 2 finite returns, got {n}")
    mean = float(r.mean())
    std = float(r.std(ddof=1))
    if std == 0.0:
        raise ValueError("return series has zero dispersion; Sharpe undefined")
    centered = r - mean
    # Population (biased) standardized moments — the plug-in estimands the
    # Lo/Mertens SE is written against.
    m2 = float((centered**2).mean())
    m3 = float((centered**3).mean())
    m4 = float((centered**4).mean())
    skew = m3 / m2**1.5
    kurtosis = m4 / m2**2
    return mean / std, float(n), skew, kurtosis
