---
name: ADR-0013 — Aggressive geometric-growth mandate
description: Reframes SKIE-Universe 2.0 from risk-averse tail protection to optimism + compounded geometric growth; installs Kelly log-wealth as the primary objective, sweeps the Kelly fraction as a registered hyperparameter {0.5, 0.75, 1.0, 1.25}, demotes the lower-tail terminal-wealth quantile to a monitored non-binding guardrail, cost-tunes the discovery alpha looser, loosens ADR-0002 admission, steepens the ADR-0010 ramp — and reaffirms the overfitting/integrity core as non-waivable and more binding under leverage
type: governance
status: proposed
date: 2026-07-12
supersedes: ""
superseded_by: ""
---

# ADR-0013 — Aggressive geometric-growth mandate

## Context

The ten founding ADRs (0001–0010) plus the data-provenance ADR-0011 were
written under a risk-averse capital posture: the binding decision metric was a
lower-tail terminal-wealth quantile (ADR-0004 Decision 4; ADR-0005 Decision 2),
the Kelly fraction was capped "strictly below 1" by fiat (ADR-0005 Decision 2,
Alternatives), the discovery error-rate target was set for strict
false-discovery avoidance (ADR-0002(c); ADR-0007 Decision 3), admission was held
conservative by risk-adjusted (Information-Ratio) redundancy screening (ADR-0002(d)),
and the live-capital ramp started at one micro-unit with a deliberately gentle,
weeks-to-months increment (ADR-0010). That posture minimizes the left tail at
the cost of forgone compounding.

The principal has directed (2026-07-12) a philosophy shift: SKIE-Universe 2.0 is
reframed from risk-averse to **optimism + exponential (compounded) growth via a
high-risk methodology**. The reframe changes **risk appetite and discovery
only** — it does **not** touch the overfitting/integrity core. Under a
compounded (geometric) objective the loss function is asymmetric in the
direction opposite to the founding assumption: a **missed** true conditional
edge forgoes compounding and is effectively unrecoverable, whereas a **false**
admission is caught downstream by the non-waivable Deflated-Sharpe / PBO
overfitting-detection gates (ADR-0007 Decision 3) and the matched-turnover
random rotor (ADR-0007 Decision 4). The founding ADRs did not encode that
asymmetry; this keystone ADR does.

