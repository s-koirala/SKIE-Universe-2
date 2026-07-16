# Arsenal-admission roadmap — retro-card candidates H100–H104

**DRAFT — for review.** Design note, not a frozen design.md. Sequences the five
retro Expert-Card candidates (H100–H104, retro of 1.0 H050/H052a/H053/H054/H055)
through the [ADR-0002](../decisions/ADR-0002-arsenal-admission-standard.md)
admission standard, using the just-closed
[H001](../../research/01_hypothesis_register/H001/design.md) covariate-information
study as the reusable method template. No scan is run here; no disposition is
changed. Every admission scan below is BLOCKED on the shadow-ledger backfill and,
for any growth-based ranking, on the two Decision-9 Kelly memos — see
[§0 Blocking preconditions](#0-blocking-preconditions).

Companion to the [retro-card register](retro_card_register_2026-07-10.md) (source
dispositions + the RC-* scan list) and its 2026-07-14 ADR-0013 re-adjudication
addendum (metric currency reconciled to geometric growth). This note adds the
per-candidate admission-scan **design** and the **readiness ranking**.

---

## 0. Blocking preconditions (bind every candidate)

These are program-level gates from [CLAUDE.md](../../CLAUDE.md) and
[ADR-0013](../decisions/ADR-0013-aggressive-geometric-growth-mandate.md); no
candidate clears admission until they lift.

1. **Shadow-ledger backfill (ADR-0003, step-4).** Every ADR-0002(c)
   conditional-gross-edge scan and every ADR-0002(d) non-redundancy test consumes
   the [shadow ledger](../decisions/ADR-0003-shadow-ledger-canonical-object.md) as
   its sole evidence source. It is not yet backfilled. No rolling-origin edge
   series exists anywhere in the 1.0 record (register gap 3), so **no RC-* scan
   can run until the ledger materializes the per-card counterfactual expert ×
   asset × bar series.** This is the single hard gate on all five.

2. **Two BLOCKING Kelly memos (ADR-0013 Decision 9).** Method-frozen 2026-07-12
   but NUMERICALLY DEFERRED:
   [kelly_growth_concavity_ruin](../methodology/kelly_growth_concavity_ruin_2026-07-12.md)
   (f*, grid-bracketing verdict, P(ruin)) and
   [discovery_alpha_cost_calibration](../methodology/discovery_alpha_cost_calibration_2026-07-12.md)
   (α level, π1, FWER-vs-FDR criterion). Until both are instantiated on the ledger,
   **geometric-growth ranking and Kelly-fraction selection over {0.5, 0.75, 1.0,
   1.25} are BLOCKED**, and the ADR-0002(d) marginal-log-wealth test has no
   currency to compute in.

3. **Screening/FWER level is null.** `screening_error_rate_target: null` in
   [config/multipletest_family.yaml](../../config/multipletest_family.yaml). Every
   Romano-Wolf-corrected conditional-edge scan therefore runs and is reported
   **descriptively**; no arm is CERTIFIED as a discovery until
   `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` sets the level (the exact regime
   H001 ran under: 1600 arm-horizons emitted, archive(null), none certified).

4. **Arsenal is empty.** H001 closed **archive(null)** 2026-07-16 (the small-n
   vol×trend label's MM-CMI is a ~1e-4-nat large-N residual failing the OOS
   predictive guard; multipletest_family.yaml `h001-volxtrend-covariate.scan_executed`).
   It admitted no expert and adopted no covariate, so the arsenal remains at **0
   members**. Consequence: the **first** admission's ADR-0002(d) test is trivially
   satisfied against an empty spanned set, but that first admission must produce
   the arsenal-covariance / correlation-bound derivation memo the register (gap 2)
   flags — every subsequent candidate is tested against it.

---

## 1. Reusable method template (from H001)

H001 built and audit-accepted the machinery every admission scan reuses; the
conditional-gross-edge scans differ from H001 only in the **estimand** (a pre-cost
edge / marginal log-wealth contribution on a traded expert series, not covariate
CMI) and the **substrate** (the shadow ledger, not the raw 5-min bars).

- **Rolling-origin engine** — `h900_windows()` (24-month train / 6-month step,
  first origin 2017-01-01), per-window fit-on-train / evaluate-on-OOS-slice,
  horizon-aware purge + Politis-White automatic-block-length embargo. Reused
  verbatim from [scripts/run_h001_covariate_study.py](../../scripts/run_h001_covariate_study.py).
- **Pooled bar-level stationary bootstrap CI** —
  `stationary_bootstrap_mean_ci` over the pooled per-bar contribution series
  (never over the ~15 window summaries; too few for block-length selection),
  Politis-Romano 1994, PW-2004 block length. This is the ADR-0004 inference stack
  and the ADR-0002(c) resampling scheme.
  [src/skie_universe2/inference/covariate_information.py](../../src/skie_universe2/inference/covariate_information.py).
- **Romano-Wolf StepM within-scan** — the ADR-0002(c) default multiplicity
  control; the `h001-volxtrend-covariate` family in
  [multipletest_family.yaml](../../config/multipletest_family.yaml) is the
  registration pattern each RC-* scan follows (`correction: romano-wolf`, level =
  deferred project-wide target).
- **PIT canary + 13-field ReproLog + burned-data mirror + trial-register append**
  — ADR-0008 integrity envelope, run before the production scan (H001 §3 / the
  `main()` ReproLog-first driver).
- **Precision gate** — CI half-width < 25% of the point estimate else
  "indeterminate — insufficient windows" (H900 §8 convention, avoids retrospective
  power per Hoenig & Heisey 2001).

The ADR-0002(d) non-redundancy test has a directly reusable analogue: H001's
`nested_predictive_delta` is the covariate-layer counterpart of the Grinold-1989
marginal-contribution framing ADR-0002(d) invokes; the return-series version
substitutes marginal log-wealth growth for nested log-loss.

---

## 2. Priority ranking (by admission readiness)

Ranked by proximity to a **clean admission scan** — a positive pre-cost edge in a
pre-declared cell, minimal blocking integrity/registration debt, and a signal form
that survives the ADR-0005 three-layer separation. All five share the §0 ledger
gate; the ranking is about what is closest **once the ledger lands**.

| Rank | Card (1.0) | Source disposition | One-line readiness rationale |
|---|---|---|---|
| **1** | **H101** ← H052a | `arsenal-admit-conditional` | Cleanest positive gross-edge lower bound in the register (NQ unconditional ORB net-positive ⇒ pre-cost-positive); admitted form is a simple published rule (first-hour ORB), cheap to port; only debt is cost-basis reconciliation + the 2.0 interface/canary. |
| **2** | **H103** ← H054 | `arsenal-admit-conditional` | Cleanest ADR-0002-shaped object (conditional edge in a proto realized-vol cell, positive on every metric); design already clean — blocked **only** on powered accumulation (n_anti=7 ≪ 174), which the ledger backfill is the mechanism for. |
| **3** | **H102** ← H053 | `re-specify-cost-bound` | Only candidate whose 1.0 series are **cost-free (directly gross)** — native ADR-0002 currency — but the edge is fragile (CPCV q05<0, DSR ∈ [−3.81,−3.29], calibration gate failed on all arms) and those failed integrity gates are MORE binding under leverage; a cost re-spec, not an admit. |
| **4** | **H100** ← H050 | `re-specify-cost-bound` | The register's one significantly **negative** result; gated form is dead (−81/−84%, HMM-as-gate prohibited by ADR-0001 D5). Only live object is the near-noise unconditional signal; needs a pre-cost decomposition just to reach an archive verdict — low admission probability. |
| **5** | **H104** ← H055 | `arsenal-admit-conditional` (post-hoc) | Largest headline edge (MGC +87%) but **furthest from a clean scan**: unregistered universe extension (MGC/SIL ∉ frozen §2 universe) ⇒ a *fresh* admission cycle; heaviest integrity debt (leakage canary deferred, ReproLog incomplete, no MPPM CI, uncorrected 5×4 surface, Tier-2 fill semantics, v1↔v2 reconciliation failure); the exact overfit-at-leverage → ruin archetype ADR-0013 makes hard-blocking. |

---

## 3. Per-candidate admission-scan designs

Each candidate is specified in four parts: **(c)** conditional-gross-edge scan
design, **(d)** non-redundancy on marginal log-wealth, **ladder** the ADR-0007
confirmation requirements, and **debt** the ledger dependency + integrity/
registration items to clear first.

### 3.1 H101 ← H052a — first-hour opening-range breakout (RANK 1)

Card: [expert_card_H101/H052a_retro](../reports/expert_card_H052a_retro_2026-07-10.md).
Scan lineage: RC-H101-1. **Admitted form is the unconditional first-hour ORB; the
HMM gate is dropped** on H052a's own evidence (gate increment null; filters the
wrong direction) and per
[ADR-0001 D5](../decisions/ADR-0001-allocator-unit-of-inference.md).

