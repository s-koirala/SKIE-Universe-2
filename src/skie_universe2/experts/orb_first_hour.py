"""H101 first-hour opening-range-breakout expert (ADR-0005 Layer 1).

Reference implementation of the H101 frozen design §4 signal
([research/01_hypothesis_register/H101/design.md]) — the unconditional first-hour
ORB. Conforms to the :class:`~skie_universe2.experts.base.Expert` contract and is
strictly causal (passes :func:`assert_prefix_invariant`). Per RTH session:

1. **Opening range** over the first ``n_or`` RTH bars: running ``OR_high``/``OR_low``.
2. **Breakout entry (first only):** from the bar after the OR window, the first RTH
   bar whose CLOSE exceeds ``OR_high`` (established through the prior bar) goes LONG;
   the first whose close is below ``OR_low`` goes SHORT. Close-confirmation, not
   intra-bar touch, so it is computable at bar close and Tier-0-fillable without
   look-ahead.
3. **Exit:** flat at the last RTH-bar label ``[15:55, 16:00)`` so no position accrues
   over the overnight gap (a position decided at ``close(t)`` earns ``(t, t+1]``, so
   holding the 15:55 bar would accrue the overnight return). The 15:50 bar holds the
   last intraday return. One round-trip per session.
4. **No breakout / outside RTH:** flat.

**RTH is DST-aware:** each bar's ``ts`` (UTC) is converted to ``America/New_York``;
RTH is the local window ``[09:30, 16:00)`` (the CME equity-index regular session, an
exchange constant). Session = the NY local calendar date.

**Known limitation (documented):** early-close sessions (holiday half-days, ~9/yr,
RTH close 13:00 ET) are not specially handled — their last RTH bar is not the 15:55
label, so a held position accrues that day's overnight return. Negligible over the
backfill; refining it needs the exchange half-day calendar (not in-repo). Flagged
for a follow-up; does not affect normal sessions.
"""

from __future__ import annotations

from datetime import time
from zoneinfo import ZoneInfo

import numpy as np

from skie_universe2.experts.base import BarWindow, SignalSeries

_NY = ZoneInfo("America/New_York")
_RTH_OPEN = time(9, 30)  # justify: CME equity-index RTH open (exchange constant)
_RTH_CLOSE = time(16, 0)  # justify: CME equity-index RTH close (exchange constant)
_LAST_RTH_LABEL = time(
    15, 55
)  # justify: last 5-min RTH bar label; exit here → no overnight accrual
_DEFAULT_N_OR = (
    12  # justify: first-hour (60 min) opening range, the 1.0 H052a definition (design §3)
)


class OrbFirstHourExpert:
    """Unconditional first-hour opening-range-breakout signal (H101 design §4)."""

    def __init__(self, n_or: int = _DEFAULT_N_OR, version: str = "1.0.0") -> None:
        if n_or < 1:
            raise ValueError(f"n_or must be >= 1, got {n_or}")
        self._n_or = n_or
        self._version = version

    @property
    def expert_id(self) -> str:
        return f"orb_first_hour@{self._version}"

    def fit(self, train: BarWindow) -> None:  # stateless rule
        return None

    def signal(self, bars: BarWindow) -> SignalSeries:  # noqa: PLR0912 — one causal session pass
        n = len(bars)
        direction = np.zeros(n, dtype=np.int8)
        strength = np.zeros(n, dtype=np.float64)
        high, low, close = bars.high, bars.low, bars.close

        cur_session = None
        or_high = -np.inf
        or_low = np.inf
        n_rth = 0
        entered = 0
        for t in range(n):
            local = bars.ts[t].astimezone(_NY)
            sd = local.date()
            tod = local.time()
            if sd != cur_session:  # new NY session → reset ORB state (fires during ETH/overnight)
                cur_session = sd
                or_high, or_low, n_rth, entered = -np.inf, np.inf, 0, 0
            if not (_RTH_OPEN <= tod < _RTH_CLOSE):
                continue  # outside RTH → flat
            if tod >= _LAST_RTH_LABEL:
                continue  # exit at RTH close → flat (no overnight accrual)
            if n_rth < self._n_or:  # inside the opening-range window → flat
                or_high = max(or_high, float(high[t]))
                or_low = min(or_low, float(low[t]))
                n_rth += 1
                continue
            if entered == 0:  # first breakout only (close-confirmation)
                if close[t] > or_high:
                    entered = 1
                elif close[t] < or_low:
                    entered = -1
            if entered != 0:
                direction[t] = np.int8(entered)
                strength[t] = 1.0
        return SignalSeries(direction=direction, strength=strength)
