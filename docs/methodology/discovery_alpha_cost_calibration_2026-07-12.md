# Discovery-alpha cost calibration: asymmetric-loss FDR/FWER derivation — method freeze

**Status:** METHOD FROZEN this session (2026-07-12) · on-ledger NUMERIC
instantiation of the alpha LEVEL / `pi1` / `lambda` / the FWER-vs-FDR criterion
**DEFERRED** to the step-4 shadow-ledger backfill · **no discovery target is
enacted here** · **BLOCKING** per
[ADR-0013](../decisions/ADR-0013-aggressive-geometric-growth-mandate.md)
Decision 9 · follow-up `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`.


> **NUMERIC INSTANTIATED 2026-07-17** (round-1 audit remediated) — the
> deferred on-ledger outputs are emitted by the addendum at the end of this
> memo (§ Numeric instantiation addendum); the frozen method body above is
> unchanged. Enacted: `screening_error_rate_target = 0.7401` (median of the
> 24-point enactment band; full precision in the config); criterion
> `retain-fwer` (Romano-Wolf retained); `prds_argument_ref` stays null.

This memo freezes the decision-theoretic derivation, the reference estimator
([src/skie_universe2/inference/discovery_alpha.py](../../src/skie_universe2/inference/discovery_alpha.py)),
and its unit tests
([tests/test_discovery_alpha.py](../../tests/test_discovery_alpha.py)) that GATE
enacting any *looser* discovery target / criterion / TOST re-weighting for the
Kelly-sweep confirmation family. Per ADR-0013 Decision 9 no loosened target may
be enacted until this memo is frozen. The binding numeric outputs — the
screening alpha LEVEL, the base rate `pi1`, the loss ratio `lambda`, and the
FWER/FDR criterion decision — are computed on the ADR-0003 shadow ledger, which
is **not yet populated**; they are therefore deferred to the post-step-4
backfill. The config
([config/multipletest_family.yaml](../../config/multipletest_family.yaml))
stays at `screening_error_rate_target: null`, `correction: romano-wolf`,
`prds_argument_ref: null` for the `allocator-confirmation-kelly-sweep` family
until that backfill run instantiates them. Every number in this memo is
**illustrative-on-synthetic-fixture**, never a ledger operating point; the
estimator's mathematical properties are demonstrated by the frozen unit tests,
each derivation section naming the test that reproduces it.

This memo is the discovery-side twin of the sizing-side freeze
[kelly_growth_concavity_ruin_2026-07-12.md](kelly_growth_concavity_ruin_2026-07-12.md)
("Memo 1"), on which it formally depends (RD1/RD2).

## Setup and notation

The Kelly-sweep confirmation family (ADR-0013 Decision 4) is a multiple-testing
problem: every (allocator-config × Kelly-fraction) pair over the registered grid
`{0.5, 0.75, 1.0, 1.25}` is one trial, and the family is corrected as a whole.
Let `N` be the family size (×4 from the Kelly dimension). For each trial let
`H_i = 0` denote a null (zero/negative-edge allocator) and `H_i = 1` a true
edge. Write `pi0 = P(H_i = 0)`, `pi1 = 1 - pi0`. A **discovery** is declaring
`H_i = 1` (admitting the allocator to live capital via the ADR-0007 ladder). A
**false discovery** (FD) admits a null; a **missed discovery** (MD) rejects a
true edge. All losses below are in **log-wealth (geometric-growth) units** —
mean log-wealth growth rate per Memo 1 (`kelly_growth.growth_rate`) — because
ADR-0013 makes geometric growth the primary objective.

## RD1 — asymmetric loss in log-wealth units

The two error types are not symmetric under the ADR-0013 compounding mandate.

**Missed-discovery loss `L_MD` (forgone compounding).** Rejecting a true-edge
allocator forgoes its compounded log-wealth over the horizon it would have been
the champion. With `g_true = growth_rate(true_edge_returns, f · b*_true)` the
per-bar geometric growth of the true edge at the operating Kelly fraction `f`
(Memo 1, D1), and `H_dwell` a champion-dwell horizon in bars,

```
L_MD = H_dwell · g_true.                                                 (RD1-1)
```

`L_MD` is large precisely because the program levers into compounding: a
forgone true edge compounds its absence over the whole dwell.

**False-discovery loss `L_FD` (bounded; see RD2).** Admitting a null allocator
sizes a zero/negative-edge return stream. Its per-bar log-wealth damage at the
**minimum live fraction** `f_min` is `−growth_rate(false_edge_returns,
f_min · b*_true)` (non-negative for a genuinely non-favourable edge). Left
unbounded over a demotion latency `H_dem` this is `L_FD_unbounded = H_dem ·
per_bar_loss`. RD2 supplies the load-bearing bound.

**The loss ratio.** Define

```
lambda = L_MD / L_FD > 1   (an ESTIMATE, not an assertion).              (RD1-2)
```

`lambda` is *estimated* from the loss model (`build_loss_model`), never asserted:
it exceeds one when the forgone compounding of a true edge outweighs the
(bounded) damage of a false one — the empirical direction under the RD2 controls,
not a stipulated inequality. This is the formal statement of "missed compounding
weighted above false discovery" (ADR-0013 Decision 9).