- **(c) Conditional-gross-edge scan.** Estimand = **pre-cost per-session ORB
  log-return edge** on the shadow-ledger counterfactual, per conditioning cell.
  Conditioning set (frozen per ADR-0002(b) before scanning): the project-standard
  set from
  [config/conditioning_covariates.yaml](../../config/conditioning_covariates.yaml)
  — `realized_vol_percentile`, `variance_ratio_state`, `time_of_day_bucket`,
  `macro_calendar_proximity`, `spread_liquidity_regime` — plus the registered
  `regime_hmm_h900` covariate as a scan **cell set** (never a gate; ADR-0001 D5),
  plus a **pre-registered first-hour-sign extension** (Lundström-direction high-vol
  cells as the primary family; the H052a §15.1 prior art predicts edge
  concentration in high-realized-vol / positive-first-hour sessions — the opposite
  of the BIC-selected non-stress gate). Multiplicity = **Romano-Wolf StepM within
  the scan** over the full cell × instrument family (ES, NQ), block bootstrap over
  the pooled per-session contribution series; level = deferred project-wide target
  (descriptive until set). Cost is NOT charged here (ADR-0002 Alternatives).

- **(d) Non-redundancy (marginal log-wealth).** First admission ⇒ empty spanned
  set ⇒ trivially non-redundant, BUT this admission must **derive the
  arsenal-covariance / residual-correlation bound memo** (register gap 2) that all
  later candidates are tested against. Test = positive marginal contribution to
  compounded log-wealth growth of the allocator when H101 is added, **or** residual
  correlation below the data-derived ensemble-variance bound (ADR-0013 amended
  form; IR view demoted to guardrail). Blocked on Kelly memos (§0.2).

