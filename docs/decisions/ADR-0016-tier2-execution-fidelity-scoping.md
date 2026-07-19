---
name: ADR-0016 — Tier-2 execution-fidelity scoping
description: Scopes what an ADR-0006 Tier-2 execution simulator IS — fill-model class (queue-position + fill-probability, not full book replay), data requirement (bounded MBO validation sample used to certify a cheaper MBP-10-derived model applied at scale), reportability delta, staged A→D gate structure with the first spend at stage B, and — load-bearing — the execution-model overfitting guard: the fill assumption is SWEPT over a pre-registered pessimistic/central/optimistic grid rather than selected, calibrated on spans disjoint from evaluation, with every (config × fill-assumption) pair a registered trial; authorizes no spend and builds nothing
type: architecture
status: accepted
date: 2026-07-18
supersedes: ""
superseded_by: ""
amended_by: ""
---

# ADR-0016 — Tier-2 execution-fidelity scoping

> **STATUS: accepted (2026-07-19).** Drafted `proposed` 2026-07-18; **accepted
> by principal direction 2026-07-19** (operator authorization recorded in the
> 2026-07-19 session; **not self-accepted**), after round-1 remediation of the
> argument-validity audit
> ([audit_trail_2026-07-19_odg-deliverables-argument-audit.md](../audits/audit_trail_2026-07-19_odg-deliverables-argument-audit.md)).
> Acceptance authorizes **stage A only** (Decision 9). This ADR **authorizes no
> spend, ingests no data, and builds no simulator** — stage B still requires its
> own named, dated operator authorization. It amends no ADR decision body,
> changes no disposition, increments no trial register, and certifies nothing.
> It is a scoping decision: it fixes *what would be built and how it would be
> guarded* so that the first spend decision (stage B below) is made against a
> written specification rather than improvised at the moment of purchase.

## Context

