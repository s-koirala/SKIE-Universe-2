"""CUSUM (Page 1954) detection-latency estimation for H900.

H900 design.md §7: L_detect = median detection latency in bars,
estimated as the CUSUM alarm delay against the filtered change-points
of the fitted HMM's causal state sequence (BOCPD, Adams & MacKay 2007,
is the registered sensitivity detector; see the H900 report card for
its disposition).

Detector construction
---------------------

For a filtered transition incumbent i -> successor j at bar tau, the
detector is the one-sided log-likelihood-ratio CUSUM

    S_tau-1 = 0;   S_t = max(0, S_{t-1} + log b_j(y_t) - log b_i(y_t))

run on the standardized emission vector under the fitted state-
conditional Gaussian densities. This is exactly Page's (1954) scheme
with the SPRT increment, which is optimal in Lorden's minimax sense
(Moustakides 1986). Starting from S = 0 at the change-point measures
the conditional detection delay of the transition that occurred.

Threshold (no free tuning parameter)
------------------------------------

The alarm threshold is h_i = log(ARL0_i) with the in-control average
run length anchored to the fitted model's own expected sojourn of the
incumbent state, ARL0_i = 1 / (1 - a_ii): a detector whose false-alarm
cadence exceeds the regime cadence would make the rotor switch on
noise. Lorden (1971) gives ARL0 >= e^h for the LLR-CUSUM, so
h = log(ARL0) guarantees at most ~one false alarm per expected sojourn.
Both inputs (a_ii, emission densities) come from the training-window
fit; nothing is tuned against the dwell outcome.

Delay convention: delay = (alarm bar - tau) + 1, i.e. the number of
post-change bars consumed before the alarm (>= 1; the detector cannot
alarm on zero observations). If no alarm fires before the next filtered
transition, the delay is right-censored at the observed sojourn length.

References
----------

- Page, E. S. 1954. "Continuous Inspection Schemes". *Biometrika*
  41(1/2): 100-115. https://doi.org/10.1093/biomet/41.1-2.100
- Lorden, G. 1971. "Procedures for Reacting to a Change in
  Distribution". *Ann. Math. Statist.* 42(6): 1897-1908.
  https://doi.org/10.1214/aoms/1177693055
- Moustakides, G. V. 1986. "Optimal Stopping Times for Detecting
  Changes in Distributions". *Ann. Statist.* 14(4): 1379-1387.
  https://doi.org/10.1214/aos/1176350164
- Adams, R. P. & MacKay, D. J. C. 2007. "Bayesian Online Changepoint
  Detection". arXiv:0710.3742 (registered sensitivity detector).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DetectionDelays:
    """CUSUM alarm delays for the transitions of one window.

    delay_bars
        Observed delay (bars, >= 1) per filtered transition.
    event
        True when the alarm fired within the successor's sojourn;
        False when right-censored at the sojourn end.
    from_state / to_state
        Transition labels.
    threshold
        The h_i used for each transition (= log ARL0 of the incumbent).
    """

    delay_bars: np.ndarray
    event: np.ndarray
    from_state: np.ndarray
    to_state: np.ndarray
    threshold: np.ndarray


def cusum_detection_delays(
    log_b: np.ndarray,
    states: np.ndarray,
    log_transmat: np.ndarray,
) -> DetectionDelays:
    """Measure CUSUM alarm delays against filtered change-points.

    Parameters
    ----------
    log_b
        (T, N) log emission densities of the window's (standardized)
        observations under the fitted model — the same matrix the
        causal filter consumed.
    states
        (T,) causal filtered state sequence of the window.
    log_transmat
        (N, N) fitted log transition matrix (source of ARL0 anchors).
    """
    lb = np.asarray(log_b, dtype=np.float64)
    s = np.asarray(states)
    lt = np.asarray(log_transmat, dtype=np.float64)
    if lb.ndim != 2 or s.ndim != 1 or lb.shape[0] != s.size:  # noqa: PLR2004 — array-rank check
        raise ValueError("log_b must be (T, N) aligned with states (T,).")
    n_states = lb.shape[1]
    if lt.shape != (n_states, n_states):
        raise ValueError("log_transmat shape mismatch with log_b state count.")

    # Transition indices: bar tau is the first bar of the new spell.
    taus = np.flatnonzero(s[1:] != s[:-1]) + 1
    delays: list[int] = []
    events: list[bool] = []
    froms: list[int] = []
    tos: list[int] = []
    thresholds: list[float] = []
    t_len = s.size
    for k, tau in enumerate(taus):
        i = int(s[tau - 1])
        j = int(s[tau])
        # ARL0 anchor: expected sojourn of the incumbent under the
        # fitted chain, 1 / (1 - a_ii). h = log(ARL0) per Lorden 1971.
        a_ii = float(np.exp(lt[i, i]))
        # Guard: a_ii == 1 would give infinite h; a_ii == 0 gives
        # ARL0 = 1 => h = 0 (alarm on first informative bar).
        a_ii = min(a_ii, 1.0 - np.finfo(np.float64).eps)
        h = float(np.log(1.0 / (1.0 - a_ii)))
        # Sojourn end: next transition or window edge (exclusive).
        end = int(taus[k + 1]) if k + 1 < taus.size else t_len
        stat = 0.0
        alarm_delay = None
        for t in range(tau, end):
            stat = max(0.0, stat + (lb[t, j] - lb[t, i]))
            if stat >= h:
                alarm_delay = t - tau + 1
                break
        if alarm_delay is None:
            delays.append(end - tau)  # censored at observed sojourn
            events.append(False)
        else:
            delays.append(int(alarm_delay))
            events.append(True)
        froms.append(i)
        tos.append(j)
        thresholds.append(h)

    return DetectionDelays(
        delay_bars=np.asarray(delays, dtype=np.int64),
        event=np.asarray(events, dtype=bool),
        from_state=np.asarray(froms, dtype=np.int64),
        to_state=np.asarray(tos, dtype=np.int64),
        threshold=np.asarray(thresholds, dtype=np.float64),
    )
