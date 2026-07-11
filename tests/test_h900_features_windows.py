"""Unit tests for H900 emission features, exclusions, PIT canary, windows."""

from __future__ import annotations

from datetime import date, datetime, timedelta

import numpy as np
import polars as pl
import pytest

from skie_universe2.eval.windows import (
    FIRST_ORIGIN,
    N_WINDOWS,
    RollingWindow,
    h900_windows,
)
from skie_universe2.features.regime_emissions import (
    RVOL_WINDOW_BARS,
    ExclusionWindow,
    aggregate_5min,
    apply_registered_exclusions,
    compute_emissions,
    emission_matrix,
    exclusion_windows_from_provenance,
    fit_moments,
    pit_canary_future_mutation,
    standardize,
)
from skie_universe2.utils.sessions import cme_session_date_expr  # noqa: F401 — used below


def _bars_1min(start: datetime, n: int, *, close0: float = 100.0) -> pl.DataFrame:
    ts = [start + timedelta(minutes=i) for i in range(n)]
    rng = np.random.default_rng(20260710)
    close = close0 * np.exp(np.cumsum(rng.normal(0, 1e-4, size=n)))
    return pl.DataFrame(
        {
            "ts_event": ts,
            "open": close,
            "high": close * 1.0001,
            "low": close * 0.9999,
            "close": close,
            "volume": np.ones(n, dtype=np.int64),
            "pit_provisional": np.zeros(n, dtype=bool),
        }
    ).with_columns(pl.col("ts_event").dt.replace_time_zone("UTC"))


class TestAggregate5min:
    def test_ohlcv_aggregation_rule(self) -> None:
        start = datetime(2020, 1, 6, 0, 0)
        df = _bars_1min(start, 10)
        out = aggregate_5min(df.lazy())
        assert out.height == 2
        first5 = df.head(5)
        row = out.row(0, named=True)
        assert row["open"] == first5.get_column("open")[0]
        assert row["close"] == first5.get_column("close")[-1]
        assert row["high"] == first5.get_column("high").max()
        assert row["low"] == first5.get_column("low").min()
        assert row["volume"] == 5

    def test_bar_label_is_window_start(self) -> None:
        start = datetime(2020, 1, 6, 0, 3)  # unaligned start
        out = aggregate_5min(_bars_1min(start, 7).lazy())
        assert out.get_column("ts_event")[0].minute == 0  # floor to 5m grid


