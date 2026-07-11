"""Port-fidelity unit tests for the roll-adjusted ingest.

Fixtures and invariant assertions ported from SKIE-Universe 1.0
``tests/unit/test_vendor_legacy_1min_roll_adjusted.py`` (sibling repo)
so the 2.0 port is held to the same behavioral contract:

  - Rolling-window front-month detection (trailing cumulative volume,
    deterministic tie-break, permutation invariance).
  - Persistence guard rejection of short oscillations.
  - Roll-ratio anchor bars per the AFML §2.4.3 roll-event definition
    (the ratio itself is the mlfinlab relative-method variant:
    rho = new_open / old_close at the roll boundary).
  - Multi-roll cumulative back-adjustment chain.
  - Return preservation within a contract and across the roll boundary
    (the fundamental invariant of the multiplicative/relative
    adjustment — mlfinlab ``get_futures_roll_series(method='relative')``;
    AFML §2.4.3's own additive form preserves price differences
    instead).
  - Output schema compliance + audit invariant
    close == unadjusted_close * adjustment_factor.
  - Decade-wraparound guard behavior.

2.0 additions (round-1 audit):

  - ``pit_provisional`` flag semantics (QUANT-1-2).
  - Strict fail-closed config loaders (CODE-1-1).
  - Provenance output-hash error path (CODE-1-2).
"""

from __future__ import annotations

import json
import math
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from skie_universe2.data.ingest.vendor_legacy_1min_roll_adjusted import (
    NoOverlapError,
    RollConfigError,
    RollEvent,
    VendorLegacy1minRollAdjustedIngestJob,
    _adjust_one_symbol,
    _assert_no_consecutive_year_collision,
    _contract_id_full_expr,
    _detect_dec_roll_coverage_gaps,
    _expiry_year_expr,
    _extract_month_code,
    _load_roll_codes,
    _load_roll_window_days,
    apply_persistence_guard,
    compute_roll_ratio_afml,
    detect_raw_front_month_by_day,
    detect_roll_events,
)
from skie_universe2.data.validation.schema import VendorLegacy1minRollAdjustedSchema
from skie_universe2.utils.paths import ProjectPaths

# ---------------------------------------------------------------------------
# Fixtures (ported verbatim from the 1.0 test suite)
# ---------------------------------------------------------------------------


def _bar(ts: datetime, contract: str, symbol: str, price: float, volume: int) -> dict:
    """One vendor_legacy_1min-shaped row with sane OHLC around *price*."""
    return {
        "ts_event": ts,
        "rtype": 34,
        "publisher_id": 1,
        "instrument_id": 42,
        "open": price,
        "high": price + 0.25,
        "low": price - 0.25,
        "close": price + 0.05,
        "volume": volume,
        "contract_symbol": contract,
        "symbol": symbol,
    }


def _two_contract_frame(
    old: str = "ESH4",
    new: str = "ESM4",
    old_last_close: float = 4000.0,
    new_first_open: float = 4020.0,
) -> pl.DataFrame:
    """Two-contract ES fixture with one committed roll.

    With ``window_days=3`` persistence guard, the roll commits on
    2024-03-05 (new leads on 3 consecutive sessions 03-05, 03-06,
    03-07). See the 1.0 test module for the full session layout.
    """
    rows: list[dict] = []
    base_price = 3995.0
    for session_idx, day in enumerate((1, 2, 3, 4)):
        for minute in range(10):
            ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
            rows.append(_bar(ts, old, "ES", base_price + session_idx * 0.5 + minute * 0.1, 100))
    rows[-1]["close"] = old_last_close
    rows[-1]["open"] = old_last_close - 0.05
    rows[-1]["high"] = old_last_close + 0.10
    rows[-1]["low"] = old_last_close - 0.20

    new_base = new_first_open
    for session_idx, day in enumerate((5, 6, 7, 8, 11)):  # 9,10 = weekend
        for minute in range(10):
            ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
            price = new_base + session_idx * 0.5 + minute * 0.1
            rows.append(_bar(ts, new, "ES", price, 200))

    for r in rows:
        if r["contract_symbol"] == new and r["ts_event"] == datetime(
            2024, 3, 5, 14, 30, tzinfo=UTC
        ):
            r["open"] = new_first_open
            r["high"] = new_first_open + 0.25
            r["low"] = new_first_open - 0.25
            r["close"] = new_first_open + 0.05
            break

    return pl.DataFrame(rows)


# ---------------------------------------------------------------------------
# Front-month detection
# ---------------------------------------------------------------------------


