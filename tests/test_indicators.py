"""Unit tests for signal-layer indicator functions."""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.signals.indicators import (
    atr,
    ema,
    kama,
    linreg_slope,
    parkinson,
    realized_vol,
    rolling_sma,
    rolling_std,
)


class TestRollingSma:
    def test_simple_case(self) -> None:
        prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = rolling_sma(prices, 3)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        assert result[2] == pytest.approx(2.0)
        assert result[3] == pytest.approx(3.0)
        assert result[4] == pytest.approx(4.0)

    def test_period_one(self) -> None:
        prices = np.array([10.0, 20.0, 30.0])
        result = rolling_sma(prices, 1)
        np.testing.assert_array_almost_equal(result, prices)

    def test_period_equals_length(self) -> None:
        prices = np.array([2.0, 4.0, 6.0])
        result = rolling_sma(prices, 3)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        assert result[2] == pytest.approx(4.0)

    def test_period_exceeds_length(self) -> None:
        prices = np.array([1.0, 2.0])
        result = rolling_sma(prices, 5)
        assert all(np.isnan(result))

    def test_invalid_period_raises(self) -> None:
        with pytest.raises(ValueError, match="period must be >= 1"):
            rolling_sma(np.array([1.0]), 0)

    def test_2d_input_raises(self) -> None:
        with pytest.raises(ValueError, match="1-D"):
            rolling_sma(np.array([[1.0, 2.0]]), 2)

    def test_constant_series(self) -> None:
        prices = np.full(10, 5.0)
        result = rolling_sma(prices, 3)
        valid = result[~np.isnan(result)]
        np.testing.assert_array_almost_equal(valid, np.full(len(valid), 5.0))


class TestRollingStd:
    def test_simple_case(self) -> None:
        prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = rolling_std(prices, 3)
        assert np.isnan(result[0])
        assert np.isnan(result[1])
        # std([1,2,3], ddof=1) = 1.0
        assert result[2] == pytest.approx(1.0)
        assert result[3] == pytest.approx(1.0)
        assert result[4] == pytest.approx(1.0)

    def test_constant_series_is_zero(self) -> None:
        prices = np.full(10, 42.0)
        result = rolling_std(prices, 3)
        valid = result[~np.isnan(result)]
        np.testing.assert_array_almost_equal(valid, np.zeros(len(valid)))

    def test_invalid_period_raises(self) -> None:
        with pytest.raises(ValueError, match="period must be >= 2"):
            rolling_std(np.array([1.0, 2.0, 3.0]), 1)

    def test_period_exceeds_length(self) -> None:
        prices = np.array([1.0])
        result = rolling_std(prices, 2)
        assert all(np.isnan(result))

    def test_known_values(self) -> None:
        # Hand-computed: std([10, 20, 30], ddof=1) = 10.0
        prices = np.array([10.0, 20.0, 30.0])
        result = rolling_std(prices, 3)
        assert result[2] == pytest.approx(10.0)


class TestEma:
    def test_leading_nans_and_seed(self) -> None:
        prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = ema(prices, 3)
        assert np.isnan(result[0]) and np.isnan(result[1])
        # seed = SMA(first 3) = 2.0
        assert result[2] == pytest.approx(2.0)
        # alpha = 2/4 = 0.5; ema[3] = 0.5*4 + 0.5*2 = 3.0
        assert result[3] == pytest.approx(3.0)

    def test_constant_series(self) -> None:
        result = ema(np.full(10, 7.0), 4)
        valid = result[~np.isnan(result)]
        np.testing.assert_array_almost_equal(valid, np.full(len(valid), 7.0))

    def test_invalid_span_raises(self) -> None:
        with pytest.raises(ValueError, match="span must be >= 1"):
            ema(np.array([1.0]), 0)