**Reproduced by:** `test_loss_model_ratio_exceeds_one_with_controls` (lambda > 1
and `optimal_threshold(lambda) > 0.5` under the RD2 controls),
`test_controls_off_tightens_relative_to_controls_on` (the RD2 conditional).

## RD2 — the ruin linkage (the load-bearing subtlety)

Under leverage a false discovery does not merely underperform: an overfit
champion at `f ≥ 1×` Kelly can **ruin** (negative geometric growth on a fake
edge; Memo 1, D3/D5). Taken alone this pushes the discovery alpha **down**
(tighter), the opposite of ADR-0013's "looser". The reframe is coherent **only
because the Type-I ruin tail is capped downstream**, so `L_FD` is bounded well
below its naive worst case:

1. **Memo-1 sizing + ruin rejection.** The frozen Kelly estimator sizes on a
   grid bracketed *below* the ruin barrier `f_max` and rejects ruinous leverage
   with the `-inf` absorbing convention (Memo 1, D2/D3/D5). A false edge cannot
   be sized into single-bar ruin at the admitted grid points.
2. **ADR-0010 earn-by-live-tracking ramp.** A newly admitted allocator enters at
   **minimum live size** `f_min` and earns size only by live-vs-shadow tracking.
   A Schuirmann TOST equivalence gate (RD6) plus CUSUM demotion removes a
   non-tracking (false) edge after a bounded demotion latency `H_dem`.
3. **DSR / PBO / matched-turnover rotor.** The non-waivable integrity core
   (Deflated Sharpe Ratio, Bailey & López de Prado 2014; Probability of Backtest
   Overfitting, Bailey, Borwein, López de Prado & Zhu 2017 (online 2016); the
   matched-turnover random rotor, ADR-0007) rejects a fraction of false edges
   *before* they reach live capital.

Together these bound the false-discovery loss:

```
L_FD  <=  (min-size exposure)  x  (demotion latency)  x  (1 - backstop rejection rate)
       =  [f_min sizing of false_edge_returns]  x  H_dem  x  (1 - r_backstop).   (RD2-1)
```

`build_loss_model` computes exactly (RD2-1): the min-size exposure enters by
sizing the false edge at `f_min · b*_true`, `H_dem` multiplies the per-bar loss,
and `(1 - r_backstop)` is the fraction surviving the DSR/PBO/rotor gate.

**The explicit conditional (why this makes Memo 2 depend on Memo 1 + ADR-0010).**
The looser alpha is licensed **only while controls (1)–(3) are in force**. The
`LossModel.controls_in_force` flag encodes this: with the controls disabled the
RD2 bound is *withheld* (`r_backstop` treated as zero, the tighter unbounded
`L_FD` used), which lowers `lambda` and tightens `t*` back toward the
conservative regime. Absent Memo-1 ruin sizing or the ADR-0010 ramp, revert to a
tighter alpha. Memo 2 is therefore not free-standing: its looseness is a
*conditional* on the sizing freeze (Memo 1) and the live-ramp governance
(ADR-0010) both holding.

**Reproduced by:** `test_controls_off_tightens_relative_to_controls_on`
(`controls_in_force=False` raises `L_FD`, lowers `lambda`, and lowers `t*`),
`test_loss_model_ratio_exceeds_one_with_controls`.

## RD3 — base-rate estimation, sensitivity band, and the circularity break

The decision threshold (RD4) needs the base rate `pi1 = P(true edge)`. Three
estimators are frozen, cross-checked against the finance factor-zoo prior:

- **Exploration-tier hit rate (empirical Bayes).** The ADR-0007 exploration tier
  produces labeled cheap trials; the raw admit rate is a first `pi1` proxy.
- **Storey-Tibshirani (2003) spline `pi0`.** `storey_pi0` fits the cubic
  smoother of `pi0(lambda) = #{p > lambda}/(m(1-lambda))` and evaluates the
  `lambda -> 1` limit, giving `pi1 = 1 - pi0`.
- **Efron (2008) two-groups local fdr.** `efron_local_fdr` estimates the
  marginal density by Lindsey's Poisson-spline method (theoretical `N(0,1)`
  null), yielding a per-trial posterior-null probability whose average is a
  third `pi0` view.

**Cross-check vs the finance prior.** Harvey, Liu & Zhu (2016) and Harvey & Liu
(2020) document a low base rate of true factors in the cross-section (a large
null proportion); the estimated `pi1` must be reported *against* that prior, not
in isolation. A `pi1` far above the factor-zoo prior is a red flag for a
mis-specified null.

**Sensitivity band, not a point.** `pi1` is reported as a **band** across the
three estimators (and across the Storey `lambda`-grid), and the downstream
threshold (RD4) is reported for the whole band. No single `pi1` point is enacted.

**Circularity break.** The exploration hit rate is itself produced *under a
screening target* — the very quantity being set — so using it naively is
circular. The break: `pi1` for the confirmation-tier calibration is estimated
from the **exploration tier's** labeled output (a different, looser tier whose
target is fixed independently), and the confirmation Storey/Efron estimates use
the **confirmation** p-value/z population, so the estimate that feeds the
confirmation target is not conditioned on that target. The two-tier ADR-0007
pipeline is what makes the break possible; the memo records it explicitly so the
backfill run does not silently reintroduce the loop.