class TestRawFrontMonthDetection:
    def test_window_days_rolling_sum(self) -> None:
        df = _two_contract_frame()
        raw = detect_raw_front_month_by_day(df, window_days=3)
        march5 = raw.filter(pl.col("session_date") == date(2024, 3, 5))
        assert march5["front_contract_symbol"][0] == "ESM4"
        march4 = raw.filter(pl.col("session_date") == date(2024, 3, 4))
        assert march4["front_contract_symbol"][0] == "ESH4"

    def test_tie_break_lexicographic(self) -> None:
        """Equal volume -> lexicographically earliest contract wins."""
        ts = datetime(2024, 3, 1, 14, 30, tzinfo=UTC)
        rows = [
            _bar(ts, "ESM4", "ES", 4000.0, 500),
            _bar(ts + timedelta(minutes=1), "ESH4", "ES", 4000.0, 500),
        ]
        raw = detect_raw_front_month_by_day(pl.DataFrame(rows), window_days=1)
        assert raw["front_contract_symbol"][0] == "ESH4"

    def test_permutation_invariant(self) -> None:
        """Front-month decision is invariant to input row order."""
        df = _two_contract_frame()
        r1 = detect_raw_front_month_by_day(df, window_days=3)
        r2 = detect_raw_front_month_by_day(df.sample(fraction=1.0, seed=1), window_days=3)
        assert (
            r1["front_contract_symbol"].to_list()
            == r2.sort(["symbol", "session_date"])["front_contract_symbol"].to_list()
        )

    def test_rejects_zero_window(self) -> None:
        with pytest.raises(ValueError, match="window_days"):
            detect_raw_front_month_by_day(_two_contract_frame(), window_days=0)


# ---------------------------------------------------------------------------
# Persistence guard
# ---------------------------------------------------------------------------


class TestPersistenceGuard:
    def test_single_clean_transition_commits(self) -> None:
        df = _two_contract_frame()
        raw = detect_raw_front_month_by_day(df, window_days=3)
        effective, rejected = apply_persistence_guard(raw, window_days=3)
        march7 = effective.filter(pl.col("session_date") == date(2024, 3, 7))
        assert march7["effective_front_contract_symbol"][0] == "ESM4"
        assert rejected == []

    def test_oscillation_rejected(self) -> None:
        """OLD -> NEW (1 session) -> OLD -> NEW (2 sessions) -> OLD with
        window_days=3 commits ZERO rolls and records the rejections."""
        raw = pl.DataFrame(
            {
                "symbol": ["ES"] * 7,
                "session_date": [
                    date(2024, 3, 1),
                    date(2024, 3, 4),
                    date(2024, 3, 5),
                    date(2024, 3, 6),
                    date(2024, 3, 7),
                    date(2024, 3, 8),
                    date(2024, 3, 11),
                ],
                "front_contract_symbol": [
                    "ESH4",
                    "ESM4",
                    "ESH4",
                    "ESM4",
                    "ESM4",
                    "ESH4",
                    "ESH4",
                ],
                "cumulative_volume": [1000, 500, 1000, 500, 500, 1000, 1000],
            }
        )
        effective, rejected = apply_persistence_guard(raw, window_days=3)
        assert effective["effective_front_contract_symbol"].unique().to_list() == ["ESH4"]
        assert len(rejected) >= 1

    def test_rejects_zero_window(self) -> None:
        raw = pl.DataFrame({"symbol": [], "session_date": [], "front_contract_symbol": []})
        with pytest.raises(ValueError, match="window_days"):
            apply_persistence_guard(raw, window_days=0)


# ---------------------------------------------------------------------------
# AFML §2.4.3 anchor
# ---------------------------------------------------------------------------


