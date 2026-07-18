# Consolidated shadow-ledger backfill + arsenal-admission plan

**Living planning note (of record; not a frozen design.md).** No hypothesis
design.md is frozen and no ledger partition is written on the strength of this
document. This is the **single tactical plan** for populating the shadow ledger
(ADR-0003) and moving candidates through admission; it **supersedes and
consolidates** the two 2026-07-16 scoped notes now archived under
[docs/research_notes/archive/](archive/):
`shadow_ledger_backfill_plan_2026-07-16.md` and
`retro_card_admission_roadmap_2026-07-16.md`. The strategic phasing that wraps
this plan lives in [program_roadmap_2026-07-17.md](program_roadmap_2026-07-17.md).

Governing ADRs: [ADR-0003](../decisions/ADR-0003-shadow-ledger-canonical-object.md)
(canonical object), [ADR-0011](../decisions/ADR-0011-two-level-data-storage-and-provenance-policy.md)
(storage), [ADR-0006](../decisions/ADR-0006-execution-fidelity-tiers.md) (Tier-0
default), [ADR-0005](../decisions/ADR-0005-three-layer-separation.md) (layers),
[ADR-0002](../decisions/ADR-0002-arsenal-admission-standard.md) (admission),
[ADR-0007](../decisions/ADR-0007-two-tier-discovery-pipeline.md) (confirmation),
[ADR-0008](../decisions/ADR-0008-integrity-non-negotiables.md) (integrity),
[ADR-0013](../decisions/ADR-0013-aggressive-geometric-growth-mandate.md) (growth
mandate).

> **Governance status note (no mixed signals).** Arsenal admission is governed by
> **ADR-0002 as amended by [ADR-0014](../decisions/ADR-0014-provisional-candidate-pool-screen-verdict.md)
> (accepted 2026-07-17)**: a singleton **SCREEN** (persistent, ex-ante-selectable
> competence window → provisional pool) feeding a set-level **VERDICT** (marginal
> geometric-growth on the ADR-0007 ladder), with screen-pass/verdict-non-select
> experts `pool-hold-reconsider`. The prior scans RC-H101-1/RC-H103-1 were run
> under the pre-amendment ADR-0002 singleton standard (2026-07-16); forward scans
> use the screen/verdict pipeline (§4.0). Certification remains BLOCKED on the
> three numeric calibrations (§2); acceptance enacted governance only.

---

## 1. Current state (what is already done)

The backfill is no longer greenfield. As of 2026-07-16 the canonical append-only
shadow ledger is **populated with the first forward expert**:

- **`OrbFirstHourExpert`** (first-hour opening-range breakout,
  [experts/orb_first_hour.py](../../src/skie_universe2/experts/orb_first_hour.py))
  backfilled over **ES + NQ × 4 Kelly fractions {0.5, 0.75, 1.0, 1.25}** (the
  ADR-0013 Decision 3 registered sweep; endpoints an OUTPUT of the P1-2.0-KELLY-*
  calibration; ≈5.2M rows) through the Expert-contract / Tier-0 exact-levered-return stack
  ([execution/tier0_barclose.py](../../src/skie_universe2/execution/tier0_barclose.py),
  ruin representable) via
  [scripts/run_shadow_ledger_backfill.py](../../scripts/run_shadow_ledger_backfill.py).
- The old backfill plan's milestones **M0–M4 are executed**: expert-interface
  contract, Tier-0 bar-close helper, driver + smoke expert, first candidate
  backfill, audit.
- The confirmation-ladder estimators are built + tested: Romano-Wolf StepM
  ([romano_wolf.py](../../src/skie_universe2/inference/romano_wolf.py)), Deflated
  Sharpe ([deflated_sharpe.py](../../src/skie_universe2/inference/deflated_sharpe.py)),
  PBO/CSCV ([pbo.py](../../src/skie_universe2/inference/pbo.py)), matched-turnover
  rotor ([matched_turnover_rotor.py](../../src/skie_universe2/inference/matched_turnover_rotor.py)),
  Ledoit-Wolf 2008 Sharpe-difference
  ([ledoit_wolf_sharpe.py](../../src/skie_universe2/inference/ledoit_wolf_sharpe.py)).
