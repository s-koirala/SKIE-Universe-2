"""Unit tests for the Tier-0 bar-close execution helper (ADR-0006 D1)."""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.execution.tier0_barclose import tier0_counterfactual


class TestTier0Counterfactual:
    def test_pit_alignment_uses_prior_position(self) -> None:
        # position decided at t earns the return over (t, t+1].
        pos = np.array([1.0, 1.0, 0.0, -1.0])
        r = np.array([np.nan, 0.02, -0.01, 0.03])  # r[t] over (t-1, t]
        out = tier0_counterfactual(pos, r, per_unit_turnover_cost=0.0)
        # ret_gross[t] = pos[t-1] * r[t]
        assert out.ret_gross[0] == 0.0
        assert out.ret_gross[1] == pytest.approx(1.0 * 0.02)  # pos[0]*r[1]
        assert out.ret_gross[2] == pytest.approx(1.0 * -0.01)  # pos[1]*r[2]
        assert out.ret_gross[3] == pytest.approx(0.0 * 0.03)  # pos[2]=0

    def test_no_cost_gross_equals_net(self) -> None:
        pos = np.array([1.0, -1.0, 1.0])
        r = np.array([np.nan, 0.01, 0.02])
        out = tier0_counterfactual(pos, r, per_unit_turnover_cost=0.0)
        np.testing.assert_array_equal(out.ret_gross, out.ret_net)

    def test_turnover_and_round_trip_cost(self) -> None:
        # flat -> long(t0) -> flat(t1): entry turnover 1 at decision 0, exit
        # turnover 1 at decision 1; each charged on the following accrual bar.
        pos = np.array([1.0, 0.0, 0.0])
        r = np.array([np.nan, 0.0, 0.0])
        c = 0.001
        out = tier0_counterfactual(pos, r, per_unit_turnover_cost=c, start_position=0.0)
        # accrual bar 1: turnover |pos[0]-start| = 1 -> cost c
        assert out.turnover[1] == pytest.approx(1.0)
        assert out.ret_net[1] == pytest.approx(-c)
        # accrual bar 2: turnover |pos[1]-pos[0]| = |0-1| = 1 -> cost c
        assert out.turnover[2] == pytest.approx(1.0)
        assert out.ret_net[2] == pytest.approx(-c)
        # total round-trip cost = 2c
        assert out.ret_net.sum() == pytest.approx(-2 * c)

    def test_start_position_entry_turnover(self) -> None:
        pos = np.array([1.0, 1.0, 1.0])
        r = np.array([np.nan, 0.0, 0.0])
        # already long before bar 0 => no entry turnover on accrual bar 1
        out = tier0_counterfactual(pos, r, per_unit_turnover_cost=0.01, start_position=1.0)
        assert out.turnover[1] == pytest.approx(0.0)
        assert out.turnover[2] == pytest.approx(0.0)

    def test_flat_position_zero_return(self) -> None:
        pos = np.zeros(5)
        r = np.array([np.nan, 0.01, -0.02, 0.03, 0.01])
        out = tier0_counterfactual(pos, r, per_unit_turnover_cost=0.01)
        np.testing.assert_array_equal(out.ret_gross, np.zeros(5))
        np.testing.assert_array_equal(out.ret_net, np.zeros(5))

    def test_negative_cost_raises(self) -> None:
        with pytest.raises(ValueError, match="per_unit_turnover_cost must be >= 0"):
            tier0_counterfactual(
                np.array([1.0, 1.0]), np.array([np.nan, 0.0]), per_unit_turnover_cost=-0.001
            )

    def test_shape_mismatch_raises(self) -> None:
        with pytest.raises(ValueError, match="shape mismatch"):
            tier0_counterfactual(np.array([1.0, 1.0]), np.array([0.0]), per_unit_turnover_cost=0.0)

    def test_short_position_return_sign_exact(self) -> None:
        # Exact levered log return for a short: log1p(-1 * expm1(r)), NOT -r.
        pos = np.array([-1.0, -1.0])
        r = np.array([np.nan, 0.02])  # market up 2%
        out = tier0_counterfactual(pos, r, per_unit_turnover_cost=0.0)
        assert out.ret_gross[1] == pytest.approx(np.log1p(-1.0 * np.expm1(0.02)))
        assert out.ret_gross[1] < 0.0  # short loses when market rises

    def test_unit_long_is_exact_r(self) -> None:
        # For pos = 1 the levered return equals r exactly.
        out = tier0_counterfactual(
            np.array([1.0, 1.0]), np.array([np.nan, 0.017]), per_unit_turnover_cost=0.0
        )
        assert out.ret_gross[1] == pytest.approx(0.017)

    def test_leverage_exact_not_linear(self) -> None:
        # pos=1.25, r=-0.8: exact log1p(1.25*expm1(-0.8)) != linear 1.25*-0.8.
        out = tier0_counterfactual(
            np.array([1.25, 1.25]), np.array([np.nan, -0.8]), per_unit_turnover_cost=0.0
        )
        assert out.ret_gross[1] == pytest.approx(np.log1p(1.25 * np.expm1(-0.8)))
        assert out.ret_gross[1] != pytest.approx(1.25 * -0.8)  # not the linear form

    def test_ruin_is_neg_inf(self) -> None:
        # pos=2.0, r=-0.8: 1 + 2*(exp(-0.8)-1) = -0.101 < 0 -> wipeout -> -inf.
        out = tier0_counterfactual(
            np.array([2.0, 2.0]), np.array([np.nan, -0.8]), per_unit_turnover_cost=0.0
        )
        assert np.isneginf(out.ret_gross[1])