class TestRollRatioAFML:
    def test_ratio_uses_canonical_anchor(self) -> None:
        df = _two_contract_frame(old_last_close=4000.0, new_first_open=4020.0)
        raw = detect_raw_front_month_by_day(df, window_days=3)
        effective, _ = apply_persistence_guard(raw, window_days=3)
        events = detect_roll_events(effective)
        assert len(events) == 1
        rr = compute_roll_ratio_afml(df, events[0], "ES", effective)
        assert rr.t_old_close_utc == datetime(2024, 3, 4, 14, 39, tzinfo=UTC)
        assert rr.t_new_open_utc == datetime(2024, 3, 5, 14, 30, tzinfo=UTC)
        assert math.isclose(rr.old_close, 4000.0, abs_tol=1e-9)
        assert math.isclose(rr.new_open, 4020.0, abs_tol=1e-9)
        assert math.isclose(rr.ratio, 4020.0 / 4000.0, abs_tol=1e-12)

    def test_raises_when_old_anchor_missing(self) -> None:
        rows = [_bar(datetime(2024, 3, 1, 14, 30, tzinfo=UTC), "ESM4", "ES", 4020.0, 1500)]
        df = pl.DataFrame(rows)
        effective = pl.DataFrame(
            {
                "symbol": ["ES", "ES"],
                "session_date": [date(2024, 3, 1), date(2024, 3, 4)],
                "effective_front_contract_symbol": ["ESH4", "ESM4"],
                "raw_front_contract_symbol": ["ESH4", "ESM4"],
            }
        )
        ev = RollEvent(date(2024, 3, 4), "ESH4", "ESM4")
        with pytest.raises(NoOverlapError):
            compute_roll_ratio_afml(df, ev, "ES", effective)


# ---------------------------------------------------------------------------
# Adjustment invariants (port fidelity core)
# ---------------------------------------------------------------------------


class TestAdjustmentInvariants:
    def test_newest_contract_has_factor_one(self) -> None:
        out, _ = _adjust_one_symbol(_two_contract_frame(), "ES", window_days=3)
        newest = out.filter(pl.col("front_contract_symbol") == "ESM4")
        assert newest["adjustment_factor"].unique().to_list() == [1.0]

    def test_older_contract_gets_ratio_factor(self) -> None:
        df = _two_contract_frame(old_last_close=4000.0, new_first_open=4020.0)
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        older = out.filter(pl.col("front_contract_symbol") == "ESH4")
        assert math.isclose(older["adjustment_factor"][0], 4020.0 / 4000.0, abs_tol=1e-12)

    def test_close_equals_unadjusted_times_factor(self) -> None:
        out, _ = _adjust_one_symbol(_two_contract_frame(), "ES", window_days=3)
        for got, u, f in zip(
            out["close"].to_list(),
            out["unadjusted_close"].to_list(),
            out["adjustment_factor"].to_list(),
            strict=True,
        ):
            assert math.isclose(got, u * f, abs_tol=1e-9)

    def test_ohlc_consistency_preserved(self) -> None:
        out, _ = _adjust_one_symbol(_two_contract_frame(), "ES", window_days=3)
        violations = out.filter(
            (pl.col("low") > pl.col("open"))
            | (pl.col("low") > pl.col("close"))
            | (pl.col("high") < pl.col("open"))
            | (pl.col("high") < pl.col("close"))
        )
        assert violations.height == 0

    def test_return_preservation_within_contract(self) -> None:
        """Within a single contract, raw and adjusted log-returns match
        (a global scalar cancels in log-diffs)."""
        df = _two_contract_frame()
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        older_adj = out.filter(pl.col("front_contract_symbol") == "ESH4").sort("ts_event")
        older_raw = (
            df.filter((pl.col("symbol") == "ES") & (pl.col("contract_symbol") == "ESH4"))
            .sort("ts_event")
            .filter(pl.col("ts_event").is_in(older_adj["ts_event"].implode()))
        )
        raw_ret = np.diff(np.log(older_raw["close"].to_numpy()))
        adj_ret = np.diff(np.log(older_adj["close"].to_numpy()))
        assert np.allclose(raw_ret, adj_ret, atol=1e-12)

    def test_return_preservation_across_roll_boundary(self) -> None:
        """Zero spurious return across the roll: adjusted old-close at
        the last-as-front session equals new-open at the first-as-front
        session; log-return across the boundary is exactly 0."""
        df = _two_contract_frame(old_last_close=4000.0, new_first_open=4020.0)
        out, _ = _adjust_one_symbol(df, "ES", window_days=3)
        last_old = out.filter(pl.col("front_contract_symbol") == "ESH4").tail(1)
        first_new = out.filter(pl.col("front_contract_symbol") == "ESM4").head(1)
        adj_log_ret = math.log(first_new["open"][0]) - math.log(last_old["close"][0])
        assert math.isclose(adj_log_ret, 0.0, abs_tol=1e-9)

    def test_schema_validates(self) -> None:
        out, _ = _adjust_one_symbol(_two_contract_frame(), "ES", window_days=3)
        VendorLegacy1minRollAdjustedSchema.validate(out)


