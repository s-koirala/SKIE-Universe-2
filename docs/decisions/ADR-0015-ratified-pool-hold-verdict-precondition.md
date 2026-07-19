---
name: ADR-0015 — Ratified pool hold (verdict precondition at empty arsenal)
description: Records the operator-ratified HOLD of the ADR-0014 set-level VERDICT while the provisional pool has effective set size ~1 (one distinct expert_hash), and registers an operator-directed, provisional, reporting-only verdict precondition (>= 2 distinct expert hashes with non-overlapping coverage vectors) in the pool-ledger schema; changes no disposition, increments no register, certifies nothing
type: governance
status: accepted
date: 2026-07-18
supersedes: ""
superseded_by: ""
---

# ADR-0015 — Ratified pool hold (verdict precondition at empty arsenal)

> **STATUS: accepted (2026-07-18, principal direction).** This ADR records a
> HOLD the operator ratified on 2026-07-18 and was accepted by the operator the
> same day; it was drafted `proposed` and was NOT self-accepted. It amends no ADR
> decision body, changes no pool disposition, increments no trial register (no
> scan runs), and certifies nothing. The verdict precondition it registers is
> explicitly **operator-directed and provisional** — an operator instruction, not
> a derived threshold — with enforcement limited to a reporting check. The lift
> action remains a named, explicit operator authorization; a MET precondition is
> reported, never acted on autonomously.

> **LIFT AUTHORIZATION RECORD (Decision 3 `lift_action`): HOLD LIFTED —
> first-admission VERDICT AUTHORIZED. Authorized by principal direction
> 2026-07-19; conveyed via session; not self-authorized.** This is the named,
> dated operator authorization Decision 3 requires; the decision body above is
> not rewritten. Grounds, both cited verbatim per the authorization record:
>
> - **(i) Label basis (the registered rule): MET.**
>   [check_verdict_precondition.py](../../scripts/audits/check_verdict_precondition.py)
>   exits 0 — 2 pairwise-disjoint coverage vectors across 3 distinct
>   `expert_hash` values; the disjoint pair is (`orb_first_hour_k1.0@1.0.0`,
>   `vr_range_reversal_k1.0@1.0.0`). ORB↔H105 is label-BLOCKED solely by the
>   `NQ:high_vol` cell-name collision (two different constructions sharing a
>   string).
> - **(ii) Realized-bar basis (M1 companion,
>   [m1_realized_overlap.json](../../reports/M1_overlap/m1_realized_overlap.json)):
>   ORB↔H105 realized-bar Jaccard = exactly 0.0** — the frozen H105 design
>   §12(c) identity, the strongest disjointness in the pool — vs ORB↔H106
>   0.089. The label and realized statistics INVERT (the label-disjoint pair
>   shares 8.9% of realized bars; the label-blocked pair shares none).
>
> **The realized-bar disjointness is the OPERATIVE ground of this lift.** The
> label rule is satisfied on its own terms, but the operator's authorization
> rests on the realized-bar evidence; the companion amendment
> ([ADR-0017](ADR-0017-realized-bar-verdict-precondition-input.md), accepted
> 2026-07-19) makes that input first-class. Scope of this authorization: the
> ADR-0014 Decision 2 set-level VERDICT protocol, queue per the
> [verdict-readiness memo](../research_notes/verdict_readiness_memo_2026-07-19.md)
> §3 (H106 first, H105 second, held-member re-adjudication on incumbent-set
> change), under the binding labeling rules: any H106 admission record carries
> its net-not-monetizable caveat verbatim (memo §5(i)); H105's adjudication on
> the current substrate is CONDITIONAL-GRADE on every artifact with a
> REGISTERED re-adjudication on the DR-1/DR-2-repaired ledger. Explicitly NOT
> authorized by this record (absence of a record is "undecided", never implied
> consent): ADR-0016 stage B (no spend, no Tier-2 estimator build); any
> ADR-0010 live-capital step; Kelly-fraction selection (all four registered
> fractions stay computed, reported, UNSELECTED); Phase-4 entry / champion
> certification (its own future named, dated operator authorization).

