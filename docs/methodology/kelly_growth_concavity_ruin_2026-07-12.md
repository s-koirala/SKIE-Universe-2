# Kelly growth: concavity, estimation error, and the ruin-consistent estimator — method freeze

**Status:** METHOD FROZEN this session (2026-07-12) · on-ledger NUMERIC
instantiation **DEFERRED** to the step-4 shadow-ledger backfill · **no Kelly
fraction is selected here** · **BLOCKING** per
[ADR-0013](../decisions/ADR-0013-aggressive-geometric-growth-mandate.md)
Decision 9 · follow-up `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`.

This memo freezes the derivation, the reference estimator
([src/skie_universe2/inference/kelly_growth.py](../../src/skie_universe2/inference/kelly_growth.py)),
and its unit tests
([tests/test_kelly_growth.py](../../tests/test_kelly_growth.py)) that GATE any
empirical selection of a swept Kelly fraction on geometric (compounded /
log-wealth) growth. Per ADR-0013 Decision 9 no fraction may be chosen on
geometric growth until this memo is frozen. The binding numeric outputs — the
on-ledger full-Kelly bet `b*`, the grid growth curve, the estimation-adjusted
optimum `f**`, `P(ruin)`, and the over-betting crossing `f_0` — are computed on
the ADR-0003 shadow ledger, which is **not yet populated**; they are therefore
deferred to the post-step-4 backfill. Every number in this memo is
**illustrative-on-representative-substrate** (an ES 1-min slice or a synthetic
benchmark used by the unit tests), never a ledger operating point.


> **NUMERIC INSTANTIATED 2026-07-17** — the deferred on-ledger outputs
> (b*, grid growth curve, f_max, f_0, f**, P(ruin)) are emitted by the
> addendum at the end of this memo; the frozen method body is unchanged.
> RECORD ONLY: no Kelly fraction is selected; the grid-bracketing verdict
> is INCONCLUSIVE-ON-NULL-LEDGER (see § B.3) and re-instantiation at the
> first arsenal admission is a registered standing condition.

The methodology contract is: the estimator's mathematical properties are
demonstrated by the frozen unit tests rather than by ad-hoc numbers embedded
here. Each derivation section names the test that reproduces it.

## Setup and notation

Let `f` be the swept Kelly **fraction** over the registered grid
`{0.5, 0.75, 1.0, 1.25}` (ADR-0013 Decision 3): `f = 1` is full Kelly,
`f = 1.25` over-betting, `f = 0.5` under-betting. Let `b*` be the
growth-optimal (full-Kelly) **bet** — the leverage that maximises log-growth on
the empirical measure — and `R` the per-bar return, drawn from the fat-tailed
shadow-ledger distribution. On the empirical (discrete) measure
`{(R_i, w_i)}_{i=1..n}` with weights `w_i >= 0`, `sum_i w_i = 1` (uniform
`w_i = 1/n` by default), the geometric growth of fraction `f` is

```
g(f) = E[ log(1 + f b* R) ] = sum_i w_i log(1 + f b* R_i).            (D1)
```

Writing `m_i = b* R_i` (the per-atom bet outcome) the analysis below is a
one-parameter concave program in `f` on the effective domain `[0, f_max)`.

## D1 — concavity and the unique interior maximum

**Closed-form derivatives.** Differentiating (D1) termwise,

```
g'(f)  = sum_i w_i m_i / (1 + f m_i),
g''(f) = -sum_i w_i m_i^2 / (1 + f m_i)^2.
```