**Reproduced by:** `test_storey_pi0_recovers_known_null_proportion` (recovers a
KNOWN `pi0 in {0.70, 0.80, 0.90, 0.95}` within 0.05 on a 20k synthetic
two-groups DGP — benchmark validation), `test_storey_pi0_bounds`,
`test_efron_local_fdr_tracks_oracle` (Lindsey lfdr rank-agrees with the oracle
lfdr, corr > 0.95).

## RD4 — the decision-theoretic threshold `t*(lambda, pi1)`

**Muller-Parmigiani-Robert-Rousseau (2004) explicit-loss Bayes rule.** Under the
additive loss `c_FD · (#FD) + c_FN · (#MD)` with `c_FD = L_FD`, `c_FN = L_MD`,
the posterior expected loss of declaring a discovery on trial `i` is `c_FD · v_i`
(where `v_i` is the posterior-null probability / local fdr) and of not declaring
is `c_FN · (1 - v_i)`. Declaring is optimal iff `c_FD v_i < c_FN (1 - v_i)`, i.e.

```
v_i < t*  with  t* = c_FN / (c_FD + c_FN) = lambda / (1 + lambda).       (RD4-1)
```

Equivalently the **posterior-null ODDS cutoff** `t*/(1 - t*) = lambda = L_MD/L_FD`
equals the missed/false cost ratio — the "prior-odds × loss → threshold" /
minimum-Bayes-factor form of Harvey (2017). `optimal_threshold` returns (RD4-1).
The cutoff is **looser exactly to the degree `lambda > 1`** (and only while the
RD2 bound holds, since `lambda` is built under `controls_in_force`): `t*` is
strictly increasing in `lambda`, `t* -> 1` as `lambda -> inf` (backstops fully
cap FD, admit everything they catch), and `t* = 1/2` at `lambda = 1` (symmetric
loss). Note `t*` on the local-fdr scale is `pi1`-free; `pi1` enters when the
cutoff is *translated* to a reportable FDR operating point
(`implied_screening_fdr`, which averages the admitted local-fdr mass — a
function of the `pi1`-dependent lfdr population).

**Sun-Cai (2007) oracle local-fdr rule.** `sun_cai_oracle_rule` ranks trials by
local fdr ascending and rejects the largest prefix whose running mean stays at or
below a target FDR — the oracle rule that **minimises the false-non-discovery
rate subject to FDR control**. It is the compound-decision counterpart of the
MPRR pointwise rule and the operational bridge from a cost-derived FDR target to
a rejection set.

**Storey (2003) q-value bridge.** `storey_qvalues` maps p-values to q-values
(`q(p_(i)) = min_{j>=i} pi0 m p_(j) / j`); rejecting at level `alpha` controls the
positive FDR at `alpha`. On a well-specified DGP the Sun-Cai oracle rule and the
Storey q-value procedure select the same rejection set — the two representations
of the same FDR control agree.

**Reproduced by:** `test_optimal_threshold_matches_mprr_analytic` (reproduces the
analytic `c_FN/(c_FD+c_FN)` cutoff and the odds identity),
`test_bayes_rule_selects_below_cutoff`,
`test_infinite_loss_ratio_admits_all_capped_edges`,
`test_sun_cai_oracle_and_storey_qvalue_agree` (Sun-Cai vs Storey q-value
agreement within 5% on a known DGP), `test_sun_cai_realized_fdr_under_level`,
`test_threshold_monotone_in_loss_ratio`,
`test_implied_screening_fdr_monotone_in_loss_ratio` (loss-ratio monotonicity:
higher `lambda` -> looser threshold and larger implied FDR).

## RD5 — the FWER→FDR decision by growth-risk comparison

Whether to control the FWER (the standing ADR-0007 Romano-Wolf StepM regime) or
switch to FDR is decided by **expected log-wealth (growth) loss**, as a function
of the family size `N` (which grows ×4 with the Kelly sweep). `fwer_vs_fdr_decision`
computes, for a Gaussian two-groups operating model (signal strength `mu`, base
rate `pi1`):

```
loss(criterion) = L_MD · E[#missed] + L_FD · E[#false].                 (RD5-1)
```

- **FWER (Romano-Wolf StepM).** Conservative single-test level
  `alpha_family / N_eff` with `N_eff = N / dependence_inflation` (Bonferroni
  bound; positive dependence shrinks the effective number of independent tests).
  Power `= Phi(mu - Phi^{-1}(1 - alpha_per))`; `E[#missed] = N pi1 (1 - power)`;
  `E[#false] <= alpha_family`.
- **FDR.** Oracle p-cutoff solving the Genovese-Wasserman (2002) operating
  characteristic `FDR(c) = pi0 c / (pi0 c + pi1 G(c)) = q_eff`; under a
  defensible PRDS argument `q_eff = fdr_level` (BH-PRDS), else
  `q_eff = fdr_level / sum_{k=1}^N 1/k` (Benjamini-Yekutieli 2001 dependency
  correction). `E[#missed] = N pi1 (1 - G(c))`, `E[#false] = N pi0 c`.

