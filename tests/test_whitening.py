"""Unit tests for AR(1) prewhitening (P1-2.0-H900-BOCPD-WHITENED).

Coverage:
- AR(1) coefficient recovery on a known process; white input -> phi ~ 0.
- within-run estimation excludes change-crossing pairs.
- whitening removes serial correlation (residual lag-1 autocorr ~ 0).
- a level shift survives whitening as an amplified innovation: exact on a
  deterministic step (delta/sqrt(1-phi^2); spike/steady = 1/(1-phi)) and, in
  expectation, matching that amplification over many seeds (a single
  near-unit-root realization can mask it, so detectability is a distributional
  property, not a single-seed one).
- Bayes-operating-point behaviour (phi=0.99, alarm_prob=0.5): whitened BOCPD
  DETECTS clean synthetic shifts well (true-positive rate ~0.95 at delta=3) but
  does NOT control false alarms (~0.43 on no-change label flips; Wilson 95%
  lower bound >> the 0.05 significance reference). These fix one reproducible
  ROC point. The ROC-WIDE "no accurate-and-timely operating point" NO-GO is the
  prior on-ledger probe's result (session_handoff sec.2: net~26pp needs
  L_detect~45 bars; ~4 bars -> noise), deferred here for a reproducible
  on-ledger re-run.
  See docs/methodology/whitening_ar_robust_bocpd_2026-07-13.md.

Statistical tolerances/sample sizes below are Monte-Carlo sampling bands, not
tuned research thresholds: each is a finite-sample band the reproduced statistic
clears with margin (sizes chosen so the CI/SE is small vs the asserted gap; see
per-line comments). phi=0.99 is a conservative near-unit-root proxy for the
structural log_rvol rho~=0.997 — amplification 1/sqrt(1-phi^2) and the alarm
rate are both monotone increasing in phi, so 0.99 lower-bounds the effect.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.inference.bocpd import bocpd_detection_delays
from skie_universe2.inference.whitening import ar1_within_run, whiten_ar1


def _ar1(n: int, phi: float, rng: np.random.Generator, mu: float = 0.0) -> np.ndarray:
    x = np.empty(n)
    x[0] = rng.standard_normal()
    for t in range(1, n):
        x[t] = phi * x[t - 1] + rng.standard_normal() * np.sqrt(1 - phi**2)
    return x + mu


def _two_state_log_transmat(a_ii: float) -> np.ndarray:
    return np.log(np.array([[a_ii, 1 - a_ii], [1 - a_ii, a_ii]]))


def test_ar1_recovers_known_phi() -> None:
    rng = np.random.default_rng(0)
    z = _ar1(5000, 0.9, rng)[:, None]
    states = np.zeros(5000, int)  # single run
    phi = ar1_within_run(z, states)
    # 0.03 band ~ 5x the LS SE sqrt((1-phi^2)/n)=sqrt(0.19/5000)~0.006 at n=5000
    assert abs(phi[0] - 0.9) < 0.03, phi[0]


def test_white_input_phi_near_zero() -> None:
    rng = np.random.default_rng(1)
    z = rng.standard_normal((4000, 1))
    phi = ar1_within_run(z, np.zeros(4000, int))
    # 0.05 band ~ 3x the SE 1/sqrt(n)=0.016 of a white-series lag-1 estimate, n=4000
    assert abs(phi[0]) < 0.05, phi[0]


def test_within_run_excludes_change_bars() -> None:
    # Two runs with a large level gap at the boundary; the cross-boundary pair
    # must NOT dominate the within-run estimate.
    rng = np.random.default_rng(2)
    a = _ar1(2000, 0.5, rng, mu=0.0)
    b = _ar1(2000, 0.5, rng, mu=20.0)  # big level shift at the join
    z = np.concatenate([a, b])[:, None]
    states = np.concatenate([np.zeros(2000, int), np.ones(2000, int)])
    phi = ar1_within_run(z, states)
    # 0.05 band ~ 3.6x the pooled LS SE sqrt((1-0.25)/4000)~0.014; a join-contaminated
    # estimate would sit near 1.0, far outside this band.
    assert abs(phi[0] - 0.5) < 0.05, phi[0]  # not pulled toward 1 by the join


def test_whitening_removes_autocorrelation() -> None:
    rng = np.random.default_rng(3)
    z = _ar1(4000, 0.95, rng)[:, None]
    states = np.zeros(4000, int)
    phi = ar1_within_run(z, states)
    w = whiten_ar1(z, phi)
    lag1 = np.corrcoef(w[:-1, 0], w[1:, 0])[0, 1]
    # 0.05 band ~ 3x the null SE 1/sqrt(n)=0.016 of a sample autocorrelation, n=4000
    assert abs(lag1) < 0.05, lag1


def test_level_shift_amplification_exact() -> None:
    # DETERMINISTIC (no RNG): a unit step of magnitude delta at bar k.
    # Eq. (W2): the whitened innovation at the shift bar equals exactly
    #   delta / sqrt(1 - phi^2)  (amplified, not damped).
    # Eq. (W3): that spike is exactly 1/(1-phi) times the steady post-shift
    #   innovation delta*(1-phi)/sqrt(1-phi^2). Seed-free, so no single-draw
    #   fragility; this is the load-bearing "real shifts survive whitening".
    phi, delta, k = 0.99, 3.0, 50
    z = np.concatenate([np.zeros(k), np.full(k, delta)])[:, None]
    w = whiten_ar1(z, np.array([phi]))
    spike, steady = w[k, 0], w[k + 1, 0]
    assert np.isclose(spike, delta / np.sqrt(1 - phi**2)), spike
    assert np.isclose(steady, delta * (1 - phi) / np.sqrt(1 - phi**2)), steady
    assert np.isclose(spike / steady, 1.0 / (1.0 - phi)), spike / steady


def test_level_shift_amplified_in_expectation() -> None:
    # Over many seeds the MEDIAN whitened shift-innovation / stable-sd matches the
    # theoretical amplification delta/sqrt(1-phi^2). A single near-unit-root
    # realization can mask the shift (the phi~1 pre-series is near-random-walk and
    # can wander to the post level), so detectability is a property of the
    # sampling distribution, tested on the median rather than on one seed.
    # n_seed=400: realized median 20.15 vs theory 21.27 is 5.3% off, inside the
    # rtol=0.10 MC band (a sampling tolerance, not a fitted threshold).
    phi, delta, k, n_seed = 0.99, 3.0, 300, 400
    theo = delta / np.sqrt(1 - phi**2)
    ratios = np.empty(n_seed)
    for s in range(n_seed):
        rng = np.random.default_rng(s)
        pre = _ar1(k, phi, rng, mu=0.0)
        post = _ar1(k, phi, rng, mu=delta)
        z = np.concatenate([pre, post])[:, None]
        w = whiten_ar1(z, np.array([phi]))
        ratios[s] = abs(w[k, 0]) / np.std(w[10 : k - 10, 0])
    assert np.isclose(np.median(ratios), theo, rtol=0.10), (np.median(ratios), theo)


def test_whiten_shape_and_edges() -> None:
    assert whiten_ar1(np.empty((0, 2)), np.array([0.5, 0.5])).shape == (0, 2)
    w = whiten_ar1(np.array([1.0, 2.0, 3.0]), np.array([0.5]))
    assert w.shape == (3, 1)
    assert w[0, 0] == 1.0  # first bar passes through
    with pytest.raises(ValueError, match="length-D"):
        whiten_ar1(np.zeros((5, 2)), np.array([0.5]))


def _wilson_lower_95(k: int, n: int) -> float:
    """Wilson (1927) score-interval lower bound for a binomial proportion at 95%."""
    z = 1.959963984540054  # standard-normal 0.975 quantile
    p = k / n
    denom = 1.0 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = (z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return center - half


def test_whitened_false_alarm_not_controlled() -> None:
    """FALSE-ALARM NON-CONTROL at the Bayes operating point (load-bearing).

    On stable near-unit-root AR(1) segments with a state-label flip but NO
    distributional change, whitened BOCPD alarms at ~0.43 — it does NOT control
    false alarms. Prewhitening removes the by-construction serial correlation the
    step-2 report flagged, yet the detector stays trigger-happy at alarm_prob=0.5.
    This is ONE ROC point (paired with the true-positive rate below); the
    ROC-WIDE "no accurate-and-timely operating point" NO-GO is the prior
    on-ledger probe's result (session_handoff sec.2), not asserted from synthetic
    substrate here. We take the Wilson 95% lower bound of the alarm rate above the
    conventional 0.05 significance reference (the previous n=40, thr<0.30 test had
    a +/-0.15 CI and a made-up threshold; both are removed).
    """
    lt = _two_state_log_transmat(0.99)
    # n_seg=200: at p~0.43 the Wilson 95% half-width is ~0.068, so the lower bound
    # ~0.363 clears the 0.05 reference by >4 half-widths (n=40 gave +/-0.15).
    n_seg = 200
    false_alarms = 0
    for seed in range(n_seg):
        rng = np.random.default_rng(1000 + seed)
        # one stationary AR(1) process throughout; the label flips at the mid
        # point but the generating distribution does NOT change.
        x = _ar1(240, 0.99, rng)[:, None]
        states = np.concatenate([np.zeros(120, int), np.ones(120, int)])
        phi = ar1_within_run(x, states)
        w = whiten_ar1(x, phi)
        dd = bocpd_detection_delays(w, states, lt)
        false_alarms += int(dd.event[0]) if dd.event.size else 0
    wilson_low = _wilson_lower_95(false_alarms, n_seg)
    assert wilson_low > 0.05, (false_alarms / n_seg, wilson_low)


def test_whitened_true_change_detection_rate() -> None:
    """Reproducible true-positive rate at the SAME Bayes operating point.

    Pairs with test_whitened_false_alarm_not_controlled to fix one ROC point
    (FPR~0.43, TPR~0.95 at alarm_prob=0.5, delta=3). On CLEAN synthetic shifts
    the whitened detector discriminates well; the ~0.43 false-alarm rate is the
    price. This is exactly why the ROC-WIDE NO-GO cannot be read off synthetic
    clean shifts and rests on the on-ledger probe over the SUBTLE real regime
    changes (session_handoff sec.2). Asserting TPR's Wilson lower bound sits well
    above the false-alarm lower bound shows the two rates are genuinely ordered.
    """
    lt = _two_state_log_transmat(0.99)
    n_seg = 200  # matched to the false-alarm test for a same-precision ROC point
    hits = 0
    for seed in range(n_seg):
        rng = np.random.default_rng(1000 + seed)
        pre = _ar1(120, 0.99, rng, mu=0.0)
        post = _ar1(120, 0.99, rng, mu=3.0)  # a real delta=3 level shift at the flip
        x = np.concatenate([pre, post])[:, None]
        states = np.concatenate([np.zeros(120, int), np.ones(120, int)])
        phi = ar1_within_run(x, states)
        w = whiten_ar1(x, phi)
        dd = bocpd_detection_delays(w, states, lt)
        hits += int(dd.event[0]) if dd.event.size else 0
    tpr_low = _wilson_lower_95(hits, n_seg)
    # TPR ~0.945 (Wilson low ~0.90) >> the false-alarm Wilson low ~0.36: on clean
    # shifts the detector is not degenerate. 0.5 is a generous ordering floor,
    # comfortably below the realized bound, not a tuned target.
    assert tpr_low > 0.5, (hits / n_seg, tpr_low)


@pytest.mark.parametrize("delta", [0.5, 1.0, 3.0])
def test_whitened_detection_rate_across_shift_sizes(delta: float) -> None:
    """Detection stays high across shift magnitudes (frozen sweep for memo §4).

    Backs the memo's "detects across delta in [0.5, 3]" statement with a robust,
    frozen assertion: at each delta the Wilson 95% lower bound of the detection
    rate exceeds 0.5 (realized rates ~0.82 / 0.86 / 0.95 at delta = 0.5 / 1 / 3),
    so the whitened detector is not degenerate on smaller shifts either. Only the
    >0.5 floor is asserted (not the exact rate), to stay robust to MC/BLAS drift.
    """
    lt = _two_state_log_transmat(0.99)
    n_seg = 200
    hits = 0
    for seed in range(n_seg):
        rng = np.random.default_rng(1000 + seed)
        pre = _ar1(120, 0.99, rng, mu=0.0)
        post = _ar1(120, 0.99, rng, mu=delta)
        x = np.concatenate([pre, post])[:, None]
        states = np.concatenate([np.zeros(120, int), np.ones(120, int)])
        phi = ar1_within_run(x, states)
        w = whiten_ar1(x, phi)
        dd = bocpd_detection_delays(w, states, lt)
        hits += int(dd.event[0]) if dd.event.size else 0
    assert _wilson_lower_95(hits, n_seg) > 0.5, (delta, hits / n_seg)


def test_true_change_still_detected_after_whitening() -> None:
    """Positive control: a real level shift IS detected fast after whitening."""
    rng = np.random.default_rng(7)
    pre = _ar1(120, 0.99, rng, mu=0.0)
    post = _ar1(120, 0.99, rng, mu=3.0)
    x = np.concatenate([pre, post])[:, None]
    states = np.concatenate([np.zeros(120, int), np.ones(120, int)])
    phi = ar1_within_run(x, states)
    w = whiten_ar1(x, phi)
    dd = bocpd_detection_delays(w, states, _two_state_log_transmat(0.99))
    assert dd.event[0]
    assert dd.delay_bars[0] <= 10, dd.delay_bars[0]
