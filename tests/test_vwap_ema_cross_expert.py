"""Tests for the H107 session-VWAP × EMA(N) crossover expert (design §4)."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from skie_universe2.experts.base import BarWindow, Expert, assert_prefix_invariant
from skie_universe2.experts.vwap_ema_cross import (
    EMA_SPAN_GRID,
    PRIMARY_EMA_SPAN,
    VwapEmaCrossExpert,
    cme_session_of,
    ema,
    in_trading_window,
    session_vwap,
)
from skie_universe2.utils.sessions import NY_TZ

_NY = ZoneInfo(NY_TZ)
_CT = ZoneInfo("America/Chicago")


def _grid(start: datetime, n: int) -> list[datetime]:
    return [start + timedelta(minutes=5 * i) for i in range(n)]


def _bars(ts, close, volume=None) -> BarWindow:
    close = np.asarray(close, dtype=np.float64)
    vol = np.full(close.size, 1000.0) if volume is None else np.asarray(volume, float)
    return BarWindow(ts=ts, open=close, high=close + 0.5, low=close - 0.5, close=close, volume=vol)


def test_is_expert_and_ids() -> None:
    assert isinstance(VwapEmaCrossExpert(), Expert)
    assert VwapEmaCrossExpert().expert_id == "vwap_ema9_cross@1.0.0"
    assert VwapEmaCrossExpert(21).expert_id == "vwap_ema21_cross@1.0.0"
    assert PRIMARY_EMA_SPAN in EMA_SPAN_GRID
    assert list(EMA_SPAN_GRID) == sorted(set(EMA_SPAN_GRID))
    with pytest.raises(ValueError):
        VwapEmaCrossExpert(0)


def test_ema_matches_recursion() -> None:
    x = np.array([1.0, 2.0, 3.0, 2.0])
    a = 2.0 / 10.0
    exp = [1.0]
    for v in x[1:]:
        exp.append(a * v + (1 - a) * exp[-1])
    np.testing.assert_allclose(ema(x, 9), exp)


def test_cme_session_assignment() -> None:
    assert cme_session_of(datetime(2024, 3, 5, 17, 55, tzinfo=_NY)).isoformat() == "2024-03-05"
    assert cme_session_of(datetime(2024, 3, 5, 18, 0, tzinfo=_NY)).isoformat() == "2024-03-06"
    # Sunday 17:00 CT reopen belongs to Monday's session
    assert cme_session_of(datetime(2024, 3, 3, 17, 0, tzinfo=_CT)).isoformat() == "2024-03-04"


def test_trading_window_is_flat_15_to_17_ct() -> None:
    for hh, mm, ok in [
        (14, 50, True),  # 14:50 CT label: decided at 14:55, earns to 15:00 CT
        (14, 55, False),  # would earn past 15:00 CT
        (15, 30, False),
        (16, 55, False),
        (17, 0, True),  # reopen
        (2, 0, True),  # overnight
        (9, 0, True),
    ]:
        assert in_trading_window(datetime(2024, 3, 5, hh, mm, tzinfo=_CT)) is ok, (hh, mm)


def test_vwap_resets_at_cme_session_open() -> None:
    a = _grid(datetime(2024, 3, 5, 15, 45, tzinfo=_NY), 3)  # 15:45..15:55, session 03-05
    b = _grid(datetime(2024, 3, 5, 18, 0, tzinfo=_NY), 2)  # session 03-06
    vw = session_vwap(_bars(a + b, [100.0, 102.0, 104.0, 50.0, 52.0], volume=[1, 1, 2, 1, 3]))
    np.testing.assert_allclose(vw[:3], [100.0, 101.0, (100 + 102 + 208) / 4])
    np.testing.assert_allclose(vw[3:], [50.0, (50 + 156) / 4])


def test_direction_sign_and_stop_and_reverse() -> None:
    ts = _grid(datetime(2024, 3, 5, 18, 0, tzinfo=_NY), 40)  # overnight, in-window
    close = [100.0] * 10 + list(100.0 + np.arange(1, 31))
    sig = VwapEmaCrossExpert(9).signal(_bars(ts, close))
    held = sig.direction[sig.direction != 0]
    assert held[-1] == 1
    assert np.count_nonzero(np.diff(held.astype(int))) <= 1
    assert np.all(sig.strength[sig.direction != 0] == 1.0)
    # strictly decreasing prices → short after the EMA crosses below VWAP
    sig2 = VwapEmaCrossExpert(3).signal(_bars(ts, list(200.0 - np.arange(40))))
    assert sig2.direction[-1] == -1


def test_flat_inside_window_even_with_signal() -> None:
    ts = _grid(datetime(2024, 3, 5, 15, 30, tzinfo=_NY), 12)  # 15:30..16:25 ET
    sig = VwapEmaCrossExpert(3).signal(_bars(ts, list(100.0 + np.arange(12))))
    for t, d in zip(ts, sig.direction, strict=True):
        if not in_trading_window(t):
            assert d == 0
    # in-window bars (15:30..15:50 ET) can hold; first two tie (EMA == VWAP) → flat
    assert np.any(sig.direction[:5] == 1)


def test_zero_volume_session_open_is_flat() -> None:
    ts = _grid(datetime(2024, 3, 5, 18, 0, tzinfo=_NY), 3)
    sig = VwapEmaCrossExpert().signal(_bars(ts, [100, 101, 102], volume=[0, 0, 10]))
    assert sig.direction[0] == 0 and sig.direction[1] == 0


@pytest.mark.parametrize("span", [3, 9, 55])
def test_prefix_invariant(span: int) -> None:
    rng = np.random.default_rng(span)
    ts = _grid(datetime(2024, 3, 4, 18, 0, tzinfo=_NY), 288 * 3)  # 3 sessions, DST-free
    close = 5000.0 * np.exp(np.cumsum(rng.normal(0, 5e-4, len(ts))))
    vol = rng.integers(1, 5000, len(ts)).astype(float)
    assert_prefix_invariant(VwapEmaCrossExpert(span), _bars(ts, close, vol))


def test_dst_window_follows_local_clock() -> None:
    utc = ZoneInfo("UTC")
    # After US DST start (2024-03-10): 15:00 CT = 20:00 UTC; before: 21:00 UTC.
    assert not in_trading_window(datetime(2024, 3, 11, 19, 55, tzinfo=utc))
    assert in_trading_window(datetime(2024, 3, 8, 20, 50, tzinfo=utc))
