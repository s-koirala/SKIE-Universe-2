# OD-G — spread/liquidity-regime mechanism: setup plan (Form A / Form B)

*Last updated: 2026-07-18.*

**Living planning note (of record; not a frozen design.md).** No hypothesis
design.md is frozen, no `cov_*` column is registered, no ledger partition is
written, and no trial-register family is incremented on the strength of this
document. It scopes the two admissible forms of the spread/liquidity mechanism
(OD-G, [backfill_admission_plan_2026-07-17.md](backfill_admission_plan_2026-07-17.md) §5),
states the decision logic between them, and gives the execution checklist for
the form the operator has resolved in favour of. The strategic phasing that
wraps it is [program_roadmap_2026-07-17.md](program_roadmap_2026-07-17.md)
(Phase 3 forward sourcing); the tactical admission mechanics are the backfill
plan §4.

Governing ADRs: [ADR-0002](../decisions/ADR-0002-arsenal-admission-standard.md)
(admission, as amended), [ADR-0003](../decisions/ADR-0003-shadow-ledger-canonical-object.md)
(ledger), [ADR-0005](../decisions/ADR-0005-three-layer-separation.md) (layers),
[ADR-0006](../decisions/ADR-0006-execution-fidelity-tiers.md) (fidelity tiers),
[ADR-0007](../decisions/ADR-0007-two-tier-discovery-pipeline.md) (ladder),
[ADR-0008](../decisions/ADR-0008-integrity-non-negotiables.md) (integrity;
Decision 5 burned data), [ADR-0013](../decisions/ADR-0013-aggressive-geometric-growth-mandate.md)
(growth currency), [ADR-0014](../decisions/ADR-0014-provisional-candidate-pool-screen-verdict.md)
(screen/verdict), [ADR-0015](../decisions/ADR-0015-ratified-pool-hold-verdict-precondition.md)
(ratified pool hold + verdict precondition).

> **Operator state recorded 2026-07-18.** OD-G is resolved in favour of the
> **Tier-0 conditioning form (Form A)**. A provisional **ADR-0016** is being
> drafted to scope a future Tier-2 build-out (Form B). This note covers both
> branches because the resolution of *which form is admissible* is not the same
> decision as *whether to run Form A now* — §3 and §4 argue the second question
> and reach a **defer** recommendation on sequencing grounds.
>
> **Operator state updated 2026-07-19 (principal direction; of record).**
> [ADR-0016](../decisions/ADR-0016-tier2-execution-fidelity-scoping.md) is
> **accepted** (stage A only — no spend authorized; stage B requires its own
> named, dated operator authorization). The §3/§4 **defer** recommendation is
> **RATIFIED**: Form A is not run in the Step-5 batch; forward sourcing
> proceeds **overnight/Globex first**, then mean-reversion; the DEC-roll
> repair (DR-1/DR-2, cost sheet) is elevated to quote-ready top priority
> (operator-only spend, not yet authorized). OD-G re-enters on ADR-0013
> currency (computable `marginal_growth_delta`) once a second
> disjoint-coverage expert exists. The decision keying below is re-bound to
> ADR-0016's recorded objects (stage-B authorized / declined / undecided, its
> Decision 6), and the round-1 argument-audit remediations are applied in
> place ([audit trail](../audits/audit_trail_2026-07-19_odg-deliverables-argument-audit.md)).

---

## 0. Substrate feasibility finding (read before anything else)

**The registered substrate contains no quote data.** The sole raw source
([config/data_sources.yaml](../../config/data_sources.yaml)
`vendor_skie_ninja_legacy_raw_1min`) is a Databento **GLBX.MDP3 `ohlcv-1m`**
chain — open/high/low/close/volume only. There is no BBO, no depth, no trade
side, no message-level data anywhere under `data/`. Consequences, both binding:

