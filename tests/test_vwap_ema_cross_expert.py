"""Tests for the H107 (DRAFT) session-VWAP × EMA(9) crossover expert (draft design §4)."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np
import pytest

from skie_universe2.experts.base import BarWindow, Expert, assert_prefix_invariant
from skie_universe2.experts.vwap_ema_cross import (
    VwapEmaCrossExpert,
    ema,
    session_vwap,
)
from skie_universe2.utils.sessions import NY_TZ

_NY = ZoneInfo(NY_TZ)


def _grid(start_ny: datetime, n: int) -> list[datetime]:
    return [start_ny + timedelta(minutes=5 * i) for i in range(n)]


def _bars(ts, close, volume=None) -> BarWindow:
    close = np.asarray(close, dtype=np.float64)
    vol = np.full(close.size, 1000.0) if volume is None else np.asarray(volume, float)
    return BarWindow(ts=ts, open=close, high=close + 0.5, low=close - 0.5, close=close, volume=vol)


def _tod(ts) -> list[str]:
    return [t.astimezone(_NY).strftime("%H:%M") for t in ts]


def test_is_expert() -> None:
    assert isinstance(VwapEmaCrossExpert(), Expert)
    assert VwapEmaCrossExpert().expert_id == "vwap_ema9_cross@0.1.0-draft"


def test_ema_matches_recursion() -> None:
    x = np.array([1.0, 2.0, 3.0, 2.0])
    a = 0.2
    exp = [1.0]
    for v in x[1:]:
        exp.append(a * v + (1 - a) * exp[-1])
    np.testing.assert_allclose(ema(x, span=9), exp)


def test_vwap_resets_each_session_and_nan_outside_rth() -> None:
    d1 = _grid(datetime(2024, 3, 5, 9, 30, tzinfo=_NY), 3)
    d2 = _grid(datetime(2024, 3, 6, 9, 30, tzinfo=_NY), 2)
    pre = [datetime(2024, 3, 6, 8, 0, tzinfo=_NY)]
    ts = d1 + pre + d2
    close = [100.0, 102.0, 104.0, 999.0, 50.0, 52.0]
    vw = session_vwap(_bars(ts, close, volume=[1, 1, 2, 5, 1, 3]))
    # typical price == close here (high/low symmetric about close)
    np.testing.assert_allclose(vw[:3], [100.0, 101.0, (100 + 102 + 208) / 4])
    assert np.isnan(vw[3])  # pre-RTH bar
    np.testing.assert_allclose(vw[4:], [50.0, (50 + 156) / 4])  # reset, overnight bar ignored


def test_direction_is_sign_of_ema_minus_vwap_in_rth_only() -> None:
    # Overnight flat closes, then an RTH up-trend: EMA lags price but the
    # cumulative VWAP lags more → EMA > VWAP → long after the first bar.
    on = _grid(datetime(2024, 3, 5, 7, 0, tzinfo=_NY), 30)  # 07:00..09:25
    rth = _grid(datetime(2024, 3, 5, 9, 30, tzinfo=_NY), 20)
    ts = on + rth
    close = [100.0] * 30 + list(100.0 + np.arange(1, 21))
    sig = VwapEmaCrossExpert().signal(_bars(ts, close))
    assert np.all(sig.direction[:30] == 0)  # overnight → flat
    rth_dir = sig.direction[30:]
    # first RTH bar: EMA (≈100.2) < VWAP (=101) → short; then trend → long
    assert rth_dir[0] == -1
    assert rth_dir[-1] == 1
    # exactly one cross (short → long) and no flip back: stop-and-reverse
    assert np.count_nonzero(np.diff(rth_dir[rth_dir != 0].astype(int))) == 1
    assert np.all(sig.strength[sig.direction != 0] == 1.0)


def test_flat_on_terminal_rth_label_and_after_close() -> None:
    ts = _grid(datetime(2024, 3, 5, 15, 40, tzinfo=_NY), 6)  # 15:40..16:05
    sig = VwapEmaCrossExpert().signal(_bars(ts, [100, 101, 102, 103, 104, 105]))
    labels = _tod(ts)
    for lab, d in zip(labels, sig.direction, strict=True):
        if lab in ("15:55", "16:00", "16:05"):
            assert d == 0


def test_zero_volume_session_open_is_flat() -> None:
    ts = _grid(datetime(2024, 3, 5, 9, 30, tzinfo=_NY), 3)
    sig = VwapEmaCrossExpert().signal(_bars(ts, [100, 101, 102], volume=[0, 0, 10]))
    assert sig.direction[0] == 0 and sig.direction[1] == 0


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_prefix_invariant(seed: int) -> None:
    rng = np.random.default_rng(seed)
    ts = _grid(datetime(2024, 3, 4, 18, 0, tzinfo=_NY), 288 * 3)  # 3 sessions, DST-free span
    close = 5000.0 * np.exp(np.cumsum(rng.normal(0, 5e-4, len(ts))))
    vol = rng.integers(1, 5000, len(ts)).astype(float)
    assert_prefix_invariant(VwapEmaCrossExpert(), _bars(ts, close, vol))


def test_dst_transition_rth_window_follows_local_clock() -> None:
    # 2024-03-11 is the first session after US DST start; 09:30 NY = 13:30 UTC.
    utc = ZoneInfo("UTC")
    ts = [datetime(2024, 3, 11, 13, 25, tzinfo=utc), datetime(2024, 3, 11, 13, 30, tzinfo=utc)]
    vw = session_vwap(_bars(ts, [100.0, 101.0]))
    assert np.isnan(vw[0]) and vw[1] == pytest.approx(101.0)
