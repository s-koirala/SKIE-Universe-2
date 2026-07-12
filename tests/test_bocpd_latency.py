"""Unit tests for the H900 BOCPD sensitivity detector (bocpd.py).

Coverage:
- Run-length posterior normalization (Adams & MacKay 2007 Alg. 1 fidelity).
- Scalar (D=1) reduction reproduces the 1.0 primitive's qualitative behavior:
  hard mean-shift collapses the MAP run length; smooth drift stays diffuse.
- anchored_hazard / stationary_distribution closed-form checks.
- Detection-delay layer: change-point recovery, censoring, transition labels,
  empty-transition guard, and CUSUM-parity of the delay convention.
- Multivariate diagonal path (D=2): a shift in either dimension is detected.
- Determinism.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.inference.bocpd import (
    anchored_hazard,
    bocpd_detection_delays,
    run_length_posterior,
    stationary_distribution,
)


def _two_state_log_transmat(a_ii: float) -> np.ndarray:
    p = np.array([[a_ii, 1.0 - a_ii], [1.0 - a_ii, a_ii]])
    return np.log(p)


# ---------------------------------------------------------------------------
# run_length_posterior — recursion fidelity
# ---------------------------------------------------------------------------


def test_posterior_rows_sum_to_one() -> None:
    rng = np.random.default_rng(20260711)
    z = rng.standard_normal(80)
    rl = run_length_posterior(z, hazard=1.0 / 250.0)
    np.testing.assert_allclose(rl.sum(axis=1), 1.0, atol=1e-10)


def test_posterior_shapes() -> None:
    z = np.array([0.1, 0.2, 0.3])
    rl = run_length_posterior(z, hazard=0.01)
    assert rl.shape == (3, 4)  # (T, T+1)


def test_empty_segment() -> None:
    rl = run_length_posterior(np.empty((0, 2)), hazard=0.01)
    assert rl.shape == (0, 1)


def test_hazard_validation() -> None:
    with pytest.raises(ValueError, match="hazard"):
        run_length_posterior([0.0, 1.0], hazard=0.0)
    with pytest.raises(ValueError, match="hazard"):
        run_length_posterior([0.0, 1.0], hazard=1.5)


def test_nig_validation() -> None:
    with pytest.raises(ValueError, match="strictly positive"):
        run_length_posterior([0.0, 1.0], hazard=0.5, kappa_0=0.0)


def test_abrupt_change_collapses_map_run_length() -> None:
    """Adams & MacKay Fig. 2 qualitative: abrupt shift collapses the MAP run length."""
    rng = np.random.default_rng(20260711)
    pre = rng.standard_normal(100)
    post = rng.standard_normal(50) + 5.0
    z = np.concatenate([pre, post])
    rl = run_length_posterior(z, hazard=1.0 / 100.0)
    pre_map = int(rl[99].argmax())
    post_map = int(rl[110].argmax())
    assert pre_map > 50, f"pre-change MAP run length {pre_map} should be large"
    assert post_map < pre_map, "post-change MAP run length should collapse"


def test_smooth_drift_stays_diffuse() -> None:
    rng = np.random.default_rng(20260711)
    z = np.linspace(0.0, 0.5, 200) + rng.standard_normal(200)
    rl = run_length_posterior(z, hazard=1.0 / 250.0)
    final = rl[-1][rl[-1] > 0]
    entropy = -np.sum(final * np.log(final + 1e-300))
    assert entropy > 0.5, f"smooth-drift posterior entropy {entropy:.3f} too peaked"


def test_run_length_truncation_preserves_normalization() -> None:
    rng = np.random.default_rng(1)
    z = rng.standard_normal(200)
    rl = run_length_posterior(z, hazard=1.0 / 100.0, max_run_length=40)
    assert rl.shape == (200, 41)
    np.testing.assert_allclose(rl.sum(axis=1), 1.0, atol=1e-10)


# ---------------------------------------------------------------------------
# hazard anchoring
# ---------------------------------------------------------------------------


def test_stationary_distribution_symmetric() -> None:
    pi = stationary_distribution(_two_state_log_transmat(0.9))
    np.testing.assert_allclose(pi, [0.5, 0.5], atol=1e-9)


def test_stationary_distribution_is_probability() -> None:
    lt = np.log(np.array([[0.8, 0.15, 0.05], [0.1, 0.85, 0.05], [0.2, 0.2, 0.6]]))
    pi = stationary_distribution(lt)
    assert pi.min() >= 0.0
    assert pi.sum() == pytest.approx(1.0)
    # stationarity: pi P = pi
    np.testing.assert_allclose(pi @ np.exp(lt), pi, atol=1e-9)


def test_anchored_hazard_matches_switch_rate() -> None:
    # Symmetric 2-state, a_ii = 0.99, uniform stationary -> switch rate H = 0.01.
    # (Symmetric case: switch rate and per-state 1-a_ii coincide, LITERATURE-3-1.)
    h = anchored_hazard(_two_state_log_transmat(0.99))
    assert h == pytest.approx(0.01, abs=1e-9)


def test_anchored_hazard_in_unit_interval() -> None:
    lt = np.log(np.array([[0.999, 0.001], [0.5, 0.5]]))
    h = anchored_hazard(lt)
    assert 0.0 < h <= 1.0


# ---------------------------------------------------------------------------
# detection-delay layer
# ---------------------------------------------------------------------------


def test_detect_change_point_recovered() -> None:
    rng = np.random.default_rng(20260711)
    pre = rng.standard_normal(100)
    post = rng.standard_normal(100) + 3.0
    z = np.concatenate([pre, post])
    states = np.concatenate([np.zeros(100, int), np.ones(100, int)])
    dd = bocpd_detection_delays(z, states, _two_state_log_transmat(0.99))
    assert dd.delay_bars.size == 1
    assert dd.from_state[0] == 0 and dd.to_state[0] == 1
    assert dd.event[0]  # alarm fired within the successor sojourn
    assert 1 <= dd.delay_bars[0] <= 25, dd.delay_bars[0]


def test_delay_at_least_one() -> None:
    rng = np.random.default_rng(3)
    z = np.concatenate([rng.standard_normal(60), rng.standard_normal(60) + 4.0])
    states = np.concatenate([np.zeros(60, int), np.ones(60, int)])
    dd = bocpd_detection_delays(z, states, _two_state_log_transmat(0.98))
    assert (dd.delay_bars >= 1).all()


def test_no_transitions_returns_empty() -> None:
    z = np.random.default_rng(0).standard_normal((50, 2))
    states = np.zeros(50, int)
    dd = bocpd_detection_delays(z, states, _two_state_log_transmat(0.95))
    assert dd.delay_bars.size == 0
    assert dd.event.size == 0
    assert dd.hazard.size == 0


def test_censoring_when_no_alarm() -> None:
    # Successor identical to incumbent (no real change) but state label flips:
    # the detector should frequently censor (no MAP reset) -> event False,
    # delay == remaining sojourn.
    z = np.zeros(40)  # constant; no distributional change at the label flip
    states = np.concatenate([np.zeros(20, int), np.ones(20, int)])
    dd = bocpd_detection_delays(z, states, _two_state_log_transmat(0.95), hazard=1e-4)
    assert dd.delay_bars.size == 1
    # With a tiny hazard and no real change, no reset -> censored at sojourn end.
    assert dd.event[0] == np.bool_(False)
    assert dd.delay_bars[0] == 20


def test_alignment_validation() -> None:
    with pytest.raises(ValueError, match="aligned"):
        bocpd_detection_delays(np.zeros((10, 2)), np.zeros(9, int), _two_state_log_transmat(0.9))


def test_multivariate_shift_in_second_dim_detected() -> None:
    rng = np.random.default_rng(20260711)
    pre = rng.standard_normal((100, 2))
    post = rng.standard_normal((100, 2))
    post[:, 1] += 3.0  # shift only the second dimension
    z = np.concatenate([pre, post])
    states = np.concatenate([np.zeros(100, int), np.ones(100, int)])
    dd = bocpd_detection_delays(z, states, _two_state_log_transmat(0.99))
    assert dd.event[0]
    assert 1 <= dd.delay_bars[0] <= 25


def test_determinism() -> None:
    rng = np.random.default_rng(7)
    z = np.concatenate([rng.standard_normal(80), rng.standard_normal(80) + 2.5])
    states = np.concatenate([np.zeros(80, int), np.ones(80, int)])
    lt = _two_state_log_transmat(0.98)
    a = bocpd_detection_delays(z, states, lt)
    b = bocpd_detection_delays(z, states, lt)
    np.testing.assert_array_equal(a.delay_bars, b.delay_bars)
    np.testing.assert_array_equal(a.event, b.event)


def test_alarm_prob_validation() -> None:
    z = np.zeros((10, 2))
    states = np.concatenate([np.zeros(5, int), np.ones(5, int)])
    lt = _two_state_log_transmat(0.9)
    with pytest.raises(ValueError, match="alarm_prob"):
        bocpd_detection_delays(z, states, lt, alarm_prob=0.0)
    with pytest.raises(ValueError, match="alarm_prob"):
        bocpd_detection_delays(z, states, lt, alarm_prob=1.0)


def test_detected_cp_localizes_near_true_change() -> None:
    """BOCPD's own change-location estimate should sit near the true transition."""
    rng = np.random.default_rng(20260711)
    z = np.concatenate([rng.standard_normal(100), rng.standard_normal(100) + 3.0])
    states = np.concatenate([np.zeros(100, int), np.ones(100, int)])
    dd = bocpd_detection_delays(z, states, _two_state_log_transmat(0.99))
    assert dd.true_cp_index[0] == 100
    assert dd.event[0]
    # localization error within a couple of bars of the true change-point.
    assert abs(int(dd.detected_cp_index[0]) - 100) <= 3, dd.detected_cp_index[0]


