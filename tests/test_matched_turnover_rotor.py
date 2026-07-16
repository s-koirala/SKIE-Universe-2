"""Unit tests for the ADR-0007 matched-turnover random-rotor benchmark.

Covers the three required properties:

(a) an expert whose entries are effectively random ⇒ percentile ≈ 0.5, p ≈ 0.5;
(b) an expert with a genuine positive edge ⇒ high percentile, small p;
(c) the matched-turnover invariant ⇒ every rotor enters exactly the expert's
    entered-session count.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.inference.matched_turnover_rotor import (
    DEFAULT_REPORT_QUANTILES,
    draw_matched_rotor_entries,
    matched_turnover_rotor,
)

N_ROTORS = 2000  # Monte-Carlo resolution for the null; p-value resolution 1/(N+1).


# ── (a) signal-free expert ⇒ percentile ≈ 0.5, p ≈ 0.5 ─────────────────


def test_random_direction_expert_is_indistinguishable_from_rotor_null() -> None:
    # Expert enters many sessions but its DIRECTION is a coin flip on symmetric
    # magnitudes ⇒ its mean is just one draw from the same null the rotor spans.
    rng = np.random.default_rng(20260716)
    n_entered = 400
    magnitudes = rng.lognormal(mean=-3.0, sigma=0.5, size=n_entered)  # positive scales
    expert_signs = rng.integers(0, 2, size=n_entered) * 2 - 1
    gross = expert_signs * magnitudes  # random-direction realized returns
    mask = np.ones(n_entered, dtype=bool)

    result = matched_turnover_rotor(gross, mask, n_rotors=N_ROTORS, rng=rng)

    # A signal-free expert sits near the middle of the coin-flip rotor null.
    assert 0.3 < result.expert_percentile < 0.7
    assert 0.3 < result.p_value < 0.7


def test_random_direction_stays_central_across_seeds() -> None:
    # Aggregate over seeds: mean percentile of a signal-free expert ≈ 0.5.
    percentiles = []
    for seed in range(30):
        rng = np.random.default_rng(seed)
        n_entered = 200
        magnitudes = rng.lognormal(mean=-3.0, sigma=0.5, size=n_entered)
        gross = (rng.integers(0, 2, size=n_entered) * 2 - 1) * magnitudes
        mask = np.ones(n_entered, dtype=bool)
        res = matched_turnover_rotor(gross, mask, n_rotors=500, rng=rng)
        percentiles.append(res.expert_percentile)
    assert abs(float(np.mean(percentiles)) - 0.5) < 0.1


# ── (b) genuine positive edge ⇒ high percentile, small p ───────────────


def test_genuine_edge_expert_beats_rotor_null() -> None:
    # Expert always takes the correct (long) direction on positive moves ⇒ every
    # entered gross return is positive, so its mean sits far above the mean-zero
    # coin-flip rotor null.
    rng = np.random.default_rng(11)
    n_entered = 300
    gross = rng.lognormal(mean=-3.0, sigma=0.5, size=n_entered)  # all positive
    mask = np.ones(n_entered, dtype=bool)

    result = matched_turnover_rotor(gross, mask, n_rotors=N_ROTORS, rng=rng)

    assert result.expert_percentile > 0.95
    assert result.p_value < 0.05
    # Smallest attainable p-value at this resolution (no rotor reaches the edge).
    assert result.p_value == pytest.approx(1.0 / (N_ROTORS + 1))


def test_negative_edge_expert_scores_low_percentile() -> None:
    # Systematically wrong direction ⇒ mean far below the null ⇒ percentile ≈ 0,
    # p ≈ 1 (a rotor almost always beats it).
    rng = np.random.default_rng(7)
    n_entered = 300
    gross = -rng.lognormal(mean=-3.0, sigma=0.5, size=n_entered)  # all negative
    mask = np.ones(n_entered, dtype=bool)

    result = matched_turnover_rotor(gross, mask, n_rotors=N_ROTORS, rng=rng)

    assert result.expert_percentile < 0.05
    assert result.p_value > 0.95


# ── (c) matched-turnover invariant ─────────────────────────────────────


def test_rotor_entry_count_matches_expert_entry_count_direction_mode() -> None:
    rng = np.random.default_rng(3)
    n_sessions = 500
    gross = rng.standard_normal(n_sessions) * 0.01
    mask = np.zeros(n_sessions, dtype=bool)
    entered = rng.choice(n_sessions, size=37, replace=False)
    mask[entered] = True

    result = matched_turnover_rotor(gross, mask, n_rotors=100, rng=rng)

    assert result.entry_count == int(mask.sum()) == 37
    assert result.n_sessions == n_sessions


def test_timing_rotor_entries_are_matched_and_distinct() -> None:
    # Every timing rotor draws EXACTLY entry_count distinct session indices from
    # the universe — the direct matched-turnover invariant on the draw itself.
    rng = np.random.default_rng(99)
    n_sessions, entry_count, n_rotors = 250, 40, 300
    entries = draw_matched_rotor_entries(n_sessions, entry_count, n_rotors, rng=rng)

    assert entries.shape == (n_rotors, entry_count)
    assert entries.min() >= 0 and entries.max() < n_sessions
    for row in entries:
        assert np.unique(row).size == entry_count  # distinct ⇒ no double-entry


def test_timing_mode_runs_and_matches_turnover() -> None:
    rng = np.random.default_rng(42)
    n_sessions = 600
    session_return = rng.standard_normal(n_sessions) * 0.01
    mask = np.zeros(n_sessions, dtype=bool)
    entered = rng.choice(n_sessions, size=25, replace=False)
    mask[entered] = True
    # Expert earns +|move| on entered sessions (a perfect-timing-and-direction toy).
    gross = np.zeros(n_sessions)
    gross[entered] = np.abs(session_return[entered])

    result = matched_turnover_rotor(
        gross,
        mask,
        n_rotors=N_ROTORS,
        rng=rng,
        mode="timing",
        session_return=session_return,
    )

    assert result.mode == "timing"
    assert result.entry_count == 25
    # Perfect selection over the whole universe beats matched-turnover randoms.
    assert result.expert_percentile > 0.95
    assert result.p_value < 0.05


# ── p-value / percentile mechanics and validation ──────────────────────


def test_pvalue_formula_and_distribution_summary() -> None:
    rng = np.random.default_rng(2024)
    n_entered = 150
    gross = rng.lognormal(mean=-3.0, sigma=0.5, size=n_entered)
    mask = np.ones(n_entered, dtype=bool)

    result = matched_turnover_rotor(gross, mask, n_rotors=1000, rng=rng)

    dist = result.rotor_distribution
    assert dist.n_rotors == 1000
    assert dist.quantile_levels == DEFAULT_REPORT_QUANTILES
    assert len(dist.quantile_values) == len(DEFAULT_REPORT_QUANTILES)
    # Quantiles are monotone non-decreasing in the level.
    assert list(dist.quantile_values) == sorted(dist.quantile_values)
    # Coin-flip rotor null is centered near zero.
    assert abs(dist.mean) < dist.std
    # p-value bounds: (1 + r)/(1 + B) with 0 <= r <= B.
    assert 1.0 / (1000 + 1) <= result.p_value <= 1.0
    assert 0.0 <= result.expert_percentile <= 1.0


def test_pvalue_is_reproducible_under_same_seed() -> None:
    gross = np.random.default_rng(0).lognormal(-3.0, 0.5, size=100)
    mask = np.ones(100, dtype=bool)
    r1 = matched_turnover_rotor(gross, mask, n_rotors=500, rng=np.random.default_rng(5))
    r2 = matched_turnover_rotor(gross, mask, n_rotors=500, rng=np.random.default_rng(5))
    assert r1.p_value == r2.p_value
    assert r1.expert_percentile == r2.expert_percentile
    assert r1.rotor_distribution.quantile_values == r2.rotor_distribution.quantile_values


def test_shape_mismatch_raises() -> None:
    rng = np.random.default_rng(1)
    with pytest.raises(ValueError, match="entered_mask shape"):
        matched_turnover_rotor(np.zeros(10), np.ones(9, dtype=bool), n_rotors=10, rng=rng)


def test_empty_entry_set_raises() -> None:
    rng = np.random.default_rng(1)
    with pytest.raises(ValueError, match="at least one entered session"):
        matched_turnover_rotor(np.zeros(10), np.zeros(10, dtype=bool), n_rotors=10, rng=rng)


def test_timing_without_session_return_raises() -> None:
    rng = np.random.default_rng(1)
    mask = np.ones(10, dtype=bool)
    with pytest.raises(ValueError, match="requires session_return"):
        matched_turnover_rotor(np.zeros(10), mask, n_rotors=10, rng=rng, mode="timing")


def test_nonpositive_n_rotors_raises() -> None:
    rng = np.random.default_rng(1)
    mask = np.ones(10, dtype=bool)
    with pytest.raises(ValueError, match="n_rotors must be >= 1"):
        matched_turnover_rotor(np.zeros(10), mask, n_rotors=0, rng=rng)


def test_draw_entries_rejects_undersized_universe() -> None:
    rng = np.random.default_rng(1)
    with pytest.raises(ValueError, match="must be >="):
        draw_matched_rotor_entries(5, 10, 3, rng=rng)
