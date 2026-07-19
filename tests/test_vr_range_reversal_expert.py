"""Tests for the H106 range-state reversal expert (design §4: rule + causality)."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from skie_universe2.experts.base import BarWindow, Expert, assert_prefix_invariant
from skie_universe2.experts.vr_range_reversal import (
    _SESSION_LAST_LABEL,
    VrRangeReversalExpert,
)
from skie_universe2.features.variance_ratio_state import (
    VR_LAG_Q,
    VR_WINDOW_BARS,
    VarianceRatioState,
    variance_ratio_state,
)
from skie_universe2.utils.sessions import NY_TZ

_NY = ZoneInfo(NY_TZ)
# One past the first defined return-space state index (window + q - 2 =
# 288); used as a conservative "comfortably past warm-up" offset only.
_WARMUP = VR_WINDOW_BARS + VR_LAG_Q - 1


def _bars(ts, close) -> BarWindow:
    close = np.asarray(close, dtype=np.float64)
    return BarWindow(
        ts=ts,
        open=close,
        high=close + 0.5,
        low=close - 0.5,
        close=close,
        volume=np.full(close.size, 1000.0),
    )


def _grid(start_ny: datetime, n: int) -> list[datetime]:
    return [start_ny + timedelta(minutes=5 * i) for i in range(n)]


def _alternating_closes(n: int, delta: float = 0.001) -> np.ndarray:
    """Closes whose returns alternate +delta/−delta → strong negative
    autocorrelation → VR(2) < 1 → RANGE state after warm-up."""
    r = np.tile([delta, -delta], n // 2 + 1)[: n - 1]
    return 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(r)]))


def _persistent_closes(n: int, delta: float = 0.001, period: int = 8) -> np.ndarray:
    """Closes whose returns hold each sign for `period` bars → positive
    lag-1 autocorrelation → VR(2) > 1 → TREND state after warm-up."""
    blocks = []
    sign = 1.0
    while len(blocks) < n - 1:
        blocks.extend([sign * delta] * period)
        sign = -sign
    r = np.asarray(blocks[: n - 1])
    return 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(r)]))


class TestConformance:
    def test_is_expert(self) -> None:
        assert isinstance(VrRangeReversalExpert(), Expert)

    def test_expert_id(self) -> None:
        assert VrRangeReversalExpert().expert_id == "vr_range_reversal@1.0.0"


class TestRule:
    def test_warmup_flat(self) -> None:
        n = _WARMUP // 2
        ts = _grid(datetime(2025, 1, 6, 18, 0, tzinfo=_NY), n)
        sig = VrRangeReversalExpert().signal(_bars(ts, _alternating_closes(n)))
        assert np.all(sig.direction == 0)

    def test_range_state_contrarian_direction(self) -> None:
        # Alternating returns → RANGE; direction must be −sign(last return).
        n = _WARMUP + 200
        # Overnight-start grid avoids the 16:55 terminal label inside the span.
        ts = _grid(datetime(2025, 1, 6, 18, 0, tzinfo=_NY), n)
        closes = _alternating_closes(n)
        sig = VrRangeReversalExpert().signal(_bars(ts, closes))
        r = np.log(closes[1:] / closes[:-1])
        active = np.nonzero(sig.direction)[0]
        assert active.size > 50  # state engaged after warm-up
        for t in active:
            assert sig.direction[t] == (-1 if r[t - 1] > 0 else 1)
            assert sig.strength[t] == 1.0

    def test_trend_state_flat(self) -> None:
        n = _WARMUP + 200
        ts = _grid(datetime(2025, 1, 6, 18, 0, tzinfo=_NY), n)
        closes = _persistent_closes(n)
        # Establish the synthetic construction actually yields TREND (not
        # UNDETERMINED) after warm-up, so the flat assertion is meaningful.
        r = np.log(closes[1:] / closes[:-1])
        states = variance_ratio_state(r, window=VR_WINDOW_BARS, q=VR_LAG_Q)
        defined = states[_WARMUP:]
        assert np.all(defined == VarianceRatioState.TREND)
        sig = VrRangeReversalExpert().signal(_bars(ts, closes))
        assert np.all(sig.direction[_WARMUP + VR_LAG_Q :] == 0)

    def test_terminal_label_flat(self) -> None:
        # A grid crossing 16:55 NY: that label must be flat even in RANGE state.
        n = _WARMUP + 400
        start = datetime(2025, 1, 6, 18, 0, tzinfo=_NY)
        ts = _grid(start, n)
        closes = _alternating_closes(n)
        sig = VrRangeReversalExpert().signal(_bars(ts, closes))
        hit = [i for i, t in enumerate(ts) if t.astimezone(_NY).time() == _SESSION_LAST_LABEL]
        assert hit, "grid must contain the 16:55 label for this test"
        for i in hit:
            assert sig.direction[i] == 0

    def test_zero_return_flat(self) -> None:
        n = _WARMUP + 50
        ts = _grid(datetime(2025, 1, 6, 18, 0, tzinfo=_NY), n)
        closes = _alternating_closes(n)
        closes[-10:] = closes[-11]  # flat tail: r = 0 → no signal
        sig = VrRangeReversalExpert().signal(_bars(ts, closes))
        assert np.all(sig.direction[-9:] == 0)


class TestCausality:
    def test_prefix_invariant(self) -> None:
        n = _WARMUP + 120
        ts = _grid(datetime(2025, 1, 6, 18, 0, tzinfo=_NY), n)
        rng = np.random.default_rng(20260720)
        r = rng.normal(0.0, 0.001, n - 1)
        closes = 100.0 * np.exp(np.concatenate([[0.0], np.cumsum(r)]))
        assert_prefix_invariant(VrRangeReversalExpert(), _bars(ts, closes))
