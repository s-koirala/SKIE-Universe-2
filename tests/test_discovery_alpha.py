"""Unit tests for the discovery-alpha cost-calibration reference estimator
(discovery_alpha.py).

These tests ARE the reproducible demonstration referenced by the method-freeze
memo ``docs/methodology/discovery_alpha_cost_calibration_2026-07-12.md`` in lieu
of embedded ad-hoc numbers. Coverage maps to the required freeze checklist:

- (a) RD3 base rate: synthetic two-groups DGP with KNOWN pi0 -> the
  Storey-Tibshirani (2003) spline recovers pi0 within tolerance.
- (b) RD4 threshold: ``optimal_threshold`` reproduces the analytic MPRR (2004)
  FD/FN-ratio posterior-null Bayes cutoff on a constructed lfdr vector.
- (c) RD4 bridge: the Sun-Cai (2007) oracle lfdr rule and the Storey (2003)
  q-value procedure agree (rejection counts) on a known Gaussian DGP.
- (d) RD1/RD4 monotonicity: higher lambda -> looser (larger) cutoff and larger
  implied screening FDR.
- (e) RD5 comparator: retain-FWER in a small-N / strong-dependence regime, and a
  preference for FDR in a large-N regime (crossover, not a magic threshold).
- (f) RD5 PRDS/BY: an FDR win sets the PRDS obligation under a defensible PRDS
  argument, else falls back to Benjamini-Yekutieli.

Plus: RD1/RD2 loss-model construction (lambda > 1, RD2 bound + controls
conditional) and the Efron (2008) empirical local-fdr estimator.

All randomness uses a fixed seed.
"""

from __future__ import annotations

import numpy as np
import pytest
from scipy.stats import norm

from skie_universe2.inference import discovery_alpha as da

# Fixed seed for every stochastic path in this module (reproducibility).
SEED = 20260712


# ---------------------------------------------------------------------------
# (a) RD3 — Storey-Tibshirani pi0 recovery on a known two-groups DGP
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("pi0_true", [0.70, 0.80, 0.90, 0.95])
def test_storey_pi0_recovers_known_null_proportion(pi0_true: float) -> None:
    """Storey-Tibshirani (2003) spline recovers the known pi0 within tolerance."""
    rng = np.random.default_rng(SEED)
    # Strong, well-separated alternative so pi0 is identifiable (RD3 benchmark).
    sample = da.synthetic_two_groups(20000, pi0=pi0_true, mu=3.5, rng=rng)
    pi0_hat = da.storey_pi0(sample.pvalues)
    # Storey's spline is slightly conservative (biased up); a modest tolerance.
    assert pi0_hat == pytest.approx(pi0_true, abs=0.05)


def test_storey_pi0_bounds() -> None:
    """pi0 estimate is clamped to (0, 1]."""
    rng = np.random.default_rng(SEED)
    sample = da.synthetic_two_groups(5000, pi0=0.5, mu=4.0, rng=rng)
    pi0_hat = da.storey_pi0(sample.pvalues)
    assert 0.0 < pi0_hat <= 1.0


# ---------------------------------------------------------------------------
# (b) RD4 — MPRR analytic FD/FN-ratio Bayes threshold
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("c_fd", "c_fn"),
    [(1.0, 1.0), (1.0, 3.0), (1.0, 9.0), (2.0, 5.0), (1.0, 0.25)],
)
def test_optimal_threshold_matches_mprr_analytic(c_fd: float, c_fn: float) -> None:
    """optimal_threshold(lambda) == c_FN / (c_FD + c_FN) (Muller et al. 2004)."""
    loss_ratio = c_fn / c_fd  # lambda = L_MD / L_FD
    analytic = c_fn / (c_fd + c_fn)
    assert da.optimal_threshold(loss_ratio) == pytest.approx(analytic, abs=1e-12)
    # Posterior-null ODDS cutoff equals the cost ratio (Harvey 2017 form).
    t = da.optimal_threshold(loss_ratio)
    assert t / (1.0 - t) == pytest.approx(loss_ratio, rel=1e-9)


def test_bayes_rule_selects_below_cutoff() -> None:
    """The Bayes discovery rule admits exactly the lfdr values below t*."""
    lfdr = np.array([0.01, 0.10, 0.30, 0.50, 0.80, 0.99])
    loss_ratio = 3.0  # t* = 0.75
    t = da.optimal_threshold(loss_ratio)
    reject = da.bayes_discovery_rule(lfdr, loss_ratio)
    assert np.array_equal(reject, lfdr < t)
    assert reject.tolist() == [True, True, True, True, False, False]