On the effective domain every denominator `1 + f m_i > 0`, so each summand of
`g''` is non-negative and `g''(f) < 0` strictly whenever at least one bet is
non-degenerate (`m_i != 0` with `w_i > 0`). Hence **`g` is strictly concave**.
At the origin `g'(0) = sum_i w_i m_i = b* E[R] > 0` for a favourable bet
(`E[R] > 0`, `b* > 0`), so `g` is increasing at `f = 0`; strict concavity then
gives a **unique interior maximiser**. Because `b*` is defined as the
growth-optimal leverage on the same measure — i.e. `sum_i w_i R_i/(1 + b* R_i)
= 0` — the maximiser of `g(f)` is exactly the full-Kelly fraction `f = 1`. This
is the Kelly (1956) / Breiman (1961) log-optimal criterion re-expressed in the
fraction coordinate.

**Fat-tail validity (the binding condition is a finite LOG-moment, not finite
variance).** The growth-optimality and a.s. dominance of the log-optimal bet
require only that `E|log(1 + f b* R)| < infinity` — a finite log-moment (Algoet
& Cover 1988; Cover & Thomas 2005, ch. 16). Heavy tails in `R` (even infinite
variance) are admissible: the logarithm tames upside tails, and the ruin
barrier (D3) governs the downside. Requiring finite variance would be a
mis-statement of the regularity condition and would wrongly exclude the
fat-tailed shadow-ledger substrate this program targets.

**Reference estimator.** `full_kelly_leverage` solves `g'(lambda) = 0` on
`(0, lambda_max)` by Brent's method; `growth_derivative` /
`growth_second_derivative` expose the closed forms; `growth_curve` evaluates
`g` over the grid.

**Reproduced by:** `test_full_kelly_coin_closed_form` (even-money coin with win
probability `p` recovers the closed-form full-Kelly stake `f* = 2p - 1`),
`test_growth_curve_peaks_at_full_kelly` (`g'(1) = 0`, `g''(1) < 0`),
`test_es_growth_curve_concave_single_peak` (strict `g'' < 0` and a single
interior peak at `f ~ 1` on real ES 1-min returns),
`test_analytic_first_derivative_matches_finite_difference` /
`test_second_derivative_matches_finite_difference` (closed forms vs finite
differences), `test_growth_finite_under_infinite_variance_returns`
(Student-t, 1.5 dof, infinite variance -> finite growth).

## D2 — estimation-error-adjusted optimum `f** <= 1`

The full-Kelly bet `b*` is unknown and must be estimated; the plug-in
`b*_hat` inherits estimation error, and the growth surface `g(f)` is concave, so
the **out-of-sample** optimum shifts below full Kelly. Chopra & Ziemba (1993)
quantify why: errors in the **mean** dominate errors in variance/covariance by
roughly 11:1 in their cash-equivalent loss, and mean-estimation error is exactly
what inflates the plug-in Kelly bet — the estimator systematically over-bets.
Rujeerapaiboon, Kuhn & Wiesemann (2016) establish the **conservatism
direction**: the distributionally-robust growth-optimal portfolio allocates
materially **lower leverage** than the nominal plug-in Kelly rule (this is a
direction-of-effect result, not a scalar inequality). Fractional-Kelly practice
(MacLean, Ziemba & Blazenko 1992; MacLean, Thorp & Ziemba 2010) is the standing
operational expression of the same shrinkage.

**Method (frozen).** `nested_rolling_origin_growth` implements a purged,
embargoed expanding-window walk-forward (López de Prado 2018, ch. 7): each fold
estimates `b*_hat` on the training span (**plug-in**) and **evaluates** `g` on a
disjoint forward test window at each grid fraction (leverage `f b*_hat`). A
`purge` gap (return-label horizon minus one; `0` for a one-bar return) and an
`embargo` (fraction of the sample) separate train from test to defeat leakage.
The estimation-adjusted optimum `f**` is the argmax of the across-fold mean
out-of-sample growth. A grid fraction whose OOS growth is `-inf` in any fold
**ruined out-of-sample** at that leverage and is penalised accordingly.