The criterion is the growth-loss argmin. As `N` grows the FWER per-test level
collapses (`alpha_family/N`), its power → 0 and its missed-compounding loss
explodes linearly, while the FDR cutoff is `N`-stable (the FDR fixed point does
not depend on `N`), so FDR wins at large `N`. At small `N` with strong
dependence, `N_eff → 1` keeps FWER power high and the false-discovery ruin term
(capped by RD2) dominates, so **retain-FWER** is the honest, admissible outcome.
Retain-FWER is not a fallback of last resort — it is the correct answer whenever
the growth-loss comparison favours it.

**PRDS discharge / BY fallback.** When FDR wins and BH is chosen, the
`prds_argument_ref` obligation is raised: BH controls FDR under positive
regression dependency (PRDS; Benjamini-Yekutieli 2001), which must be *argued*
for the Kelly-sweep loss-differential structure and recorded in the trial
register. If PRDS is not defensible, the criterion falls back to
Benjamini-Yekutieli (valid under arbitrary dependence at a power cost).

**Retained gates.** The Hansen (2005) SPA **existence** gate is retained under
*every* branch (`spa_existence_gate_retained = True`): the criterion decision
governs *identification*, not the existence test. The switch stays **inside the
same bootstrap machinery** — Romano-Shaikh-Wolf (2008) formalize k-FWER / FDP
control in the Romano-Wolf (2005) StepM bootstrap framework, so moving from FWER
to FDR is a *disciplined criterion change*, not a replacement of the resampling
engine.

**Reproduced by:** `test_comparator_retains_fwer_small_n_strong_dependence`
(retain-FWER at `N=4`, strong dependence),
`test_comparator_prefers_fdr_large_n` (BH-PRDS at `N=2000`, independence),
`test_comparator_loss_ratio_monotone_in_n` (FWER/FDR growth-loss ratio increases
monotonically in `N` — the crossover is a monotone determinism check, not a
magic threshold), `test_bh_sets_prds_obligation_else_by_fallback` (PRDS
obligation set under a defensible argument, else BY fallback).

## RD6 — registered OUTPUTS (deferred), TOST re-weighting, and grid coordination

The following are **OUTPUTS to be instantiated on the ledger** at the step-4
backfill; none is written as a constant now:

| Output | Config field | Instantiation source |
|---|---|---|
| Screening alpha LEVEL | `screening_error_rate_target` (stays `null`) | `optimal_threshold(lambda)` → `implied_screening_fdr` on the ledger lfdr population |
| Correction criterion | `correction` (stays `romano-wolf`) | `fwer_vs_fdr_decision` on the ledger `N`, loss model, dependence |
| PRDS obligation | `prds_argument_ref` (stays `null`) | set iff the decision returns `bh-prds` |
| Base rate | (register with the family) | RD3 `pi1` band on the ledger |
| Loss ratio | (register with the family) | RD1/RD2 `lambda` on the ledger fat-tailed returns |

**ADR-0010 TOST re-weighting (Schuirmann 1987).** The live-ramp equivalence gate
declares a live allocator "tracking shadow" iff a Schuirmann two-one-sided-test
rejects both one-sided nulls at level `alpha_TOST` within an equivalence margin
`±delta` at power `1 - beta`. These are derived from the **same loss model**: the
equivalence margin `delta` is the log-wealth tracking error the program tolerates
before demotion (the same `L_FD` per-bar-loss scale that bounds RD2), and the
`alpha_TOST`/power split weights a false "tracking" verdict (keeps a false edge
live — an `L_FD` event) against a false "not-tracking" verdict (demotes a true
edge — an `L_MD` event) with the *same* `lambda`. The TOST `(alpha, delta,
power)` triple is therefore an OUTPUT of the loss model, deferred with the
backfill, not tuned here.

**Kelly-grid coordination with Memo 1.** The loss model must be evaluated on the
**same fat-tailed shadow-ledger distribution** and the **same Kelly grid
`{0.5, 0.75, 1.0, 1.25}`** as Memo 1: `L_MD` uses `growth_rate` at the operating
fraction, `L_FD` sizes the false edge at the grid's minimum live fraction, and
both reuse Memo-1's `full_kelly_leverage`/`growth_rate` (no re-implementation of
log-wealth). The discovery calibration and the sizing selection are thus computed
on one coherent substrate.

## Appendix — zero-magic-number register

Every tunable is a named constant or a documented function default with a
cited/derived rationale (CLAUDE.md Parameter Selection). The **enacted** alpha
LEVEL, FDR target `q`, and family FWER level are **REQUIRED parameters with no
numeric default** — they are on-ledger OUTPUTS, never constants baked in the
estimator. Any synthetic-DGP helper takes a caller-supplied seeded Generator (a
staged-`.py` seed/magic-number pre-commit guard enforces this).

