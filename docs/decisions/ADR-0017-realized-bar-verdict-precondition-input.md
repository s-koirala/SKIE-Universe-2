---
name: ADR-0017 — Realized-bar verdict-precondition input (amends ADR-0015)
description: Adds the pairwise realized-bar Jaccard over shadow-ledger active bars as a first-class, reported input of the ADR-0015 verdict precondition — the statistic the 2026-07-19 label/realized inversion showed the label rule cannot see; keeps the block provisional, operator-directed, and reporting-check-only; changes no disposition, increments no register, certifies nothing
type: governance
status: accepted
date: 2026-07-19
supersedes: ""
superseded_by: ""
amended_by: ""
---

# ADR-0017 — Realized-bar verdict-precondition input (amends ADR-0015)

> **STATUS: accepted (2026-07-19, principal direction; conveyed via session;
> not self-accepted).** This ADR records an acceptance the operator already
> granted in the 2026-07-19 authorization (the same conveyance form as the
> ADR-0015/ADR-0016 acceptances); drafting the record of a granted acceptance
> is not self-acceptance. It amends ADR-0015 by ADDITION only (banner +
> `amended_by`; the ADR-0015 decision body is not rewritten — its
> Consequences' own rule: supersession "through a new ADR, never by silent
> edit"). It changes no pool disposition, increments no trial register, and
> certifies nothing.

## Context

ADR-0015 Decision 2 records the verdict precondition as a **label-based**
rule: ≥ 2 distinct `expert_hash` values whose coverage vectors — unions of
`competence_window_cells` **labels** — are pairwise non-overlapping. The
setup plan §2.2 flagged the label form as gameable at registration time
("a cell named `ES:wide_spread` has label-Jaccard 0 … even if 80% of its
realized active bars are the same bars ORB was long in") and §2.3 M1
proposed the realized-bar companion statistic, explicitly deferring its
promotion to "an ADR-0015 amendment (operator acceptance required)".

On 2026-07-19 the Phase-3 forward batch produced the empirical case, in
BOTH directions at once
([m1_realized_overlap.json](../../reports/M1_overlap/m1_realized_overlap.json)):

- **ORB↔H105** — realized-bar Jaccard **exactly 0.0** (the frozen H105
  design §12(c) identity: 452k+ overnight-ETH accrual bars, none shared
  with the ORB pool's RTH bars) — yet **label-BLOCKED**, solely because two
  different constructions (ORB's RTH-open full-sample rvol tercile; H105's
  overnight-entry per-origin tercile) share the string `NQ:high_vol`.
- **ORB↔H106** — **label-disjoint** (no shared cell name), yet sharing
  **8.9%** of realized bars (H106's range-state bars include RTH bars ORB
  holds).

The pair the label rule certifies is the weaker disjointness; the pair it
blocks is the strongest in the pool. The quantity the precondition exists
to guarantee — that the set-level VERDICT adjudicates experts whose
competence windows are actually distinct — is measured by the realized-bar
statistic, not the labels.

## Decision

1. **The realized-bar overlap becomes a FIRST-CLASS input of the ADR-0015
   verdict precondition.** Statistic: the pairwise **realized-bar Jaccard**
   `J(A,B) = |T_A ∩ T_B| / |T_A ∪ T_B|` where `T_X` is the set of
   `(instrument, bar_ts)` tuples on which expert X held non-zero exposure
   within its passing competence-window sessions, computed from the shadow
   ledger (ADR-0003, the sole evidence source) by the existing machinery
   [scripts/run_m1_overlap_report.py](../../scripts/run_m1_overlap_report.py)
   — with the session-level Jaccard reported alongside (the two
   granularities answer different questions; setup plan §2.3).
2. **Both bases are REPORTED; neither gates mechanically.** The
   precondition block stays `provisional: true`, operator-directed, and
   `enforcement: reporting-check-only` (ADR-0015 Decisions 2–3 unchanged in
   force). The reporting checker
   ([check_verdict_precondition.py](../../scripts/audits/check_verdict_precondition.py))
   reports the realized-bar basis ALONGSIDE the label basis (it reads the
   M1 artifact when present and says so plainly when absent); its
   exit-code contract (0 MET / 1 BLOCKED / 2 error) keys on the registered
   label rule exactly as before, so no consumer's semantics change — the
   realized-bar report is additive context for the operator's lift
   decision.
3. **No numeric disjointness cutoff is introduced.** Per the setup plan
   §2.3 M2 and the ADR-0015 Alternatives ("a 'derived' threshold computed
   from nothing would be a hand-set constant wearing a derivation
   costume"), the realized-bar input is a reported quantity the operator
   weighs; the pre-scan §12(c) prediction-vs-realization comparison is the
   discipline against post-hoc rationalization. Any future numeric bound
   requires its own derivation and its own ADR.
4. **Precedence note for the record:** the 2026-07-19 lift (ADR-0015
   banner record) was granted with the **realized-bar basis operative** —
   the first application of this amendment's input.

## Enactment

Accepted and enacted 2026-07-19: (i) ADR-0015 receives the
`amended_by: ADR-0017` banner treatment (decision body untouched); (ii)
[config/pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml)
`verdict_precondition` gains a `realized_bar_input` addendum citing this
ADR (existing keys unaltered); (iii) the checker is extended per Decision 2
with its exit-code contract and existing tests preserved. Nothing else
changes; no disposition moves, no register increments.

## Consequences

- **Positive:** the precondition's letter and purpose are re-aligned — the
  quantity the operator's lift decision actually rests on is now a
  registered input with registered machinery, not a side-channel exhibit.
- **Positive:** label-namespace collisions (the `NQ:high_vol` class) stop
  masquerading as substantive blocks, and label-disjoint-but-bar-overlapping
  candidates stop masquerading as clean lifts.
- **Negative/accepted:** the realized-bar statistic is computable only
  AFTER a candidate's ledger and screen exist (it needs passing cells and
  active bars), so it cannot pre-screen a design — the §12(c) pre-scan
  prediction obligation (M3(c)) remains the ex-ante discipline.
- **Obligation:** the M1 machinery's recomputation of recorded cell
  membership must mirror each candidate's RECORDED construction (it does:
  RC-*-2 constructions for ORB, frozen-harness `_prepare_instrument` for
  the fresh candidates); any construction change is a new registered cycle.
- **Obligation:** `provisional: true` stands — once verdict outcomes
  accrue, any data-derived successor supersedes through a new ADR, never a
  silent edit (ADR-0015 Consequences, carried forward).

## Alternatives considered

- **Leave M1 a side-channel report (status quo).** Rejected: the
  2026-07-19 inversion shows the label rule and the lift-relevant quantity
  can point in opposite directions simultaneously; an input the operator
  must consult belongs in the registered block, not in session notes.
- **Replace the label rule with the realized-bar rule.** Rejected: the
  label rule is the accepted operator instruction and remains cheap,
  ex-ante computable at registration time, and useful as a first filter;
  the amendment ADDS the operative statistic rather than swapping rules —
  strictly more information, no removed guard.
- **Introduce a numeric realized-bar Jaccard cutoff.** Rejected (Decision
  3): no verdict history exists to calibrate one; it would be exactly the
  hand-set constant ADR-0015 refused.
- **Rename cells to dodge the collision (e.g. `on_high_vol`).** Rejected:
  H105's design is frozen (rename = new HID for zero information), and the
  fix would treat the symptom — the namespace — while leaving the
  gameability of labels intact.

## References

- [ADR-0015](ADR-0015-ratified-pool-hold-verdict-precondition.md) — the
  amended ADR: Decision 2 (the label rule, retained), Decision 3 (lift
  semantics, retained), Consequences (the amendment rule this ADR follows),
  and the 2026-07-19 LIFT AUTHORIZATION RECORD (the first application).
- [od_g_spread_liquidity_setup_plan_2026-07-18.md](../research_notes/od_g_spread_liquidity_setup_plan_2026-07-18.md)
  §2.2–§2.3 — the label-gameability analysis and the M1/M2 proposal this
  ADR enacts.
- [reports/M1_overlap/m1_realized_overlap.json](../../reports/M1_overlap/m1_realized_overlap.json)
  — the 2026-07-19 inversion exhibit (ReproLog run `8f40fc91f700`).
- [verdict_readiness_memo_2026-07-19.md](../research_notes/verdict_readiness_memo_2026-07-19.md)
  §2 — the operator brief that carried the exhibit.
- [ADR-0003](ADR-0003-shadow-ledger-canonical-object.md) — the ledger as
  sole evidence source (the statistic's substrate).
