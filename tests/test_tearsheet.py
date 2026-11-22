"""Unit tests for the canonical tearsheet analytics (pure, no IO)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from skie_universe2.reporting import tearsheet as ts


def test_equity_and_drawdown_known_path():
    r = np.log(np.array([1.10, 0.90, 1.05]))  # +10%, -10%, +5% simple
    eq = ts.equity(r)
    np.testing.assert_allclose(eq, [1.10, 0.99, 1.0395], rtol=1e-9)
    dd = ts.drawdown(eq)
    # peak after bar0 is 1.10; trough 0.99 -> -10%; recovers but stays below peak
    assert dd[0] == pytest.approx(0.0, abs=1e-12)
    assert dd[1] == pytest.approx(0.99 / 1.10 - 1.0, rel=1e-9)
    assert dd.min() == pytest.approx(0.99 / 1.10 - 1.0, rel=1e-9)


def test_drawdown_captures_first_session_loss():
    r = np.array([-0.10, 0.05])
    dd = ts.drawdown(ts.equity(r))
    assert dd[0] == pytest.approx(math.exp(-0.10) - 1.0, rel=1e-9)  # loss vs 1.0 inception
    m = ts.metrics(r, np.ones(2), ["2020-01-01", "2020-12-31"])
    assert m["max_drawdown_pct"] == pytest.approx((math.exp(-0.10) - 1.0) * 100, rel=1e-9)


def test_metrics_small_case():
    r = np.array([0.01, -0.02, 0.03])
    dates = ["2020-01-01", "2020-07-01", "2020-12-31"]
    m = ts.metrics(r, np.array([5.0, 6.0, 7.0]), dates)
    assert m["n_sessions"] == 3
    assert m["total_return_pct"] == pytest.approx((math.exp(0.02) - 1) * 100, rel=1e-9)
    assert m["win_rate_pct"] == pytest.approx(200 / 3, rel=1e-9)
    assert m["profit_factor"] == pytest.approx(
        2.045556, rel=1e-5
    )  # simple-return gross profit / loss
    assert m["avg_win_bps"] == pytest.approx(200.0, rel=1e-9)  # mean(1%,3%)=2%
    assert m["avg_loss_bps"] == pytest.approx(-200.0, rel=1e-9)
    assert m["max_drawdown_pct"] == pytest.approx(
        (math.exp(-0.01) / math.exp(0.01) - 1) * 100, rel=1e-6
    )
    assert m["sharpe_ann"] > 0 and m["sortino_ann"] > 0
    assert m["avg_turnover"] == pytest.approx(6.0, rel=1e-9)


def test_metrics_guards_on_degenerate_series():
    r = np.array([0.001, 0.001, 0.001, 0.001])  # all positive, zero vol band
    dates = ["2021-01-01", "2021-04-01", "2021-07-01", "2021-10-01"]
    m = ts.metrics(r, np.zeros(4), dates)
    assert m["win_rate_pct"] == 100.0
    assert math.isinf(m["profit_factor"])  # no losses
    assert m["max_drawdown_pct"] == pytest.approx(0.0, abs=1e-9)  # monotone increasing
    assert math.isinf(m["sortino_ann"])  # zero downside, mean>0 -> +inf
    assert m["avg_loss_bps"] == 0.0


def test_mc_cone_is_seed_deterministic_and_bounded():
    r = np.random.default_rng(0).normal(0, 0.01, 300)
    a = ts.mc_cone(r, np.random.default_rng(42), n_mc=2000, cone_points=50)
    b = ts.mc_cone(r, np.random.default_rng(42), n_mc=2000, cone_points=50)
    assert a["p50"] == b["p50"]  # same seed -> identical
    assert len(a["t_index"]) <= 50
    # cone ordering p05 <= p50 <= p95 at the terminal point
    assert a["p05"][-1] <= a["p50"][-1] <= a["p95"][-1]
    assert 0.0 <= a["terminal"]["prob_loss_pct"] <= 100.0


def test_monthly_groups_and_compounds():
    r = np.array([0.01, 0.02, -0.01])
    dates = ["2022-01-10", "2022-01-20", "2022-02-05"]
    rows = ts.monthly(r, dates)
    assert len(rows) == 1 and rows[0]["year"] == 2022
    jan = rows[0]["months"][0]
    assert jan == pytest.approx((math.exp(0.03) - 1) * 100, rel=1e-9)  # 0.01+0.02 compounded
    assert rows[0]["months"][1] == pytest.approx((math.exp(-0.01) - 1) * 100, rel=1e-9)
    assert rows[0]["months"][2] is None  # no March


def test_downsample_keeps_endpoints():
    a = np.arange(1000.0)
    d = ts.downsample(a, n=100)
    assert d.size <= 100 and d[0] == 0.0 and d[-1] == 999.0
    assert ts.downsample(np.arange(10.0), n=100).size == 10  # no upsampling


def _series(key, vals, **kw):
    return ts.SeriesSpec(key, key, np.asarray(vals, float), **kw)


def _inputs(sym, keys_primary):
    dates = ["2020-01-01", "2020-06-01", "2020-12-31"]
    series = [_series("gross", [0.01, 0.0, -0.01])]
    for k, prim in keys_primary:
        series.append(_series(k, [0.005, 0.0, -0.005], is_primary_net=prim))
    return ts.InstrumentInputs(sym, dates, series, np.array([1.0, 1.0, 1.0]))


def test_build_report_happy_path_and_schema():
    rep = ts.build_report(
        hid="HX",
        title="t",
        subtitle="s",
        cost_note="c",
        instruments=[_inputs("ES", [("net", True)]), _inputs("NQ", [("net", True)])],
        generated="2026-11-22",
        n_mc=500,
    )
    assert rep["instrument_order"] == ["ES", "NQ"]
    assert rep["primary_net_key"] == "net" and rep["gross_key"] == "gross"
    assert rep["mc_cone_key"] == "net"
    assert set(rep["instruments"]) == {"ES", "NQ"}
    assert "net" in rep["instruments"]["ES"]["mc"]  # mc computed for primary net
    assert rep["has_verdict"] is False


def test_build_report_rejects_series_mismatch_and_bad_primary():
    with pytest.raises(ValueError):
        ts.build_report(
            hid="H",
            title="t",
            subtitle="s",
            cost_note="c",
            instruments=[_inputs("ES", [("net", True)]), _inputs("NQ", [("other", True)])],
            generated="2026-11-22",
        )
    with pytest.raises(ValueError):  # zero primaries
        ts.build_report(
            hid="H",
            title="t",
            subtitle="s",
            cost_note="c",
            instruments=[_inputs("ES", [("net", False)])],
            generated="2026-11-22",
        )
    with pytest.raises(ValueError):  # two primaries
        ts.build_report(
            hid="H",
            title="t",
            subtitle="s",
            cost_note="c",
            instruments=[_inputs("ES", [("net", True), ("net2", True)])],
            generated="2026-11-22",
        )


def test_round_floats_drops_nonfinite_keeps_bool():
    out = ts.round_floats(
        {"a": float("inf"), "b": float("nan"), "c": 1.23456789, "d": True, "e": [1.0, 2.5]}
    )
    assert out["a"] is None and out["b"] is None
    assert out["c"] == pytest.approx(1.23457, rel=1e-4)
    assert out["d"] is True
    assert out["e"] == [1.0, 2.5]
