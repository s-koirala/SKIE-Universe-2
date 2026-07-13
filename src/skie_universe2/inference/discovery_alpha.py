"""Discovery-alpha cost calibration — decision-theoretic reference estimator
(method freeze for ``P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE``).

Status (BLOCKING per ADR-0013 Decision 9)
-----------------------------------------

This module is the *frozen reference estimator* that gates ENACTING any
loosened discovery target / criterion / TOST re-weighting for the Kelly-sweep
confirmation family (``config/multipletest_family.yaml`` family
``allocator-confirmation-kelly-sweep``). The METHOD — the asymmetric log-wealth
loss model, the base-rate estimators, the decision-theoretic threshold solver,
and the FWER-vs-FDR growth-risk comparator — is frozen here on synthetic and
representative fixtures. The NUMERIC on-ledger instantiation (the actual
screening alpha LEVEL, ``pi1``, the loss ratio ``lambda``, and the FWER/FDR
criterion decision) is DEFERRED to the post-step-4 shadow-ledger backfill,
because the ADR-0003 ledger is not yet populated. **No discovery target is
enacted by this module.** ``screening_error_rate_target`` stays ``null``,
``correction`` stays ``romano-wolf``, and ``prds_argument_ref`` stays ``null``
in the config until the backfill run instantiates them.

Dependency on Memo 1 (``kelly_growth``) and ADR-0010
----------------------------------------------------

The loss model is expressed in **log-wealth (geometric-growth) units** and
reuses :func:`skie_universe2.inference.kelly_growth.growth_rate` for every
log-wealth quantity — it does NOT re-implement growth. The false-discovery loss
``L_FD`` is *bounded* (RD2) by the downstream ruin controls: (a) Memo-1's
grid-bracketed-below-ruin sizing + ``-inf`` ruin rejection, and (b) the ADR-0010
earn-by-live-tracking ramp (Schuirmann TOST gate + CUSUM demotion at minimum
live size) together with the DSR / PBO / matched-turnover-rotor backstops. The
looser alpha is licensed **only while those controls are in force**; with the
controls disabled (:attr:`LossModel.controls_in_force` ``False``) the bound is
not applied and the model reverts toward a tighter alpha. Memo 2 therefore
formally depends on Memo 1 + ADR-0010.

Derivation map (see the companion memo
``docs/methodology/discovery_alpha_cost_calibration_2026-07-12.md``)
--------------------------------------------------------------------

- **RD1 asymmetric loss.** :func:`build_loss_model` estimates ``L_FD`` (admitting
  a zero/neg-edge allocator sized at the minimum live fraction) and ``L_MD``
  (rejecting a true-edge allocator = forgone compounding over a champion-dwell
  horizon), both in log-wealth units, and returns the loss ratio
  ``lambda = L_MD / L_FD`` as an ESTIMATE (not asserted > 1).
- **RD2 ruin linkage.** ``L_FD`` is bounded as
  ``(min-size exposure) x (demotion latency) x (1 - backstop rejection rate)``;
  the explicit conditional on the controls being in force is carried on the
  returned :class:`LossModel`.
- **RD3 base rate.** :func:`storey_pi0` (Storey & Tibshirani 2003 spline) and
  :func:`efron_local_fdr` (Efron 2008 two-groups local fdr via Lindsey's
  Poisson-spline density) estimate ``pi0`` / ``pi1``; a sensitivity band is the
  caller's responsibility (report multiple lambda in the grid) and the
  circularity break is documented in the memo.
- **RD4 decision-theoretic threshold.** :func:`optimal_threshold` returns the
  Muller-Parmigiani-Robert-Rousseau 2004 posterior-null Bayes cutoff
  ``t* = lambda / (1 + lambda)`` (equivalently, posterior-null ODDS cutoff
  ``= L_MD / L_FD``); :func:`sun_cai_oracle_rule` implements the Sun-Cai 2007
  oracle local-fdr rule (min FNR s.t. FDR <= level); :func:`storey_qvalues`
  is the Storey 2003 q-value bridge.
- **RD5 FWER->FDR decision.** :func:`fwer_vs_fdr_decision` compares the expected
  log-wealth (growth) loss of FWER control vs FDR control as a function of the
  family size ``N`` and returns a criterion in
  ``{"retain-fwer", "bh-prds", "benjamini-yekutieli"}`` plus the PRDS-argument
  obligation flag. The Hansen 2005 SPA existence gate is retained either way,
  and the criterion switch stays inside the Romano-Wolf 2005 / Romano-Shaikh-Wolf
  2008 bootstrap framework (not a machinery replacement).

Zero-magic-number register
--------------------------

Every tunable is a named module constant or a documented function default with a
cited/derived rationale; see the memo appendix. The enacted alpha LEVEL, the
FDR target ``q``, and the family FWER level are REQUIRED parameters with no
numeric default (they are on-ledger OUTPUTS, not constants baked here). Any
synthetic-DGP helper takes a caller-supplied seeded ``numpy`` Generator.

References
----------

- Benjamini, Y. & Hochberg, Y. 1995. "Controlling the False Discovery Rate".
  *J. R. Statist. Soc. B* 57(1): 289-300.
  https://doi.org/10.1111/j.2517-6161.1995.tb02031.x
- Benjamini, Y. & Hochberg, Y. 1997. "Multiple Hypotheses Testing with Weights".
  *Scand. J. Statist.* 24(3): 407-418. https://doi.org/10.1111/1467-9469.00072
- Benjamini, Y. & Yekutieli, D. 2001. "The Control of the FDR under Dependency".
  *Ann. Statist.* 29(4): 1165-1188. https://doi.org/10.1214/aos/1013699998
- Storey, J. D. 2002. "A Direct Approach to False Discovery Rates".
  *J. R. Statist. Soc. B* 64(3): 479-498. https://doi.org/10.1111/1467-9868.00346
- Storey, J. D. 2003. "The Positive FDR: a Bayesian Interpretation and the
  q-value". *Ann. Statist.* 31(6): 2013-2035.
  https://doi.org/10.1214/aos/1074290335
- Storey, J. D. & Tibshirani, R. 2003. "Statistical Significance for Genomewide
  Studies". *PNAS* 100(16): 9440-9445. https://doi.org/10.1073/pnas.1530509100
- Genovese, C. & Wasserman, L. 2002. "Operating Characteristics and Extensions
  of the FDR Procedure". *J. R. Statist. Soc. B* 64(3): 499-517.
  https://doi.org/10.1111/1467-9868.00347
- Sun, W. & Cai, T. T. 2007. "Oracle and Adaptive Compound Decision Rules for
  FDR Control". *JASA* 102(479): 901-912.
  https://doi.org/10.1198/016214507000000545
- Muller, P., Parmigiani, G., Robert, C. & Rousseau, J. 2004. "Optimal Sample
  Size for Multiple Testing". *JASA* 99(468): 990-1001.
  https://doi.org/10.1198/016214504000001646
- Efron, B. 2008. "Microarrays, Empirical Bayes and the Two-Groups Model".
  *Statist. Sci.* 23(1): 1-22. https://doi.org/10.1214/07-STS236
- Harvey, C. R. 2017. "Presidential Address: The Scientific Outlook in Financial
  Economics". *J. Finance* 72(4): 1399-1440. https://doi.org/10.1111/jofi.12530
- Harvey, C. R. & Liu, Y. 2020. "False (and Missed) Discoveries in Financial
  Economics". *J. Finance* 75(5): 2503-2553. https://doi.org/10.1111/jofi.12951
- Hansen, P. R. 2005. "A Test for Superior Predictive Ability". *JBES* 23(4):
  365-380. https://doi.org/10.1198/073500105000000063
- Romano, J. P. & Wolf, M. 2005. "Stepwise Multiple Testing as Formalized Data
  Snooping". *Econometrica* 73(4): 1237-1282.
  https://doi.org/10.1111/j.1468-0262.2005.00615.x
- Romano, J. P., Shaikh, A. M. & Wolf, M. 2008. "Formalized Data Snooping Based
  on Generalized Error Rates". *Econometric Theory* 24(2): 404-447.
  https://doi.org/10.1017/S0266466608080171
- Bailey, D. H. & Lopez de Prado, M. 2014. "The Deflated Sharpe Ratio".
  *J. Portfolio Management* 40(5): 94-107.
  https://doi.org/10.3905/jpm.2014.40.5.094
- Bailey, D. H.; Borwein, J. M.; Lopez de Prado, M. & Zhu, Q. J. 2017 (online
  2016). "The Probability of Backtest Overfitting". *J. Computational Finance*
  20(4): 39-69. https://doi.org/10.21314/JCF.2016.322
- Schuirmann, D. J. 1987. "A Comparison of the Two One-Sided Tests Procedure and
  the Power Approach for Assessing the Equivalence of Average Bioavailability".
  *J. Pharmacokinet. Biopharm.* 15(6): 657-680.
  https://doi.org/10.1007/BF01068419
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import numpy.typing as npt
from scipy.interpolate import BSpline, UnivariateSpline
from scipy.optimize import brentq
from scipy.stats import norm

from skie_universe2.inference.kelly_growth import full_kelly_leverage, growth_rate

__all__ = [
    "LINDSEY_SPLINE_DF",
    "STOREY_LAMBDA_GRID",
    "STOREY_SPLINE_DF",
    "CriterionDecision",
    "LossModel",
    "TwoGroupsModel",
    "bayes_discovery_rule",
    "build_loss_model",
    "efron_local_fdr",
    "fwer_vs_fdr_decision",
    "implied_screening_fdr",
    "optimal_threshold",
    "storey_pi0",
    "storey_qvalues",
    "sun_cai_oracle_rule",
    "synthetic_two_groups",
    "two_groups_lfdr_gaussian",
]


# ---------------------------------------------------------------------------
# Registered defaults (each cited/derived; see memo appendix). The enacted
# alpha LEVEL, FDR target q and family FWER level are NOT here — they are
# required parameters (on-ledger OUTPUTS), never constants.
# ---------------------------------------------------------------------------

# Storey & Tibshirani (2003) default tuning grid for the pi0 smoother.
STOREY_LAMBDA_GRID: np.ndarray = np.arange(0.05, 0.96, 0.05)  # ref: Storey-Tibshirani 2003

# Storey & Tibshirani (2003) smoother spline degree (cubic).
STOREY_SPLINE_DF: int = 3  # ref: Storey-Tibshirani 2003 smooth.spline df=3

# Efron (2008) locfdr default natural-spline degrees of freedom for the
# Lindsey Poisson-spline marginal-density estimate.
LINDSEY_SPLINE_DF: int = 7  # ref: Efron 2008 locfdr natural-spline df=7

_EPS: float = float(np.finfo(np.float64).eps)

# Poisson-IRLS numerical guards (solver controls, NOT statistical parameters).
_IRLS_MAX_STEPS: int = 50  # numerical: IRLS iteration cap; converges far sooner
_IRLS_TOL: float = 1.0e-8  # numerical: coefficient-change convergence tolerance
_IRLS_RIDGE: float = 1.0e-6  # numerical: design-matrix conditioning ridge, not a penalty

# Root-search bracket floor for the oracle FDR p-cutoff (kept strictly inside
# (0, 1) so the Gaussian quantile is finite). Solver guard, not a threshold.
_CUTOFF_BRACKET_FLOOR: float = 1.0e-12

# A degree-3 (cubic) spline needs at least degree + 1 = 4 knots; below this the
# Storey smoother is undefined and the largest-lam plug-in is used instead.
_MIN_SPLINE_KNOTS: int = 4  # numerical: cubic-spline minimum support (degree + 1)


# ---------------------------------------------------------------------------
# Input hygiene
# ---------------------------------------------------------------------------


def _clean_1d(x: npt.ArrayLike, name: str) -> np.ndarray:
    a = np.asarray(x, dtype=np.float64).ravel()
    if a.size == 0:
        raise ValueError(f"{name} is empty.")
    if not np.all(np.isfinite(a)):
        raise ValueError(f"{name} contains non-finite values (NaN or inf).")
    return a


def _clean_pvalues(pvalues: npt.ArrayLike) -> np.ndarray:
    p = _clean_1d(pvalues, "pvalues")
    if np.any(p < 0.0) or np.any(p > 1.0):
        raise ValueError("pvalues must lie in [0, 1].")
    return p


def _clean_lfdr(lfdr: npt.ArrayLike) -> np.ndarray:
    v = _clean_1d(lfdr, "lfdr")
    if np.any(v < 0.0) or np.any(v > 1.0):
        raise ValueError("lfdr (posterior-null probabilities) must lie in [0, 1].")
    return v


# ---------------------------------------------------------------------------
# RD3 — base-rate estimation: Storey-Tibshirani pi0 + Efron two-groups lfdr
# ---------------------------------------------------------------------------


def storey_pi0(
    pvalues: npt.ArrayLike,
    *,
    lambdas: npt.ArrayLike = STOREY_LAMBDA_GRID,
    spline_df: int = STOREY_SPLINE_DF,
) -> float:
    """Storey & Tibshirani (2003) spline estimate of the null proportion ``pi0``.

    For each ``lam`` in ``lambdas`` the raw estimate is
    ``pi0(lam) = #{p_i > lam} / (m (1 - lam))``; a cubic smoothing spline of
    ``pi0(lam)`` against ``lam`` is fitted and evaluated at the largest ``lam``
    (the ``lam -> 1`` limit where nulls dominate), then clamped to ``(0, 1]``.
    ``pi1 = 1 - pi0`` is the base rate of true edges (RD3).

    A single-``lam`` grid falls back to the plain Storey (2002) ratio at that
    ``lam`` (no spline is defined on one point).
    """
    p = _clean_pvalues(pvalues)
    lam = np.asarray(lambdas, dtype=np.float64).ravel()
    if np.any(lam < 0.0) or np.any(lam >= 1.0):
        raise ValueError("lambdas must lie in [0, 1).")
    m = p.size
    pi0_lam = np.array([np.mean(p > lam_i) / (1.0 - lam_i) for lam_i in lam], dtype=np.float64)

    if lam.size < _MIN_SPLINE_KNOTS:
        # Too few knots for a cubic spline; use the largest-lam plug-in.
        pi0_hat = float(pi0_lam[int(np.argmax(lam))])
    else:
        order = np.argsort(lam)
        deg = int(min(spline_df, lam.size - 1))
        spline = UnivariateSpline(lam[order], pi0_lam[order], k=deg, s=float(lam.size))
        pi0_hat = float(spline(float(lam.max())))

    return float(min(max(pi0_hat, 1.0 / m), 1.0))


def two_groups_lfdr_gaussian(
    z: npt.ArrayLike,
    *,
    pi0: float,
    mu: float,
    sigma: float = 1.0,
) -> np.ndarray:
    """Analytic (oracle) two-groups local fdr for a Gaussian mixture (Efron 2008).

    Null density ``f0 = N(0, 1)``, alternative density ``f1 = N(mu, sigma)``,
    marginal ``f = pi0 f0 + (1 - pi0) f1``; the local fdr (posterior-null
    probability) is ``lfdr(z) = pi0 f0(z) / f(z)``. This is the ORACLE lfdr used
    as a benchmark when the mixture is known; :func:`efron_local_fdr` is the
    empirical estimator for unknown mixtures.
    """
    zz = _clean_1d(z, "z")
    if not (0.0 < pi0 <= 1.0):
        raise ValueError("pi0 must lie in (0, 1].")
    if not (sigma > 0.0):
        raise ValueError("sigma must be positive.")
    f0 = norm.pdf(zz)
    f1 = norm.pdf(zz, loc=float(mu), scale=float(sigma))
    f = pi0 * f0 + (1.0 - pi0) * f1
    lfdr = np.where(f > 0.0, pi0 * f0 / f, 1.0)
    return np.clip(lfdr, 0.0, 1.0)


def _poisson_irls(design: np.ndarray, counts: np.ndarray) -> np.ndarray:
    """Ridge-stabilised Poisson IRLS fit of ``log E[counts] = design @ beta``.

    Lindsey's method for a Poisson-spline density (Efron 2008): the histogram
    bin counts are Poisson with log-mean linear in a spline basis. The tiny
    ridge only conditions the normal equations; it is a numerical guard, not a
    statistical penalty.
    """
    x = np.asarray(design, dtype=np.float64)
    y = np.asarray(counts, dtype=np.float64)
    n_features = x.shape[1]
    beta = np.zeros(n_features, dtype=np.float64)
    beta[0] = np.log(max(y.mean(), 1.0))
    ridge = _IRLS_RIDGE * np.eye(n_features)
    for _ in range(_IRLS_MAX_STEPS):
        eta = x @ beta
        mu = np.exp(np.clip(eta, -700.0, 700.0))
        w = mu
        working = eta + (y - mu) / np.maximum(mu, _EPS)
        xtw = x.T * w
        lhs = xtw @ x + ridge
        rhs = xtw @ working
        beta_new = np.linalg.solve(lhs, rhs)
        if np.max(np.abs(beta_new - beta)) < _IRLS_TOL:
            beta = beta_new
            break
        beta = beta_new
    return beta


def efron_local_fdr(
    z: npt.ArrayLike,
    *,
    pi0: float | None = None,
    spline_df: int = LINDSEY_SPLINE_DF,
    n_bins: int | None = None,
) -> np.ndarray:
    """Efron (2008) two-groups local fdr via Lindsey's Poisson-spline density.

    The marginal density ``f(z)`` is estimated by binning ``z`` and fitting a
    Poisson regression of the bin counts on a B-spline basis of the bin centres
    (Lindsey's method). With the theoretical null ``f0 = N(0, 1)`` and a null
    proportion ``pi0`` (estimated via :func:`storey_pi0` on the one-sided
    p-values ``1 - Phi(z)`` when not supplied), the local fdr is
    ``lfdr(z) = pi0 f0(z) / f_hat(z)`` clipped to ``[0, 1]``.

    Parameters
    ----------
    n_bins
        Histogram bin count. Defaults to the Freedman-Diaconis rule (data-driven,
        no magic constant); falls back to ``ceil(sqrt(n))`` if the IQR is zero.
    """
    zz = _clean_1d(z, "z")
    n = zz.size
    if n_bins is None:
        iqr = float(np.subtract(*np.percentile(zz, [75, 25])))
        if iqr > 0.0:
            width = 2.0 * iqr / np.cbrt(n)  # Freedman-Diaconis rule (data-driven)
            span = float(zz.max() - zz.min())
            n_bins = int(max(8, np.ceil(span / width))) if width > 0.0 else int(np.ceil(np.sqrt(n)))
        else:
            n_bins = int(np.ceil(np.sqrt(n)))
    counts, edges = np.histogram(zz, bins=int(n_bins))
    centers = 0.5 * (edges[:-1] + edges[1:])
    binwidth = float(edges[1] - edges[0])

    deg = 3  # cubic B-spline pieces (Efron 2008 natural-spline density basis)
    n_interior = int(max(1, spline_df - deg))
    qs = np.linspace(0.0, 1.0, n_interior + 2)[1:-1]
    interior = np.quantile(centers, qs)
    lo, hi = float(centers.min()), float(centers.max())
    knots = np.concatenate(([lo] * (deg + 1), interior, [hi] * (deg + 1)))
    basis = np.asarray(BSpline.design_matrix(np.clip(centers, lo, hi), knots, deg).todense())
    design = np.column_stack([np.ones(basis.shape[0]), basis])

    beta = _poisson_irls(design, counts.astype(np.float64))
    log_dens = design @ beta
    dens = np.exp(np.clip(log_dens, -700.0, 700.0))
    area = float(np.sum(dens) * binwidth)
    f_hat_centers = dens / area if area > 0.0 else dens

    if pi0 is None:
        pi0 = storey_pi0(1.0 - norm.cdf(zz))
    if not (0.0 < pi0 <= 1.0):
        raise ValueError("pi0 must lie in (0, 1].")
    f0_centers = norm.pdf(centers)
    lfdr_centers = np.clip(pi0 * f0_centers / np.maximum(f_hat_centers, _EPS), 0.0, 1.0)
    return np.clip(np.interp(zz, centers, lfdr_centers), 0.0, 1.0)


# ---------------------------------------------------------------------------
# RD1 / RD2 — asymmetric log-wealth loss with the RD2 ruin bound
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class LossModel:
    """Asymmetric log-wealth loss and the derived loss ratio ``lambda`` (RD1/RD2).

    ``l_md`` is the missed-discovery loss (forgone compounded log-wealth of a
    true-edge allocator over a champion-dwell horizon); ``l_fd`` is the
    false-discovery loss (log-wealth damage of a zero/neg-edge allocator sized at
    the minimum live fraction, RD2-bounded by the demotion latency and the
    backstop rejection rate). ``loss_ratio = l_md / l_fd`` is the estimate of
    ``lambda`` (``+inf`` if the bounded ``l_fd`` is zero). ``controls_in_force``
    records whether the RD2 downstream controls (Memo-1 ruin sizing + ADR-0010
    ramp + DSR/PBO/rotor) were credited when bounding ``l_fd``; when ``False``
    the bound is NOT applied and the ratio reverts toward the tighter regime.
    """

    l_fd: float
    l_md: float
    loss_ratio: float
    controls_in_force: bool
    l_fd_unbounded: float
    backstop_rejection_rate: float
    min_live_fraction: float
    demotion_latency_bars: float
    champion_dwell_bars: float
    notes: str


def build_loss_model(
    true_edge_returns: npt.ArrayLike,
    false_edge_returns: npt.ArrayLike,
    *,
    operating_fraction: float,
    min_live_fraction: float,
    champion_dwell_bars: float,
    demotion_latency_bars: float,
    backstop_rejection_rate: float,
    controls_in_force: bool = True,
    b_star_true: float | None = None,
    weights_true: npt.ArrayLike | None = None,
    weights_false: npt.ArrayLike | None = None,
) -> LossModel:
    """Estimate the asymmetric log-wealth loss model (RD1) with the RD2 bound.

    ``L_MD`` (missed discovery = rejecting a true edge) is the forgone compounded
    log-wealth over the champion-dwell horizon:
    ``L_MD = champion_dwell_bars * g_true`` where ``g_true =
    growth_rate(true_edge_returns, operating_fraction * b*_true)`` reuses Memo 1.

    ``L_FD`` (false discovery = admitting a zero/neg-edge allocator) is bounded
    per RD2 by ``(min-size exposure) x (demotion latency) x (1 - backstop
    rejection rate)``. The min-size exposure enters through sizing the false edge
    at ``min_live_fraction * b*_true``; the per-bar log-wealth damage is
    ``-growth_rate(false_edge_returns, min_live_fraction * b*_true)`` (>= 0 for a
    non-favourable edge); the demotion latency multiplies it; and the surviving
    fraction ``(1 - backstop_rejection_rate)`` caps it. The bound is applied only
    when ``controls_in_force`` is ``True`` (RD2 conditional); otherwise
    ``backstop_rejection_rate`` is treated as zero and the tighter unbounded
    ``L_FD`` is used.

    All quantities are named parameters (champion dwell, demotion latency,
    backstop rejection rate, the two Kelly fractions); no magic numbers. The
    numeric values are on-ledger OUTPUTS — the fixtures here are illustrative.
    """
    if not (0.0 <= backstop_rejection_rate <= 1.0):
        raise ValueError("backstop_rejection_rate must lie in [0, 1].")
    if champion_dwell_bars <= 0.0 or demotion_latency_bars <= 0.0:
        raise ValueError("horizons must be positive.")
    if operating_fraction <= 0.0 or min_live_fraction <= 0.0:
        raise ValueError("Kelly fractions must be positive.")

    true_r = _clean_1d(true_edge_returns, "true_edge_returns")
    false_r = _clean_1d(false_edge_returns, "false_edge_returns")
    if b_star_true is None:
        b_true = full_kelly_leverage(true_r, weights=weights_true)
    else:
        b_true = float(b_star_true)
    if not np.isfinite(b_true) or b_true <= 0.0:
        raise ValueError("true_edge_returns imply no positive full-Kelly bet; not a true edge.")

    g_true = growth_rate(
        true_r, operating_fraction * b_true, weights=weights_true, barrier="absorbing"
    )
    if not np.isfinite(g_true) or g_true <= 0.0:
        raise ValueError("operating_fraction ruins or fails to grow on true_edge_returns.")
    l_md = float(champion_dwell_bars) * float(g_true)

    applied_false = min_live_fraction * b_true
    g_false = growth_rate(false_r, applied_false, weights=weights_false, barrier="absorbing")
    # A false edge damages log-wealth per bar: loss is the non-negative part of
    # the negative growth (a genuinely-null edge grows <= 0 when sized).
    per_bar_loss = max(0.0, -float(g_false))
    l_fd_unbounded = float(demotion_latency_bars) * per_bar_loss

    if controls_in_force:
        l_fd = l_fd_unbounded * (1.0 - backstop_rejection_rate)
        note = "RD2 bound applied (Memo-1 ruin sizing + ADR-0010 ramp + DSR/PBO/rotor in force)."
    else:
        l_fd = l_fd_unbounded
        note = (
            "controls NOT in force: RD2 bound withheld, tighter L_FD used "
            "(revert to conservative alpha)."
        )

    ratio = float("inf") if l_fd <= 0.0 else l_md / l_fd
    return LossModel(
        l_fd=float(l_fd),
        l_md=float(l_md),
        loss_ratio=float(ratio),
        controls_in_force=bool(controls_in_force),
        l_fd_unbounded=float(l_fd_unbounded),
        backstop_rejection_rate=float(backstop_rejection_rate),
        min_live_fraction=float(min_live_fraction),
        demotion_latency_bars=float(demotion_latency_bars),
        champion_dwell_bars=float(champion_dwell_bars),
        notes=note + " ILLUSTRATIVE on the supplied fixture; on-ledger values deferred.",
    )


# ---------------------------------------------------------------------------
# RD4 — decision-theoretic threshold: MPRR Bayes cutoff + Sun-Cai + q-value
# ---------------------------------------------------------------------------


def optimal_threshold(loss_ratio: float) -> float:
    """MPRR (2004) posterior-null Bayes cutoff ``t* = lambda / (1 + lambda)`` (RD4).

    Under the additive loss ``c_FD * (false discoveries) + c_FN * (missed
    discoveries)`` with ``lambda = c_FN / c_FD = L_MD / L_FD``, the Bayes rule
    declares a discovery on hypothesis ``i`` iff its posterior-null probability
    (local fdr) ``v_i`` satisfies ``v_i < t*`` with

        t* = c_FN / (c_FD + c_FN) = lambda / (1 + lambda).

    Equivalently the posterior-null ODDS cutoff ``t* / (1 - t*) = lambda`` equals
    the missed/false cost ratio (Muller et al. 2004; the prior-odds x loss ->
    threshold form of Harvey 2017). ``t*`` is strictly increasing in ``lambda``:
    a larger ``lambda`` (missed compounding weighted above false discovery)
    yields a LOOSER (larger tolerated) cutoff, exactly the ADR-0013 direction.
    ``lambda = +inf`` gives ``t* -> 1`` (admit everything the backstops cap).
    """
    if loss_ratio < 0.0 or (np.isnan(loss_ratio)):
        raise ValueError("loss_ratio must be non-negative.")
    if not np.isfinite(loss_ratio):
        return 1.0 - _EPS
    return float(loss_ratio / (1.0 + loss_ratio))


def bayes_discovery_rule(lfdr: npt.ArrayLike, loss_ratio: float) -> np.ndarray:
    """Boolean discovery vector under the MPRR Bayes cutoff (RD4).

    ``reject_i = (lfdr_i < optimal_threshold(loss_ratio))``. ``True`` = declare a
    discovery (admit the allocator).
    """
    v = _clean_lfdr(lfdr)
    t_star = optimal_threshold(loss_ratio)
    return v < t_star


def implied_screening_fdr(lfdr: npt.ArrayLike, loss_ratio: float) -> float:
    """Realised FDR (mean posterior-null mass among discoveries) at the MPRR cutoff.

    This is the FDR level the decision-theoretic cutoff *implies* on a given
    local-fdr population — the bridge from the loss ratio to a reportable FDR
    operating point (RD4). It is monotone non-decreasing in ``loss_ratio``: a
    looser cutoff admits higher-lfdr hypotheses, raising the average. Returns
    ``0.0`` when nothing is admitted.
    """
    v = _clean_lfdr(lfdr)
    admitted = v < optimal_threshold(loss_ratio)
    if not np.any(admitted):
        return 0.0
    return float(np.mean(v[admitted]))


@dataclass(frozen=True)
class SunCaiRule:
    """Sun-Cai (2007) oracle local-fdr rule outcome."""

    reject: np.ndarray
    realized_fdr: float
    n_reject: int
    fdr_level: float


def sun_cai_oracle_rule(lfdr: npt.ArrayLike, *, fdr_level: float) -> SunCaiRule:
    """Sun & Cai (2007) oracle local-fdr rule: min FNR s.t. FDR <= ``fdr_level``.

    Rank the local-fdr values ascending and reject the largest prefix whose
    running mean stays at or below ``fdr_level`` (the moving-average local-fdr
    rule; the running mean of the smallest ``k`` local fdrs is the oracle FDR of
    rejecting them). Among all FDR-controlling rules this rejection set minimises
    the false-non-discovery rate.

    ``fdr_level`` is a REQUIRED parameter with no default — the enacted level is
    an on-ledger OUTPUT, not a constant baked here.
    """
    if not (0.0 < fdr_level < 1.0):
        raise ValueError("fdr_level must lie in (0, 1).")
    v = _clean_lfdr(lfdr)
    order = np.argsort(v, kind="stable")
    sorted_v = v[order]
    running_mean = np.cumsum(sorted_v) / np.arange(1.0, v.size + 1.0)
    below = running_mean <= fdr_level
    k = int(np.searchsorted(~below, True)) if np.any(~below) else v.size
    # k = number of leading entries kept (largest prefix under the level).
    if not below[0]:
        k = 0
    reject = np.zeros(v.size, dtype=bool)
    if k > 0:
        reject[order[:k]] = True
    realized = float(running_mean[k - 1]) if k > 0 else 0.0
    return SunCaiRule(
        reject=reject, realized_fdr=realized, n_reject=int(k), fdr_level=float(fdr_level)
    )


def storey_qvalues(pvalues: npt.ArrayLike, *, pi0: float | None = None) -> np.ndarray:
    """Storey (2003) q-values — the FDR bridge from p-values (RD4).

    ``q(p_(i)) = min_{j >= i} pi0 * m * p_(j) / j`` (monotone, enforced by a
    backward cumulative minimum). Rejecting at level ``alpha`` (``q_i <= alpha``)
    controls the positive FDR at ``alpha`` (Storey 2003). ``pi0`` defaults to the
    :func:`storey_pi0` spline estimate.
    """
    p = _clean_pvalues(pvalues)
    m = p.size
    if pi0 is None:
        pi0 = storey_pi0(p)
    order = np.argsort(p, kind="stable")
    p_sorted = p[order]
    ranks = np.arange(1.0, m + 1.0)
    raw = pi0 * m * p_sorted / ranks
    q_sorted = np.minimum.accumulate(raw[::-1])[::-1]
    q_sorted = np.clip(q_sorted, 0.0, 1.0)
    q = np.empty(m, dtype=np.float64)
    q[order] = q_sorted
    return q


# ---------------------------------------------------------------------------
# RD5 — FWER-vs-FDR growth-risk comparator as a function of family size N
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TwoGroupsModel:
    """Gaussian two-groups operating model for the growth-risk comparator.

    ``pi0`` null proportion, ``mu`` one-sided alternative z-shift (signal
    strength), ``sigma`` alternative scale. Operating characteristics are
    computed analytically from this model (Genovese & Wasserman 2002).
    """

    pi0: float
    mu: float
    sigma: float = 1.0

    @property
    def pi1(self) -> float:
        return 1.0 - self.pi0


@dataclass(frozen=True)
class CriterionDecision:
    """FWER-vs-FDR criterion decision by growth-risk comparison (RD5).

    ``criterion`` is one of ``{"retain-fwer", "bh-prds", "benjamini-yekutieli"}``.
    ``prds_obligation`` is ``True`` iff the BH-PRDS branch is chosen and the
    ``prds_argument_ref`` in the trial register must be discharged (else a BY
    fallback is used). The Hansen (2005) SPA existence gate is retained under
    every branch, and the switch stays inside the Romano-Wolf (2005) /
    Romano-Shaikh-Wolf (2008) bootstrap framework (not a machinery swap).
    """

    criterion: str
    prds_obligation: bool
    family_size: int
    loss_fwer: float
    loss_fdr: float
    power_fwer: float
    power_fdr: float
    fdr_cutoff: float
    spa_existence_gate_retained: bool
    bootstrap_framework: str
    notes: str


def _oracle_fdr_pcutoff(model: TwoGroupsModel, target_fdr: float) -> tuple[float, float]:
    """Oracle p-value cutoff ``c`` with two-groups FDR(``c``) = ``target_fdr``.

    One-sided z-test ``p = 1 - Phi(z)``. Under the null ``P(P <= c) = c``; under
    the alternative ``z ~ N(mu, sigma)`` so
    ``G(c) = Phi((mu - Phi^{-1}(1 - c)) / sigma)`` (Genovese & Wasserman 2002;
    the cited ``Phi(mu - Phi^{-1}(1 - c))`` is the ``sigma = 1`` special case).
    The oracle FDR of the cutoff ``c`` is
    ``pi0 c / (pi0 c + pi1 G(c))``, strictly increasing in ``c``, so a unique
    root exists. Returns ``(c, power = G(c))``.
    """
    pi0 = model.pi0
    pi1 = model.pi1

    def g_alt(c: float) -> float:
        return float(norm.sf((norm.isf(c) - model.mu) / model.sigma))

    def fdr_gap(c: float) -> float:
        denom = pi0 * c + pi1 * g_alt(c)
        if denom <= 0.0:
            return -target_fdr
        return pi0 * c / denom - target_fdr

    lo, hi = _CUTOFF_BRACKET_FLOOR, 1.0 - _CUTOFF_BRACKET_FLOOR
    if fdr_gap(hi) <= 0.0:
        c = hi
    elif fdr_gap(lo) >= 0.0:
        c = lo
    else:
        c = float(brentq(fdr_gap, lo, hi))
    return c, float(g_alt(c))


def fwer_vs_fdr_decision(
    model: TwoGroupsModel,
    family_size: int,
    loss_model: LossModel,
    *,
    family_alpha: float,
    fdr_level: float,
    dependence_inflation: float = 1.0,
    prds_defensible: bool = True,
) -> CriterionDecision:
    """Decide FWER vs FDR by expected log-wealth (growth) loss at family size ``N`` (RD5).

    Expected growth loss under each criterion combines the asymmetric loss model:
    ``loss = L_MD * E[missed discoveries] + L_FD * E[false discoveries]``.

    - **FWER (Romano-Wolf StepM).** Conservative single-test level
      ``family_alpha / N_eff`` with ``N_eff = N / dependence_inflation`` (the
      Bonferroni bound; ``dependence_inflation >= 1`` shrinks the effective
      number of independent tests under positive dependence). Power
      ``= Phi((mu - Phi^{-1}(1 - alpha_per)) / sigma)``;
      ``E[missed] = N pi1 (1 - power)``;
      ``E[false] <= family_alpha`` (FWER bounds the expected false count near the
      family level).
    - **FDR.** Oracle p-cutoff solving FDR(c) = effective level (Genovese &
      Wasserman 2002); under ``prds_defensible`` the BH-PRDS level is
      ``fdr_level``, else the Benjamini-Yekutieli level is
      ``fdr_level / sum_{k=1}^N 1/k`` (BY 2001 dependency correction).
      ``E[missed] = N pi1 (1 - power)``, ``E[false] = N pi0 c``.

    The criterion is the growth-loss argmin. On a tie or FWER-advantage the
    honest outcome is ``retain-fwer`` (RD5: retain-FWER is admissible). When FDR
    wins, ``bh-prds`` is returned with ``prds_obligation = True`` if
    ``prds_defensible`` (the PRDS argument must be discharged), else
    ``benjamini-yekutieli``.

    ``family_alpha`` and ``fdr_level`` are REQUIRED parameters (no default): the
    enacted levels are on-ledger OUTPUTS, not constants.
    """
    if family_size < 1:
        raise ValueError("family_size must be >= 1.")
    if not (0.0 < family_alpha < 1.0):
        raise ValueError("family_alpha must lie in (0, 1).")
    if not (0.0 < fdr_level < 1.0):
        raise ValueError("fdr_level must lie in (0, 1).")
    if dependence_inflation < 1.0:
        raise ValueError("dependence_inflation must be >= 1 (1 = independence).")

    n = int(family_size)
    pi1 = model.pi1

    # FWER side (Romano-Wolf StepM; Bonferroni-bounded per-test level).
    n_eff = max(1.0, n / dependence_inflation)
    alpha_per = family_alpha / n_eff
    power_fwer = float(norm.sf((norm.isf(alpha_per) - model.mu) / model.sigma))
    e_missed_fwer = n * pi1 * (1.0 - power_fwer)
    e_false_fwer = family_alpha  # FWER bounds E[V] ~ family level
    loss_fwer = loss_model.l_md * e_missed_fwer + loss_model.l_fd * e_false_fwer

    # FDR side (BH-PRDS or BY-corrected level).
    if prds_defensible:
        effective_fdr = fdr_level
    else:
        harmonic = float(np.sum(1.0 / np.arange(1.0, n + 1.0)))  # BY 2001 sum_{k=1}^N 1/k
        effective_fdr = fdr_level / harmonic
    c_cut, power_fdr = _oracle_fdr_pcutoff(model, effective_fdr)
    e_missed_fdr = n * pi1 * (1.0 - power_fdr)
    e_false_fdr = n * model.pi0 * c_cut
    loss_fdr = loss_model.l_md * e_missed_fdr + loss_model.l_fd * e_false_fdr

    if loss_fwer <= loss_fdr:
        criterion = "retain-fwer"
        prds_obligation = False
        note = (
            "FWER growth-loss <= FDR: retain-FWER (Romano-Wolf StepM); "
            "honest admissible outcome."
        )
    elif prds_defensible:
        criterion = "bh-prds"
        prds_obligation = True
        note = "FDR growth-loss < FWER and PRDS defensible: BH-PRDS; discharge prds_argument_ref."
    else:
        criterion = "benjamini-yekutieli"
        prds_obligation = False
        note = (
            "FDR growth-loss < FWER but PRDS not defensible: "
            "Benjamini-Yekutieli fallback (BY 2001)."
        )

    return CriterionDecision(
        criterion=criterion,
        prds_obligation=prds_obligation,
        family_size=n,
        loss_fwer=float(loss_fwer),
        loss_fdr=float(loss_fdr),
        power_fwer=power_fwer,
        power_fdr=float(power_fdr),
        fdr_cutoff=float(c_cut),
        spa_existence_gate_retained=True,
        bootstrap_framework=(
            "romano-wolf-stepm (Romano-Shaikh-Wolf 2008 generalized-error-rate switch)"
        ),
        notes=note,
    )


# ---------------------------------------------------------------------------
# Synthetic two-groups DGP helper (seeded)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class TwoGroupsSample:
    """A drawn two-groups sample (RD3 fixture)."""

    z: np.ndarray
    pvalues: np.ndarray
    is_alt: np.ndarray
    pi0: float
    mu: float
    sigma: float


def synthetic_two_groups(
    n_tests: int,
    *,
    pi0: float,
    mu: float,
    rng: np.random.Generator,
    sigma: float = 1.0,
) -> TwoGroupsSample:
    """Draw a Gaussian two-groups sample with KNOWN ``pi0`` (RD3 benchmark).

    Each test is null (``z ~ N(0, 1)``) with probability ``pi0`` or alternative
    (``z ~ N(mu, sigma)``) otherwise; one-sided p-values are ``1 - Phi(z)``. The
    caller supplies a seeded ``numpy`` Generator (reproducibility log traces the
    seed).
    """
    if n_tests < 1:
        raise ValueError("n_tests must be >= 1.")
    if not (0.0 < pi0 < 1.0):
        raise ValueError("pi0 must lie in (0, 1).")
    if not (sigma > 0.0):
        raise ValueError("sigma must be positive.")
    is_alt = rng.random(n_tests) >= pi0
    z = rng.standard_normal(n_tests)
    z = np.where(is_alt, mu + sigma * z, z)
    p = 1.0 - norm.cdf(z)
    return TwoGroupsSample(
        z=z,
        pvalues=p,
        is_alt=is_alt,
        pi0=float(pi0),
        mu=float(mu),
        sigma=float(sigma),
    )
