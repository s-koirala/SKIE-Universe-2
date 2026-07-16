"""Expert-interface contract for the shadow-ledger backfill (ADR-0005 Layer 1).

Resolves open decision OD-1 of the shadow-ledger backfill plan
([docs/research_notes/shadow_ledger_backfill_plan_2026-07-16.md]). An **expert**
is a pluggable Layer-1 signal producer: given a bar window it emits a per-bar
signal (direction + calibrated strength) computable at bar ``t`` **from data ≤ t
only** (ADR-0005 Layer 1: signal only — no sizing, no fills). The backfill driver
maps the signal through the position policy (Layer 2) and the Tier-0 execution
helper (Layer 3) into the counterfactual returns the ledger stores.

The contract is a :class:`~typing.Protocol` (structural typing) so existing
producers (`meta_shift_signal`, a future ORB expert) satisfy it without a shared
base class, and it is ``runtime_checkable`` for driver-side validation.

**Causality is the load-bearing precondition** (ADR-0008 D1). Every conforming
expert MUST satisfy prefix-invariance: ``signal(bars[:t]).direction ==
signal(bars).direction[:t]`` (and likewise for strength) — the emitted signal at
bar ``t`` is invariant to bars ``> t``. :func:`assert_prefix_invariant` is the
canary the driver runs before any expert's returns enter evidence, the supervised
analogue of the shadow-ledger writer's look-ahead obligation.

Trained experts express per-rolling-window refit through :meth:`Expert.fit`
(fit trained components on the training slice, moments/params from train only);
stateless rule experts implement it as a no-op. The driver calls ``fit`` on each
rolling-origin training window (purged) and ``signal`` on the eval span, exactly
as the H900/H001 drivers refit-then-filter.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

# Signal direction encoding (Layer 1): sign of the position the expert wants.
FLAT = np.int8(0)
LONG = np.int8(1)
SHORT = np.int8(-1)
_VALID_DIRECTIONS = frozenset({-1, 0, 1})


@dataclass(frozen=True)
class BarWindow:
    """Chronological OHLCV bar window with timestamps (the expert's input).

    All arrays share length and order; ``ts`` are the bar-label timestamps
    (UTC, the ``ts_event`` convention of the substrate). A bar labelled ``t``
    covers ``[t, t+bar)`` and is observable at its close — no look-ahead in the
    indexing (the shadow-ledger / emission convention).
    """

    ts: list[datetime]
    open: NDArray[np.float64]
    high: NDArray[np.float64]
    low: NDArray[np.float64]
    close: NDArray[np.float64]
    volume: NDArray[np.float64]

    def __post_init__(self) -> None:
        n = len(self.ts)
        for name in ("open", "high", "low", "close", "volume"):
            arr = np.asarray(getattr(self, name), dtype=np.float64)
            object.__setattr__(self, name, arr)
            if arr.shape != (n,):
                raise ValueError(f"{name} shape {arr.shape} != (len(ts)={n},)")

    def __len__(self) -> int:
        return len(self.ts)

    def prefix(self, k: int) -> BarWindow:
        """The first ``k`` bars — used by the causality canary."""
        return BarWindow(
            ts=self.ts[:k],
            open=self.open[:k],
            high=self.high[:k],
            low=self.low[:k],
            close=self.close[:k],
            volume=self.volume[:k],
        )


@dataclass(frozen=True)
class SignalSeries:
    """Per-bar Layer-1 signal: direction ∈ {-1,0,1} and strength ∈ [0,1].

    ``direction`` is the signed position intent at each bar close; ``strength``
    is a calibrated confidence the position policy (Layer 2) scales by. Both are
    same-length as the input window and strictly causal.
    """

    direction: NDArray[np.int8]
    strength: NDArray[np.float64]

    def __post_init__(self) -> None:
        raw = np.asarray(self.direction, dtype=np.float64)  # validate before int8 cast
        # Integer-valued in {-1,0,1}: a fractional intent (e.g. 0.9) that would
        # silently truncate to 0 under int8 casting is rejected (CODE-1-2).
        if raw.size and not np.all(np.isin(raw, (-1.0, 0.0, 1.0))):
            raise ValueError("direction values must be integer-valued in {-1, 0, 1}")
        d = raw.astype(np.int8)
        s = np.asarray(self.strength, dtype=np.float64)
        object.__setattr__(self, "direction", d)
        object.__setattr__(self, "strength", s)
        if d.shape != s.shape:
            raise ValueError(f"direction {d.shape} and strength {s.shape} shape mismatch")
        # Strength may be NaN (warm-up / undetermined bar) but not +/-inf, and any
        # non-NaN value must lie in [0, 1] (CODE-1-3: inf previously slipped through).
        non_nan = s[~np.isnan(s)]
        if non_nan.size and (
            not np.all(np.isfinite(non_nan)) or non_nan.min() < 0.0 or non_nan.max() > 1.0
        ):
            raise ValueError("strength must be NaN (warm-up) or finite in [0, 1]")

    def __len__(self) -> int:
        return len(self.direction)


@runtime_checkable
class Expert(Protocol):
    """Pluggable Layer-1 signal producer for the shadow-ledger backfill.

    Conformance requires: a versioned :attr:`expert_id` (``{name}@{version}``,
    version bump = new ledger identity per ADR-0003 D3); a :meth:`fit` refit hook
    (no-op if stateless); and a strictly causal :meth:`signal` satisfying
    prefix-invariance (checked by :func:`assert_prefix_invariant`).
    """

    @property
    def expert_id(self) -> str:
        """Versioned ``{name}@{version}`` identity (must contain ``@``)."""
        ...

    def fit(self, train: BarWindow) -> None:
        """Refit trained components on the TRAINING slice only (no-op if stateless)."""
        ...

    def signal(self, bars: BarWindow) -> SignalSeries:
        """Per-bar causal (direction, strength); data ≤ t only."""
        ...


def assert_valid_expert_id(expert_id: str) -> None:
    """Enforce the ``{name}@{version}`` ledger-identity contract (ADR-0003 D3).

    A version bump is a NEW ledger identity, so the id must contain exactly one
    ``@`` with a non-empty name and version. Called by the PIT-canary gate so the
    check that guards ledger entry also guards identity well-formedness (CODE-1-1).
    """
    parts = expert_id.split("@")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        raise ValueError(
            f"expert_id must be '{{name}}@{{version}}' with non-empty name and "
            f"version; got {expert_id!r}"
        )


# Default causality-canary cut grid density: a leak whose source and target bars
# both lie inside the prefix at a single cut escapes; a dense interior grid of
# cuts catches any leak for which some grid cut separates its source and target
# (REPRODUCIBILITY-1-1). 16 interior cuts balances coverage against N re-signals.
_DEFAULT_CANARY_CUTS = 16  # justify: canary grid density, not an analysis parameter


def assert_prefix_invariant(
    expert: Expert,
    bars: BarWindow,
    *,
    cuts: list[int] | None = None,
) -> None:
    """Signal-layer PIT canary (ADR-0008 D1): assert ``signal`` is prefix-invariant.

    For each cut ``c``, compares ``expert.signal(bars.prefix(c))`` against
    ``expert.signal(bars)[:c]`` on both direction and strength. A mismatch means
    the signal at some bar ``< c`` depends on a bar ``≥ c`` — a look-ahead leak.
    Also validates :attr:`Expert.expert_id`. Raises ``AssertionError`` on any leak.

    **Multiple cuts are load-bearing.** A single cut only catches leaks whose
    forward reach crosses that one boundary; a data-dependent leak where BOTH the
    source and target bars lie inside the prefix escapes. This sweeps a grid so a
    leak is caught whenever some grid cut separates its source and target bars.
    ``cuts=None`` uses ``_DEFAULT_CANARY_CUTS`` evenly-spaced interior cuts; pass an
    explicit list for a denser/targeted sweep.

    The expert must already be ``fit`` (on a training slice disjoint from and prior
    to ``bars``) if it has trained components — this checks the ``signal`` map's
    causality, not the train/eval split (the driver enforces purge/embargo).
    """
    assert_valid_expert_id(expert.expert_id)
    n = len(bars)
    if cuts is None:
        grid = np.linspace(1, n - 1, num=min(n - 1, _DEFAULT_CANARY_CUTS), dtype=int)
        cuts = sorted({int(c) for c in grid})
    full = expert.signal(bars)
    for cut in cuts:
        if not 0 < cut < n:
            raise ValueError(f"cut must be inside the window; got {cut} for len {n}")
        pref = expert.signal(bars.prefix(cut))
        if not np.array_equal(pref.direction, full.direction[:cut]):
            raise AssertionError(
                f"PIT canary FAILED for {expert.expert_id}: direction differs before "
                f"cut={cut} — signal at some bar < cut depends on a bar ≥ cut (look-ahead)."
            )
        if not np.array_equal(pref.strength, full.strength[:cut], equal_nan=True):
            raise AssertionError(
                f"PIT canary FAILED for {expert.expert_id}: strength differs before "
                f"cut={cut} — look-ahead leak in the calibrated strength."
            )