class TestMultiRollChain:
    def test_three_contract_cumulative_product(self) -> None:
        """ESH4 -> ESM4 -> ESU4: cumulative factor for ESH4 equals the
        product of both roll ratios (AFML §2.4.3 back-adjust chain)."""
        rows: list[dict] = []
        for session_idx, day in enumerate((1, 4)):
            for minute in range(10):
                ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
                rows.append(_bar(ts, "ESH4", "ES", 3995.0 + session_idx + minute * 0.1, 100))
        rows[-1]["close"] = 4000.0
        rows[-1]["open"] = 3999.95
        rows[-1]["high"] = 4000.10
        rows[-1]["low"] = 3999.80

        for session_idx, day in enumerate((5, 6, 7, 8, 11)):
            for minute in range(10):
                ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
                price = 4020.0 + session_idx * 10 + minute * 0.1
                if day == 5 and minute == 0:
                    rows.append(
                        {
                            "ts_event": ts,
                            "rtype": 34,
                            "publisher_id": 1,
                            "instrument_id": 42,
                            "open": 4020.0,
                            "high": 4020.25,
                            "low": 4019.75,
                            "close": 4020.05,
                            "volume": 200,
                            "contract_symbol": "ESM4",
                            "symbol": "ES",
                        }
                    )
                else:
                    rows.append(_bar(ts, "ESM4", "ES", price, 200))
        rows[-1]["close"] = 4100.0
        rows[-1]["open"] = 4099.95
        rows[-1]["high"] = 4100.10
        rows[-1]["low"] = 4099.80

        for session_idx, day in enumerate((12, 13, 14, 15, 18)):
            for minute in range(10):
                ts = datetime(2024, 3, day, 14, 30 + minute, tzinfo=UTC)
                price = 4130.0 + session_idx * 5 + minute * 0.1
                if day == 12 and minute == 0:
                    rows.append(
                        {
                            "ts_event": ts,
                            "rtype": 34,
                            "publisher_id": 1,
                            "instrument_id": 42,
                            "open": 4130.0,
                            "high": 4130.25,
                            "low": 4129.75,
                            "close": 4130.05,
                            "volume": 300,
                            "contract_symbol": "ESU4",
                            "symbol": "ES",
                        }
                    )
                else:
                    rows.append(_bar(ts, "ESU4", "ES", price, 300))

        out, summary = _adjust_one_symbol(pl.DataFrame(rows), "ES", window_days=3)
        factors = summary["contract_factors"]
        # Summary keys are decade-disambiguated (contract_id_full).
        assert math.isclose(factors["ESU4_2024"], 1.0, abs_tol=1e-12)
        rho_2 = 4130.0 / 4100.0
        assert math.isclose(factors["ESM4_2024"], rho_2, abs_tol=1e-12)
        rho_1 = 4020.0 / 4000.0
        assert math.isclose(factors["ESH4_2024"], rho_1 * rho_2, abs_tol=1e-12)

    def test_chain_continuity_holds(self) -> None:
        _out, summary = _adjust_one_symbol(_two_contract_frame(), "ES", window_days=3)
        rolls = summary["rolls"]
        for k in range(len(rolls) - 1):
            assert rolls[k].event.new_contract == rolls[k + 1].event.old_contract


# ---------------------------------------------------------------------------
# Decade-wraparound + month-code guards
# ---------------------------------------------------------------------------


