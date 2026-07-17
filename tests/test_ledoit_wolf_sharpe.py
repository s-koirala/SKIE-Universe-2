"""Unit tests for the Ledoit-Wolf 2008 studentized-bootstrap Sharpe-difference test."""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.inference.ledoit_wolf_sharpe import (
    SharpeDiffResult,
    sharpe_diff_hac_se,
    sharpe_ratio_difference_test,
)


def _ar1(
    n: int, phi: float, sigma: float, rng: np.random.Generator, mean: float = 0.0
) -> np.ndarray:
    """AR(1) series x_t = phi x_{t-1} + eps_t with a level shift `mean`."""
    e = rng.normal(0.0, sigma, n)
    x = np.empty(n)
    x[0] = e[0]
    for t in range(1, n):
        x[t] = phi * x[t - 1] + e[t]
    return x + mean


class TestSharpeRatioDifferenceTest:
    def test_genuine_difference_small_p_ci_excludes_zero(self) -> None:
        # returns_a has a higher mean (higher Sharpe) than returns_b -> reject H0.
        rng = np.random.default_rng(0)
        n = 1500
        a = rng.normal(0.10, 1.0, n)
        b = rng.normal(-0.05, 1.0, n)
        res = sharpe_ratio_difference_test(
            a, b, block_length=4.0, rng=np.random.default_rng(1), n_bootstrap=999
        )
        assert isinstance(res, SharpeDiffResult)
        assert res.sharpe_diff > 0
        assert res.p_value < 0.05
        assert not (res.ci_low <= 0.0 <= res.ci_high)  # CI excludes zero

    def test_exchangeable_series_large_p_ci_includes_zero(self) -> None:
        # Two independent draws from the SAME distribution (H0 true) -> do not reject.
        rng = np.random.default_rng(2)
        n = 1500
        a = rng.normal(0.0, 1.0, n)
        b = rng.normal(0.0, 1.0, n)
        res = sharpe_ratio_difference_test(
            a, b, block_length=4.0, rng=np.random.default_rng(3), n_bootstrap=999
        )
        assert res.p_value > 0.05
        assert res.ci_low <= 0.0 <= res.ci_high  # CI includes zero

    def test_pvalue_ci_agree_by_construction(self) -> None:
        # p < alpha  <=>  CI excludes zero (both are |.|-based, LW08 eqs. 7 & 9).
        rng = np.random.default_rng(4)
        n = 800
        a = rng.normal(0.08, 1.0, n)
        b = rng.normal(0.0, 1.0, n)
        res = sharpe_ratio_difference_test(
            a, b, block_length=4.0, rng=np.random.default_rng(5), n_bootstrap=999, alpha=0.05
        )
        excludes_zero = not (res.ci_low <= 0.0 <= res.ci_high)
        assert excludes_zero == (res.p_value < res.alpha)

    def test_block_bootstrap_hac_se_wider_than_iid(self) -> None:
        # Positively autocorrelated (AR(1)) inputs -> the Bartlett HAC SE (which
        # accounts for serial dependence) exceeds the iid naive SE (bandwidth 0).
        rng = np.random.default_rng(6)
        n = 2000
        a = _ar1(n, phi=0.6, sigma=1.0, rng=rng, mean=0.05)
        b = _ar1(n, phi=0.6, sigma=1.0, rng=rng, mean=0.0)
        _, se_hac, lag = sharpe_diff_hac_se(a, b)  # auto NW94 bandwidth
        _, se_iid, lag0 = sharpe_diff_hac_se(a, b, bandwidth=0)
        assert lag0 == 0
        assert lag >= 1  # NW94 selected a positive truncation lag under dependence
        assert se_hac > se_iid

    def test_auto_block_length_selection(self) -> None:
        # block_length=None auto-selects via Politis-White and records it (>= 1).
        rng = np.random.default_rng(7)
        n = 1200
        a = _ar1(n, phi=0.5, sigma=1.0, rng=rng, mean=0.05)
        b = _ar1(n, phi=0.5, sigma=1.0, rng=rng, mean=0.0)
        res = sharpe_ratio_difference_test(
            a, b, block_length=None, rng=np.random.default_rng(8), n_bootstrap=500
        )
        assert res.block_length >= 1.0
        assert np.isfinite(res.p_value)

    def test_determinism_same_seed_same_result(self) -> None:
        rng = np.random.default_rng(9)
        n = 1000
        a = rng.normal(0.05, 1.0, n)
        b = rng.normal(0.0, 1.0, n)
        r1 = sharpe_ratio_difference_test(
            a, b, block_length=6.0, rng=np.random.default_rng(42), n_bootstrap=500
        )
        r2 = sharpe_ratio_difference_test(
            a, b, block_length=6.0, rng=np.random.default_rng(42), n_bootstrap=500
        )
        assert r1 == r2

    def test_symmetry_swap_flips_sign_same_p(self) -> None:
        rng = np.random.default_rng(10)
        n = 1200
        a = rng.normal(0.10, 1.0, n)
        b = rng.normal(0.0, 1.0, n)
        r_ab = sharpe_ratio_difference_test(
            a, b, block_length=5.0, rng=np.random.default_rng(11), n_bootstrap=500
        )
        r_ba = sharpe_ratio_difference_test(
            b, a, block_length=5.0, rng=np.random.default_rng(11), n_bootstrap=500
        )
        assert r_ab.sharpe_diff == pytest.approx(-r_ba.sharpe_diff)
        assert r_ab.studentized_stat == pytest.approx(-r_ba.studentized_stat)
        assert r_ab.ci_low == pytest.approx(-r_ba.ci_high)
        assert r_ab.ci_high == pytest.approx(-r_ba.ci_low)
        assert r_ab.p_value == pytest.approx(r_ba.p_value)

    def test_degenerate_zero_variance_guard(self) -> None:
        rng = np.random.default_rng(12)
        n = 500
        a = np.full(n, 0.01)  # constant series -> zero variance
        b = rng.normal(0.0, 1.0, n)
        with pytest.raises(ValueError, match="zero variance|Sharpe difference undefined"):
            sharpe_ratio_difference_test(
                a, b, block_length=4.0, rng=np.random.default_rng(13), n_bootstrap=200
            )

    def test_length_mismatch_and_too_short_raise(self) -> None:
        rng = np.random.default_rng(14)
        with pytest.raises(ValueError, match="equal length"):
            sharpe_ratio_difference_test(
                rng.normal(size=100),
                rng.normal(size=101),
                block_length=4.0,
                rng=np.random.default_rng(15),
                n_bootstrap=100,
            )
        with pytest.raises(ValueError, match=">= 2"):
            sharpe_ratio_difference_test(
                np.array([0.1]),
                np.array([0.2]),
                block_length=4.0,
                rng=np.random.default_rng(16),
                n_bootstrap=100,
            )


