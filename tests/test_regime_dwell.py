"""Unit tests for sojourn-spell extraction (H900 dwell analysis).

Synthetic state sequences with known sojourns; censoring semantics per
H900 design.md §2/§8 (window-edge right-censoring, first-spell
left-censor flag, session-truncated sensitivity variant).
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.models.regime.dwell import (
    SpellSet,
    extract_spells,
    filtered_state_path,
)


class TestExtractSpellsContinuous:
    def test_known_sojourns(self) -> None:
        # Spells: 0 x3, 1 x2, 0 x4, 2 x1 (last).
        states = np.array([0, 0, 0, 1, 1, 0, 0, 0, 0, 2])
        out = extract_spells(states)
        np.testing.assert_array_equal(out.duration_bars, [3, 2, 4, 1])
        np.testing.assert_array_equal(out.state, [0, 1, 0, 2])
        np.testing.assert_array_equal(out.start_index, [0, 3, 5, 9])
        # Last spell right-censored; interior spells observed.
        np.testing.assert_array_equal(out.event, [True, True, True, False])
        # First spell left-censored (start unobserved at window edge).
        np.testing.assert_array_equal(out.left_censored, [True, False, False, False])

    def test_usable_drops_left_censored_only(self) -> None:
        states = np.array([0, 0, 1, 1, 1, 0])
        usable = extract_spells(states).usable()
        np.testing.assert_array_equal(usable.duration_bars, [3, 1])
        np.testing.assert_array_equal(usable.event, [True, False])

    def test_single_state_sequence_is_one_censored_spell(self) -> None:
        states = np.zeros(7, dtype=np.int64)
        out = extract_spells(states)
        np.testing.assert_array_equal(out.duration_bars, [7])
        np.testing.assert_array_equal(out.event, [False])
        np.testing.assert_array_equal(out.left_censored, [True])
        assert out.usable().duration_bars.size == 0

    def test_session_break_does_not_cut_spell_in_primary_rule(self) -> None:
        # Same state across a session boundary: primary rule (design §2)
        # counts it as ONE spell regardless of session ids.
        states = np.array([0, 0, 0, 0, 1])
        sessions = np.array([1, 1, 2, 2, 2])
        out = extract_spells(states, session_ids=sessions, truncate_at_session=False)
        np.testing.assert_array_equal(out.duration_bars, [4, 1])

    def test_empty_and_validation(self) -> None:
        out = extract_spells(np.array([], dtype=np.int64))
        assert out.duration_bars.size == 0
        with pytest.raises(ValueError, match="1-D"):
            extract_spells(np.zeros((3, 2)))
        with pytest.raises(ValueError, match="session_ids required"):
            extract_spells(np.array([0, 1]), truncate_at_session=True)


class TestExtractSpellsSessionTruncated:
    def test_boundary_cut_is_right_censored(self) -> None:
        # State 0 persists across a session change: the ending fragment
        # is censored, the resuming fragment is a new observation.
        states = np.array([0, 0, 0, 0, 1, 1])
        sessions = np.array([1, 1, 2, 2, 2, 2])
        out = extract_spells(states, session_ids=sessions, truncate_at_session=True)
        np.testing.assert_array_equal(out.duration_bars, [2, 2, 2])
        np.testing.assert_array_equal(out.state, [0, 0, 1])
        # Fragment cut by the boundary (same state continues): censored.
        # Fragment ending in a real transition: event. Last: censored.
        np.testing.assert_array_equal(out.event, [False, True, False])

    def test_transition_exactly_at_boundary_is_event(self) -> None:
        # State changes at the same bar the session changes: the spell's
        # natural end WAS observed (state transition), so event=True.
        states = np.array([0, 0, 1, 1])
        sessions = np.array([1, 1, 2, 2])
        out = extract_spells(states, session_ids=sessions, truncate_at_session=True)
        np.testing.assert_array_equal(out.duration_bars, [2, 2])
        np.testing.assert_array_equal(out.event, [True, False])


class TestFilteredStatePath:
    def test_argmax_of_rows(self) -> None:
        post = np.array([[0.9, 0.1], [0.4, 0.6], [0.55, 0.45]])
        np.testing.assert_array_equal(filtered_state_path(post), [0, 1, 0])

    def test_rejects_non_2d(self) -> None:
        with pytest.raises(ValueError, match=r"\(T, N\)"):
            filtered_state_path(np.zeros(5))


class TestSpellSetInvariants:
    def test_durations_sum_to_sequence_length(self) -> None:
        rng = np.random.default_rng(20260710)
        states = rng.integers(0, 3, size=500)
        out = extract_spells(states)
        assert int(out.duration_bars.sum()) == 500
        assert isinstance(out, SpellSet)

    def test_truncated_variant_durations_also_sum(self) -> None:
        rng = np.random.default_rng(20260711)
        states = rng.integers(0, 2, size=300)
        sessions = np.repeat(np.arange(10), 30)
        out = extract_spells(states, session_ids=sessions, truncate_at_session=True)
        assert int(out.duration_bars.sum()) == 300