- **Two admission scans have run on the populated ledger, both null:**
  - **RC-H101-1** (unconditional first-hour ORB, H101 ← 1.0 H052a):
    `provisional-archive-null` — every Romano-Wolf-adjusted p ≥ 0.17, primary
    cell does not beat its matched-turnover rotor, DSR < 0.5 both instruments.
    [RC-H101-1 disposition](../reports/H101/RC-H101-1_admission_disposition_2026-07-16.md).
  - **RC-H103-1** (stress-state anti-gate ORB, H103 ← 1.0 H054, ES+NQ):
    `provisional-archive-null` — no admission-grade stress edge (every RW-adj
    p ≥ 0.42); both cells fail the §8 25% precision gate; the Lundström
    high-vol-concentration prior (Holmberg, Lönnbark & Lundström 2013,
    [FRL 10(1):27-33](https://doi.org/10.1016/j.frl.2012.09.001)) is
    **contradicted** (ES ORB edge is in CALM sessions); RC-XCORR-1 redundancy is
    instrument-specific.
    [RC-H103-1 disposition](../reports/H103/RC-H103-1_admission_disposition_2026-07-16.md).
- **Arsenal: EMPTY.** No ADR-0002(b) member admitted; no ADR-0002(d) covariance
  anchor authored.

The reusable machinery (ledger writer, feature pipeline, Tier-0 helper,
rolling-origin windows, cost model, PIT canaries, ReproLog) is documented in the
archived backfill note §0–§4 and is **unchanged**; it is not re-specified here.

## 2. Blocking preconditions — ALL THREE INSTANTIATED 2026-07-17 (Phase 1 done)

The three numeric calibrations are now on-ledger numbers (audit-remediated;
values in CLAUDE.md and the memo addenda). Certification machinery is
EXECUTABLE; nothing is certified yet.

1. **Discovery-alpha numeric — INSTANTIATED.** `screening_error_rate_target`
   = 0.7401 (RD4 posterior-null cutoff, median of the 24-point enactment band;
   full precision in [config/multipletest_family.yaml](../../config/multipletest_family.yaml),
   which governs); criterion retain-fwer; ADR-0014 (S-d) bounds DSR ≥ 0.2599 /
   PBO ≤ 0.7401 as provisional operational proxies. RC-H101-1 / RC-H103-1 ran
   under the earlier null-level descriptive regime; the RC-*-2 screens run
   under the enacted level.
2. **Kelly concavity/ruin numeric — INSTANTIATED, RECORD ONLY.** Concavity
   exhibited on-ledger (in-sample peak at f = 1.0), P(ruin) = 0 at every grid
   point, f_0 = 1.978–1.990, ES/net degenerate (no favourable bet), OOS f**
   edge-pinned with CIs including zero → grid-bracketing verdict
   **inconclusive-on-null-ledger**; re-instantiation at the first admission is
   a registered standing condition. No fraction selected (Phase-4 champion
   action; blocked on arsenal ≥ 1).
3. **Unsupervised detection latency — EXECUTED (reproducible on-ledger ROC).**
   The latent-state unsupervised latency is **UNATTAINABLE** (no accurate,
   non-degenerate operating point on either instrument); latent-state cells
   fail ADR-0014 (S-e) outright and rule-based causal covariate cells carry
   their structural observation lag (amended screen rule, frozen in the
   RC-*-2 addenda). The supervised-CUSUM value stays forbidden.

Standing invariant (ADR-0013 Decision 8): the loosened discovery posture is
licensed **only** by the non-waivable DSR/PBO + matched-turnover rotor at the
confirmation tier. Aggression is bought with more conservative multiplicity
accounting, never weaker correction.

## 3. Remaining backfill scope

**First-pass substrate** stays ES + NQ 5-min roll-adjusted, 2015–2025 (the only
in-project substrate). Additions:

- **Retro candidates not yet scanned:** H102 (← H053), H100 (← H050), H104
  (← H055). Each needs its design.md frozen (`/preregister`), its `cov_*` set
  registered in [config/covariates.yaml](../../config/covariates.yaml), and a
  full ES/NQ × 4-fraction backfill of its expert form before its scan.
- **Reconsideration-eligible (ADR-0014, in force):** H101, H103 already
  backfilled + scanned → null under the pre-amendment singleton standard. Under
  the accepted ADR-0014 they are **re-classed** from `provisional-archive-null` to
  reconsideration-eligible pending a **screen re-run** (the persistence +
  ex-ante-selectability tests they never ran). The re-run is queued, blocked on
  the §2 numeric calibrations.
- **Forward experts (coverage gap).** The retro cards are all ORB-adjacent /
  equity-index. The arsenal's thesis — disjoint-window complementarity — needs
  experts whose competence windows are *disjoint* from ORB. New forward
  hypotheses are required beyond the retro queue; they enter the same backfill →
  scan path.

**Kelly-fraction materialization (carried OD-6):** every fraction is a distinct
`expert_id` suffix (`..._k0.5@v`), all four materialized, none selected (gated on
precondition 2). 4× partition inflation per expert is accepted (Tier-0 cost,
append-only).

## 4. Admission-scan designs (remaining candidates)

### 4.0 The screen/verdict pipeline (ADR-0014, in force)

Admission runs in two stages (ADR-0014, accepted 2026-07-17):

- **SCREEN (singleton → pool).** (a) interface/leakage-canary, (b) frozen
  conditioning set, (c) conditional gross edge with Romano-Wolf-within-scan, plus
  (S-d) window persistence (PBO/DSR below data-derived bounds) and (S-e) ex-ante
  selectability (dwell ≥ realistic unsupervised latency). A screen pass enters the
  provisional pool ([config/pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml)).
- **VERDICT (set-level).** (d) non-redundancy + marginal geometric-growth
  contribution on the ADR-0007 ladder against the actual incumbent set; a
  screen-passing but non-selected candidate is `pool-hold-reconsider`,
  re-adjudicated on incumbent-set change; disposition per the ADR-0009 taxonomy
  (as amended).

The per-candidate scan **estimand and conditioning set are unchanged by the
split**; the designs below give that estimand and are screen-ready. Historical
note: RC-H101-1/RC-H103-1 predate the split and ran as ADR-0002 singleton scans.

### 4.1 H102 ← H053 — 09:45→10:30 ET multi-timeframe regression (next in queue)

- **(c)** Estimand = pre-cost per-session strategy log-return edge per cell;
  LightGBM arms are the pre-registered primary cells; conditioning set =
  project-standard + `regime_hmm_h900`; Romano-Wolf StepM within scan. Distinctive:
  the only candidate whose 1.0 series are cost-free (directly gross) — native
  ADR-0002 currency. A fresh per-cell scan is required (1.0 SPA family m=2 was
  family-level, not per-cell).
- **(d)** The 09:45–10:30 window nests inside the first-hour ORB session and
  shares the ES/NQ substrate → high a-priori correlation with any ORB arsenal;
  the marginal-log-wealth test is the binding question, not standalone gross edge.
- **DSR/PBO** are the operative constraint (1.0 shows DSR ∈ [−3.81, −3.29], CPCV
  q05 < 0 on every arm); more binding under leverage (ADR-0013).
- **Debt:** RC-H102-1 cost decomposition (1.0 cost prior 10–20%/yr exceeds the
  ≈5.3%/yr gross ⇒ cost share > 100%); failed calibration gate blocks any
  probability-forecast use (directional form only).

### 4.2 H100 ← H050 — HMM-gated LightGBM directional signal

- The **gated form is not a candidate** — evidence-confirmed harmful and
  HMM-as-gate prohibited (ADR-0001 D5). Only live object: RC-H100-3, a
  Romano-Wolf-corrected conditional-edge scan of the *unconditional* 1-min signal,
  contingent on RC-H100-1 (pre-cost decomposition never emitted in 1.0).
- Lowest admission probability of the queue; most likely terminal disposition is
  `archive-no-gross-edge` (ADR-0002) / `archive-no-persistent-window` (ADR-0014)
  after RC-H100-1/3.

### 4.3 H104 ← H055 — wick-rejection mean-reversion scalp

- Largest headline edge (MGC +87%), **furthest from a clean scan**: MGC/SIL are
  outside the frozen §2 universe → a **fresh admission cycle** with its own
  trial-register entry; the registered surface must carry the 5-config × 4-symbol
  sweep, the ~5-month window extension, and the universe extension.
- **RC-H104-3 integrity closure is hard-blocking before any scan:** PIT-canary
  suite, ReproLog wire, limit-fill-at-wick (Tier-2, ADR-0006), MPPM CI,
  walk-forward inner CV, v1↔v2 reconciliation.
- This is the overfit-at-leverage → **ruin** archetype ADR-0013 §8 hard-blocks;
  the confirmation ladder must run under the ADR-0004 rolling regime, not the
  full-window headline.

### 4.4 Cross-cutting

- **RC-XCORR-1** (ADR-0002(d) / ADR-0014 verdict input for 2nd+ admissions):
  pairwise marginal-log-wealth residual correlations among admitted candidates;
  feeds the correlation bound once the **first** admission defines the arsenal
  covariance (register gap 2). Known dependencies: H101↔H103 session-complement,
  H103↔H052a algebraic, H102 window nested in the ORB hour, H104 sole
  non-equity-index / mean-reversion diversifier.
- **First-admission obligation:** the first admitted expert must author the
  arsenal-covariance / residual-correlation bound memo every later candidate is
  tested against. Under ADR-0014 this is the |arsenal|=0 → 1 transition of the
  cold-start (roadmap Phase 2).

## 5. Open decisions (operator input)

Carried from the two archived notes; still open.

- **OD-A (first admission sequencing).** All candidates gate on the numeric
  preconditions (§2). Confirm the first admission target (H101 re-run under the
  screen vs a fresh forward expert) — it defines the arsenal-covariance memo.
- **OD-B (H103 pooling universe).** RC-H103-1 proposed ES+NQ+MES+MNQ pooling to
  reach n ≥ 174 stress-cell trades; confirm the micro siblings are in the
  intended universe (RC-H103-1 ran ES+NQ only).
- **OD-C (H104 fresh-cycle scope).** Confirm MGC/SIL enter as a new admission
  cycle with their own trial-register entry and that RC-H104-3 is a hard
  pre-admission gate.
- **OD-D (Databento December-roll repull).** `P1-2.0-DATABENTO-DEC-ROLL-REPULL`
  (operator-only vendor spend): the December-roll windows are currently
  *excluded*, not *corrected*
  ([config/data_sources.yaml](../../config/data_sources.yaml)). Decide whether to
  repull before broadening scope.
- **OD-E (signal/target persistence).** Keep signal_strength / target_position as
  a gitignored `data/interim/` attribution sidecar, not `cov_` columns (reserved
  for ADR-0002(b) conditioning covariates). Recommended; confirm.
- **OD-F (correction cadence).** Append-only ledger: a code change to an expert =
  version bump = full re-backfill into new partitions, old ones deprecated
  (ADR-0003 D3). Confirm single full run vs incremental per-window appends.
