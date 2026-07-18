# SKIE-Universe 2.0 — program-level phased roadmap

**Living planning note (of record; not a frozen design.md).** The single
strategic roadmap for the universe. It is
dependency-ordered, not calendar-dated: phases are gated by binding governance
and by the numeric calibrations the program has deferred, never by invented
schedule dates (zero-magic-number). Tactical detail for the backfill/admission
mechanics lives in [backfill_admission_plan_2026-07-17.md](backfill_admission_plan_2026-07-17.md);
this note owns the sequencing and the gate structure.

Supersedes the forward-planning content of the two archived 2026-07-16 scoped
notes ([docs/research_notes/archive/](archive/)). The
[retro-card register](retro_card_register_2026-07-10.md) (source dispositions)
and the dated session handoffs are retained as historical records.

## Terminal objective

A **certified champion allocator earning live capital** (ADR-0010 ramp), pursued
under the geometric-growth mandate (ADR-0013), with the **allocator as the unit
of inference** (ADR-0001). The unit of statistical inference is never the
individual strategy; the champion is a configuration selected over an arsenal of
experts by best geometric (compounded / Kelly log-wealth) growth on the shadow
ledger, through the non-waivable ADR-0007 confirmation ladder.

## Governance status (binding; read first)

- **In force:** ADR-0001…0014 (all accepted). Admission is governed by
  **ADR-0002 as amended by [ADR-0014](../decisions/ADR-0014-provisional-candidate-pool-screen-verdict.md)**
  (accepted 2026-07-17) — the screen/verdict split + provisional pool +
  `pool-hold-reconsider` + the standing-monitored `P1-2.0-POOL-PRIORITY-CALIBRATE`.
  The primary metric is geometric growth (ADR-0013); the incumbent is the standing
  champion (ADR-0012).
- ADR-0014 acceptance **enacts governance only**: it selects no Kelly fraction,
  sets no discovery level, and certifies no admission — the three BLOCKING numeric
  calibrations (Phase 1) still gate all of that.

## Current frontier (2026-07-16)

Shadow ledger **populated** (`OrbFirstHourExpert` × ES+NQ × 4 Kelly fractions);
confirmation-ladder estimators built + tested; two admission scans run
(RC-H101-1, RC-H103-1) → both `provisional-archive-null`; **arsenal EMPTY**;
three numeric calibrations still deferred. This session added ADR-0014 (accepted
2026-07-17) + the pool-ledger schema (audited) and enacted the screen/verdict
amendment map.

## The critical path in one line

The bottleneck is **Phase 1** — three numeric calibrations the program has
deferred across 2026-07-12 (the two Kelly memos) and 2026-07-14 (H900 whitened),
now *executable because the ledger exists*. Every
downstream capability (certification, Kelly-fraction selection, the ADR-0014
screen, a champion) is gated on them. Phases 0–2 are the near-term unlock; the
empty arsenal is a Phase-2 event, not a standing state.

---

## Phase 0 — Governance close-out *(DONE 2026-07-17)*

- **ADR-0014 accepted** (principal direction) and **enacted**: amendment-map
  banners + `amended_by` on ADR-0002/0004/0007/0009, pool-schema status
  `accepted`, the standing follow-up `P1-2.0-POOL-PRIORITY-CALIBRATE` opened, and
  the H101/H103 **screen re-runs** queued (blocked on Phase 1).
- Commit this session's governance artifacts (ADR-0014, pool-ledger schema, audit
  trail, this roadmap + the consolidated plan, canonical-doc updates).
- **Gate out:** the admission pipeline's shape is fixed — **screen → pool →
  verdict** (ADR-0014) governs Phase 2+.

## Phase 1 — Instantiate the three BLOCKING numeric calibrations *(DONE 2026-07-17)*

Executed on the populated ledger (audit-remediate round 1 applied; values in
CLAUDE.md and the memo addenda).

1. **`P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`** → screening α level +
   FWER-vs-FDR criterion (+ PRDS/BY justification if BH). **Nothing is certified
   until this sets the level** — RC-H101-1/RC-H103-1 ran descriptively under the
   null level. Produces the ADR-0014 (S-c)/(S-d) screen bounds.
2. **`P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`** → f*, grid-bracketing verdict,
   P(ruin), f_0 on the ledger's fat-tailed multi-period distribution. Enables
   geometric-growth Kelly-fraction selection over {0.5, 0.75, 1.0, 1.25} (the
   ADR-0013 Decision 3 registered sweep; endpoints an OUTPUT of the
   P1-2.0-KELLY-* calibration) and the marginal-log-wealth currency the
   ADR-0002(d)/verdict test needs.
3. **`P1-2.0-H900-BOCPD-WHITENED`** on-ledger unsupervised-latency numeric → the
   ADR-0014 (S-e) selectability threshold; also closes the deferred on-ledger
   prewhitened-ROC re-run. *Feeds the ADR-0014 (S-e) selectability gate.*

- **Gate out:** the screen/verdict machinery moves from *specified* to
  *executable*; certification becomes possible. This phase directly discharges
  the residual risk recorded in
  [the ADR-0014 audit trail](../audits/audit_trail_2026-07-17_adr0014-pool-ledger.md).

## Phase 2 — First admission *(SCREENS DONE 2026-07-17; verdict pending)*

- Run the admission pass on the populated ledger via the ADR-0014 **screen → pool
  → set-level verdict** pipeline. Candidates: the re-framed H101/H103 (now
  reconsideration-eligible) and the next retro card (H102), per
  [backfill_admission_plan_2026-07-17.md](backfill_admission_plan_2026-07-17.md) §4.