class TestKama:
    def test_constant_series_stays_constant(self) -> None:
        result = kama(np.full(20, 3.0), 5)
        valid = result[~np.isnan(result)]
        np.testing.assert_array_almost_equal(valid, np.full(len(valid), 3.0))

    def test_leading_nans(self) -> None:
        result = kama(np.arange(10, dtype=float), 4)
        assert all(np.isnan(result[:3]))
        assert not np.isnan(result[4])

    def test_seed_is_finite_at_period_minus_one(self) -> None:
        # entries 0 .. period-2 are NaN; index period-1 is the finite seed.
        prices = np.arange(10, dtype=float)
        result = kama(prices, 4)
        assert all(np.isnan(result[:3]))  # indices 0..period-2
        assert result[3] == pytest.approx(prices[3])  # index period-1 = seed

    def test_trending_series_tracks_price_under_high_er(self) -> None:
        # Perfect ramp => ER=1 => fast smoothing constant (2/3)^2 per bar, so
        # KAMA rises monotonically and lags price by a bounded, small amount
        # (the fast bound is 2/(2+1), not 1, so exact tracking is not expected).
        prices = np.arange(30, dtype=float)
        result = kama(prices, 5)
        valid = result[~np.isnan(result)]
        assert np.all(np.diff(valid) > 0.0)  # monotonically increasing
        assert result[-1] == pytest.approx(prices[-1], abs=2.0)
        # KAMA under ER=1 must track closer than the slow-bound EMA would.
        assert result[-1] > prices[-1] - 2.0


class TestLinregSlope:
    def test_perfect_line(self) -> None:
        prices = np.array([0.0, 2.0, 4.0, 6.0, 8.0])
        result = linreg_slope(prices, 3)
        assert np.isnan(result[0]) and np.isnan(result[1])
        np.testing.assert_array_almost_equal(result[2:], np.full(3, 2.0))

    def test_flat_line_zero_slope(self) -> None:
        result = linreg_slope(np.full(6, 5.0), 3)
        valid = result[~np.isnan(result)]
        np.testing.assert_array_almost_equal(valid, np.zeros(len(valid)))

    def test_invalid_period_raises(self) -> None:
        with pytest.raises(ValueError, match="period must be >= 2"):
            linreg_slope(np.array([1.0, 2.0, 3.0]), 1)


class TestAtr:
    def test_shape_and_leading_nans(self) -> None:
        h = np.array([2.0, 3.0, 4.0, 5.0, 6.0])
        low = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        c = np.array([1.5, 2.5, 3.5, 4.5, 5.5])
        result = atr(h, low, c, 2)
        assert all(np.isnan(result[:2]))
        assert not np.isnan(result[2])

    def test_known_value(self) -> None:
        # constant HL range 1.0, close mid-bar; TR (with prior close) = 1.0
        h = np.array([2.0, 2.0, 2.0, 2.0])
        low = np.array([1.0, 1.0, 1.0, 1.0])
        c = np.array([1.5, 1.5, 1.5, 1.5])
        result = atr(h, low, c, 2)
        assert result[3] == pytest.approx(1.0)

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="share shape"):
            atr(np.array([1.0, 2.0]), np.array([1.0]), np.array([1.0, 2.0]), 2)


class TestParkinson:
    def test_known_value(self) -> None:
        # constant high/low ratio 2:1 => ln(2)^2 each bar
        h = np.full(5, 2.0)
        low = np.full(5, 1.0)
        result = parkinson(h, low, 3)
        expected = np.sqrt((1.0 / (4.0 * np.log(2.0))) * np.log(2.0) ** 2)
        assert result[2] == pytest.approx(expected)

    def test_leading_nans(self) -> None:
        h = np.full(5, 2.0)
        low = np.full(5, 1.0)
        result = parkinson(h, low, 3)
        assert all(np.isnan(result[:2]))


class TestRealizedVol:
    def test_known_value(self) -> None:
        r = np.array([0.1, 0.1, 0.1, 0.1])
        result = realized_vol(r, 3)
        assert np.isnan(result[0]) and np.isnan(result[1])
        assert result[2] == pytest.approx(np.sqrt(3 * 0.01))

    def test_zero_returns_zero_vol(self) -> None:
        result = realized_vol(np.zeros(5), 3)
        valid = result[~np.isnan(result)]
        np.testing.assert_array_almost_equal(valid, np.zeros(len(valid)))
