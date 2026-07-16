"""Unit tests for the CSCV Probability-of-Backtest-Overfitting estimator.

Grounds in [Bailey, Borwein, López de Prado & Zhu 2016, J. Comput. Finance
20(4):39-69](https://doi.org/10.21314/JCF.2016.322). All randomness is seeded via
``np.random.default_rng``; no unseeded RNG.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from skie_universe2.inference.pbo import (
    PBOResult,
    probability_of_backtest_overfitting,
)


def _noise_matrix(t_obs: int, n_configs: int, seed: int) -> np.ndarray:
    """T×N matrix of i.i.d. standard-normal per-period returns."""
    rng = np.random.default_rng(seed)
    return rng.standard_normal((t_obs, n_configs))


class TestStructure:
    def test_result_shapes_and_counts(self) -> None:
        m = _noise_matrix(320, 12, seed=0)
        res = probability_of_backtest_overfitting(m, s_splits=8)
        assert isinstance(res, PBOResult)
        assert res.s_splits == 8
        assert res.n_combinations == math.comb(8, 4)
        assert res.logits.shape == (res.n_combinations,)
        assert res.relative_ranks.shape == (res.n_combinations,)
        assert res.selected_configs.shape == (res.n_combinations,)
        assert 0.0 <= res.pbo <= 1.0

    def test_relative_ranks_strictly_interior(self) -> None:
        # ω_c ∈ (0,1) strictly ⇒ every logit is finite (no clipping needed).
        m = _noise_matrix(200, 6, seed=1)
        res = probability_of_backtest_overfitting(m, s_splits=8)
        assert np.all(res.relative_ranks > 0.0)
        assert np.all(res.relative_ranks < 1.0)
        assert np.all(np.isfinite(res.logits))

    def test_pbo_matches_logit_sign_fraction(self) -> None:
        m = _noise_matrix(300, 8, seed=2)
        res = probability_of_backtest_overfitting(m, s_splits=10)
        assert res.pbo == pytest.approx(np.mean(res.logits < 0.0))

    def test_logit_is_omega_logit(self) -> None:
        m = _noise_matrix(240, 5, seed=3)
        res = probability_of_backtest_overfitting(m, s_splits=8)
        expected = np.log(res.relative_ranks / (1.0 - res.relative_ranks))
        np.testing.assert_allclose(res.logits, expected)


class TestNoiseIsHalf:
    # (a) Under the null (N independent skill-less configs) the IS-best is a
    # random draw OOS, so E[PBO] = 0.5 (Bailey et al. 2016 §4). A SINGLE
    # performance matrix estimates this with large variance (SD ≈ 0.2 at these
    # sizes), so the null property is asserted on the MEAN over seeded draws —
    # the estimand is the expectation, not any single realisation.
    def test_independent_noise_pbo_near_half(self) -> None:
        pbos = np.array(
            [
                probability_of_backtest_overfitting(
                    _noise_matrix(800, 20, seed=1000 + k), s_splits=10
                ).pbo
                for k in range(60)
            ]
        )
        assert pbos.mean() == pytest.approx(0.5, abs=0.05)

    def test_noise_pooled_logits_symmetric(self) -> None:
        # Pooled over draws, the logit distribution is centred at 0 (symmetric
        # IS/OOS exchange under the null).
        pooled = np.concatenate(
            [
                probability_of_backtest_overfitting(
                    _noise_matrix(800, 16, seed=2000 + k), s_splits=10
                ).logits
                for k in range(40)
            ]
        )
        assert pooled.mean() == pytest.approx(0.0, abs=0.1)


class TestGenuineEdgeIsLow:
    def test_persistent_edge_pbo_low(self) -> None:
        # (b) one config with a genuine drift edge above pure-noise peers: the
        # IS-best (the edge config) stays OOS-best ⇒ PBO ≈ 0.
        rng = np.random.default_rng(20)
        t_obs, n_configs = 1600, 20
        m = rng.standard_normal((t_obs, n_configs))
        # A persistent Sharpe edge realised in every period (drift ≫ 0), so the
        # config dominates on any IS or OOS block — not IS-overfit.
        m[:, 0] += 1.5
        res = probability_of_backtest_overfitting(m, s_splits=14)
        assert res.pbo < 0.05
        # the edge config is the selected IS-best in (nearly) every combination
        assert np.mean(res.selected_configs == 0) > 0.95

    def test_edge_survives_on_mean_metric(self) -> None:
        rng = np.random.default_rng(21)
        m = rng.standard_normal((1200, 15))
        m[:, 3] += 1.0
        res = probability_of_backtest_overfitting(m, s_splits=12, metric="mean")
        assert res.pbo < 0.1


class TestOverfitIsHigh:
    # (c) A configuration set built so that whatever wins IS is a systematic OOS
    # loser drives PBO → 1. Diagonal-peak design: with N = S configs, config j
    # carries a large positive mean spike confined to block j and is pure noise
    # elsewhere. For any IS = S/2 blocks, the IS-best is a config whose peak
    # block lies IN the IS set (spike dominates); its peak block is therefore
    # EXCLUDED from OOS, so its OOS score is baseline noise while the S/2 configs
    # peaking in the OOS blocks score high — the IS-winner lands in the bottom
    # half OOS ⇒ λ < 0 for (nearly) every combination.
    def _diagonal_peak(self, t_obs: int, s_splits: int, spike: float, seed: int) -> np.ndarray:
        rng = np.random.default_rng(seed)
        m = rng.standard_normal((t_obs, s_splits))  # N = S configs
        block_len = t_obs // s_splits
        for j in range(s_splits):
            m[j * block_len : (j + 1) * block_len, j] += spike
        return m

    def test_overfit_config_pbo_high(self) -> None:
        m = self._diagonal_peak(t_obs=1600, s_splits=16, spike=10.0, seed=30)
        res = probability_of_backtest_overfitting(m, s_splits=16, metric="mean")
        assert res.pbo > 0.9

    def test_overfit_high_on_sharpe_metric(self) -> None:
        # The IS-inflation / OOS-collapse holds under the Sharpe ranking too.
        m = self._diagonal_peak(t_obs=1200, s_splits=12, spike=8.0, seed=31)
        res = probability_of_backtest_overfitting(m, s_splits=12, metric="sharpe")
        assert res.pbo > 0.9


class TestValidation:
    def test_rejects_non_2d(self) -> None:
        with pytest.raises(ValueError, match="2-D"):
            probability_of_backtest_overfitting(np.zeros(10), s_splits=4)

    def test_rejects_single_config(self) -> None:
        with pytest.raises(ValueError, match=">= 2 config"):
            probability_of_backtest_overfitting(np.zeros((100, 1)), s_splits=4)

    def test_rejects_odd_splits(self) -> None:
        with pytest.raises(ValueError, match="even"):
            probability_of_backtest_overfitting(_noise_matrix(100, 5, 0), s_splits=7)

    def test_rejects_splits_below_two(self) -> None:
        with pytest.raises(ValueError, match="even and >= 2"):
            probability_of_backtest_overfitting(_noise_matrix(100, 5, 0), s_splits=0)

    def test_rejects_tiny_blocks(self) -> None:
        # T=10, S=8 ⇒ block_len=1 < 2 (Sharpe ddof=1 undefined).
        with pytest.raises(ValueError, match="block_len"):
            probability_of_backtest_overfitting(_noise_matrix(10, 5, 0), s_splits=8)

    def test_rejects_unknown_metric(self) -> None:
        with pytest.raises(ValueError, match="metric must be"):
            probability_of_backtest_overfitting(_noise_matrix(200, 5, 0), metric="sortino")

    def test_combination_cap_enforced(self) -> None:
        m = _noise_matrix(600, 5, 0)
        with pytest.raises(ValueError, match="exceeds max_combinations"):
            probability_of_backtest_overfitting(m, s_splits=16, max_combinations=100)

    def test_cap_can_be_raised(self) -> None:
        m = _noise_matrix(600, 5, 0)
        res = probability_of_backtest_overfitting(m, s_splits=16, max_combinations=math.comb(16, 8))
        assert res.n_combinations == math.comb(16, 8)


class TestScoreFnOverride:
    def test_custom_score_fn_used(self) -> None:
        m = _noise_matrix(320, 6, seed=40)
        # negated-Sharpe scorer flips which config is "best" — result still valid.
        res = probability_of_backtest_overfitting(
            m, s_splits=8, score_fn=lambda sub: -sub.mean(axis=0) / sub.std(axis=0, ddof=1)
        )
        assert 0.0 <= res.pbo <= 1.0
        assert np.all(np.isfinite(res.logits))


class TestDeterminism:
    def test_estimator_is_deterministic(self) -> None:
        m = _noise_matrix(400, 8, seed=50)
        a = probability_of_backtest_overfitting(m, s_splits=10)
        b = probability_of_backtest_overfitting(m, s_splits=10)
        assert a.pbo == b.pbo
        np.testing.assert_array_equal(a.logits, b.logits)
        np.testing.assert_array_equal(a.selected_configs, b.selected_configs)