| Tunable | Symbol / default | Source / rationale |
|---|---|---|
| Storey `lambda` grid | `STOREY_LAMBDA_GRID = arange(0.05, 0.96, 0.05)` | Storey & Tibshirani (2003) default tuning grid for the `pi0` smoother. |
| Storey smoother degree | `STOREY_SPLINE_DF = 3` | Storey & Tibshirani (2003) `smooth.spline` cubic df. |
| Lindsey spline df | `LINDSEY_SPLINE_DF = 7` | Efron (2008) `locfdr` natural-spline default. |
| Histogram bins (Efron) | Freedman-Diaconis rule | Data-driven bin width; no constant. |
| Screening alpha LEVEL | REQUIRED param (no default) | On-ledger OUTPUT of `optimal_threshold`/`implied_screening_fdr`; never a constant. |
| FDR target `q`, family FWER `alpha` | REQUIRED params (no default) | On-ledger OUTPUTS; passed as illustrative fixtures in the tests only. |
| Loss ratio `lambda` | OUTPUT of `build_loss_model` | Estimated from `L_MD`/`L_FD` in log-wealth units; not asserted. |
| Champion dwell / demotion latency / backstop rate / Kelly fractions | named params | Loss-model inputs; on-ledger values deferred; fixtures illustrative. |
| IRLS guards | `_IRLS_MAX_STEPS`, `_IRLS_TOL`, `_IRLS_RIDGE` | Poisson-IRLS numerical controls (iteration cap, convergence tolerance, conditioning ridge) — not statistical parameters. |
| Cubic-spline minimum support | `_MIN_SPLINE_KNOTS = 4` | Degree + 1 = 4 knots required for a cubic spline (numerical). |
| Root-search floor | `_CUTOFF_BRACKET_FLOOR = 1e-12` | Keeps the oracle FDR p-cutoff strictly inside `(0,1)` (solver guard). |

## References

1. Kelly, J. L. Jr. 1956. "A New Interpretation of Information Rate." *Bell
   System Technical Journal* 35(4): 917-926.
   https://doi.org/10.1002/j.1538-7305.1956.tb03809.x
2. MacLean, L. C., Thorp, E. O. & Ziemba, W. T. (eds.) 2011. *The Kelly Capital
   Growth Investment Criterion: Theory and Practice.* World Scientific.
   https://doi.org/10.1142/7598 — edited volume; any NUMERIC claim must be pinned
   to the specific contributed chapter, not this volume DOI. No numeric claim
   here relies on it.
3. Benjamini, Y. & Hochberg, Y. 1995. "Controlling the False Discovery Rate."
   *J. R. Statist. Soc. B* 57(1): 289-300.
   https://doi.org/10.1111/j.2517-6161.1995.tb02031.x
4. Benjamini, Y. & Yekutieli, D. 2001. "The Control of the False Discovery Rate
   under Dependency." *Ann. Statist.* 29(4): 1165-1188.
   https://doi.org/10.1214/aos/1013699998
5. Storey, J. D. 2002. "A Direct Approach to False Discovery Rates."
   *J. R. Statist. Soc. B* 64(3): 479-498.
   https://doi.org/10.1111/1467-9868.00346
6. Storey, J. D. 2003. "The Positive False Discovery Rate: a Bayesian
   Interpretation and the q-value." *Ann. Statist.* 31(6): 2013-2035.
   https://doi.org/10.1214/aos/1074290335
7. Genovese, C. & Wasserman, L. 2002. "Operating Characteristics and Extensions
   of the False Discovery Rate Procedure." *J. R. Statist. Soc. B* 64(3):
   499-517. https://doi.org/10.1111/1467-9868.00347
8. Sun, W. & Cai, T. T. 2007. "Oracle and Adaptive Compound Decision Rules for
   False Discovery Rate Control." *JASA* 102(479): 901-912.
   https://doi.org/10.1198/016214507000000545
9. Muller, P., Parmigiani, G., Robert, C. & Rousseau, J. 2004. "Optimal Sample
   Size for Multiple Testing." *JASA* 99(468): 990-1001.
   https://doi.org/10.1198/016214504000001646
10. Efron, B. 2008. "Microarrays, Empirical Bayes and the Two-Groups Model."
    *Statist. Sci.* 23(1): 1-22. https://doi.org/10.1214/07-STS236
11. Storey, J. D. & Tibshirani, R. 2003. "Statistical Significance for
    Genomewide Studies." *PNAS* 100(16): 9440-9445.
    https://doi.org/10.1073/pnas.1530509100
12. Benjamini, Y. & Hochberg, Y. 1997. "Multiple Hypotheses Testing with
    Weights." *Scand. J. Statist.* 24(3): 407-418.
    https://doi.org/10.1111/1467-9469.00072
13. Hansen, P. R. 2005. "A Test for Superior Predictive Ability." *J. Bus. Econ.
    Statist.* 23(4): 365-380. https://doi.org/10.1198/073500105000000063
14. Romano, J. P. & Wolf, M. 2005. "Stepwise Multiple Testing as Formalized Data
    Snooping." *Econometrica* 73(4): 1237-1282.
    https://doi.org/10.1111/j.1468-0262.2005.00615.x
15. Romano, J. P., Shaikh, A. M. & Wolf, M. 2008. "Formalized Data Snooping
    Based on Generalized Error Rates." *Econometric Theory* 24(2): 404-447.
    https://doi.org/10.1017/S0266466608080171
16. Harvey, C. R. & Liu, Y. 2020. "False (and Missed) Discoveries in Financial
    Economics." *J. Finance* 75(5): 2503-2553.
    https://doi.org/10.1111/jofi.12951
17. Harvey, C. R., Liu, Y. & Zhu, H. 2016. "...and the Cross-Section of Expected
    Returns." *Rev. Financ. Stud.* 29(1): 5-68.
    https://doi.org/10.1093/rfs/hhv059
18. Harvey, C. R. 2017. "Presidential Address: The Scientific Outlook in
    Financial Economics." *J. Finance* 72(4): 1399-1440.
    https://doi.org/10.1111/jofi.12530
