# H101 screen addendum — RC-H101-2 (ADR-0014 SCREEN re-run protocol)

**Status: FROZEN at registration (2026-07-17), before any screen computation.**
Parent design: [design.md](design.md) (frozen SHA `a7c5c9178f66…`, 2026-07-16) —
**unchanged**; this addendum adds the ADR-0014 screen machinery only (the
estimand and conditioning set are those of the frozen design, per
[backfill_admission_plan_2026-07-17.md](../../../docs/research_notes/backfill_admission_plan_2026-07-17.md) §4.0).
Governing: [ADR-0014](../../../docs/decisions/ADR-0014-provisional-candidate-pool-screen-verdict.md)
Decision 1 (SCREEN), Decision 3 (H101 re-classed `pending screen re-run`);
ADR-0002 as amended; ADR-0008 (register increment, burned-data mirror);
ADR-0009 (Expert Card v2, append-only).

**Why no new HID:** ADR-0014 Decision 3 frames the re-run as a re-adjudication
of the SAME hypothesis under the amended admission machinery, with "a fresh
trial-register increment and an appended Expert Card version". A new HID would
break the ADR-0009 append-only card chain. Scan id: **RC-H101-2**; register
family: `rc-h101-2`; Expert Card: `expert_card_v2` cross-linking v1 (the retro
card) and the RC-H101-1 disposition.

## Screen gates (instantiated; all bounds are registered OUTPUTs, none hand-set)

- **(S-a) Interface / leakage canary.** Re-run the expert-contract causality
  canary (`assert_prefix_invariant`, default 16 cuts) on one evaluation sample
  per instrument at screen time; the backfill's canary evidence is referenced,
  not re-litigated. PASS = no prefix violation.
- **(S-b) Conditioning set.** UNCHANGED from the frozen design §3: cells
  {unconditional, high_vol, low_vol, first_hour_up, first_hour_down}; the vol
  terciles remain full-sample DESCRIPTIVE cutoffs (design §6's
  train-window-only rule binds gates, not descriptive covariates — the H101
  cells slice an unconditional strategy and do not define positions).
- **(S-c) Conditional gross edge.** Estimand unchanged (per-session pre-cost
  gross ORB edge per cell). Romano-Wolf StepM over the 5-cell family per
  instrument, stationary block bootstrap, **seed 20260716** (the design §11
  registered seed — the RC-H101-1 disposition's bit-identical re-run
  commitment), N_bootstrap 1000. A cell passes iff **mean gross > 0 AND
  RW-adjusted p < the enacted `screening_error_rate_target`** (0.7401 at
  freeze, full precision in config/multipletest_family.yaml, which governs;
  enacted 2026-07-17 by the round-1-remediated discovery-alpha instantiation; the positive-mean conjunct
  excludes the negative-effect pathology of one-sided levels above 1/2).
- **(S-d) Window persistence.** For every S-c-passing cell:
  - **DSR ≥ 1 − level = 0.2599 at freeze** (`dsr_bound_ref`; the config value governs), computed as in RC-H103-1
    (HAC effective n; skew/kurtosis-adjusted) at the GATE trial count
    **N_trials = 20** (the register's full distinct instrument×cell surface —
    the conservative raw count; the correlation-adjusted effective count from
    the measured cell correlations is REPORTED alongside, per ADR-0014
    Decision 4, but the gate binds at the raw count because a smaller N_eff
    lowers the deflation benchmark and would weaken the gate).
  - **PBO ≤ level = 0.7401 at freeze** (`pbo_bound_ref`; the config value
    governs) via CSCV (S = 16, the frozen pbo.py default) on the
    per-instrument **T×5 NaN-masked matrix** — each cell a strategy whose
    member sessions carry their gross return and non-member sessions NaN —
    scored by a **member-only Sharpe** `score_fn` (each column's Sharpe over
    its member sessions within each CSCV split; columns with < 2 members in
    a split rank last). The NaN masking gives the common-T row index
    standard CSCV requires (resolving the RC-H101-1 §3.5 deferral without
    touching the BLOCKED Kelly-fraction axis) while the member-only scorer
    removes the √(member-density) Sharpe shrinkage that zero-filled masking
    would impose unevenly across cells (audit round 2, QUANT-2-4 — the
    earlier equal-shrinkage claim was wrong and is retracted).
  - **Per-cell rolling-origin growth series** (design §6 6-month windows):
    per window × cell, the mean gross over member sessions — the
    `per_cell_oos_growth` vector of the pool-ledger record (stateless expert:
    every window is untrained data; persistence = across-window consistency).
  - The S-d/S-e stages are fully DETERMINISTIC (closed-form DSR,
    combinatorial CSCV, run-length medians) — no stage seed exists (the
    earlier draft's stage-seed line is retracted; audit round 2,
    QUANT-2-7).
