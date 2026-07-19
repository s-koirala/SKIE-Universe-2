"""H105 overnight/Globex session-drift expert (ADR-0005 Layer 1).

Reference implementation of the H105 frozen design §4 signal
([research/01_hypothesis_register/H105/design.md]) — the long-overnight
risk-premium harvest. Conforms to the
:class:`~skie_universe2.experts.base.Expert` contract and is strictly causal
(passes :func:`assert_prefix_invariant`); the rule is a **pure time-of-day
function** (stateless — causality is structural).

Rule (design §4): direction **+1 (LONG)** on every bar whose NY-local label
time lies in ``[18:00, EXIT)`` where ``EXIT`` = the RTH open minus one
5-minute bar (09:25); **0** otherwise. Under the Tier-0 accrual convention
(a position decided at ``close(t)`` earns ``(t, t+1]``):

- entry at the close of the first bar labeled >= 18:00 (~18:05, the first
  tradable close after the Globex reopen — the 18:00 auction is not claimed);
- exit at the close of the 09:25-labeled bar (~09:30, the RTH open);
- **every accrual row is labeled strictly inside the overnight ETH segment
  (18:00, 09:30)** — bar-disjoint from the ORB pool's RTH accrual rows
  ([10:35, 15:55]) by construction (design §12(c): an identity, not an
  estimate).

The un-flagged band ``[09:25, 18:00)`` guarantees no exposure ever accrues
across a session-boundary data gap (weekends, excluded December windows, the
ES 2025-12-03 truncation): the last bar before any such gap is un-flagged.

**DST-aware:** each bar's ``ts`` (UTC) is converted to ``America/New_York``
(the same convention as :mod:`skie_universe2.experts.orb_first_hour`);
DST-transition Sundays simply shorten/lengthen the flagged window with the
local clock.

Mechanism citations (design §1): Boyarchenko, Larsen & Whelan 2023, Rev.
Financ. Stud. 36(9):3502-3547 (https://doi.org/10.1093/rfs/hhad020);
Lou, Polk & Skouras 2019, J. Financ. Econ. 134:192-213
(https://doi.org/10.1016/j.jfineco.2019.03.011).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import numpy as np

from skie_universe2.experts.base import BarWindow, SignalSeries
from skie_universe2.features.regime_emissions import BAR_MINUTES
from skie_universe2.utils.sessions import ETH_REOPEN, NY_TZ, RTH_OPEN

_NY = ZoneInfo(NY_TZ)
# justify: derived — the last flagged label is one evidence-grid bar before
# the RTH open, so the position exits AT the RTH open (design §4.2); both
# inputs are registered constants (exchange RTH open; H900 §3 bar grid).
_EXIT_LABEL = (datetime.combine(date.min, RTH_OPEN) - timedelta(minutes=BAR_MINUTES)).time()


class OvernightSessionDriftExpert:
    """Long-overnight session-drift signal (H105 design §4)."""

    def __init__(self, version: str = "1.0.0") -> None:
        self._version = version

    @property
    def expert_id(self) -> str:
        return f"overnight_session_drift@{self._version}"

    def fit(self, train: BarWindow) -> None:  # stateless rule
        return None

    def signal(self, bars: BarWindow) -> SignalSeries:
        n = len(bars)
        direction = np.zeros(n, dtype=np.int8)
        strength = np.zeros(n, dtype=np.float64)
        for t in range(n):
            tod = bars.ts[t].astimezone(_NY).time()
            if tod >= ETH_REOPEN or tod < _EXIT_LABEL:
                direction[t] = np.int8(1)
                strength[t] = 1.0
        return SignalSeries(direction=direction, strength=strength)
