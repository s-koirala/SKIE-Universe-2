"""Unit tests for the expert-interface contract (OD-1)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from skie_universe2.experts.base import (
    BarWindow,
    Expert,
    SignalSeries,
    assert_prefix_invariant,
    assert_valid_expert_id,
)


def _bars(n: int, seed: int = 0) -> BarWindow:
    rng = np.random.default_rng(seed)
    close = 100.0 + np.cumsum(rng.normal(0, 1, n))
    base = datetime(2025, 1, 6, 9, 30, tzinfo=UTC)
    return BarWindow(
        ts=[base + timedelta(minutes=5 * i) for i in range(n)],
        open=close,
        high=close + 0.5,
        low=close - 0.5,
        close=close,
        volume=np.full(n, 1000.0),
    )


class _CausalMomentum:
    """Reference causal expert: sign of the 1-bar close change (data <= t)."""

    expert_id = "causal_mom@1.0.0"

    def fit(self, train: BarWindow) -> None:  # stateless
        pass

    def signal(self, bars: BarWindow) -> SignalSeries:
        d = np.zeros(len(bars), dtype=np.int8)
        diff = np.sign(np.diff(bars.close)).astype(np.int8)
        d[1:] = diff
        return SignalSeries(direction=d, strength=np.full(len(bars), 0.5))


class _LeakyExpert:
    """Deliberately look-ahead: uses the NEXT bar's close (bars > t)."""

    expert_id = "leaky@1.0.0"

    def fit(self, train: BarWindow) -> None:
        pass

    def signal(self, bars: BarWindow) -> SignalSeries:
        d = np.zeros(len(bars), dtype=np.int8)
        # direction[t] peeks at close[t+1] — a leak.
        d[:-1] = np.sign(bars.close[1:] - bars.close[:-1]).astype(np.int8)
        return SignalSeries(direction=d, strength=np.full(len(bars), 0.5))


class TestBarWindow:
    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="shape"):
            BarWindow(
                ts=[datetime(2025, 1, 1, tzinfo=UTC)],
                open=np.array([1.0, 2.0]),
                high=np.array([1.0]),
                low=np.array([1.0]),
                close=np.array([1.0]),
                volume=np.array([1.0]),
            )

    def test_prefix(self) -> None:
        b = _bars(20)
        p = b.prefix(8)
        assert len(p) == 8
        np.testing.assert_array_equal(p.close, b.close[:8])


class TestSignalSeries:
    def test_invalid_direction_raises(self) -> None:
        with pytest.raises(ValueError, match="direction"):
            SignalSeries(direction=np.array([2], dtype=np.int8), strength=np.array([0.5]))

    def test_strength_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="strength"):
            SignalSeries(direction=np.array([1], dtype=np.int8), strength=np.array([1.5]))


class TestProtocolConformance:
    def test_causal_expert_is_expert(self) -> None:
        assert isinstance(_CausalMomentum(), Expert)

    def test_expert_id_versioned(self) -> None:
        assert "@" in _CausalMomentum().expert_id


def _mono_bars(n: int) -> BarWindow:
    """Monotone-increasing close so a causal momentum baseline is trivially LONG."""
    close = 100.0 + np.arange(n, dtype=float)
    base = datetime(2025, 1, 6, 9, 30, tzinfo=UTC)
    return BarWindow(
        ts=[base + timedelta(minutes=5 * i) for i in range(n)],
        open=close,
        high=close + 0.5,
        low=close - 0.5,
        close=close,
        volume=np.full(n, 1000.0),
    )


class _PointLeak:
    """Deterministic data-dependent leak: on monotone-up bars the causal baseline
    is always LONG, but ``direction[3]`` is flipped to SHORT whenever the far-future
    bar 20 is present in the window (a genuine forward reach)."""

    expert_id = "pointleak@1.0.0"

    def fit(self, train: BarWindow) -> None:
        pass

    def signal(self, bars: BarWindow) -> SignalSeries:
        d = np.ones(len(bars), dtype=np.int8)  # causal baseline (monotone-up => LONG)
        if len(bars) > 20:  # noqa: PLR2004 — fixed leak source bar for the test
            d[3] = np.int8(-1)  # future-dependent override: differs from causal +1
        return SignalSeries(direction=d, strength=np.full(len(bars), 0.5))


class TestPrefixInvariantCanary:
    def test_causal_expert_passes_default_grid(self) -> None:
        assert_prefix_invariant(_CausalMomentum(), _bars(40, 1))

    def test_leaky_expert_fails(self) -> None:
        with pytest.raises(AssertionError, match="PIT canary FAILED"):
            assert_prefix_invariant(_LeakyExpert(), _bars(40, 2))

    def test_point_leak_caught_by_grid_missed_by_single_cut(self) -> None:
        bars = _mono_bars(40)
        # A single cut past the leak source (bar 3 and bar 20 both in the prefix)
        # MISSES the leak — the exact single-cut blind spot the sweep fixes.
        assert_prefix_invariant(_PointLeak(), bars, cuts=[30])
        # The default dense grid includes a cut in (3, 20] (prefix excludes bar 20,
        # so d[3] reverts to the causal +1 there) and CATCHES the value difference.
        with pytest.raises(AssertionError, match="PIT canary FAILED"):
            assert_prefix_invariant(_PointLeak(), bars)

    def test_cut_out_of_range_raises(self) -> None:
        with pytest.raises(ValueError, match="cut must be inside"):
            assert_prefix_invariant(_CausalMomentum(), _bars(10), cuts=[10])


class TestExpertIdValidation:
    def test_valid_id(self) -> None:
        assert_valid_expert_id("orb_first_hour@1.0.0")

    @pytest.mark.parametrize("bad", ["noversion", "@1.0.0", "name@", "a@b@c", ""])
    def test_malformed_id_raises(self, bad: str) -> None:
        with pytest.raises(ValueError, match="expert_id must be"):
            assert_valid_expert_id(bad)
