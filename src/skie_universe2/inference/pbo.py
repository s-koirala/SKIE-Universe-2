"""Probability of Backtest Overfitting (PBO) via CSCV (ADR-0007 / ADR-0008).

Reference implementation of the Combinatorially-Symmetric Cross-Validation
(CSCV) estimator of the Probability of Backtest Overfitting, per
[Bailey, Borwein, López de Prado & Zhu 2016, *The probability of backtest
overfitting*, J. Comput. Finance 20(4):39-69](https://doi.org/10.21314/JCF.2016.322)
(DOI Crossref-verified in-repo, CLAUDE.md `P1-2.0-CITE-DOI-VERIFY-PBO-2017`).

The confirmation-tier ``PBO exhibit`` mandated non-waivable by
[ADR-0007](../../../docs/decisions/ADR-0007-two-tier-discovery-pipeline.md)
Decision 3 and required as an overfitting-detection integrity control by
[ADR-0008](../../../docs/decisions/ADR-0008-integrity-non-negotiables.md).
The estimator consumes the trial-level performance matrix reconstructed from the
ADR-0008 Decision 6 trial register's return-series pointers.

Method (CSCV, Bailey et al. 2016 §3)
------------------------------------
Input is a performance matrix ``M`` of shape ``(T, N)`` — per-period performance
(returns or another additive per-period statistic) of each of ``N`` strategy
configurations over ``T`` observations. The rows are partitioned into ``S``
(even) disjoint, contiguous, equal-size submatrices. For each of the
``C(S, S/2)`` ways of choosing ``S/2`` submatrices as the in-sample (IS) set, the
complementary ``S/2`` form the out-of-sample (OOS) set. On IS the ``N`` configs
are ranked and the IS-best ``n*`` is selected; ``n*``'s performance rank on OOS
gives the relative rank ``ω_c = rank(n*) / (N + 1) ∈ (0, 1)`` and the logit
``λ_c = ln(ω_c / (1 − ω_c))``. The PBO estimate is the fraction of combinations
whose IS-best lands below the OOS median — ``PBO = P(λ_c < 0)`` — i.e. the
estimated probability that an IS-selected configuration under-performs OOS.

``ω_c`` is strictly interior (``rank(n*) ∈ [1, N]`` including average ranks under
ties), so every ``λ_c`` is finite; no clipping is applied.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from itertools import combinations

import numpy as np
from numpy.typing import NDArray

# Compute guard on C(S, S/2), NOT an analysis parameter: each combination costs
# O(T·N), so an accidentally large S would blow up silently. C(20,10)=184756
# brackets the Bailey et al. 2016 reference S=16 (C(16,8)=12870) with ample
# headroom; callers who deliberately want a finer split raise it explicitly.
# justify: operational compute cap, not a tunable analysis threshold.
DEFAULT_MAX_COMBINATIONS = math.comb(20, 10)


def _sharpe(sub: NDArray[np.float64]) -> NDArray[np.float64]:
    """Per-column Sharpe proxy ``mean / std`` (ddof=1) of a submatrix.

    A zero-variance column (degenerate constant series) falls back to its mean,
    so ranking never yields NaN/inf; this is an edge-case guard for pathological
    inputs, not a modelling choice (return data is non-degenerate per block).
    """
    mean = sub.mean(axis=0)
    std = sub.std(axis=0, ddof=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(std > 0.0, mean / std, mean)


def _mean(sub: NDArray[np.float64]) -> NDArray[np.float64]:
    """Per-column mean performance of a submatrix."""
    return sub.mean(axis=0)


_METRICS: dict[str, Callable[[NDArray[np.float64]], NDArray[np.float64]]] = {
    "sharpe": _sharpe,
    "mean": _mean,
}


@dataclass(frozen=True)
class PBOResult:
    """CSCV Probability-of-Backtest-Overfitting result (Bailey et al. 2016)."""

    pbo: float
    logits: NDArray[np.float64]  # λ_c per combination
    relative_ranks: NDArray[np.float64]  # ω_c ∈ (0,1) per combination
    selected_configs: NDArray[np.int64]  # IS-best n* per combination
    n_combinations: int
    s_splits: int


def _average_rank(scores: NDArray[np.float64], target: int) -> float:
    """1-indexed average (tie-corrected) rank of ``scores[target]`` among *scores*.

    Ascending: the smallest value has rank 1, the largest rank ``N``. Ties share
    the mean of the ranks they span, so the result lies strictly in ``[1, N]``.
    """
    v = scores[target]
    less = int(np.count_nonzero(scores < v))
    equal = int(np.count_nonzero(scores == v))
    return less + (equal + 1) / 2.0


def probability_of_backtest_overfitting(
    performance: NDArray[np.float64],
    *,
    s_splits: int = 16,
    metric: str = "sharpe",
    score_fn: Callable[[NDArray[np.float64]], NDArray[np.float64]] | None = None,
    max_combinations: int = DEFAULT_MAX_COMBINATIONS,
) -> PBOResult:
    """Estimate PBO by Combinatorially-Symmetric Cross-Validation (Bailey et al. 2016).

    Parameters
    ----------
    performance : 2-D float array, shape ``(T, N)``
        Per-period performance of ``N`` strategy configurations over ``T``
        observations (columns are configs, rows are time). Rows must be
        time-ordered; blocks are formed by contiguous slicing.
    s_splits : int, default 16
        Number ``S`` of disjoint contiguous submatrices; must be even and ``>= 2``
        (Bailey et al. 2016 use ``S = 16``). ``C(S, S/2)`` combinations are
        enumerated. Trailing ``T mod S`` rows that do not fill an equal-size block
        are dropped (documented; keeps IS/OOS balanced as the method requires).
    metric : {"sharpe", "mean"}, default "sharpe"
        Built-in per-column ranking statistic. ``"sharpe"`` is ``mean/std``
        (ddof=1); ``"mean"`` ranks on mean performance. Ignored when *score_fn*
        is supplied.
    score_fn : callable, optional
        Custom scorer mapping a submatrix ``(rows, N)`` to a length-``N`` score
        vector (higher is better). Overrides *metric*.
    max_combinations : int, default ``C(20,10)``
        Compute guard: raise ``ValueError`` if ``C(S, S/2)`` exceeds it. Raise the
        cap deliberately for a finer split rather than removing it.

    Returns
    -------
    PBOResult
        ``pbo`` (fraction of combinations with ``λ_c < 0``), the per-combination
        ``logits`` and ``relative_ranks`` (``ω_c``), the IS-best ``selected_configs``
        (``n*``), ``n_combinations`` = ``C(S, S/2)``, and ``s_splits``.

    Raises
    ------
    ValueError
        If *performance* is not 2-D, ``N < 2``, ``S`` is odd or ``< 2``, a block
        would hold fewer than 2 rows (Sharpe needs ddof=1 variance), or
        ``C(S, S/2) > max_combinations``.
    """
    m = np.asarray(performance, dtype=np.float64)
    if m.ndim != 2:
        raise ValueError(f"performance must be 2-D (T, N), got {m.ndim}-D")
    t_obs, n_configs = m.shape
    if n_configs < 2:
        raise ValueError(f"need >= 2 configurations to rank, got N={n_configs}")
    if s_splits < 2 or s_splits % 2 != 0:
        raise ValueError(f"s_splits must be even and >= 2, got {s_splits}")

    if score_fn is None:
        if metric not in _METRICS:
            raise ValueError(f"metric must be one of {sorted(_METRICS)}, got {metric!r}")
        score_fn = _METRICS[metric]

    n_comb = math.comb(s_splits, s_splits // 2)
    if n_comb > max_combinations:
        raise ValueError(
            f"C({s_splits}, {s_splits // 2}) = {n_comb} exceeds max_combinations="
            f"{max_combinations}; raise max_combinations to proceed"
        )

    block_len = t_obs // s_splits
    if block_len < 2:
        raise ValueError(
            f"each of S={s_splits} blocks needs >= 2 rows (Sharpe ddof=1); "
            f"T={t_obs} gives block_len={block_len}"
        )

    # Contiguous equal-size blocks; trailing T mod S rows dropped (§3 balance).
    block_rows = [np.arange(s * block_len, (s + 1) * block_len) for s in range(s_splits)]

    all_blocks = frozenset(range(s_splits))
    logits = np.empty(n_comb, dtype=np.float64)
    rel_ranks = np.empty(n_comb, dtype=np.float64)
    selected = np.empty(n_comb, dtype=np.int64)

    for c, is_blocks in enumerate(combinations(range(s_splits), s_splits // 2)):
        oos_blocks = sorted(all_blocks - set(is_blocks))
        is_idx = np.concatenate([block_rows[b] for b in is_blocks])
        oos_idx = np.concatenate([block_rows[b] for b in oos_blocks])

        is_scores = score_fn(m[is_idx])
        oos_scores = score_fn(m[oos_idx])
        n_star = int(np.argmax(is_scores))  # ties → first; documented

        omega = _average_rank(oos_scores, n_star) / (n_configs + 1)
        selected[c] = n_star
        rel_ranks[c] = omega
        logits[c] = math.log(omega / (1.0 - omega))

    pbo = float(np.mean(logits < 0.0))
    return PBOResult(
        pbo=pbo,
        logits=logits,
        relative_ranks=rel_ranks,
        selected_configs=selected,
        n_combinations=n_comb,
        s_splits=s_splits,
    )
