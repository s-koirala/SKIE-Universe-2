"""Variance-ratio trend/range state covariate S_vr (H001 §3 comparison covariate).

The project-standard ``variance_ratio_state`` conditioning covariate
([config/conditioning_covariates.yaml]; Lo & MacKinlay 1988) as a causal,
per-bar trend/range classifier used as a CONTROL in the H001 conditioning set
``Z = {S_hmm, S_vr}``.

Per bar ``t`` the per-period variance ratio over the trailing ``window`` log
returns is ``VR(q) = Var_window(q-period returns) / (q · Var_window(1-period
returns))`` ([Lo & MacKinlay 1988](https://doi.org/10.1093/rfs/1.1.41)):
``VR > 1`` ⇒ positive serial correlation (trend), ``VR < 1`` ⇒ negative serial
correlation (range/mean-reversion). Strictly causal (data ≤ t; trailing windows,
no centering).

Instantiation note (run-time deviation, logged in the H001 run report): the
frozen H001 design §3 adopts the *project-standard* ``variance_ratio_state`` by
reference, but that registry entry does not numerically pin the VR window/lag.
The two parameters are instantiated here to repo-traceable scales — ``window =
RVOL_WINDOW_BARS`` (288, the H900 realized-vol / feature-lookback scale) and
``q = 2`` (the canonical minimal first-order variance ratio) — not tuned to the
H001 outcome. The classification (trend vs range) is robust to the exact
normalization constant.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from skie_universe2.features.regime_emissions import RVOL_WINDOW_BARS

# S_vr instantiation parameters (see module note; not H001-tuned).
VR_WINDOW_BARS = RVOL_WINDOW_BARS  # justify: H900 realized-vol / feature-lookback scale (288)
VR_LAG_Q = 2  # justify: canonical minimal (first-order) Lo-MacKinlay variance ratio


class VarianceRatioState:
    """Trend/range codes for S_vr."""

    RANGE = 0
    TREND = 1
    UNDETERMINED = -1


def _rolling_sum(a: NDArray[np.float64], window: int) -> NDArray[np.float64]:
    """Trailing rolling sum via cumulative sums; leading ``window-1`` are NaN."""
    n = a.size
    out = np.full(n, np.nan, dtype=np.float64)
    if n < window:
        return out
    cs = np.concatenate([[0.0], np.cumsum(a)])
    out[window - 1 :] = cs[window:] - cs[: n - window + 1]
    return out


def _rolling_sample_var(a: NDArray[np.float64], window: int) -> NDArray[np.float64]:
    """Trailing rolling sample variance (ddof=1) via cumulative sums.

    Leading ``window-1`` entries are NaN. Assumes *a* is finite over any full
    window (callers segment the series so no gap/NaN spans a window).
    """
    n = a.size
    out = np.full(n, np.nan, dtype=np.float64)
    if n < window or window < 2:
        return out
    cs = np.concatenate([[0.0], np.cumsum(a)])
    css = np.concatenate([[0.0], np.cumsum(a * a)])
    s = cs[window:] - cs[: n - window + 1]
    ss = css[window:] - css[: n - window + 1]
    mean = s / window
    out[window - 1 :] = (ss - window * mean * mean) / (window - 1)
    return out


def rolling_variance_ratio(
    log_returns: NDArray[np.float64],
    *,
    window: int = VR_WINDOW_BARS,
    q: int = VR_LAG_Q,
) -> NDArray[np.float64]:
    """Causal per-period Lo-MacKinlay variance ratio over a trailing window.

    Parameters
    ----------
    log_returns : 1-D float array
        Contiguous per-bar log returns (caller segments at data gaps so no gap
        spans a window).
    window : int
        Trailing window length in bars (``>= q + 1``).
    q : int
        Aggregation lag (``>= 2``).

    Returns
    -------
    NDArray[np.float64]
        ``VR(q)`` at each bar; NaN for the leading ``window + q - 2`` warm-up
        bars and where the 1-period variance is zero.
    """
    if q < 2:
        raise ValueError(f"q must be >= 2, got {q}")
    if window < q + 1:
        raise ValueError(f"window must be >= q + 1, got window={window}, q={q}")
    r = np.asarray(log_returns, dtype=np.float64)
    if r.ndim != 1:
        raise ValueError(f"log_returns must be 1-D, got {r.ndim}-D")
    n = r.size
    out = np.full(n, np.nan, dtype=np.float64)
    if n < window + q - 1:
        return out

    var1 = _rolling_sample_var(r, window)
    # q-period overlapping returns p[i] = r[i] + ... + r[i-q+1]; valid i >= q-1.
    p = _rolling_sum(r, q)
    p_valid = p[q - 1 :]  # drop the leading NaNs so cumsum stays finite
    var_q_shifted = _rolling_sample_var(p_valid, window)
    var_q = np.full(n, np.nan, dtype=np.float64)
    var_q[q - 1 :] = var_q_shifted

    with np.errstate(invalid="ignore", divide="ignore"):
        vr = var_q / (q * var1)
    vr = np.where(np.isfinite(var1) & (var1 > 0.0), vr, np.nan)
    out[:] = vr
    out[: window + q - 2] = np.nan
    return out


def variance_ratio_state(
    log_returns: NDArray[np.float64],
    *,
    window: int = VR_WINDOW_BARS,
    q: int = VR_LAG_Q,
) -> NDArray[np.int64]:
    """Classify each bar TREND (VR>1) / RANGE (VR<1) / UNDETERMINED (warm-up).

    Contiguous input required (segment at data gaps). VR exactly 1 → RANGE.
    """
    vr = rolling_variance_ratio(log_returns, window=window, q=q)
    out = np.full(vr.shape, VarianceRatioState.UNDETERMINED, dtype=np.int64)
    valid = np.isfinite(vr)
    out[valid] = np.where(vr[valid] > 1.0, VarianceRatioState.TREND, VarianceRatioState.RANGE)
    return out
