"""Hansen (2005) test for Superior Predictive Ability (SPA).

Frozen reference estimator for the ADR-0007 Decision 3 confirmation-ladder
inference: does ANY candidate in a family outperform a benchmark, with the
multiple-comparison null handled by bootstrap and Hansen's sample-dependent
recentering removing the Reality Check's sensitivity to poor and irrelevant
alternatives (Hansen 2005, J. Bus. Econ. Stat. 23(4):365-380,
https://doi.org/10.1198/073500105000000063; White 2000 Reality Check,
https://doi.org/10.1111/1468-0262.00152, recovered as the "upper" variant).

Inputs are PERFORMANCE differentials ``d[t, k] = candidate_k performance −
benchmark performance`` (positive mean = candidate better; in this project
the performance currency is per-window/per-session geometric log-wealth
growth, ADR-0013). Under H0: ``E[d_k] <= 0`` for all k.

Statistic (studentized, Hansen's T^SPA form): ``T = max_k sqrt(t) *
mean(d_k) / omega_k`` with ``omega_k^2`` the stationary-bootstrap kernel
estimate of the long-run variance of ``sqrt(t) * mean(d_k)``
(``omega^2 = gamma_0 + 2 * sum_i kappa(i) * gamma_i`` with
``kappa(i) = (1 - i/t)(1-p)^i + (i/t)(1-p)^(t-i)``, ``p = 1/block_length`` —
the closed form of the vetted reference implementation
``arch.bootstrap.SPA._compute_variance``, verified term-for-term in tests,
and consistent with Hansen's kernel-weighted long-run variance; exact
equation numbers in the paywalled original are not independently verified
and are not cited here). ``studentize=False`` gives the unstudentized
max-mean variant (the statistic form used by the cross-validation
benchmark test; note arch's own ``studentize`` DEFAULT is True).

DISCLOSED DEVIATION (audit QUANT-1-1): Hansen defines T^SPA with an outer
floor at zero, ``max{max_k ..., 0}``; this implementation and the arch
reference both use the UNFLOORED max. The bootstrap comparison
``T*_b > T`` is applied under the same transform on both sides, so
p-values are identical whenever any candidate mean is positive; when ALL
candidate means are negative the unfloored statistic is negative and the
resulting p-value is (weakly) LARGER than the floored form's — i.e. the
deviation is in the non-rejecting, conservative direction and cannot
manufacture an admission.

Null distribution: stationary bootstrap (Politis-Romano 1994) with JOINT row
resampling across candidates (one index draw per replicate applied to every
column — cross-candidate dependence preserved), reusing this project's
frozen :func:`skie_universe2.inference.bootstrap.stationary_bootstrap_indices`.
Three recenterings, three p-values (Hansen 2005; ordering
``lower <= consistent <= upper``):

- ``lower``      g_l(mean_k) = max(mean_k, 0) — negative-mean candidates keep
  their drift (their bootstrap max contribution is suppressed): lower bound.
- ``consistent`` g_c(mean_k) = mean_k * 1{mean_k >= -sqrt((omega_k^2/t) *
  2 log log t)} — only candidates NOT rejected by the law-of-iterated-
  logarithm band are recentred; deeply poor candidates cannot inflate the
  null. Hansen's recommended p-value; the PRIMARY read.
- ``upper``      g_u(mean_k) = mean_k — every candidate recentred to the
  null boundary: White's Reality Check analog, the conservative bound.

``p_i = (1/B) * #{b : T*_b(i) > T}`` with the same strict inequality as the
reference implementation.

The estimator is PURE (seeded Generator in, deterministic out) and consumes
no project state; every verdict-tier use passes the level read from
``config/multipletest_family.yaml`` downstream, never a constant here.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from skie_universe2.inference.bootstrap import stationary_bootstrap_indices

# justify: structural — log(log(t)) needs t > e; the smallest t with a
# defined LIL band and ddof-safe moments.
_MIN_OBS = 4
_EPS = 1e-12  # justify: structural div-by-zero guard, not a tunable threshold
_NDIM_PANEL = 2  # justify: structural — the (t, k) panel shape contract


@dataclass(frozen=True)
class SPAResult:
    """Outcome of the Hansen (2005) SPA test over one candidate family."""

    statistic: float
    p_value_lower: float
    p_value_consistent: float
    p_value_upper: float
    studentized: bool
    means: NDArray[np.float64]
    omega2: NDArray[np.float64]
    consistent_valid: NDArray[np.bool_]
    n_obs: int
    n_models: int
    n_bootstrap: int
    block_length: float


def sb_kernel_variance(diffs: NDArray[np.float64], block_length: float) -> NDArray[np.float64]:
    """Stationary-bootstrap kernel long-run variance per column (Hansen 2005).

    ``omega^2_k = gamma_0(k) + 2 * sum_{i=1}^{t-1} kappa(i) gamma_i(k)`` with
    ``kappa(i) = (1 - i/t)(1-p)^i + (i/t)(1-p)^(t-i)`` and
    ``p = 1/block_length`` — term-for-term the reference implementation's
    closed form (arch ``SPA._compute_variance``, non-nested branch).
    Floored at 0 (a kernel estimate can go slightly negative in finite
    samples; a negative variance is not interpretable).
    """
    d = np.asarray(diffs, dtype=np.float64)
    if d.ndim != _NDIM_PANEL:
        raise ValueError(f"diffs must be 2-D (t, k); got ndim={d.ndim}")
    if d.shape[0] < 1:
        raise ValueError("diffs must contain at least one row")
    if not np.isfinite(d).all():
        raise ValueError("diffs contains non-finite values")
    if float(block_length) < 1.0:
        raise ValueError(f"block_length must be >= 1, got {block_length}")
    t = d.shape[0]
    demeaned = d - d.mean(axis=0)
    p = 1.0 / float(block_length)
    variances = np.sum(demeaned**2, axis=0) / t
    for i in range(1, t):
        kappa = (1.0 - i / t) * (1.0 - p) ** i + (i / t) * (1.0 - p) ** (t - i)
        variances = (
            variances + 2.0 * kappa * np.sum(demeaned[: t - i, :] * demeaned[i:, :], axis=0) / t
        )
    return np.maximum(variances, 0.0)


def hansen_spa(
    diffs: NDArray[np.float64],
    *,
    block_length: float,
    rng: np.random.Generator,
    n_bootstrap: int,
    studentize: bool = True,
) -> SPAResult:
    """Hansen (2005) SPA test on a (t, k) performance-differential panel.

    Parameters
    ----------
    diffs
        Shape (t, k): per-period performance differentials, candidate minus
        benchmark (positive = candidate better). NaN/inf rejected; columns
        with (near-)zero variance rejected (a constant differential has no
        sampling distribution to test).
    block_length
        Stationary-bootstrap expected block length (caller selects it via
        ``politis_white_block_length`` per project convention; >= 1).
    rng
        Seeded Generator — deterministic output for a fixed seed.
    n_bootstrap
        Number of bootstrap replicates B (>= 1).
    studentize
        True (default): Hansen's studentized T^SPA (primary; matches
        arch's own default). False: the unstudentized max-mean variant
        (used by the cross-validation benchmark test).
    """
    d = np.asarray(diffs, dtype=np.float64)
    if d.ndim != _NDIM_PANEL:
        raise ValueError(f"diffs must be 2-D (t, k); got ndim={d.ndim}")
    t, k = d.shape
    if t < _MIN_OBS:
        raise ValueError(f"need at least {_MIN_OBS} observations, got {t}")
    if k < 1:
        raise ValueError("need at least one candidate column")
    if not np.isfinite(d).all():
        raise ValueError("diffs contains non-finite values")
    if float(block_length) < 1.0:
        raise ValueError(f"block_length must be >= 1, got {block_length}")
    if n_bootstrap < 1:
        raise ValueError(f"n_bootstrap must be >= 1, got {n_bootstrap}")
    col_sd = d.std(axis=0, ddof=1)
    if np.any(col_sd <= _EPS):
        bad = np.nonzero(col_sd <= _EPS)[0].tolist()
        raise ValueError(
            f"degenerate (near-constant) differential column(s) {bad}: a constant "
            "differential has no sampling distribution; drop or fix upstream"
        )

    means = d.mean(axis=0)
    omega2 = sb_kernel_variance(d, block_length)
    scale = np.sqrt(np.maximum(omega2, _EPS)) if studentize else np.ones(k)

    # Hansen's law-of-iterated-logarithm validity band for the consistent
    # recentering: candidates with mean below -sqrt((omega^2/t) 2 log log t)
    # are NOT recentred (their negative drift suppresses them in the null).
    threshold = -np.sqrt((omega2 / t) * 2.0 * np.log(np.log(t)))
    consistent_valid = means >= threshold

    g_lower = np.maximum(means, 0.0)
    g_consistent = np.where(consistent_valid, means, 0.0)
    g_upper = means
    recenterings = (g_lower, g_consistent, g_upper)

    root_t = np.sqrt(t)
    statistic = float(np.max(root_t * means / scale))

    exceed = np.zeros(3, dtype=np.int64)
    for _ in range(n_bootstrap):
        idx = stationary_bootstrap_indices(t, block_length=float(block_length), rng=rng)
        star_means = d[idx].mean(axis=0)
        for j, g in enumerate(recenterings):
            t_star = float(np.max(root_t * (star_means - g) / scale))
            if t_star > statistic:
                exceed[j] += 1

    p_lower, p_consistent, p_upper = (exceed / float(n_bootstrap)).tolist()
    return SPAResult(
        statistic=statistic,
        p_value_lower=float(p_lower),
        p_value_consistent=float(p_consistent),
        p_value_upper=float(p_upper),
        studentized=studentize,
        means=means,
        omega2=omega2,
        consistent_valid=consistent_valid,
        n_obs=t,
        n_models=k,
        n_bootstrap=n_bootstrap,
        block_length=float(block_length),
    )