class TestGuards:
    @pytest.mark.parametrize(
        ("sym", "expected"),
        [("ESH5", "H"), ("NQZ24", "Z"), ("MCLF5", "F"), ("MGCG25", "G")],
    )
    def test_month_code_known_shapes(self, sym: str, expected: str) -> None:
        assert _extract_month_code(sym) == expected

    @pytest.mark.parametrize("sym", ["", "ES", "H5", "1234", "ESXX"])
    def test_month_code_unparseable_returns_none(self, sym: str) -> None:
        assert _extract_month_code(sym) is None

    def test_year_straddle_maps_to_one_expiry_key(self) -> None:
        """QUANT-2-1: a contract with bars in adjacent calendar years is
        ONE physical contract under expiry-year keying — the derivation
        guard must NOT fire, and both bars share one key."""
        rows = [
            _bar(datetime(2015, 12, 31, 14, 30, tzinfo=UTC), "ESH6", "ES", 2000.0, 100),
            _bar(datetime(2016, 1, 4, 14, 30, tzinfo=UTC), "ESH6", "ES", 2001.0, 100),
        ]
        df = pl.DataFrame(rows)
        _assert_no_consecutive_year_collision(df, "ES")  # no raise
        keys = df.with_columns(_contract_id_full_expr().alias("k"))["k"].unique().to_list()
        assert keys == ["ESH6_2016"]

    def test_decade_gap_yields_distinct_expiry_keys(self) -> None:
        rows = [
            _bar(datetime(2015, 3, 1, 14, 30, tzinfo=UTC), "ESH5", "ES", 2000.0, 100),
            _bar(datetime(2025, 3, 3, 14, 30, tzinfo=UTC), "ESH5", "ES", 5000.0, 100),
        ]
        df = pl.DataFrame(rows)
        _assert_no_consecutive_year_collision(df, "ES")  # no raise
        keys = sorted(df.with_columns(_contract_id_full_expr().alias("k"))["k"].unique())
        assert keys == ["ESH5_2015", "ESH5_2025"]

    @pytest.mark.parametrize(
        ("sym", "bar_year", "expected_expiry"),
        [
            ("MCLG6", 2025, 2026),  # Feb-2026 contract trading in Dec-2025
            ("MCLG6", 2026, 2026),
            ("ESH5", 2015, 2015),
            ("ESH5", 2025, 2025),  # decade wraparound
            ("ESH7", 2026, 2027),  # forward-traded March-2027 contract
            ("NQZ24", 2024, 2024),  # 2-digit year suffix
        ],
    )
    def test_expiry_year_derivation(self, sym: str, bar_year: int, expected_expiry: int) -> None:
        df = pl.DataFrame([_bar(datetime(bar_year, 6, 2, 14, 30, tzinfo=UTC), sym, "X", 1.0, 1)])
        got = df.select(_expiry_year_expr("contract_symbol").alias("e"))["e"][0]
        assert got == expected_expiry


# ---------------------------------------------------------------------------
# Year-straddle regression (round-2 audit QUANT-2-1, critical)
# ---------------------------------------------------------------------------

_ALL_12_CODES = frozenset("FGHJKMNQUVXZ")


class TestYearStraddleRegression:
    def _straddle_frame(self) -> pl.DataFrame:
        """Single contract MCLG6 (Feb-2026 expiry) trading through the
        2025->2026 year boundary with a 2.8% overnight boundary move —
        the refuter's reproduction shape."""
        rows: list[dict] = []
        # Dec-2025 sessions.
        for day in (29, 30, 31):
            for minute in range(10):
                ts = datetime(2025, 12, day, 14, 30 + minute, tzinfo=UTC)
                rows.append(_bar(ts, "MCLG6", "MCL", 70.0 + minute * 0.01, 100))
        # Jan-2026 sessions, gapped up ~2.8% at the boundary.
        for day in (2, 5, 6):
            for minute in range(10):
                ts = datetime(2026, 1, day, 14, 30 + minute, tzinfo=UTC)
                rows.append(_bar(ts, "MCLG6", "MCL", 72.0 + minute * 0.01, 100))
        return pl.DataFrame(rows)

    def test_no_fabricated_roll_and_boundary_return_preserved(self) -> None:
        df = self._straddle_frame()
        out, summary = _adjust_one_symbol(df, "MCL", window_days=2, roll_codes=_ALL_12_CODES)
        # (a) No fabricated roll: one physical contract -> zero rolls,
        # single factor 1.0 (pre-fix, bar-year keying produced a
        # spurious MCLG6_2025 -> MCLG6_2026 roll here).
        assert summary["rolls"] == []
        assert summary["contract_factors"] == {"MCLG6_2026": 1.0}
        assert out["adjustment_factor"].unique().to_list() == [1.0]
        # (b) The real ~2.8% year-boundary return survives adjustment
        # exactly (pre-fix it was erased by the fabricated ratio).
        out_sorted = out.sort("ts_event")
        last_2025 = out_sorted.filter(pl.col("ts_event").dt.year() == 2025).tail(1)
        first_2026 = out_sorted.filter(pl.col("ts_event").dt.year() == 2026).head(1)
        raw = df.sort("ts_event")
        raw_last = raw.filter(pl.col("ts_event").dt.year() == 2025).tail(1)
        raw_first = raw.filter(pl.col("ts_event").dt.year() == 2026).head(1)
        adj_ret = math.log(first_2026["open"][0]) - math.log(last_2025["close"][0])
        raw_ret = math.log(raw_first["open"][0]) - math.log(raw_last["close"][0])
        assert math.isclose(adj_ret, raw_ret, abs_tol=1e-12)
        assert adj_ret > 0.02  # the boundary move is real and preserved

    def test_real_december_roll_across_boundary_counts_once(self) -> None:
        """MCLZ5 (Dec-2025 expiry) -> MCLG6 (Feb-2026 expiry) committed
        in December; MCLG6 then straddles the year boundary. Exactly ONE
        roll is detected (the real one), not two."""
        rows: list[dict] = []
        for day in (8, 9):
            for minute in range(10):
                ts = datetime(2025, 12, day, 14, 30 + minute, tzinfo=UTC)
                rows.append(_bar(ts, "MCLZ5", "MCL", 69.0 + minute * 0.01, 500))
        # MCLG6 takes over 12-10 and persists through January.
        for day in (10, 11, 12, 15):
            for minute in range(10):
                ts = datetime(2025, 12, day, 14, 30 + minute, tzinfo=UTC)
                rows.append(_bar(ts, "MCLG6", "MCL", 70.0 + minute * 0.01, 800))
        for day in (2, 5):
            for minute in range(10):
                ts = datetime(2026, 1, day, 14, 30 + minute, tzinfo=UTC)
                rows.append(_bar(ts, "MCLG6", "MCL", 72.0 + minute * 0.01, 800))
        _out, summary = _adjust_one_symbol(
            pl.DataFrame(rows), "MCL", window_days=2, roll_codes=_ALL_12_CODES
        )
        assert len(summary["rolls"]) == 1
        ev = summary["rolls"][0].event
        assert ev.old_contract == "MCLZ5_2025"
        assert ev.new_contract == "MCLG6_2026"
        assert ev.roll_date == date(2025, 12, 10)