**Bracketing verdict is an OUTPUT, not an assertion.** Whether the grid floor
`0.5` brackets `f**` from below — i.e. whether `f** > 0.5` so the registered
grid contains the estimation-adjusted optimum in its interior — is an **output
of the on-ledger run**, deferred with the backfill. The expected direction
(`f** <= 1`, plausibly `0.5 < f** < 1`) is stated as a prior from Chopra-Ziemba
/ Rujeerapaiboon, **not** asserted by the estimator or the tests. On a
favourable illustrative slice the OOS argmax can even land at `1.25` (the grid
top); this is expected sampling behaviour on a single window and underscores why
the verdict must come from the full rolling-origin ledger evaluation, not a
point substrate.

**Reproduced by:** `test_rolling_origin_synthetic_happy_path_selects_grid_member`
(fresh-clone-portable success path: runs to completion on a seeded synthetic
substrate, computes OOS growth, selects a grid member as `f**`, and audits the
purge+embargo train/test gap), `test_rolling_origin_rejects_infeasible_split`
(refuses infeasible split geometry rather than fabricating folds). The
real-fat-tail twin `test_rolling_origin_runs_and_selects_grid_member` re-runs the
success path on the ES slice but is data-gated and skips on any fresh clone, so
it is not relied on for the fresh-clone D2 coverage.

## D3 — single-period ruin barrier and the `-inf` convention

The wealth multiplier `1 + f b* R_i` stays positive for every positive-weight
atom iff

```
f < f_max = -1 / (b* min_i R_i)                                        (D3)
```

when a losing bar exists (`min_i b* R_i < 0`); with no adverse bet the barrier
is `+infinity`. At `f >= f_max` some multiplier is `<= 0`: a single bar wipes
out (or overshoots) the stake and `log(1 + f b* R_i)` is `-infinity`. The frozen
convention is **`g(f) = -inf`** at and beyond the barrier — the outcome has
positive probability and represents true ruin. Capping the multiplier at a
positive floor to keep `g` finite is **rejected** (see D5); the barrier is a
hard feature of the geometry, not a numerical nuisance.

Per grid point the estimator reports the **distance to barrier** `f_max - f` and
the **single-bar ruin probability** `P(1 + f b* R <= 0)` with a
stationary-bootstrap CI (D5 machinery). `effective_domain_fmax`,
`single_bar_ruin_probability`, and `bootstrap_single_bar_ruin` implement these.

**Reproduced by:** `test_effective_domain_fmax_closed_form`,
`test_fmax_infinite_without_losing_bar`,
`test_absorbing_barrier_inf_propagation`,
`test_bootstrap_single_bar_ruin_point_and_ci`,
`test_single_bar_ruin_zero_below_barrier`.

## D4 — multi-period over-betting zero-growth crossing `f_0`

Because `g` is concave with its interior max at `f = 1` (`g(1) > 0`) and
`g(f) -> -infinity` as `f -> f_max`, it crosses zero exactly once in the
over-betting region at some `f_0 in (1, f_max)`. For **thin-tailed** small bets
(the diffusion / Gaussian limit) the growth is
`g(f) ~ f b* mu - (1/2) f^2 b*^2 sigma^2`, whose positive root is `f_0 = 2` —
**twice Kelly gives zero growth** (Thorp 2006). Fat tails push `f_0` **below**
2: adverse tail bars subtract log-wealth faster than the quadratic
approximation, so the over-betting cushion is thinner than the thin-tailed
benchmark implies. `zero_growth_fraction` solves `g(f_0) = 0` for `f_0 > 1`.

**Verdict is an OUTPUT.** Whether the grid top `1.25` sits inside the
positive-growth region (`1.25 < f_0`) is an **on-ledger output**, deferred. It
must be checked against the ledger's fat-tailed `f_0`, not the `f_0 = 2`
thin-tailed benchmark: on a fat-tailed ledger `f_0` may fall toward — or below —
`1.25`, in which case the grid's top point would itself be an over-betting
zero-or-negative-growth operating point, and the swept grid's upper reach is
re-examined before any selection.

