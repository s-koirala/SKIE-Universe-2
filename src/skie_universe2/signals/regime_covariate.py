"""Small-n volatility×trend regime covariate emitter (H001, ADR-0005 Layer 1).

Reference implementation of the H001 frozen design §5 state constructor
([research/01_hypothesis_register/H001/design.md]). This is a **pure
conditioning-covariate emitter** in the sense of ADR-0001 Decision 5
(covariate / allocator-prior-tilt, NEVER a position gate): it outputs a
per-bar categorical regime state only — no direction, strength, or size
(those belonged to the demoted directional prototype
``meta_shift_signal`` / ``meta_shift_policy``, retained only as
exploration-tier smoke-test infrastructure per H001 §7).

The state is built from one trend indicator and one volatility indicator,
each over a small window ``n`` (H001 §3 grid). It is **magic-number-free by
construction** (H001 §5): the volatility sub-state is a training-window
**median split** (a rank statistic, fit on the training slice only — never
the evaluation slice) and the trend sub-state is a **sign statistic**;
neither is a tuned threshold. This is the leakage-safe fit/transform contract
— :meth:`RegimeCovariateEmitter.fit` estimates the split on training data,
:meth:`~RegimeCovariateEmitter.transform` labels any (causal) data using that
frozen split.

State index (ledger-column convention, ADR-0003; ``cov_`` Float64 MAP index):

======  ====================  ===========================
index   state                 (vol, trend)
======  ====================  ===========================
0       CONTRACT_DOWN         (contract, down)
1       CONTRACT_UP           (contract, up)
2       EXPAND_DOWN           (expand, down)
3       EXPAND_UP             (expand, up)
-1      UNDETERMINED          warm-up / degenerate (NaN scalar or zero slope)
======  ====================  ===========================

The reversal/momentum *interpretation* of each state is NOT assumed here; it
is an output of the H001 §4 forward-variance-ratio test (which state predicts
VR<1 vs VR>1). Only the four registered indicator families of each kind
(H001 §3) are dispatched; extension requires a design amendment.

**Warm-up (family-dependent, conservative).** A bar is UNDETERMINED until both
its trend and volatility scalars are finite. That leading region is the max of
the two scalars' first-finite indices and is family-dependent: it is the frozen
design §5 nominal ``max(n_v, n_t) - 1`` for most families, but one bar longer
for families whose scalar consumes an extra bar — ``sma_slope`` (first-difference
of the SMA), ``atr`` (prior-close true-range term), and the log-return vol
families ``rolling_std`` / ``realized_vol`` (``log_returns[0]`` is NaN). This is
strictly conservative relative to §5 (more UNDETERMINED bars, never fewer) and
introduces no look-ahead.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from skie_universe2.signals.indicators import (
    atr,
    ema,
    kama,
    linreg_slope,
    parkinson,
    realized_vol,
    rolling_sma,
    rolling_std,
)


class RegimeState(enum.IntEnum):
    """The four MAP regime states plus the undetermined sentinel.

    The four determined indices are load-bearing: :func:`_states_from_scalars`
    encodes them as ``vol_bit * 2 + trend_bit`` (contract=0/expand=1 ×
    down=0/up=1). ``test_state_index_encoding_is_locked`` asserts this mapping so
    a renumbering here cannot silently desync the emitted covariate column
    (ADR-0003).
    """

    CONTRACT_DOWN = 0
    CONTRACT_UP = 1
    EXPAND_DOWN = 2
    EXPAND_UP = 3
    UNDETERMINED = -1


# Sentinel state index (warm-up / degenerate), derived from the enum so the
# enum is the single source of truth for the encoding.
UNDETERMINED = np.int8(RegimeState.UNDETERMINED)


# Registered indicator families (H001 §3). Each entry maps a family name to a
# callable that returns the per-bar scalar whose sign (trend) or median-split
# (vol) defines the sub-state. All are strictly causal (data ≤ t).
TREND_FAMILIES: tuple[str, ...] = ("sma_slope", "ema", "kama", "linreg_slope")
VOL_FAMILIES: tuple[str, ...] = ("rolling_std", "atr", "parkinson", "realized_vol")


@dataclass(frozen=True)
class OHLCArrays:
    """Column-oriented OHLC bar arrays (all same length, chronological)."""

    open: NDArray[np.float64]
    high: NDArray[np.float64]
    low: NDArray[np.float64]
    close: NDArray[np.float64]

    def __post_init__(self) -> None:
        # Coerce to float64 ndarrays at the boundary so list/Series callers get a
        # clear ValueError rather than an AttributeError, and downstream indicator
        # dtype guarantees hold (frozen dataclass → object.__setattr__).
        for _name in ("open", "high", "low", "close"):
            object.__setattr__(self, _name, np.asarray(getattr(self, _name), dtype=np.float64))
        shapes = {self.open.shape, self.high.shape, self.low.shape, self.close.shape}
        if len(shapes) != 1:
            raise ValueError("open/high/low/close must share shape")
        if self.close.ndim != 1:
            raise ValueError(f"OHLC arrays must be 1-D, got {self.close.ndim}-D")

    def log_returns(self) -> NDArray[np.float64]:
        """Close-to-close log returns, aligned to bars (``r[0] = NaN``)."""
        r = np.full(self.close.shape, np.nan, dtype=np.float64)
        r[1:] = np.log(self.close[1:] / self.close[:-1])
        return r


def _trend_scalar(bars: OHLCArrays, family: str, n: int) -> NDArray[np.float64]:
    """Per-bar trend scalar whose SIGN gives the up/down sub-state (H001 §5)."""
    close = bars.close
    if family == "sma_slope":
        sma = rolling_sma(close, n)
        out = np.full(close.shape, np.nan, dtype=np.float64)
        out[1:] = sma[1:] - sma[:-1]  # first difference of the SMA
        return out
    if family == "ema":
        return close - ema(close, n)  # price-vs-MA (H001 §5)
    if family == "kama":
        return close - kama(close, n)  # price-vs-MA (H001 §5)
    if family == "linreg_slope":
        return linreg_slope(close, n)
    raise ValueError(f"unknown trend family {family!r}; registered: {TREND_FAMILIES}")


def _vol_scalar(bars: OHLCArrays, family: str, n: int) -> NDArray[np.float64]:
    """Per-bar volatility scalar for the contract/expand median split (H001 §5)."""
    if family == "rolling_std":
        return rolling_std(bars.log_returns(), n)  # StdDev of log returns (H001 §3)
    if family == "atr":
        return atr(bars.high, bars.low, bars.close, n)
    if family == "parkinson":
        return parkinson(bars.high, bars.low, n)
    if family == "realized_vol":
        return realized_vol(bars.log_returns(), n)
    raise ValueError(f"unknown vol family {family!r}; registered: {VOL_FAMILIES}")


def _states_from_scalars(
    trend: NDArray[np.float64],
    vol: NDArray[np.float64],
    vol_median: float,
) -> NDArray[np.int8]:
    """Map (trend scalar, vol scalar, fitted median) → state-index array.

    UNDETERMINED where either scalar is NaN (warm-up) or the trend is exactly
    flat (zero slope — a degenerate sign). ``vol < median`` → contract,
    ``vol >= median`` → expand (H001 §5). ``trend > 0`` → up, ``< 0`` → down.
    """
    n = len(trend)
    out = np.full(n, UNDETERMINED, dtype=np.int8)
    valid = np.isfinite(trend) & np.isfinite(vol) & (trend != 0.0)
    vol_bit = (vol[valid] >= vol_median).astype(np.int8)  # 0 contract, 1 expand
    trend_bit = (trend[valid] > 0.0).astype(np.int8)  # 0 down, 1 up
    out[valid] = vol_bit * 2 + trend_bit
    return out


@dataclass
class RegimeCovariateEmitter:
    """Leakage-safe fit/transform emitter for the H001 vol×trend state.

    Parameters
    ----------
    trend_family, vol_family : str
        One registered family each (:data:`TREND_FAMILIES`, :data:`VOL_FAMILIES`).
    n_t, n_v : int
        Trend / volatility window (H001 §3 grid ``{2,3,4,5,8}``).

    The only fitted parameter is ``vol_median_`` — the training-window median
    of the volatility scalar, the contract/expand split point (H001 §5). Trend
    uses a sign statistic and needs no fit.
    """

    trend_family: str
    vol_family: str
    n_t: int
    n_v: int
    vol_median_: float | None = None

    def __post_init__(self) -> None:
        if self.trend_family not in TREND_FAMILIES:
            raise ValueError(
                f"unknown trend family {self.trend_family!r}; registered: {TREND_FAMILIES}"
            )
        if self.vol_family not in VOL_FAMILIES:
            raise ValueError(f"unknown vol family {self.vol_family!r}; registered: {VOL_FAMILIES}")
        if self.n_t < 2 or self.n_v < 2:
            raise ValueError(f"n_t and n_v must be >= 2, got n_t={self.n_t}, n_v={self.n_v}")

    def fit(self, train_bars: OHLCArrays) -> RegimeCovariateEmitter:
        """Estimate the contract/expand split from the TRAINING slice only.

        Stores ``vol_median_`` = median of the finite training volatility
        scalar. No evaluation data may be passed here (H001 §5/§6:
        discretizer moments estimated on the training slice only).
        """
        vol = _vol_scalar(train_bars, self.vol_family, self.n_v)
        finite = vol[np.isfinite(vol)]
        if finite.size == 0:
            raise ValueError(
                "no finite volatility scalar in the training slice — "
                "window longer than the usable sample?"
            )
        self.vol_median_ = float(np.median(finite))
        return self

    def transform(self, bars: OHLCArrays) -> NDArray[np.int8]:
        """Label bars with the per-bar state index using the fitted split.

        Must be called after :meth:`fit`. Fully causal: every scalar at bar
        ``t`` uses only data ≤ ``t``, and the split threshold is the frozen
        training-window median (no evaluation leakage).
        """
        if self.vol_median_ is None:
            raise RuntimeError("call fit(...) before transform(...)")
        trend = _trend_scalar(bars, self.trend_family, self.n_t)
        vol = _vol_scalar(bars, self.vol_family, self.n_v)
        return _states_from_scalars(trend, vol, self.vol_median_)

    def fit_transform(self, train_bars: OHLCArrays) -> NDArray[np.int8]:
        """Convenience: fit on ``train_bars`` then label the same slice.

        In-sample labelling only — for out-of-sample labelling, :meth:`fit`
        on the training slice and :meth:`transform` the test slice separately
        (H001 §6 rolling-origin evaluation).
        """
        return self.fit(train_bars).transform(train_bars)
