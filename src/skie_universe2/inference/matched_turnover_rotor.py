"""Matched-turnover random-rotor benchmark (ADR-0007 Decision 4; non-waivable).

The matched-turnover random rotor is ladder benchmark 5 of the ADR-0007
confirmation tier and is declared **non-waivable** there (Decision 4): an
allocator or expert edge claim must beat *random entries at matched turnover*,
otherwise the "edge" is a turnover / exposure artifact rather than selection
skill. This module is the reference estimator for that control at the
single-expert per-session activity level.

Motivating structure (ADR-0007 §Context; ADR-0008 §Decision 2 bar-level costs)
------------------------------------------------------------------------------

An expert such as the H101 first-hour opening-range-breakout (ORB) trades at
most once per **session**: one entry, held to close. Its edge is the mean
per-session realized gross return over the sessions it *entered*. The only
thing under the expert's control that the rotor removes is the **entry
signal** — which session to enter (timing) and/or which direction to take
(sign). Everything else — the set of tradeable sessions, the number of
sessions traded, the holding convention, and the per-session return magnitudes
available in the market — is held fixed. The rotor therefore isolates the
signal: if the expert cannot beat coin-flip entries that churn at the *same*
per-session activity, its gross edge is not evidence of selection skill.

The matched-turnover contract (what is held fixed vs randomized)
----------------------------------------------------------------

Held FIXED (matched between expert and every rotor):

- **Turnover / activity.** Every rotor enters exactly ``entered_mask.sum()``
  sessions — the same count the expert traded. Exposure per session and the
  hold-to-close convention are identical, so transaction-cost drag and
  gross-exposure are matched by construction (ADR-0008 Decision 2: costs are a
  bar-level log drag, so equal turnover ⇒ equal cost structure).
- **Return substrate.** Rotors earn returns from the *same* per-session return
  series the expert traded against — either the expert's own realized-magnitude
  series (direction mode) or a supplied universe-wide per-session return series
  (timing mode). No rotor can access a return the expert could not have.

RANDOMIZED (the signal, and only the signal):

- **Direction** (both modes): each entered session gets an independent
  fair-coin long/short sign, so the rotor's directional edge is null in
  expectation.
- **Timing** (``mode="timing"`` only): the ``k`` entered sessions are drawn
  uniformly without replacement from the universe of ``n_sessions``, so *which*
  sessions are traded carries no information.

Two matched-turnover modes (ADR-0007 Decision 2 "same switching frequency ...
uniformly random ... choice", specialized to per-session experts)
-----------------------------------------------------------------

- ``mode="direction"`` (default; requires only the expert's own series).
  Rotors enter the **same set** of sessions the expert entered and randomize
  only the **sign**, earning ``sign * |gross_return|`` per entered session.
  This is the tightest control: session set, count and magnitudes are held
  bit-identical to the expert; only the direction call is replaced by a coin.
  Tests whether the expert's *direction selection* beats chance.
- ``mode="timing"`` (requires ``session_return``, the universe-wide per-session
  long-return). Rotors enter the **same count** ``k`` of sessions, drawn at
  random from all ``n_sessions``, with random sign. Tests whether the expert's
  *joint timing-and-direction selection* beats chance at matched activity.

Inference
---------

Each rotor's statistic is its mean per-session return over its ``k`` entered
sessions — the same estimator applied to the expert (mean gross return over
entered sessions). Against the empirical rotor null the one-sided p-value is

    p = (1 + #{rotor_mean >= expert_mean}) / (1 + n_rotors)

the Davison & Hinkley (1997) Monte-Carlo convention (the ``+1`` counts the
observed configuration, so ``p`` is never zero and stays valid at finite
``n_rotors``); the alternative is "the expert's mean exceeds matched-turnover
random entry". The expert's percentile in the rotor distribution is reported
alongside (mid-rank, so exact ties split evenly).

References
----------

- Decision record: [docs/decisions/ADR-0007-two-tier-discovery-pipeline.md]
  (Decision 2 ladder item 5, Decision 4 non-waivable), amended by ADR-0013 but
  the rotor is retained non-waivable.
- [docs/decisions/ADR-0008-integrity-non-negotiables.md] Decision 2 (bar-level
  cost application — the reason turnover must be matched, not merely bounded).
- Davison, A. C. & Hinkley, D. V. (1997). *Bootstrap Methods and their
  Application*, CUP, §4.2 (the ``(1 + r) / (1 + B)`` Monte-Carlo p-value).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray

# Reporting quantile levels for the rotor-mean summary. These are descriptive
# summary points (a 5-number-style spread of the null distribution), NOT tunable
# analysis thresholds — no decision is taken on them; the binding statistic is
# the one-sided p-value below. Overridable via the `report_quantiles` argument.
DEFAULT_REPORT_QUANTILES: tuple[float, ...] = (0.05, 0.25, 0.50, 0.75, 0.95)

Mode = Literal["direction", "timing"]


@dataclass(frozen=True)
class RotorMeanDistribution:
    """Summary of the matched-turnover random-rotor mean-return null.

    Attributes
    ----------
    mean, std : float
        Mean and (population, ``ddof=0``) standard deviation of the ``n_rotors``
        rotor mean returns.
    quantile_levels : tuple of float
        The probability levels at which the null is summarized.
    quantile_values : tuple of float
        The rotor-mean quantiles at ``quantile_levels`` (same length/order).
    n_rotors : int
        Number of random rotors generated.
    """

    mean: float
    std: float
    quantile_levels: tuple[float, ...]
    quantile_values: tuple[float, ...]
    n_rotors: int


@dataclass(frozen=True)
class MatchedTurnoverRotorResult:
    """Result of the ADR-0007 matched-turnover random-rotor benchmark.

    Attributes
    ----------
    expert_mean : float
        The expert's mean per-session gross return over the sessions it entered.
    entry_count : int
        Sessions the expert entered ``= entered_mask.sum()``; every rotor enters
        exactly this many (the matched-turnover invariant).
    n_sessions : int
        Universe size the rotor draws timing from (``entered_mask.size``). In
        ``mode="direction"`` this is context only — rotors reuse the entered set.
    mode : {"direction", "timing"}
        Which signal component was randomized (see module docstring).
    rotor_distribution : RotorMeanDistribution
        Summary of the rotor mean-return null.
    expert_percentile : float
        Mid-rank fraction of rotor means at or below ``expert_mean`` in ``[0, 1]``
        (exact ties split evenly); ``~0.5`` for a signal-free expert, ``~1`` for a
        strong edge.
    p_value : float
        One-sided ``(1 + #{rotor_mean >= expert_mean}) / (1 + n_rotors)``; small
        ⇒ the expert beats matched-turnover random entry.
    """

    expert_mean: float
    entry_count: int
    n_sessions: int
    mode: Mode
    rotor_distribution: RotorMeanDistribution
    expert_percentile: float
    p_value: float


def draw_matched_rotor_entries(
    n_sessions: int,
    entry_count: int,
    n_rotors: int,
    *,
    rng: np.random.Generator,
) -> NDArray[np.int64]:
    """Draw the entered-session indices for ``n_rotors`` timing-matched rotors.

    Each rotor draws ``entry_count`` distinct session indices uniformly without
    replacement from ``range(n_sessions)`` — the timing-randomization that holds
    the number of entered sessions (turnover) fixed while making *which* sessions
    are entered signal-free.

    Parameters
    ----------
    n_sessions : int
        Universe size to draw from (``>= entry_count``).
    entry_count : int
        Sessions each rotor enters (the matched-turnover count, ``>= 1``).
    n_rotors : int
        Number of rotors (``>= 1``).
    rng : numpy.random.Generator
        Seeded RNG (``numpy.random.default_rng``).

    Returns
    -------
    NDArray[np.int64]
        Shape ``(n_rotors, entry_count)``; row ``j`` holds the distinct entered
        session indices of rotor ``j``. Every row has exactly ``entry_count``
        unique indices — the matched-turnover invariant.
    """
    if entry_count < 1:
        raise ValueError(f"entry_count must be >= 1, got {entry_count}")
    if n_rotors < 1:
        raise ValueError(f"n_rotors must be >= 1, got {n_rotors}")
    if n_sessions < entry_count:
        raise ValueError(
            f"n_sessions ({n_sessions}) must be >= entry_count ({entry_count}) "
            "to draw distinct entries without replacement"
        )
    out = np.empty((n_rotors, entry_count), dtype=np.int64)
    for j in range(n_rotors):
        out[j] = rng.choice(n_sessions, size=entry_count, replace=False)
    return out


def _fair_coin_signs(shape: tuple[int, ...], rng: np.random.Generator) -> NDArray[np.float64]:
    """Independent fair-coin signs in ``{-1.0, +1.0}`` of the given shape."""
    return (2 * rng.integers(0, 2, size=shape) - 1).astype(np.float64)


def matched_turnover_rotor(
    session_gross_returns: NDArray[np.float64],
    entered_mask: NDArray[np.bool_],
    *,
    n_rotors: int,
    rng: np.random.Generator,
    mode: Mode = "direction",
    session_return: NDArray[np.float64] | None = None,
    report_quantiles: tuple[float, ...] = DEFAULT_REPORT_QUANTILES,
) -> MatchedTurnoverRotorResult:
    """Benchmark an expert's per-session edge against matched-turnover random rotors.

    See the module docstring for the matched-turnover contract (what is held
    fixed vs randomized) and the ADR-0007 grounding. The expert statistic is the
    mean of ``session_gross_returns`` over the sessions marked in
    ``entered_mask``; every rotor enters the same number of sessions and earns
    from the same return substrate, randomizing only the entry signal.

    Parameters
    ----------
    session_gross_returns : 1-D float array
        The expert's realized per-session gross return, aligned to the session
        axis, ``0`` (or arbitrary) on sessions it did not enter — only entries
        selected by *entered_mask* are read. In ``mode="direction"`` the rotor
        magnitudes are ``|session_gross_returns[entered]|``.
    entered_mask : 1-D bool array
        Same length as *session_gross_returns*; ``True`` where the expert
        entered. Must mark at least one session.
    n_rotors : int
        Number of random rotors (``>= 1``). The p-value resolution is
        ``1 / (n_rotors + 1)``.
    rng : numpy.random.Generator
        Seeded RNG (``numpy.random.default_rng``); the sole randomness source.
    mode : {"direction", "timing"}, default "direction"
        ``"direction"`` — rotors reuse the expert's entered session set and
        randomize only the long/short sign (magnitudes held identical).
        ``"timing"`` — rotors draw the same *count* of sessions at random from
        the universe (requires *session_return*) and randomize sign, so both
        which sessions and which direction are signal-free.
    session_return : 1-D float array, optional
        Universe-wide per-session long-return (the direction-agnostic move a
        long would earn each session). Required and used only in
        ``mode="timing"``; must be the same length as *session_gross_returns*.
    report_quantiles : tuple of float, default :data:`DEFAULT_REPORT_QUANTILES`
        Probability levels summarizing the rotor-mean null (descriptive only).

    Returns
    -------
    MatchedTurnoverRotorResult
        Frozen result: expert mean, matched entry count, rotor-mean-null summary,
        the expert's mid-rank percentile, and the one-sided p-value.

    Raises
    ------
    ValueError
        On shape mismatch, empty entry set, ``n_rotors < 1``, or
        ``mode="timing"`` without *session_return*.
    """
    gross = np.asarray(session_gross_returns, dtype=np.float64)
    mask = np.asarray(entered_mask, dtype=bool)
    if gross.ndim != 1:
        raise ValueError(f"session_gross_returns must be 1-D, got {gross.ndim}-D")
    if mask.shape != gross.shape:
        raise ValueError(
            f"entered_mask shape {mask.shape} != session_gross_returns shape {gross.shape}"
        )
    if n_rotors < 1:
        raise ValueError(f"n_rotors must be >= 1, got {n_rotors}")

    n_sessions = gross.size
    entered_idx = np.flatnonzero(mask)
    entry_count = int(entered_idx.size)
    if entry_count < 1:
        raise ValueError("entered_mask must mark at least one entered session")

    expert_mean = float(gross[entered_idx].mean())

    if mode == "direction":
        magnitudes = np.abs(gross[entered_idx])  # (entry_count,)
        signs = _fair_coin_signs((n_rotors, entry_count), rng)  # (n_rotors, entry_count)
        rotor_means = (signs * magnitudes).mean(axis=1)
    elif mode == "timing":
        if session_return is None:
            raise ValueError("mode='timing' requires session_return (universe per-session return)")
        underlying = np.asarray(session_return, dtype=np.float64)
        if underlying.shape != gross.shape:
            raise ValueError(
                f"session_return shape {underlying.shape} != "
                f"session_gross_returns shape {gross.shape}"
            )
        entries = draw_matched_rotor_entries(n_sessions, entry_count, n_rotors, rng=rng)
        signs = _fair_coin_signs((n_rotors, entry_count), rng)
        rotor_means = (signs * underlying[entries]).mean(axis=1)
    else:  # pragma: no cover - Literal guard
        raise ValueError(f"mode must be 'direction' or 'timing', got {mode!r}")

    n_ge = int(np.count_nonzero(rotor_means >= expert_mean))
    p_value = (1 + n_ge) / (1 + n_rotors)
    # Mid-rank percentile: strictly-below mass + half the tie mass.
    below = float(np.count_nonzero(rotor_means < expert_mean))
    ties = float(np.count_nonzero(rotor_means == expert_mean))
    expert_percentile = (below + 0.5 * ties) / n_rotors

    levels = tuple(float(q) for q in report_quantiles)
    q_values = tuple(float(v) for v in np.quantile(rotor_means, levels))
    distribution = RotorMeanDistribution(
        mean=float(rotor_means.mean()),
        std=float(rotor_means.std()),
        quantile_levels=levels,
        quantile_values=q_values,
        n_rotors=n_rotors,
    )
    return MatchedTurnoverRotorResult(
        expert_mean=expert_mean,
        entry_count=entry_count,
        n_sessions=n_sessions,
        mode=mode,
        rotor_distribution=distribution,
        expert_percentile=expert_percentile,
        p_value=p_value,
    )
