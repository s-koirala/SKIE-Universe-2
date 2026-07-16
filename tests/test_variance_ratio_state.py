"""Unit tests for the S_vr variance-ratio trend/range covariate (H001 §3)."""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.features.variance_ratio_state import (
    VarianceRatioState,
    rolling_variance_ratio,
    variance_ratio_state,
)


class TestRollingVarianceRatio:
    def test_warmup_nan(self) -> None:
        rng = np.random.default_rng(0)
        r = rng.normal(0, 1, size=200)
        vr = rolling_variance_ratio(r, window=50, q=2)
        assert np.all(np.isnan(vr[: 50 + 2 - 2]))  # window+q-2 leading NaN
        assert np.isfinite(vr[-1])

    def test_iid_returns_vr_near_one(self) -> None:
        # White-noise returns => no serial correlation => VR(2) ~ 1.
        rng = np.random.default_rng(1)
        r = rng.normal(0, 1, size=6000)
        vr = rolling_variance_ratio(r, window=500, q=2)
        assert np.nanmean(vr) == pytest.approx(1.0, abs=0.1)

    def test_trending_returns_vr_above_one(self) -> None:
        # Positively autocorrelated returns (AR(1), phi>0) => VR(2) > 1.
        rng = np.random.default_rng(2)
        n = 6000
        e = rng.normal(0, 1, size=n)
        r = np.empty(n)
        r[0] = e[0]
        for t in range(1, n):
            r[t] = 0.5 * r[t - 1] + e[t]
        vr = rolling_variance_ratio(r, window=500, q=2)
        assert np.nanmean(vr) > 1.2

    def test_mean_reverting_returns_vr_below_one(self) -> None:
        # Negatively autocorrelated returns (AR(1), phi<0) => VR(2) < 1.
        rng = np.random.default_rng(3)
        n = 6000
        e = rng.normal(0, 1, size=n)
        r = np.empty(n)
        r[0] = e[0]
        for t in range(1, n):
            r[t] = -0.5 * r[t - 1] + e[t]
        vr = rolling_variance_ratio(r, window=500, q=2)
        assert np.nanmean(vr) < 0.8

    def test_invalid_q_raises(self) -> None:
        with pytest.raises(ValueError, match="q must be >= 2"):
            rolling_variance_ratio(np.zeros(100), window=50, q=1)

    def test_window_too_small_raises(self) -> None:
        with pytest.raises(ValueError, match="window must be >= q"):
            rolling_variance_ratio(np.zeros(100), window=2, q=2)


class TestVarianceRatioState:
    def test_classification(self) -> None:
        rng = np.random.default_rng(4)
        n = 6000
        e = rng.normal(0, 1, size=n)
        r = np.empty(n)
        r[0] = e[0]
        for t in range(1, n):
            r[t] = 0.5 * r[t - 1] + e[t]  # trending
        st = variance_ratio_state(r, window=500, q=2)
        determined = st[st != VarianceRatioState.UNDETERMINED]
        assert set(np.unique(determined)).issubset({0, 1})
        # trending series => mostly TREND
        assert (determined == VarianceRatioState.TREND).mean() > 0.6

    def test_warmup_undetermined(self) -> None:
        st = variance_ratio_state(np.random.default_rng(5).normal(size=400), window=100, q=2)
        assert np.all(st[:100] == VarianceRatioState.UNDETERMINED)

    def test_causal_prefix_stability(self) -> None:
        # Trailing-window causal statistic: a prefix's labels must match the
        # full series' labels on that prefix.
        rng = np.random.default_rng(6)
        r = rng.normal(0, 1, size=2000)
        full = variance_ratio_state(r, window=300, q=2)
        pref = variance_ratio_state(r[:1200], window=300, q=2)
        np.testing.assert_array_equal(pref, full[:1200])