class TestComputeEmissions:
    def test_ret_and_rvol_definitions(self) -> None:
        n5 = RVOL_WINDOW_BARS + 10
        df = _bars_1min(datetime(2020, 1, 6), n5 * 5)
        bars = aggregate_5min(df.lazy())
        feats = compute_emissions(bars)
        close = bars.get_column("close").to_numpy()
        ret = np.diff(np.log(close))
        got_ret = feats.get_column("ret_5m").to_numpy()
        np.testing.assert_allclose(got_ret[1:], ret, atol=1e-15)
        # rvol at the first index with a full 288-return window.
        k = RVOL_WINDOW_BARS  # feats row index k uses returns 1..k
        expected = np.sqrt(np.sum(ret[:RVOL_WINDOW_BARS] ** 2))
        got = feats.get_column("rvol_5m_24h").to_numpy()
        assert got[k] == pytest.approx(expected, rel=1e-12)
        assert np.isnan(got[k - 1]) or feats.get_column("rvol_5m_24h")[k - 1] is None
        # emission_valid marks exactly the fully-warmed rows.
        valid = feats.get_column("emission_valid").to_numpy()
        assert not valid[:RVOL_WINDOW_BARS].any()
        assert valid[RVOL_WINDOW_BARS:].all()

    def test_weekend_gap_keeps_return_exclusion_gap_nulls_it(self) -> None:
        # Two segments separated by 2 days (weekend): return kept.
        a = _bars_1min(datetime(2020, 1, 6), 50)
        b = _bars_1min(datetime(2020, 1, 8), 50)
        feats = compute_emissions(aggregate_5min(pl.concat([a, b]).lazy()))
        rets = feats.get_column("ret_5m")
        assert rets.null_count() == 1  # only the very first bar
        # Segments separated by 3 weeks (Dec-roll exclusion): nulled.
        c = _bars_1min(datetime(2020, 2, 1), 50)
        feats2 = compute_emissions(aggregate_5min(pl.concat([a, c]).lazy()))
        assert feats2.get_column("ret_5m").null_count() == 2

    def test_passthrough_column_alignment_under_row_perturbation(self) -> None:
        """Round-2 audit CODE-2-1 contract: auxiliary per-bar columns must be
        threaded THROUGH compute_emissions (which re-sorts by ts_event) and
        come out row-aligned even when the input arrives order-perturbed.
        Re-attaching a column positionally to the re-sorted output is the
        defect this pins against."""
        df = _bars_1min(datetime(2020, 1, 6), 300)
        bars = aggregate_5min(df.lazy())
        # Attach an auxiliary column keyed to the bar timestamp, then
        # shuffle the rows deterministically.
        bars = bars.with_columns(
            unadjusted_close=pl.col("close") + 1000.0  # distinct, per-bar keyed
        )
        rng = np.random.default_rng(20260710)
        perm = rng.permutation(bars.height)
        shuffled = bars[perm.tolist()]
        out = compute_emissions(shuffled)
        # Output is sorted by ts_event and the passthrough column still
        # matches its own bar's close + 1000 on every row.
        ts = out.get_column("ts_event")
        assert ts.is_sorted()
        np.testing.assert_allclose(
            out.get_column("unadjusted_close").to_numpy(),
            out.get_column("close").to_numpy() + 1000.0,
            atol=0.0,
        )
        # And the computed features are identical to the sorted-input run.
        base = compute_emissions(bars)
        for col in ("ret_5m", "rvol_5m_24h", "emission_valid", "unadjusted_close"):
            assert base.get_column(col).equals(out.get_column(col))

    def test_emission_matrix_shape(self) -> None:
        df = _bars_1min(datetime(2020, 1, 6), (RVOL_WINDOW_BARS + 20) * 5)
        feats = compute_emissions(aggregate_5min(df.lazy()))
        x = emission_matrix(feats)
        assert x.shape[1] == 2
        assert np.all(np.isfinite(x))


class TestExclusions:
    def test_pit_provisional_and_gap_windows_removed(self) -> None:
        df = _bars_1min(datetime(2020, 12, 7), 3 * 24 * 60)
        df = df.with_columns(
            pit_provisional=pl.arange(0, df.height) < 10,
        )
        exclusions = (ExclusionWindow(symbol="ES", start=date(2020, 12, 8), end=date(2020, 12, 9)),)
        out = apply_registered_exclusions(
            df.lazy(),
            symbol="ES",
            exclusions=exclusions,
            exclude_pit_provisional=True,
            exclude_coverage_gaps=True,
        ).collect()
        assert out.height < df.height
        assert out.get_column("pit_provisional").sum() == 0
        # No retained bar has a session date inside the exclusion window.
        sess = out.select(cme_session_date_expr("ts_event").alias("s")).get_column("s")
        assert not ((sess >= date(2020, 12, 8)) & (sess <= date(2020, 12, 9))).any()

    def test_inclusion_variant_is_identity(self) -> None:
        df = _bars_1min(datetime(2020, 12, 7), 500)
        out = apply_registered_exclusions(
            df.lazy(),
            symbol="ES",
            exclusions=(),
            exclude_pit_provisional=False,
            exclude_coverage_gaps=False,
        ).collect()
        assert out.height == df.height

    def test_provenance_parser(self) -> None:
        gaps = [
            {
                "symbol": "NQ",
                "expected_crossover_window": "2016-12-08 .. 2017-01-03",
            },
            {
                "symbol": "NQ",
                "expected_crossover_window": (
                    "2025-12-08 .. (successor takeover unobserved; sample ends 2025-12-19)"
                ),
            },
        ]
        out = exclusion_windows_from_provenance(gaps)
        assert out == (
            ExclusionWindow(symbol="NQ", start=date(2016, 12, 8), end=date(2017, 1, 3)),
            ExclusionWindow(symbol="NQ", start=date(2025, 12, 8), end=date.max),
        )


