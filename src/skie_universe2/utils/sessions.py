"""CME trading-session attribution (shared).

Single source of truth for the UTC-timestamp -> CME-session-date rule,
used by both the roll-adjusted ingest (front-month volume attribution)
and the shadow-ledger writer (partition-key integrity, ADR-0003).
Extracted from the 1.0 ``vendor_legacy_1min_roll_adjusted`` module so
the two consumers cannot drift (round-1 audit finding QUANT-1-6).
"""

from __future__ import annotations

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
