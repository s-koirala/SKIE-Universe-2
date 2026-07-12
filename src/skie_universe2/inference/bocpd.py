"""BOCPD (Adams & MacKay 2007) detection-latency estimation for H900.

Registered sensitivity detector for the H900 break-even-dwell derivation
(design.md §7): L_detect = median detection latency in bars, measured as
the alarm delay against the *filtered change-points* of the fitted HMM's
causal state sequence. The primary detector is the LLR-CUSUM
([cusum.py](cusum.py); Page 1954); this module is the registered BOCPD
sensitivity detector whose deferral is closed by the follow-up
``P1-2.0-H900-BOCPD-SENSITIVITY`` (report §6 deviation 1, §9).

Relationship to the 1.0 reference
----------------------------------

The run-length recursion, the normal-inverse-gamma (NIG) conjugate update,
and the Student-t predictive are a numerical-fidelity port of SKIE-Universe
1.0 ``src/skie_ninja/inference/bocd.py`` (Adams & MacKay 2007, Algorithm 1).
The scalar path (``D == 1``) reproduces the 1.0 primitive exactly; the port
generalizes the observation model to the ``D``-dimensional **diagonal**
Gaussian emission of the H900 HMM by factorizing the predictive across
dimensions (independent per-dimension NIG; log-predictives summed). This is
the exact likelihood implied by the fitted diagonal-covariance emission and
introduces no new coupling.

Two 1.0 operating parameters are deliberately NOT carried over, because they
are SKIE-Universe 1.0 ADR-0018 project-operational defaults (magic numbers)
inappropriate for the H900 estimand. The H900 runner
(``scripts/run_h900_dwell_study.py``) sets them as follows (this module's
function defaults differ and are documented per-function):

- ``hazard``: instead of the 1.0 default ``1/250``, the H900 run supplies a
  data-derived constant hazard equal to ``1 / median(filtered dwell)`` of the
  evaluation window — the regime-switching cadence. This is the optimistic,
  liberal calibration registered for 2.0. Because it is the eval-fold median
  dwell, it biases the break-even comparison CONSERVATIVELY (a longer dwell
  gives a smaller hazard, hence a larger L_detect and a larger D_be), so it
  cannot manufacture a GO. :func:`anchored_hazard` — the stationary switch rate
  ``sum_i pi_i (1 - a_ii)``, whose reciprocal is the mean pooled inter-switch
  interval (elementary Markov arithmetic, not a change-detection-theory result)
  — is this module's default and the registered robustness alternative; the
  NO-GO holds under both (see the H900 report).
- alarm rule: instead of the 1.0 fixed ``window``/``threshold`` test, the
  changepoint alarm is the **posterior-majority** rule — the first post-change
  bar at which the run-length posterior places at least ``alarm_prob`` mass
  (default 0.5, the Bayes-optimal decision boundary under 0-1 loss) on run
  lengths whose implied segment start is at or after the true filtered
  change-point. The run-length posterior mode (MAP) is used only to REPORT the
  detected changepoint location, not to trigger the alarm (Adams & MacKay
  2007 §2 / Algorithm 1; Fearnhead & Liu 2007, online declaration via run
  length). ``alarm_prob`` is a decision rule, not a tuned parameter.

Detector construction
---------------------

For a filtered transition incumbent ``i`` -> successor ``j`` at bar ``tau``,
BOCPD is run over the local window ``[tau_prev, tau_next)`` (per-transition
anchored) on the standardized emission vectors ``z_t`` (NOT the HMM emission
densities — the detector is model-light by design, which is the point of a
sensitivity check). The delay is the number of post-change bars consumed
before the posterior-majority alarm fires:

    delay = (alarm bar - tau) + 1   (>= 1),

right-censored at the next filtered transition or the segment edge, matching
the CUSUM censoring convention so the two L_detect estimates are comparable.
Note (KM censoring): the censoring time is the successor sojourn length, which
is not guaranteed independent of the detection delay across pooled transition
types; the H900 report treats L_detect's non-informative-censoring assumption
as a documented caveat and reports the uncensored-event-delay median as a
biased-low companion (alarm-selected subsample), not a robustness guarantee —
its bias direction is conditional on the unresolved attribution of the
non-alarming transitions (report §4/§5.1). The NIG predictive further assumes
iid-within-run
observations, which the autocorrelated ``log_rvol`` emission violates by
construction (overlapping rolling window); the net direction on L_detect is
expected-but-unverified (an evidence-over-count effect and a
variance-under-estimate effect oppose), and a whitened/AR variant is a
registered limitation and future work.

References
----------

- Adams, R. P. & MacKay, D. J. C. 2007. "Bayesian Online Changepoint
  Detection". arXiv:0710.3742. https://arxiv.org/abs/0710.3742
- Fearnhead, P. & Liu, Z. 2007. "On-line Inference for Multiple Changepoint
  Problems". *J. R. Stat. Soc. B* 69(4): 589-605.
  https://doi.org/10.1111/j.1467-9868.2007.00601.x
- Murphy, K. P. 2007. "Conjugate Bayesian analysis of the Gaussian
  distribution". UBC technical note (NIG posterior-update formulas).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.special import logsumexp
from scipy.stats import t as student_t

__all__ = [
    "BocpdDetectionDelays",
    "anchored_hazard",
    "bocpd_detection_delays",
    "run_length_posterior",
    "stationary_distribution",
]


# --------------------------------------------------------------------------
# NIG / Student-t predictive (vectorized over run length R and dimension D)
# --------------------------------------------------------------------------


def _student_t_logpdf_sum(
    x: np.ndarray,
    mu: np.ndarray,
    kappa: np.ndarray,
    alpha: np.ndarray,
    beta: np.ndarray,
) -> np.ndarray:
    """Diagonal Gaussian log-predictive summed over dimensions.

    Under a per-dimension normal-inverse-gamma posterior with sufficient
    statistics ``(mu, kappa, alpha, beta)`` each shaped ``(R, D)``, the
    posterior predictive of the ``D``-vector ``x`` factorizes across
    dimensions as a product of Student-t densities (Murphy 2007):

        x_d ~ t_{2 alpha_d}(mu_d, beta_d (kappa_d + 1) / (alpha_d kappa_d)).

    The diagonal emission makes the joint log-predictive the per-dimension
    sum. Returns a length-``R`` array of joint log-predictive densities.
    """
    df = 2.0 * alpha
    scale = np.sqrt(beta * (kappa + 1.0) / (alpha * kappa))
    # x broadcasts (D,) against (R, D); sum the per-dim Student-t logpdfs.
    logp = student_t.logpdf(x[np.newaxis, :], df=df, loc=mu, scale=scale)
    return logp.sum(axis=1)


def run_length_posterior(
    z: np.ndarray,
    hazard: float,
    *,
    mu_0: float = 0.0,
    kappa_0: float = 1.0,
    alpha_0: float = 1.0,
    beta_0: float = 1.0,
    max_run_length: int | None = None,
) -> np.ndarray:
    """Adams & MacKay 2007 Algorithm 1 run-length posterior over a segment.

    Faithful port of the 1.0 ``bocd_run`` recursion, generalized to
    ``D``-dimensional diagonal observations and with optional run-length
    truncation for long segments.

    Parameters
    ----------
    z
        ``(T, D)`` standardized emission vectors of one segment. A ``(T,)``
        input is treated as ``D = 1`` (exact 1.0-scalar reduction).
    hazard
        Constant hazard ``H = 1/lambda`` in ``(0, 1]`` (see
        :func:`anchored_hazard`).
    mu_0, kappa_0, alpha_0, beta_0
        NIG prior hyperparameters. Weakly informative and, because ``z`` is
        the fit's standardized emission (marginally ~N(0, 1) per dimension),
        canonical rather than tuned: ``mu_0 = 0`` matches the standardization
        mean and ``kappa_0 = alpha_0 = beta_0 = 1`` is the unit-scale
        one-pseudo-observation prior. Nothing here is fit to the dwell
        outcome.
    max_run_length
        If set, the run-length support is capped at this many states (the
        smallest-run-length mass beyond the cap is folded into the largest
        retained run length, preserving normalization). ``None`` keeps the
        exact ``O(T^2)`` support; the H900 runner caps it at a multiple of
        the fitted sojourn for long sessions.

    Returns
    -------
    np.ndarray
        ``(T, R_max + 1)`` array; row ``t`` is the normalized posterior
        ``P(r_t = r | z_{0:t})`` (zero-padded on the right when truncated).
    """
    if not (0.0 < hazard <= 1.0):
        raise ValueError(f"hazard must be in (0, 1]; got {hazard}.")
    if kappa_0 <= 0.0 or alpha_0 <= 0.0 or beta_0 <= 0.0:
        raise ValueError("kappa_0, alpha_0, beta_0 must be strictly positive.")

    arr = np.asarray(z, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, np.newaxis]
    if arr.ndim != 2:  # noqa: PLR2004 — array-rank check
        raise ValueError(f"z must be 1-D or 2-D; got shape {arr.shape}.")
    t_len, d = arr.shape
    log_h = np.log(hazard)
    log_1mh = np.log1p(-hazard) if hazard < 1.0 else -np.inf

    if t_len == 0:
        return np.zeros((0, 1), dtype=np.float64)

    cap = t_len if max_run_length is None else min(max_run_length, t_len)

    # Per-run-length NIG sufficient statistics, shape (R, D). Seeded with
    # the prior row (r = 0).
    mu = np.full((1, d), float(mu_0))
    kappa = np.full((1, d), float(kappa_0))
    alpha = np.full((1, d), float(alpha_0))
    beta = np.full((1, d), float(beta_0))
    log_joint = np.array([0.0])  # unnormalized log P(r_0 = 0, .) = 0

    out = np.zeros((t_len, cap + 1), dtype=np.float64)

    for t in range(t_len):
        x = arr[t]
        log_pred = _student_t_logpdf_sum(x, mu, kappa, alpha, beta)

        log_growth = log_joint + log_pred + log_1mh
        log_cp = logsumexp(log_joint + log_pred + log_h)
        new_log_joint = np.concatenate(([log_cp], log_growth))

        # NIG growth update (Murphy 2007), prior row prepended for r = 0.
        new_kappa = np.concatenate(([[kappa_0] * d], kappa + 1.0), axis=0)
        new_mu = np.concatenate(([[mu_0] * d], (kappa * mu + x) / (kappa + 1.0)), axis=0)
        new_alpha = np.concatenate(([[alpha_0] * d], alpha + 0.5), axis=0)
        new_beta = np.concatenate(
            ([[beta_0] * d], beta + (kappa * (x - mu) ** 2) / (2.0 * (kappa + 1.0))),
            axis=0,
        )

        # Optional run-length truncation: fold the oldest-run-length mass into
        # the largest retained state so the posterior stays normalized.
        if new_log_joint.size > cap + 1:
            keep = cap + 1
            folded = logsumexp(new_log_joint[keep - 1 :])
            new_log_joint = np.concatenate((new_log_joint[: keep - 1], [folded]))
            new_mu = new_mu[:keep]
            new_kappa = new_kappa[:keep]
            new_alpha = new_alpha[:keep]
            new_beta = new_beta[:keep]

        log_joint = new_log_joint
        mu, kappa, alpha, beta = new_mu, new_kappa, new_alpha, new_beta

        posterior = np.exp(log_joint - logsumexp(log_joint))
        out[t, : posterior.size] = posterior

    return out


# --------------------------------------------------------------------------
# Hazard anchoring
# --------------------------------------------------------------------------


def stationary_distribution(log_transmat: np.ndarray) -> np.ndarray:
    """Stationary distribution of the fitted Markov chain.

    Left eigenvector of ``P = exp(log_transmat)`` for eigenvalue 1,
    normalized to a probability vector. Falls back to the uniform
    distribution if the chain is degenerate (no unit eigenvalue found to
    tolerance), which keeps :func:`anchored_hazard` finite.
    """
    p = np.exp(np.asarray(log_transmat, dtype=np.float64))
    n = p.shape[0]
    vals, vecs = np.linalg.eig(p.T)
    idx = int(np.argmin(np.abs(vals - 1.0)))
    vec = np.real(vecs[:, idx])
    total = vec.sum()
    if not np.isfinite(total) or abs(total) < 1e-12:  # noqa: PLR2004 — degeneracy tol
        return np.full(n, 1.0 / n)
    pi = vec / total
    # Numerical negatives from the eig solve -> clip and renormalize.
    pi = np.clip(pi, 0.0, None)
    s = pi.sum()
    return pi / s if s > 0 else np.full(n, 1.0 / n)


def anchored_hazard(log_transmat: np.ndarray) -> float:
    """Constant hazard = the fitted chain's stationary switch rate.

    The stationary switch rate — the occupancy-weighted probability of leaving
    the current state on a given bar — is ``H = sum_i pi_i (1 - a_ii)``; its
    reciprocal ``1 / H`` is the mean pooled inter-switch interval (elementary
    Markov arithmetic, not a change-detection-theory result; it equals the
    occupancy-weighted per-state sojourn ``sum_i pi_i / (1 - a_ii)`` only when
    all ``a_ii`` are equal). The constant hazard is this switch rate ``H``, the
    whole-chain analog of the per-state expected sojourn ``1/(1 - a_ii)`` the
    CUSUM detector uses for its ARL0 threshold anchor; it carries no free
    parameter. (The CUSUM threshold's ``ARL0 >= e^h`` bound is the Lorden 1971
    result; that bound is not used here — this detector has no threshold ``h``.)
    Clipped to ``(0, 1]``.
    """
    lt = np.asarray(log_transmat, dtype=np.float64)
    a_ii = np.exp(np.diag(lt))
    pi = stationary_distribution(lt)
    hazard = float(np.sum(pi * (1.0 - a_ii)))
    eps = np.finfo(np.float64).eps
    return min(max(hazard, eps), 1.0)


# --------------------------------------------------------------------------
# Detection-delay layer (mirror of cusum_detection_delays)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class BocpdDetectionDelays:
    """Per-transition BOCPD alarm delays for one filtered segment.

    Estimand (H900 design §7, "alarm delay against the filtered change-
    points"): each filtered transition is assessed in its own local context.
    The detector is anchored at the PRIOR filtered change-point, so its
    established run is exactly the incumbent sojourn; the delay is then the
    number of bars from the transition to the first bar whose posterior
    majority places the current run's start at or after the transition. This
    is the fair, model-light analog of the supervised CUSUM: BOCPD is told
    WHEN each incumbent segment began (bounding its window), but NOT WHAT the
    successor state is, and it additionally REPORTS its own estimate of the
    change location.

    delay_bars
        Observed delay (bars, >= 1) per filtered transition.
    event
        True when the alarm fired within the successor sojourn; False when
        right-censored at the sojourn end.
    from_state / to_state
        Transition labels (same as the CUSUM detector).
    true_cp_index / detected_cp_index
        Segment-local bar index of the true filtered change-point and of
        BOCPD's own MAP changepoint estimate at the alarm (``-1`` when
        censored) — "when the change happened" per the operator request.
    hazard
        The constant hazard used (repeated per transition so the archived
        latency table is self-describing).
    """

    delay_bars: np.ndarray
    event: np.ndarray
    from_state: np.ndarray
    to_state: np.ndarray
    true_cp_index: np.ndarray
    detected_cp_index: np.ndarray
    hazard: np.ndarray


def bocpd_detection_delays(
    z: np.ndarray,
    states: np.ndarray,
    log_transmat: np.ndarray,
    *,
    hazard: float | None = None,
    alarm_prob: float = 0.5,
    mu_0: float = 0.0,
    kappa_0: float = 1.0,
    alpha_0: float = 1.0,
    beta_0: float = 1.0,
    max_run_length: int | None = None,
) -> BocpdDetectionDelays:
    """Measure per-transition-anchored BOCPD alarm delays.

    Fair, model-light analog of
    :func:`skie_universe2.inference.cusum.cusum_detection_delays`. For each
    filtered transition ``i -> j`` at bar ``tau``, BOCPD is run over the local
    window ``[tau_prev, tau_next)`` (previous change-point to next), so the
    detector enters ``tau`` having established the incumbent run — exactly the
    context the supervised CUSUM gets by resetting at ``tau``, but WITHOUT the
    successor identity ``j``. The alarm is the first post-``tau`` bar at which
    the posterior probability that the current run began at or after ``tau``
    reaches ``alarm_prob``; the delay is right-censored at ``tau_next``.

    Parameters
    ----------
    z
        ``(T, D)`` standardized emission vectors of the segment (the same
        observations the causal filter consumed).
    states
        ``(T,)`` causal filtered state sequence of the segment.
    log_transmat
        ``(N, N)`` fitted log transition matrix (source of the anchored
        hazard; see :func:`anchored_hazard`).
    hazard
        Override the anchored hazard. ``None`` derives it from
        ``log_transmat``.
    alarm_prob
        Posterior-probability threshold for declaring the change detected.
        Default ``0.5`` is the Bayes-optimal decision boundary under 0-1 loss
        (posterior majority) — a decision rule, not a tuned parameter.
    mu_0, kappa_0, alpha_0, beta_0
        NIG prior hyperparameters (see :func:`run_length_posterior`).
    max_run_length
        Optional run-length truncation forwarded to
        :func:`run_length_posterior` (per-transition windows are short, so
        this is a safety cap only).
    """
    if not (0.0 < alarm_prob < 1.0):
        raise ValueError(f"alarm_prob must be in (0, 1); got {alarm_prob}.")
    arr = np.asarray(z, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, np.newaxis]
    s = np.asarray(states)
    if arr.ndim != 2 or s.ndim != 1 or arr.shape[0] != s.size:  # noqa: PLR2004 — rank/align check
        raise ValueError("z must be (T, D) aligned with states (T,).")

    h = anchored_hazard(log_transmat) if hazard is None else float(hazard)

    taus = np.flatnonzero(s[1:] != s[:-1]) + 1
    t_len = s.size

    if taus.size == 0:
        empty_i = np.empty(0, dtype=np.int64)
        return BocpdDetectionDelays(
            delay_bars=empty_i,
            event=np.empty(0, dtype=bool),
            from_state=empty_i.copy(),
            to_state=empty_i.copy(),
            true_cp_index=empty_i.copy(),
            detected_cp_index=empty_i.copy(),
            hazard=np.empty(0, dtype=np.float64),
        )

    delays: list[int] = []
    events: list[bool] = []
    froms: list[int] = []
    tos: list[int] = []
    true_cp: list[int] = []
    det_cp: list[int] = []

    for k, tau in enumerate(taus):
        i = int(s[tau - 1])
        j = int(s[tau])
        tau_prev = int(taus[k - 1]) if k > 0 else 0
        tau_next = int(taus[k + 1]) if k + 1 < taus.size else t_len
        local = arr[tau_prev:tau_next]
        change_local = int(tau) - tau_prev  # local index of the true change

        rl = run_length_posterior(
            local,
            h,
            mu_0=mu_0,
            kappa_0=kappa_0,
            alpha_0=alpha_0,
            beta_0=beta_0,
            max_run_length=max_run_length,
        )

        alarm_delay = None
        detected = -1
        for tl in range(change_local, local.shape[0]):
            post = rl[tl]
            # P(current run started at or after the true change) = mass on
            # run lengths r with implied start (tl - r + 1) >= change_local,
            # i.e. r <= tl - change_local + 1.
            r_thresh = tl - change_local + 1
            p_changed = float(post[: r_thresh + 1].sum())
            if p_changed >= alarm_prob:
                alarm_delay = tl - change_local + 1
                map_r = int(post.argmax())
                detected = max(0, tau_prev + (tl - map_r + 1))
                break

        if alarm_delay is None:
            delays.append(tau_next - int(tau))  # censored at successor sojourn end
            events.append(False)
            detected = -1
        else:
            delays.append(int(alarm_delay))
            events.append(True)
        froms.append(i)
        tos.append(j)
        true_cp.append(int(tau))
        det_cp.append(int(detected))

    return BocpdDetectionDelays(
        delay_bars=np.asarray(delays, dtype=np.int64),
        event=np.asarray(events, dtype=bool),
        from_state=np.asarray(froms, dtype=np.int64),
        to_state=np.asarray(tos, dtype=np.int64),
        true_cp_index=np.asarray(true_cp, dtype=np.int64),
        detected_cp_index=np.asarray(det_cp, dtype=np.int64),
        hazard=np.full(len(delays), h, dtype=np.float64),
    )
