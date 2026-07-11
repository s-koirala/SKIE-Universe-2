"""Unit tests for the Kaplan-Meier estimator + pooled bootstrap (H900 §8).

Hand-checkable KM arithmetic, censoring behavior, Greenwood/median-CI
plumbing, and stationary-bootstrap pooled-median reproducibility.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.inference.survival import (
    km_fit,
    km_median,
    km_median_greenwood_ci,
    pooled_km_median_stationary_bootstrap,
)


class TestKMFit:
    def test_no_censoring_matches_empirical_survivor(self) -> None:
        # Durations 1..4, all events: S = 3/4, 2/4, 1/4, 0.
        d = np.array([1.0, 2.0, 3.0, 4.0])
        e = np.ones(4, dtype=bool)
        fit = km_fit(d, e)
        np.testing.assert_array_equal(fit.times, [1, 2, 3, 4])
        np.testing.assert_allclose(fit.survival, [0.75, 0.5, 0.25, 0.0], atol=1e-12)

    def test_klein_moeschberger_hand_example(self) -> None:
        # Durations: 3(e), 5(c), 7(e), 9(e), 9(c), 11(e)
        # t=3: n=6,d=1 -> S=5/6
        # t=7: n=4,d=1 -> S=5/6*3/4=0.625
        # t=9: n=3,d=1 -> S=0.625*2/3=0.41667
        # t=11: n=1,d=1 -> S=0.
        d = np.array([3.0, 5.0, 7.0, 9.0, 9.0, 11.0])
        e = np.array([True, False, True, True, False, True])
        fit = km_fit(d, e)
        np.testing.assert_array_equal(fit.times, [3, 7, 9, 11])
        np.testing.assert_allclose(fit.survival, [5 / 6, 5 / 8, 5 / 12, 0.0], atol=1e-12)
        assert fit.n_observations == 6
        assert fit.n_uncensored == 4

    def test_censoring_raises_survival_vs_event(self) -> None:
        d = np.array([2.0, 2.0, 4.0, 6.0])
        s_all_events = km_fit(d, np.array([True, True, True, True]))
        s_censored = km_fit(d, np.array([True, False, True, True]))
        # Censoring the second 2.0 keeps more survivor mass at t >= 4.
        s_a = s_all_events.survival[s_all_events.times == 4.0][0]
        s_c = s_censored.survival[s_censored.times == 4.0][0]
        assert s_c > s_a

    def test_validation(self) -> None:
        with pytest.raises(ValueError, match="strictly positive"):
            km_fit(np.array([0.0, 1.0]), np.array([True, True]))
        with pytest.raises(ValueError, match="no observations"):
            km_fit(np.array([]), np.array([], dtype=bool))


class TestKMMedian:
    def test_median_smallest_time_below_half(self) -> None:
        d = np.array([1.0, 2.0, 3.0, 4.0])
        e = np.ones(4, dtype=bool)
        assert km_median(km_fit(d, e)) == 2.0

    def test_median_undefined_when_curve_stays_above_half(self) -> None:
        # 1 event among 9 censored: S never reaches 0.5.
        d = np.array([1.0] + [10.0] * 9)
        e = np.array([True] + [False] * 9)
        assert np.isnan(km_median(km_fit(d, e)))

    def test_heavy_censoring_shifts_median_up(self) -> None:
        rng = np.random.default_rng(20260710)
        d = rng.exponential(10.0, size=400) + 1.0
        e_all = np.ones(400, dtype=bool)
        # Administrative right-censoring at 15.0 (comfortably above
        # the exp(10)+1 median ~ 7.9 so the censored median is defined).
        cutoff = 15.0
        d_cens = np.minimum(d, cutoff)
        e_cens = d <= cutoff
        m_all = km_median(km_fit(d, e_all))
        m_cens = km_median(km_fit(d_cens, e_cens))
        # KM handles the censoring: medians should agree closely
        # (both estimate the same distribution; median < cutoff).
        assert abs(m_all - m_cens) < 0.5
        # Naive median treating censored as events would be biased DOWN.
        naive = float(np.median(d_cens))
        assert naive <= m_cens


class TestMedianGreenwoodCI:
    def test_ci_brackets_median_and_narrows_with_n(self) -> None:
        rng = np.random.default_rng(20260710)
        small = rng.exponential(10.0, size=60) + 1.0
        large = rng.exponential(10.0, size=2000) + 1.0
        est_s = km_median_greenwood_ci(small, np.ones(60, dtype=bool), alpha=0.05)
        est_l = km_median_greenwood_ci(large, np.ones(2000, dtype=bool), alpha=0.05)
        assert est_s.ci_low <= est_s.median <= est_s.ci_high
        assert est_l.ci_low <= est_l.median <= est_l.ci_high
        assert (est_l.ci_high - est_l.ci_low) < (est_s.ci_high - est_s.ci_low)

    def test_upper_bound_inf_when_unattained(self) -> None:
        # Very heavy censoring: lower band never crosses 0.5.
        d = np.array([1.0, 2.0] + [50.0] * 20)
        e = np.array([True, True] + [False] * 20)
        est = km_median_greenwood_ci(d, e, alpha=0.05)
        assert np.isinf(est.ci_high)


class TestPooledBootstrap:
    def test_reproducible_under_seed(self) -> None:
        rng_data = np.random.default_rng(1)
        d = rng_data.geometric(0.05, size=300).astype(float)
        e = rng_data.random(300) > 0.1
        a = pooled_km_median_stationary_bootstrap(
            d, e, alpha=0.05, n_bootstrap=200, rng=np.random.default_rng(20260710)
        )
        b = pooled_km_median_stationary_bootstrap(
            d, e, alpha=0.05, n_bootstrap=200, rng=np.random.default_rng(20260710)
        )
        assert (a.median, a.ci_low, a.ci_high) == (b.median, b.ci_low, b.ci_high)

    def test_ci_contains_point_estimate_typically(self) -> None:
        rng_data = np.random.default_rng(2)
        d = rng_data.geometric(0.05, size=500).astype(float)
        e = np.ones(500, dtype=bool)
        out = pooled_km_median_stationary_bootstrap(
            d, e, alpha=0.05, n_bootstrap=400, rng=np.random.default_rng(20260710)
        )
        assert out.ci_low <= out.median <= out.ci_high
        assert out.block_selection.method == "politis_white_2004"
        assert out.n_undefined_replicates < 400
