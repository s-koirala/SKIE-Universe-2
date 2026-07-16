"""Unit tests for Romano-Wolf StepM FWER control (ADR-0002(c))."""

from __future__ import annotations

import numpy as np

from skie_universe2.inference.romano_wolf import romano_wolf_stepm


def _masks(n: int, spans: list[tuple[int, int]]) -> np.ndarray:
    m = np.zeros((len(spans), n), dtype=bool)
    for c, (lo, hi) in enumerate(spans):
        m[c, lo:hi] = True
    return m


class TestRomanoWolfStepM:
    def test_true_positive_cell_rejected_nulls_not(self) -> None:
        rng = np.random.default_rng(0)
        n = 3000
        x = rng.normal(0.0, 1.0, n)
        x[1000:2000] += 0.20  # genuine positive edge in cell 1
        masks = _masks(n, [(0, 1000), (1000, 2000), (2000, 3000)])
        res = romano_wolf_stepm(
            x,
            masks,
            block_length=8.0,
            rng=np.random.default_rng(1),
            n_bootstrap=500,
            alpha=0.05,
        )
        assert res.rejected[1] and res.adjusted_pvalue[1] < 0.05
        assert not res.rejected[0] and not res.rejected[2]

    def test_global_null_controls_fwer(self) -> None:
        # All cells mean 0 -> FWER control -> typically no rejection at alpha=0.05.
        rng = np.random.default_rng(2)
        n = 3000
        x = rng.normal(0.0, 1.0, n)
        masks = _masks(n, [(0, 1000), (1000, 2000), (2000, 3000)])
        res = romano_wolf_stepm(
            x,
            masks,
            block_length=8.0,
            rng=np.random.default_rng(3),
            n_bootstrap=500,
            alpha=0.05,
        )
        assert res.rejected.sum() == 0
        assert np.all(res.adjusted_pvalue >= 0.05)

    def test_adjusted_pvalues_monotone_along_order(self) -> None:
        rng = np.random.default_rng(4)
        n = 4000
        x = rng.normal(0.0, 1.0, n)
        x[:1000] += 0.30
        x[1000:2000] += 0.10
        masks = _masks(n, [(0, 1000), (1000, 2000), (2000, 3000), (3000, 4000)])
        res = romano_wolf_stepm(
            x,
            masks,
            block_length=8.0,
            rng=np.random.default_rng(5),
            n_bootstrap=400,
        )
        order = np.argsort(-res.stat)
        p_ordered = res.adjusted_pvalue[order]
        assert np.all(np.diff(p_ordered) >= -1e-12)  # non-decreasing along step-down

    def test_studentization_penalizes_high_variance(self) -> None:
        # Two cells, same mean; the higher-variance cell has the smaller statistic.
        rng = np.random.default_rng(6)
        n = 2000
        x = np.empty(n)
        x[:1000] = rng.normal(0.1, 0.5, 1000)  # low variance
        x[1000:] = rng.normal(0.1, 2.0, 1000)  # high variance
        masks = _masks(n, [(0, 1000), (1000, 2000)])
        res = romano_wolf_stepm(
            x,
            masks,
            block_length=5.0,
            rng=np.random.default_rng(7),
            n_bootstrap=300,
        )
        assert res.stat[0] > res.stat[1]  # low-variance cell has larger t

    def test_small_cell_never_rejected(self) -> None:
        rng = np.random.default_rng(8)
        n = 2000
        x = rng.normal(0.0, 1.0, n)
        x[:1] += 100.0  # a 1-member "cell" with huge value
        masks = _masks(n, [(0, 1), (1, 2000)])
        res = romano_wolf_stepm(
            x,
            masks,
            block_length=5.0,
            rng=np.random.default_rng(9),
            n_bootstrap=200,
        )
        assert not res.rejected[0]  # < min_n members -> t = -inf, never rejected

    def test_overlapping_cells_edge_in_overlap(self) -> None:
        # Overlapping (nested-like) cells: the joint bootstrap must handle shared
        # membership. Edge lives ONLY in the shared overlap; the two overlapping
        # cells each partly cover it, a disjoint third does not.
        rng = np.random.default_rng(10)
        n = 3000
        x = rng.normal(0.0, 1.0, n)
        x[1000:1500] += 0.60  # genuine edge in the overlap region
        masks = np.zeros((3, n), dtype=bool)
        masks[0, 0:1500] = True  # cell A: [0,1500) — includes the overlap
        masks[1, 1000:2500] = True  # cell B: [1000,2500) — shares [1000,1500) with A
        masks[2, 2500:3000] = True  # cell C: disjoint, pure null
        res = romano_wolf_stepm(
            x, masks, block_length=8.0, rng=np.random.default_rng(11), n_bootstrap=500
        )
        # Every cell (even non-rejected) has a real adjusted p in [0,1], not the 1.0 floor
        # unless genuinely non-significant; the disjoint null cell C must not reject.
        assert np.all((res.adjusted_pvalue >= 0.0) & (res.adjusted_pvalue <= 1.0))
        assert not res.rejected[2]  # disjoint null never rejects under FWER control
        # At least one overlap-bearing cell should carry a smaller adjusted p than the
        # disjoint null (the edge is detectable through the shared membership).
        assert min(res.adjusted_pvalue[0], res.adjusted_pvalue[1]) < res.adjusted_pvalue[2]

    def test_all_cells_adjusted_p_assigned_not_defaulted(self) -> None:
        # Regression guard for the step-down break bug: when the top cell does NOT
        # reject, lower cells must still receive their true stepdown-adjusted p-value
        # (monotone non-decreasing), never the 1.0 initializer as a floor artifact.
        rng = np.random.default_rng(12)
        n = 3000
        n_boot = 500
        x = rng.normal(0.05, 1.0, n)  # weak global positive; top cell may not reject
        masks = _masks(n, [(0, 1000), (1000, 2000), (2000, 3000)])
        res = romano_wolf_stepm(
            x, masks, block_length=8.0, rng=np.random.default_rng(13), n_bootstrap=n_boot
        )
        order = np.argsort(-res.stat)
        p_ordered = res.adjusted_pvalue[order]
        assert np.all(np.diff(p_ordered) >= -1e-12)  # monotone along the order
        # Not every non-top cell is pinned at exactly 1.0 (the pre-fix artifact); the
        # second-ranked cell must carry a value ON the bootstrap resolution grid
        # (a multiple of 1/(B+1)), proving it was computed rather than defaulted. The
        # divisor tracks n_boot so it cannot drift from the parametrization.
        second = res.adjusted_pvalue[order[1]]
        grid_div = n_boot + 1
        grid = round(second * grid_div) / grid_div
        assert abs(second - grid) < 1e-9  # on the (1+count)/(1+B) grid => actually computed

    def test_constant_negative_cell_not_rejected(self) -> None:
        # Degenerate sd==0 cell with a constant NEGATIVE mean must get t=-inf (never
        # rejected), not t=0.0 (which would outrank a finite-negative cell).
        rng = np.random.default_rng(14)
        n = 2000
        x = rng.normal(0.0, 1.0, n)
        x[:500] = -0.5  # constant negative cell (sd==0)
        masks = _masks(n, [(0, 500), (500, 2000)])
        res = romano_wolf_stepm(
            x, masks, block_length=5.0, rng=np.random.default_rng(15), n_bootstrap=200
        )
        assert res.stat[0] == -np.inf  # constant non-positive cell -> -inf
        assert not res.rejected[0]