19. Bailey, D. H. & López de Prado, M. 2014. "The Deflated Sharpe Ratio."
    *J. Portfolio Management* 40(5): 94-107.
    https://doi.org/10.3905/jpm.2014.40.5.094
20. Bailey, D. H., Borwein, J. M., López de Prado, M. & Zhu, Q. J. 2017 (online
    2016). "The Probability of Backtest Overfitting." *J. Computational Finance*
    20(4): 39-69. https://doi.org/10.21314/JCF.2016.322
21. Schuirmann, D. J. 1987. "A Comparison of the Two One-Sided Tests Procedure
    and the Power Approach for Assessing the Equivalence of Average
    Bioavailability." *J. Pharmacokinet. Biopharm.* 15(6): 657-680.
    https://doi.org/10.1007/BF01068419


## Numeric instantiation addendum (2026-07-17) — on-ledger outputs

**Status:** NUMERIC INSTANTIATED (round-1 audit-remediated). Harness
[scripts/run_discovery_alpha_calibration.py](../../scripts/run_discovery_alpha_calibration.py)
(seed 20260717), ReproLog `repro_log_ba92c200ec074f6e961d2a6632bb45ff.json`,
machine artifact
[reports/discovery_alpha_calibration/discovery_alpha_calibration.json](../../reports/discovery_alpha_calibration/discovery_alpha_calibration.json).
The frozen method body above is unchanged; this addendum records the deferred
RD6-table OUTPUTs computed on the populated ADR-0003 ledger
(`orb_first_hour_k1.0@1.0.0`, ES+NQ, per-session NET currency; entered
sessions ES 2276 / NQ 2202; ADR-0004 6-month evaluation windows of 104 (ES) /
100 (NQ) median entered sessions).

### A.1 Inputs (all data-derived or explicitly banded; none hand-set)

| Input | Value | Source rule |
|---|---|---|
| false-edge substrate | demeaned realized per-session net stream, per instrument | the memo's zero-edge canonical case; raw streams as sensitivity |
| true-edge substrate | same stream mean-shifted to the DSR benchmark Sharpe (RC-H101-1: 0.0357; RC-H103-1: 0.0580) | minimum selection-distinguishable edge from the register's own DSR blocks |
| `mu` anchors | ES 0.948/1.148, NQ 0.832/1.057 | `sr_benchmark * sqrt(n_eff_hac)` per scan x instrument |
| `H_dwell` | 104 (ES) / 100 (NQ) sessions (1-window floor); x{2,4} reported sensitivity | ADR-0004 window; the floor is the only structurally guaranteed dwell (ADR-0012 dwell memo unfrozen); larger dwell only loosens the level |
| `H_dem` | **banded {1, 2, 4} evaluation windows** (enactment axis) | demotion at the next cycle is NOT certain (ADR-0012 dethroning non-operational; audit QUANT-1-3) — the exposure horizon is priced into the band, not fixed at its floor |
| `r_backstop` | **banded {0, 0.3332}** (enactment axis) | the realized 2/2 gate record is structurally CENSORED (a slipped null surfaces as an admission, not a miss; audit QUANT-1-4): r = 0 is the no-information anchor, 0.3332 the lower endpoint of the Jeffreys central 95% interval (Beta(2.5, 0.5) 2.5th pct) on the censored record, treated as a PRIOR |
| `rho_bar` / `rho_min` | 0.4168 / 0.0000 | exact RC-H101-1 cell-mask contribution-series correlations |

### A.2 RD1/RD2 loss ratio and RD4 cutoff — the 24-point enactment band

Band = instrument x same-instrument mu-anchor x H_dem {1,2,4} x r {0, 0.3332},
at the 1-window dwell floor. Per-cell t* (4 points each = 2 instruments x 2
anchors):

| H_dem \ r | r = 0 (no-information) | r = 0.3332 (Jeffreys endpoint) |
|---|---|---|
| 1 window | 0.8061 - 0.8393 | 0.8618 - 0.8867 |
| 2 windows | 0.6751 - 0.7230 | 0.7571 - 0.7965 |
| 4 windows | 0.5096 - 0.5662 | 0.6091 - 0.6619 |

**ENACTED: `screening_error_rate_target` = 0.7401** (median of the 24-point
band; exact value 0.7400550140326007 carried in the config — the YAML value
governs all gate comparisons), band [0.5096, 0.8867], stationary-bootstrap 95%
CI [0.4239, 1.0000] (N=1000, PW block lengths; 0 dropped evaluations, 0
partial replicates). Lambda spans 1.04-7.83 across the band. **Closed-form
validation:** `lambda ~ (H_dwell/H_dem) x 4/(1 - r)` (operating-Kelly growth
SR^2/2 over half-Kelly variance drag SR^2/8); at H_dwell = H_dem, r = 0.3332
this gives lambda ~ 6.00 -> t* ~ 0.857, matching the (1-window, Jeffreys)
cells (0.862-0.887, higher-moment deviations only) — the estimator is
consistent with the analytic anchor. Sensitivities: H_dwell x2/x4 (at 1-window
H_dem, Jeffreys r) -> t* 0.926-0.969 (looser; reported only); controls-OFF
(RD2 conditional) -> t* 0.806-0.819 ES/NQ (the mandated fallback direction);
raw un-demeaned streams -> ES t* 0.694 (negative-mean stream), NQ t* -> 1
(weakly positive mean; the costless-false-discovery limit).

