"""Romano-Wolf stepwise (StepM) multiple-testing correction (ADR-0002(c) default).

Family-wise-error-rate control for the conditional-gross-edge admission scan: given
a family of one-sided hypotheses ``H0_c: mean gross edge in cell c ≤ 0``, the
stepdown max-t procedure of
[Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x) rejects the
largest-statistic cells while controlling the FWER, with per-hypothesis adjusted
p-values computed by the efficient step-down algorithm of
[Romano & Wolf 2016](https://doi.org/10.1016/j.spl.2016.02.012) (every ordered
hypothesis receives its monotone-enforced adjusted p-value, not only those rejected),
using a serial-dependence-preserving stationary block bootstrap
([Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870)) so the
joint null distribution respects the per-session return dependence (the ADR-0002(c)
stack).

Cells are subsets/weightings of the session dimension (conditioning cells that may
overlap); the bootstrap resamples **sessions** (block) and recomputes every cell's
studentized statistic jointly, so cross-cell dependence from overlapping membership
is captured. The screening/FWER **level** is the DEFERRED project-wide
``screening_error_rate_target`` — this estimator returns the FWER-adjusted
step-down p-values and the rejection set at a caller-supplied ``alpha``, but the
admission scan runs it DESCRIPTIVELY (reports adjusted p-values, certifies nothing)
until that level is set.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from skie_universe2.inference.bootstrap import stationary_bootstrap_indices


@dataclass(frozen=True)
class StepMResult:
    """Romano-Wolf StepM output over a family of one-sided cell hypotheses."""

    stat: NDArray[np.float64]  # observed studentized statistic per cell
    adjusted_pvalue: NDArray[np.float64]  # FWER step-down-adjusted one-sided p-value per cell
    rejected: NDArray[np.bool_]  # FWER-rejected at `alpha` (descriptive if level deferred)
    alpha: float
    n_bootstrap: int
    block_length: float


def _cell_stats(
    session_values: NDArray[np.float64],
    cell_masks: NDArray[np.bool_],
    min_n: int = 2,
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Per-cell mean and studentized one-sided statistic (H0: mean <= 0).

    ``t_c = mean_c / (sd_c / sqrt(n_c))``; cells with < ``min_n`` members get
    ``t = -inf`` (never rejected).
    """
    n_cells = cell_masks.shape[0]
    means = np.full(n_cells, np.nan, dtype=np.float64)
    stats = np.full(n_cells, -np.inf, dtype=np.float64)
    for c in range(n_cells):
        v = session_values[cell_masks[c]]
        if v.size < min_n:
            continue
        m = float(v.mean())
        sd = float(v.std(ddof=1))
        means[c] = m
        # Degenerate (sd==0) cell: +inf if the constant mean is positive (maximally
        # rejectable under H0: mean<=0), -inf if non-positive (maximally NON-rejectable,
        # matching the < min_n guard), 0.0 only for an exact-zero constant cell. Using
        # 0.0 for a constant-negative cell would let it outrank a finite-negative cell.
        if sd > 0:
            stats[c] = m / (sd / np.sqrt(v.size))
        else:
            stats[c] = np.inf if m > 0 else (-np.inf if m < 0 else 0.0)
    return means, stats


def romano_wolf_stepm(
    session_values: NDArray[np.float64],
    cell_masks: NDArray[np.bool_],
    *,
    block_length: float,
    rng: np.random.Generator,
    n_bootstrap: int,
    alpha: float = 0.05,
    min_n: int = 2,
) -> StepMResult:
    """Stepdown max-t FWER control over one-sided cell-edge hypotheses (Romano-Wolf 2005).

    Parameters
    ----------
    session_values : 1-D float array
        Per-session realized gross return of the expert (length = n_sessions).
    cell_masks : bool array, shape (n_cells, n_sessions)
        Membership of each session in each conditioning cell (cells may overlap).
    block_length : float
        Stationary-bootstrap expected block length (PW-selected on the session series).
    rng : numpy Generator
        Seeded RNG (reproducibility).
    n_bootstrap : int
        Bootstrap replications for the joint null max-t distribution.
    alpha : float
        FWER level for the ``rejected`` set. NOTE: the binding admission level is the
        DEFERRED project-wide ``screening_error_rate_target``; pass it descriptively.
    min_n : int
        Minimum cell membership for a testable statistic.

    Returns
    -------
    StepMResult
        Observed statistics, FWER step-down-adjusted p-values, and the rejection set.
    """
    x = np.asarray(session_values, dtype=np.float64)
    masks = np.asarray(cell_masks, dtype=bool)
    if masks.ndim != 2 or masks.shape[1] != x.size:
        raise ValueError(f"cell_masks must be (n_cells, {x.size}); got {masks.shape}")
    n_sessions = x.size
    n_cells = masks.shape[0]

    means, stats = _cell_stats(x, masks, min_n=min_n)

    # Bootstrap the CENTERED studentized statistics jointly (resample sessions with a
    # block bootstrap, recompute each cell's centered t on the resample).
    boot = np.full((n_bootstrap, n_cells), -np.inf, dtype=np.float64)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n_sessions, block_length=block_length, rng=rng)
        xb = x[idx]
        for c in range(n_cells):
            m = masks[c][idx]
            v = xb[m]
            if v.size < min_n or np.isnan(means[c]):
                continue
            sd = float(v.std(ddof=1))
            if sd > 0:
                boot[b, c] = (float(v.mean()) - means[c]) / (sd / np.sqrt(v.size))

    # Step-down (Romano-Wolf 2016 efficient adjusted-p algorithm): order cells by
    # observed stat descending; at position j the step-down p-value for cell c is
    # P*(max centered-bootstrap-stat over the STILL-UNTESTED suffix {j, j+1, ...} >=
    # stat_c), enforced monotone non-decreasing along the order. EVERY cell receives
    # its adjusted p-value — the loop does NOT break at the first non-rejection (that
    # would leave lower-ranked cells, including the pre-registered primary, at the 1.0
    # initializer instead of their true stepdown-adjusted value).
    order = np.argsort(-stats)
    adjusted = np.ones(n_cells, dtype=np.float64)
    prev_p = 0.0
    for j, c in enumerate(order):
        active = order[j:]  # this cell + all lower-stat cells (the untested suffix)
        active_boot_max = boot[:, active].max(axis=1)
        p = (1.0 + np.sum(active_boot_max >= stats[c])) / (1.0 + n_bootstrap)
        p = max(p, prev_p)  # monotone non-decreasing along the step-down order
        adjusted[c] = min(p, 1.0)
        prev_p = adjusted[c]

    # Rejection with step-down consonance: walk the order and reject until the first
    # non-rejection (a cell rejects only if all higher-stat cells rejected).
    rejected = np.zeros(n_cells, dtype=bool)
    for c in order:
        if adjusted[c] <= alpha and np.isfinite(stats[c]):
            rejected[c] = True
        else:
            break

    return StepMResult(
        stat=stats,
        adjusted_pvalue=adjusted,
        rejected=rejected,
        alpha=alpha,
        n_bootstrap=n_bootstrap,
        block_length=float(block_length),
    )