**Reproduced by:** `test_zero_growth_crossing_thin_tailed_two_times_kelly`
(Gaussian small-bet substrate returns `f_0 ~ 2`),
`test_zero_growth_crossing_above_full_kelly` (`1 < f_0 < f_max`),
`test_zero_growth_crossing_pinned_to_barrier_near_full_kelly` (near-barrier
fat-tailed regime where the barrier sits just above full Kelly: `g` stays
finite-and-positive across the whole interior and dives to `-inf` only within
float-epsilon of `f_max`, so `f_0` pins to `f_max` — the grid-top over-betting
verdict is delivered, not silently dropped as nan).

## D5 — the frozen ruin-consistent estimator

The frozen **primary** growth estimator is the **absorbing barrier**:

- Any positive-weight atom with `1 + f b* R_i <= 0` sends the mean log-growth to
  `-infinity`; a bootstrap **path** that hits the barrier is **dead** (wealth is
  absorbed at zero, all subsequent bars irrelevant). `growth_rate(...,
  barrier="absorbing")` implements this on the measure; path-level ruin is the
  event that any bar in a resample breaches.
- **`P(ruin)` is a first-class reported object** (not a footnote): single-bar
  ruin probability with a stationary-bootstrap percentile CI, per grid point.
- The **Busseti, Ryu & Boyd (2016) drawdown bound** is reported: for a drawdown
  fraction `a in (0,1)` and probability `b in (0,1)` with `lambda = log b /
  log a`, `E[W^{-lambda}] <= 1` implies `Prob(W_min < a) < b` (with
  `W = 1 + f b* R`). `drawdown_probability_bound` returns the largest certified
  bound by solving `E[W^{-lambda*}] = 1` for the risk exponent `lambda* > 0`
  and reporting `a^{lambda*}`. At full Kelly the exponent is exactly `1` (the
  Kelly self-financing property `E[W^{-1}] = 1`), so `P(wealth ever halves) <=
  0.5`; under-betting raises the exponent and tightens the bound.
- **CIs** use the project stationary bootstrap (Politis & Romano 1994) with the
  automatic block length of Politis & White (2004) as corrected by Patton,
  Politis & White (2009), reused from
  [bootstrap.py](../../src/skie_universe2/inference/bootstrap.py) — no
  re-implementation.

**Capping is rejected as the primary estimator and kept ONLY as a labelled
sensitivity.** Capping floors the wealth multiplier at a small positive
`cap_floor` so the log is finite instead of `-inf`. This **biases `g`-hat
UPWARD at the leveraged grid points** (`f in {1.0, 1.25}`): it replaces genuine
ruin (`-inf`) with a survivable finite loss, **manufacturing survivable
over-betting** on a fat-tailed measure where the leveraged points are precisely
where ruin mass concentrates. Under the ADR-0013 leverage mandate this is not a
harmless approximation — it fabricates compounded edge exactly where an overfit
champion would ruin. The `cap_floor` is moreover **deliberately arbitrary**
(capping has no canonical floor); that arbitrariness is itself the
methodological argument against it. Capping is retained only for sensitivity
reporting, guarded by a unit test that the **cap-minus-absorbing gap widens
monotonically in `f`** — the signature of the upward leverage bias.

**Reproduced by:** `test_full_kelly_drawdown_exponent_is_one`,
`test_fractional_kelly_has_larger_drawdown_exponent`,
`test_capping_finite_where_absorbing_infinite`,
`test_cap_minus_absorbing_gap_monotone_in_f`,
`test_absorbing_finite_below_barrier`.

## Appendix — zero-magic-number register

Every tunable is a named constant or a documented function default with a
cited/derived rationale (CLAUDE.md Parameter Selection). None is hand-tuned to
the geometric-growth objective; the on-ledger instantiation registers the exact
operating values with the backfill.