### A.3 RD3 base rate

Exploration hit rate (H001, H101, H103 -> 0/3 admitted): pi1 = 0, Jeffreys 95%
[0.00015, 0.5356], median 0.0674 — PRIMARY (consistent with the factor-zoo
prior). Storey spline pi1 = 0.9286 and Efron-Lindsey pi1 = 0.9115 on the n=14
correlated trial population **trip this memo's own RD3 red flag** (far above
the factor-zoo prior => mis-specified null at tiny dependent N) and are
reported-but-excluded from decision use. The enacted t* is pi1-free (RD4).

### A.4 RD5 criterion — retain-fwer at every registered family size

At the enacted level with the measured dependence (`dependence_inflation =
1 + (N-1) x 0.4168`), the growth-loss comparison favours FWER at every N in
{5, 10, 20, 40, 100, 400, 2000} (N=5: loss_fwer 0.036 <= loss_fdr 0.036;
N=2000: 4.53 < 14.5). **Criterion: `retain-fwer`** — Romano-Wolf StepM stays
for the screen families AND the confirmation identification step;
`prds_argument_ref` stays null (no BH enacted). CAVEAT (audit QUANT-1-5): the
rows with N > 20 extrapolate the NESTED-cell equicorrelation to future
(config x Kelly-fraction) families whose dependence does not exist yet; they
are flagged `conditional_on_dependence_transfer` in the artifact, and the RD5
criterion for the confirmation family is **re-decided on that family's own
measured dependence at its first swept scan** (folded into §A.8). The PRDS
empirical check (rho_min = 0.0000, non-negative correlations being a
SUFFICIENT condition for PRDS of one-sided tests on a multivariate normal —
Benjamini-Yekutieli 2001 §3.1 multivariate-normal example) would have
permitted BH-PRDS had FDR won; recorded for completeness.

### A.5 Reporting bridges and RD6 TOST diagnostic

The memo's RD6 arrow (`optimal_threshold -> implied_screening_fdr` on the
ledger lfdr population) is reported as a bridge, not enacted (documented
deviation; A.6): the empirical bridge at the enacted cutoff admits **ALL 14
trials** (every Efron lfdr from the degenerate n=14 Lindsey fit lies in
[0.016, 0.196], below any candidate cutoff) and returns their mean = the
Efron pi0 = **0.0885** — an untrustworthy number because the same fit implies
pi1 ~ 0.91 against the RD3 red flag (the bridge is uninformative in the
admit-everything direction, not the admit-nothing direction). The model
bridge across the Jeffreys pi1 band at the enacted t* = {lo: 0.0,
median: 0.649, hi: 0.406} — non-monotone because the admitted set flips
discontinuously at pi1 -> 0. TOST diagnostic at the enacted level: the
powered window is undefined (`nan`, serialized as a string sentinel) because
the level >= 0.5 makes the one-sided z-quantiles vanish — recorded; the loss
model's H_dem is the banded assumption axis (A.1), and the lambda-weighted
asymmetric TOST re-split remains an ADR-0010 Phase-5 action (no champion
exists).

### A.6 Documented deviations from the frozen memo (audit trail)

1. **Enacted level = t\*, not the implied-FDR translation.** The RD6 arrow's
   translation is degenerate on this ledger, in the ADMIT-EVERYTHING
   direction (corrected per audit QUANT-1-2/REPRODUCIBILITY-1-1): the
   empirical lfdr population from the n=14 correlated Lindsey fit is
   uniformly tiny, so the bridge admits all trials and returns the Efron pi0
   (0.0885) — a number the RD3 red flag marks untrustworthy; the model bridge
   is separately discontinuous at pi1 -> 0 (an earlier fixed-point
   construction oscillated without a fixed point and was removed). t* is the
   memo's primary RD4 decision object and pi1-free; it is enacted directly,
   with both translations reported.
2. **Scale transfer is a governance choice, not a statistical identity**
   (audit QUANT-1-1/LITERATURE-1-1). t* lives on the posterior-null /
   local-fdr scale (MPRR). Its application as the Romano-Wolf adjusted-p
   threshold (S-c) and as the DSR/PBO bounds (S-d) transfers the number
   across inferential scales with different operating characteristics; no
   bridge between the scales is claimed. The transfer is enacted as an
   OPERATIONAL PROXY under the ADR-0013 cost-tuned-looser mandate (the
   cost-derived error budget applied to the gates the program actually
   operates), is flagged provisional in A.7, and is re-derived on a
   non-degenerate lfdr estimator at the §A.8 re-instantiation.
3. **The H_dem and r_backstop point assumptions are replaced by band axes**
   (audit QUANT-1-3/QUANT-1-4): certain-demotion-in-one-window and the
   censored 2/2 record are not defensible point inputs; both are priced into
   the enactment band (A.1/A.2) and the median is enacted.

### A.7 Enactment semantics (what 0.7401 governs; provisional operational proxies)

- `config/multipletest_family.yaml screening_error_rate_target` =
  0.7400550140326007 — the project-wide screening error budget (ADR-0002(c)
  as amended); the YAML value governs all gate comparisons.