1. **`spread_liquidity_regime` is not directly measurable in this project.**
   The covariate is registered in
   [config/conditioning_covariates.yaml](../../config/conditioning_covariates.yaml)
   as part of the ADR-0002(b) project-standard set with `cells: liquidity bands
   (registered per expert)` — i.e. the *cells are undefined until an expert
   registers them*, and no construction is specified. Any Form-A design must
   therefore pre-register a **proxy estimator** computable from OHLCV, name it
   in the design.md, and record the construction in
   `conditioning_covariates.yaml` alongside the H103 precedent (the
   `realized_vol_percentile` entry carries an explicit `input_feature` /
   `input_lookback_bars` / `reference_distribution` spec; anything less is not
   reproducible). Defensible candidate estimators, all peer-reviewed and all
   OHLCV-computable:
   - [Corwin & Schultz 2012, J. Finance 67:719-760](https://doi.org/10.1111/j.1540-6261.2012.01729.x)
     — high-low spread estimator (two-day high/low ratios).
   - [Abdi & Ranaldo 2017, Rev. Financ. Stud. 30:4437-4480](https://doi.org/10.1093/rfs/hhx084)
     — close-high-low (CHL) spread estimator. The paper's stated results:
     highest cross-sectional / average time-series correlations with the TAQ
     effective-spread benchmark, and the most accurate estimates for **less
     liquid (wide-spread) stocks**; in its smallest-effective-spread quintile
     Corwin-Schultz *outperforms* CHL (its Table III), and in the 1%-spread
     simulation CHL carries a persistent upward bias. For tick-constrained
     ES/NQ — the low-spread regime — **no estimator in this list has a
     verified bias advantage**, so the §7 primary-proxy selection must rest on
     an empirical bias characterization on this substrate, not on a headline
     gloss. *(Corrected 2026-07-19: the prior "lower bias than Corwin-Schultz
     in low-spread regimes" gloss inverted the paper's stated result domain —
     audit finding QUANT-1-11 / LITERATURE-1-2.)*
   - [Roll 1984, J. Finance 39:1127-1139](https://doi.org/10.1111/j.1540-6261.1984.tb03897.x)
     — serial-covariance effective spread (undefined for positive
     autocovariance; the failure rate must be reported, not silently floored).
   - [Amihud 2002, J. Financ. Markets 5:31-56](https://doi.org/10.1016/S1386-4181(01)00024-6)
     — illiquidity ratio |r| / dollar volume (a price-impact, not spread,
     construct — a different mechanism; do not conflate).

   The choice among these is **not** free: it is a pre-registration decision
   with an empirical justification obligation (user-global parameter rule). The
   honest form is to select one primary estimator on documented bias
   characteristics for liquid index futures, register the others as declared
   sensitivity arms, and record every arm in the trial-register family — not to
   scan four proxies and report the best.

2. **The Tier-0 cost model is blind to the covariate the expert conditions on.**
   [config/instruments.yaml](../../config/instruments.yaml) sets
   `slippage_ticks_per_side: 1` for ES and NQ as a *constant*, self-documented
   as a "conservative floor pending empirical calibration"
   (1.0 follow-up `P1-H052A-COST-CALIBRATION-EMPIRICAL`), and
   [futures_rt_v1.py](../../src/skie_universe2/costs/futures_rt_v1.py) applies
   it as a fixed per-side drag. A wide-spread / thin-liquidity cell is precisely
   where a 1-tick constant is most optimistic, so **net** edge in exactly the
   cells Form A exists to isolate is biased upward by construction. This does
   not block the screen — ADR-0014 (S-c) is a **pre-cost** gross-edge condition
   and the screen tests no net claim — but it is a hard constraint on what the
   Expert Card may say, and it must be written into the card's §6 cost section
   at freeze, not discovered at the verdict.

Neither finding kills Form A. Both make its evidentiary ceiling lower than the
mechanism's name suggests, and both belong in §5's pre-registration step.

---

## 1. The two forms

### Form A — Tier-0 conditioning expert (the resolved-now form)

**One-line statement.** A directional expert that takes liquidity at bar close
and whose conditional-edge scan is partitioned by a pre-registered, OHLCV-proxied
spread/liquidity-regime covariate.

| Element | Specification |
|---|---|
| **Estimand (S-c)** | Per-cell **pre-cost** per-session strategy log-return edge, conditional on the declared `cov_spread_liquidity_regime` bands, on unit exposure — identical in kind to the estimand of RC-H101-2 / RC-H103-2. ADR-0013 currency (geometric growth) enters at the verdict, not the screen. |
| **Signal layer (ADR-0005 D1)** | May consume: the OHLCV bar history at or before bar *t*, the registered features, and the liquidity-proxy covariate value at *t* (causal, no smoothing). Emits **direction + calibrated confidence only**. May NOT consume: any fill assumption, any spread-capture premise, any quote or queue quantity (none exists in-substrate anyway). |
| **Position layer (ADR-0005 D2)** | Untouched from the existing stack: the registered Kelly sweep {0.5, 0.75, 1.0, 1.25} ([policy/kelly_sweep.py](../../src/skie_universe2/policy/kelly_sweep.py)), all four fractions materialized, none selected (blocked; CLAUDE.md Phase-1 record). |
| **Execution layer (ADR-0005 D3 / ADR-0006 D1)** | **Tier 0 — market order, bar close**, via [tier0_barclose.py](../../src/skie_universe2/execution/tier0_barclose.py). `execution_tier: 0` recorded in the shadow ledger (ADR-0006 D5) and in the pool record's `provenance.execution_tier`. |
| **Permitted claims** | (i) The direction of the *pre-cost* conditional edge in a declared liquidity band; (ii) the persistence of that edge (S-d DSR/PBO); (iii) the ex-ante selectability of the band (S-e); (iv) net-of-cost figures **explicitly labelled Tier-0, constant-1-tick-slippage**, per ADR-0008 D2's requirement that gross and net come from the same ledger rows. |
| **Forbidden claims (ADR-0006 D2)** | Any spread capture, any passive/limit fill, any queue-position or adverse-selection argument, any scalping hold-time claim, any liquidity-provision framing, any interbar entry. These are unreportable below Tier 2 and no downgraded variant is run in their place (backfill plan §5 OD-G: the block is reported, not worked around). |

**Where the choice is recorded.** Per the operator instruction and ADR-0005 D4
(cross-layer tuning prohibited), the Tier-0 market-at-close decision is written
into the design.md's **execution-layer section** — *not* into the signal
section, and *not* as an implicit property of the harness. The purpose is
structural: an execution assumption recorded at the execution layer is
auditable against ADR-0006, whereas the same assumption smuggled into the
signal description becomes an untestable premise of the mechanism. The design
must additionally carry an explicit negative clause: *"this expert makes no
fill-timing claim; if the mechanism's premise later requires one, the promotion
is an ADR-0006 D3 stage gate, not an amendment to this section."*

**What Form A is not.** It is not "the liquidity strategy at lower fidelity." It
is a different hypothesis: *does directional edge vary across liquidity states?*
— a conditioning question — as opposed to *can we monetise the spread?* — a
microstructure question Form A cannot pose. Conflating them is the specific
error ADR-0006 D2 exists to prevent.

### Form B — Tier-2 liquidity mechanism (target; blocked)

**One-line statement.** The actual mechanism: passive or spread-capturing
execution whose edge *is* the liquidity premium, evaluated with a queue model.

Requirements, none of which the project currently has:

- **Substrate.** Tick or MBP/MBO data for ES/NQ (Databento GLBX.MDP3 `mbp-1`
  or `mbo`), registered in `config/data_sources.yaml` before ingest per
  ADR-0011 D3. Operator-authorised vendor spend, in the same class as the open
  `P1-2.0-DATABENTO-DEC-ROLL-REPULL`.
- **Queue-position model + latency assumption**, per ADR-0006 D1 Tier 2, with
  order-flow-aware slippage
  ([Cont, Kukanov & Stoikov 2014](https://doi.org/10.1093/jjfinec/nbt003)).
- **Validation obligation.** ADR-0006 Consequences: *"the Tier-2 fill model
  itself must be validated against live fills (ADR-0010 tracking data) before
  its outputs are confirmation-grade."* At |arsenal| = 0 there is no live
  capital and therefore no live fills — so Form B's outputs are **not
  confirmation-grade until after a champion is trading**, which is Phase 5. This
  is the single most under-appreciated constraint on Form B and it should be
  stated in ADR-0016 rather than discovered later. *(ADR-0016 D5(V-c) now
  states it: (V-a)/(V-b) gate the build; live reconciliation is the standing
  re-validation condition, while the ADR-0006 Obligation continues to withhold
  confirmation-grade from Tier-2 outputs until live fills exist — a
  build-gate vs confirmation-grade distinction the round-1 audit's refute gate
  confirmed consistent across all three documents.)*
- **Tier-1 as an intermediate.** [tier1_intrabar.py](../../src/skie_universe2/execution/tier1_intrabar.py)
  exists untracked in the working tree; Tier 1 is the minimum for stop/pyramid
  exhibits but is **not** sufficient for any Form-B claim.

Form B is therefore blocked on ADR-0016 stages B–D (substrate acquisition →
queue/latency model → live-fill validation), with stage D structurally
downstream of first live capital.

**Governance question for the ADR-0016 draft — RESOLVED 2026-07-19 (ADR-0016
Decision 10).**
ADR-0006 D3 makes tier promotion a stage gate effected "with a **design.md
amendment**," while the project's pre-registration discipline makes a frozen
design.md immutable — any change requires a **new HID**. These two rules
prescribe different objects for the same event. ADR-0016 Decision 10 resolves
it on the **estimand**: unchanged estimand = same-HID tier promotion via an
append-only execution-tier addendum (own SHA; frozen sections untouched);
changed estimand = **successor HID** subject to ADR-0008 D5. **OD-G is the
changed-estimand case (D10(b))** — Form A's conditioning question vs Form B's
microstructure question ("What Form A is not", above) — so Form B inherits
none of Form A's burned spans, §4's expensive case is the governing one, and
that is exactly why the §4 defer recommendation is ratified.

---

## 2. The cosmetic-novelty risk (the binding analytical problem)

### 2.1 The precondition Form A is being recruited to satisfy

ADR-0015 holds the set-level VERDICT until the pool contains **≥ 2 distinct
`expert_hash` values whose coverage vectors are non-overlapping**
([pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml)
`verdict_precondition`, `min_distinct_disjoint_coverage: 2`, operator-directed
and provisional). The current pool state:

| Quantity | Value |
|---|---|
| Records | 8 (2 HIDs × 4 Kelly fractions) |
| Distinct `expert_hash` | **1** (`orb_first_hour_k1.0@1.0.0`) |
| Union of `competence_window_cells` | `ES:first_hour_up`, `ES:stress`, `NQ:first_hour_up`, `NQ:high_vol`, `NQ:non_stress` |

**Distinct hash is trivial.** Any new expert implementation produces a new
content hash by definition; the first half of the precondition is satisfied by
writing a file. **The binding half is non-overlap**, and it is the half a
cosmetically-novel candidate defeats.

### 2.2 Why Form A is the mechanism most exposed to this failure

Three structural correlations, each documented, push a liquidity-conditioned
RTH expert onto the same bars the pool already holds:

1. **Liquidity is a time-of-day variable.** Intraday spreads follow a
   **reverse-J**: most elevated at the open, declining through midday, rising
   again toward the close
   ([McInish & Wood 1992, J. Finance 47:753-764](https://doi.org/10.1111/j.1540-6261.1992.tb04408.x));
   intraday volatility and trading activity show the related U-shape
   ([Wood, McInish & Ord 1985, J. Finance 40:723-739](https://doi.org/10.1111/j.1540-6261.1985.tb04996.x)
   — a returns/volatility/activity study, not a spread study). A "wide-spread"
   cell defined on any of the §0 proxies will therefore be disproportionately
   populated by **opening bars** — the exact 12-bar window (09:30–10:30 NY on
   the 5-minute grid) the ORB expert trades — **and by closing bars**, which
   ORB does not trade; the M3(c) expected-overlap prediction must state both
   loadings. *(Corrected 2026-07-19: the prior "U-shape, widest at the open,
   narrowing through midday" description misattributed WMO 1985 and cited
   Chordia-Roll-Subrahmanyam 2001, a daily-frequency aggregate-liquidity
   study, for an intraday claim — CRS dropped; audit finding QUANT-1-12 /
   LITERATURE-1-1.)*
2. **Liquidity is a volatility variable.** All four §0 estimators are functions
   of price ranges or |return|; they are mechanically correlated with realized
   volatility. The pool already covers volatility cells (`NQ:high_vol`,
   `ES:stress`, `NQ:non_stress`), so a liquidity partition risks being a noisy
   re-labelling of a partition already in the pool.
3. **Same session, same instruments, same bar grid.** Unlike overnight/Globex,
   nothing about Form A moves it off the 78-bar RTH session
   ([run_screen_h101_h103.py](../../scripts/run_screen_h101_h103.py):
   `RTH_BARS_PER_SESSION = 78`).

The failure mode is therefore precise: **Form A can satisfy the letter of the
coverage-novelty precondition while failing its purpose.** A cell named
`ES:wide_spread` has label-Jaccard **0** against `{ES:first_hour_up,
ES:stress, …}` — zero overlap, precondition MET — even if 80% of its realized
active bars are the same bars ORB was long in. The schema's
`complementarity.window_overlap_jaccard` is specified as *"Jaccard overlap of
competence-window **cells**"*, i.e. over cell **labels**, which is exactly the
gameable form.

### 2.3 Mitigation (mandatory if Form A is ever run)

**M1 — Measure and report disjointness on realized competence windows, not
only on names.** The ADR-0015 precondition as recorded in the accepted ADR and
[pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml) is
**label-based** (union of `competence_window_cells` per distinct
`expert_hash`) and stands until amended — a living note cannot rewrite an
accepted rule (ADR-0015 Consequences: supersession "through a new ADR, never
by silent edit"; audit finding QUANT-1-7). M1 is therefore a **mandatory
REPORTED companion statistic**: alongside the label-based precondition,
compute a Jaccard index over the **realized active-bar index sets**:

```
J(A, B) = |T_A ∩ T_B| / |T_A ∪ T_B|
```

where `T_X` is the set of `(instrument, session_date, bar_index)` tuples on
which expert *X* held non-zero exposure **within its passing competence-window
cells**, taken from the shadow ledger (ADR-0003 — the sole evidence source, so
this is computable from existing partitions with no new run). Report a session-
level Jaccard alongside the bar-level one; they answer different questions
("same days?" vs "same minutes?") and a candidate that is disjoint at bar level
but identical at session level is still poor diversification for an allocator
that switches at session cadence. A schema addendum making realized-bar
disjointness a first-class `verdict_precondition` input is **proposed as an
ADR-0015 amendment** (operator acceptance required); until accepted, M1
informs the operator-gated lift action (ADR-0015 Decision 3) and gates
nothing mechanically.

**M2 — Set the disjointness criterion before the scan, and record it as
operator-directed.** No calibrated threshold for "non-overlapping" exists (ADR-0015
is explicit that the ≥ 2 rule is an operator instruction, not a derived bound),
and inventing a numeric Jaccard cutoff here would be exactly the "hand-set
constant wearing a derivation costume" ADR-0015 Alternatives rejects. The
honest form: **pre-register the realized-overlap statistic as a reported
quantity**, declare the operator's acceptance decision on it as a named,
dated operator action (mirroring ADR-0015's `lift_action`), and let the number
inform rather than mechanically gate. What is *not* acceptable is computing the
overlap after seeing the screen result.

**M3 — Pre-registered mechanism-distinctness check.** Before freeze, the design
must demonstrate that Form A is a **distinct mechanism**, not a re-parameterised
ORB. Minimum content, all computable pre-scan on existing ledger/feature data
and therefore costing no OOS span:
- (a) **Entry-rule non-nesting**: an explicit statement of the entry/exit rule
  with a demonstration that it is not a function of the opening range. If the
  signal is "breakout of X conditioned on liquidity," it *is* ORB with a
  covariate and should be declared as such (a re-parameterisation is a
  legitimate object — it is just not a source of coverage novelty, and it must
  not be presented as one).
- (b) **Covariate near-collinearity report**: the association between the
  chosen liquidity proxy and (i) `time_of_day_bucket` and (ii)
  `realized_vol_percentile` / `cov_regime_state_h900`, over the training
  windows only. High association does not disqualify — it *predicts* the
  overlap M1 measures, and it is better known before the burn than after.
- (c) **Expected-overlap statement**: a written, pre-scan prediction of the
  realized-bar overlap against the existing pool coverage, so the post-scan
  number can be compared against it rather than rationalised. The prediction
  must state both the open-side loading (ORB-overlapping) and the close-side
  loading (non-ORB) implied by the reverse-J intraday spread pattern (§2.2).

**M4 — Cell membership must be rule-based, not latent (S-e).** See §5.

---

## 3. Ranking against the other three approved mechanisms

The four operator-approved directions (backfill plan §3; roadmap Phase 3),
ranked on **structural disjointness from the existing ORB pool coverage** —
the property that actually lifts the ADR-0015 precondition:

| Rank | Mechanism | Basis of disjointness | Strength | Principal feasibility gate |
|---|---|---|---|---|
| **1** | **Overnight / Globex** | **Session.** ETH bars (16:00–09:30 NY) are a disjoint bar set from the 78-bar RTH session **by construction** — the intersection with `first_hour_up` is the empty set, provably, before any scan. | **Strongest at bar level** (identity, not estimate). Session-level overlap is near-complete (same trading dates), so per M1 both granularities are reported; bar-level disjointness is the axis the ADR-0015 coverage precondition needs. | ETH-bars substrate check: cheap, no vendor spend. **But the December blind spot binds hardest here** — all 10 DEC-roll exclusion windows are Globex-session windows, plus the post-2025-12-08 tail ([cost sheet §2.1.4](databento_pull_spec_cost_sheet_2026-07-18.md)). Screenable NOW at conditional grade on the exclusion-filtered substrate with the blind spot declared in the design; **DR-1/DR-2 is prerequisite for December-inclusive or confirmation-grade overnight evidence** *(reconciled 2026-07-19, audit finding QUANT-1-4)*. |
| **2** | **Mean-reversion** | **State.** `variance_ratio_state` = `range` is the complement of the trend state ORB exploits ([Lo & MacKinlay 1988, Rev. Financ. Stud. 1(1):41-66](https://doi.org/10.1093/rfs/1.1.41); [variance_ratio_state.py](../../src/skie_universe2/features/variance_ratio_state.py) already built and registered). | **Moderate.** Genuinely different mechanism and a partition already in the project-standard set — but **same sessions, same bars**, so realized-bar overlap must be *measured* (M1), not assumed. | None material: the feature exists, the substrate exists. Cheapest of the four to reach freeze. |
| **3** | **Macro-calendar-conditioned** | **Trigger.** Release timestamps (08:30 ET data, 14:00 ET FOMC) are an exogenous event set, largely outside the first hour. | **Moderate**, but partly *illusory*: 08:30 releases sit one hour before the RTH open and their volatility propagates directly into the ORB window. | **Hard gate:** no macro-calendar source is registered in `config/data_sources.yaml`. A PIT-correct release calendar (with *as-released* timestamps, not restated ones) must be acquired and registered first. Highest infrastructure cost after Form B. |
| **4** | **Spread/liquidity (Form A)** | **Covariate label only.** No session, state, or trigger separation — see §2.2. | **Weakest.** Its disjointness claim rests on a partition that is mechanically correlated with both time-of-day and volatility, i.e. with the two dimensions the pool already covers. | §0: covariate not directly measurable (proxy pre-registration required); cost model blind to the covariate. |

**Recommendation on §3: do not run Form A in the current Step-5 batch.**

Grounds:

1. **It is the weakest instrument for the job it is being recruited for.** The
   binding constraint is the ADR-0015 non-overlap requirement, and Form A is
   the only one of the four whose disjointness cannot be established *a priori*
   — it can only be measured after the spans are burned. Overnight/Globex
   delivers the same precondition-lift with disjointness known **before** the
   run.
2. **Its screen carries an extra, uncalibrated degree of freedom.** The proxy
   choice (§0) is a fork the other three mechanisms do not have. Under the
   enacted level of 0.7401 the screen is deliberately loose, and adding a
   four-way construction fork to a loose screen is the worst available
   combination — the H103 exhibit already on record is the cautionary case: the
   ES stress-cell mean **flips sign** with the percentile-boundary construction
   (leaked full-sample −5.0922e-04/session vs certified per-origin
   +1.0295e-04/session; `construction_dependence_note` in
   `conditioning_covariates.yaml`), and the standing status of the Lundström
   prior is **UNRESOLVED** as a direct result. A liquidity proxy is a strictly
   more construction-sensitive object than a volatility percentile.
3. **It burns spans that Form B needs more than Form A does** — §4.

Form A is not rejected. It is **queued behind overnight/Globex and
mean-reversion**, and its value is re-assessed once the pool has a genuinely
disjoint second expert and the ADR-0015 precondition is lifted — at which point
Form A's `complementarity.marginal_growth_delta` becomes computable and the
mechanism can be judged on the currency that actually matters (ADR-0013) rather
than on a coverage-novelty proxy.

---

## 4. The data-burn ordering argument

**The rule.** ADR-0008 Decision 5: *"Every OOS span consumed by any HID is
recorded in `config/burned_data_ledger.yaml`; a burned span is dead to
successor hypotheses' confirmation-tier evidence."* Under the ADR-0004 rolling
regime the ledger is updated **per evaluation window**, and the note is explicit
that rolling evaluation "burns faster than 1.0." The existing screens each
consumed 15 rolling windows per instrument across the ES+NQ 2015–2025 substrate
— the **only** in-project substrate (backfill plan §3).

**The consequence for OD-G.** Form A and Form B are the *same mechanism at two
fidelities on the same bars*. Running Form A's screen consumes exactly the OOS
spans on which Form B's Tier-2 evidence would later have to be confirmed. Two
cases were open at drafting; ADR-0016 Decision 10 (2026-07-19) resolves OD-G
into the **first** — successor HID, the changed-estimand case D10(b):

- **If Form B is a successor HID** (the pre-registration-immutability reading):
  ADR-0008 D5 bites directly — those spans are **dead to Form B's
  confirmation-tier evidence**. Form B would be reduced to whatever span
  remains, on a substrate with no unburned reserve. This is the expensive case,
  and it is the one the current rule-set most plainly implies.
- **If Form B is a tier promotion of the same HID** (the ADR-0006 D3 reading):
  the higher-tier result *supersedes* the lower-tier one and the successor
  clause does not apply. But the promotion is only meaningful if the two forms
  test the same estimand — and they do **not** (§1: conditioning question vs
  microstructure question). Claiming promotion to reuse the spans would be
  choosing the reading that preserves data rather than the one that describes
  the science.

Either way, the asymmetry is decisive: **Form A's information value is low and
its span cost is the same as Form B's; Form B's information value is high and it
cannot run yet.** Burning a scarce, non-renewable resource on the low-value
variant of a mechanism, before the high-value variant is even scoped, is a
strictly dominated sequencing choice.

**Recommendation on §4: do not burn spans on Form A before the ADR-0016
stage-B decision is recorded.** The promotion-vs-successor question is now
resolved (ADR-0016 D10(b): Form B is a successor HID; Form A's spans are dead
to it with full ADR-0008 D5 force). Orderings re-keyed 2026-07-19 to
ADR-0016's recorded decision objects — stage-B **authorized / declined /
undecided** per its Decision 6 (audit finding QUANT-1-2):

- **Preferred — defer (RATIFIED by principal direction 2026-07-19).** Source
  overnight/Globex (and, if a second is wanted, mean-reversion) for the
  Step-5 batch. Hold OD-G Form A until the ADR-0016 **stage-B decision** is
  recorded. If stage B is **declined** (the recorded NO-GO terminal object),
  Form A becomes the terminal form of the mechanism, its span cost is no
  longer an opportunity cost, and it can be queued on its own merits. If
  stage B is **authorized**, sequence Form B first and never run Form A as a
  screen at all.
- **Acceptable-if-overridden — reserve.** If the operator wants Form A in the
  Step-5 batch regardless, ring-fence an explicit span reserve for Form B
  (declared in `burned_data_ledger.yaml` at Form A's freeze, not after) and run
  Form A only on the complement. This costs Form A statistical power and must be
  reflected in its power analysis at pre-registration — not discovered as a null
  afterwards.

---

## 5. Execution checklist — Form A, if and when run

Ordered; each step gated on the prior. Nothing below is authorisation to
proceed — this is the procedure for when the §6 gate returns RUN-A.

**5.1 `hypothesis-new`.** Assign the HID (`/hypothesis-new`; next free in the
H1xx forward series), with the mechanism statement, the citation basis, and an
explicit declaration that this is the **Tier-0 conditioning form** of OD-G.

**5.2 Pre-registration — freeze design.md AND the conditioning set BEFORE any
scan (ADR-0002(b), non-waivable; ADR-0008 D4).** `/preregister`. Must contain,
at minimum:
- **§ Execution layer:** Tier 0, market order at bar close, via
  `tier0_barclose.py`; the ADR-0006 D2 forbidden-claims list reproduced
  verbatim; the negative clause from §1 ("no fill-timing claim is made").
- **§ Conditioning set:** the liquidity-proxy estimator selected in §0, with
  `input_feature`, `input_lookback_bars`, and `reference_distribution`
  specified to the H103 standard (training-window empirical CDF, per-origin —
  the leakage-clean construction; the full-sample-cutoff construction is a
  known sign-flipping defect on this project's own evidence). Declared
  sensitivity arms named here, or not run.
- **§ Cells:** the liquidity bands, named, with the S-e classification of each
  (§5.4).
- **§ Cost:** the §0 finding that `slippage_ticks_per_side` is constant and
  therefore optimistic in the wide-spread cells.
- **§ Mechanism-distinctness:** M3(a)–(c) from §2.3, including the written
  pre-scan overlap prediction.
- Register the `cov_*` column(s) in
  [config/covariates.yaml](../../config/covariates.yaml) **in the same commit**
  as the freeze (the file's own enforcement rule: a ledger frame's `cov_*`
  columns must exactly equal the registered set for the expert family, and a
  family absent from the file has the empty registered set — an unregistered
  column is refused at write time).
- **Power analysis** (`power-analysis`, post-registration / pre-data): required
  n per cell at the enacted level. Note the H103 precedent — both cells failed
  the §8 25% precision gate at n = 437 / 313 sessions — so a liquidity band that
  partitions the same sessions more finely is at material risk of being
  underpowered before it starts. If the power analysis says the binding cells
  cannot reach precision on the available substrate, **stop here**: that is a
  free, span-cost-zero null.

**5.3 Tier-0 backfill (ADR-0003 D3, append-only).** New
`expert_id@version` × {ES, NQ} × 4 Kelly fractions
(`..._k0.5@v` … `..._k1.25@v`, all four materialized, none selected) through
the Expert-contract / Tier-0 stack via
[run_shadow_ledger_backfill.py](../../scripts/run_shadow_ledger_backfill.py).
New partitions only; no in-place edit of any existing partition. `execution_tier
= 0` recorded per ADR-0006 D5. ReproLog emitted (13 fields).

**5.4 ADR-0014 SCREEN at the enacted level.**
- Level: `screening_error_rate_target` from
  [config/multipletest_family.yaml](../../config/multipletest_family.yaml),
  which **governs** — currently `0.7400550140326007`; criterion **retain-fwer**
  (Romano-Wolf stays; no BH; `prds_argument_ref` null). Read the value from the
  config at runtime; do not transcribe it into code.
- **(S-d) bounds derived at runtime from that level, never hard-coded:**
  `DSR ≥ 1 − level = 0.2599449859673993` and `PBO ≤ level = 0.7400550140326007`.
- **(S-c):** Romano-Wolf StepM within the scan, ADR-0004
  serial-dependence-preserving block bootstrap; a new `rc-*` register family.
- **(S-e) — the classification obligation, stated explicitly.** Per the amended
  screen rule (CLAUDE.md; `detection_cost_caveat` in
  `conditioning_covariates.yaml`; pool schema `detection_latency_bars`
  `status: QUANTIFIED_2026-07-17_P1-2.0-H900-BOCPD-WHITENED`):
  - a cell whose membership derives from a **latent state** **fails S-e
    outright** — the whitened on-ledger ROC established that the unsupervised
    latent-state detection latency is **UNATTAINABLE** (no accurate,
    non-degenerate operating point on either instrument), and
    `detection_latency_bars` records null for such a cell;
  - a **rule-based causal** cell (membership computable from realized data at
    decision time) carries its **structural observation lag** in RTH bars — the
    existing precedents are 0 bars for session-start-determined cells and 12
    bars for first-hour-determined cells (`run_screen_h101_h103.py`);
  - the supervised-CUSUM oracle latency (2–3 bars) remains **forbidden** as the
    input.
  **Design consequence:** the liquidity bands must be specified as *rule-based
  causal* functions of realized OHLCV (e.g. a proxy value scored against the
  training-window empirical CDF, evaluated at a declared decision bar), with the
  observation lag stated in the design. A band defined by a filtered/latent
  liquidity state fails S-e and the screen cannot pass — this is a
  design-time constraint, not a runtime discovery.
- Every screen evaluation, pass or fail, increments the family-wise trial
  register (ADR-0008 D6) with the per-trial record: HID/scan id, Sharpe
  estimate, ledger-partition pointer, clustering metadata.

**5.5 Disposition and artifacts.**
- Disposition: `pool-hold-reconsider` (screen pass; verdict deferred under the
  ADR-0015 hold) or `archive-no-persistent-window` (screen fail;
  `archive-no-gross-edge` as the sub-reason if no cell shows gross edge).
  "Fail" is not a disposition (ADR-0009).
- **Expert Card** (8 sections, script-generated from the run outputs — never
  hand-copied, ADR-0009 D3).
- **Pool append**: one record per (expert × Kelly fraction × ledger slice),
  generated from card §§3–5, into
  [pool_ledger.jsonl](../../data/processed/pool_ledger/pool_ledger.jsonl).
- **Trial-register increment** (already required at 5.4; the record is the
  artifact).
- **Burned-data mirror**: every consumed OOS span written to
  [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml),
  mirrored from card §7, per evaluation window.
- **M1 overlap computation** (§2.3) run against the existing pool coverage and
  reported alongside the disposition, with the M3(c) pre-scan prediction quoted
  for comparison.
- Round-tripped through `audit-remediate-loop` (3-round cap) before commit;
  commit via `/commit-with-provenance`.

---

## 6. Decision gate — Form A vs Form B

The gate is on the **ADR-0016 stage-B decision state** — authorized /
declined / undecided, the recorded objects its Decision 6 defines (stage A is
the scoping ADR itself, **accepted 2026-07-19**; a "stage-A go/no-go" does not
exist as an object — re-keyed per audit finding QUANT-1-2) — and on the
**state of the pool's second expert**. Read down the first two columns; the
action is the operator's.

| ADR-0016 stage-B decision (Tier-2 substrate spend) | Pool state | Action on OD-G | Rationale |
|---|---|---|---|
| **Undecided** (current state) | 1 distinct `expert_hash` | **DEFER Form A.** Source overnight/Globex for Step-5. | §4: Form A's spans are Form B's spans; do not burn them before the fidelity question is answered. Overnight/Globex lifts the ADR-0015 precondition with provable disjointness (§3). |
| **Undecided** | ≥ 2 distinct hashes, disjoint (precondition MET) | **DEFER Form A**; proceed to the operator-authorised first-admission VERDICT. | The precondition is already lifted; Form A's only near-term argument (coverage novelty) is moot, and its `marginal_growth_delta` becomes computable after the first admission — judge it then, on ADR-0013 currency. |
| **Authorized** (stage-B spend granted) | any | **DROP Form A as a screen.** Scope Form B under ADR-0016 stages B–D; reserve the spans. | Running Form A first destroys Form B's confirmation-tier evidence (successor HID, ADR-0016 D10(b)) for a strictly less informative result. Live-fill reconciliation (ADR-0016 V-c; ADR-0006 Obligation) sits downstream of first live capital — Tier-2 outputs reach confirmation-grade only then. |
| **Declined** (stage B declined / not scheduled) | 1 distinct hash | **HOLD Form A behind overnight/Globex + mean-reversion**; re-assess after. | Form A is now the terminal form (no opportunity cost), but it remains the weakest of the four on structural disjointness (§3) and should not lead the queue. |
| **Declined** | ≥ 2 distinct hashes | **RUN Form A** under the full §5 checklist, including M1–M4. | Terminal form, no span opportunity cost, and set-relative value is measurable against a real incumbent set. This is the only cell in which Form A is the right next action. |
| Any | Form A design cannot state a **rule-based causal** cell definition | **BLOCK.** Report to operator; do not run a downgraded version. | S-e fails outright for latent-state cells (§5.4); running anyway certifies nothing and burns spans. |
| Any | Power analysis (5.2) says the binding cells cannot reach precision | **STOP at 5.2.** Record the null. | A span-cost-zero null is the cheapest true result available; the H103 precision-gate failures at n = 437/313 make this a live possibility. |

**Standing conditions on every RUN cell.** (i) Realized-bar and session-level
disjointness (M1) are computed and **REPORTED alongside** the label-based
ADR-0015 verdict precondition, which **governs until the proposed ADR-0015
amendment is accepted** (§2.3 M1; a living note cannot rewrite the accepted
rule); (ii) meeting it is *reported*, never acted on autonomously — the lift is
a named, dated operator authorization (ADR-0015 Decision 3); (iii) the ADR-0006
D2 forbidden-claims list binds every artifact Form A produces, permanently, at
Tier 0.

---

## 7. Open items this note does not resolve

- **ADR-0016 stage-B decision** — named, dated operator authorization or
  decline of the bounded MBO validation pull (Databento `mbo` + `mbp-10` for
  ES; vendor spend; ADR-0011 D3 registration precedes ingest). Stage A — the
  scoping ADR — is **accepted 2026-07-19**; the stage-B decision state is
  **undecided**.
- **The promotion-vs-successor governance question — RESOLVED 2026-07-19** by
  ADR-0016 Decision 10: unchanged estimand = same-HID promotion via
  append-only execution-tier addendum; changed estimand = successor HID under
  ADR-0008 D5. OD-G is the changed-estimand case (D10(b)): Form B inherits
  none of Form A's spans.
- **Liquidity-proxy selection** (§0) — which of Corwin-Schultz / Abdi-Ranaldo /
  Roll / Amihud is primary, on documented bias characteristics for liquid index
  futures, with the others declared as sensitivity arms or dropped.
- **Empirical slippage calibration** (`P1-H052A-COST-CALIBRATION-EMPIRICAL`,
  carried from 1.0) — the constant 1-tick per-side prior is the direct source of
  the §0(2) net-edge bias in wide-spread cells.
- **Overnight/Globex substrate check** — confirm the roll-adjusted store carries
  ETH bars. Cheap, blocking for the recommended Step-5 alternative, and worth
  doing before this note's recommendation is acted on.
