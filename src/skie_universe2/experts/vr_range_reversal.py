"""H106 variance-ratio range-state reversal expert (ADR-0005 Layer 1).

Reference implementation of the H106 frozen design §4 signal
([research/01_hypothesis_register/H106/design.md]) — a one-bar contrarian
rule gated on the REGISTERED ``variance_ratio_state`` feature. Conforms to
the :class:`~skie_universe2.experts.base.Expert` contract and is strictly
causal (passes :func:`assert_prefix_invariant`).

Rule (design §4): with r_t = log(close_t / close_{t-1}) and s_t the trailing
variance-ratio state (registered constants: window 288 bars, lag q = 2 —
``features/variance_ratio_state.py``):

- direction_t = **−sign(r_t)** iff s_t = RANGE (VR(2) < 1 → negative
  first-lag autocorrelation; the AR(1) conditional-mean sign is opposite
  the last return) AND r_t ≠ 0 AND the bar is not the session's terminal
  label; else 0. One-bar hold, re-decided every bar.
- **No cross-gap accrual:** direction is forced 0 on the session's last
  5-minute label (``ETH_HALT_START − BAR_MINUTES`` = 16:55 NY, derived
  from exchange constants), so no position accrues across the maintenance
  halt, weekends, or exclusion gaps. Documented limitation (ORB
  precedent): holiday early-close sessions (~9/yr) end before 16:55 and
  their true last bar can accrue the gap return; not special-cased.

The VR state is computed on the contiguous valid-bar return sequence as
stored (the registered ``rvol_5m_24h`` continuous-sequence convention;
design §3). Warm-up (UNDETERMINED) → flat.

Mechanism citations (design §1): Lo & MacKinlay 1988, Rev. Financ. Stud.
1(1):41-66 (https://doi.org/10.1093/rfs/1.1.41); Lo & MacKinlay 1990, Rev.
Financ. Stud. 3(2):175-205 (https://doi.org/10.1093/rfs/3.2.175).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from skie_universe2.experts.base import BarWindow, SignalSeries
from skie_universe2.features.regime_emissions import BAR_MINUTES
from skie_universe2.features.variance_ratio_state import (
    VR_LAG_Q,
    VR_WINDOW_BARS,
    VarianceRatioState,
    variance_ratio_state,
)
from skie_universe2.utils.sessions import ETH_HALT_START, NY_TZ

_NY = ZoneInfo(NY_TZ)
# justify: derived — the session's last 5-minute label is one evidence-grid
# bar before the daily maintenance halt (design §4.3); both inputs are
# registered constants (exchange halt start; H900 §3 bar grid).
_SESSION_LAST_LABEL = (
    datetime.combine(date.min, ETH_HALT_START) - timedelta(minutes=BAR_MINUTES)
).time()
_MIN_BARS_FOR_RETURN = 2  # justify: structural — one return needs two closes


class VrRangeReversalExpert:
    """Range-state one-bar contrarian signal (H106 design §4)."""

    def __init__(self, version: str = "1.0.0") -> None:
        self._version = version

    @property
    def expert_id(self) -> str:
        return f"vr_range_reversal@{self._version}"

    def fit(self, train: BarWindow) -> None:  # stateless rule
        return None

    def signal(self, bars: BarWindow) -> SignalSeries:
        n = len(bars)
        direction = np.zeros(n, dtype=np.int8)
        strength = np.zeros(n, dtype=np.float64)
        if n < _MIN_BARS_FOR_RETURN:
            return SignalSeries(direction=direction, strength=strength)
        close = bars.close
        r = np.log(close[1:] / close[:-1])  # r[j] = return over bar j+1
        # Trailing VR state through return j (bar j+1); registered constants.
        state_r = variance_ratio_state(r, window=VR_WINDOW_BARS, q=VR_LAG_Q)
        for t in range(1, n):
            rt = r[t - 1]
            if state_r[t - 1] != VarianceRatioState.RANGE or not np.isfinite(rt) or rt == 0.0:
                continue
            if bars.ts[t].astimezone(_NY).time() == _SESSION_LAST_LABEL:
                continue  # session terminal label → flat (no cross-gap accrual)
            direction[t] = np.int8(-1 if rt > 0 else 1)
            strength[t] = 1.0
        return SignalSeries(direction=direction, strength=strength)
