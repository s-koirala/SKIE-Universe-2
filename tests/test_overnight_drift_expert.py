"""Tests for the H105 overnight session-drift expert (design §4: rule + causality).

Pins: the exact flagged label window [18:00, 09:25) NY (DST-aware), the
Tier-0 accrual-disjointness identity vs RTH (design §12(c)), and the
gap-robustness property (no accrual across session-boundary gaps).
"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from skie_universe2.execution.tier0_barclose import tier0_counterfactual
from skie_universe2.experts.base import BarWindow, Expert, assert_prefix_invariant
from skie_universe2.experts.overnight_drift import OvernightSessionDriftExpert
from skie_universe2.utils.sessions import ETH_REOPEN, RTH_CLOSE, RTH_OPEN

_NY = ZoneInfo("America/New_York")


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


def _grid(start_ny: datetime, n_bars: int) -> list[datetime]:
    """Contiguous 5-minute label grid starting at a NY-local datetime."""
    return [start_ny + timedelta(minutes=5 * i) for i in range(n_bars)]


def _full_session_grid(day: datetime) -> list[datetime]:
    """One full CME session: labels 18:00 (D-1) .. 16:55 (D), NY local.

    276 labels = 186 overnight + 78 RTH + 12 post-RTH (no halt bars exist).
    """
    start = datetime(day.year, day.month, day.day, 18, 0, tzinfo=_NY)
    ts = _grid(start, 186)  # 18:00 .. 09:25 next day (overnight segment labels)
    rth_start = ts[-1] + timedelta(minutes=5)
    assert rth_start.timetz().replace(tzinfo=None) == RTH_OPEN
    ts += _grid(rth_start, 78 + 12)  # 09:30 .. 16:55
    return ts


class TestConformance:
    def test_is_expert(self) -> None:
        assert isinstance(OvernightSessionDriftExpert(), Expert)

    def test_expert_id(self) -> None:
        assert OvernightSessionDriftExpert().expert_id == "overnight_session_drift@1.0.0"


class TestRule:
    def test_flag_window_exact_winter(self) -> None:
        # 2025-01-06 18:00 NY (EST) through next day 16:55: flagged bars are
        # exactly the labels [18:00, 09:25) = the first 185 of the 186
        # overnight labels (the 09:25 label itself is un-flagged: the
        # position decided at the 09:20-bar close accrues into the
        # 09:25-labeled row, exiting AT the RTH open).
        ts = _full_session_grid(datetime(2025, 1, 6))
        sig = OvernightSessionDriftExpert().signal(_bars_from(ts, np.full(len(ts), 100.0)))
        assert np.all(sig.direction[:185] == 1)
        assert np.all(sig.direction[185:] == 0)  # 09:25 label + RTH + post-RTH flat
        assert np.all(sig.strength[:185] == 1.0)
        assert np.all(sig.strength[185:] == 0.0)

    def test_flag_window_exact_summer(self) -> None:
        # Same structure under EDT (2025-06-09): DST handled via tz conversion.
        ts = _full_session_grid(datetime(2025, 6, 9))
        sig = OvernightSessionDriftExpert().signal(_bars_from(ts, np.full(len(ts), 100.0)))
        assert np.all(sig.direction[:185] == 1)
        assert np.all(sig.direction[185:] == 0)

    def test_long_only(self) -> None:
        ts = _full_session_grid(datetime(2025, 1, 6))
        sig = OvernightSessionDriftExpert().signal(_bars_from(ts, np.full(len(ts), 100.0)))
        assert set(np.unique(sig.direction)) <= {0, 1}

    def test_rth_never_flagged(self) -> None:
        ts = _full_session_grid(datetime(2025, 1, 6))
        sig = OvernightSessionDriftExpert().signal(_bars_from(ts, np.full(len(ts), 100.0)))
        for t, d in zip(ts, sig.direction, strict=True):
            tod = t.astimezone(_NY).time()
            if RTH_OPEN <= tod < RTH_CLOSE:
                assert d == 0


class TestAccrualDisjointness:
    def test_accrual_rows_strictly_inside_overnight_segment(self) -> None:
        # Design §12(c) identity: with nonzero log-returns everywhere, the
        # Tier-0 counterfactual accrues ONLY on rows labeled inside
        # (18:00, 09:30) NY — never on an RTH or post-RTH row.
        ts = _full_session_grid(datetime(2025, 1, 6))
        closes = 100.0 * np.exp(0.001 * np.arange(len(ts)))  # nonzero r everywhere
        bars = _bars_from(ts, closes)
        sig = OvernightSessionDriftExpert().signal(bars)
        target = sig.direction.astype(np.float64) * sig.strength
        r = np.full(len(ts), np.nan)
        r[1:] = np.log(closes[1:] / closes[:-1])
        cf = tier0_counterfactual(target, r, per_unit_turnover_cost=0.0)
        accrual_rows = np.nonzero(cf.ret_gross != 0.0)[0]
        assert accrual_rows.size == 185  # one per held bar
        for i in accrual_rows:
            tod = ts[i].astimezone(_NY).time()
            in_overnight = tod > ETH_REOPEN or tod < RTH_OPEN
            assert in_overnight, f"accrual row {i} labeled {tod} outside (18:00, 09:30)"

    def test_no_accrual_across_weekend_gap(self) -> None:
        # Friday session tail (ends 16:55) -> Sunday 18:00 reopen. The last
        # pre-gap bar is un-flagged, so no exposure accrues over the gap.
        fri_tail = _grid(datetime(2025, 1, 10, 9, 30, tzinfo=_NY), 78 + 12)  # RTH+post
        sun_open = _grid(datetime(2025, 1, 12, 18, 0, tzinfo=_NY), 10)
        ts = fri_tail + sun_open
        closes = 100.0 * np.exp(0.001 * np.arange(len(ts)))
        bars = _bars_from(ts, closes)
        sig = OvernightSessionDriftExpert().signal(bars)
        target = sig.direction.astype(np.float64) * sig.strength
        r = np.full(len(ts), np.nan)
        r[1:] = np.log(closes[1:] / closes[:-1])
        cf = tier0_counterfactual(target, r, per_unit_turnover_cost=0.0)
        gap_row = len(fri_tail)  # the Sunday 18:00 row accrues Fri 16:55 -> Sun 18:00
        assert cf.ret_gross[gap_row] == 0.0


class TestCausality:
    def test_prefix_invariant_two_sessions(self) -> None:
        ts = _full_session_grid(datetime(2025, 1, 6)) + _full_session_grid(datetime(2025, 1, 7))
        closes = 100.0 * np.exp(0.0005 * np.arange(len(ts)))
        assert_prefix_invariant(OvernightSessionDriftExpert(), _bars_from(ts, closes))
