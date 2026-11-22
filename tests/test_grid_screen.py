"""Synthetic-data tests for the H107 parameter-grid screen (grid_screen.py)."""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pytest

from skie_universe2.screening.grid_screen import (
    CostVariant,
    GridPanel,
    per_unit_drag,
    run_grid_screen,
)

_LABELS = ("ema3", "ema9", "ema21")


def _panel(mu: tuple[float, ...], t: int = 1500, seed: int = 0) -> GridPanel:
    rng = np.random.default_rng(seed)
    common = rng.normal(0, 0.01, t)
    g = np.column_stack([m + common + rng.normal(0, 0.004, t) for m in mu])
    dates = [date(2016, 1, 4) + timedelta(days=i) for i in range(t)]
    return GridPanel(
        instrument="ES",
        dates=dates,
        labels=_LABELS,
        gross=g,
        turnover=np.full(g.shape, 4.0),
        canary={"pass": True},
        cost_variants=(CostVariant("ES/lifetime", 1e-4), CostVariant("MES/lifetime", 3e-4)),
    )


def _run(panel: GridPanel, **kw) -> dict:
    return run_grid_screen(
        [panel],
        level=0.05,
        seed=1,
        n_trials_gate=kw.get("n_trials", 3),
        register_sharpes=[0.01, -0.02, 0.03],
        primary_label="ema9",
        dwell_bars_per_session=264.0,
        n_bootstrap=200,
    )


def test_null_grid_has_no_pass() -> None:
    res = _run(_panel((0.0, 0.0, 0.0)))
    assert not any(c["screen_pass"] for c in res["instruments"][0]["cells"])
    assert "archive" in res["disposition"]


def test_strong_edge_passes_sc() -> None:
    res = _run(_panel((0.0, 0.004, 0.0)))
    cells = {c["cell"]: c for c in res["instruments"][0]["cells"]}
    assert cells["ema9"]["s_c_pass"]
    assert cells["ema9"]["rw_adj_pvalue"] < 0.05
    assert not cells["ema3"]["s_c_pass"]


def test_net_descriptive_is_gross_minus_turnover_drag() -> None:
    p = _panel((0.001, 0.001, 0.001))
    c = _run(p)["instruments"][0]["cells"][1]
    assert c["net_descriptive"]["ES/lifetime"] == pytest.approx(c["mean_gross"] - 4.0 * 1e-4)
    assert c["net_descriptive"]["MES/lifetime"] == pytest.approx(c["mean_gross"] - 4.0 * 3e-4)
    assert c["mean_turnover_per_session"] == pytest.approx(4.0)


def test_spine_shaped_fields_present() -> None:
    inst = _run(_panel((0.0, 0.001, 0.0)))["instruments"][0]
    for c in inst["cells"]:
        for key in ("cell", "n", "mean_gross", "sharpe", "rw_adj_pvalue", "s_c_pass", "s_d"):
            assert key in c
        assert {"dsr", "pbo", "pass", "per_window_growth"} <= set(c["s_d"])
    assert 0.0 <= inst["pbo"]["pbo"] <= 1.0


def test_non_finite_panel_rejected() -> None:
    p = _panel((0.0, 0.0, 0.0))
    g = p.gross.copy()
    g[3, 1] = np.nan
    bad = GridPanel("ES", p.dates, p.labels, g, p.turnover, {"pass": True})
    with pytest.raises(ValueError):
        _run(bad)


def test_per_unit_drag_micro_vs_emini() -> None:
    # same price, MES multiplier 5 vs ES 50: micro drag per $-fee is 10x larger
    es = per_unit_drag(2.17, reference_price=5000.0, multiplier=50.0)
    mes = per_unit_drag(0.64, reference_price=5000.0, multiplier=5.0)
    assert mes / es == pytest.approx((0.64 / 25000) / (2.17 / 250000), rel=1e-4)
