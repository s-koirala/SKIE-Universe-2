"""Boundary and DST tests for utils.sessions.session_segment_expr.

The segment classifier is the single source of truth for the CME session
segments consumed by the P3-A substrate check and the H105 overnight expert
(P3-A round-1 audit finding CODE-1-5: script-local classification invites
drift). Boundaries are exchange constants; these tests pin the half-open
interval conventions and the DST awareness of the NY-local conversion.
"""

from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import polars as pl

from skie_universe2.utils.sessions import (
    SEGMENT_HALT_ANOMALY,
    SEGMENT_OVERNIGHT_ETH,
    SEGMENT_POST_RTH_ETH,
    SEGMENT_RTH,
    session_segment_expr,
)

_NY = ZoneInfo("America/New_York")


def _classify(local_dts: list[datetime]) -> list[str]:
    """Classify NY-local datetimes through the UTC-input expression."""
    utc = [dt.replace(tzinfo=_NY).astimezone(UTC).replace(tzinfo=None) for dt in local_dts]
    frame = pl.DataFrame({"ts_event": utc}).with_columns(
        pl.col("ts_event").dt.replace_time_zone("UTC")
    )
    return frame.select(session_segment_expr("ts_event")).get_column("segment").to_list()


class TestBoundaries:
    """Half-open interval edges, one representative non-DST-transition day."""

    def test_rth_open_edge_inclusive(self) -> None:
        assert _classify([datetime(2023, 6, 14, 9, 30)]) == [SEGMENT_RTH]

    def test_pre_open_is_overnight(self) -> None:
        assert _classify([datetime(2023, 6, 14, 9, 25)]) == [SEGMENT_OVERNIGHT_ETH]

    def test_last_rth_label(self) -> None:
        assert _classify([datetime(2023, 6, 14, 15, 55)]) == [SEGMENT_RTH]

    def test_rth_close_edge_exclusive(self) -> None:
        assert _classify([datetime(2023, 6, 14, 16, 0)]) == [SEGMENT_POST_RTH_ETH]

    def test_halt_start_edge(self) -> None:
        assert _classify([datetime(2023, 6, 14, 17, 0)]) == [SEGMENT_HALT_ANOMALY]

    def test_reopen_edge_is_overnight(self) -> None:
        assert _classify([datetime(2023, 6, 14, 18, 0)]) == [SEGMENT_OVERNIGHT_ETH]

    def test_midnight_is_overnight(self) -> None:
        assert _classify([datetime(2023, 6, 15, 0, 0)]) == [SEGMENT_OVERNIGHT_ETH]


class TestDstAwareness:
    """The same UTC hour maps to different segments across the DST switch."""

    def test_winter_vs_summer_utc_offset(self) -> None:
        # 14:30 UTC is 09:30 EST (RTH open) in winter but 10:30 EDT in summer.
        winter = pl.DataFrame({"ts_event": [datetime(2023, 1, 18, 14, 30)]}).with_columns(
            pl.col("ts_event").dt.replace_time_zone("UTC")
        )
        summer = pl.DataFrame({"ts_event": [datetime(2023, 6, 14, 14, 30)]}).with_columns(
            pl.col("ts_event").dt.replace_time_zone("UTC")
        )
        assert winter.select(session_segment_expr()).item() == SEGMENT_RTH
        assert summer.select(session_segment_expr()).item() == SEGMENT_RTH
        # 13:30 UTC: 08:30 EST (overnight) in winter, 09:30 EDT (RTH) in summer.
        w2 = winter.with_columns(pl.col("ts_event").dt.offset_by("-1h"))
        s2 = summer.with_columns(pl.col("ts_event").dt.offset_by("-1h"))
        assert w2.select(session_segment_expr()).item() == SEGMENT_OVERNIGHT_ETH
        assert s2.select(session_segment_expr()).item() == SEGMENT_RTH

    def test_spring_forward_night_stays_overnight(self) -> None:
        # 2021-03-14: 02:00 EST -> 03:00 EDT. Bars either side of the jump
        # (06:55 and 07:05 UTC) are both inside the overnight segment.
        frame = pl.DataFrame(
            {"ts_event": [datetime(2021, 3, 14, 6, 55), datetime(2021, 3, 14, 7, 5)]}
        ).with_columns(pl.col("ts_event").dt.replace_time_zone("UTC"))
        assert frame.select(session_segment_expr()).get_column("segment").to_list() == [
            SEGMENT_OVERNIGHT_ETH,
            SEGMENT_OVERNIGHT_ETH,
        ]