def test_infinite_loss_ratio_admits_all_capped_edges() -> None:
    """lambda -> inf (backstops fully cap L_FD) drives t* -> 1 (admit all)."""
    lfdr = np.array([0.01, 0.5, 0.999])
    assert da.optimal_threshold(float("inf")) == pytest.approx(1.0, abs=1e-10)
    assert da.bayes_discovery_rule(lfdr, float("inf")).all()


# ---------------------------------------------------------------------------
# (c) RD4 — Sun-Cai oracle lfdr rule vs Storey q-value agreement
# ---------------------------------------------------------------------------


def test_sun_cai_oracle_and_storey_qvalue_agree() -> None:
    """On a known DGP, Sun-Cai oracle lfdr and Storey q-value reject ~ the same set."""
    rng = np.random.default_rng(SEED)
    pi0_true = 0.85
    mu = 3.0
    sample = da.synthetic_two_groups(20000, pi0=pi0_true, mu=mu, rng=rng)
    fdr_level = 0.10  # illustrative-on-synthetic-fixture, not a ledger operating point

    # Oracle lfdr (known mixture) -> Sun-Cai 2007 rule.
    lfdr = da.two_groups_lfdr_gaussian(sample.z, pi0=pi0_true, mu=mu)
    sc = da.sun_cai_oracle_rule(lfdr, fdr_level=fdr_level)

    # Storey 2003 q-values (known pi0) at the same level.
    q = da.storey_qvalues(sample.pvalues, pi0=pi0_true)
    n_q = int(np.sum(q <= fdr_level))

    # The oracle FDR rule and the q-value procedure are two views of the same
    # control; on a well-specified DGP their rejection counts agree closely.
    assert sc.n_reject == pytest.approx(n_q, rel=0.05)
    # And both control FDR at the level.
    assert sc.realized_fdr <= fdr_level + 1e-9


def test_sun_cai_realized_fdr_under_level() -> None:
    """Sun-Cai realized FDR never exceeds the requested level."""
    lfdr = np.array([0.001, 0.02, 0.05, 0.08, 0.20, 0.40, 0.90])
    rule = da.sun_cai_oracle_rule(lfdr, fdr_level=0.10)
    assert rule.realized_fdr <= 0.10 + 1e-12
    assert rule.n_reject >= 1


# ---------------------------------------------------------------------------
# (d) RD1/RD4 — loss-ratio monotonicity (higher lambda -> looser)
# ---------------------------------------------------------------------------


def test_threshold_monotone_in_loss_ratio() -> None:
    """Higher lambda -> strictly larger tolerated posterior-null cutoff."""
    ratios = [0.5, 1.0, 2.0, 5.0, 20.0, 100.0]
    thresholds = [da.optimal_threshold(r) for r in ratios]
    assert all(b > a for a, b in zip(thresholds, thresholds[1:], strict=False))


def test_implied_screening_fdr_monotone_in_loss_ratio() -> None:
    """Higher lambda -> looser cutoff -> larger implied screening FDR."""
    rng = np.random.default_rng(SEED)
    sample = da.synthetic_two_groups(10000, pi0=0.8, mu=3.0, rng=rng)
    lfdr = da.two_groups_lfdr_gaussian(sample.z, pi0=0.8, mu=3.0)
    ratios = [1.0, 2.0, 5.0, 15.0, 50.0]
    fdrs = [da.implied_screening_fdr(lfdr, r) for r in ratios]
    assert all(b >= a - 1e-12 for a, b in zip(fdrs, fdrs[1:], strict=False))
    assert fdrs[-1] > fdrs[0]  # strictly looser at the top


# ---------------------------------------------------------------------------
# RD1/RD2 — loss-model construction, lambda > 1, and the controls conditional
# ---------------------------------------------------------------------------


def _true_edge_returns(rng: np.random.Generator, n: int = 5000) -> np.ndarray:
    """Favourable fat-tailed edge (positive drift, Student-t innovations)."""
    return 0.02 + 0.01 * rng.standard_t(4.0, size=n)


def _false_edge_returns(rng: np.random.Generator, n: int = 5000) -> np.ndarray:
    """Zero/negative-edge draw (no drift, same fat tails)."""
    return -0.001 + 0.01 * rng.standard_t(4.0, size=n)


def test_loss_model_ratio_exceeds_one_with_controls() -> None:
    """With controls in force, L_MD (forgone compounding) >> RD2-bounded L_FD."""
    rng = np.random.default_rng(SEED)
    true_r = _true_edge_returns(rng)
    false_r = _false_edge_returns(rng)
    lm = da.build_loss_model(
        true_r,
        false_r,
        operating_fraction=1.0,
        min_live_fraction=0.5,
        champion_dwell_bars=250.0,
        demotion_latency_bars=20.0,
        backstop_rejection_rate=0.7,
        controls_in_force=True,
    )
    assert lm.l_md > 0.0
    assert lm.l_fd >= 0.0
    assert lm.loss_ratio > 1.0  # lambda estimate > 1 (missed compounding dominates)
    assert da.optimal_threshold(lm.loss_ratio) > 0.5