- **Ladder (ADR-0007).** On promotion to an allocator configuration: beat all five
  rungs net of switching costs — best static expert, equal-weight, inverse-vol,
  flat, and the **non-waivable matched-turnover random rotor** (Benchmark 5). SPA
  existence + Romano-Wolf StepM identification over the (config × Kelly-fraction)
  family; DSR from the register's per-trial records; PBO via CSCV. Every
  (config × fraction) pair is one trial in the `allocator-confirmation-kelly-sweep`
  family.

- **Debt to clear first.** (i) Ledger backfill (§0.1). (ii) **RC-H101-1 cost-basis
  reconciliation** — the 1.0 card's ≈3e-4 drag quote is internally inconsistent
  with its own `log(1 − cost/notional)` formula; the derived cost share is
  basis-indeterminate (NQ ≈13% notional to ≈83% account-dollar; ES ≈74–99%). Admit
  is pre-cost so this does not gate (c), but it gates any net claim. (iii) 2.0
  PIT-clean interface port + leakage-canary suite (1.0 `leakage-canary-pass` is
  evidence, not the 2.0 suite). Lowest total debt of the five.

### 3.2 H103 ← H054 — anti-gate (stress-state-only) first-hour ORB (RANK 2)

Card: [expert_card_H103/H054_retro](../reports/expert_card_H054_retro_2026-07-10.md).
Scan lineage: RC-H103-1. The cleanest ADR-0002-shaped object in the register — a
conditional-edge claim in a proto-pre-declared regime cell with no
standalone-profitability pretension.