| Tunable | Symbol / default | Source / rationale |
|---|---|---|
| Kelly-fraction grid | `KELLY_FRACTION_GRID = (0.5, 0.75, 1.0, 1.25)` | ADR-0013 Decision 3 registered sweep. |
| Bootstrap replications | `DEFAULT_N_BOOTSTRAP = 2000` | H900 §8 / SKIE-Universe 1.0 H052a replication convention for the stationary bootstrap (Politis & Romano 1994). |
| CI level | `DEFAULT_CI_ALPHA = 0.05` | Two-sided nominal 95% coverage (reporting convention). |
| Block length | auto | Politis & White (2004), Patton-Politis-White (2009) correction, via `bootstrap.choose_block_length` — data-derived, no free parameter. |
| Embargo | `DEFAULT_EMBARGO_FRACTION = 0.01` | López de Prado (2018) §7.4, ~1% of sample. |
| Purge | `purge` (default `0`) | Return-label horizon minus one; `0` for a one-bar return (no look-ahead). Named parameter. |
| Walk-forward warm-up | `DEFAULT_MIN_TRAIN_FRACTION = 0.5` | Evaluation-design choice; registered per-ledger, not tuned to growth. |
| Walk-forward folds | `DEFAULT_N_SPLITS = 5` | Evaluation-design choice; registered per-ledger, not tuned. |
| Root-search brackets | `_BARRIER_BRACKET_SHRINK`, `_MAX_BRACKET_DOUBLINGS`, `_MIN_FIT_BARS` | Numerical solver guards (stay strictly inside the effective domain; bound pathological searches; minimum bars to fit an interior optimum) — not statistical parameters. |
| Cap floor | `DEFAULT_CAP_FLOOR = 1e-4` | **SENSITIVITY ONLY**; deliberately arbitrary (capping has no canonical floor — the reason it is rejected as primary). Never used by the absorbing estimator. |

## References

1. Kelly, J. L. Jr. 1956. "A New Interpretation of Information Rate." *Bell
   System Technical Journal* 35(4): 917-926.
   https://doi.org/10.1002/j.1538-7305.1956.tb03809.x
2. Breiman, L. 1961. "Optimal Gambling Systems for Favorable Games." *Proc.
   Fourth Berkeley Symposium on Mathematical Statistics and Probability*,
   Vol. 1, pp. 65-78. University of California Press.
3. Algoet, P. H. & Cover, T. M. 1988. "Asymptotic Optimality and Asymptotic
   Equipartition Properties of Log-Optimum Investment." *Annals of Probability*
   16(2): 876-898. https://doi.org/10.1214/aop/1176991793
4. Cover, T. M. & Thomas, J. A. 2005. *Elements of Information Theory* (2nd
   ed.), ch. 6 & 16. Wiley. https://doi.org/10.1002/047174882X
5. MacLean, L. C., Ziemba, W. T. & Blazenko, G. 1992. "Growth Versus Security in
   Dynamic Investment Analysis." *Management Science* 38(11): 1562-1585.
   https://doi.org/10.1287/mnsc.38.11.1562
6. MacLean, L. C., Thorp, E. O. & Ziemba, W. T. 2010. "Long-term capital growth:
   the good and bad properties of the Kelly and fractional Kelly criteria."
   *Quantitative Finance* 10(7): 681-687.
   https://doi.org/10.1080/14697688.2010.506108
7. MacLean, L. C., Thorp, E. O. & Ziemba, W. T. (eds.) 2011. *The Kelly Capital
   Growth Investment Criterion: Theory and Practice.* World Scientific.
   https://doi.org/10.1142/7598 — edited volume; any NUMERIC claim (e.g. a
   half-Kelly operating point) must be pinned to the specific contributed
   chapter, not this volume DOI. No numeric claim in this memo relies on it.
8. Thorp, E. O. 2006. "The Kelly Criterion in Blackjack, Sports Betting, and the
   Stock Market." In *Handbook of Asset and Liability Management*, Vol. 1,
   ch. 9, pp. 385-428. Elsevier. https://doi.org/10.1016/S1872-0978(06)01009-X