## Context

As of 2026-07-18 the ADR-0014 provisional candidate pool
([pool_ledger.jsonl](../../data/processed/pool_ledger/pool_ledger.jsonl))
holds 8 records across 2 HIDs (H101, H103) — and exactly **one** distinct
`expert_hash`: `orb_first_hour_k1.0@1.0.0`. The arsenal is EMPTY. Under
ADR-0014 the next pipeline stage would be the set-level VERDICT (the first
admission, which also authors the arsenal-covariance / residual-correlation
anchor). The operator has ratified a HOLD on that verdict. Three grounds:

**(a) Effective set size ~1.** All 8 pool records share one `expert_hash`;
H101 and H103 differ only in the conditioning partition applied to an
identical gross return series (one ledger stream, one expert implementation).
Verifiable: the six unchanged-construction cells carry identical statistics
across the `rc-h101-2` and `rc-h103-2` register families in
[config/multipletest_family.yaml](../../config/multipletest_family.yaml)
(e.g. `ES:unconditional` sharpe_estimate 0.009495 in both;
`ES:first_hour_up` 0.031077; `NQ:first_hour_up` 0.048615), and the H103
Expert Card v2 §3 records that the S-c stage reproduces the RC-1 statistics
bit-identically for the 6/10 unchanged-construction cells. A set-level
marginal-geometric-growth adjudication over a set of effective size ~1 has no
between-arm structure to measure; `complementarity.marginal_growth_delta` is
null by construction for every record.

**(b) Multiplicity and burned data would be paid for zero information
(ADR-0014 Decision 4).** Running the five-rung ADR-0007 ladder now would
append verdict-tier trials to the family and consume confirmation-tier
out-of-sample spans (ADR-0008 Decision 5 burned-data ledger) while the
set-level question the verdict exists to answer — marginal contribution to an
incumbent set — is undefined at |arsenal| = 0 and degenerate on a
single-implementation pool. Selection bias is conserved; the cost is not
recoverable.

**(c) The sole null-allocator comparison on record already fails.**
[RC-H101-1](../reports/H101/RC-H101-1_admission_disposition_2026-07-16.md)
§3.2 records that the adjudicated primary (high_vol) cell does not beat its
own matched-turnover random rotor on either instrument (ES rotor p = 0.558,
NQ p = 0.288). That is the only rotor comparison on record — the RC-2
screen-passing competence cells have none (the rotor is a verdict-tier
object) — and the rotor is ADR-0007 Benchmark 5, the non-waivable null
allocator. A verdict on this pool would re-run, at burned-data cost, a
comparison whose singleton form is already on record as failed for the one
cell where it was run.

## Decision

1. **HOLD.** No set-level VERDICT (ADR-0014 Decision 2), no ADR-0007
   five-rung ladder, no Hansen SPA / StepM over allocator configurations, no
   verdict-tier rotor, and no ADR-0002(d) non-redundancy test runs while the
   pool's distinct-`expert_hash` count is 1 and the arsenal is empty. This is
   a **hold, not an archive**: every pool record keeps its
   `pool-hold-reconsider` disposition unchanged, no Expert Card is
   re-versioned by this ADR, and no trial-register family is incremented (no
   scan runs).

2. **Verdict precondition (operator-directed, provisional).** A
   `verdict_precondition` block is added to
   [config/pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml)
   recording the rule: the set-level VERDICT is not scheduled until the pool
   holds **>= 2 distinct `expert_hash` values whose coverage vectors
   (competence-window cells) are non-overlapping**. The block is marked
   `provisional: true`, `derivation: operator-directed, NOT calibrated`, and
   `enforcement: reporting-check-only`. The ">= 2 non-overlapping coverage
   vectors" rule is an **operator instruction, not a derived threshold** — no
   data-derived justification is claimed for it, and it must not be cited as
   a calibrated bound.