The reframe is disciplined, not reckless. Growth-optimal betting is the Kelly
criterion ([Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x)),
whose modern treatment under estimation error, drawdown constraints, and
fractional sizing is
[MacLean, Thorp & Ziemba 2011](https://doi.org/10.1142/7598) (the edited volume
collecting the Kelly capital-growth literature, incl. Thorp's applied work). The geometric-growth metric penalizes
over-betting **in expectation**: under **standard (thin-tailed, single-period)
assumptions** expected log-wealth is concave in the leverage fraction with an
interior maximum, so a fraction above the growth optimum loses on the metric's
own merits. That concavity, the location of the interior maximum, and the
claim that the swept grid brackets that optimum are **assertions to be
derived/exhibited on the shadow-ledger multi-period, fat-tailed distribution**
(with CIs, and explicit ruin handling: a realized `1 + f·R ≤ 0` yields **−∞**
geometric growth, correctly rejecting that fraction) **before** any swept scan
selects a fraction on best geometric growth — the derivation cannot be assumed,
because at leverage (e.g. f = 1.25) a single fat-tailed bar with `1 + f·R ≤ 0`
is ruin and log-wealth is undefined. This is registered as the blocking
follow-up `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` (Decision 9). The single
most important safeguard the mandate reaffirms: at
leverage/compounding an overfit champion does **not** merely underperform — it
**ruins** (negative geometric growth on a fake edge). The overfitting gates
therefore protect the very compounded returns they are being levered into.
Aggressive on sizing and discovery; ruthless about not deploying fake edges.

This ADR is **status: proposed**. It is a draft for review before enactment; no
downstream ADR is edited in place until this ADR is accepted. On acceptance, the
amendments in the map below are applied to the named ADRs (each amendment is
itself STATUS: proposed until then), and this ADR stands as the governing record
of the reframe.

## Decision

1. **Philosophy shift declared.** SKIE-Universe 2.0's capital posture is
   optimism + exponential (compounded geometric) growth pursued through a
   high-risk methodology. The reframe alters **risk appetite** (sizing, tail
   posture) and **discovery** (error-rate budget, admission bar, escalation
   speed). It does **not** alter the overfitting-detection or integrity core
   (Decision 8). Every change below is a re-parameterization, an
   objective-swap, or — where the registered cost analysis supports it — a
   change of error-control **criterion** (the ADR-0007 identification step may
   move from FWER to FDR / Benjamini-Hochberg, a strictly weaker guarantee, not
   merely a looser level); no correction machinery, canary, register, or ledger
   is removed, and enacting BH requires its PRDS / Benjamini-Yekutieli
   justification (config `prds_argument_ref`) first.

2. **Primary objective: geometric (compounded) growth.** The primary
   decision/ranking metric across the program becomes **geometric growth =
   mean log-wealth growth rate = the Kelly-optimal growth rate**
   ([Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x);
   Thorp; [MacLean, Thorp & Ziemba 2011](https://doi.org/10.1142/7598)). It
   replaces the lower-tail terminal-wealth quantile as the PRIMARY metric
   everywhere that quantile was primary/binding (ADR-0004 Decision 4; ADR-0005
   Decision 2; inherited into the ADR-0007 confirmation-ladder adjudication).
   Geometric growth is computed on the shadow ledger (ADR-0003) under the same
   stationary-bootstrap resampling and automatic block length already mandated
   for the demoted quantile (ADR-0004 Decision 4:
   [Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870);
   [Politis & White 2004](https://doi.org/10.1081/ETC-120028836)), so the
   inference machinery now produces confidence intervals on the new primary
   metric and on the demoted guardrail alike.

3. **Kelly fraction is a registered swept hyperparameter.** The position-layer
   Kelly multiplier (ADR-0005 Decision 2) is no longer capped below 1 by fiat.
   It becomes a **registered hyperparameter swept over the grid {0.5
   (half, the [MacLean, Thorp & Ziemba 2011](https://doi.org/10.1142/7598)
   estimation-error shrink point), 0.75 (three-quarter), 1.0 (full), 1.25
   (leveraged, >1)}**. The grid brackets the estimation-error-adjusted
   geometric-growth optimum — from half-Kelly through leveraged — so the
   data-selected winner is **not structurally floored above the growth
   optimum**. Results are reported for **all** fractions; selection is by
   **best geometric growth over the joint (allocator-config × Kelly-fraction)
   space**. The grid endpoints and 0.25 spacing are a **pre-registered sweep
   whose FINAL values are an OUTPUT of the registered calibration follow-up**
   (Decision 9: `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` /
   `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`, which confirm or adjust that
   {0.5, 0.75, 1.0, 1.25} brackets the shadow-ledger geometric-growth
   optimum), not asserted here and not hand-tuned constants (a hyperparameter
   search per the zero-magic-number rule); the winning fraction is
   data-selected. Over-betting is penalized **in expectation** (Context); that
   the metric rejects an unjustified >1× fraction on the shadow-ledger
   multi-period fat-tailed distribution — including the ruin case
   `1 + f·R ≤ 0 → −∞` — is **to be exhibited** by the concavity/ruin memo
   before any swept scan selects on geometric growth, not assumed. This sweep
   is a **pre-registered position-layer search evaluated
   against the position layer's own geometric-growth objective** — it is
   therefore **not** cross-layer tuning under ADR-0005 Decision 4 (it does not
   raise the fraction to repair a signal-layer weakness).

4. **Multiplicity carries the Kelly dimension.** The Kelly-fraction sweep
   **expands the multiple-testing family**: every **(config × Kelly-fraction)
   pair is one trial**, carried in the ADR-0008 family-wise trial register and
   covered by the ADR-0007 SPA/StepM correction over the enlarged family. The
   SPA existence test
   ([Hansen 2005](https://doi.org/10.1198/073500105000000063)), the Romano-Wolf
   StepM identification
   ([Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x)), and
   the intersection-union across all five benchmark rungs are unchanged in
   structure; the loss differentials they consume are re-defined on geometric
   growth. Expanding the family is a strictly **more conservative** correction:
   aggressive sizing is paid for by honest accounting, never exempted from it.

5. **Lower-tail terminal-wealth quantile demoted to a monitored,
   non-binding guardrail.** The lower-tail terminal-wealth quantile (ADR-0004
   Decision 4; ADR-0005 Decision 2, bullets 2–3 and Consequences) is
   **demoted from primary/binding to a monitored, non-binding guardrail**. It
   is still computed at the same bootstrap and block length, still reported as a
   time series, and its registered level and horizon-T declaration are retained
   — but bound to the guardrail, not to the deployment decision. The guardrail
   **informs, it does not veto**. Regret, turnover-adjusted net edge, detection
   latency, and regime dwell (ADR-0004 Decision 4) likewise remain **reported
   diagnostics**, not decision metrics.

6. **Discovery alpha cost-tuned looser (registered follow-up).** The discovery
   error-rate budget — the ADR-0002(c) screening error-rate target and the
   ADR-0007 confirmation FWER — is **cost-tuned looser** (a higher tolerated
   false-discovery rate) via an **explicit registered error-rate-cost analysis**
   weighing the expected cost of a **missed** true edge at target compounded
   return against the cost of a **false** discovery. The alpha level is the
   **output** of that analysis (zero-magic-number: never a hard-coded
   constant). Where the cost analysis supports it, **FDR control
   ([Benjamini & Hochberg 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x))
   may replace strict FWER** for the StepM identification step. This is a change
   of error-control **criterion** (FWER → FDR is a strictly **weaker
   guarantee**), not merely a looser level: enacting BH requires its **PRDS
   ([Benjamini & Yekutieli 2001](https://doi.org/10.1214/aos/1013699998))**
   dependency justification — config `prds_argument_ref` must be satisfied
   (non-null), otherwise Benjamini-Yekutieli is used — before BH is enacted.
   The correction **machinery** — Romano-Wolf StepM, block/stationary
   bootstrap, BH-with-PRDS or Benjamini-Yekutieli, per-family registration in
   `config/multipletest_family.yaml` — is untouched; what moves is the
   registered target **and, where justified, the error-control criterion**.
   This calibration is registered as follow-up
   **`P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`** (Decision 9).

7. **Admission loosened (ADR-0002) and ramp steepened (ADR-0010).**
   - ADR-0002 admission is made **more permissive** — the conditional-edge +
     non-redundancy structure stays, but (c)'s screening target loosens per
     Decision 6 and (d)'s redundancy test is re-expressed on marginal
     **log-wealth growth** contribution (the Information-Ratio / ensemble-variance
     view demoted to a monitored guardrail). The (a) leakage-canary and (b)
     frozen-conditioning-set gates stay binding.
   - ADR-0010 escalation is **steepened for a proven champion**: the initial
     tranche and per-promotion increment scale with the **overfitting-detection
     margin** (DSR effect size, 1−PBO) and the geometric-growth estimate across
     the Kelly grid, replacing the flat one-micro-unit floor. The initial lift
     is bounded by the **overfitting-detection margin, never by a raw
     backtest-Kelly point estimate** (that alternative stays rejected). All
     earn-by-live-measurement machinery (TOST tracking gate, CUSUM demotion,
     prohibited accelerants) is retained; only α/δ/power and the size increment
     are cost-re-weighted and steepened.

8. **Non-waivable overfitting/integrity core (REAFFIRMED — more binding under
   leverage).** The following are **non-waivable** and are made **more**
   important by this mandate, not less. At leverage/compounding an overfit
   champion drives **negative geometric growth (ruin)** on a fake edge rather
   than merely underperforming; these gates protect the compounded returns the
   program is levering into and are the **backstop that licenses** the looser
   admission screen and the steeper ramp:
   - **Deflated Sharpe** overfitting-detection
     ([Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094)),
     computed from the effective number of independent trials and cross-trial
     Sharpe variance estimated from the register's per-trial records.
   - **PBO** exhibit via combinatorially symmetric cross-validation
     ([Bailey, Borwein, López de Prado & Zhu 2017](https://doi.org/10.21314/JCF.2016.322)).
   - **Matched-turnover random rotor** (ADR-0007 Decision 4, Benchmark 5): the
     direct control that **selection adds value beyond churn**. The looser
     admission bar inflates N, which makes this rotor the load-bearing guard
     against admitting rotor-indistinguishable noise experts.
   - **PIT canaries, pre-registered scans, family-wise trial register (now
     including the Kelly-fraction dimension), burned-data ledger, ReproLog**
     (ADR-0008).
   - **Shadow ledger** as the sole evidence source (ADR-0003).
   The correction machinery of ADR-0007 (SPA/StepM, DSR, PBO) is **not** the
   rejected "drop-SPA/DSR optimistic paradigm" alternative: 2.0 loosens the
   discovery **alpha** and swaps the **objective** to geometric growth, but
   **keeps** SPA/StepM/DSR/PBO and the rotor.

9. **Calibration follow-ups registered.** Two open follow-ups are registered.
   - **`P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`**: a methodology memo
     performing the error-rate-cost analysis that (i) sets the loosened
     screening/FWER target (Decision 6), (ii) fixes the FWER-vs-FDR choice for
     the StepM identification step (and, if BH, satisfies the
     `prds_argument_ref` PRDS/Benjamini-Yekutieli obligation), (iii) sets the
     ADR-0010 TOST α/δ/power re-weighting and the steepened size increment
     (Decision 7), and (iv) **confirms or adjusts the Kelly grid endpoints and
     0.25 spacing** — the final {0.5, 0.75, 1.0, 1.25} values are an **output**
     of this calibration (that they bracket the shadow-ledger
     geometric-growth optimum), not asserted (Decision 3).
   - **`P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`** (**BLOCKING**): a
     methodology memo that **derives/exhibits, with CIs, on the shadow-ledger
     multi-period fat-tailed distribution** (not the standard thin-tailed
     single-period model) both the **interior maximum** of expected log-wealth
     in the Kelly fraction and the **grid's bracketing of that optimum**, with
     **explicit ruin handling** (a realized `1 + f·R ≤ 0` yields **−∞**
     geometric growth, correctly rejecting that fraction).
   Both are **registered follow-ups, not hard-coded values**; no loosened
   target is enacted before its memo is frozen and its ReproLog emitted, and
   **no swept fraction is selected on geometric growth before the concavity/ruin
   memo is frozen + ReproLog emitted**.

## Amendment map

Per-ADR, which numbered decision changes and to what. Every amendment is
STATUS: proposed and preserves the overfitting-detection/integrity core; only
risk-appetite and discovery parameters move. Structure (gates, machinery,
register, ledger) is retained throughout.

| ADR | Decision / clause | Current (risk-averse) | Amended (aggressive) | Integrity kept |
|---|---|---|---|---|
| ADR-0002 | (c) Conditional gross edge — screening error-rate target | Symmetric/conservative error-rate-cost analysis; target implicitly tight | Re-parameterize the loss to weight a **missed** true edge (forgone compounding, unrecoverable) above a **false** admission (backstopped by DSR/PBO + rotor); target tuned **looser** (higher tolerated FDR), value still derived from the documented cost analysis | Romano-Wolf/block-bootstrap/BH-PRDS-or-BY machinery and per-family registration untouched; only the registered **target** moves; every (config × Kelly-fraction) trial enters the same corrected family |
| ADR-0002 | (d) Non-redundancy | Marginal contribution ranked by **Information Ratio**; "ensemble-variance budget" (variance-minimizing) | Re-express marginal-contribution test as marginal contribution to **compounded log-wealth growth**; admit if positive marginal log-growth **or** residual correlation below a data-derived bound; IR / ensemble-variance view **demoted to a monitored guardrail** | Non-redundancy **requirement** retained (stops the arsenal becoming an unaccounted multiple-testing engine); bound still derived from arsenal covariance, never a fixed constant |
| ADR-0002 | Admission conjunction (a)–(d) + "not required" list | Effective bar held conservative by (c) target and (d) IR bound; no explicit aggressive posture stated | State the **aggressive posture explicitly**: conjunction retained but deliberately more permissive via looser (c) and growth-based (d); (a) interface/leakage-canary and (b) frozen conditioning set stay **binding** | Trial-register increment on every scan must reconcile with the mandate-expanded (config × Kelly-fraction) family; aggressive inclusion does **not** relax multiplicity accounting |
| ADR-0004 | Front-matter `description` (metric headline) | Headlines "…registered lower-tail terminal-wealth quantile as the primary metric family" | Rewrite so the **primary/ranking metric is geometric (compounded) growth = Kelly-optimal log-wealth growth**, reported across the (config × Kelly-fraction) grid; lower-tail quantile listed among monitored guardrails | Metric family still reported as a time series; nothing removed |
| ADR-0004 | Decision 4 — primary metric family (terminal-wealth lower-tail quantile) | Lower-tail terminal-wealth quantile is the **binding** wealth objective (level per ADR-0005) | Add **geometric growth** as the **LEAD** decision/ranking bullet, computed at each Kelly fraction {0.5, 0.75, 1.0, 1.25}; winner data-selected by best geometric growth over the joint space; relabel the quantile a **monitored, non-binding guardrail** (same bootstrap/block length, still reported) | Stationary-bootstrap resampling, automatic block length, Sharpe CIs all retained — now also producing CIs on the new primary metric; each (config × fraction) pair is a registered trial under ADR-0007 correction |
| ADR-0004 | Decision 3 — refit-cadence selection objective | Cadence selected by nested rolling-origin CV on **out-of-window regret** (benchmark-tracking) | Keep the nested-CV selection machinery (anti-overfit, no hand-set cadence) but change the selection objective to **out-of-window geometric (log-wealth) growth**; regret retained as a secondary reported diagnostic | Nested rolling-origin CV, prohibition of hand-set cadence, zero-magic-number all retained; only the objective is reframed |
| ADR-0005 | Decision 2 bullet 1 — fractional Kelly under hard drawdown constraint | Fraction "strictly below 1" by fiat; selected on the **drawdown/ruin bootstrap**; half-Kelly prior | Fraction is a **registered swept hyperparameter {0.5, 0.75, 1.0, 1.25}** (endpoints/0.25 spacing an **output** of the calibration follow-up confirming the grid brackets the shadow-ledger geometric-growth optimum from the half-Kelly MTZ shrink point through leveraged, not asserted), reported for all; selection by **best geometric growth** over the joint space (only after the concavity/ruin memo is frozen); drawdown/ruin bootstrap **demoted to a monitored guardrail**; MTZ estimation-error point re-purposed as the reason the growth metric + DSR/PBO matter, not a reason to cap <1 | Shadow-ledger sourcing unchanged; every (config × fraction) pair is a registered trial under ADR-0007 correction |
| ADR-0005 | Decision 2 bullet 3 — binding lower-tail terminal-wealth quantile | The **single most conservative** clause: lower-tail quantile is THE binding decision metric, peaks below full Kelly | **Demote** to a monitored, non-binding guardrail (still computed, still reported, level/horizon sweep retained); **primary metric becomes geometric growth**; registered horizon-T/quantile-level bound to the guardrail, not the deployment decision | Registered horizon-T and quantile-level declaration retained (bound to guardrail) |
| ADR-0005 | Decision 2 bullet 2 — pyramiding consequences reporting metric | Pyramiding consequences scored in **lower-tail-quantile** terms | Report pyramiding consequences **primarily in geometric-growth terms**, quantile carried as guardrail; pyramiding schedules enter the swept position-policy space and the ADR-0008 register / ADR-0007 correction | Pyramiding **gate**, pre-registration as its own hypothesis, and "exhibit the skew/tail interaction, never assume benign" requirement all retained unchanged |
| ADR-0005 | Consequences bullet 1 — audit bar for "exponential growth" claims | Claims must survive **lower-tail-quantile accounting** | Claims must survive **geometric-growth accounting PLUS the non-waivable overfitting gates** (DSR + PBO + rotor); quantile reported as guardrail | Auditability preserved (still not the backtest median); objective flips from tail-safety to compounded growth |
| ADR-0005 | Alternatives — "Full Kelly. Rejected." | Full and leveraged Kelly rejected a priori; ruin risk treated as dominant before any data | **Remove the a-priori rejection**: 1.0 and 1.25 are **registered points in the sweep**, data-selected by geometric growth (over-betting penalized **in expectation**; the interior-maximum/ruin behaviour to be exhibited by the concavity/ruin memo before selection); MTZ argument re-cast as why the overfitting core is **more** important at leverage | DSR+PBO, rotor, and ADR-0008 core non-waivable at these fractions; over-betting penalized in expectation on the metric, not by fiat |
| ADR-0007 | Decision 2 — confirmation-ladder adjudication metric | "Beat the ladder" adjudicated on ADR-0004's **lower-tail-quantile** primary | Re-anchor "beat the ladder" to **geometric growth** as the primary ranking/decision metric against every rung; quantile demoted to a monitored guardrail reported alongside each pass | Full five-rung ladder, net-of-cost, switching-cost inclusion, intersection-union all retained; only the scalar changes |
| ADR-0007 | Decision 3 — SPA/StepM family definition | Family = allocator-**configuration** set only; omits the sizing dimension | Redefine the family as every **(config × Kelly-fraction) pair** over {0.5, 0.75, 1.0, 1.25}; loss differentials defined on **geometric growth**; strictly **more conservative** (larger family) | SPA existence test, StepM identification, intersection-union across all five benchmarks, register increment all retained |
| ADR-0007 | Decision 1 & 3 — discovery alpha (screening target + confirmation FWER) | Set for strict false-discovery avoidance (FP treated as dominant cost) | **Cost-tune looser** via registered error-rate-cost analysis (missed-edge cost vs false-discovery cost); permit **FDR (BH)** for identification where the cost analysis supports it — a change of error-control **criterion** (FWER → FDR, a strictly **weaker guarantee**), not merely a looser level; alpha is the **output**, not a constant | SPA existence test, StepM/BH identification, intersection-union, register increment all retained; the alpha **level** and, where justified, the error-control **criterion** move — enacting BH requires its PRDS / Benjamini-Yekutieli justification (config `prds_argument_ref` satisfied) first (follow-up `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`) |
| ADR-0007 | Alternatives — "Dropping SPA/DSR ('optimistic paradigm' literally)" | Rejected alternative; phrase "optimistic paradigm" risks misreading as license to drop the machinery | Retain the rejection **verbatim** and **strengthen** it: 2.0's aggressive reframe is **not** this alternative — it loosens alpha and swaps the objective but **keeps** SPA/StepM/DSR/PBO + rotor; add the leverage-ruin rationale | Correction machinery non-waivable; explicitly distinguished from the rejected paradigm |
| ADR-0007 | Decision 5 — promotion-path cross-references | Inherits conservative ADR-0002 admission and cautious ADR-0010 ramp at two stages | Keep stage **ordering** and no-skip / record-every-transition rule intact; update cross-refs to reflect looser ADR-0002 admission and steeper ADR-0010 ramp — the threshold moves live **in those ADRs**, not here | Gate **sequence** non-waivable; only thresholds inside referenced gates move |
| ADR-0010 | Decision 1 — minimum-size cap on simulation evidence | Flat one-micro-unit floor; ramp "slow by construction" regardless of margin | **Steepen for a proven champion**: initial tranche and per-promotion increment scale with the **overfitting-detection margin (DSR effect size, 1−PBO)** and the geometric-growth estimate across the Kelly grid, replacing the flat floor; initial lift bounded by the **overfitting-detection margin, never a raw backtest-Kelly point estimate** | Escalation beyond the initial tranche stays earned by live tracking (Decisions 3/4); an overstated start is rapidly demoted; every (schedule-config × fraction) pair is a registered trial |
| ADR-0010 | Decision 2 — max leverage ceiling + size increment | Binding leverage ceiling derived from the **lower-tail-quantile** constraint; implicitly gentle increment | Re-derive the ceiling from the **Kelly-optimal geometric-growth objective** across {0.5, 0.75, 1.0, 1.25} (over-betting penalized in expectation → ceiling data-selected on merit, once the concavity/ruin memo is frozen); demote the quantile-implied ceiling to a monitored guardrail; **steepen the registered size increment** | Freeze + no-mid-flight-edit pre-registration discipline retained **verbatim**; both dimensions frozen at pre-registration and carried in the register |
| ADR-0010 | Decision 3 — TOST α / power-target / δ calibration | Error-rate-cost analysis weighted so **false-promotion cost dominates** → tight α, tight δ, long windows | **Re-weight only the calibration** toward the mandate: looser α and/or wider δ toward the cost-model tolerance → shorter powered window, faster promotion; values data-selected by the registered cost analysis | TOST affirmative-tracking **structure** and power-driven window retained (the earn-by-measurement kernel); promotion still requires **positive** tracking evidence — only speed/threshold tuned |

## Consequences

- **Positive:** the program's decision metric now matches its stated objective —
  configurations are ranked by realized compounded log-wealth, not by how well
  they protect the left tail, so the highest-growth honest configuration is no
  longer structurally disfavored.
- **Positive:** the Kelly-fraction sweep is a data-driven search rather than an
  a-priori cap; full and leveraged Kelly are tested on merit, and the
  geometric-growth metric penalizes over-betting **in expectation** — its
  interior maximum, the grid's bracketing of that optimum, and the ruin
  handling (`1 + f·R ≤ 0 → −∞`) are to be **exhibited** on the shadow-ledger
  fat-tailed distribution before any swept selection, not asserted.
- **Positive:** the overfitting/integrity core is reaffirmed as the backstop
  that **licenses** the looser screen and steeper ramp — aggression on sizing
  and discovery is bought with strictly more conservative multiplicity
  accounting (the family grows by the Kelly dimension), not with weaker
  correction.
- **Negative:** the multiple-testing family expands by the Kelly-fraction
  dimension (×4 grid points), raising the correction burden and the compute cost
  of confirmation; this is the honest price of sweeping the sizing dimension.
- **Negative:** a looser discovery alpha admits more false positives at the
  screen; this is deliberate (missed compounding is the dominant cost) and is
  contained downstream by the non-waivable DSR/PBO gates and the random rotor —
  which must therefore hold their calibration under the higher N.
- **Negative:** steepening the ramp raises the stakes of an overstated start;
  the initial-lift bound (overfitting-detection margin, never a backtest-Kelly
  point estimate) and the retained CUSUM demotion are the containment.
- **Obligation:** the calibration follow-up
  `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` must be frozen (methodology
  memo + ReproLog) before any loosened target is enacted; no alpha, δ, α, power,
  size-increment value, or Kelly-grid endpoint/spacing is a hard-coded constant
  (the grid's final {0.5, 0.75, 1.0, 1.25} values are an output of this memo);
  where the memo resolves identification to BH, its PRDS / Benjamini-Yekutieli
  justification (config `prds_argument_ref`) must be satisfied before BH is
  enacted.
- **Obligation (BLOCKING):** the concavity/ruin follow-up
  `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` must be frozen (methodology memo +
  ReproLog) — deriving/exhibiting, with CIs and explicit ruin handling
  (`1 + f·R ≤ 0 → −∞`), the interior maximum and the grid's bracketing of the
  optimum on the shadow-ledger multi-period fat-tailed distribution — **before
  any swept fraction is selected on geometric growth**.
- **Obligation:** on acceptance, the amendment map is applied to ADRs
  0002/0004/0005/0007/0010 (each amendment STATUS: proposed until then); the
  ADR-0008 trial register and `config/multipletest_family.yaml` must be updated
  to carry the (config × Kelly-fraction) family before the first swept scan.
- **Obligation:** this ADR is enacted only after review; until accepted it is a
  proposed draft and no downstream ADR is edited in place.

## Alternatives considered

- **Keep the risk-averse posture (status quo).** Rejected by principal
  direction: under a compounded objective, ranking on a lower-tail quantile
  forgoes the compounding the program exists to capture, and caps the Kelly
  fraction below the growth optimum before any data is seen.
- **Drop SPA/StepM/DSR/PBO at confirmation (the literal "optimistic
  paradigm").** Rejected, and the rejection is strengthened here: the asset
  class's decades of null results are its base rate; removing the correction
  machinery manufactures false discoveries precisely when leverage makes them
  ruinous. 2.0 loosens the discovery **alpha** and swaps the **objective**, and
  **keeps** every detector.
- **Uncapped / unbounded Kelly (maximize leverage).** Rejected: **under
  standard (thin-tailed, single-period) assumptions** expected log-wealth is
  concave in the fraction with an interior optimum, so unbounded leverage lowers
  compounded growth on the metric's own terms. On the shadow-ledger
  multi-period fat-tailed distribution this concavity, the location of the
  interior optimum, and the claim that the registered grid {0.5, 0.75, 1.0,
  1.25} brackets it are **to be derived/exhibited (with CIs, and explicit ruin
  handling: a realized `1 + f·R ≤ 0` yields −∞ geometric growth, rejecting that
  fraction) by `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` before any swept
  selection** — not asserted; the winner is then data-selected.
- **Size proportional to the backtest-Kelly point estimate from day one
  (ADR-0010).** Stays rejected: it maximizes exposure at the moment of maximum
  estimation error — ruin-first under the overbetting asymmetry. The steepened
  initial lift is bounded by the overfitting-detection margin, not the point
  estimate.
- **Hand-set looser alpha / larger size increment.** Rejected: violates the
  zero-magic-number rule. All loosened targets are outputs of the registered
  error-rate-cost analysis (`P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`).

## References

- [Kelly 1956, Bell Syst. Tech. J. 35:917-926](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x)
  — the growth-optimal (log-wealth) criterion.
- [MacLean, Thorp & Ziemba 2011, *The Kelly Capital Growth Investment
  Criterion: Theory and Practice*, World Scientific](https://doi.org/10.1142/7598)
  — fractional Kelly, estimation error, drawdown-constrained growth; edited
  volume collecting the Kelly capital-growth literature (incl. Thorp's applied work).
- [Hansen 2005, J. Bus. Econ. Stat. 23:365-380](https://doi.org/10.1198/073500105000000063)
  — SPA test (confirmation-ladder existence test; family now expanded by the
  Kelly dimension).
- [Romano & Wolf 2005, Econometrica 73:1237-1282](https://doi.org/10.1111/j.1468-0262.2005.00615.x)
  — StepM FWER identification (machinery retained; alpha cost-tuned).
- [Benjamini & Hochberg 1995, J. R. Stat. Soc. B 57:289-300](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)
  — FDR control, permitted for the identification step where the cost analysis
  supports it.
- [Benjamini & Yekutieli 2001, Ann. Statist. 29(4):1165-1188](https://doi.org/10.1214/aos/1013699998)
  — FDR under dependency (PRDS) and the general-dependence correction; the
  justification obligation (`prds_argument_ref`) before enacting BH.
- [Bailey & López de Prado 2014, J. Portfolio Manage. 40(5):94-107](https://doi.org/10.3905/jpm.2014.40.5.094)
  — Deflated Sharpe; non-waivable overfitting detection.
- [Bailey, Borwein, López de Prado & Zhu 2017, J. Comput. Finance 20(4):39-69](https://doi.org/10.21314/JCF.2016.322)
  — PBO via CSCV; non-waivable overfitting detection.
- [White 2000, Econometrica 68:1097-1126](https://doi.org/10.1111/1468-0262.00152)
  — Reality Check, the data-snooping lineage this program enforces.
- [ADR-0001](ADR-0001-allocator-unit-of-inference.md),
  [ADR-0002](ADR-0002-arsenal-admission-standard.md),
  [ADR-0003](ADR-0003-shadow-ledger-canonical-object.md),
  [ADR-0004](ADR-0004-rolling-evaluation-regime.md),
  [ADR-0005](ADR-0005-three-layer-separation.md),
  [ADR-0007](ADR-0007-two-tier-discovery-pipeline.md),
  [ADR-0008](ADR-0008-integrity-non-negotiables.md),
  [ADR-0009](ADR-0009-expert-card-terminal-deliverable.md),
  [ADR-0010](ADR-0010-live-capital-escalation.md) — the ADRs this mandate
  amends (0002/0004/0005/0007/0010) or relies on (0001/0003/0008/0009).