9. Chopra, V. K. & Ziemba, W. T. 1993. "The Effect of Errors in Means,
   Variances, and Covariances on Optimal Portfolio Choice." *Journal of
   Portfolio Management* 19(2): 6-11. https://doi.org/10.3905/jpm.1993.409440
10. Rujeerapaiboon, N., Kuhn, D. & Wiesemann, W. 2016. "Robust Growth-Optimal
    Portfolios." *Management Science* 62(7): 2090-2109.
    https://doi.org/10.1287/mnsc.2015.2228 — cited for the **conservatism
    direction** (the robust reformulation yields a materially lower-leverage
    growth-optimal allocation than nominal plug-in Kelly), not as a strict
    scalar inequality.
11. Busseti, E., Ryu, E. K. & Boyd, S. 2016. "Risk-Constrained Kelly Gambling."
    *Journal of Investing* 25(3): 118-134.
    https://doi.org/10.3905/joi.2016.25.3.118 — drawdown bound: for
    `a, b in (0,1)`, `lambda = log b / log a`, `E[(r_T)^{-lambda}] <= 1`
    implies `Prob(W_min < a) < b`.
12. Politis, D. N. & Romano, J. P. 1994. "The Stationary Bootstrap." *JASA*
    89(428): 1303-1313. https://doi.org/10.1080/01621459.1994.10476870
13. Politis, D. N. & White, H. 2004. "Automatic Block-Length Selection for the
    Dependent Bootstrap." *Econometric Reviews* 23(1): 53-70.
    https://doi.org/10.1081/ETC-120028836
14. Patton, A., Politis, D. N. & White, H. 2009. "Correction to 'Automatic
    Block-Length Selection for the Dependent Bootstrap'." *Econometric Reviews*
    28(4): 372-375. https://doi.org/10.1080/07474930802459016

Supporting (estimator provenance, not a primary-derivation source): López de
Prado, M. 2018. *Advances in Financial Machine Learning*, ch. 7 (purged /
embargoed cross-validation). Wiley.


## Numeric instantiation addendum (2026-07-17) — on-ledger outputs

**Status:** NUMERIC INSTANTIATED, RECORD ONLY. Harness
[scripts/run_kelly_growth_calibration.py](../../scripts/run_kelly_growth_calibration.py)
(seed 20260717, N_bootstrap 2000), ReproLog
`repro_log_d371b253d6be47e596ea0aa99182801e.json` (round-1-remediated rerun; numerically identical to the initial run e246363134df410c8e25ddfaf9145e17 — the pipeline is deterministic at the registered seed), machine artifact
[reports/kelly_growth_calibration/kelly_growth_calibration.json](../../reports/kelly_growth_calibration/kelly_growth_calibration.json).
Substrate: per-SESSION return streams of `orb_first_hour_k1.0@1.0.0` (ES+NQ;
sessions are the expert's compounding atoms — one round-trip per session,
flat overnight), NET primary / GROSS sensitivity.

### B.1 D1-D5 outputs per stream

| Stream | b* | f_max | f_0 | f**_oos | g(f) x1e5 at {0.5,0.75,1.0,1.25} | P(ruin) [CI] all f |
|---|---:|---:|---:|---:|---|---|
| ES/net | **0 (degenerate)** | - | - | - | - (no favourable bet; mean -1.14e-4/session) | - |
| ES/gross | 1.337 | 7.56 | 1.982 | 0.5 | 3.33, 4.17, 4.45, 4.16 | 0 [0, 0] |
| NQ/net | 1.696 | 8.16 | 1.990 | 1.25 | 7.72, 9.65, 10.3, 9.65 | 0 [0, 0] |
| NQ/gross | 2.684 | 5.16 | 1.978 | 1.25 | 19.5, 24.4, 26.1, 24.4 | 0 [0, 0] |

