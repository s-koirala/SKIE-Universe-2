"""Unit tests for the H001 covariate-information estimators (design §4/§5/§8)."""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.inference.covariate_information import (
    cmi_pointwise_contributions,
    conditional_mutual_information,
    forward_variance_ratio,
    nested_predictive_delta,
    partition_redundancy,
    stationary_bootstrap_mean_ci,
    stratified_permutation_pvalue,
    vr_sign_label,
)


class TestForwardVarianceRatio:
    def test_alignment_and_tail_nan(self) -> None:
        r = np.array([0.0, 1.0, -1.0, 1.0, -1.0, 1.0])
        vr = forward_variance_ratio(r, 2)
        # last h=2 bars have no full forward window
        assert np.isnan(vr[-1]) and np.isnan(vr[-2])
        assert np.isfinite(vr[0])

    def test_perfect_reversion_below_one(self) -> None:
        # alternating returns => cumulative ~0, sum of squares > 0 => VR ~ 0 (<1)
        r = np.array([0.0, 1.0, -1.0, 1.0, -1.0, 1.0, -1.0])
        vr = forward_variance_ratio(r, 2)
        assert vr[1] == pytest.approx(0.0, abs=1e-9)  # (1-1)^2 / (1+1) = 0

    def test_perfect_trend_equals_h(self) -> None:
        # identical forward returns => (h*a)^2 / (h*a^2) = h  (upper bound)
        r = np.array([0.0, 0.5, 0.5, 0.5, 0.5])
        vr = forward_variance_ratio(r, 3)
        assert vr[0] == pytest.approx(3.0)  # (1.5)^2 / (3*0.25) = 2.25/0.75 = 3

    def test_degenerate_window_is_nan(self) -> None:
        r = np.array([0.1, 0.0, 0.0, 0.0, 0.2])
        vr = forward_variance_ratio(r, 3)
        assert np.isnan(vr[0])  # forward returns all zero => 0/0

    def test_nan_return_propagates(self) -> None:
        r = np.array([0.1, np.nan, 0.2, 0.3, 0.4])
        vr = forward_variance_ratio(r, 2)
        assert np.isnan(vr[0])  # window includes the NaN

    def test_bounded_in_zero_h(self) -> None:
        rng = np.random.default_rng(0)
        r = rng.normal(0, 1, size=500)
        vr = forward_variance_ratio(r, 6)
        finite = vr[np.isfinite(vr)]
        assert np.all(finite >= 0.0) and np.all(finite <= 6.0 + 1e-9)


class TestVrSignLabel:
    def test_labels(self) -> None:
        vr = np.array([0.5, 1.5, np.nan, 1.0])
        lab = vr_sign_label(vr)
        assert lab[0] == 0  # reversion
        assert lab[1] == 1  # continuation
        assert lab[2] == -1  # invalid
        assert lab[3] == 0  # exactly 1 => not > 1


class TestConditionalMutualInformation:
    def test_conditional_independence_near_zero(self) -> None:
        # Y and X both depend on Z but are independent GIVEN Z => I(Y;X|Z) ~ 0,
        # while the UNCONDITIONAL MI (Z collapsed) is clearly positive.
        rng = np.random.default_rng(1)
        n = 20000
        z = rng.integers(0, 2, size=n)
        y = np.where(rng.random(n) < np.where(z == 1, 0.8, 0.2), 1, 0)
        x = np.where(rng.random(n) < np.where(z == 1, 0.8, 0.2), 1, 0)
        cmi = conditional_mutual_information(y, x, z)
        uncond = conditional_mutual_information(y, x, np.zeros(n, dtype=np.int64))
        assert abs(cmi) < 0.01  # conditionally independent
        assert uncond > 0.05  # marginally dependent (spurious via Z)

    def test_conditional_dependence_positive(self) -> None:
        # X carries info about Y beyond Z => I(Y;X|Z) > 0.
        rng = np.random.default_rng(2)
        n = 20000
        z = rng.integers(0, 2, size=n)
        x = rng.integers(0, 2, size=n)
        # Y depends on x XOR z (needs x even after conditioning on z)
        flip = rng.random(n) < 0.1
        y = (x ^ z) ^ flip.astype(np.int64)
        cmi = conditional_mutual_information(y, x, z)
        assert cmi > 0.1

    def test_pointwise_mean_is_plugin_cmi(self) -> None:
        rng = np.random.default_rng(3)
        n = 5000
        z = rng.integers(0, 3, size=n)
        x = rng.integers(0, 2, size=n)
        y = (x ^ z ^ (rng.random(n) < 0.2).astype(np.int64)) % 2
        contrib = cmi_pointwise_contributions(y, x, z)
        # plug-in CMI = MM CMI minus the MM entropy corrections; the pointwise
        # mean equals the *plug-in* CMI, which is close to the MM CMI here.
        mm = conditional_mutual_information(y, x, z)
        assert contrib.mean() == pytest.approx(mm, abs=0.02)

    def test_multicolumn_z(self) -> None:
        rng = np.random.default_rng(4)
        n = 8000
        z = rng.integers(0, 2, size=(n, 2))
        x = rng.integers(0, 2, size=n)
        y = rng.integers(0, 2, size=n)
        cmi = conditional_mutual_information(y, x, z)
        assert abs(cmi) < 0.02  # all independent