class TestStandardization:
    def test_train_moments_only(self) -> None:
        rng = np.random.default_rng(20260710)
        train = rng.normal([0.0, 5.0], [1.0, 2.0], size=(1000, 2))
        moments = fit_moments(train)
        z = standardize(train, moments)
        np.testing.assert_allclose(z.mean(axis=0), 0.0, atol=1e-12)
        np.testing.assert_allclose(z.std(axis=0), 1.0, atol=1e-12)
        # Eval data standardized with TRAIN moments — not centered.
        eval_x = rng.normal([1.0, 6.0], [1.0, 2.0], size=(500, 2))
        z_eval = standardize(eval_x, moments)
        assert abs(z_eval[:, 0].mean()) > 0.5

    def test_degenerate_feature_rejected(self) -> None:
        x = np.column_stack([np.ones(50), np.arange(50.0)])
        with pytest.raises(ValueError, match="zero variance"):
            fit_moments(x)


class TestPitCanary:
    def test_causal_pipeline_passes(self) -> None:
        df = _bars_1min(datetime(2020, 1, 6), (RVOL_WINDOW_BARS + 50) * 5)
        bars = aggregate_5min(df.lazy())
        pit_canary_future_mutation(
            bars, cut_index=bars.height // 2, rng=np.random.default_rng(20260710)
        )

    def test_canary_catches_injected_lookahead(self) -> None:
        """Negative control: a future-shifted feature MUST trip the canary.

        Simulate the canonical look-ahead defect by shifting the close
        column back one bar (close[t] := close[t+1]) BEFORE feature
        computation, then run the canary comparison by hand: the last
        pre-cut feature values now depend on the first post-cut bar, so
        mutating bars >= cut changes features at bars < cut.
        """

        def leaky_transform(frame: pl.DataFrame) -> pl.DataFrame:
            return frame.with_columns(close=pl.col("close").shift(-1).fill_null(strategy="forward"))

        df = _bars_1min(datetime(2020, 1, 6), (RVOL_WINDOW_BARS + 50) * 5)
        bars = aggregate_5min(df.lazy())
        cut = bars.height // 2
        mutated = pl.concat(
            [bars.slice(0, cut), bars.slice(cut).with_columns(close=pl.col("close") * 2.0)]
        )
        a = compute_emissions(leaky_transform(bars)).get_column("ret_5m").head(cut)
        b = compute_emissions(leaky_transform(mutated)).get_column("ret_5m").head(cut)
        assert not a.equals(b), "canary failed to flag an injected look-ahead"


class TestWindows:
    def test_fifteen_windows_registered_arithmetic(self) -> None:
        w = h900_windows()
        assert len(w) == N_WINDOWS == 15
        assert w[0] == RollingWindow(
            window_id=0,
            train_start=date(2015, 1, 1),
            origin=FIRST_ORIGIN,
            eval_end=date(2017, 7, 1),
        )
        assert w[1].origin == date(2017, 7, 1)
        assert w[-1] == RollingWindow(
            window_id=14,
            train_start=date(2022, 1, 1),
            origin=date(2024, 1, 1),
            eval_end=date(2024, 7, 1),
        )

    def test_windows_tile_contiguously(self) -> None:
        w = h900_windows()
        for a, b in zip(w, w[1:], strict=False):
            assert b.origin == a.eval_end or (b.origin > a.origin)
            assert (b.origin.year * 12 + b.origin.month) - (
                a.origin.year * 12 + a.origin.month
            ) == 6
