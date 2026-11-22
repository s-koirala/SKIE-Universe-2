"""H107 session-VWAP × EMA(N) crossover expert (ADR-0005 Layer 1).

Reference implementation of the H107 design §4 signal
([research/01_hypothesis_register/H107/design.md]). Conforms to the
:class:`~skie_universe2.experts.base.Expert` contract and is strictly causal
(passes :func:`assert_prefix_invariant`). The EMA span ``N`` is a member of
the registered grid :data:`EMA_SPAN_GRID` (design §4/§5: every grid point is
a separate expert id and a separate registered trial; none is hand-picked).

Rule (design §4), on the 5-minute evidence grid:

- ``EMA_N(t)`` — exponential moving average of the 5-minute CLOSE, span ``N``
  (alpha = 2 / (N + 1)), run continuously over the contiguous stored bar
  sequence (the charting-platform convention), seeded with the first close.
- ``VWAP(t)`` — CME-trading-session-anchored VWAP: cumulative
  ``sum(typical * volume) / sum(volume)`` over every bar of the current CME
  session (opens 17:00 CT = 18:00 ET; Sunday 17:00 CT opens Monday's session)
  through bar ``t`` inclusive; typical = (high + low + close) / 3. Resets at
  each session boundary.
- **direction(t) = sign(EMA_N(t) − VWAP(t))** on every decision bar inside
  the trading window; 0 on ties / undefined VWAP (zero cumulative volume).
  Always-in (stop-and-reverse) inside the window.
- **Trading window (principal direction 2026-11-22, Central Time):** flat
  from 15:00 CT until the 17:00 CT reopen; 24-hour trading otherwise.
  In NY-local labels: positions are decided on labels outside
  ``[15:55, 18:00)`` ET. Under the Tier-0 accrual convention (a position
  decided at ``close(t)`` earns ``(t, t+1]``) the last held decision label
  15:50 ET earns to 16:00 ET = 15:00 CT; the first new decision is the close
  of the 18:00 ET (17:00 CT) bar. Weekends are covered by the same rule
  (Friday flat at 15:00 CT; Sunday reopen 17:00 CT).

Documented limitation (ORB/H106 precedent): holiday early-close sessions are
not special-cased (no exchange holiday calendar in-repo) — the last bar before
an early halt can accrue the gap to the next reopen.

Strength is constant 1.0 on held bars (size is the Layer-2 Kelly fraction).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from skie_universe2.experts.base import BarWindow, SignalSeries
from skie_universe2.features.regime_emissions import BAR_MINUTES
from skie_universe2.utils.sessions import ETH_REOPEN, NY_TZ, RTH_CLOSE

_NY = ZoneInfo(NY_TZ)
# justify: registered grid (design §4/§5) — log-spaced (~1.6x ratio,
# Fibonacci-like) spans covering 15 min .. ~4.6 h of 5-min bars; includes
# the principal-specified 9. Each point = one expert id = one trial per
# instrument (14 screen trials).
EMA_SPAN_GRID: tuple[int, ...] = (3, 5, 9, 13, 21, 34, 55)
PRIMARY_EMA_SPAN = 9  # justify: the principal's original specification (2026-11-22)
# justify: derived — flat-from label = one grid bar before 16:00 ET (15:00 CT)
# so no position accrues past 15:00 CT; registered exchange/bar constants.
FLAT_FROM_LABEL = (datetime.combine(date.min, RTH_CLOSE) - timedelta(minutes=BAR_MINUTES)).time()
REOPEN_LABEL = ETH_REOPEN  # 18:00 ET = 17:00 CT CME Globex reopen (exchange constant)


def ema(close: np.ndarray, span: int) -> np.ndarray:
    """Causal recursive EMA (alpha = 2/(span+1)) seeded with the first value."""
    if span < 1:
        raise ValueError(f"span must be >= 1, got {span}")
    alpha = 2.0 / (span + 1.0)
    out = np.empty(close.shape, dtype=np.float64)
    if close.size == 0:
        return out
    acc = float(close[0])
    out[0] = acc
    for i in range(1, close.size):
        acc = alpha * float(close[i]) + (1.0 - alpha) * acc
        out[i] = acc
    return out


def cme_session_of(ts: datetime) -> date:
    """CME trading-session date: bars labeled >= 18:00 ET belong to the next day."""
    local = ts.astimezone(_NY)
    return local.date() + timedelta(days=1) if local.time() >= REOPEN_LABEL else local.date()


def session_vwap(bars: BarWindow) -> np.ndarray:
    """CME-session-anchored cumulative VWAP; NaN until the session has volume."""
    n = len(bars)
    out = np.full(n, np.nan)
    tp = (bars.high + bars.low + bars.close) / 3.0
    cur = None
    pv = vol = 0.0
    for t in range(n):
        sd = cme_session_of(bars.ts[t])
        if sd != cur:  # first bar of a new CME session → reset the anchor
            cur, pv, vol = sd, 0.0, 0.0
        v = float(bars.volume[t])
        if np.isfinite(v) and v > 0.0 and np.isfinite(tp[t]):
            pv += float(tp[t]) * v
            vol += v
        if vol > 0.0:
            out[t] = pv / vol
    return out


def in_trading_window(ts: datetime) -> bool:
    """True iff a position may be decided at this bar's close (design §4)."""
    tod = ts.astimezone(_NY).time()
    return not (FLAT_FROM_LABEL <= tod < REOPEN_LABEL)


class VwapEmaCrossExpert:
    """Session-VWAP × EMA(span) stop-and-reverse signal (H107 design §4)."""

    def __init__(self, span: int = PRIMARY_EMA_SPAN, version: str = "1.0.0") -> None:
        if span < 1:
            raise ValueError(f"span must be >= 1, got {span}")
        self._span = int(span)
        self._version = version

    @property
    def span(self) -> int:
        return self._span

    @property
    def expert_id(self) -> str:
        return f"vwap_ema{self._span}_cross@{self._version}"

    def fit(self, train: BarWindow) -> None:  # stateless rule
        return None

    def signal(self, bars: BarWindow) -> SignalSeries:
        n = len(bars)
        direction = np.zeros(n, dtype=np.int8)
        strength = np.zeros(n, dtype=np.float64)
        if n == 0:
            return SignalSeries(direction=direction, strength=strength)
        e = ema(bars.close, self._span)
        vw = session_vwap(bars)
        for t in range(n):
            if not np.isfinite(vw[t]) or not in_trading_window(bars.ts[t]):
                continue
            d = e[t] - vw[t]
            if d > 0.0:
                direction[t] = np.int8(1)
            elif d < 0.0:
                direction[t] = np.int8(-1)
            else:
                continue
            strength[t] = 1.0
        return SignalSeries(direction=direction, strength=strength)