def test_controls_off_tightens_relative_to_controls_on() -> None:
    """Disabling the RD2 controls raises L_FD, lowering lambda and the cutoff."""
    rng = np.random.default_rng(SEED)
    true_r = _true_edge_returns(rng)
    false_r = _false_edge_returns(rng)
    kwargs = dict(
        operating_fraction=1.0,
        min_live_fraction=0.5,
        champion_dwell_bars=250.0,
        demotion_latency_bars=20.0,
        backstop_rejection_rate=0.7,
    )
    on = da.build_loss_model(true_r, false_r, controls_in_force=True, **kwargs)
    off = da.build_loss_model(true_r, false_r, controls_in_force=False, **kwargs)
    assert off.l_fd >= on.l_fd
    assert off.loss_ratio <= on.loss_ratio
    assert da.optimal_threshold(off.loss_ratio) <= da.optimal_threshold(on.loss_ratio)


# ---------------------------------------------------------------------------
# (e) RD5 — FWER-vs-FDR growth-risk comparator crossover
# ---------------------------------------------------------------------------


def _loss_model_for_comparator() -> da.LossModel:
    rng = np.random.default_rng(SEED)
    return da.build_loss_model(
        _true_edge_returns(rng),
        _false_edge_returns(rng),
        operating_fraction=1.0,
        min_live_fraction=0.5,
        champion_dwell_bars=250.0,
        demotion_latency_bars=20.0,
        backstop_rejection_rate=0.7,
        controls_in_force=True,
    )


def test_comparator_retains_fwer_small_n_strong_dependence() -> None:
    """Small N + strong dependence -> retain-FWER (FWER power high, ruin capped)."""
    lm = _loss_model_for_comparator()
    model = da.TwoGroupsModel(pi0=0.8, mu=3.0)
    decision = da.fwer_vs_fdr_decision(
        model,
        family_size=4,  # the x4 Kelly sweep family at a single allocator config
        loss_model=lm,
        family_alpha=0.05,  # illustrative-on-synthetic-fixture, not a ledger level
        fdr_level=0.10,  # illustrative-on-synthetic-fixture, not a ledger level
        dependence_inflation=4.0,  # strong positive dependence collapses N_eff -> 1
        prds_defensible=True,
    )
    assert decision.criterion == "retain-fwer"
    assert decision.prds_obligation is False
    assert decision.spa_existence_gate_retained is True


def test_comparator_prefers_fdr_large_n() -> None:
    """Large N (independence) -> FWER power collapses -> FDR growth-loss wins."""
    lm = _loss_model_for_comparator()
    model = da.TwoGroupsModel(pi0=0.8, mu=3.0)
    decision = da.fwer_vs_fdr_decision(
        model,
        family_size=2000,
        loss_model=lm,
        family_alpha=0.05,  # illustrative-on-synthetic-fixture, not a ledger level
        fdr_level=0.10,  # illustrative-on-synthetic-fixture, not a ledger level
        dependence_inflation=1.0,  # independence
        prds_defensible=True,
    )
    assert decision.criterion == "bh-prds"
    assert decision.prds_obligation is True


def test_comparator_loss_ratio_monotone_in_n() -> None:
    """FWER/FDR growth-loss ratio increases with N (crossover is monotone)."""
    lm = _loss_model_for_comparator()
    model = da.TwoGroupsModel(pi0=0.8, mu=3.0)
    sizes = [4, 50, 500, 5000]
    ratios = []
    for n in sizes:
        d = da.fwer_vs_fdr_decision(
            model,
            family_size=n,
            loss_model=lm,
            family_alpha=0.05,  # illustrative fixture
            fdr_level=0.10,  # illustrative fixture
            dependence_inflation=1.0,
            prds_defensible=True,
        )
        ratios.append(d.loss_fwer / d.loss_fdr)
    assert all(b > a for a, b in zip(ratios, ratios[1:], strict=False))


