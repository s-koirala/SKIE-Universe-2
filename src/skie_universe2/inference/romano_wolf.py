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

    adjusted, rejected = _stepdown_adjust(stats, boot, alpha=alpha, n_bootstrap=n_bootstrap)

    return StepMResult(
        stat=stats,
        adjusted_pvalue=adjusted,
        rejected=rejected,
        alpha=alpha,
        n_bootstrap=n_bootstrap,
        block_length=float(block_length),
    )


def _stepdown_adjust(
    stats: NDArray[np.float64],
    boot: NDArray[np.float64],
    *,
    alpha: float,
    n_bootstrap: int,
) -> tuple[NDArray[np.float64], NDArray[np.bool_]]:
    """Shared Romano-Wolf 2016 efficient step-down adjusted-p + consonance walk.

    Extracted verbatim from the two variants (audit CODE-1-1; behavior pinned
    by the existing masked-variant and panel test suites, including the k=1
    masked/panel equivalence test). Order hypotheses by observed stat
    descending; at position j the step-down p-value for hypothesis c is
    P*(max centered-bootstrap-stat over the STILL-UNTESTED suffix
    {j, j+1, ...} >= stat_c), enforced monotone non-decreasing along the
    order. EVERY hypothesis receives its adjusted p-value — the loop does NOT
    break at the first non-rejection (that would leave lower-ranked
    hypotheses, including a pre-registered primary, at the 1.0 initializer).
    Rejection then walks the order with step-down consonance: reject until
    the first non-rejection.
    """
    n_hyp = stats.shape[0]
    order = np.argsort(-stats)
    adjusted = np.ones(n_hyp, dtype=np.float64)
    prev_p = 0.0
    for j, c in enumerate(order):
        active = order[j:]  # this hypothesis + all lower-stat ones (untested suffix)
        active_boot_max = boot[:, active].max(axis=1)
        p = (1.0 + np.sum(active_boot_max >= stats[c])) / (1.0 + n_bootstrap)
        p = max(p, prev_p)  # monotone non-decreasing along the step-down order
        adjusted[c] = min(p, 1.0)
        prev_p = adjusted[c]

    rejected = np.zeros(n_hyp, dtype=bool)
    for c in order:
        if adjusted[c] <= alpha and np.isfinite(stats[c]):
            rejected[c] = True
        else:
            break
    return adjusted, rejected


def romano_wolf_stepm_panel(
    panel: NDArray[np.float64],
    *,
    block_length: float,
    rng: np.random.Generator,
    n_bootstrap: int,
    alpha: float = 0.05,
    min_n: int = 2,
) -> StepMResult:
    """Stepdown max-t FWER control over a PANEL of one-sided mean hypotheses.

    Panel counterpart of :func:`romano_wolf_stepm` (added 2026-07-19 for the
    VERDICT-1 protocol; append-only — the masked variant above is untouched):
    the family members are K distinct per-session value series over the SAME
    session axis (e.g. the four registered Kelly-arm marginal-growth-delta
    streams of one verdict candidate), rather than masked subsets of one
    series. H0_k: ``E[panel[:, k]] <= 0``; one-sided studentized
    ``t_k = mean_k / (sd_k / sqrt(t))`` with the identical degenerate-column
    conventions as ``_cell_stats``; the joint null resamples ROWS with the
    stationary bootstrap (cross-column dependence preserved — one index draw
    per replicate applied to every column); the adjusted p-values use the
    same Romano-Wolf 2016 efficient step-down algorithm and consonant
    rejection walk as the masked variant, verbatim.

    Parameters mirror :func:`romano_wolf_stepm`; ``panel`` has shape
    ``(n_sessions, k)``. The panel must be fully finite (raises otherwise —
    a partially-observed family is a different estimand), so every column
    shares the same ``n_sessions`` row count and ``min_n`` binds ONCE at
    the panel level (``n_sessions >= min_n`` enforced below); there is no
    reachable per-column membership path in this variant (audit
    CODE-1-3/QUANT-1-7 docstring correction). A degenerate (sd == 0)
    column still gets the same ±inf convention as the masked variant.
    """
    x = np.asarray(panel, dtype=np.float64)
    if x.ndim != 2:
        raise ValueError(f"panel must be 2-D (n_sessions, k); got ndim={x.ndim}")
    if not np.isfinite(x).all():
        raise ValueError("panel contains non-finite values")
    n_sessions, n_cols = x.shape
    if n_sessions < min_n:
        raise ValueError(f"need at least {min_n} sessions, got {n_sessions}")

    means = np.full(n_cols, np.nan, dtype=np.float64)
    stats = np.full(n_cols, -np.inf, dtype=np.float64)
    for c in range(n_cols):
        v = x[:, c]
        m = float(v.mean())
        sd = float(v.std(ddof=1))
        means[c] = m
        if sd > 0:
            stats[c] = m / (sd / np.sqrt(v.size))
        else:
            stats[c] = np.inf if m > 0 else (-np.inf if m < 0 else 0.0)

    boot = np.full((n_bootstrap, n_cols), -np.inf, dtype=np.float64)
    for b in range(n_bootstrap):
        idx = stationary_bootstrap_indices(n_sessions, block_length=block_length, rng=rng)
        xb = x[idx]
        for c in range(n_cols):
            v = xb[:, c]
            sd = float(v.std(ddof=1))
            if sd > 0:
                boot[b, c] = (float(v.mean()) - means[c]) / (sd / np.sqrt(v.size))

    adjusted, rejected = _stepdown_adjust(stats, boot, alpha=alpha, n_bootstrap=n_bootstrap)

    return StepMResult(
        stat=stats,
        adjusted_pvalue=adjusted,
        rejected=rejected,
        alpha=alpha,
        n_bootstrap=n_bootstrap,
        block_length=float(block_length),
    )
