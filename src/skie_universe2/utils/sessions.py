"""CME trading-session attribution (shared).

Single source of truth for the UTC-timestamp -> CME-session-date rule,
used by both the roll-adjusted ingest (front-month volume attribution)
and the shadow-ledger writer (partition-key integrity, ADR-0003).
Extracted from the 1.0 ``vendor_legacy_1min_roll_adjusted`` module so
the two consumers cannot drift (round-1 audit finding QUANT-1-6).
"""

from __future__ import annotations

from datetime import time

import polars as pl

CME_TZ = "America/Chicago"
# 17:00 CT is the boundary between CME trading sessions: a trade
# timestamped 17:00 CT on calendar day D-1 belongs to session date D.
# Shifting all bars by +7h in America/Chicago then taking the date
# gives the session date directly. Matches the CME daily-settlement
# convention for non-holiday weekday timestamps.
CME_SESSION_SHIFT_HOURS = 7


def cme_session_date_expr(ts_col: str = "ts_event") -> pl.Expr:
    """Polars expression mapping a UTC timestamp column to CME session date.

    Rule: CME trading session D runs 17:00 CT (day D-1) through 16:00 CT
    (day D). Shifting a local (America/Chicago) timestamp by +7h aligns
    17:00 -> 00:00 of the next calendar day; the date() of the shifted
    timestamp IS the session date.

    Limitations:
      - Does NOT advance past weekend / holiday boundaries (e.g., Friday
        17:01 CT maps to Saturday calendar date, not Monday session).
        Acceptable for front-month volume argmax (weekends/holidays have
        essentially zero volume) and for ledger partition keying (the
        rule is deterministic and applied identically on write and
        validation).
    """
    return (
        pl.col(ts_col)
        .dt.convert_time_zone(CME_TZ)
        .dt.offset_by(f"{CME_SESSION_SHIFT_HOURS}h")
        .dt.date()
    )


# --- Session-segment classification (P3-A / H105; single source of truth so
# the substrate-check harness and the overnight expert cannot drift — the
# same centralization rationale as cme_session_date_expr above, applied per
# round-1 audit finding CODE-1-5 of the P3-A feasibility check).
#
# Segments partition each CME session by NY-local time-of-day (DST-aware).
# All four boundaries are CME exchange-schedule constants for the equity
# index complex, not tunables. Source: CME Group trading-hours schedule for
# equity index futures — Sun-Fri 17:00-16:00 CT with a daily maintenance
# halt 16:00-17:00 CT (= 17:00-18:00 ET), RTH 08:30-15:00 CT (= 09:30-16:00
# ET); https://www.cmegroup.com/trading-hours.html (verified 2026-07-19,
# P3-A round-2 audit LITERATURE-2-2):
NY_TZ = "America/New_York"
RTH_OPEN = time(9, 30)  # justify: CME equity-index RTH open (exchange constant)
RTH_CLOSE = time(16, 0)  # justify: CME equity-index RTH close (exchange constant)
# justify: CME Globex daily maintenance-halt start / reopen, ET (exchange constants)
ETH_HALT_START = time(17, 0)
ETH_REOPEN = time(18, 0)

SEGMENT_OVERNIGHT_ETH = "overnight_eth"
SEGMENT_RTH = "rth"
SEGMENT_POST_RTH_ETH = "post_rth_eth"
SEGMENT_HALT_ANOMALY = "halt_anomaly"


def session_segment_expr(ts_col: str = "ts_event") -> pl.Expr:
    """Polars expression classifying each bar into a session segment.

    Segments (NY-local label time-of-day, DST-aware via tz conversion):
      - ``rth``:           [09:30, 16:00)
      - ``post_rth_eth``:  [16:00, 17:00)
      - ``halt_anomaly``:  [17:00, 18:00) — the daily maintenance halt;
        bars here indicate schedule-variant (holiday/early-close) sessions
      - ``overnight_eth``: >= 18:00 or < 09:30 — the overnight Globex
        segment (18:00 day D-1 -> 09:30 day D of CME session D)
    """
    tod = pl.col(ts_col).dt.convert_time_zone(NY_TZ).dt.time()
    return (
        pl.when((tod >= RTH_OPEN) & (tod < RTH_CLOSE))
        .then(pl.lit(SEGMENT_RTH))
        .when((tod >= RTH_CLOSE) & (tod < ETH_HALT_START))
        .then(pl.lit(SEGMENT_POST_RTH_ETH))
        .when((tod >= ETH_HALT_START) & (tod < ETH_REOPEN))
        .then(pl.lit(SEGMENT_HALT_ANOMALY))
        .otherwise(pl.lit(SEGMENT_OVERNIGHT_ETH))
        .alias("segment")
    )