- **(S-e) Ex-ante selectability (amended at freeze — see note).** Latency
  input = the P1-2.0-H900-BOCPD-WHITENED reproducible on-ledger emission
  (primary variant). That emission's verdict is **no accurate,
  non-degenerate operating point** (rule v2: net negative everywhere below
  the always-alarm corner; the sole calibrated-positive point fails the
  registered majority-coherence floor at FP 0.86), so the LATENT-STATE
  unsupervised detection latency is **UNATTAINABLE** (`latent_state_latency_attainable: false`) and any cell
  whose membership tracks a latent state FAILS S-e outright. The H101 cells
  are RULE-BASED CAUSAL covariates (they slice an unconditional strategy on
  realized data): membership is computable at decision time, so the causal
  allocator selects by DIRECT OBSERVATION and each cell's S-e latency input
  is its STRUCTURAL OBSERVATION LAG in RTH bars — 0 for the session-start
  trailing-rvol cells (covariate window ends at/before the open) and 12 (the
  opening-range window) for the first-hour-sign cells, both known before any
  ORB entry decision. PASS = median consecutive-session membership run x 78
  RTH bars/session >= the cell's observation lag; the latent-state
  UNATTAINABLE verdict is recorded on every cell as the reason
  HMM-state-conditioned cells cannot pass this gate. (Amendment note: the
  originally drafted rule consumed a "KM median at best-net" scalar; the
  reproducible 1c emission returned no positive-net operating point, so that
  rule degenerates — the deviation is recorded in the 1c artifact, the
  whitening memo addendum, and here, all BEFORE any screen computation.)

## Disposition rule (ADR-0009/0014)

- ≥ 1 cell passes S-a ∧ S-b ∧ S-c ∧ S-d ∧ S-e → **screen PASS** →
  `pool-hold-reconsider`-eligible pool entry: Expert Card v2 emitted, pool
  ledger record generated from card §3–5 (never hand-copied), trial register
  + burned-data ledger incremented. **STOP before any set-level VERDICT**
  (|arsenal| = 0; first-member stop per the execution brief).
- No cell passes → **`archive-no-persistent-window`** (with
  `archive-no-gross-edge` sub-reason iff S-c passed nowhere), Expert Card v2
  emitted, register incremented. "fail" is not a disposition.
- Certification: NOTHING is certified by a screen pass; pool entry is a queue
  position, not membership (ADR-0014 Decision 6).

## Register / integrity commitments

- Family `rc-h101-2` appended to
  [config/multipletest_family.yaml](../../../config/multipletest_family.yaml)
  BEFORE the run (per-trial records at scan time; ADR-0008 D6).
- Burned-data ledger: the RC-H101-2 evaluation spans (ES+NQ ledger sessions,
  2015–2025 primary-exclusion substrate) mirrored to
  [config/burned_data_ledger.yaml](../../../config/burned_data_ledger.yaml).
- ReproLog emitted BEFORE the scan (this addendum's SHA-256 in
  `config_resolved_sha256`); harness `scripts/run_screen_h101_h103.py`.
- Evidence source: the CANONICAL k1.0 ledger partitions only (ADR-0003).
