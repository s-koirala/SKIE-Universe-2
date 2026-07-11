"""Rolling-origin estimation windows for the H900 dwell-time study.

Implements the window arithmetic registered in
research/01_hypothesis_register/H900/design.md §2 (ADR-0004 Decision 2):
training window 24 months, step 6 months, first origin 2017-01-01,
yielding exactly 15 windows. Each window's evaluation span is the
6-month step interval that follows its origin; state inference in the
evaluation span is out-of-sample with respect to the training fit.

Boundary convention: all boundaries are half-open UTC-date boundaries
``[start, end)`` applied to the bar timestamp column (``ts_event``,
UTC). The design registers calendar-date boundaries; UTC-midnight
interpretation is deterministic and identical on write and read.

References
----------

- Tashman 2000, Int. J. Forecast. 16:437-450
  (https://doi.org/10.1016/S0169-2070(00)00065-0)
- Bergmeir & Benitez 2012, Inf. Sci. 191:192-213
  (https://doi.org/10.1016/j.ins.2011.12.028)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

# All three registered by H900 design.md §2 ("training window 24 months,
# step 6 months, first origin 2017-01-01 — yielding 15 evaluation
# windows"); the design's own justification: 24m is the shortest window
# with stable BIC selection in the 1.0 HMM toolkit validation, 6m is the
# ADR-0004 reporting cadence, neither tuned against the outcome.
TRAIN_MONTHS = 24  # justify: H900 design.md §2 (registered a priori)
STEP_MONTHS = 6  # justify: H900 design.md §2 (registered a priori)
FIRST_ORIGIN = date(2017, 1, 1)  # justify: H900 design.md §2 (registered a priori)
N_WINDOWS = 15  # justify: H900 design.md §2/§9 ("fixed by §2 arithmetic")


def _add_months(d: date, months: int) -> date:
    """Add calendar months to a date (day-of-month preserved; all H900
    boundaries are month-firsts so no clamping is ever needed)."""
    total = d.year * 12 + (d.month - 1) + months
    year, month = divmod(total, 12)
    if d.day != 1:
        raise ValueError(f"H900 window boundaries must be month-firsts; got {d}.")
    return date(year, month + 1, 1)


@dataclass(frozen=True)
class RollingWindow:
    """One rolling-origin window.

    ``train_start <= ts < origin`` is the training span (before purge);
    ``origin <= ts < eval_end`` is the evaluation span (before embargo).
    Purge (bars) and embargo (bars) are applied by the caller in bar
    space, per design.md §6.
    """

    window_id: int
    train_start: date
    origin: date
    eval_end: date


def h900_windows() -> tuple[RollingWindow, ...]:
    """Return the 15 registered H900 rolling-origin windows."""
    windows = []
    for k in range(N_WINDOWS):
        origin = _add_months(FIRST_ORIGIN, STEP_MONTHS * k)
        windows.append(
            RollingWindow(
                window_id=k,
                train_start=_add_months(origin, -TRAIN_MONTHS),
                origin=origin,
                eval_end=_add_months(origin, STEP_MONTHS),
            )
        )
    return tuple(windows)