- **(c) Conditional-gross-edge scan.** Estimand = pre-cost per-session ORB
  log-return edge in the **realized-vol-percentile stress cell**, replacing the
  learned HMM stress state with the rule-based `realized_vol_percentile` covariate
  (ADR-0001 D5; the card's evidence is agnostic between the two — the scan measures
  the delta). **Pooled multi-instrument** (ES + NQ + MES + MNQ) to accumulate the
  stress cell toward the design-derived **n ≥ 174** stress-cell trades (the 2025
  fire rate came in at 2.95% vs the design's 10% — the scan must also test whether
  the vol-percentile cell definition controls that gap). Romano-Wolf StepM within
  scan; `realized_vol_percentile` is the pre-registered primary cell family.

- **(d) Non-redundancy (marginal log-wealth).** H103 trades the **complement** of
  the session set an H101 expert favors → candidate **diversifier pairing**; its
  marginal log-wealth contribution must be measured (not assumed) against an arsenal
  that may already contain H101. Note the algebraic dependence on H052a (H103's
  secondary statistic) and partial OOS overlap with H053 — both resolved at
  RC-XCORR-1 (§4).

- **Ladder (ADR-0007).** As §3.1. The `arsenal-admit-diversifier` disposition is a
  live alternative to `arsenal-admit-conditional` here if the rotor + non-redundancy
  evidence shows selection value concentrated in the diversification, not the
  standalone cell.

- **Debt to clear first.** (i) Ledger backfill — and here it is **load-bearing for
  power**, not just currency: n=7 → n≥174 accumulation is only affordable on the
  shadow ledger (live/paper accumulation would take decades). (ii) 2.0 interface
  port + leakage canary (1.0 ran 17/17 PIT tests — supporting, not the 2.0 suite).
  No cost-inconsistency or registration debt. Cleaner design than H101; ranked
  second only because it **cannot** admit until the ledger powers the cell.

### 3.3 H102 ← H053 — 09:45→10:30 ET multi-timeframe regression (RANK 3)

Card: [expert_card_H102/H053_retro](../reports/expert_card_H053_retro_2026-07-10.md).
Scan lineage: RC-H102-1 (cost) + RC-H102-2 (conditional edge). Distinctive: the
only candidate whose 1.0 series are **cost-free (directly gross)** — native
ADR-0002 admission currency.

- **(c) Conditional-gross-edge scan.** Estimand = pre-cost per-session strategy
  log-return edge per cell; LightGBM arms are the pre-registered primary cells (they
  dominated ElasticNet on 3 of 4 gross cells). Conditioning set = project-standard
  + `regime_hmm_h900`. Romano-Wolf StepM within scan; register carries the retro
  2-model × 2-symbol × CPCV trials. The 1.0 SPA family m=2 (p 0.367/0.290) is
  family-level, not per-cell — a fresh per-cell scan is required.

- **(d) Non-redundancy (marginal log-wealth).** The 09:45–10:30 window nests inside
  the H101/H103 first-hour ORB session and shares the ES/NQ substrate → high a-priori
  correlation with an ORB-containing arsenal; the marginal-log-wealth test is the
  binding admission question, not the standalone gross edge.

- **Ladder (ADR-0007).** As §3.1, but the **DSR/PBO gates are the operative
  constraint**: the 1.0 record already shows DSR ∈ [−3.81, −3.29] and CPCV q05 < 0
  on every arm. Under ADR-0013 this fragility is MORE binding at leverage (a
  fragile edge sized by the Kelly sweep ruins rather than underperforms), so the
  confirmation ladder is expected to reject unless the fresh scan materially
  improves the effective-trials-adjusted edge.

