"""Pure indicator functions for the signal layer (ADR-0005 Layer 1).

Stateless, array-in / array-out functions operating on numpy arrays.
No side effects, no state, no position logic.
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray


def rolling_sma(prices: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """Simple moving average with leading NaNs for incomplete windows.

    Parameters
    ----------
    prices : 1-D float array
        Close prices (or any series).
    period : int
        Lookback window (must be >= 1).

    Returns
    -------
    NDArray[np.float64]
        Same length as *prices*; first ``period - 1`` entries are NaN.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    prices = np.asarray(prices, dtype=np.float64)
    if prices.ndim != 1:
        raise ValueError(f"prices must be 1-D, got {prices.ndim}-D")

    out = np.full_like(prices, np.nan)
    if len(prices) < period:
        return out

    # Cumulative-sum trick for O(n) SMA.
    cs = np.cumsum(prices)
    out[period - 1] = cs[period - 1] / period
    if len(prices) > period:
        out[period:] = (cs[period:] - cs[:-period]) / period
    return out


def rolling_std(prices: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """Rolling sample standard deviation (ddof=1) with leading NaNs.

    Parameters
    ----------
    prices : 1-D float array
        Close prices (or any series).
    period : int
        Lookback window (must be >= 2 for ddof=1).

    Returns
    -------
    NDArray[np.float64]
        Same length as *prices*; first ``period - 1`` entries are NaN.
    """
    if period < 2:
        raise ValueError(f"period must be >= 2 for ddof=1, got {period}")
    prices = np.asarray(prices, dtype=np.float64)
    if prices.ndim != 1:
        raise ValueError(f"prices must be 1-D, got {prices.ndim}-D")

    n = len(prices)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < period:
        return out

    # Stride-trick view → vectorised std across windows.
    shape = (n - period + 1, period)
    strides = (prices.strides[0], prices.strides[0])
    windows = np.lib.stride_tricks.as_strided(prices, shape=shape, strides=strides)
    out[period - 1 :] = np.std(windows, axis=1, ddof=1)
    return out


def _rolling_windows(x: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """Read-only (n-period+1, period) stride view of trailing windows."""
    n = len(x)
    shape = (n - period + 1, period)
    strides = (x.strides[0], x.strides[0])
    return np.lib.stride_tricks.as_strided(x, shape=shape, strides=strides, writeable=False)


# ── Trend-indicator family (ADR-0005 Layer 1; H001 design §3) ─────────


def ema(prices: NDArray[np.float64], span: int) -> NDArray[np.float64]:
    """Exponential moving average, causal, with leading NaNs.

    Smoothing factor ``alpha = 2 / (span + 1)`` (the standard EMA span
    convention). The recursion is seeded with the SMA of the first
    ``span`` bars at index ``span - 1``; entries ``0 .. span - 2`` are NaN
    (warm-up). Uses only data ≤ t (no look-ahead).

    Parameters
    ----------
    prices : 1-D float array
        Price (or level) series.
    span : int
        EMA span (``>= 1``); ``alpha = 2 / (span + 1)``.

    Returns
    -------
    NDArray[np.float64]
        Same length as *prices*; first ``span - 1`` entries are NaN.
    """
    if span < 1:
        raise ValueError(f"span must be >= 1, got {span}")
    prices = np.asarray(prices, dtype=np.float64)
    if prices.ndim != 1:
        raise ValueError(f"prices must be 1-D, got {prices.ndim}-D")

    n = len(prices)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < span:
        return out

    alpha = 2.0 / (span + 1.0)
    out[span - 1] = float(np.mean(prices[:span]))
    for i in range(span, n):
        out[i] = alpha * prices[i] + (1.0 - alpha) * out[i - 1]
    return out


def kama(
    prices: NDArray[np.float64],
    period: int,
    *,
    fast: int = 2,
    slow: int = 30,
) -> NDArray[np.float64]:
    """Kaufman Adaptive Moving Average, causal, with leading NaNs.

    The efficiency ratio ``ER = |p_t - p_{t-period}| / Σ|Δp|`` over the
    trailing ``period`` bars scales the smoothing constant between a fast
    and slow EMA bound. The recursion is seeded at index ``period - 1``
    with ``p[period - 1]``; entries ``0 .. period - 2`` are NaN (warm-up)
    and index ``period - 1`` is the finite seed. Uses only data ≤ t.

    ``fast=2``/``slow=30`` are Kaufman's canonical smoothing-bound
    constants ([Kaufman 2020, *Trading Systems and Methods*, 6th ed.],
    *practitioner*), carried by citation, not tuned here.

    Parameters
    ----------
    prices : 1-D float array
        Price (or level) series.
    period : int
        Efficiency-ratio lookback (``>= 1``).
    fast, slow : int, keyword-only
        Fast / slow EMA smoothing-period bounds (Kaufman defaults 2 / 30).

    Returns
    -------
    NDArray[np.float64]
        Same length as *prices*; entries ``0 .. period - 2`` are NaN.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    prices = np.asarray(prices, dtype=np.float64)
    if prices.ndim != 1:
        raise ValueError(f"prices must be 1-D, got {prices.ndim}-D")

    n = len(prices)
    out = np.full(n, np.nan, dtype=np.float64)
    if n <= period:
        return out

    fast_sc = 2.0 / (fast + 1.0)
    slow_sc = 2.0 / (slow + 1.0)
    abs_delta = np.abs(np.diff(prices))  # length n-1, index i = |p[i+1]-p[i]|

    out[period - 1] = prices[period - 1]
    for i in range(period, n):
        change = abs(prices[i] - prices[i - period])
        volatility = float(np.sum(abs_delta[i - period : i]))
        er = change / volatility if volatility > 0.0 else 0.0
        sc = (er * (fast_sc - slow_sc) + slow_sc) ** 2
        out[i] = out[i - 1] + sc * (prices[i] - out[i - 1])
    return out


def linreg_slope(prices: NDArray[np.float64], period: int) -> NDArray[np.float64]:
    """Rolling OLS slope of price on bar index over trailing ``period`` bars.

    Regresses the ``period``-bar price window on ``x = 0 .. period-1`` and
    returns the slope (price change per bar). Leading ``period - 1`` entries
    are NaN. Vectorised; uses only data ≤ t.

    Parameters
    ----------
    prices : 1-D float array
        Price (or level) series.
    period : int
        Rolling OLS window (``>= 2``).

    Returns
    -------
    NDArray[np.float64]
        Same length as *prices*; first ``period - 1`` entries are NaN.
    """
    if period < 2:
        raise ValueError(f"period must be >= 2, got {period}")
    prices = np.asarray(prices, dtype=np.float64)
    if prices.ndim != 1:
        raise ValueError(f"prices must be 1-D, got {prices.ndim}-D")

    n = len(prices)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < period:
        return out

    x = np.arange(period, dtype=np.float64)
    x_mean = x.mean()
    x_dev = x - x_mean
    denom = float(np.sum(x_dev**2))  # constant across windows

    windows = _rolling_windows(prices, period)
    y_mean = windows.mean(axis=1, keepdims=True)
    out[period - 1 :] = (windows - y_mean) @ x_dev / denom
    return out


# ── Volatility-indicator family (ADR-0005 Layer 1; H001 design §3) ────


def atr(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    close: NDArray[np.float64],
    period: int,
) -> NDArray[np.float64]:
    """Average true range (simple rolling mean of true range).

    True range ``TR_t = max(high_t - low_t, |high_t - close_{t-1}|,
    |low_t - close_{t-1}|)``; ATR is the rolling mean of TR over ``period``
    bars. ``TR_0`` uses ``high_0 - low_0`` (no prior close). The first
    ``period`` entries are NaN — one extra bar beyond ``period - 1`` is
    consumed because the mean starts at index ``period`` so every averaged
    TR uses a prior close. Uses only data ≤ t.

    Parameters
    ----------
    high, low, close : 1-D float array
        Bar highs, lows, and closes (same length).
    period : int
        Rolling-mean window over true range (``>= 1``).

    Returns
    -------
    NDArray[np.float64]
        Same length as the inputs; first ``period`` entries are NaN.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    high = np.asarray(high, dtype=np.float64)
    low = np.asarray(low, dtype=np.float64)
    close = np.asarray(close, dtype=np.float64)
    if not (high.shape == low.shape == close.shape):
        raise ValueError("high, low, close must share shape")
    if high.ndim != 1:
        raise ValueError(f"inputs must be 1-D, got {high.ndim}-D")

    n = len(high)
    tr = np.empty(n, dtype=np.float64)
    tr[0] = high[0] - low[0]
    prev_close = close[:-1]
    tr[1:] = np.maximum.reduce(
        [
            high[1:] - low[1:],
            np.abs(high[1:] - prev_close),
            np.abs(low[1:] - prev_close),
        ]
    )
    # Rolling mean over `period`, but TR[0] is a partial (no prior close);
    # start the mean at index `period` so every averaged TR uses a prior close.
    out = np.full(n, np.nan, dtype=np.float64)
    if n <= period:
        return out
    windows = _rolling_windows(tr[1:], period)  # TR indices 1..n-1
    out[period:] = windows.mean(axis=1)
    return out


def parkinson(
    high: NDArray[np.float64],
    low: NDArray[np.float64],
    period: int,
) -> NDArray[np.float64]:
    """Parkinson high-low range volatility over ``period`` bars.

    ``σ_P = sqrt( (1 / (4 ln 2)) · mean_period( (ln(high/low))^2 ) )``
    ([Parkinson 1980](https://doi.org/10.1086/296071)). Leading
    ``period - 1`` entries are NaN. Uses only data ≤ t.

    Parameters
    ----------
    high, low : 1-D float array
        Bar highs and lows (same length; strictly positive).
    period : int
        Rolling window (``>= 1``).

    Returns
    -------
    NDArray[np.float64]
        Same length as the inputs; first ``period - 1`` entries are NaN.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    high = np.asarray(high, dtype=np.float64)
    low = np.asarray(low, dtype=np.float64)
    if high.shape != low.shape:
        raise ValueError("high and low must share shape")
    if high.ndim != 1:
        raise ValueError(f"inputs must be 1-D, got {high.ndim}-D")

    n = len(high)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < period:
        return out
    log_hl_sq = np.log(high / low) ** 2
    windows = _rolling_windows(log_hl_sq, period)
    factor = 1.0 / (4.0 * np.log(2.0))
    out[period - 1 :] = np.sqrt(factor * windows.mean(axis=1))
    return out


def realized_vol(
    log_returns: NDArray[np.float64],
    period: int,
) -> NDArray[np.float64]:
    """Realized volatility: sqrt of the rolling sum of squared log returns.

    ``RV_t = sqrt( Σ_{period} r^2 )`` over the trailing ``period`` log
    returns. Leading ``period - 1`` entries are NaN. Uses only data ≤ t.

    Parameters
    ----------
    log_returns : 1-D float array
        Per-bar log returns.
    period : int
        Rolling window (``>= 1``).

    Returns
    -------
    NDArray[np.float64]
        Same length as *log_returns*; first ``period - 1`` entries are NaN.
    """
    if period < 1:
        raise ValueError(f"period must be >= 1, got {period}")
    log_returns = np.asarray(log_returns, dtype=np.float64)
    if log_returns.ndim != 1:
        raise ValueError(f"log_returns must be 1-D, got {log_returns.ndim}-D")

    n = len(log_returns)
    out = np.full(n, np.nan, dtype=np.float64)
    if n < period:
        return out
    windows = _rolling_windows(log_returns**2, period)
    out[period - 1 :] = np.sqrt(windows.sum(axis=1))
    return out
