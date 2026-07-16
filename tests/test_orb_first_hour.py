"""Tests for the H101 first-hour ORB expert (design §4: rule + causality)."""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from skie_universe2.experts.base import BarWindow, Expert, assert_prefix_invariant
from skie_universe2.experts.orb_first_hour import OrbFirstHourExpert

_NY = ZoneInfo("America/New_York")
_N_RTH = 78  # 09:30 .. 15:55 inclusive (5-min bars)


def _bars_from(ts, close) -> BarWindow:
    close = np.asarray(close, dtype=np.float64)
    return BarWindow(
        ts=ts,
        open=close,
        high=close + 0.5,
        low=close - 0.5,
        close=close,
        volume=np.full(close.size, 1000.0),
    )


def _rth_session(day: datetime, closes) -> tuple[list, np.ndarray]:
    """One RTH session (78 five-min bars 09:30..15:55 NY) with given closes."""
    base = datetime(day.year, day.month, day.day, 9, 30, tzinfo=_NY)
    ts = [base + timedelta(minutes=5 * i) for i in range(len(closes))]
    return ts, np.asarray(closes, dtype=np.float64)


class TestConformance:
    def test_is_expert(self) -> None:
        assert isinstance(OrbFirstHourExpert(), Expert)

    def test_expert_id(self) -> None:
        assert OrbFirstHourExpert().expert_id == "orb_first_hour@1.0.0"


class TestOrbRule:
    def test_or_window_flat_then_breakout_long(self) -> None:
        # First 12 bars (OR) at 100; then jump to 102 (> OR_high 100.5) -> LONG.
        closes = [100.0] * 12 + [102.0] * (_N_RTH - 12)
        ts, c = _rth_session(datetime(2025, 1, 6), closes)  # January = EST
        sig = OrbFirstHourExpert(n_or=12).signal(_bars_from(ts, c))
        assert np.all(sig.direction[:12] == 0)  # OR window flat
        assert np.all(sig.direction[12:77] == 1)  # held LONG after breakout
        assert sig.direction[77] == 0  # exit flat at the 15:55 bar (no overnight)
        assert np.all(sig.strength[12:77] == 1.0)

    def test_breakout_short(self) -> None:
        closes = [100.0] * 12 + [98.0] * (_N_RTH - 12)  # below OR_low 99.5 -> SHORT
        ts, c = _rth_session(datetime(2025, 1, 6), closes)
        sig = OrbFirstHourExpert(n_or=12).signal(_bars_from(ts, c))
        assert np.all(sig.direction[12:77] == -1)

    def test_no_breakout_flat_all_session(self) -> None:
        # Price stays inside the OR range all day -> never breaks out.
        closes = [100.0] * _N_RTH
        ts, c = _rth_session(datetime(2025, 1, 6), closes)
        sig = OrbFirstHourExpert(n_or=12).signal(_bars_from(ts, c))
        assert np.all(sig.direction == 0)

    def test_first_breakout_only_holds_direction(self) -> None:
        # Breaks up at bar 12, then dips back inside then above again: direction
        # stays LONG (first breakout only, held to close) — never flips.
        closes = [100.0] * 12 + [102.0, 100.0, 103.0] + [102.0] * (_N_RTH - 15)
        ts, c = _rth_session(datetime(2025, 1, 6), closes)
        sig = OrbFirstHourExpert(n_or=12).signal(_bars_from(ts, c))
        assert np.all(sig.direction[12:77] == 1)

    def test_outside_rth_flat(self) -> None:
        # Prepend two ETH bars (09:00, 09:20 NY) before the RTH session.
        eth_ts = [datetime(2025, 1, 6, 9, 0, tzinfo=_NY), datetime(2025, 1, 6, 9, 20, tzinfo=_NY)]
        ts, c = _rth_session(datetime(2025, 1, 6), [100.0] * 12 + [102.0] * (_N_RTH - 12))
        allts = eth_ts + ts
        allc = np.concatenate([[100.0, 100.0], c])
        sig = OrbFirstHourExpert(n_or=12).signal(_bars_from(allts, allc))
        assert sig.direction[0] == 0 and sig.direction[1] == 0  # ETH bars flat


class TestCausality:
    def test_prefix_invariant_multi_session(self) -> None:
        # Two RTH sessions back-to-back with breakouts; the signal must be causal.
        ts1, c1 = _rth_session(datetime(2025, 1, 6), [100.0] * 12 + [102.0] * (_N_RTH - 12))
        ts2, c2 = _rth_session(datetime(2025, 1, 7), [100.0] * 12 + [98.0] * (_N_RTH - 12))
        bars = _bars_from(ts1 + ts2, np.concatenate([c1, c2]))
        assert_prefix_invariant(OrbFirstHourExpert(n_or=12), bars)

    def test_second_session_resets_opening_range(self) -> None:
        # Session 2's OR must not be contaminated by session 1 (state reset).
        ts1, c1 = _rth_session(datetime(2025, 1, 6), [100.0] * _N_RTH)  # no breakout
        ts2, c2 = _rth_session(datetime(2025, 1, 7), [200.0] * 12 + [202.0] * (_N_RTH - 12))
        sig = OrbFirstHourExpert(n_or=12).signal(_bars_from(ts1 + ts2, np.concatenate([c1, c2])))
        assert np.all(sig.direction[:_N_RTH] == 0)  # session 1 no breakout
        assert np.all(sig.direction[_N_RTH + 12 : 2 * _N_RTH - 1] == 1)  # session 2 breaks out