3. **Reporting check only.**
   [scripts/audits/check_verdict_precondition.py](../../scripts/audits/check_verdict_precondition.py)
   evaluates the precondition against the live pool ledger and prints
   MET/BLOCKED with a reason. It is deliberately **not** wired into
   pre-commit, CI, or any path that blocks a commit. Meeting the precondition
   does **not** trigger a verdict: the lift action is a **named operator
   action** — explicit, dated operator authorization of the first-admission
   VERDICT protocol — and a MET result is reported to the operator, never
   acted on autonomously.

## Consequences

- At |arsenal| = 0 this defers the first admission — and the first admission
  is what authors the arsenal-covariance / residual-correlation anchor
  ([program roadmap](../research_notes/program_roadmap_2026-07-17.md)
  Phase 2; [backfill plan](../research_notes/backfill_admission_plan_2026-07-17.md)
  §4.4) — so the anchor is deferred with it. This is accepted deliberately:
  an anchor authored from a single-implementation pool would encode one
  expert's covariance with itself.
- Forward sourcing of disjoint-window experts becomes the gating item for the
  admission program (roadmap Phase 3 re-order); the ORB-adjacent retro queue
  cannot supply a non-overlapping coverage vector.
- The precondition is provisional by construction: once verdict outcomes
  exist, any data-derived successor (e.g. via `P1-2.0-POOL-PRIORITY-CALIBRATE`
  monitoring evidence) supersedes it through a new ADR, never by silent edit.
- The pool's `pool-hold-reconsider` records remain reconsideration-eligible
  under ADR-0014 Decision 3 — re-adjudicated on incumbent-set change — which
  this HOLD does not modify.

## Alternatives considered

- **Run the set-level VERDICT now (|arsenal| = 0, one expert_hash).**
  Rejected on grounds (a)–(c): no between-arm structure to adjudicate,
  multiplicity/burned-data cost for zero information, and the singleton rotor
  comparison already on record as failed.
- **Archive H101/H103 instead of holding.** Rejected: ADR-0014 Decision 3
  makes screen-pass/verdict-non-select experts reconsideration-eligible;
  their screen passes are held queue entries, and set-relative value against
  a future incumbent is exactly what a terminal archive would foreclose.
- **Derive the precondition threshold from data now.** Rejected: no verdict
  history exists to calibrate on; a "derived" threshold computed from nothing
  would be a hand-set constant wearing a derivation costume. Recording the
  rule as an explicit operator instruction is the honest form (user global
  zero-magic-number rule requires labeling, not laundering).
- **Enforce the precondition as a blocking gate (pre-commit/CI).** Rejected:
  the verdict is operator-gated in both directions; a mechanical block would
  encode an unaccepted proposed-ADR rule into the commit path.

## References

- [ADR-0014](ADR-0014-provisional-candidate-pool-screen-verdict.md) — the
  screen/verdict split this HOLD sequences; Decision 4 (multiplicity
  conserved), Decision 3 (`pool-hold-reconsider`).
- [ADR-0007](ADR-0007-two-tier-discovery-pipeline.md) — Benchmark 5
  matched-turnover random rotor (non-waivable null allocator).
- [ADR-0008](ADR-0008-integrity-non-negotiables.md) — burned-data ledger,
  trial register (Decision 5/6).
- [RC-H101-1 admission disposition](../reports/H101/RC-H101-1_admission_disposition_2026-07-16.md)
  — §3.2 rotor evidence (ES p = 0.558, NQ p = 0.288).
- [config/multipletest_family.yaml](../../config/multipletest_family.yaml) —
  `rc-h101-2` / `rc-h103-2` shared-cell statistic identity (ground (a)).
- [H103 Expert Card v2](../../research/01_hypothesis_register/H103/expert_card_v2.md)
  §3 — S-c bit-identical reproduction note (6/10 unchanged cells).
- [data/processed/pool_ledger/pool_ledger.jsonl](../../data/processed/pool_ledger/pool_ledger.jsonl)
  — the 8 records / 2 HIDs / 1 expert_hash state this ADR holds.
