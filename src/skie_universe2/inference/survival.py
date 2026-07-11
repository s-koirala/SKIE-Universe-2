"""Kaplan-Meier survival estimation for dwell/latency distributions.

H900 design.md §8: median dwell per window via Kaplan-Meier
(right-censoring at window edges) with Greenwood-based CI; pooled
median via stationary bootstrap over spell sequences with
Politis-White automatic block length.

References
----------

- Kaplan, E. L. & Meier, P. 1958. "Nonparametric Estimation from
  Incomplete Observations". *JASA* 53(282): 457-481.
  https://doi.org/10.1080/01621459.1958.10501452
- Greenwood, M. 1926. "The natural duration of cancer". *Reports on
  Public Health and Medical Subjects* 33: 1-26. HMSO. (Greenwood
  variance formula.)
- Brookmeyer, R. & Crowley, J. 1982. "A Confidence Interval for the
  Median Survival Time". *Biometrics* 38(1): 29-41.
  https://doi.org/10.2307/2530286 — median CI by inverting the
  pointwise CI of S(t) at 1/2.
- Politis, D. N. & Romano, J. P. 1994. *JASA* 89:1303-1313 (stationary
  bootstrap); Politis & White 2004 / Patton, Politis & White 2009
  (automatic block length) — via the ported
  :mod:`skie_universe2.inference.bootstrap`.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.stats import norm

from skie_universe2.inference.bootstrap import (
    BlockLengthSelection,
    choose_block_length,
    stationary_bootstrap_indices,
)

# Median survival probability level — definitional, not tunable.
_MEDIAN_LEVEL = 0.5  # justify: definition of the median (S(t) = 1/2)


@dataclass(frozen=True)
class KaplanMeierFit:
    """KM estimate on right-censored durations.

    ``times`` are the distinct event times; ``survival`` is S(t) just
    after each event time; ``greenwood_var`` is the Greenwood variance
    of S(t); ``at_risk``/``n_events`` per event time.
    """

    times: np.ndarray
    survival: np.ndarray
    greenwood_var: np.ndarray
    at_risk: np.ndarray
    n_events: np.ndarray
    n_observations: int
    n_uncensored: int


def km_fit(durations: np.ndarray, events: np.ndarray) -> KaplanMeierFit:
    """Kaplan-Meier product-limit estimate (Kaplan & Meier 1958)."""
    d = np.asarray(durations, dtype=np.float64)
    e = np.asarray(events, dtype=bool)
    if d.shape != e.shape or d.ndim != 1:
        raise ValueError("durations and events must be aligned 1-D arrays.")
    if d.size == 0:
        raise ValueError("no observations.")
    if np.any(d <= 0):
        raise ValueError("durations must be strictly positive.")

    event_times = np.unique(d[e])
    survival = np.empty(event_times.size, dtype=np.float64)
    gw_var = np.empty(event_times.size, dtype=np.float64)
    at_risk = np.empty(event_times.size, dtype=np.int64)
    n_ev = np.empty(event_times.size, dtype=np.int64)

    s = 1.0
    gw_sum = 0.0  # running sum of d_i / (n_i (n_i - d_i))
    for k, t in enumerate(event_times):
        n_i = int(np.sum(d >= t))
        d_i = int(np.sum((d == t) & e))
        s *= 1.0 - d_i / n_i
        if n_i > d_i:
            gw_sum += d_i / (n_i * (n_i - d_i))
            gw_var[k] = s * s * gw_sum
        else:
            gw_var[k] = np.nan  # S hits 0; Greenwood undefined
        survival[k] = s
        at_risk[k] = n_i
        n_ev[k] = d_i
    return KaplanMeierFit(
        times=event_times,
        survival=survival,
        greenwood_var=gw_var,
        at_risk=at_risk,
        n_events=n_ev,
        n_observations=int(d.size),
        n_uncensored=int(e.sum()),
    )


def km_median(fit: KaplanMeierFit) -> float:
    """KM median: smallest event time with S(t) <= 1/2 (NaN if never)."""
    idx = np.flatnonzero(fit.survival <= _MEDIAN_LEVEL)
    if idx.size == 0:
        return float("nan")
    return float(fit.times[idx[0]])


@dataclass(frozen=True)
class MedianEstimate:
    """Median with a 2-sided CI (method recorded by the caller)."""

    median: float
    ci_low: float
    ci_high: float
    alpha: float
    n_observations: int
    n_uncensored: int


def km_median_greenwood_ci(
    durations: np.ndarray,
    events: np.ndarray,
    *,
    alpha: float,
) -> MedianEstimate:
    """KM median with a Brookmeyer-Crowley (1982) CI.

    The CI is the set of times t whose pointwise Greenwood
    (linear-scale) 1-alpha band for S(t) contains 1/2 (i.e. where
    S(t) = 1/2 cannot be rejected). S is non-increasing, so:

    - lower bound = first event time where the LOWER band
      S(t) - z*se(t) falls to <= 1/2 (before that, S(t) is credibly
      above 1/2, so the median is credibly later);
    - upper bound = first event time where the UPPER band
      S(t) + z*se(t) falls below 1/2 (from there on, S(t) is credibly
      below 1/2, so the median has credibly passed). Unattained upper
      bound => +inf; degenerate lower bound => first event time.
    """
    fit = km_fit(durations, events)
    z = float(norm.ppf(1.0 - alpha / 2.0))
    se = np.sqrt(np.where(np.isnan(fit.greenwood_var), 0.0, fit.greenwood_var))
    upper_band = fit.survival + z * se
    lower_band = fit.survival - z * se

    med = km_median(fit)
    lo_idx = np.flatnonzero(lower_band <= _MEDIAN_LEVEL)
    hi_idx = np.flatnonzero(upper_band < _MEDIAN_LEVEL)
    ci_low = float(fit.times[lo_idx[0]]) if lo_idx.size else float(fit.times[0])
    ci_high = float(fit.times[hi_idx[0]]) if hi_idx.size else float("inf")
    return MedianEstimate(
        median=med,
        ci_low=ci_low,
        ci_high=ci_high,
        alpha=alpha,
        n_observations=fit.n_observations,
        n_uncensored=fit.n_uncensored,
    )


@dataclass(frozen=True)
class PooledMedianBootstrap:
    """Pooled KM median with a stationary-bootstrap percentile CI."""

    median: float
    ci_low: float
    ci_high: float
    alpha: float
    n_bootstrap: int
    n_undefined_replicates: int
    block_selection: BlockLengthSelection
    n_observations: int
    n_uncensored: int


def pooled_km_median_stationary_bootstrap(
    durations: np.ndarray,
    events: np.ndarray,
    *,
    alpha: float,
    n_bootstrap: int,
    rng: np.random.Generator,
    block_length: float | None = None,
) -> PooledMedianBootstrap:
    """Pooled-median CI via stationary bootstrap over the spell sequence.

    The (duration, event) pairs are resampled JOINTLY (identical index
    draws) in their chronological order with the Politis-Romano 1994
    stationary bootstrap; block length auto-selected on the duration
    sequence per Politis-White 2004 / PPW 2009 unless supplied. Each
    replicate re-estimates the KM median; the CI is the percentile
    interval (Efron & Tibshirani 1993 §13). Replicates whose KM curve
    never reaches 1/2 (undefined median) are dropped and counted.
    """
    d = np.asarray(durations, dtype=np.float64)
    e = np.asarray(events, dtype=bool)
    if d.shape != e.shape or d.ndim != 1:
        raise ValueError("durations and events must be aligned 1-D arrays.")
    if block_length is None:
        selection = choose_block_length(d, bootstrap_type="stationary")
    else:
        selection = BlockLengthSelection(
            method="fixed",
            block_length=float(block_length),
            bootstrap_type="stationary",
            notes="caller-specified fixed block length.",
        )
    point = km_median(km_fit(d, e))
    medians = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(d.size, block_length=selection.block_length, rng=rng)
        medians[b] = km_median(km_fit(d[idx], e[idx]))
    ok = np.isfinite(medians)
    n_undef = int(np.sum(~ok))
    if not np.any(ok):
        raise RuntimeError("all bootstrap replicates had undefined KM medians.")
    lo, hi = np.percentile(medians[ok], [100 * alpha / 2.0, 100 * (1 - alpha / 2.0)])
    return PooledMedianBootstrap(
        median=float(point),
        ci_low=float(lo),
        ci_high=float(hi),
        alpha=alpha,
        n_bootstrap=n_bootstrap,
        n_undefined_replicates=n_undef,
        block_selection=selection,
        n_observations=int(d.size),
        n_uncensored=int(e.sum()),
    )
