"""Unit tests for the Deflated Sharpe Ratio estimator (Bailey & LdP 2014; Lo 2002).

Analytic / known-case checks:

- N=1 with normal returns reduces to the standard (undeflated) Sharpe p-value.
- Increasing N lowers the DSR (the deflated benchmark rises).
- Negative skew / excess kurtosis widens the SE and lowers the DSR.
- A clearly-strong Sharpe at N=1 gives DSR ~ 1.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from skie_universe2.inference.deflated_sharpe import (
    DeflatedSharpe,
    deflated_sharpe_ratio,
    expected_max_sharpe,
    sharpe_moments,
    sharpe_standard_error,
)


class TestSharpeStandardError:
    def test_normal_case_reduces_to_classic_formula(self) -> None:
        # gamma3 = 0, gamma4 = 3  ->  sqrt((1 + SR^2/2)/(n-1))
        sr, n = 0.4, 101
        se = sharpe_standard_error(sr, n)
        expected = np.sqrt((1.0 + sr * sr / 2.0) / (n - 1))
        assert se == pytest.approx(expected)

    def test_negative_skew_widens_se(self) -> None:
        sr, n = 0.5, 250
        se_symmetric = sharpe_standard_error(sr, n, skew=0.0)
        se_neg_skew = sharpe_standard_error(sr, n, skew=-1.5)
        assert se_neg_skew > se_symmetric

    def test_excess_kurtosis_widens_se(self) -> None:
        sr, n = 0.5, 250
        se_gaussian = sharpe_standard_error(sr, n, kurtosis=3.0)
        se_fat = sharpe_standard_error(sr, n, kurtosis=9.0)
        assert se_fat > se_gaussian

    def test_se_shrinks_with_sample_size(self) -> None:
        assert sharpe_standard_error(0.3, 1001) < sharpe_standard_error(0.3, 101)

    def test_raises_on_too_few_obs(self) -> None:
        with pytest.raises(ValueError, match="n_obs must be >= 2"):
            sharpe_standard_error(0.3, 1)

    def test_raises_on_inadmissible_variance_term(self) -> None:
        # Large positive skew * large SR drives (1 - skew*SR + ...) negative.
        with pytest.raises(ValueError, match="non-positive"):
            sharpe_standard_error(5.0, 100, skew=3.0, kurtosis=1.0)


class TestExpectedMaxSharpe:
    def test_single_trial_is_zero_benchmark(self) -> None:
        assert expected_max_sharpe(1, sr_std=0.7) == 0.0

    def test_benchmark_increases_with_n_trials(self) -> None:
        sr_std = 0.5
        vals = [expected_max_sharpe(n, sr_std) for n in (2, 5, 20, 100, 1000)]
        assert all(np.diff(vals) > 0)

    def test_benchmark_scales_linearly_with_sigma(self) -> None:
        b1 = expected_max_sharpe(50, sr_std=1.0)
        b2 = expected_max_sharpe(50, sr_std=2.0)
        assert b2 == pytest.approx(2.0 * b1)

    def test_matches_false_strategy_theorem_closed_form(self) -> None:
        n_trials, sr_std = 100, 0.6
        gamma = float(np.euler_gamma)
        z1 = norm.ppf(1.0 - 1.0 / n_trials)
        z2 = norm.ppf(1.0 - 1.0 / (n_trials * np.e))
        expected = sr_std * ((1.0 - gamma) * z1 + gamma * z2)
        assert expected_max_sharpe(n_trials, sr_std) == pytest.approx(expected)

    def test_raises_on_zero_trials(self) -> None:
        with pytest.raises(ValueError, match="n_trials must be >= 1"):
            expected_max_sharpe(0, sr_std=0.5)

    def test_raises_on_negative_sigma(self) -> None:
        with pytest.raises(ValueError, match="sr_std must be >= 0"):
            expected_max_sharpe(10, sr_std=-0.1)


class TestDeflatedSharpeRatio:
    def test_single_trial_reduces_to_standard_sharpe_pvalue(self) -> None:
        # N=1, normal returns -> benchmark 0, DSR = Phi(SR / SE), the classic
        # one-sided Sharpe p-value that true Sharpe > 0.
        sr, n = 0.35, 260
        res = deflated_sharpe_ratio(sr, n_obs=n, n_trials=1, sr_std=0.4)
        se = np.sqrt((1.0 + sr * sr / 2.0) / (n - 1))
        expected = float(norm.cdf(sr / se))
        assert res.sr_benchmark == 0.0
        assert res.dsr == pytest.approx(expected)

    def test_returns_frozen_dataclass_with_expected_fields(self) -> None:
        res = deflated_sharpe_ratio(0.3, n_obs=200, n_trials=10, sr_std=0.5)
        assert isinstance(res, DeflatedSharpe)
        with pytest.raises(AttributeError):
            res.dsr = 0.0  # type: ignore[misc]
        assert res.n_trials == 10
        assert 0.0 <= res.dsr <= 1.0

    def test_increasing_n_trials_lowers_dsr(self) -> None:
        # Fixed observed edge; more trials -> higher benchmark -> lower DSR.
        common = dict(sr_observed=0.30, n_obs=500, sr_std=0.25)
        dsrs = [deflated_sharpe_ratio(n_trials=n, **common).dsr for n in (1, 10, 100, 1000, 10000)]
        assert all(np.diff(dsrs) < 0)

    def test_negative_skew_lowers_dsr(self) -> None:
        # Observed edge clears the benchmark (DSR > 0.5), so a wider SE lowers it.
        common = dict(sr_observed=0.30, n_obs=500, n_trials=10, sr_std=0.10)
        dsr_symmetric = deflated_sharpe_ratio(skew=0.0, **common)
        dsr_neg_skew = deflated_sharpe_ratio(skew=-1.5, **common)
        assert dsr_symmetric.dsr > 0.5
        assert dsr_neg_skew.se_sr > dsr_symmetric.se_sr
        assert dsr_neg_skew.dsr < dsr_symmetric.dsr

    def test_excess_kurtosis_lowers_dsr(self) -> None:
        common = dict(sr_observed=0.30, n_obs=500, n_trials=10, sr_std=0.10)
        dsr_gaussian = deflated_sharpe_ratio(kurtosis=3.0, **common)
        dsr_fat = deflated_sharpe_ratio(kurtosis=12.0, **common)
        assert dsr_gaussian.dsr > 0.5
        assert dsr_fat.se_sr > dsr_gaussian.se_sr
        assert dsr_fat.dsr < dsr_gaussian.dsr

    def test_strong_sharpe_single_trial_dsr_near_one(self) -> None:
        # A large per-observation Sharpe over a long sample, no selection bias.
        res = deflated_sharpe_ratio(0.5, n_obs=2000, n_trials=1, sr_std=0.3)
        assert res.dsr > 0.999

    def test_benchmark_exceeding_observed_gives_dsr_below_half(self) -> None:
        # Weak observed edge deflated by a huge trial family -> below the coin flip.
        res = deflated_sharpe_ratio(0.05, n_obs=500, n_trials=100000, sr_std=0.4)
        assert res.dsr < 0.5

    def test_dsr_bounded_unit_interval(self) -> None:
        for sr in (-0.5, 0.0, 0.2, 1.0):
            res = deflated_sharpe_ratio(sr, n_obs=300, n_trials=25, sr_std=0.3)
            assert 0.0 <= res.dsr <= 1.0


class TestSharpeMoments:
    def test_recovers_sharpe_and_gaussian_moments(self) -> None:
        rng = np.random.default_rng(12345)
        r = rng.normal(0.001, 0.01, size=20000)
        sr, n, skew, kurt = sharpe_moments(r)
        assert n == 20000
        assert sr == pytest.approx(r.mean() / r.std(ddof=1))
        assert skew == pytest.approx(0.0, abs=0.1)
        assert kurt == pytest.approx(3.0, abs=0.15)

    def test_drops_nonfinite(self) -> None:
        r = np.array([0.01, np.nan, -0.02, np.inf, 0.005])
        _, n, _, _ = sharpe_moments(r)
        assert n == 3

    def test_raises_on_zero_dispersion(self) -> None:
        with pytest.raises(ValueError, match="zero dispersion"):
            sharpe_moments(np.full(50, 0.01))

    def test_raises_on_too_few_points(self) -> None:
        with pytest.raises(ValueError, match="need >= 2"):
            sharpe_moments(np.array([0.01]))

    def test_feeds_deflated_sharpe_ratio(self) -> None:
        rng = np.random.default_rng(7)
        r = rng.normal(0.0008, 0.01, size=5000)
        sr, n, skew, kurt = sharpe_moments(r)
        res = deflated_sharpe_ratio(
            sr, n_obs=int(n), n_trials=20, sr_std=0.2, skew=skew, kurtosis=kurt
        )
        assert 0.0 <= res.dsr <= 1.0