- The **first admission authors the arsenal-covariance / residual-correlation
  bound memo** (register gap 2) every later ADR-0002(d)/verdict test is measured
  against. This is the |arsenal| 0 → 1 transition; at |arsenal|=0 non-redundancy
  is vacuous and (under ADR-0014) the pool cold-start coverage-novelty primary is
  inert, ordering by the persistence margin.
- **Two outcomes, both handled:** (a) a first arm admitted (arsenal → 1); or
  (b) screen-fail → `archive-no-persistent-window`, screen-pass/verdict-non-select
  → `pool-hold-reconsider` (held, not discarded) → pivot to sourcing new candidates.
- **Gate out:** the empty-arsenal state is resolved as an explicit event; the
  covariance anchor exists.
- **Status 2026-07-17:** RC-H101-2 and RC-H103-2 both SCREEN PASS at the
  enacted level → the pool holds two `pool-hold-reconsider` candidates (7
  passing cells total; H103 under the certified leakage-clean stress
  construction). The VERDICT (first admission; authors the covariance anchor)
  is deliberately NOT run (|arsenal| = 0 stop per the execution brief) — it is
  the next operator-gated action, together with sourcing disjoint-window
  forward experts (Phase 3).

## Phase 3 — Arsenal breadth *(retro queue re-framed + forward experts)*

- Route the remaining retro cards (H100/H104, subject to their integrity/cost
  debt; H102 continues here only if Phase 2 left it `pool-hold-reconsider`)
  through the admission pipeline; re-run any
  `pool-hold-reconsider` members against each changed incumbent set (ADR-0014
  Decision 3).
- **Coverage gap named:** the retro cards are all ORB-adjacent / equity-index.
  Genuine disjoint-window complementarity — the program's thesis — needs
  **forward hypotheses** whose competence windows are disjoint from ORB. These
  enter the same backfill → scan path and are the real source of arsenal value.
- `P1-2.0-POOL-PRIORITY-CALIBRATE` begins accruing verdict outcomes → the
  standing-monitored ranking weights mature from the structural cold-start rule
  into data-fitted (CI-bearing) coefficients.
- **Gate out:** arsenal ≥ 2 — the minimum for the allocator to be a non-trivial
  unit of inference.

## Phase 4 — Allocator confirmation + champion *(first capital-eligible object)*

- At arsenal ≥ 2, run the **ADR-0007 confirmation ladder** on allocator
  configurations × Kelly-fraction: Hansen SPA existence + Romano-Wolf StepM
  identification across all five rungs (best static expert, equal-weight,
  inverse-vol, flat, **matched-turnover random rotor**), Deflated Sharpe + PBO,
  net of switching costs, on **geometric growth** (ADR-0013). Kelly-fraction
  winner data-selected only after Phase-1 precondition 2 is frozen.
- The winner becomes the **standing incumbent champion** (ADR-0012) and the
  ADR-0010 live-capital anchor.
- **Gate out:** a certified, capital-eligible champion exists.

## Phase 5 — Champion-challenger + live-capital ramp *(standing operation)*

- Instantiate **`P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE`** (dethroning margin +
  champion-dwell floor; ADR-0012 Decisions 3/5) — needed only once a champion
  exists, non-operational until frozen.
- Begin the **ADR-0010 steepened ramp** (ADR-0013): live-vs-shadow tracking,
  TOST affirmative-tracking gate, CUSUM demotion, prohibited accelerants
  retained.
- Standing loop: new challengers cycle admission → (pool) → confirmation ladder →
  dethrone-or-hold; the champion earns size by live measurement.
- **Gate out:** self-sustaining champion-challenger operation under live capital.

---

## Gate → phase map

| Gate (follow-up) | Status | Unlocks |
|---|---|---|
| ADR-0014 acceptance | **accepted 2026-07-17** | Phase 0 (done) → screen/verdict shape for Phase 2+ |
| `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` | **numeric instantiated 2026-07-17** (level 0.7401, retain-fwer) | certification level + screen (S-c)/(S-d) bounds SET |
| `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` | **numeric instantiated 2026-07-17** (record only; bracketing inconclusive-on-null-ledger) | fraction selection still a Phase-4 champion action (arsenal ≥ 1) |
| `P1-2.0-H900-BOCPD-WHITENED` (on-ledger numeric) | **executed 2026-07-17** (latent-state latency UNATTAINABLE; amended S-e rule) | ADR-0014 (S-e) selectability input QUANTIFIED |
| `P1-2.0-POOL-PRIORITY-CALIBRATE` | opened 2026-07-17 (standing/monitored) | Phase 3 → data-fitted pool ranking |
| `P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE` | registered, non-operational | Phase 5 → champion dethroning |
| `P1-2.0-DATABENTO-DEC-ROLL-REPULL` | operator-only vendor spend | breadth (Dec-roll substrate repair) |

## Non-waivable throughout (ADR-0008 / ADR-0013 §8)

DSR, PBO, matched-turnover random rotor, PIT canaries, family-wise trial
register (incl. the Kelly-fraction and — on ADR-0014 acceptance — pool
dimensions), burned-data ledger, ReproLog, shadow ledger as sole evidence.
More binding under leverage: an overfit champion **ruins** rather than
underperforms, so aggression on sizing/discovery is paid for by strictly more
conservative multiplicity accounting, never weaker correction.