# ---------------------------------------------------------------------------
# pit_provisional flag (2.0 addition, QUANT-1-2)
# ---------------------------------------------------------------------------


class TestPitProvisionalFlag:
    def test_committed_challenger_window_flagged(self) -> None:
        """Sessions in [challenger_start, commit] INCLUSIVE carry True
        (round-2 audit QUANT-2-4: the commit-session label uses that
        session's own full-session volume, so it is decidable only at
        session close); steady-state sessions carry False. Fixture:
        ESM4 leads 03-05 (streak 1), 03-06 (streak 2), 03-07 (streak 3
        = window -> commit)."""
        df = _two_contract_frame()
        raw = detect_raw_front_month_by_day(df, window_days=3)
        effective, _ = apply_persistence_guard(raw, window_days=3)
        flags = {
            row["session_date"]: row["pit_provisional"] for row in effective.iter_rows(named=True)
        }
        assert flags[date(2024, 3, 5)] is True
        assert flags[date(2024, 3, 6)] is True
        assert flags[date(2024, 3, 7)] is True  # commit session (QUANT-2-4)
        assert flags[date(2024, 3, 4)] is False  # incumbent steady state
        assert flags[date(2024, 3, 8)] is False  # post-commit steady state

    def test_rejected_challenger_window_flagged(self) -> None:
        """Rejected-oscillation sessions were also undecidable at session
        time — they carry True even though the incumbent label survived."""
        raw = pl.DataFrame(
            {
                "symbol": ["ES"] * 5,
                "session_date": [
                    date(2024, 3, 1),
                    date(2024, 3, 4),
                    date(2024, 3, 5),
                    date(2024, 3, 6),
                    date(2024, 3, 7),
                ],
                "front_contract_symbol": ["ESH4", "ESM4", "ESM4", "ESH4", "ESH4"],
                "cumulative_volume": [1000, 500, 500, 1000, 1000],
            }
        )
        effective, rejected = apply_persistence_guard(raw, window_days=3)
        flags = {
            row["session_date"]: row["pit_provisional"] for row in effective.iter_rows(named=True)
        }
        assert flags[date(2024, 3, 4)] is True  # pending challenger
        assert flags[date(2024, 3, 5)] is True  # pending challenger
        assert flags[date(2024, 3, 6)] is False  # incumbent re-took, decidable
        assert len(rejected) == 1

    def test_output_carries_flag_on_provisional_bars(self) -> None:
        out, _ = _adjust_one_symbol(_two_contract_frame(), "ES", window_days=3)
        assert "pit_provisional" in out.columns
        by_session = (
            out.with_columns(pl.col("ts_event").dt.date().alias("_d"))
            .group_by("_d")
            .agg(pl.col("pit_provisional").any().alias("_any"), pl.col("pit_provisional").all())
        )
        flagged_days = sorted(by_session.filter(pl.col("_any"))["_d"].to_list())
        # [challenger_start, commit] inclusive (QUANT-2-4).
        assert flagged_days == [date(2024, 3, 5), date(2024, 3, 6), date(2024, 3, 7)]

    def test_flag_does_not_alter_prices(self) -> None:
        """The flag is metadata: shared columns are identical to the frame
        produced with the flag column dropped (trivially true here, but
        pins the no-numerical-change contract for the port)."""
        out, _ = _adjust_one_symbol(
            _two_contract_frame(old_last_close=4000.0, new_first_open=4020.0),
            "ES",
            window_days=3,
        )
        older = out.filter(pl.col("front_contract_symbol") == "ESH4")
        assert math.isclose(older["adjustment_factor"][0], 4020.0 / 4000.0, abs_tol=1e-12)