class TestStratifiedPermutation:
    def test_conditional_independence_large_p(self) -> None:
        rng = np.random.default_rng(5)
        n = 4000
        z = rng.integers(0, 2, size=n)
        y = np.where(rng.random(n) < np.where(z == 1, 0.8, 0.2), 1, 0)
        x = np.where(rng.random(n) < np.where(z == 1, 0.8, 0.2), 1, 0)
        p = stratified_permutation_pvalue(
            y, x, z, rng=np.random.default_rng(99), n_permutations=199
        )
        assert p > 0.05  # cannot reject conditional independence

    def test_conditional_dependence_small_p(self) -> None:
        rng = np.random.default_rng(6)
        n = 4000
        z = rng.integers(0, 2, size=n)
        x = rng.integers(0, 2, size=n)
        y = (x ^ z ^ (rng.random(n) < 0.1).astype(np.int64)) % 2
        p = stratified_permutation_pvalue(
            y, x, z, rng=np.random.default_rng(99), n_permutations=199
        )
        assert p < 0.01


class TestBootstrapCI:
    def test_covers_mean(self) -> None:
        rng = np.random.default_rng(7)
        v = rng.normal(0.3, 1.0, size=3000)
        ci = stationary_bootstrap_mean_ci(
            v, block_length=10.0, rng=np.random.default_rng(8), n_bootstrap=500
        )
        assert ci.ci_low < ci.point < ci.ci_high
        assert ci.ci_low < 0.3 < ci.ci_high

    def test_positive_signal_excludes_zero(self) -> None:
        rng = np.random.default_rng(9)
        v = rng.normal(0.5, 0.3, size=3000)  # clearly positive mean
        ci = stationary_bootstrap_mean_ci(
            v, block_length=8.0, rng=np.random.default_rng(10), n_bootstrap=500
        )
        assert ci.ci_low > 0.0


class TestNestedPredictiveDelta:
    def test_informative_x_positive_delta(self) -> None:
        rng = np.random.default_rng(11)
        n = 12000
        z = rng.integers(0, 2, size=n)
        x = rng.integers(0, 2, size=n)
        y = (x ^ z ^ (rng.random(n) < 0.15).astype(np.int64)) % 2
        half = n // 2
        d = nested_predictive_delta(y[:half], z[:half], x[:half], y[half:], z[half:], x[half:])
        assert d.delta_logloss > 0.0  # X reduces test log-loss beyond Z
        assert d.delta_mcfadden > 0.0

    def test_redundant_x_nonpositive_delta(self) -> None:
        # X independent of Y given Z => no OOS improvement (delta ~ 0 or < 0).
        rng = np.random.default_rng(12)
        n = 12000
        z = rng.integers(0, 2, size=n)
        x = rng.integers(0, 2, size=n)  # noise
        y = np.where(rng.random(n) < np.where(z == 1, 0.75, 0.25), 1, 0)
        half = n // 2
        d = nested_predictive_delta(y[:half], z[:half], x[:half], y[half:], z[half:], x[half:])
        assert d.delta_logloss < 0.02  # no material improvement

    def test_single_class_raises(self) -> None:
        y = np.zeros(100, dtype=np.int64)
        z = np.zeros(100, dtype=np.int64)
        x = np.zeros(100, dtype=np.int64)
        with pytest.raises(ValueError, match="both target classes"):
            nested_predictive_delta(y, z, x, y, z, x)


class TestPartitionRedundancy:
    def test_identical_partitions(self) -> None:
        a = np.array([0, 0, 1, 1, 2, 2] * 50)
        red = partition_redundancy(a, a)
        assert red.adjusted_rand == pytest.approx(1.0)
        assert red.adjusted_mutual_info == pytest.approx(1.0, abs=1e-6)

    def test_independent_partitions_near_zero(self) -> None:
        rng = np.random.default_rng(13)
        a = rng.integers(0, 4, size=5000)
        b = rng.integers(0, 4, size=5000)
        red = partition_redundancy(a, b)
        assert abs(red.adjusted_rand) < 0.02
        assert abs(red.adjusted_mutual_info) < 0.02