[ADR-0006](ADR-0006-execution-fidelity-tiers.md) defines three execution
fidelity tiers and makes Tier 2 — "tick (or finest available) data, queue
position model for limit orders, explicit latency assumption, order-flow-aware
slippage" — the required tier for any limit-order, interbar-entry, or
scalping-hold-time claim (Decision 1, Decision 2). It does **not** specify what
a Tier-2 simulator *is*: which fill-model class, on what data, validated how.
Its own Consequences record the gap ("Tier 2 requires tick-data acquisition and
a queue model — a substantial infrastructure hypothesis of its own") and its
standing Obligation ("the Tier-2 fill model itself must be validated against
live fills") names a validation source, [ADR-0010](ADR-0010-live-capital-escalation.md)
tracking data, that does not exist yet and cannot exist before the arsenal does.
The program therefore holds a binding reportability rule with no substrate and
no specification behind it.

The gap is now load-bearing in three places:

1. **H104** (retro of 1.0 H055, wick-rejection mean-reversion scalp) is a
   limit-at-wick-extreme design. Its 1.0 evidence was simulated at Tier 0 with a
   next-bar-open market entry that, by its own KPI caveat, "admits more trades"
   than the limit semantic — so every number is exploration-tier only, and the
   registered closure scan RC-H104-3 cannot resolve the limit-fill-at-wick
   semantics at any tier the project can currently run.
2. **OD-G** (opened 2026-07-18, [backfill plan](../research_notes/backfill_admission_plan_2026-07-17.md)
   §OD-G): a spread/liquidity-regime mechanism whose edge derives from spread
   capture, queue position, or liquidity provision cannot be screened at all
   under ADR-0006 Decision 2. Its only currently admissible form is a Tier-0
   directional expert that *conditions* on a spread/liquidity covariate while
   taking liquidity at bar close — a proxy, not the mechanism.
3. **Forward mechanism sourcing generally.** Under
   [ADR-0015](ADR-0015-ratified-pool-hold-verdict-precondition.md) the gating
   item is a disjoint-window forward expert. Several natural candidate
   mechanisms at the program's frequency are fill-sensitive; each will hit the
   same wall, and each will be tempted into the same Tier-0 proxy.

There is also a discipline gap specific to execution modelling, and it is the
reason this ADR exists as governance rather than as an engineering ticket. The
project's overfitting core — Deflated Sharpe
([Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094)),
PBO/CSCV ([Bailey, Borwein, López de Prado & Zhu 2017](https://doi.org/10.21314/JCF.2016.322)),
the matched-turnover random rotor (ADR-0007 Benchmark 5), the family-wise trial
register (ADR-0008 Decision 6) — guards the **signal** search space. Nothing in
the founding governance guards the **execution-model** search space. A fill
model has free parameters (queue position at submission, fill probability
conditional on queue depletion, adverse-selection haircut on passive fills,
latency, cancel/replace policy). Absent a rule, those parameters are tunable
until a marginal strategy clears its gates, and **no existing gate catches it**:
DSR counts signal trials, PBO resamples signal-configuration folds, and the
rotor matches turnover under a *fixed* fill assumption. Tuning the fill model is
also precisely the cross-layer repair ADR-0005 Decision 4 prohibits ("loosening
fill assumptions to rescue a cost-bound expert") — but ADR-0005 states the
prohibition without giving it a detection mechanism. Tier-2 machinery without
that mechanism would be a net integrity *regression*: it would replace a
transparently pessimistic Tier-0 proxy with an opaque, high-degree-of-freedom
model that produces better-looking numbers by construction.

The direction of the bias is known, not speculative. Assuming a limit fill
whenever price touches the level grants exactly the fills where the market
traded through — the adversely-selected ones — and flatters mean-reversion
strategies specifically ([Harris 2003](https://global.oup.com/academic/product/trading-and-exchanges-9780195144703),
*practitioner*, monograph — no DOI; the mechanism is the classic informed-order-flow
adverse selection of a passive quote,
[Glosten & Milgrom 1985](https://doi.org/10.1016/0304-405X(85)90044-3)). H104 is
a mean-reversion scalp entering on limit orders at wick extremes: the single
strategy class most inflated by the optimistic assumption, which is why its
Tier-0 numbers cannot be repaired by any amount of care at Tier 0.

## Decision

1. **Fill-model class: queue-position + fill-probability modelling, NOT full
   order-book replay/matching.** The Tier-2 substrate is scoped as a *stochastic
   fill model* — for a resting order of known side, price level, and submission
   time, estimate its position in the queue and the probability of execution
   before cancellation or adverse move, with an explicit adverse-selection
   characterization of the fills granted. The reference model class is the
   queue-reactive family
   ([Huang, Lehalle & Rosenbaum 2015](https://doi.org/10.1080/01621459.2014.982278)),
   with order-flow-driven price-impact terms per
   [Cont, Kukanov & Stoikov 2014](https://doi.org/10.1093/jjfinec/nbt003) —
   already the citation ADR-0006 Decision 1 attaches to Tier 2.
   - **Full order-book replay/matching requires**: complete MBO (market-by-order)
     history for the full evaluation span; a matching engine reproducing the
     venue's priority rules; and — the defeating requirement — a counterfactual
     model of how *other* participants would have reacted to the simulated
     order's presence in the book. It **can claim** exact queue position and
     exact fills for a passive order under the counterfactual assumption that
     the book is unperturbed. It **cannot claim** validity once the simulated
     order is large enough to change others' behaviour, and it cannot escape
     that assumption by construction (replay is deterministic; the market's
     reaction is not in the tape).
   - **Queue-position + fill-probability modelling requires**: enough order-level
     detail to *estimate* queue position and depletion dynamics, and a validation
     sample where those estimates can be checked. It **can claim** distributional
     statements — fill rate by queue position, expected adverse-selection cost of
     a passive fill, the sign and rough magnitude of the Tier-0-vs-Tier-2 delta,
     and *sensitivity* of a strategy claim across the fill-assumption range. It
     **cannot claim** per-order determinism ("this specific order filled"), and
     it must not be reported as if it did.
   - Rationale for the choice: the program's decision object is whether a
     strategy claim survives plausible execution reality, which is a
     distributional question. Full replay buys per-order determinism the program
     does not need, at a data and engineering cost that is the dominant term, and
     it purchases that determinism under a market-impact counterfactual that is
     itself unvalidated. This choice is scoped, not permanent: a future ADR may
     revisit it if a claim class genuinely requires per-order semantics.

2. **Data requirement: MBO for validation, MBP-10 at scale.** Queue position is
   *observable* only from MBO (market-by-order), which carries individual order
   add/modify/cancel/trade events and therefore true position within a price
   level. MBP-10 (aggregated market-by-price depth, ten levels) carries only
   aggregate size per level: queue position is **approximable** from it — by
   attributing the resting size ahead of a hypothetical submission and modelling
   depletion from the visible trade and cancel flow — never observable. The
   trade-off is fidelity against volume: MBO is order-of-magnitude larger and
   costlier per unit span; MBP-10 is tractable across the multi-year evidence
   spans the shadow ledger requires.
   - The **staged approach is the decision**: acquire a **bounded MBO sample**
     (a pre-registered, narrow span and symbol set, sized by the validation
     power requirement of Decision 5, not by convenience), use it to **validate**
     an MBP-10-derived queue/fill estimator against MBO ground truth, and then
     apply the **validated cheaper model at scale** on MBP-10. The MBO sample is
     a *measuring instrument for the model*, not evidence about any strategy.
   - Spans consumed by MBO validation are consumed **for calibration**, and are
     therefore burned for evaluation purposes under Decision 4 and ADR-0008
     Decision 5.
   - No vendor, product, or price is named or authorized here; the vendor
     selection and its spend are stage-B objects (Decision 6).

3. **Reportability delta.** Tier-2 changes reportability exactly as ADR-0006
   Decision 2 already specifies — this ADR adds no new reportability rule and
   restates none. What a validated Tier-2 substrate does is make the claim
   classes ADR-0006 Decision 1 names for Tier 2 (limit-order, interbar-entry,
   scalping-hold-time) **reportable at all**, subject to the tier-promotion stage
   gate of ADR-0006 Decision 3 and to Decision 4 of this ADR. Three boundaries
   hold even then:
   - **Per-order determinism remains unreportable** under the model class of
     Decision 1. Claims are distributional; "this order would have filled" is not
     a reportable claim.
   - **Market-impact-dependent claims remain unreportable.** Any claim whose
     validity depends on the simulated order not having changed others' behaviour
     — i.e. capacity claims beyond the size the validation sample supports —
     stays outside the tier. Capacity remains an ADR-0009 §-level estimate with
     its assumption stated, not a Tier-2 output.
   - **A claim that survives only part of the Decision-4 fill-assumption sweep is
     unreportable as a claim.** It is reportable only as a sensitivity exhibit,
     labeled with the range over which it fails. This is stricter than ADR-0006
     Decision 2, which conditions reportability on tier alone.
   - Unchanged: the bar-level cost model applies at every tier (ADR-0006
     Decision 4); tier is a recorded ledger column and mixed-tier comparisons
     stay prohibited (Decision 5); a Tier-2 result supersedes its Tier-0/1
     predecessor (Decision 3).

4. **Execution-model overfitting guard (load-bearing).** The fill assumption is
   **SWEPT, never selected.** This is the direct analogue of the ADR-0013
   Decision 3 swept Kelly fraction — a free parameter that could be tuned into a
   result is instead pre-registered as a grid, reported at every point, and
   required to hold across the range — and of the matched-turnover rotor's role
   as the control for selection skill.
   - **(E-a) Pre-registered fill-assumption grid.** Every Tier-2 evaluation
     declares, before it runs, a grid of at least **pessimistic / central /
     optimistic** fill assumptions spanning the model's free dimensions (queue
     position at submission, fill probability conditional on depletion,
     adverse-selection haircut, latency). Grid endpoints and spacing are an
     **OUTPUT** of the stage-C validation (Decision 5) — bracketing the empirical
     range observed on the MBO sample — never hand-set constants (user-global
     zero-magic-number rule). The ADR-0013 Kelly-grid precedent is adjacent,
     not identical: that grid was fixed as a **registered sweep** at acceptance
     and its bracketing adequacy checked empirically afterwards
     ([kelly_growth_concavity_ruin_2026-07-12.md](../methodology/kelly_growth_concavity_ruin_2026-07-12.md)
     §B — inconclusive-on-null-ledger, re-instantiation registered at first
     admission); the fill grid goes one step further by making its endpoints a
     stage-C calibration OUTPUT.
   - **(E-b) Report at every point.** Results are reported at **all** grid
     points, never only at the selected or best one. A single-point Tier-2 number
     is not a Tier-2 result.
   - **(E-c) Survive the whole range.** A claim is admissible only if it holds at
     **every** grid point including the pessimistic endpoint. Claims that hold
     only centrally or only optimistically are sensitivity exhibits (Decision 3),
     not claims. Rationale: under the ADR-0013 geometric-growth objective at
     leverage, an execution-overfit champion does not merely underperform — it
     ruins, exactly as a signal-overfit champion does, and it is *harder* to
     detect because the error lives in a layer no existing gate audits.
   - **(E-d) Disjoint calibration and evaluation spans.** Fill-model parameters
     are calibrated on spans **disjoint** from the spans on which any strategy
     claim is evaluated. Calibration is data consumption: every calibration span
     is recorded in `config/burned_data_ledger.yaml` per ADR-0008 Decision 5 and
     is dead to successor confirmation-tier evidence. Calibrating a fill model on
     the same span the strategy is evaluated on is leakage through the execution
     layer, and the ADR-0008 Decision 1 PIT/canary discipline applies to
     execution-layer parameters exactly as it does to features.
   - **(E-e) Every (config × fill-assumption) pair is a registered trial.** The
     fill-assumption dimension **expands the multiple-testing family** exactly as
     the Kelly dimension does under ADR-0013 Decision 4: each pair appends a
     per-trial record to `config/multipletest_family.yaml` per ADR-0008
     Decision 6 (identifier, Sharpe estimate, return-series pointer, clustering
     metadata), enters the Romano-Wolf / SPA correction over the enlarged family,
     and enters the **DSR effective-trials** estimator. The family after this ADR
     is (config × Kelly-fraction × fill-assumption). Expanding the family is
     strictly more conservative: execution realism is bought with more honest
     multiplicity accounting, never less.
   - **(E-f) No cross-layer repair.** ADR-0005 Decision 4 already prohibits
     loosening fill assumptions to rescue a cost-bound expert; (E-a)–(E-e) are
     its **detection mechanism**. A pre-registered grid reported at every point
     makes the repair visible as a claim that survives only at the optimistic
     endpoint, which (E-c) then rejects.

5. **Validation protocol — decided before the build, not after.** The stage-C
   model is accepted only against criteria fixed now:
   - **(V-a) Cross-validation against MBO ground truth.** On the bounded sample
     where both representations are held, MBP-10-derived queue-position and
     fill-probability estimates are compared against the MBO-observed truth, with
     the comparison reported as a distribution (error in queue position; realized
     vs predicted fill rate), not a point summary. **Acceptance bounds are
     EXTERNAL to this comparison**: the bound-generating rule is pre-registered
     before the MBO sample is opened, and it is a decision-relevance criterion —
     the estimator's queue-position and fill-rate errors must be small enough
     that the Decision-4(E-a) pessimistic endpoint still brackets the true fill
     distribution conservatively for every Decision-3 claim class. What is an
     OUTPUT of the comparison is the measured error distribution and the E-a
     grid endpoints — never the pass/fail bounds themselves, which would let
     the model grade its own exam and build the loosening Decision 6 forbids
     into the bound-generation step.
   - **(V-b) Stylized-fact reproduction.** The model must reproduce known
     microstructure regularities: monotone **fill rate by queue position**
     (orders nearer the front fill more often — a direct consequence of
     price-time priority; the calibrated queue-reactive model of
     [Huang, Lehalle & Rosenbaum 2015](https://doi.org/10.1080/01621459.2014.982278)
     generates the quantitative shape of that curve by simulation, and the
     simulated curve is tested against the MBO-observed one);
     and a negative **adverse-selection profile of passive fills** (passive fills
     are on average granted into subsequent adverse moves —
     [Glosten & Milgrom 1985](https://doi.org/10.1016/0304-405X(85)90044-3);
     [Harris 2003](https://global.oup.com/academic/product/trading-and-exchanges-9780195144703),
     *practitioner*). A model that fills passive orders without an
     adverse-selection cost has failed validation regardless of its queue-position
     accuracy — that failure mode is the exact bias ADR-0006 was written to
     prevent.
   - **(V-c) Live-vs-shadow reconciliation is the eventual gold standard but
     cannot gate this build.** ADR-0006's standing Obligation and the ADR-0010
     live-tracking machinery are the only source of ground truth about *this
     account's* realized fills. It arrives after a champion exists and after live
     capital is deployed — i.e. after the point at which the build decision must
     be made. This ADR therefore does **not** wait on it: (V-a) and (V-b) are the
     gating criteria, and live reconciliation is registered as a **standing
     re-validation condition** — the first live fills re-open the fill-model
     calibration, and a Tier-2 claim asserted before then carries that
     re-validation condition explicitly in its Expert Card (ADR-0009).

6. **Staged gate structure.** Four stages; each gate is an explicit, dated
   operator authorization, and no stage runs on the authorization of its
   predecessor. Each gate has exactly three recordable states: **authorized**
   (named, dated), **declined / not scheduled** (named, dated — the NO-GO
   terminal object of the staged structure), or **undecided** (the default;
   absence of a record is "undecided", never implied consent). External
   documents that key decisions to this ADR must bind to these recorded
   objects — a stage-B authorization or a stage-B decline — not to a
   paraphrased "stage-A go/no-go", which this ADR does not define.
   - **Stage A — scope + ADR (no spend).** This document. Fixes the model class,
     the data strategy, the reportability delta, the overfitting guard, and the
     validation criteria. Cost: drafting only.
   - **Stage B — bounded validation pull (FIRST and ONLY spend decision at this
     stage).** Acquire the bounded MBO sample of Decision 2, span/symbols/size
     pre-registered against the Decision-5 validation-power requirement. The
     **validation-power specification** — the minimum order-event counts per
     regime block sufficient to estimate the (V-a) error distribution and the
     E-a grid endpoints at stated precision — is **authored and pre-registered
     as part of the stage-B pre-registration, before pricing**; the bounded
     sample's size is registered against it, never against convenience. This is
     the first spend the Tier-2 programme requires, and it is deliberately the
     *small* one. Requires named operator authorization; upstream registered per
     Decision 7 **before** ingest. **Feed-era constraint:** every candidate
     block must lie entirely within the venue span where order-level
     (MBO-quality) granularity is confirmed — the vendor dataset page states
     GLBX MDP 3.0 moved to full order-event granularity "since March 2017"
     (exact cutoff operator-confirmed with the vendor before pricing; the
     repo's earlier note carried 2017-05-21 — the discrepancy is open). A block
     outside that span has no order-level ground truth and voids the
     validation purpose of the pull.
   - **Stage C — build + validate against the sample.** Implement the MBP-10-derived
     queue/fill estimator in the `execution` subpackage (ADR-0005 Decision 3),
     validate per Decision 5, and emit the Decision-4 grid endpoints as the
     calibration OUTPUT. Cost: engineering time only — no additional data spend.
   - **Stage D — decide the broad pull on what C shows.** The full-span data
     acquisition decision is made *after* stage C, informed by measured
     validation error rather than by hope.
   - **The containment is explicit**: if the cheap MBP-10-derived model **cannot**
     reproduce MBO queue behaviour within the stage-C acceptance bounds, that is
     learned at **stage-B cost, not full-pull cost**. A negative stage-C result is
     a successful outcome of this structure, not a failure of it, and is recorded
     as such rather than remediated by loosening the acceptance bounds.

7. **Storage and provenance (ADR-0011, binding, no exception).** Raw tick data —
   MBO and MBP-10 alike — lands in the **machine-level store** `~/datasets/`,
   never in this repository, with a retrieval-time provenance sidecar carrying
   its SHA-256 (ADR-0011 Decisions 1 and 4). Only processed derivatives are
   project-level, materialized by in-project ingest under `data/processed/` with
   per-file SHA-256 in `data/_manifest.json`; nothing under `data/` is committed
   beyond the manifest exceptions of ADR-0011 Decision 5. The upstream **must be
   registered in [config/data_sources.yaml](../../config/data_sources.yaml)
   BEFORE ingest** — ingest modules refuse unregistered sources (ADR-0011
   Decision 3), and adding a source without registering it is an integrity
   violation under ADR-0008. Registration is part of stage B, not a follow-up to
   it. The volume asymmetry is a planning input for the machine-level store, not
   a licence to stage tick data inside the repo.

8. **What this unblocks — and what it does not.**
   - **Unblocks (conditional on stages B–D):** **H104**, whose registered closure
     scan RC-H104-3 is hard-blocked on limit-fill-at-wick semantics that no tier
     below 2 can express — the Tier-0 next-bar-open simplification "admits more
     trades" than the limit semantic, and the strategy class is the one most
     inflated by that bias, so no Tier-0 re-run can resolve it. **OD-G**, the
     spread/liquidity mechanism, which under ADR-0006 Decision 2 is currently
     admissible only as a Tier-0 directional proxy conditioning on a
     spread/liquidity covariate while taking liquidity at bar close — the
     mechanism itself becomes screenable. And **future microstructure work**
     generally: queue-position, passive-fill, and hold-time-sensitive mechanisms
     become a sourceable class rather than an automatically blocked one.
   - **Does NOT unblock the current critical path.** Under ADR-0015 the gating
     item is a **second disjoint-window expert** — ≥ 2 distinct `expert_hash`
     values with non-overlapping coverage vectors — to lift the ratified pool
     HOLD and make the pool verdict-eligible. Tier-2 work supplies no such
     expert and lifts no precondition. It is **parallel investment**, and if it
     is authorized it must be scheduled as such: it does not substitute for
     forward mechanism sourcing, and stage-B authorization must not be read as
     re-prioritizing the critical path behind it.

9. **This ADR builds nothing and authorizes nothing.** No `execution`
   subpackage code, no data acquisition, no vendor commitment, and no ADR-0006
   tier promotion follows from acceptance. Acceptance authorizes **stage A only**
   — the existence of this specification. Stage B requires its own named,
   dated operator authorization.

10. **Tier-promotion vs successor-HID rule (resolves the governance question
    the OD-G setup plan flags).** ADR-0006 Decision 3 effects tier promotion
    "with a design.md amendment"; the project's pre-registration discipline
    makes a frozen design.md immutable (any change → new HID). The two rules
    prescribe different objects for the same event; this decision reconciles
    them on the estimand:
    - **(a) Unchanged estimand** — same entry/exit semantics, same conditioning
      set, same claim classes, execution fidelity upgraded only: a **tier
      promotion of the same HID** under ADR-0006 Decision 3. The "design.md
      amendment" is scoped as an **append-only execution-tier addendum** (own
      registered SHA; the frozen sections untouched — the same append-only
      idiom as the H103 `expert_card_v3` correction of record), and the
      higher-tier result supersedes the lower-tier one per ADR-0006 Decision 3.
    - **(b) Changed estimand** — the lower-fidelity form tests a different
      question than the higher-fidelity mechanism (the OD-G case: Form A's
      conditioning question vs Form B's microstructure question, per the
      [setup plan](../research_notes/od_g_spread_liquidity_setup_plan_2026-07-18.md)
      §1 "What Form A is not"): the higher-tier evaluation is a **successor
      HID**, and ADR-0008 Decision 5 applies with full force — spans consumed
      by the lower-fidelity form are dead to the successor's
      confirmation-tier evidence.
    - **(c) The classification is declared at the lower-fidelity freeze**, not
      argued after results exist: any design.md for a fill-sensitive mechanism
      run below Tier 2 states which case a later Tier-2 evaluation would be.
      Choosing (a) to preserve spans when the estimands differ is the "reading
      that preserves data rather than the one that describes the science" the
      setup plan §4 forbids.
    - **(d) Calibration spans are burned by registration.** ADR-0008 Decision 5
      names hypotheses; this decision extends the ledger's coverage to non-HID
      consumers: every fill-model calibration span (Decision 4(E-d)) is
      recorded in `config/burned_data_ledger.yaml` with a
      `consumer: execution-calibration` tag and is dead to successor
      confirmation-tier evidence exactly as an HID-consumed span is.

## Consequences

- **Positive:** ADR-0006's Tier-2 definition acquires a specification. The
  reportability rule it enforces stops being a rule with nothing behind it, and
  the first spend decision is made against written criteria rather than
  improvised at the point of purchase.
- **Positive:** the execution-model search space acquires a guard for the first
  time. Decision 4 closes a real hole — the integrity core audits signal trials
  and (since ADR-0013) sizing trials, but a fill model could until now be tuned
  until a strategy worked with no gate catching it, and no amount of Tier-2
  engineering would have caught it either. The fix reuses the project's own
  proven idiom (sweep, don't select) rather than inventing new machinery.
- **Positive:** the staged structure makes the expensive failure cheap. The
  question that decides the whole programme — can an MBP-10-derived model
  reproduce MBO queue behaviour? — is answered at stage-B cost.
- **Negative (the honest cost):** this is a **multi-week-to-months scoped
  project**, not a task. Data acquisition, a validated fill model, the sweep
  machinery, and re-running fill-sensitive candidates across a
  three-point-minimum grid are each substantial. **Loosely scoped, it could
  consume the program** — execution infrastructure is unusually good at
  absorbing effort, and unlike a hypothesis it produces no disposition to stop
  at. The containment is the stage structure with bounded stage-B spend, the
  requirement that stage D be decided on measured stage-C error, and the
  Decision-8 statement that this is parallel to, never ahead of, the critical
  path.
- **Negative:** the multiple-testing family expands again, by the
  fill-assumption dimension (≥ 3 points), on top of the ADR-0013 Kelly dimension
  (×4). Correction burden and confirmation compute rise multiplicatively. This is
  the honest price of sweeping the execution dimension, and it is paid in the
  same currency ADR-0013 established.
- **Negative:** Decision 4(E-c) will reject claims that a single-point Tier-2
  simulator would have passed. That is the intent; it also means Tier-2 promotion
  can *lower* a strategy's apparent standing, and the Decision-8 unblocking
  should not be read as a promise that H104 or OD-G will survive.
- **Obligation — DATA-BURN ORDERING (the sequencing argument).** OOS spans burned
  running a fill-sensitive mechanism as a Tier-0 proxy are recorded in the
  burned-data ledger (ADR-0008 Decision 5) and are **dead to successor
  confirmation-tier evidence** — which, per Decision 10(b), includes the Tier-2
  evaluation of the same mechanism whenever the proxy and the mechanism test
  different estimands; OD-G is that case by the setup plan's own §1 analysis.
  The spans that would be the natural Tier-2 test set are exactly the
  ones a Tier-0 proxy consumes first. **So if Tier-2 is ever going to happen,
  deciding *before* spending OOS data on proxies is the strictly cheaper
  sequence**: the alternative pays for the proxy in data, then discovers it must
  buy fresh spans to test the mechanism properly. This argument does not force
  the decision — it fixes when the decision is cheapest to make, which is now,
  and it applies with full force to OD-G, whose only currently admissible form
  *is* a Tier-0 proxy.
- **Obligation:** acceptance of this ADR is principal-only. If accepted, stage B
  requires separate named authorization, and the upstream registration of
  Decision 7 precedes any ingest.
- **Obligation (standing):** per Decision 5(V-c), the first live fills under
  ADR-0010 re-open the fill-model calibration; any Tier-2 claim asserted before
  live reconciliation carries that re-validation condition explicitly in its
  Expert Card (ADR-0009).

## Alternatives considered

- **Full order-book replay/matching as the Tier-2 class.** Rejected for now
  (Decision 1): requires full-span MBO plus a venue-faithful matching engine, and
  its per-order determinism rests on an unvalidated counterfactual that other
  participants would not have reacted to the simulated order. The program's
  decision object is distributional; buying determinism it does not need is the
  dominant cost term. Revisitable by a successor ADR if a claim class genuinely
  requires per-order semantics.
- **MBP-10 only, no MBO validation sample.** Rejected: queue position is not
  observable in aggregated depth, so an MBP-10-derived estimator without an MBO
  cross-validation is an unfalsifiable model of the exact quantity the tier
  exists to measure. It would satisfy ADR-0006's letter while defeating its
  purpose, and the resulting Tier-2 label would be worse than an honest Tier-0
  one.
- **Full-span MBO from the start (skip the staged gate).** Rejected: pays the
  large acquisition cost before learning whether the cheap model works, which is
  the one question that determines whether the large pull is worth making. The
  A→B→C→D ordering exists to convert that risk into a bounded stage-B cost.
- **Select the single "most realistic" fill assumption instead of sweeping.**
  Rejected, and this is the core of the ADR: "most realistic" is a researcher
  degree of freedom in a layer no existing gate audits, and selecting it is
  formally identical to selecting a Kelly fraction by hand (rejected in ADR-0013
  Decision 3) or reporting only the best fold (rejected by PBO). The sweep is
  also cheaper to defend than a defensible point estimate would be.
- **Calibrate the fill model on the evaluation span (it's "only execution").**
  Rejected: execution-layer parameters fitted on the evaluation span leak
  future information into the return series exactly as a leaked feature does, and
  ADR-0008 Decision 1's PIT discipline is not scoped to the signal layer.
- **Rely on live paper trading instead of building Tier 2.** Rejected on the same
  ground ADR-0006 rejected it: it burns calendar time and confounds execution
  error with signal decay. Decision 5(V-c) keeps live reconciliation as the
  eventual gold standard and standing re-validation trigger without letting it
  gate the build.
- **Do nothing; keep running fill-sensitive mechanisms as Tier-0 proxies.**
  Rejected as a *default*, though it remains a legitimate principal choice: the
  data-burn ordering argument in Consequences shows the proxy path consumes the
  spans a later Tier-2 evaluation would need, so drifting into it without a
  decision is the one option that is strictly dominated.
- **Accept this ADR and proceed directly to stage B.** Rejected: acceptance
  authorizes stage A only (Decision 9). Bundling the spend decision into the
  scoping decision is precisely the improvisation this ADR exists to prevent.

## References

- [Huang, Lehalle & Rosenbaum 2015, J. Am. Stat. Assoc. 110(509):107-122](https://doi.org/10.1080/01621459.2014.982278)
  — queue-reactive model; the reference fill-model class of Decision 1 and the
  source of the fill-rate-by-queue-position stylized fact in Decision 5(V-b).
  **DOI verified** via Crossref (2026-07-18).
- [Cont, Kukanov & Stoikov 2014, J. Financ. Econom. 12(1):47-88](https://doi.org/10.1093/jjfinec/nbt003)
  — price impact of order-book events; order-flow-aware slippage, the citation
  ADR-0006 Decision 1 already attaches to Tier 2. **DOI verified** via Crossref
  (2026-07-18).
- [Glosten & Milgrom 1985, J. Financ. Econ. 14(1):71-100](https://doi.org/10.1016/0304-405X(85)90044-3)
  — informed-order-flow adverse selection of passive quotes; the mechanism behind
  the adverse-selection validation criterion in Decision 5(V-b). **DOI verified**
  via Crossref (2026-07-18).
- [Harris 2003, *Trading and Exchanges: Market Microstructure for Practitioners*,
  Oxford University Press](https://global.oup.com/academic/product/trading-and-exchanges-9780195144703)
  (*practitioner*) — the touch-equals-fill bias and its direction. **Monograph:
  no DOI exists**; author (Larry Harris), publisher, year, and ISBN
  978-0-19-514470-3 confirmed against booksellers and the OUP catalogue listing.
  The publisher product page itself returned no machine-readable content at
  draft time, so the URL is carried from ADR-0006's existing citation rather than
  re-verified. **No DOI is asserted.**
- [Bailey & López de Prado 2014, J. Portfolio Manage. 40(5):94-107](https://doi.org/10.3905/jpm.2014.40.5.094)
  — Deflated Sharpe; the effective-trials estimator that Decision 4(E-e) feeds
  the fill-assumption dimension into.
- [Bailey, Borwein, López de Prado & Zhu 2017, J. Comput. Finance 20(4):39-69](https://doi.org/10.21314/JCF.2016.322)
  — PBO via CSCV; the signal-space overfitting gate whose execution-space
  counterpart Decision 4 supplies.
- [Perold 1988, J. Portfolio Manage. 14(3):4-9](https://doi.org/10.3905/jpm.1988.409150)
  — implementation shortfall; the paper-vs-reality gap ADR-0006 tiers exist to
  measure.
- [ADR-0005](ADR-0005-three-layer-separation.md) — Decision 3 (execution layer
  owns fill models, latency, queue position), Decision 4 (cross-layer tuning
  prohibited; Decision 4(E-f) here is its detection mechanism).
- [ADR-0006](ADR-0006-execution-fidelity-tiers.md) — the tier definitions this
  ADR scopes; Decision 1 (Tier-2 definition), Decision 2 (reportability rule,
  referenced not restated), Decision 3 (promotion stage gate), Decision 4
  (cost model at every tier), Decision 5 (tier as ledger column), and the
  standing Tier-2 fill-model validation Obligation.
- [ADR-0007](ADR-0007-two-tier-discovery-pipeline.md) — confirmation ladder;
  Benchmark 5 matched-turnover random rotor, the selection-skill control whose
  role Decision 4 mirrors for the execution layer.
- [ADR-0008](ADR-0008-integrity-non-negotiables.md) — Decision 1 (PIT/leakage
  canaries, applied to execution-layer parameters by Decision 4(E-d)), Decision 5
  (burned-data ledger; the data-burn ordering argument), Decision 6 (family-wise
  trial register; the (config × Kelly-fraction × fill-assumption) family).
- [ADR-0010](ADR-0010-live-capital-escalation.md) — live-vs-shadow tracking; the
  eventual gold-standard validation of Decision 5(V-c) and the standing
  re-validation trigger.
- [ADR-0011](ADR-0011-two-level-data-storage-and-provenance-policy.md) —
  Decisions 1/3/4/5; the storage and pre-ingest registration rules of Decision 7.
- [ADR-0013](ADR-0013-aggressive-geometric-growth-mandate.md) — Decision 3
  (swept Kelly fraction: the idiom Decision 4 applies to the fill assumption),
  Decision 4 (multiplicity carries the swept dimension), Decision 8 (non-waivable
  integrity core, more binding under leverage).
- [ADR-0015](ADR-0015-ratified-pool-hold-verdict-precondition.md) — the ratified
  pool HOLD and its disjoint-window verdict precondition, which Decision 8 states
  this ADR does **not** lift.
- [config/data_sources.yaml](../../config/data_sources.yaml) — the upstream
  registry Decision 7 requires before any ingest.
- [backfill_admission_plan_2026-07-17.md](../research_notes/backfill_admission_plan_2026-07-17.md)
  §OD-G — the open spread/liquidity-mechanism decision this ADR scopes a
  resolution path for; [program_roadmap_2026-07-17.md](../research_notes/program_roadmap_2026-07-17.md)
  Phase 3 — the forward-sourcing critical path this work is parallel to.
- [expert_card_H055_retro_2026-07-10.md](../reports/expert_card_H055_retro_2026-07-10.md)
  §1 — the H104 Tier-0/limit-at-wick reportability caveat ("admits more trades"
  than the limit semantic) that RC-H104-3 is blocked on.