- **Concavity/interior-max (D1) EXHIBITED on-ledger:** every non-degenerate
  in-sample curve peaks exactly at f = 1.0 with `g''(f) < 0` at all four grid
  points (analytic second derivative -8.8e-5 .. -5.4e-4).
- **Ruin handling (D3/D5) EXHIBITED:** the absorbing-barrier estimator ran
  with zero single-bar ruin mass at every grid point (stationary-bootstrap
  95% CIs [0, 0]; distance-to-barrier >= 3.9 fractions everywhere); the
  Busseti-Ryu-Boyd bound at f = 1.0 returns exponent 1 exactly (prob_bound
  0.050 at the 0.05 drawdown level — the Kelly self-financing property), and
  the leveraged point (1.25) carries bound ~0.167.
- **Over-betting crossing (D4):** f_0 = 1.978-1.990 vs the thin-tailed
  benchmark 2.0 — the session-level substrate is only mildly fat-tailed at
  these leverages, and the grid top 1.25 < f_0 on every non-degenerate stream
  (the 1.25 point sits inside the positive-growth region **in sample**).
- **ES/net is DEGENERATE:** the realizable (post-cost) ES stream has no
  favourable bet (E[R] < 0) — `full_kelly_leverage` = 0 and the D1-D5 report
  is undefined. This is the honest on-ledger answer for a null expert.

### B.2 D2 estimation-adjusted OOS optimum

Frozen purged/embargoed expanding walk-forward (5 folds, 1% embargo, purge 0,
50% warm-up): the OOS argmax lands at the grid **floor** on ES/gross (0.5;
OOS growth negative beyond it — the Chopra-Ziemba shrinkage manifest) and at
the grid **top** on NQ/net and NQ/gross (1.25). The stationary-bootstrap 95%
CIs on g(f) **include zero at every fraction on every stream** (no-favourable-
bet resamples: 666/2000 ES-gross, 528 NQ-net, 316 NQ-gross) — no fraction's
growth is distinguishable from nothing on this substrate. Note (audit
QUANT-1-8): the CI's zero lower bound is partly MECHANICAL — the registered
policy assigns g = 0 to a no-favourable-bet resample, so whenever the no-bet
mass exceeds alpha/2 (it does on every stream) the lower bound is pinned at 0
by the imputation and cannot exhibit negative mass; the policy is recorded in
the artifact and the across-fold OOS curves (which DO go negative on
ES/gross) carry the sign information.

### B.2b Artifact provenance note

The frozen estimator stamps each per-stream report with its default
"deferred to the step-4 backfill" note; the artifact retains that string
under `notes_frozen_estimator_default` for traceability and carries the
superseding note ("this artifact IS the deferred on-ledger instantiation")
in `notes` (audit QUANT-1-7/REPRODUCIBILITY-1-2; the frozen module is
untouched).

### B.3 Grid-bracketing verdict — INCONCLUSIVE-ON-NULL-LEDGER

The registered question ("does {0.5, 0.75, 1.0, 1.25} bracket the
estimation-adjusted optimum?") receives: **in-sample, trivially yes** (the
interior max sits at f = 1.0 by construction and the curve is concave); **out
of sample, not resolvable** — the OOS argmax pins to opposite grid edges on
different streams and every growth CI includes zero, because the only ledger
expert is a null (RC-H101-1/RC-H103-1). A bracketing verdict on a no-edge
stream carries no information about the bracketing behaviour on a real edge.
The verdict is recorded as **inconclusive-on-null-ledger**, and
**re-instantiation on the first admitted (true-edge) expert stream is a
registered standing condition** of this addendum — the same condition as the
discovery-alpha addendum §A.8. No grid adjustment is made (none is supported
by evidence), and NO Kelly fraction is selected (Phase-4 champion action;
additionally blocked on arsenal >= 1).
