---
name: ADR-0014 — Provisional candidate pool (screen/verdict split)
description: Splits ADR-0002 arsenal admission into a cheap singleton SCREEN (persistent, ex-ante-selectable competence window → provisional pool) and an expensive set-level VERDICT (marginal geometric-growth contribution to the incumbent allocator, adjudicated on the ADR-0007 confirmation ladder); makes screen-passing-but-unselected experts reconsideration-eligible rather than archived; registers the pool-priority ranking as a STANDING, MONITORED calibration whose weights are an empirical output, never a hand-set or literature-derived constant
type: governance
status: accepted
date: 2026-07-17
supersedes: ""
superseded_by: ""
amended_by: ""
---

# ADR-0014 — Provisional candidate pool (screen/verdict split)

> **STATUS: accepted (2026-07-17).** Accepted by principal direction. This ADR
> splits the ADR-0002 admission standard into a singleton SCREEN and a set-level
> VERDICT and amends ADR-0004/0007/0009; the amendment map below is the in-force
> record, and the named ADRs carry `amended_by: ADR-0014` banners (their numbered
> decision bodies are **not** rewritten in place, per the ADR-0013 convention).
> Enactment does **not** enact a loosened target, select a Kelly fraction, or
> certify an admission; it re-composes the admission pipeline and defers all
> numeric ranking weights to the standing monitored calibration
> `P1-2.0-POOL-PRIORITY-CALIBRATE` (Decision 6). The three BLOCKING numeric
> calibrations still gate certification.

## Context

Two forward admission candidates — H101 (unconditional first-hour ORB) and
H103 (stress-state anti-gate ORB) — were dispositioned `provisional-archive-null`
on the shadow ledger (2026-07-16). Each was adjudicated by a **singleton,
full-sample** admission scan (RC-H101-1, RC-H103-1) whose binding failures were
pooled quantities: no cell beat its matched-turnover rotor pooled over the
sample; §8 precision gates failed; the Ledoit-Wolf anti-gate differential was
non-significant. The arsenal is EMPTY as a result.

Read against the founding governance, the singleton-scan-as-verdict construction
has three defects:

1. **Degeneracy at |arsenal| < 2.** ADR-0002(d) non-redundancy is defined
   relative to *existing arsenal members / a covariance anchor*. With an empty
   arsenal there is nothing to be redundant to, so (d) cannot bind and the
   admission conjunction collapses toward a standalone-edge test — the very
   standalone burden ADR-0002 states does not exist, and the strategy-level gate
   ADR-0001 abolished. The first admission is structurally unable to be evaluated
   the way admissions two-onward will be.