# ---------------------------------------------------------------------------
# (e') RD5 — alternative-scale (sigma) faithfulness of the operating chars.
#   Regression guard: the two-groups power must scale the WHOLE quantile shift
#   by sigma, power = sf((Phi^{-1}(1 - level) - mu) / sigma), not just the mean
#   (Genovese & Wasserman 2002; the DGP draws z = mu + sigma * N(0, 1)). Every
#   other fixture uses the sigma = 1 default, so these exercise the general path.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("sigma", [1.0, 1.5, 2.0])
def test_fwer_power_scales_full_shift_by_sigma(sigma: float) -> None:
    """power_fwer == sf((isf(alpha_per) - mu)/sigma) for all sigma (analytic)."""
    lm = _loss_model_for_comparator()
    mu = 3.0
    family_alpha = 0.05  # illustrative fixture
    family_size = 4
    dependence_inflation = 1.0
    model = da.TwoGroupsModel(pi0=0.8, mu=mu, sigma=sigma)
    decision = da.fwer_vs_fdr_decision(
        model,
        family_size=family_size,
        loss_model=lm,
        family_alpha=family_alpha,
        fdr_level=0.10,  # illustrative fixture
        dependence_inflation=dependence_inflation,
        prds_defensible=True,
    )
    n_eff = max(1.0, family_size / dependence_inflation)
    alpha_per = family_alpha / n_eff
    expected = float(norm.sf((norm.isf(alpha_per) - mu) / sigma))
    assert decision.power_fwer == pytest.approx(expected, rel=1e-12)
    # The mis-scaled (mean-only) form must differ off the sigma = 1 default,
    # proving the regression path is actually exercised.
    mis_scaled = float(norm.sf(norm.isf(alpha_per) - mu / sigma))
    if sigma != 1.0:
        assert abs(decision.power_fwer - mis_scaled) > 1e-6


@pytest.mark.parametrize("sigma", [1.5, 2.0])
def test_oracle_fdr_cutoff_realizes_target_and_power_under_scaled_alt(
    sigma: float,
) -> None:
    """MC cross-check: oracle cutoff realizes target FDR and reported power at sigma != 1."""
    rng = np.random.default_rng(SEED)
    pi0 = 0.8
    mu = 3.0
    target_fdr = 0.10  # illustrative fixture
    lm = _loss_model_for_comparator()
    model = da.TwoGroupsModel(pi0=pi0, mu=mu, sigma=sigma)
    decision = da.fwer_vs_fdr_decision(
        model,
        family_size=2000,
        loss_model=lm,
        family_alpha=0.05,  # illustrative fixture
        fdr_level=target_fdr,
        dependence_inflation=1.0,
        prds_defensible=True,
    )
    c = decision.fdr_cutoff  # oracle one-sided p-value cutoff
    sample = da.synthetic_two_groups(400000, pi0=pi0, mu=mu, sigma=sigma, rng=rng)
    rej = sample.pvalues <= c
    n_rej = int(rej.sum())
    assert n_rej > 0
    realized_fdr = float((rej & ~sample.is_alt).sum()) / n_rej
    realized_power = float((rej & sample.is_alt).sum()) / int(sample.is_alt.sum())
    # Oracle cutoff was solved to hit target_fdr under the scaled alternative.
    assert realized_fdr == pytest.approx(target_fdr, abs=0.01)
    # Reported oracle power matches the realized rejection rate among alternatives.
    assert realized_power == pytest.approx(decision.power_fdr, abs=0.01)


# ---------------------------------------------------------------------------
# (f) RD5 — PRDS obligation vs Benjamini-Yekutieli fallback
# ---------------------------------------------------------------------------


def test_bh_sets_prds_obligation_else_by_fallback() -> None:
    """FDR win + PRDS defensible -> bh-prds obligation; else BY fallback."""
    lm = _loss_model_for_comparator()
    model = da.TwoGroupsModel(pi0=0.8, mu=3.0)
    common = dict(
        family_size=2000,
        loss_model=lm,
        family_alpha=0.05,  # illustrative fixture
        fdr_level=0.10,  # illustrative fixture
        dependence_inflation=1.0,
    )
    bh = da.fwer_vs_fdr_decision(model, prds_defensible=True, **common)
    by = da.fwer_vs_fdr_decision(model, prds_defensible=False, **common)
    assert bh.criterion == "bh-prds" and bh.prds_obligation is True
    assert by.criterion == "benjamini-yekutieli" and by.prds_obligation is False


# ---------------------------------------------------------------------------
# Efron (2008) empirical local-fdr estimator (RD3)
# ---------------------------------------------------------------------------


def test_efron_local_fdr_tracks_oracle() -> None:
    """Efron (2008) Lindsey lfdr correlates with the oracle lfdr on a known DGP."""
    rng = np.random.default_rng(SEED)
    pi0_true = 0.85
    mu = 3.0
    sample = da.synthetic_two_groups(30000, pi0=pi0_true, mu=mu, rng=rng)
    oracle = da.two_groups_lfdr_gaussian(sample.z, pi0=pi0_true, mu=mu)
    est = da.efron_local_fdr(sample.z, pi0=pi0_true)
    # Rank agreement: the empirical estimate orders hypotheses like the oracle.
    corr = float(np.corrcoef(oracle, est)[0, 1])
    assert corr > 0.95
    # Deep-null z (large negative) has lfdr ~ 1 under both.
    deep = da.efron_local_fdr(sample.z, pi0=pi0_true)[np.argmin(sample.z)]
    assert deep > 0.9
