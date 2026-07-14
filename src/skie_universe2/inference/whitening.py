"""AR(1) prewhitening for the H900 BOCPD sensitivity detector.

Registered follow-up ``P1-2.0-H900-BOCPD-WHITENED`` (H900 report §9; step-2
audit findings QUANT-1-5 / QUANT-2-2). The step-2 BOCPD sensitivity ran the
Adams & MacKay (2007) NIG-iid predictive directly on the standardized emission
vector, whose ``log_rvol_5m_24h`` dimension is autocorrelated *by construction*
— it is (the log of) a 288-bar overlapping rolling sum of squared returns, so
consecutive 5-minute bars share ~287/288 of their terms and the lag-1
autocorrelation is ~287/288 ≈ 0.997 (near unit root). The iid-within-run
assumption is therefore violated, which the step-2 report flagged as biasing
L_detect by an unverified net direction.

This module supplies the classic remedy: **prewhiten** the emission with a
per-dimension AR(1) innovation filter, then run the *unchanged* BOCPD detector
on the (approximately white) innovations, so the NIG-iid predictive is
correctly specified. A genuine regime change — a shift in the emission level —
survives whitening as a large innovation and remains detectable; only the
nuisance serial correlation is removed. This is the standard prewhitened /
residual control-chart construction for autocorrelated monitoring.

The AR(1) coefficient is estimated from **within-run** pairs only (consecutive
bars in the same filtered state), so it captures the incumbent-run serial
dependence the detector's predictive must match, not the between-run level
shifts it must detect. For ``log_rvol`` the estimate reproduces the structural
value (~0.997) — it is fixed by the feature definition, not fit to the dwell
outcome, so it introduces no circularity with the L_detect / verdict estimand.

References
----------
- Box, G. E. P. & Jenkins, G. M. 1976. *Time Series Analysis: Forecasting and
  Control*. Holden-Day (prewhitening).
- Alwan, L. C. & Roberts, H. V. 1988. "Time-Series Modeling for Statistical
  Process Control". *J. Bus. Econ. Stat.* 6(1):87-95.
  https://doi.org/10.1080/07350015.1988.10509640
- Runger, G. C. & Willemain, T. R. 1995. "Model-based and Model-free Control of
  Autocorrelated Processes". *J. Qual. Technol.* 27(4):283-292.
  https://doi.org/10.1080/00224065.1995.11979608
"""

from __future__ import annotations

import numpy as np

__all__ = ["ar1_within_run", "whiten_ar1"]

# Boundary clip: an exact unit root makes the innovation renormalization
# 1/sqrt(1 - phi^2) singular. 0.9999 caps it at ~70x while preserving the
# near-unit-root whitening for log_rvol. Structural, not tuned.
_PHI_CLIP = 1.0 - 1e-4


def ar1_within_run(z: np.ndarray, states: np.ndarray) -> np.ndarray:
    """Per-dimension within-run AR(1) coefficient of an emission segment.

    Estimated by pooled least squares over consecutive-bar pairs that lie in
    the same filtered state (``states[t] == states[t-1]``) — the incumbent-run
    serial dependence, excluding the between-run change bars the detector must
    flag. Returns a ``(D,)`` array clipped to ``(-_PHI_CLIP, _PHI_CLIP)``.

    Parameters
    ----------
    z
        ``(T, D)`` standardized emission vectors of the segment (``(T,)`` is
        treated as ``D = 1``).
    states
        ``(T,)`` causal filtered state sequence of the segment.

    Returns
    -------
    np.ndarray
        ``(D,)`` per-dimension within-run AR(1) coefficients, clipped to
        ``(-_PHI_CLIP, _PHI_CLIP)``; zeros where no within-run lag pair exists.
    """
    arr = np.asarray(z, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, np.newaxis]
    s = np.asarray(states)
    if arr.ndim != 2 or s.ndim != 1 or arr.shape[0] != s.size:  # noqa: PLR2004 — rank/align
        raise ValueError("z must be (T, D) aligned with states (T,).")
    d = arr.shape[1]
    if arr.shape[0] < 2:  # noqa: PLR2004 — need a lagged pair
        return np.zeros(d, dtype=np.float64)

    # Demean each run (contiguous same-state segment) before forming lag pairs,
    # so the state-level means the detector must DETECT do not inflate the
    # serial-dependence coefficient the detector's predictive must MATCH.
    bounds = np.concatenate(([0], np.flatnonzero(s[1:] != s[:-1]) + 1, [s.size]))
    lags: list[np.ndarray] = []
    curs: list[np.ndarray] = []
    for lo, hi in zip(bounds[:-1], bounds[1:], strict=True):  # equal length by construction
        seg = arr[lo:hi]
        if seg.shape[0] < 2:  # noqa: PLR2004 — need a lagged pair within the run
            continue
        seg = seg - seg.mean(axis=0)
        lags.append(seg[:-1])
        curs.append(seg[1:])
    if not lags:
        return np.zeros(d, dtype=np.float64)
    lag = np.concatenate(lags)
    cur = np.concatenate(curs)
    num = (lag * cur).sum(axis=0)
    den = (lag * lag).sum(axis=0)
    with np.errstate(divide="ignore", invalid="ignore"):
        # np.where already selects 0.0 wherever den == 0; the 1e-300 floor only
        # keeps the masked-out branch from a divide-by-zero warning (its value is
        # discarded by np.where), so it is a numerical guard, not a tuned value.
        phi = np.where(den > 0.0, num / np.maximum(den, 1e-300), 0.0)
    return np.clip(phi, -_PHI_CLIP, _PHI_CLIP)


def whiten_ar1(z: np.ndarray, phi: np.ndarray) -> np.ndarray:
    """AR(1) prewhitening of an emission segment.

    Innovation filter per dimension: ``w_t = (z_t - phi_d z_{t-1}) /
    sqrt(1 - phi_d^2)``, with ``w_0 = z_0``. The ``1/sqrt(1 - phi^2)`` factor
    renormalizes the innovation to the marginal variance of a unit-variance
    AR(1), so the whitened series is ~unit-variance white and the BOCPD NIG
    unit-scale prior stays appropriate. A level shift of magnitude ``delta`` in
    ``z`` maps to an innovation of ~``delta / sqrt(1 - phi^2)`` — undamped and
    amplified — so genuine regime changes remain (indeed become more) detectable
    while the incumbent-run serial correlation is removed.

    Parameters
    ----------
    z
        ``(T, D)`` standardized emission vectors (``(T,)`` treated as ``D = 1``).
    phi
        ``(D,)`` per-dimension AR(1) coefficients (see :func:`ar1_within_run`).

    Returns
    -------
    np.ndarray
        ``(T, D)`` whitened innovations; row 0 is passed through unchanged
        (``w_0 = z_0``), rows ``1..T-1`` follow the innovation filter (W1).
    """
    arr = np.asarray(z, dtype=np.float64)
    if arr.ndim == 1:
        arr = arr[:, np.newaxis]
    p = np.clip(np.asarray(phi, dtype=np.float64).ravel(), -_PHI_CLIP, _PHI_CLIP)
    if arr.ndim != 2 or p.size != arr.shape[1]:  # noqa: PLR2004 — rank/align
        raise ValueError("phi must be a length-D vector aligned with z's columns.")
    if arr.shape[0] == 0:
        return arr.copy()
    scale = np.sqrt(1.0 - p**2)
    w = arr.copy()
    w[1:] = (arr[1:] - p * arr[:-1]) / scale
    return w