- **Debt to clear first.** (i) Ledger backfill. (ii) **RC-H102-1 cost
  decomposition** — the 1.0 cost prior (10–20%/yr) exceeds the best arm's ≈5.3%/yr
  gross ⇒ cost share > 100%; a cheaper execution path (micro contracts) is the
  re-spec lever, but the current spec cannot survive its own cost model. (iii) The
  failed calibration gate (BSS ≤ 0 on all arms) independently blocks any
  probability-forecast use — only the directional-signal form is a candidate.

### 3.4 H100 ← H050 — HMM regime-gated LightGBM directional signal (RANK 4)

Card: [expert_card_H100/H050_retro](../reports/expert_card_H050_retro_2026-07-10.md).
Scan lineage: RC-H100-1 (pre-cost decomp) + RC-H100-2 (variant completion) +
RC-H100-3 (conditional scan). The register's one significantly **negative** result.

- **(c) Conditional-gross-edge scan.** The **gated form is not an admission
  candidate** — it is evidence-confirmed harmful (net differential CI excludes zero
  on the negative side, both symbols; whipsaw cost-drag 1.87×/5.66× the signal
  magnitude) and HMM-as-gate is prohibited (ADR-0001 D5). The only live object is
  **RC-H100-3**: a Romano-Wolf-corrected conditional-edge scan of the *unconditional*
  1-min LightGBM signal over the project-standard set. Precondition **RC-H100-1**:
  the pre-cost decomposition never emitted in 1.0 (the INVESTIGATE memo §6.4
  attribution is net-based arithmetic on two net arms, not the pre-cost per-cell
  edge ADR-0002(c) needs). `archive-no-gross-edge` is unavailable **only** because
  that decomposition is missing.

- **(d) Non-redundancy.** Moot until (c) finds a positive pre-cost cell — the
  unconditional signal is near-noise net (−2.63/−0.39 annualised) and unmeasured
  pre-cost.

- **Ladder (ADR-0007).** Not reached on current evidence.

- **Debt to clear first.** (i) Ledger backfill. (ii) **RC-H100-1 pre-cost
  decomposition** — the gating item that determines whether H100 archives or
  produces a live unconditional-signal re-spec. (iii) RC-H100-2 variant completion
  (H050.invert / H050.stable-state v1 cards are numeric-empty). Lowest admission
  probability of the five; most likely terminal disposition is `archive-no-gross-edge`
  after RC-H100-1/3.

### 3.5 H104 ← H055 — wick-rejection mean-reversion scalp (RANK 5)

Card: [expert_card_H104/H055_retro](../reports/expert_card_H055_retro_2026-07-10.md).
Scan lineage: RC-H104-1 (signal-layer scan) + RC-H104-2 (cost) + RC-H104-3
(integrity closure). Largest headline edge, **furthest from a clean scan.**

- **(c) Conditional-gross-edge scan.** Estimand = pre-cost edge of the **unsized**
  wick-rejection signal — the ADR-0005 three-layer separation is mandatory here:
  the 1.0 C-config Kelly multipliers are position-layer policy, not signal
  evidence, and the same signal ranges +20.2% to −9.3% basket ROI across configs.
  **RC-H104-1 requires a fresh admission cycle**: MGC and SIL are outside the frozen
  design §2 universe ({ES, NQ, MES, MNQ}), so they enter as a **new trial-register
  entry** per the ADR-0002 post-hoc obligation, and the registered trial surface
  MUST carry the researcher degrees of freedom — the 5-config × 4-symbol sweep, the
  ~5-month **window extension** (realized OOS to 2026-05-15 past the registered
  2025-12-03/19 edge), and the **universe extension** (MGC/SIL). Romano-Wolf StepM
  over that full surface. The Kelly sweep {0.5, 0.75, 1.0, 1.25} replaces the ad-hoc
  super-Kelly / C3 configs (register addendum §3).