def test_censored_transition_has_no_detected_cp() -> None:
    z = np.zeros(40)
    states = np.concatenate([np.zeros(20, int), np.ones(20, int)])
    dd = bocpd_detection_delays(z, states, _two_state_log_transmat(0.95), hazard=1e-4)
    assert not dd.event[0]
    assert int(dd.detected_cp_index[0]) == -1  # sentinel for "no detection"
    assert int(dd.true_cp_index[0]) == 20


def test_higher_alarm_prob_never_detects_sooner() -> None:
    """A stricter posterior-majority threshold cannot shorten the delay."""
    rng = np.random.default_rng(11)
    z = np.concatenate([rng.standard_normal(60), rng.standard_normal(60) + 3.5])
    states = np.concatenate([np.zeros(60, int), np.ones(60, int)])
    lt = _two_state_log_transmat(0.98)
    lax = bocpd_detection_delays(z, states, lt, alarm_prob=0.5)
    strict = bocpd_detection_delays(z, states, lt, alarm_prob=0.9)
    # Both fire for this seed/+3.5-sigma shift (no vacuous pass, CODE-2-1).
    assert lax.event[0] and strict.event[0]
    assert strict.delay_bars[0] >= lax.delay_bars[0]


def test_smaller_hazard_never_detects_sooner() -> None:
    """Conservative-bias witness (QUANT-1-2): a smaller hazard (longer prior
    run length) cannot detect a change SOONER. This underpins the H900 claim
    that the eval-fold hazard = 1/median-dwell cannot manufacture a GO — a
    longer dwell => smaller hazard => longer/equal L_detect => larger D_be.
    """
    rng = np.random.default_rng(20260711)
    z = np.concatenate([rng.standard_normal(80), rng.standard_normal(80) + 2.5])
    states = np.concatenate([np.zeros(80, int), np.ones(80, int)])
    lt = _two_state_log_transmat(0.97)
    sensitive = bocpd_detection_delays(z, states, lt, hazard=0.20)  # short-run prior
    reluctant = bocpd_detection_delays(z, states, lt, hazard=0.01)  # long-run prior
    # Both must fire for this seed/shift so the property is actually exercised
    # (no vacuous pass — this is the load-bearing conservative-bias witness).
    assert sensitive.event[0] and reluctant.event[0]
    assert reluctant.delay_bars[0] >= sensitive.delay_bars[0]
