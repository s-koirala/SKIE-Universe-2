"""Unit tests for CUSUM detection latency on synthetic change-points (H900 §7)."""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from skie_universe2.inference.cusum import cusum_detection_delays


def _gaussian_log_b(x: np.ndarray, means: np.ndarray, sigma: float) -> np.ndarray:
    """(T, N) log emission densities for univariate Gaussian states."""
    return np.column_stack([norm.logpdf(x, loc=m, scale=sigma) for m in means])


def _persistent_log_transmat(n: int, stay: float) -> np.ndarray:
    a = np.full((n, n), (1.0 - stay) / (n - 1))
    np.fill_diagonal(a, stay)
    return np.log(a)


class TestCusumDelays:
    def test_detects_clean_mean_shift_fast(self) -> None:
        # Well-separated states (4 sigma apart): detection within a few
        # bars of each change-point.
        rng = np.random.default_rng(20260710)
        means = np.array([-2.0, 2.0])
        states = np.array([0] * 100 + [1] * 100 + [0] * 100)
        x = rng.normal(means[states], 1.0)
        log_b = _gaussian_log_b(x, means, 1.0)
        out = cusum_detection_delays(log_b, states, _persistent_log_transmat(2, 0.99))
        assert out.delay_bars.size == 2
        assert np.all(out.event)
        # LLR per post-change bar ~ N(2*mu^2/sigma^2, ...) = 8; h = log(100)
        # ~ 4.6 -> expected delay ~ 1-3 bars.
        assert np.all(out.delay_bars <= 5)
        np.testing.assert_array_equal(out.from_state, [0, 1])
        np.testing.assert_array_equal(out.to_state, [1, 0])

    def test_weak_shift_has_longer_delay_than_strong(self) -> None:
        rng = np.random.default_rng(20260710)
        states = np.array([0] * 300 + [1] * 300)
        lt = _persistent_log_transmat(2, 0.995)
        delays = {}
        for name, sep in [("strong", 2.0), ("weak", 0.4)]:
            means = np.array([0.0, sep])
            x = rng.normal(means[states], 1.0)
            log_b = _gaussian_log_b(x, means, 1.0)
            out = cusum_detection_delays(log_b, states, lt)
            assert out.delay_bars.size == 1
            delays[name] = int(out.delay_bars[0])
        assert delays["weak"] > delays["strong"]

    def test_censored_when_sojourn_too_short_to_detect(self) -> None:
        # Nearly indistinguishable states + 2-bar sojourn: no alarm; the
        # delay is right-censored at the observed sojourn length.
        rng = np.random.default_rng(20260710)
        means = np.array([0.0, 0.05])
        states = np.array([0] * 50 + [1] * 2 + [0] * 50)
        x = rng.normal(0.0, 1.0, size=states.size)  # no real shift at all
        log_b = _gaussian_log_b(x, means, 1.0)
        out = cusum_detection_delays(log_b, states, _persistent_log_transmat(2, 0.999))
        # Transition 0->1 at bar 50 (sojourn 2 bars), 1->0 at bar 52.
        first = 0
        assert out.event[first] == np.False_ or out.delay_bars[first] <= 2
        if not out.event[first]:
            assert out.delay_bars[first] == 2

    def test_threshold_anchored_to_incumbent_expected_sojourn(self) -> None:
        rng = np.random.default_rng(20260710)
        means = np.array([-1.0, 1.0])
        states = np.array([0] * 60 + [1] * 60)
        x = rng.normal(means[states], 1.0)
        log_b = _gaussian_log_b(x, means, 1.0)
        stay = 0.98
        out = cusum_detection_delays(log_b, states, _persistent_log_transmat(2, stay))
        # h = log(1 / (1 - a_ii)) = log(50).
        np.testing.assert_allclose(out.threshold, [np.log(1.0 / (1.0 - stay))], atol=1e-12)

    def test_no_transitions_yields_empty(self) -> None:
        x = np.zeros(20)
        log_b = _gaussian_log_b(x, np.array([0.0, 1.0]), 1.0)
        out = cusum_detection_delays(
            log_b, np.zeros(20, dtype=np.int64), _persistent_log_transmat(2, 0.9)
        )
        assert out.delay_bars.size == 0

    def test_validation(self) -> None:
        with pytest.raises(ValueError, match="aligned"):
            cusum_detection_delays(np.zeros((10, 2)), np.zeros(5, dtype=np.int64), np.zeros((2, 2)))
        with pytest.raises(ValueError, match="mismatch"):
            cusum_detection_delays(
                np.zeros((10, 2)), np.zeros(10, dtype=np.int64), np.zeros((3, 3))
            )
