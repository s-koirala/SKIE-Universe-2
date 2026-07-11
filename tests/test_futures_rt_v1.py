"""Unit tests for the futures_rt_v1 cost model + break-even formula (H900 §7)."""

from __future__ import annotations

import textwrap

import numpy as np
import pytest

from skie_universe2.costs.futures_rt_v1 import (
    MU_CENTRAL,
    MU_GRID,
    FuturesRtV1CostModel,
    InstrumentCostSpec,
    break_even_dwell_bars,
)
from skie_universe2.utils.paths import ProjectPaths


@pytest.fixture(scope="module")
def model() -> FuturesRtV1CostModel:
    paths = ProjectPaths.discover()
    return FuturesRtV1CostModel.from_config(paths.config / "instruments.yaml")


def _legacy_1p0_spec(symbol: str, tick_value: float, multiplier: float) -> InstrumentCostSpec:
    """The 1.0-carried fee inputs (exchange fee $1.18/side), superseded by
    the round-1 audit LITERATURE-1-2 erratum in config/instruments.yaml.
    Kept in-test to pin the FORMULA against the design §7 bracket values,
    which were computed under these inputs (QUANT-2-2)."""
    return InstrumentCostSpec(
        symbol=symbol,
        commission_per_side_usd=0.85,
        exchange_fee_usd=1.18,
        nfa_fee_usd=0.02,
        tick_value=tick_value,
        multiplier=multiplier,
        slippage_ticks_per_side=1.0,
    )


class TestSwitchCost:
    def test_es_round_trip_matches_registered_schedule(self, model: FuturesRtV1CostModel) -> None:
        # 2 * (0.85 + 1.38 + 0.02 + 12.50) = 29.50 USD (exchange fee $1.38
        # non-member eff. 2024-02-01, LITERATURE-1-2 erratum).
        assert model.switch_cost_usd("ES") == pytest.approx(29.50, abs=1e-12)

    def test_nq_round_trip_matches_registered_schedule(self, model: FuturesRtV1CostModel) -> None:
        # 2 * (0.85 + 1.38 + 0.02 + 5.00) = 14.50 USD.
        assert model.switch_cost_usd("NQ") == pytest.approx(14.50, abs=1e-12)

    def test_quant_2_2_reference_drags_reproduced_under_legacy_inputs(self) -> None:
        """Formula fidelity vs design §7 bracket values (ES ~1.21e-4 @4800,
        NQ ~4.15e-5 @17000), which QUANT-2-2 computed under the 1.0-carried
        $1.18 exchange fee. The registered config now carries $1.38
        (LITERATURE-1-2), so the legacy inputs are pinned in-test."""
        legacy = FuturesRtV1CostModel(
            specs={
                "ES": _legacy_1p0_spec("ES", tick_value=12.50, multiplier=50.0),
                "NQ": _legacy_1p0_spec("NQ", tick_value=5.00, multiplier=20.0),
            }
        )
        assert legacy.switch_drag_notional("ES", reference_price=4800.0) == pytest.approx(
            1.21e-4, rel=0.01
        )
        assert legacy.switch_drag_notional("NQ", reference_price=17000.0) == pytest.approx(
            4.15e-5, rel=0.01
        )

    def test_registered_schedule_drags_at_reference_prices(
        self, model: FuturesRtV1CostModel
    ) -> None:
        # Current registered schedule: ES 29.50/240000, NQ 14.50/340000.
        assert model.switch_drag_notional("ES", reference_price=4800.0) == pytest.approx(
            1.2293e-4, rel=1e-3
        )
        assert model.switch_drag_notional("NQ", reference_price=17000.0) == pytest.approx(
            4.2648e-5, rel=1e-3
        )

    def test_drag_is_positive_log1p_form(self, model: FuturesRtV1CostModel) -> None:
        drag = model.switch_drag_notional("ES", reference_price=5000.0)
        cost = model.switch_cost_usd("ES")
        expected = -np.log1p(-cost / (5000.0 * 50.0))
        assert drag == pytest.approx(expected, abs=1e-15)
        assert drag > 0

    def test_account_dollar_sensitivity_basis(self, model: FuturesRtV1CostModel) -> None:
        # $10K account convention: ES 29.50/10000 -> ~2.954e-3 drag.
        drag = model.switch_drag_account_dollar("ES")
        assert drag == pytest.approx(-np.log1p(-29.50 / 10_000.0), abs=1e-15)

    def test_unregistered_symbol_fails_closed(self, model: FuturesRtV1CostModel) -> None:
        with pytest.raises(KeyError, match="no registered futures_rt_v1 fee schedule"):
            model.switch_cost_usd("MCL")  # roll_rule only; no fee block

    def test_partial_fee_block_raises_listing_missing_fields(self, tmp_path) -> None:
        """Round-1 audit CODE-1-2 regression: a misspelled fee field must
        raise (fail-closed), not silently drop the instrument."""
        bad = tmp_path / "instruments.yaml"
        bad.write_text(
            textwrap.dedent(
                """
                instruments:
                  ES:
                    commission_per_side_usd: 0.85
                    exchange_fee_us: 1.38  # <- misspelled field (regression trigger)
                    nfa_fee_usd: 0.02
                    tick_value: 12.50
                    multiplier: 50.0
                    slippage_ticks_per_side: 1
                """
            ),
            encoding="utf-8",
        )
        with pytest.raises(KeyError, match="partial futures_rt_v1 fee schedule.*exchange_fee_usd"):
            FuturesRtV1CostModel.from_config(bad)

    def test_roll_rule_only_block_is_skipped_not_raised(self, tmp_path) -> None:
        cfg = tmp_path / "instruments.yaml"
        cfg.write_text(
            textwrap.dedent(
                """
                instruments:
                  MCL:
                    exchange: NYMEX
                    description: x
                """
            ),
            encoding="utf-8",
        )
        model = FuturesRtV1CostModel.from_config(cfg)
        assert model.specs == {}

    def test_validation(self, model: FuturesRtV1CostModel) -> None:
        with pytest.raises(ValueError, match="n_contracts"):
            model.switch_cost_usd("ES", n_contracts=0)
        with pytest.raises(ValueError, match="reference_price"):
            model.switch_drag_notional("ES", reference_price=0.0)


class TestBreakEvenFormula:
    def test_registered_formula(self) -> None:
        # D_be(mu) = L_detect + c_switch / mu (design §7, verbatim).
        assert break_even_dwell_bars(
            detection_latency_bars=10.0, c_switch=1.2e-4, mu_per_bar=1.2e-4
        ) == pytest.approx(11.0)

    def test_smaller_mu_makes_gate_harder(self) -> None:
        d = [
            break_even_dwell_bars(detection_latency_bars=5.0, c_switch=1e-4, mu_per_bar=mu)
            for mu in MU_GRID
        ]
        assert d == sorted(d, reverse=True)

    def test_mu_grid_registered_values(self) -> None:
        assert MU_GRID == (1e-5, 4e-5, 1.2e-4, 2.7e-4)
        assert MU_CENTRAL == 1.2e-4

    def test_validation(self) -> None:
        with pytest.raises(ValueError, match="mu_per_bar"):
            break_even_dwell_bars(detection_latency_bars=1.0, c_switch=1.0, mu_per_bar=0.0)
        with pytest.raises(ValueError, match=">= 0"):
            break_even_dwell_bars(detection_latency_bars=-1.0, c_switch=1.0, mu_per_bar=1.0)
