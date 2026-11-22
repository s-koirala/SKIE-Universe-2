"""H107 session-VWAP × EMA(9) crossover expert (ADR-0005 Layer 1) — DRAFT.

Reference implementation of the H107 DRAFT design §4 signal
([research/01_hypothesis_register/H107/design.md]). The design is NOT frozen:
this module may change until `/preregister` freezes the design SHA, after which
any rule change requires a new HID. Conforms to the
:class:`~skie_universe2.experts.base.Expert` contract and is strictly causal
(passes :func:`assert_prefix_invariant`).

Rule (draft design §4), on the 5-minute evidence grid:

- ``EMA9_t`` — exponential moving average of the 5-minute CLOSE, span 9
  (alpha = 2 / (9 + 1)), run continuously over the contiguous stored bar
  sequence (all segments, the charting-platform convention), seeded with the
  first close.
- ``VWAP_t`` — RTH-session-anchored VWAP: cumulative
  ``sum(typical_price * volume) / sum(volume)`` over the session's RTH bars
  from the first bar labeled >= 09:30 NY through bar ``t`` inclusive;
  typical price = (high + low + close) / 3. Resets each NY session date.
- **direction_t = sign(EMA9_t − VWAP_t)** on RTH decision bars labeled in
  ``[09:30, 15:55)``; 0 if the difference is exactly 0 or VWAP is undefined
  (zero cumulative volume). Always-in during RTH: the "crossover" is the
  sign change of (EMA9 − VWAP), i.e. stop-and-reverse.
- **Flat outside RTH and on the 15:55 label** — under the Tier-0 accrual
  convention (a position decided at ``close(t)`` earns ``(t, t+1]``) holding
  the 15:55 bar would accrue the overnight gap (ORB precedent). Documented
  limitation inherited from ORB: holiday early-close sessions (~9/yr) are not
  special-cased.

Strength is constant 1.0 on held bars (size is the Layer-2 Kelly fraction).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from skie_universe2.experts.base import BarWindow, SignalSeries
from skie_universe2.features.regime_emissions import BAR_MINUTES
from skie_universe2.utils.sessions import NY_TZ, RTH_CLOSE, RTH_OPEN

_NY = ZoneInfo(NY_TZ)
EMA_SPAN = 9  # justify: the strategy as specified by the principal (2026-11-22) — "9 EMA"
_EMA_ALPHA = 2.0 / (EMA_SPAN + 1.0)  # justify: standard span→alpha EMA convention
# justify: derived — last RTH 5-minute label (one grid bar before the RTH
# close); flat here so no position accrues over the overnight gap.
_LAST_RTH_LABEL = (datetime.combine(date.min, RTH_CLOSE) - timedelta(minutes=BAR_MINUTES)).time()


def ema(close: np.ndarray, span: int = EMA_SPAN) -> np.ndarray:
    """Causal recursive EMA seeded with the first value (NaN-propagation-free)."""
    alpha = 2.0 / (span + 1.0)
    out = np.empty_like(close, dtype=np.float64)
    if close.size == 0:
        return out
    acc = float(close[0])
    for i, c in enumerate(close):
        acc = alpha * float(c) + (1.0 - alpha) * acc if i else acc
        out[i] = acc
    return out


def session_vwap(bars: BarWindow) -> np.ndarray:
    """RTH-anchored cumulative VWAP per NY session date; NaN outside RTH."""
    n = len(bars)
    out = np.full(n, np.nan)
    tp = (bars.high + bars.low + bars.close) / 3.0
    cur = None
    pv = vol = 0.0
    for t in range(n):
        local = bars.ts[t].astimezone(_NY)
        if not (RTH_OPEN <= local.time() < RTH_CLOSE):
            continue
        if local.date() != cur:  # first RTH bar of a new session → reset anchor
            cur, pv, vol = local.date(), 0.0, 0.0
        v = float(bars.volume[t])
        if np.isfinite(v) and v > 0.0 and np.isfinite(tp[t]):
            pv += float(tp[t]) * v
            vol += v
        if vol > 0.0:
            out[t] = pv / vol
    return out


class VwapEmaCrossExpert:
    """Session-VWAP × EMA(9) stop-and-reverse RTH signal (H107 draft §4)."""

    def __init__(self, version: str = "0.1.0-draft") -> None:
        self._version = version

    @property
    def expert_id(self) -> str:
        return f"vwap_ema9_cross@{self._version}"

    def fit(self, train: BarWindow) -> None:  # stateless rule
        return None

    def signal(self, bars: BarWindow) -> SignalSeries:
        n = len(bars)
        direction = np.zeros(n, dtype=np.int8)
        strength = np.zeros(n, dtype=np.float64)
        if n == 0:
            return SignalSeries(direction=direction, strength=strength)
        e = ema(bars.close)
        vw = session_vwap(bars)
        for t in range(n):
            if not np.isfinite(vw[t]) or bars.ts[t].astimezone(_NY).time() >= _LAST_RTH_LABEL:
                continue  # outside RTH / undefined VWAP / terminal RTH label → flat
            d = e[t] - vw[t]
            if d > 0.0:
                direction[t] = np.int8(1)
            elif d < 0.0:
                direction[t] = np.int8(-1)
            else:
                continue
            strength[t] = 1.0
        return SignalSeries(direction=direction, strength=strength)