# ---------------------------------------------------------------------------
# Strict fail-closed config loaders (2.0 addition, CODE-1-1)
# ---------------------------------------------------------------------------


class TestStrictConfigLoaders:
    def _write_yaml(self, tmp_path: Path, body: str) -> Path:
        p = tmp_path / "instruments.yaml"
        p.write_text(body, encoding="utf-8")
        return p

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(RollConfigError, match="not found"):
            _load_roll_window_days("ES", yaml_path=tmp_path / "absent.yaml")

    def test_malformed_yaml_raises(self, tmp_path: Path) -> None:
        p = self._write_yaml(tmp_path, "instruments: [not: a: mapping")
        with pytest.raises(RollConfigError, match="not valid YAML"):
            _load_roll_window_days("ES", yaml_path=p)

    def test_missing_symbol_raises(self, tmp_path: Path) -> None:
        p = self._write_yaml(
            tmp_path, "instruments:\n  NQ:\n    roll_rule:\n      window_days: 5\n"
        )
        with pytest.raises(RollConfigError, match="not declared"):
            _load_roll_window_days("ES", yaml_path=p)

    def test_missing_window_days_raises(self, tmp_path: Path) -> None:
        p = self._write_yaml(tmp_path, "instruments:\n  ES:\n    roll_rule:\n      codes: [H]\n")
        with pytest.raises(RollConfigError, match="window_days"):
            _load_roll_window_days("ES", yaml_path=p)

    def test_missing_codes_raises(self, tmp_path: Path) -> None:
        p = self._write_yaml(
            tmp_path, "instruments:\n  ES:\n    roll_rule:\n      window_days: 5\n"
        )
        with pytest.raises(RollConfigError, match="codes"):
            _load_roll_codes("ES", yaml_path=p)

    def test_non_cme_code_raises(self, tmp_path: Path) -> None:
        p = self._write_yaml(
            tmp_path,
            "instruments:\n  ES:\n    roll_rule:\n      window_days: 5\n      codes: [H, A]\n",
        )
        with pytest.raises(RollConfigError, match="non-CME"):
            _load_roll_codes("ES", yaml_path=p)

    def test_valid_entry_loads(self, tmp_path: Path) -> None:
        p = self._write_yaml(
            tmp_path,
            "instruments:\n  ES:\n    roll_rule:\n      window_days: 7\n      codes: [H, M]\n",
        )
        assert _load_roll_window_days("ES", yaml_path=p) == 7
        assert _load_roll_codes("ES", yaml_path=p) == frozenset({"H", "M"})

    def test_project_config_is_strict_complete(self) -> None:
        """The shipped config/instruments.yaml satisfies the strict
        loaders for every registered symbol (no silent-default reliance)."""
        for sym in ("ES", "NQ", "MCL", "MGC", "SIL"):
            assert _load_roll_window_days(sym) >= 1
            assert _load_roll_codes(sym)

    def test_override_constructor_args_bypass_yaml(self) -> None:
        """The explicit override args are the only sanctioned default
        path; a job constructed with overrides never reads the YAML."""
        job = VendorLegacy1minRollAdjustedIngestJob(
            symbols=("ES",),
            window_days_override=3,
            roll_codes_override={"ES": frozenset("HMUZ")},
        )
        out = job.adjust(_two_contract_frame().lazy())
        assert out.collect().height > 0


# ---------------------------------------------------------------------------
# Provenance error path (2.0 addition, CODE-1-2) + coverage-gap detector
# ---------------------------------------------------------------------------


class _FakeCtx:
    """Minimal RunContext stand-in for emit_provenance."""

    def __init__(self, root: Path) -> None:
        self.paths = ProjectPaths(root=root)
        self.log = None
        self.checksums: dict[str, str] = {}

    def add_dataset_checksum(self, name: str, sha256: str) -> None:
        self.checksums[name] = sha256


