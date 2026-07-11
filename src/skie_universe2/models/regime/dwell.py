"""Sojourn (dwell) spell extraction from causal filtered state sequences.

H900 design.md §2/§8: the unit of dwell analysis is a sojourn spell of
the causal filtered state sequence (argmax of the forward-filtered
posterior at each bar; never smoothed states). Censoring rules:

- The LAST spell of a window is in progress at the window edge —
  right-censored (design §8: "right-censoring at window edges for
  spells in progress").
- The FIRST spell of a window began before the window (its start is
  unobserved => left-censored). Kaplan-Meier handles right censoring
  only, so first spells are flagged and excluded from estimation by
  the caller; including their observed part as if complete would bias
  the median down, and treating them as right-censored would misstate
  the risk set (Klein & Moeschberger 2003, *Survival Analysis*, §3.4
  on truncation vs censoring).
- Session-boundary rule (design §2): a spell continuing across the
  daily maintenance break counts as ONE spell (primary). The
  registered sensitivity variant truncates spells at session
  boundaries: the fragment ending at a session change is
  right-censored; the fragment resuming next session starts a new
  observation.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SpellSet:
    """Extracted sojourn spells (parallel arrays).

    duration_bars
        Observed spell length in 5-minute bars (>= 1).
    event
        True when the spell's natural end (a state transition) was
        observed; False when right-censored (window edge or, in the
        session-truncated variant, a session boundary).
    left_censored
        True for the first spell of the window (start unobserved);
        excluded from KM estimation by callers.
    state
        Filtered state label of the spell.
    start_index
        Bar index (within the supplied sequence) of the spell start.
    """

    duration_bars: np.ndarray
    event: np.ndarray
    left_censored: np.ndarray
    state: np.ndarray
    start_index: np.ndarray

    def usable(self) -> SpellSet:
        """Spells eligible for KM estimation (drop left-censored)."""
        keep = ~self.left_censored
        return SpellSet(
            duration_bars=self.duration_bars[keep],
            event=self.event[keep],
            left_censored=self.left_censored[keep],
            state=self.state[keep],
            start_index=self.start_index[keep],
        )


def extract_spells(
    states: np.ndarray,
    *,
    session_ids: np.ndarray | None = None,
    truncate_at_session: bool = False,
) -> SpellSet:
    """Run-length-encode a filtered state sequence into sojourn spells.

    Parameters
    ----------
    states
        (T,) integer filtered state sequence for one window.
    session_ids
        (T,) session identifiers (e.g. CME session-date ordinals).
        Required when ``truncate_at_session`` is True.
    truncate_at_session
        False (primary): spells continue across session boundaries.
        True (sensitivity): spells are cut at session changes; the
        ending fragment is right-censored.
    """
    s = np.asarray(states)
    if s.ndim != 1:
        raise ValueError(f"states must be 1-D; got shape {s.shape!r}.")
    t_len = s.size
    if t_len == 0:
        empty_i = np.empty(0, dtype=np.int64)
        empty_b = np.empty(0, dtype=bool)
        return SpellSet(empty_i, empty_b, empty_b, empty_i, empty_i)
    if truncate_at_session:
        if session_ids is None:
            raise ValueError("session_ids required when truncate_at_session=True.")
        sess = np.asarray(session_ids)
        if sess.shape != s.shape:
            raise ValueError("session_ids must align with states.")

    # Break points: state change, plus session change in the truncated
    # variant.
    change = s[1:] != s[:-1]
    if truncate_at_session:
        assert session_ids is not None
        sess = np.asarray(session_ids)
        boundary = sess[1:] != sess[:-1]
        cut = change | boundary
    else:
        boundary = np.zeros(t_len - 1, dtype=bool)
        cut = change
    starts = np.concatenate([[0], np.flatnonzero(cut) + 1])
    ends = np.concatenate([np.flatnonzero(cut), [t_len - 1]])  # inclusive

    durations = ends - starts + 1
    n = starts.size
    event = np.empty(n, dtype=bool)
    for k in range(n):
        if ends[k] == t_len - 1:
            # In progress at the window edge.
            event[k] = False
        elif truncate_at_session and boundary[ends[k]] and not change[ends[k]]:
            # Cut purely by a session boundary (same state continues):
            # natural end not observed.
            event[k] = False
        else:
            event[k] = True

    left = np.zeros(n, dtype=bool)
    left[0] = True  # first spell of the window: start unobserved.

    return SpellSet(
        duration_bars=durations.astype(np.int64),
        event=event,
        left_censored=left,
        state=s[starts].astype(np.int64),
        start_index=starts.astype(np.int64),
    )


def filtered_state_path(filtered_posteriors: np.ndarray) -> np.ndarray:
    """Per-bar MAP state from causal filtered posteriors (argmax rows).

    This is a per-bar functional of the CAUSAL filter output — distinct
    from full-sequence Viterbi decoding, which is banned for evidence
    generation (no-look-ahead rule; 1.0 toolkit contract).
    """
    p = np.asarray(filtered_posteriors, dtype=np.float64)
    if p.ndim != 2:  # noqa: PLR2004 — array-rank check
        raise ValueError(f"filtered posteriors must be (T, N); got {p.shape!r}.")
    return np.argmax(p, axis=1).astype(np.int64)
