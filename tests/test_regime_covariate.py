"""Unit tests for the H001 vol×trend regime covariate emitter (§5)."""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.signals.indicators import rolling_std
from skie_universe2.signals.regime_covariate import (
    TREND_FAMILIES,
    VOL_FAMILIES,
    OHLCArrays,
    RegimeCovariateEmitter,
    RegimeState,
)


def _bars_from_close(close: np.ndarray, spread: float = 0.5) -> OHLCArrays:
    """Build simple OHLC arrays from a close series (high/low = close ± spread)."""
    close = np.asarray(close, dtype=np.float64)
    return OHLCArrays(
        open=close,
        high=close + spread,
        low=close - spread,
        close=close,
    )


def _synthetic_close(n: int, seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return 100.0 + np.cumsum(rng.normal(0.0, 1.0, size=n))


class TestConstruction:
    def test_unknown_trend_family_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown trend family"):
            RegimeCovariateEmitter("bogus", "rolling_std", 3, 3)

    def test_unknown_vol_family_raises(self) -> None:
        with pytest.raises(ValueError, match="unknown vol family"):
            RegimeCovariateEmitter("sma_slope", "bogus", 3, 3)

    def test_window_too_small_raises(self) -> None:
        with pytest.raises(ValueError, match="n_t and n_v must be >= 2"):
            RegimeCovariateEmitter("sma_slope", "rolling_std", 1, 3)


class TestFitTransform:
    def test_transform_before_fit_raises(self) -> None:
        emit = RegimeCovariateEmitter("sma_slope", "rolling_std", 3, 3)
        with pytest.raises(RuntimeError, match="call fit"):
            emit.transform(_bars_from_close(_synthetic_close(50, 1)))

    def test_fit_stores_training_median(self) -> None:
        emit = RegimeCovariateEmitter("linreg_slope", "rolling_std", 3, 3)
        bars = _bars_from_close(_synthetic_close(200, 2))
        emit.fit(bars)
        # median is a finite float split point
        assert emit.vol_median_ is not None
        assert np.isfinite(emit.vol_median_)

    def test_states_are_valid_indices(self) -> None:
        emit = RegimeCovariateEmitter("sma_slope", "realized_vol", 4, 4)
        bars = _bars_from_close(_synthetic_close(300, 3))
        states = emit.fit_transform(bars)
        assert states.dtype == np.int8
        assert set(np.unique(states)).issubset({-1, 0, 1, 2, 3})

    def test_warmup_is_undetermined(self) -> None:
        emit = RegimeCovariateEmitter("sma_slope", "rolling_std", 5, 5)
        bars = _bars_from_close(_synthetic_close(100, 4))
        states = emit.fit_transform(bars)
        # leading bars (< warm-up) must be undetermined
        assert states[0] == RegimeState.UNDETERMINED
        assert states[1] == RegimeState.UNDETERMINED


class TestStateEncoding:
    def test_state_index_encoding_is_locked(self) -> None:
        # _states_from_scalars encodes vol_bit*2 + trend_bit; these indices must
        # stay pinned or the emitted covariate column desyncs from RegimeState.
        assert (
            RegimeState.CONTRACT_DOWN,
            RegimeState.CONTRACT_UP,
            RegimeState.EXPAND_DOWN,
            RegimeState.EXPAND_UP,
        ) == (0, 1, 2, 3)
        assert RegimeState.UNDETERMINED == -1

    def test_extra_warmup_bar_for_first_difference_family(self) -> None:
        # sma_slope (SMA first-difference) + rolling_std (log_returns[0]=NaN) each
        # consume one extra warm-up bar => n leading UNDETERMINED, conservatively.
        emit = RegimeCovariateEmitter("sma_slope", "rolling_std", 5, 5)
        states = emit.fit_transform(_bars_from_close(_synthetic_close(100, 9)))
        assert np.all(states[:5] == RegimeState.UNDETERMINED)


class TestLeakageSafety:
    """The split point must be the TRAINING median, applied to any slice."""

    def test_split_uses_training_median_not_test(self) -> None:
        # Train on a low-volatility slice, transform a high-volatility slice.
        train_close = 100.0 + np.cumsum(np.random.default_rng(10).normal(0.0, 0.1, size=300))
        test_close = 100.0 + np.cumsum(np.random.default_rng(11).normal(0.0, 5.0, size=300))
        emit = RegimeCovariateEmitter("linreg_slope", "realized_vol", 3, 3)
        emit.fit(_bars_from_close(train_close))
        states = emit.transform(_bars_from_close(test_close))
        # Test vol is far above the (low) training median => every determined
        # bar is an EXPAND state (index >= 2), never CONTRACT.
        determined = states[states != RegimeState.UNDETERMINED]
        assert determined.size > 0
        assert np.all(determined >= 2)

    def test_fit_transform_matches_manual_median_split(self) -> None:
        emit = RegimeCovariateEmitter("sma_slope", "rolling_std", 3, 3)
        bars = _bars_from_close(_synthetic_close(200, 5))
        states = emit.fit_transform(bars)
        # Reconstruct the vol sub-state independently and cross-check occupancy.
        vol = rolling_std(bars.log_returns(), 3)
        med = float(np.median(vol[np.isfinite(vol)]))
        assert emit.vol_median_ == pytest.approx(med)
        # bars classified EXPAND must have vol >= median where determined
        expand = (states == 2) | (states == 3)
        assert np.all(vol[expand] >= med)


class TestCausality:
    def test_transform_prefix_equals_prefix_of_transform(self) -> None:
        # With a fixed fitted median, causal indicators must give identical
        # labels for a prefix whether computed on the prefix or the full slice.
        full = _bars_from_close(_synthetic_close(400, 7))
        emit = RegimeCovariateEmitter("ema", "atr", 4, 4).fit(full)
        k = 250
        prefix = OHLCArrays(
            open=full.open[:k],
            high=full.high[:k],
            low=full.low[:k],
            close=full.close[:k],
        )
        full_states = emit.transform(full)
        prefix_states = emit.transform(prefix)
        np.testing.assert_array_equal(prefix_states, full_states[:k])


class TestAllFamilyCombinations:
    def test_every_registered_pair_runs(self) -> None:
        bars = _bars_from_close(_synthetic_close(300, 8))
        for tf in TREND_FAMILIES:
            for vf in VOL_FAMILIES:
                emit = RegimeCovariateEmitter(tf, vf, 3, 3)
                states = emit.fit_transform(bars)
                assert states.shape == bars.close.shape
                assert set(np.unique(states)).issubset({-1, 0, 1, 2, 3})


class TestOHLCArrays:
    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="share shape"):
            OHLCArrays(
                open=np.array([1.0, 2.0]),
                high=np.array([1.0]),
                low=np.array([1.0, 2.0]),
                close=np.array([1.0, 2.0]),
            )

    def test_log_returns_leading_nan(self) -> None:
        bars = _bars_from_close(np.array([100.0, 101.0, 102.0]))
        r = bars.log_returns()
        assert np.isnan(r[0])
        assert r[1] == pytest.approx(np.log(101.0 / 100.0))