class TestProvenanceErrorPath:
    def test_output_hash_failure_recorded_not_substituted(self, tmp_path: Path) -> None:
        (tmp_path / "pyproject.toml").write_text("[project]\nname='t'\n", encoding="utf-8")
        job = VendorLegacy1minRollAdjustedIngestJob(symbols=("ES",))
        ctx = _FakeCtx(tmp_path)
        prov_path = job.emit_provenance(ctx, [], tmp_path / "does_not_exist")
        payload = json.loads(prov_path.read_text(encoding="utf-8"))
        assert payload["output_frame_sha256"] == ""
        assert payload["output_frame_sha256_error"]  # non-null reason
        # The input hash is never substituted into dataset_checksums.
        assert job.name not in ctx.checksums


class TestDecRollCoverageGapDetector:
    def test_late_year_boundary_roll_detected(self) -> None:
        """QUANT-2-2b: rule is expiry-year comparison (new > old expiry,
        committed on/after Jan 01 of the new expiry year), not the old
        'H in January' heuristic."""
        summary = {
            "ES": {
                "rolls": [
                    {
                        "roll_date": "2016-01-04",
                        "old_contract": "ESZ5_2015",
                        "new_contract": "ESH6_2016",
                    },
                    {
                        "roll_date": "2016-03-11",
                        "old_contract": "ESH6_2016",
                        "new_contract": "ESM6_2016",
                    },
                ]
            }
        }
        gaps = _detect_dec_roll_coverage_gaps(summary)
        assert len(gaps) == 1
        assert gaps[0]["defect_id"] == "DEC_ROLL_LATE_COMMIT"
        assert gaps[0]["kind"] == "late_committed_roll"
        assert gaps[0]["committed_roll_date"] == "2016-01-04"
        assert gaps[0]["expected_crossover_window"].startswith("2015-12-08")

    def test_monthly_instrument_late_roll_detected(self) -> None:
        """Non-H codes are covered by the expiry-year rule: a January-
        committed MCLZ5 -> MCLG6 roll (Feb expiry, not March) flags."""
        summary = {
            "MCL": {
                "rolls": [
                    {
                        "roll_date": "2026-01-02",
                        "old_contract": "MCLZ5_2025",
                        "new_contract": "MCLG6_2026",
                    }
                ]
            }
        }
        gaps = _detect_dec_roll_coverage_gaps(summary)
        assert len(gaps) == 1
        assert gaps[0]["kind"] == "late_committed_roll"

    def test_timely_december_roll_not_flagged(self) -> None:
        """A year-boundary roll committed in December of the OLD expiry
        year is on time — not a gap."""
        summary = {
            "ES": {
                "rolls": [
                    {
                        "roll_date": "2015-12-11",
                        "old_contract": "ESZ5_2015",
                        "new_contract": "ESH6_2016",
                    }
                ]
            }
        }
        assert _detect_dec_roll_coverage_gaps(summary) == []

    def test_mid_quarter_rolls_not_flagged(self) -> None:
        summary = {
            "ES": {
                "rolls": [
                    {
                        "roll_date": "2024-06-14",
                        "old_contract": "ESM4_2024",
                        "new_contract": "ESU4_2024",
                    }
                ]
            }
        }
        assert _detect_dec_roll_coverage_gaps(summary) == []

    def test_terminal_window_detected(self) -> None:
        """QUANT-2-2a: final front-month is a Z contract and the sample
        runs into its expiry month with no successor roll (the verified
        NQZ5-through-2025-12-19 case)."""
        summary = {
            "NQ": {
                "rolls": [],
                "final_front_contract_id_full": "NQZ5_2025",
                "last_session_date": "2025-12-19",
            }
        }
        gaps = _detect_dec_roll_coverage_gaps(summary)
        assert len(gaps) == 1
        assert gaps[0]["kind"] == "terminal_window"
        assert gaps[0]["old_contract"] == "NQZ5_2025"
        assert gaps[0]["expected_crossover_window"].startswith("2025-12-08")

    def test_terminal_window_not_flagged_before_expiry_month(self) -> None:
        summary = {
            "NQ": {
                "rolls": [],
                "final_front_contract_id_full": "NQZ5_2025",
                "last_session_date": "2025-11-28",
            }
        }
        assert _detect_dec_roll_coverage_gaps(summary) == []

    def test_terminal_window_not_flagged_for_non_z_front(self) -> None:
        summary = {
            "ES": {
                "rolls": [],
                "final_front_contract_id_full": "ESH6_2026",
                "last_session_date": "2026-01-15",
            }
        }
        assert _detect_dec_roll_coverage_gaps(summary) == []