class TestNumericBenchmark:
    def test_hac_se_matches_lo2002_closed_form_iid_normal(self) -> None:
        # Analytical benchmark (CLAUDE.md Verification): for two INDEPENDENT IID-normal
        # return series, the LW08 delta-method SE of the Sharpe difference reduces (the
        # cross-covariance term vanishes under independence) to the Lo-2002 single-Sharpe
        # variance summed: Var(SR_a - SR_b) = [(1 + SR_a^2/2) + (1 + SR_b^2/2)] / n.
        rng = np.random.default_rng(20260716)
        n = 200_000
        mu_a, sd_a = 0.05, 1.0
        mu_b, sd_b = 0.02, 1.3
        a = rng.normal(mu_a, sd_a, n)
        b = rng.normal(mu_b, sd_b, n)  # independent of a
        # bandwidth=0 -> HAC LRV is the lag-0 (IID) influence variance, the delta-method SE.
        sharpe_diff, se, lag = sharpe_diff_hac_se(a, b, bandwidth=0)
        assert lag == 0
        sr_a = a.mean() / a.std(ddof=1)
        sr_b = b.mean() / b.std(ddof=1)
        closed_form_se = np.sqrt(((1.0 + sr_a**2 / 2.0) + (1.0 + sr_b**2 / 2.0)) / n)
        # At n=2e5 the influence-based SE and the closed form agree to ~1%.
        assert abs(se - closed_form_se) / closed_form_se < 0.02
        assert abs(sharpe_diff - (sr_a - sr_b)) < 1e-12