- ADR-0014 (S-c): a cell passes iff mean gross > 0 AND Romano-Wolf-adjusted
  p < the level (weak-FWER at the enacted budget; the positive-mean conjunct
  excludes the negative-effect pathology of one-sided levels above 1/2).
- ADR-0014 (S-d): DSR >= 1 - level = **0.2599**; PBO <= **0.7401**
  (`dsr_bound_ref` / `pbo_bound_ref` in the pool-ledger schema resolve here).
- These p/DSR/PBO applications are PROVISIONAL OPERATIONAL PROXIES of the
  posterior-null budget (deviation A.6.2) — revisited, with the level itself,
  at the §A.8 re-instantiation.
- The looseness is licensed ONLY by the RD2 controls being in force (Memo-1
  ruin sizing + ADR-0010 minimum-size ramp + the non-waivable verdict ladder:
  rotor + DSR/PBO at the set-level VERDICT). Under controls-off the level
  reverts toward 0.81 (A.2) and the enactment must be revisited.
- Nothing is certified by this addendum; no Kelly fraction is selected; the
  screen admits into the ADR-0014 provisional POOL only.

### A.8 Standing re-instantiation conditions

1. On the first arsenal admission (a realized true-edge stream), the loss
   model's true-edge substrate stops being an anchor-shifted synthetic and
   this calibration is **re-instantiated on the realized stream** (fresh
   ReproLog, same frozen method; the enacted level re-derived, not carried
   forward).
2. Once an admitted expert accrues live-vs-shadow outcomes, the censored
   `r_backstop` prior is replaced with that outcome record (the only design
   able to observe a gate miss).
3. The RD5 criterion for the confirmation (config x Kelly-fraction) family is
   re-decided on that family's own measured dependence at its first swept
   scan (the N > 20 rows here are conditional extrapolations).
4. The A.6.2 scale transfer is re-derived on a non-degenerate lfdr estimator
   when the trial population supports one.

### A.9 Reproduction closure (2026-07-18)

The enacted artifact is now under an executable reproduction gate, closing
the step-2 reproduction gap of the 2026-07-18 execution brief.

- **Generator identified.** The artifact
  `reports/discovery_alpha_calibration/discovery_alpha_calibration.json` was
  produced by `scripts/run_discovery_alpha_calibration.py` (landed in commit
  `65e1dc8`), ReproLog `repro_log_ba92c200ec074f6e961d2a6632bb45ff.json`:
  recorded git HEAD `6e915058` (the pre-commit dirty-tree run state), seed
  20260717, dataset checksums for the two RC-1 scan JSONs plus the
  shadow-ledger roll-up (4811 partitions). Provenance nuance, recorded here:
  the ReproLog's `config_resolved_sha256` (`c7788707…`) snapshots THIS memo
  as of run time; the committed memo differs (`b7edc598…`) because the §A
  addendum was audit-remediated between the run and commit `65e1dc8`. The
  generator's numerics do not read the memo; the snapshot is informational.
- **Reproduction check.**
  `scripts/audits/check_discovery_alpha_reproduction.py` re-runs the full
  calibration into a scratch path and compares FIELD-BY-FIELD against the
  enacted artifact, with a hard exact-float-equality gate (`==`, never
  isclose) on `enactment.screening_error_rate_target`. Pre-flight: recorded
  dataset checksums are recomputed (substrate-drift abort); the check emits
  its own ReproLog BEFORE the re-run. **Result 2026-07-18: REPRODUCED** —
  frozen 0.7400550140326007 == fresh 0.7400550140326007 (exact float
  equality True), 0 field mismatches over the entire artifact, exit code 0
  (check ReproLog `repro_log_de9a810dbeeb4664b9c405e1f6d798cf.json`; diff
  record `runs/discovery_alpha_repro_check/reproduction_diff.json` — that
  scratch path always holds the LATEST run's record and embeds its
  `check_run_id`).
- **Unit tests** (`tests/test_discovery_alpha_enactment.py`, 14 tests):
  (i) MPRR cutoff t* = λ/(1+λ) exact over a λ grid, strictly monotone,
  boundary behaviour (0, +inf, negative, nan) and the odds identity on every
  enactment-band point; (ii) enactment-band median computed over the 24
  enactment members ONLY (including the sensitivity points would change the
  median — witnessed), band extrema; (iii) bootstrap-primitive seed
  reproducibility, CI brackets the enacted level, nan replicates dropped not
  zero-filled (source-level pin — the semantics live inline in the frozen
  generator, whose numerics are not modified); (iv) config coupling — the
  YAML `screening_error_rate_target` equals the artifact's `t_star_enacted`
  at FULL float precision (`==` on the parsed floats), and both screen
  artifacts' S-d bounds equal the COMPUTED (1 − level, level) exactly.
- Nothing in this addendum changes any enacted value; the reproduction gate
  reports, it never re-derives.
- Audit round 1 (2026-07-18) remediated the checker's exit-code contract
  (a crash now maps to exit 2 ERROR, never to the exit-1 FINDING code;
  crash-mapping unit test added) and the check was RE-EXECUTED post-
  remediation: REPRODUCED again, exit 0, 0 field mismatches (ReproLog
  `repro_log_53c25c7a11594dcc920d7d65f9b89de4.json`).
