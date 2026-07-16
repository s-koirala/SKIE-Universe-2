"""Reference smoke expert — a trivial causal-momentum rule (ADR-0005 Layer 1).

Not an admission candidate: this is the pipeline **smoke-test expert** that
exercises the shadow-ledger backfill driver end-to-end (the plan's M2) without
the baggage of the demoted `meta_shift` prototype (whose premise H001 archived
null) or its magic numbers. It conforms to the :class:`~skie_universe2.experts.base.Expert`
contract and is strictly causal (passes :func:`assert_prefix_invariant`): the
direction at bar ``t`` is the sign of the trailing ``lookback``-bar log return,
using data ≤ ``t`` only; strength is a constant. Stateless — :meth:`fit` is a
no-op.
"""

from __future__ import annotations

import numpy as np

from skie_universe2.experts.base import BarWindow, SignalSeries

# Reference-expert lookback; a plumbing default for the smoke test, not a
# data-selected analysis parameter (this expert produces no evidence).
_REF_LOOKBACK = 3  # justify: smoke-test plumbing constant, not an admission parameter
_REF_STRENGTH = 0.5  # justify: constant smoke-test strength; no calibration claim


class CausalMomentumExpert:
    """Sign of the trailing ``lookback``-bar close-to-close log return (causal)."""

    def __init__(self, lookback: int = _REF_LOOKBACK, version: str = "1.0.0") -> None:
        if lookback < 1:
            raise ValueError(f"lookback must be >= 1, got {lookback}")
        self._lookback = lookback
        self._version = version

    @property
    def expert_id(self) -> str:
        return f"ref_causal_mom_l{self._lookback}@{self._version}"

    def fit(self, train: BarWindow) -> None:  # stateless
        return None

    def signal(self, bars: BarWindow) -> SignalSeries:
        close = np.asarray(bars.close, dtype=np.float64)
        n = close.size
        direction = np.zeros(n, dtype=np.int8)
        if n > self._lookback:
            # trailing log return over [t-lookback, t], defined for t >= lookback
            trailing = np.log(close[self._lookback :] / close[: n - self._lookback])
            direction[self._lookback :] = np.sign(trailing).astype(np.int8)
        strength = np.full(n, _REF_STRENGTH, dtype=np.float64)
        return SignalSeries(direction=direction, strength=strength)