2. **Wrong inferential object.** ADR-0001 makes the **allocator** the unit of
   inference; ADR-0013 makes **marginal log-wealth (geometric) growth** the
   decision currency. An expert's value to an allocator is its *marginal*
   contribution to the set's compounded growth — an interaction functional over
   the arm-set and the switching dynamics — not its pooled standalone edge. An
   expert with disjoint competence windows (positive in regimes where incumbents
   fail, null elsewhere) can raise set growth while having weak or negative
   pooled edge; the switching-oracle regret diagnostic (ADR-0004 Decision 4,
   [Herbster & Warmuth 1998](https://doi.org/10.1023/A:1007424614876)) is the
   lens that exposes exactly this structure. A pooled full-sample scan integrates
   that structure away. The matched-turnover rotor (ADR-0007 Benchmark 5) is a
   correct *null allocator* and the RC scans' rotor comparison is a legitimate
   necessary screen — but it was run pooled and standalone, and it does not test
   the marginal-to-a-set functional.

3. **Mislabeled disposition.** ADR-0009 forbids "fail" as a disposition, yet
   `archive-no-gross-edge` applied to an expert whose disjoint-window
   contribution was never measured records "undetermined as an allocator arm" as
   "has no edge." Because complementarity is set-relative, an expert that is
   redundant or edgeless against an *empty* arsenal carries no information about
   its value against a *future incumbent* whose drawdown regimes it might
   complement. Terminal archival forecloses the founding premise — that
   transient, regime-local edges combine — before the premise is testable.

The premise "works at some folds, combines with others that work at other
folds" is the program's thesis (ADR-0004 rolling-origin + switching-oracle
regret). Its disciplined form is **not** "existence of winning folds" — a random
rotor also wins some folds, and the in-sample switching oracle over noise has
vacuous regret — but "**persistent, ex-ante-selectable** winning windows,"
established by out-of-sample persistence (PBO/CSCV,
[Bailey, Borwein, López de Prado & Zhu 2017](https://doi.org/10.21314/JCF.2016.322);
DSR, [Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094))
and selectability (dwell ≥ realistic detection latency, ADR-0004 Decision 6 /
H900). This ADR encodes that discipline by splitting admission into a screen and
a set-level verdict.

## Decision

Arsenal admission (ADR-0002) is split into two inferential objects with distinct
units, costs, and burdens.

1. **SCREEN — singleton, necessary, cheap → provisional candidate pool.** An
   expert enters the **provisional candidate pool** iff it exhibits **at least
   one persistent, ex-ante-selectable competence window**:
   - **(S-a)** ADR-0002(a) interface compliance + leakage-canary suite (retained
     verbatim; non-waivable, ADR-0008).
   - **(S-b)** ADR-0002(b) pre-declared conditioning set (retained verbatim).
   - **(S-c)** **Conditional gross edge** in ≥ 1 declared cell, multiplicity-
     corrected *within the scan* (ADR-0002(c) machinery retained: Romano-Wolf
     StepM over the cell family with the ADR-0004 serial-dependence-preserving
     bootstrap). This is the necessary presence-of-signal condition.
   - **(S-d)** **Window persistence.** The cell's edge survives out-of-sample:
     PBO/CSCV below a data-derived bound **and** DSR above a data-derived bound —
     both tied to registered OUTPUTs, never implicit constants. The DSR gate is
     **not** "positive DSR": DSR is a probability ∈ [0,1]
     ([deflated_sharpe.py](../../src/skie_universe2/inference/deflated_sharpe.py)),
     so a > 0 test is vacuous. The DSR decision boundary is tied to the registered
     screening error-rate target (DSR ≥ 1 − screen α, α the `screen_alpha_ref`
     OUTPUT of the discovery-alpha calibration), and the PBO bound is likewise
     tied to the registered screening error-rate target (PBO ≤ screen α,
     `pbo_bound_ref`). Computed per the ADR-0007 confirmation
     estimators. This is the guard that separates a real window from
     fold-cherry-picking; it is the load-bearing addition of the screen.
   - **(S-e)** **Ex-ante selectability.** The winning window is selectable by a
     *causal* allocator: estimated regime dwell in the cell ≥ the **realistic
     (unsupervised) detection latency** (ADR-0004 Decision 6; H900; the
     `detection_cost_caveat` in
     [config/conditioning_covariates.yaml](../../config/conditioning_covariates.yaml)
     — never the supervised-CUSUM oracle latency, which is explicitly forbidden
     as the latency input). A window no causal allocator can enter reduces only
     *oracle* regret, not achievable growth, and does not pass.
     **BLOCKED/DEFERRED input.** The realistic unsupervised detection latency is
     currently **unquantified** — the repo registry records it as pending
     `P1-2.0-H900-BOCPD-WHITENED` (the on-ledger prewhitened ROC re-run is
     DEFERRED; only the *forbidden* supervised-CUSUM 2–3-bar latency is
     quantified). S-e is therefore an OUTPUT-placeholder gate on the same
     discipline as the Kelly memos: **the screen cannot be executed end-to-end,
     and the H101/H103 re-runs it queues cannot run their S-e test, until a
     reproducible on-ledger unsupervised latency is emitted.** No screen pass may
     be certified against an unquantified S-e latency.

   The screen **does not** require beating the rotor pooled, unconditional net
   edge, standalone Sharpe, or non-redundancy — none of which is well-defined or
   informative at the singleton/empty-arsenal boundary. Every screen evaluation
   (pass or fail) increments the ADR-0008 family-wise trial register and emits an
   Expert Card (ADR-0009).

2. **VERDICT — set-level, sufficient, expensive → arsenal membership / capital.**
   Arsenal membership and capital-eligibility are adjudicated on the **arsenal as
   a set**, never on singletons, by the ADR-0007 confirmation ladder under the
   ADR-0013 primary metric: a candidate's contribution is its **marginal
   geometric (log-wealth) growth contribution to the realizable incumbent
   allocator**, net of costs including switching costs, over rolling evaluation
   (ADR-0004), and it must clear the full five-rung ladder — including the
   non-waivable matched-turnover random rotor (Benchmark 5) — with the
   non-waivable DSR/PBO overfitting core. **ADR-0002(d) non-redundancy is
   evaluated HERE**, against the actual incumbent set, where the
   ensemble-covariance bound and the marginal-log-growth test are well-defined
   (ADR-0002(d) as amended by ADR-0013; the marginal-IR / Fundamental-Law view,
   [Grinold 1989](https://doi.org/10.3905/jpm.1989.409211), retained as the
   demoted monitored guardrail). The switching-oracle regret (ADR-0004) is
   reported as the diagnostic that motivated set-level adjudication, not as a
   competing decision metric — the binding verdict metric remains geometric
   growth (ADR-0013).

3. **Reconsideration-eligible dispositions (amends ADR-0009 taxonomy).**
   - An expert that fails the **screen** (no persistent, ex-ante-selectable
     window in any cell) is **`archive-no-persistent-window`** — a superset of
     the old `archive-no-gross-edge` (which remains a valid sub-reason: no gross
     edge in any cell). Terminal.
   - An expert that **passes the screen** (has a real, selectable window) but is
     **not selected at the verdict** (redundant with, or zero/negative marginal
     to, the current incumbent set) is **`pool-hold-reconsider`** — **NOT
     archived**. Because redundancy and marginal contribution are set-relative,
     a `pool-hold-reconsider` expert is **re-adjudicated whenever the incumbent
     set changes** (a new champion admitted, a member demoted), against the new
     set, with a fresh trial-register increment and an appended Expert Card
     version (ADR-0009 append-only).
   - **H101 and H103 are re-dispositioned to reconsideration-eligible.** Their
     `provisional-archive-null` verdicts were rendered against an empty arsenal
     by pooled singleton scans that did not run the screen's persistence/
     selectability tests. They are re-classified as **pending screen re-run**:
     if a persistent, ex-ante-selectable window exists they become
     `pool-hold-reconsider`; only if the screen fails do they become
     `archive-no-persistent-window`. No claim is certified either way here — the
     re-run is registered work, not asserted.

4. **Pool membership is a selection object; multiplicity is conserved.** Ranking
   the pool and promoting the top-k into the expensive verdict is itself a
   multiple comparison. **Pool trials enter the DSR effective-trials *estimator***
   (correlation-adjusted per ADR-0007 Decision 3 — the effective number of
   independent trials and cross-trial Sharpe variance, never a raw additive
   member count, since complementarity makes pool members correlated by
   construction) **and the SPA/StepM family** (consistent with ADR-0013 Decision 4
   expanding the family by the Kelly dimension — the pool dimension is added the
   same way). The
   founding invariant holds verbatim: **aggressive inclusion is bought with
   strictly more conservative multiplicity accounting, never weaker correction**
   (ADR-0007; ADR-0013 Decision 8). The looser *screen* is licensed **only**
   because the set-level verdict retains the full non-waivable ladder + DSR/PBO +
   rotor.

5. **Pool ledger artifact.** The provisional pool is materialized as an
   append-only ledger (ADR-0008) sourced from the shadow ledger (ADR-0003),
   schema at [config/pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml).
   Each member record is **generated** from Expert Card sections 3–5 (ADR-0009
   conditional-edge panel / ensemble block / stability profile), never
   hand-copied. The schema records a wide diagnostic set; the **ranking
   functional is confined to the gated factors of Decision 6**, and path-maximum
   statistics (max run-up, longest win/loss run, streak counts) are recorded with
   `role: descriptive` and are **barred from the ranking key** — they are the
   sample-extreme quantities DSR/PBO deflate, and ranking on them re-imports the
   overfitting the verdict removes.

6. **Pool-priority ranking is a STANDING, MONITORED calibration — not a constant
   (registered follow-up `P1-2.0-POOL-PRIORITY-CALIBRATE`).** Pool members are
   ordered for the expensive verdict by **expected marginal geometric-growth
   contribution to the incumbent set**, structured — not numerically fixed — as a
   **persistence-gated, realizability-gated, complementarity-weighted** score.
   The functional form and every weight are an **empirical output**, obtained by
   the project's own accruing evidence, of which screen-time recorded features
   actually predicted realized set-level marginal growth at prior verdicts. This
   follow-up is deliberately **standing and monitored, not a one-shot frozen
   memo**: the principal's constraint is that this construction goes against the
   grain and its answer does not reside in the literature, so the calibration is
   **revisited on a registered cadence as verdict outcomes accumulate**, its
   weights treated as tracked quantities with confidence intervals, never
   hand-tuned and never imported as a published constant (user global
   zero-magic-number rule; the same OUTPUT-placeholder discipline as the two
   BLOCKING Kelly memos).
   - **Cold-start ordering (calibration-free, declared provisional).** Until
     enough verdict outcomes exist to calibrate, the pool is ordered by
     **regime-coverage novelty first** — an expert that *uniquely* covers a
     regime cell the current arsenal leaves uncovered outranks one crowding a
     covered cell — with ties broken by the **screen persistence margin** (S-d
     DSR / 1−PBO). Coverage-novelty-first is a **structural** argument, not a
     tuned weight: switching-oracle regret is dominated by the worst-covered
     regime, so covering an empty cell is where marginal regret-reduction is
     largest by construction. **At |arsenal| = 0 the coverage-novelty primary is
     inert** — every cell is uncovered, so the predicate is uniformly true and
     cannot discriminate; ordering then falls entirely to the persistence-margin
     tie-breaker (S-d DSR / 1−PBO). This is acceptable because ranking sets only
     the verdict queue and certifies nothing; the primary begins to bite once ≥ 1
     incumbent exists. This cold-start rule is explicitly provisional and is
     itself superseded by the monitored calibration once it has data.
   - No pool ordering is used to *certify* anything: ranking sets the **queue**
     for the set-level verdict, which alone certifies membership (Decision 2).
     Mis-ranking costs compute, not correctness.

## Enactment

**Accepted and enacted 2026-07-17.** On acceptance: (i) ADR-0002/0004/0007/0009
received the banner + `amended_by: ADR-0014` treatment (per the ADR-0013
precedent) and the amendment map below is the in-force record — their numbered
decision bodies are not rewritten in place; (ii) `P1-2.0-POOL-PRIORITY-CALIBRATE`
is opened as a standing monitored follow-up; (iii) the H101/H103 screen re-runs
are queued, blocked on the Phase-1 numeric calibrations
([program_roadmap_2026-07-17.md](../research_notes/program_roadmap_2026-07-17.md));
(iv) [config/pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml)
status flips to `accepted`. This acceptance enacts **no** numeric target, selects
**no** Kelly fraction, and certifies **no** admission — the three BLOCKING
calibrations (discovery-alpha, Kelly concavity/ruin, H900 whitened latency) still
gate all of that.

## Amendment map (proposed)

Per-ADR, which clause changes and to what. Structure (gates, machinery,
register, ledger, non-waivable overfitting core) is retained throughout; only
the *composition* of the admission pipeline moves.

| ADR | Decision / clause | Current | Proposed (ADR-0014) | Integrity kept |
|---|---|---|---|---|
| ADR-0002 | Admission conjunction (a)–(d) | Single conjunction (a)∧(b)∧(c)∧(d) applied as one admission test | **Split** into SCREEN (a)∧(b)∧(c) + new (S-d) persistence + (S-e) selectability → provisional pool, and VERDICT (set-level marginal geometric growth on the ADR-0007 ladder, where (d) is evaluated) | (a) leakage-canary and (b) frozen conditioning set stay binding; (c) Romano-Wolf/bootstrap machinery retained at the screen |
| ADR-0002 | (d) Non-redundancy | Evaluated at admission — vacuous at \|arsenal\|<2 | **Moved to the set-level VERDICT**, evaluated against the actual incumbent set where the covariance bound and marginal-log-growth test are well-defined; IR/ensemble-variance view stays the ADR-0013 demoted guardrail | Non-redundancy **requirement** retained; bound still derived from arsenal covariance, never a constant |
| ADR-0002 | (d) citation label | "Grinold-Kahn framework" attached to the sole-author Grinold 1989 DOI (10.3905/jpm.1989.409211) | Relabel to "Fundamental Law / marginal-IR" (the "Grinold-Kahn" compound points to the distinct 1995/2000 *Active Portfolio Management* textbook); DOI unchanged | Cosmetic; the demoted-guardrail semantics of (d) unchanged |
| ADR-0002 | (e) Archive dispositions | Only `archive-no-gross-edge` | `archive-no-persistent-window` (screen failure; `no-gross-edge` a sub-reason) **+** `pool-hold-reconsider` (screen pass, verdict non-selection — reconsideration-eligible, set-relative, re-adjudicated on incumbent-set change) | "fail" still prohibited as a disposition; every scan still increments the trial register + emits a card |
| ADR-0004 | Decision 4 — switching-oracle regret | Reported diagnostic in the metric family | Elevated to the **conceptual justification** for set-level adjudication of disjoint-window experts; remains a **reported diagnostic**, NOT re-promoted to a decision metric (verdict currency stays geometric growth per ADR-0013) | Metric family unchanged; geometric growth remains primary; nothing removed |
| ADR-0007 | Decision 5 — promotion path | exploration → admission (ADR-0002) → allocator inclusion → confirmation ladder → capital | Insert the pool as an explicit stage: exploration → **SCREEN → provisional pool** → **set-level VERDICT (confirmation ladder)** → capital; no stage skipped; every transition recorded | Stage ordering, no-skip rule, register increment retained; Benchmark-5 rotor + DSR/PBO stay at the verdict, non-waivable |
| ADR-0007 | Decision 3 — SPA/StepM + DSR family | Family = (config × Kelly-fraction) pairs | Family additionally carries the **pool-selection dimension** (top-k ranking is a comparison); pool trials enter the DSR effective-trials estimator (correlation-adjusted, not a raw count) and the SPA/StepM family | Correction machinery untouched; expanding the family is strictly more conservative |
| ADR-0009 | Decision 6 — disposition enum | Fixed six-value enum | Add `pool-hold-reconsider`; refine `archive-no-gross-edge` → `archive-no-persistent-window` (old value retained as a sub-reason); a `pool-hold` card is append-only re-versioned on each set-relative re-adjudication | Eight-section card, machine-readability, append-only, pass/fail prohibition all retained |

## Consequences

- **Positive:** the empty-arsenal boundary is no longer a governance
  contradiction — the first admission is an explicit degenerate case (screen
  into pool, verdict deferred until a set exists) rather than a standalone gate
  masquerading as an allocator-unit inference.
- **Positive:** the founding premise (disjoint-window combination) becomes
  testable at the object that owns it — the set — instead of being foreclosed by
  singleton nulls; `pool-hold-reconsider` makes a null a *held* result, not a
  discarded one.
- **Positive:** the ranking discipline (persistence + selectability gate,
  path-maxima barred, weights monitored-not-fixed) keeps "everything works
  somewhere" from becoming a license to admit noise; the screen's DSR/PBO/dwell
  gates are the price of the looser conjunction.
- **Negative:** the pool is a new persisted, multiplicity-bearing object; its
  size inflates the DSR trial count and the SPA/StepM family, raising the
  correction burden — the honest price of holding candidates instead of
  discarding them.
- **Negative:** `pool-hold-reconsider` implies **re-adjudication on every
  incumbent-set change**, i.e. recurring compute against a growing pool; bounded
  by Tier-0 default fidelity (ADR-0006) and ledger reuse (ADR-0003), and by the
  ranking queue (only top-k re-run per change).
- **Obligation:** `P1-2.0-POOL-PRIORITY-CALIBRATE` is a **standing** follow-up —
  it never reaches a terminal "frozen" state the way a one-shot memo does; each
  monitoring checkpoint emits a ReproLog and updates the tracked weights with
  CIs. Until its first checkpoint has data, the calibration-free cold-start
  ordering (coverage-novelty-first) governs, declared provisional.
- **Obligation:** no numeric ranking weight, persistence bound, or dwell
  threshold is a hard-coded constant; the (S-d) PBO/DSR bounds are data-derived
  (tied to the registered screening error-rate target), the (S-e) unsupervised
  detection latency is **BLOCKED/DEFERRED on `P1-2.0-H900-BOCPD-WHITENED`** (the
  screen is not end-to-end executable, and no screen pass is certifiable, until
  it emits a reproducible on-ledger value), and the ranking weights are monitored
  outputs.

## Alternatives considered

- **Keep the singleton admission scan as the verdict (status quo).** Rejected:
  degenerate at |arsenal|<2, tests the wrong functional (pooled standalone, not
  marginal-to-set), and mislabels undetermined-as-arm as no-edge — the three
  defects in Context.
- **Admit the first expert on standalone edge, then switch to set-level.**
  Rejected: re-imports the standalone burden ADR-0002 abolished and the
  strategy-level gate ADR-0001 abolished; the screen's persistence/selectability
  gates + the rotor null-allocator comparison at the verdict achieve first-arm
  admission without a standalone-profitability test.
- **Rank the pool by max run-up / longest win streak / consecutive wins.**
  Rejected outright: these are sample-extreme path functionals with fat right
  tails under the null; a random arm maximizes them. Ranking on them is
  selection-on-luck that re-inflates exactly what DSR/PBO deflate. Recorded as
  `role: descriptive` only.
- **Fix the pool-priority weights now from the literature.** Rejected per
  principal direction and the zero-magic-number rule: the construction is novel
  (against the grain) and its weights do not reside in published work; they are
  outputs of standing empirical monitoring of the project's own verdict history,
  with a structural (not tuned) cold-start rule until that history exists.
- **Admit everything into the arsenal (no screen).** Rejected (ADR-0002
  Alternatives, verbatim): dilutes allocator learning with pure-noise experts,
  inflates the regret bound via N, and makes the trial register meaningless. The
  screen is a *necessary* filter into a *pool*, not the abolished admission gate.

## References

- [Herbster & Warmuth 1998, Mach. Learn. 32:151-178](https://doi.org/10.1023/A:1007424614876)
  — fixed-share / switching-oracle regret; the diagnostic that exposes
  disjoint-window value.
- [Bailey, Borwein, López de Prado & Zhu 2017, J. Comput. Finance 20(4):39-69](https://doi.org/10.21314/JCF.2016.322)
  — PBO via CSCV; the (S-d) persistence guard against fold-cherry-picking.
- [Bailey & López de Prado 2014, J. Portfolio Manage. 40(5):94-107](https://doi.org/10.3905/jpm.2014.40.5.094)
  — Deflated Sharpe; (S-d) persistence and pool-size trial accounting.
- [Grinold 1989, J. Portfolio Manage. 15(3):30-37](https://doi.org/10.3905/jpm.1989.409211)
  — the Fundamental Law of active management (IR = IC·√breadth); the marginal-IR
  contribution framing invoked here. (ADR-0002(d)'s legacy "Grinold-Kahn
  framework" label for this same sole-author DOI is harmonized to "Fundamental
  Law / marginal-IR" on acceptance — see the amendment map; the "Grinold-Kahn"
  compound points to the distinct 1995/2000 textbook.) Retained as the ADR-0013
  demoted guardrail at the verdict.
- [Hansen 2005, J. Bus. Econ. Stat. 23:365-380](https://doi.org/10.1198/073500105000000063);
  [Romano & Wolf 2005, Econometrica 73:1237-1282](https://doi.org/10.1111/j.1468-0262.2005.00615.x)
  — SPA existence + StepM identification; the family now also carries the pool
  dimension.
- [Sullivan, Timmermann & White 1999, J. Finance 54:1647-1691](https://doi.org/10.1111/0022-1082.00163)
  — the in-sample-survives / out-of-sample-decays arc; why persistence (S-d), not
  presence, is the screen's binding condition.
- [Kelly 1956, Bell Syst. Tech. J. 35:917-926](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x);
  [MacLean, Thorp & Ziemba 2011, World Scientific](https://doi.org/10.1142/7598)
  — geometric (log-wealth) growth; the verdict currency (ADR-0013).
- [ADR-0001](ADR-0001-allocator-unit-of-inference.md),
  [ADR-0002](ADR-0002-arsenal-admission-standard.md),
  [ADR-0003](ADR-0003-shadow-ledger-canonical-object.md),
  [ADR-0004](ADR-0004-rolling-evaluation-regime.md),
  [ADR-0007](ADR-0007-two-tier-discovery-pipeline.md),
  [ADR-0008](ADR-0008-integrity-non-negotiables.md),
  [ADR-0009](ADR-0009-expert-card-terminal-deliverable.md),
  [ADR-0012](ADR-0012-standing-incumbent-allocator.md),
  [ADR-0013](ADR-0013-aggressive-geometric-growth-mandate.md) — amended
  (0002/0004/0007/0009) or relied upon (0001/0003/0008/0012/0013).