- **(d) Non-redundancy (marginal log-wealth).** H104 is the only non-equity-index
  (MGC/SIL, both post-hoc) and only mean-reversion candidate → a-priori the
  **strongest diversifier**, but the residual-correlation measurement is contingent
  on resolving the registration status of its strongest cells first.

- **Ladder (ADR-0007).** The DSR/PBO gates + matched-turnover rotor are the
  load-bearing guard: MGC's edge shows decay onset ≈2026-Q2 (memo §7a) and the
  fixed-cell hindsight-bias precedent (H062 C3 MGC −94% failed walk-forward CV), so
  the confirmation ladder must run under the ADR-0004 rolling regime, not the
  full-window +87% headline. This is precisely the overfit-at-leverage → **ruin**
  case ADR-0013 §8 makes hard-blocking.

- **Debt to clear first (heaviest of the five).** (i) Ledger backfill. (ii)
  **RC-H104-3 integrity closure is hard-blocking before admission (a)**: PIT-canary
  suite (`leakage-canary-deferred`), 13-field ReproLog wire (`repro-log-incomplete`
  per the v1 corrigendum), limit-fill-at-wick semantic (removes the known-optimistic
  next-bar-open entry, a Tier-2 claim class per
  [ADR-0006](../decisions/ADR-0006-execution-fidelity-tiers.md)), MPPM(ρ=1) CI
  primitive, walk-forward inner-CV, and the v1↔v2 numeric reconciliation (four
  discrepant v1-column cells). (iii) **RC-H104-2 cost application** on the MGC cells
  (3,000–10,000 trades) — flagged BLOCKING-BEFORE-PAPER-TRADE. (iv) The frozen §1
  net-Sharpe tri-benchmark H_1 was **never evaluated** — UNTESTED, not null.

---

## 4. Cross-cutting: RC-XCORR-1 and family registration

- **RC-XCORR-1 (ADR-0002(d) input for the 2nd+ admissions).** Pairwise net-of-cost
  (→ marginal-log-wealth under ADR-0013) residual correlations among admitted
  candidates. Known structural dependencies to resolve: H101↔H103
  session-complement pairing; H103↔H052a algebraic dependence; H102's window nested
  in the ORB first hour; H104 the sole non-equity-index / mean-reversion
  diversifier. Feeds the correlation bound **once the first admission (H101) defines
  the arsenal covariance** (§0.4).

- **Trial-register discipline (ADR-0008).** Every RC-* scan appends per-trial
  records to
  [config/multipletest_family.yaml](../../config/multipletest_family.yaml) when run
  (conditioning sets frozen per ADR-0002(b) **before** scanning), and every consumed
  OOS span mirrors to
  [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml) (already
  recorded 2026-07-10 for all 11 spans; commit SHA was pending). Confirmation-tier
  trials additionally join the `allocator-confirmation-kelly-sweep` family with the
  (config × Kelly-fraction) expansion.

- **Universal registration-conformance check** (register gap 5): every retro card
  is checked against the **frozen 1.0 design.md**, not only the KPI cards — the H055
  cards misquote their own frozen window/universe/H_1. This binds RC-H104-1 most,
  but applies to all five.

---

## 5. Open items for operator decision

1. **Sequencing vs the ledger.** All five gate on the backfill; confirm H101 is the
   intended first admission (it defines the arsenal-covariance memo every later
   candidate needs).
2. **H103 pooling universe.** RC-H103-1 proposes ES+NQ+MES+MNQ pooling to reach
   n≥174 — confirm the micro siblings are in the intended admission universe.
3. **H104 fresh-cycle scope.** Confirm MGC/SIL enter as a new admission cycle with
   their own trial-register entry, and that RC-H104-3 is a hard pre-admission gate
   (not a parallel track).
4. **Diversifier dispositions.** H103 and H104 are candidate `arsenal-admit-diversifier`
   rather than `arsenal-admit-conditional` — the disposition is an output of the
   rotor + RC-XCORR-1 evidence, deferred to scan time.
