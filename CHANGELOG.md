# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (VERDICT-1 freeze + first-admission queue — NO ADMISSION, 2026-07-19)
- **VERDICT-1 first-admission protocol FROZEN** (SHA-256
  `ac611bc4a786717a249c93b58b61ed5b400f686a18e4735b911e3db7137e10ef`; freeze
  ReproLog `repro_log_f975dcef3c05…`;
  `research/02_verdict/VERDICT-1_protocol.md`;
  `docs/audits/audit_trail_2026-07-19_verdict-1-freeze.md`, 3-round ACCEPT)
  under the operator's 2026-07-19 authorization (ADR-0015 lift + ADR-0017
  realized-bar precondition input + verdict authorization). Two prerequisite
  frozen estimators: **Hansen 2005 SPA** (`src/skie_universe2/inference/hansen_spa.py`,
  arch==8.0.0 cross-validation, 13 tests, memo) and **panel Romano-Wolf
  StepM** (`romano_wolf_stepm_panel`, k=1 masked-equivalence, 7 tests, memo).
  Session-aligned 8-column (instrument × Kelly-arm) joint panel; registered
  surface 16/40; rolling-train B1/B3; level read at runtime. Shared candidate
  registry `src/skie_universe2/verdict/registry.py`; adjudication harness
  `scripts/run_verdict.py`; disposition emitter
  `scripts/emit_verdict_disposition.py` (protocol §7 substrate-grade labeling).
- **First-admission queue executed: H106 and H105 both NOT admitted; arsenal
  remains EMPTY** (`docs/reports/VERDICT-1/verdict_queue_outcome_2026-07-19.md`).
  H106 fails the matched-turnover rotor (net-not-monetizable); H105 fails the
  non-waivable DSR persistence bound under the cumulative 72-trial deflation.
  The ADR-0014 D3 ORB re-adjudication and the Work-Plan-D first-admission
  triggers did NOT fire (no incumbent-set change). Append-only:
  `first-admission-verdict` register +32 trials, pool +8 copy-forward records,
  burned ledger +60 `admission-verdict` spans, two Expert Card v2s. No
  `config/arsenal.yaml`; no Kelly fraction selected.
- **DR-1/DR-2 December-roll repair — agent-side prep AUDIT-ACCEPTED** (3-round;
  `docs/audits/audit_trail_2026-07-19_dr-repair-phase4-bundle.md`): the
  append-only `DEC_ROLL_LATE_COMMIT` defect record restored byte-identical,
  roll-citation attribution reconciled (LITERATURE-1-4 partially closed —
  roll-date convention pinned, ~8-day early-migration figure an internal
  estimate), runbook §5.0 flags the ingest-merge stage NOT-YET-BUILT.
  Governance-level spend authorized; execution operator-only.
- **Phase-4 confirmation protocol drafted `proposed`**
  (`research/02_verdict/PHASE4_confirmation_protocol_PROPOSED.md`) — authorizes,
  runs, and registers nothing.

### Added (Phase-3 forward batch — H105/H106 screened into the pool, 2026-07-19)
- **P3-A overnight/Globex substrate feasibility: GO.** ETH bars present at
  full session coverage (186 five-minute overnight bars/session at the
  median, both instruments); December/Globex blind spot quantified from the
  provenance register (91 ES / 101 NQ excluded sessions, 3.32%/3.66%;
  69.0%/67.8% of excluded bars are overnight-ETH; processed substrate ends
  2025-12-03 ES / 2025-12-05 NQ). Harness
  `scripts/run_overnight_substrate_check.py`; record
  `docs/research_notes/overnight_globex_substrate_feasibility_2026-07-19.md`;
  session-segment classifier single-sourced into
  `src/skie_universe2/utils/sessions.py` (+9 boundary/DST tests). 2-round
  audit accept (`docs/audits/audit_trail_2026-07-19_p3a-overnight-substrate-check.md`).
- **H105 (overnight/Globex session drift) + H106 (VR range-state reversal)
  pre-registered and FROZEN** (design SHAs `64753d968289…` /
  `cb18e545ddb2…`; freeze ReproLogs f69c1cdb359c / 3e5e41a1d9c3) after a
  3-round audit-remediate ACCEPT
  (`docs/audits/audit_trail_2026-07-19_h105-h106-preregistration.md`; 20
  confirmed majors remediated across rounds incl. a refuter-reproduced HAC
  bandwidth-cap crash; 4 false positives killed at the adversarial gate).
  New experts `overnight_drift.py` / `vr_range_reversal.py` (+17 tests);
  packaged ADR-0014 screen spine
  `src/skie_universe2/screening/screen_spine.py` (leakage-clean per-origin
  vol cells, matched DSR count/dispersion surfaces, §8 KPSS/CI/precision/
  Lo-SE/Ledoit-Wolf exhibits, fail-closed dispersion + ledger-checksum
  binding; +14 tests); v1 disposition emitter
  `scripts/emit_screen_expert_card_v1.py` (card + pool + register trials +
  scripted burned-span mirror); pre-data power gates (S-c well-powered at
  the enacted level; §8 precision declared unreachable at literature
  effects).
- **Both candidates backfilled and SCREEN PASS at the enacted level.**
  5,196,320 rows × 2 experts (ES+NQ × Kelly {0.5,0.75,1.0,1.25}, canaries
  PASS). RC-H105-1: 6 passing cells (unconditional overnight drift present
  gross but fails S-d — persistent windows are conditional). RC-H106-1: 4
  passing ES cells (ES:low_vol DSR 1.000 / PBO 0.047; NQ fails S-d
  everywhere). Pool: **16 records / 4 HIDs / 3 distinct expert_hash**;
  trial register +20; burned-data ledger +60 window-spans.
- **ADR-0015 verdict precondition: MET (label-based, reporting-only) — and
  the mandatory M1 companion inverts it** (`reports/M1_overlap/`):
  ORB↔H105 realized-bar Jaccard **0.0 exactly** (frozen §12(c) identity
  confirmed) yet label-blocked by a `NQ:high_vol` name collision;
  ORB↔H106 label-disjoint yet sharing 8.9% of realized bars. Operator
  brief `docs/research_notes/verdict_readiness_memo_2026-07-19.md`:
  cold-start queue H106 > H105 > H101 > H103 (H106 net-not-monetizable
  caveat declared); **DR-1/DR-2 now BINDING for confirmation-grade
  adjudication of H105**. STOPPED at the operator gates (ADR-0015
  `lift_action`; DR-1/DR-2 spend; ADR-0016 stage B undecided). Nothing
  certified; no Kelly fraction selected; arsenal EMPTY.

### Added (OD-G adjudication + ADR-0016 Tier-2 scoping — accepted 2026-07-19)
- **ADR-0016 — Tier-2 execution-fidelity scoping, ACCEPTED (stage A only; by
  principal direction 2026-07-19; no spend authorized).** Queue-position +
  fill-probability model class (not book replay); bounded-MBO-validates-MBP-10
  data strategy; load-bearing execution-model overfitting guard (fill
  assumption SWEPT pessimistic/central/optimistic; every pair a registered
  trial; claims must survive the whole range); staged A→D gates with three
  recordable states (authorized/declined/undecided) and the first spend at
  stage B; **Decision 10** promotion-vs-successor rule (unchanged estimand =
  same-HID promotion via append-only execution-tier addendum; changed
  estimand = successor HID under ADR-0008 D5 — OD-G Form B is the
  successor-HID case). Accepted after round-1 remediation of the 15-agent
  argument-validity audit (12 majors fixed; 1 critical refuted at the gate;
  `docs/audits/audit_trail_2026-07-19_odg-deliverables-argument-audit.md`).
- **OD-G resolved and deferred.** Form A (Tier-0 conditioning) is the
  admissible form but is DEFERRED out of the Step-5 batch; forward-sourcing
  priority fixed: (1) overnight/Globex, (2) mean-reversion, (3) macro-calendar,
  (4) spread/liquidity. `docs/research_notes/od_g_spread_liquidity_setup_plan_2026-07-18.md`
  and `docs/research_notes/databento_pull_spec_cost_sheet_2026-07-18.md`
  remediated per the audit and first-committed.
- **DEC-roll repair elevated.** `P1-2.0-DATABENTO-DEC-ROLL-REPULL` elevated to
  quote-ready top purchase priority (DR-1/DR-2 spec in the cost sheet;
  operator-only spend, not yet authorized).

### Added (ADR-0015 ratified pool HOLD — accepted 2026-07-18; logged retroactively 2026-07-19)
- **ADR-0015 — Ratified pool HOLD + verdict precondition, ACCEPTED 2026-07-18**
  (omitted from this changelog at the time): set-level VERDICT held until
  ≥ 2 distinct `expert_hash` values with non-overlapping coverage vectors;
  reporting-check-only checker `scripts/audits/check_verdict_precondition.py`
  (BLOCKED: `distinct_expert_hash_count = 1`); lift is a named, dated operator
  authorization.

### Added (ADR-0014 provisional candidate pool — accepted + enacted 2026-07-17)
- **ADR-0014 — Provisional candidate pool (screen/verdict split), ACCEPTED.**
  Splits ADR-0002 admission into a singleton SCREEN (persistent, ex-ante-selectable
  competence window → provisional pool) and a set-level VERDICT (marginal
  geometric-growth on the ADR-0007 ladder); adds `pool-hold-reconsider` and
  `archive-no-persistent-window` dispositions (ADR-0009); re-classes H101/H103 as
  reconsideration-eligible pending a screen re-run. Pool-ledger schema
  `config/pool_ledger_schema.yaml` (ranking weights an OUTPUT of the
  standing-monitored `P1-2.0-POOL-PRIORITY-CALIBRATE`; path-maxima barred from
  ranking; S-e latency BLOCKED on `P1-2.0-H900-BOCPD-WHITENED`). Amendment-map
  banners + `amended_by` added to ADR-0002/0004/0007/0009 (decision bodies not
  rewritten in place). 2-round audit-remediate accept
  (`docs/audits/audit_trail_2026-07-17_adr0014-pool-ledger.md`, incl. a self-caught
  YAML parse fix). Governance-only: no Kelly fraction selected, no discovery level
  set, no admission certified.
- **`P1-2.0-POOL-PRIORITY-CALIBRATE` registered** (standing, monitored, non-blocking).

### Changed (forward planning consolidated, 2026-07-17)
- Consolidated the two 2026-07-16 scoped notes into
  `docs/research_notes/backfill_admission_plan_2026-07-17.md` (tactical) and the new
  `docs/research_notes/program_roadmap_2026-07-17.md` (Phase 0–5 strategic);
  archived `shadow_ledger_backfill_plan_2026-07-16.md` and
  `retro_card_admission_roadmap_2026-07-16.md` under `docs/research_notes/archive/`
  with SUPERSEDED banners. CLAUDE.md updated (ADR-0014 row, ADR-0002 amendment note,
  `P1-2.0-POOL-PRIORITY-CALIBRATE` registration, Progress).

### Added (H900-BOCPD-WHITENED method-freeze, 2026-07-14)
- **`P1-2.0-H900-BOCPD-WHITENED` — METHOD FROZEN.** Finalized from PARKED: the
  AR(1)-prewhitening primitive `src/skie_universe2/inference/whitening.py`
  (within-run φ estimation that excludes change-crossing pairs; innovation filter
  `w_t = (z_t − φ z_{t−1})/√(1 − φ²)`; prewhitened/residual control-chart
  construction per [Alwan & Roberts 1988](https://doi.org/10.1080/07350015.1988.10509640),
  [Runger & Willemain 1995](https://doi.org/10.1080/00224065.1995.11979608), Box
  & Jenkins 1976), 13 tests, and methodology memo
  `docs/methodology/whitening_ar_robust_bocpd_2026-07-13.md`. 2-round
  audit-remediate accept (24 findings, 0 refuted, all remediated;
  `docs/audits/audit_trail_2026-07-14_handoff-resolution.md`). Prewhitening the
  near-unit-root (ρ≈0.997) log-rvol removes the by-construction autocorrelation
  and keeps real shifts detectable, but does not control false alarms at the
  Bayes operating point (~0.43); the ROC-wide NO-GO robustness rests on the prior
  on-ledger ROC probe (net≈26pp @ L_detect≈45; ~4 bars→noise, session_handoff §2),
  with a reproducible on-ledger prewhitened ROC re-run **DEFERRED** to the
  shadow-ledger backfill. ReproLog `logs/reproducibility/repro_log_56b6293a…json`.

### Changed (retro-card register — ADR-0013 re-adjudication addendum, 2026-07-14)
- **`P1-2.0-RETRO-CARD-1.0-REGISTER` metric-currency reconciliation.** Added an
  ADR-0013 re-adjudication addendum to
  `docs/research_notes/retro_card_register_2026-07-10.md`: the retro cards'
  old-paradigm currency (net-Sharpe/LW2008, terminal-wealth q05 lower-tail
  quantile, MPPM/Calmar/PF) is superseded by geometric (log-wealth) growth as the
  binding admission/ranking metric; the lower-tail quantile is demoted to a
  monitored guardrail; the Kelly fraction is swept {0.5,0.75,1.0,1.25}; discovery
  alpha is cost-tuned; the integrity core is more binding under leverage. Numeric
  re-adjudication is **DEFERRED** (BLOCKING on the shadow-ledger backfill + the
  Kelly numeric instantiation + `P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE`); the
  register stays OPEN.

### Fixed (handoff-review reconciliation + identity hygiene, 2026-07-14)
- **Handoff-review findings reconciled.** Annotated
  `docs/research_notes/handoff_review_findings_2026-07-13.md`: Findings 1–3
  (snapshot staleness) and 5 (hygiene) confirmed and actioned; Findings 4 & 6
  **REFUTED in the persistent working container** (the whitening source/tests and
  the untracked run inventory are present here, not lost) — per-finding
  correction blocks + a top correction banner added.
- **Identity-hygiene leak fixed.** Stripped the absolute OS-username path from
  `docs/research_notes/session_handoff_2026-07-12.md` L297 and sanitized the
  quoted path in the findings report's Finding 5 (per rules/publishing.md).

### Changed (aggressive geometric-growth mandate — ENACTED, 2026-07-12)
- **ADR-0012 / ADR-0013 accepted and enacted.** The principal accepted ADR-0012
  (standing-incumbent champion-challenger) and ADR-0013 (aggressive
  geometric-growth mandate). Both flip `status: proposed -> accepted`; the five
  amended-ADR banners (ADR-0002/0004/0005/0007/0010) and the
  `allocator-confirmation-kelly-sweep` config family flip to `accepted`; the
  ADR-0013 amendment map is now the authoritative in-force amendment record
  (decision bodies not rewritten in place). Registered a third BLOCKING gate,
  `P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE` (ADR-0012): the champion-challenger
  framework is in force but the dethroning rule is non-operational until that
  memo is frozen. Empirical Kelly-fraction selection on geometric growth and
  enactment of any loosened discovery target remain gated on the two BLOCKING
  Decision-9 memos below.

### Added (Kelly calibration memos — method-frozen, 2026-07-12)
- **`P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` — METHOD FROZEN.** New estimator
  `src/skie_universe2/inference/kelly_growth.py` (D1 concavity / interior-max on
  the empirical fat-tailed measure with the finite-log-moment condition per
  [Algoet & Cover 1988](https://doi.org/10.1214/aop/1176991793); D2
  estimation-error rolling-origin f\*\*; D3 single-period ruin barrier with the
  -inf convention; D4 over-betting zero-growth crossing; D5 frozen
  ruin-consistent estimator = absorbing barrier + P(ruin) +
  [Busseti-Ryu-Boyd 2016](https://doi.org/10.3905/joi.2016.25.3.118) drawdown
  bound + stationary-bootstrap CIs), 30 tests, and methodology memo
  `docs/methodology/kelly_growth_concavity_ruin_2026-07-12.md`. 3-round
  audit-remediate accept. No Kelly fraction selected; numeric on-ledger
  instantiation deferred to the step-4 shadow-ledger backfill.
- **`P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` — METHOD FROZEN.** New
  estimator `src/skie_universe2/inference/discovery_alpha.py` (RD1 asymmetric
  log-wealth loss; RD2 ruin-linkage conditional on Memo 1 + ADR-0010; RD3
  base-rate via [Storey & Tibshirani 2003](https://doi.org/10.1073/pnas.1530509100)
  / [Efron 2008](https://doi.org/10.1214/07-STS236); RD4 decision-theoretic
  threshold via [Müller et al. 2004](https://doi.org/10.1198/016214504000001646)
  / [Sun & Cai 2007](https://doi.org/10.1198/016214507000000545); RD5 FWER->FDR
  with the PRDS / [Benjamini-Yekutieli 2001](https://doi.org/10.1214/aos/1013699998)
  obligation, retain-FWER honestly admissible), 28 tests, and methodology memo
  `docs/methodology/discovery_alpha_cost_calibration_2026-07-12.md`. 2-round
  audit-remediate accept. No target enacted; numeric alpha level / criterion
  deferred to step-4; `config/multipletest_family.yaml` left with OUTPUT
  placeholders.

### Changed (aggressive geometric-growth mandate — governance detail; superseded by the ENACTED entry above, 2026-07-12)
- **ADR-0013 — aggressive geometric-growth mandate (keystone, STATUS: proposed).**
  Reframes SKIE-Universe 2.0 from risk-averse tail protection to optimism +
  compounded geometric growth: installs Kelly log-wealth growth rate as the
  primary objective ([Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x);
  [MacLean, Thorp & Ziemba 2011](https://doi.org/10.1142/7598)), sweeps the
  Kelly fraction as a registered hyperparameter {0.5, 0.75, 1.0, 1.25} with the
  winner data-selected by best geometric growth over the joint
  (allocator-config × Kelly-fraction) space, demotes the lower-tail
  terminal-wealth quantile to a monitored non-binding guardrail, cost-tunes the
  discovery alpha looser, loosens ADR-0002 admission, and steepens the ADR-0010
  ramp. Reaffirms the overfitting/integrity core (DSR/PBO, matched-turnover
  random rotor, PIT canaries, trial register, ReproLog, shadow ledger,
  SPA/StepM) as NON-WAIVABLE and MORE binding under leverage. Gated by two
  BLOCKING follow-ups: `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` and
  `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`.
- **ADR-0012 — standing-incumbent allocator / champion-challenger (STATUS:
  proposed).** Champion ranked on geometric growth, dethroned only via the
  ADR-0007 confirmation ladder.
- 18-row amendment map + `amended_by` banners on ADR-0002/0004/0005/0007/0010;
  reframed methodology doc, README, CLAUDE.md, and config; rationale-only H900
  report reframes. 3-round audit-remediate accept; integrity core preserved
  every round. **Now ACCEPTED and enacted (2026-07-12); the amendment map is the
  authoritative in-force record. Empirical Kelly-fraction selection and
  loosened-alpha enactment remain gated on the two BLOCKING calibration memos,
  now method-frozen (numeric instantiation deferred to the step-4 backfill).**

### Added (H900 sensitivity + conditioning set, 2026-07-11/12)
- **H900 BOCPD detection-latency sensitivity (Step 2).** New unsupervised
  change-point detector `src/skie_universe2/inference/bocpd.py` (Adams-MacKay
  2007 port; [arXiv:0710.3742](https://arxiv.org/abs/0710.3742)) and
  reproduction gate `scripts/audits/check_h900_bocpd_reproduction.py`.
  CUSUM verdict GO reproduced bit-identically; BOCPD (unsupervised) is NO-GO on
  both variants (ES L_detect 66 / NQ 52 bars vs KM dwell 12 / 9) — establishing
  that the H900 GO is **supervised-detection-dependent**. Closes report
  deviation-1. Report at
  `reports/H900/H900_bocpd_sensitivity_2026-07-11.md`; 3-round audit-remediate
  accept.
- **Conditioning-set registration + standing report objects (Step 3).**
  Registered the winning 4-state diagonal-covariance Gaussian HMM (on
  standardized `ret_5m`, log `rvol_5m_24h`) as the ADR-0002 candidate
  conditioning covariate — ADR-0001-D5-compliant covariate-not-gate —
  in `config/conditioning_covariates.yaml`; registered dwell-time and
  detection-latency as standing ADR-0004 metric-family report objects in
  `docs/methodology/allocator_metric_family_report_objects.md`. 2-round
  audit-remediate accept.

### Investigation (2026-07-12)
- **`P1-2.0-H900-BOCPD-WHITENED` — COMPLETE; NO-GO robust.** Whitened/AR-robust
  BOCPD prewhitening the near-unit-root log-rvol
  ([Fearnhead & Liu 2007](https://doi.org/10.1111/j.1467-9868.2007.00601.x)),
  tested on the archived filtered sequences without refit. The full
  net-detection-vs-hazard ROC shows no operating point is both accurate and
  timely (best discrimination net ~26pp needs L_detect ~45 bars; low latency
  ~4 bars is pure noise). Whitening does NOT rescue the NO-GO; the
  supervised-detection-dependence of the H900 GO is robust. Module +
  tests drafted but PARKED/uncommitted on branch
  `claude/h900-bocpd-whitened`; finalized deliverable pending.

### Added (research program launch, 2026-07-10)
- **Phase B** — retro Expert Cards H100–H104 (ADR-0009) from 1.0 evidence for
  H050/H052a/H053/H054/H055; register digest; burned-data ledger seeded with
  11 spans; closes `P1-2.0-RETRO-CARD-1.0-REGISTER`. 3-round audit-remediate
  accept (10 confirmed findings remediated, 0 refuted); trail at
  `docs/audits/audit_trail_2026-07-10_phaseB-retro-expert-cards.md`.
- **Phase C** — `skie_universe2` package: numerical-fidelity port of the 1.0
  roll-adjusted ingest (bit-exact vs the registered 1.0 reference on shared
  columns), shadow-ledger writer per ADR-0003 (journaled two-phase commit,
  atomic partition claims, locked JSONL trails, covariate registry), ADR-0011
  registry-refusal gate, ES+NQ evidence bars materialized with `pit_provisional`
  PIT flags and a machine-readable December-roll substrate-defect register
  (operator follow-up `P1-2.0-DATABENTO-DEC-ROLL-REPULL`). 105 tests. 3-round
  audit-remediate accept (2 criticals remediated); trail at
  `docs/audits/audit_trail_2026-07-10_phaseC-substrate-shadow-ledger.md`.
- **Phase A pre-registration** — H900 dwell-time feasibility gate (ADR-0004
  Decision 6) frozen: 11-section design at
  `research/01_hypothesis_register/H900/design.md`, singleton multipletest
  family registered, freeze ReproLog with `config_resolved_sha256` = design
  SHA-256.
- **Phase A execution (2026-07-11) — H900 verdict: GO.** Registered §10 H1
  criterion met on BOTH instruments (ES pooled KM median dwell 12 bars CI
  [10,14] vs break-even 4.45; NQ 9 bars CI [8,10] vs 2.54; inclusive
  sensitivity also GO). 1.0 HMM toolkit + stationary-bootstrap ports,
  dwell/KM/CUSUM/cost modules, 146 new tests (suite 251). 3-round
  audit-remediate accept (10 confirmed findings remediated incl. a PW
  block-length selector defect and a fee erratum, 0 refuted); trail at
  `docs/audits/audit_trail_2026-07-11_phaseA-h900-dwell-feasibility.md`;
  report at `reports/H900/H900_dwell_feasibility_report_2026-07-11.md`.
  The allocator program proceeds; 4-state diag Gaussian HMM registered as
  the ADR-0002 conditioning-set candidate.

### Fixed
- `uv sync` failure on fresh clone: empty `[build-system]` table in
  `pyproject.toml` replaced with explicit `[tool.uv] package = false`
  (repo is intentionally non-installable).
- `.gitignore` parent-directory exclusions defeated the `!**/.gitkeep`
  negations (gitignore(5) re-include semantics); rewritten to contents-level
  patterns so all 28 `manifest.json` subdirs survive a clone. `.gitkeep`
  added to the 11 previously untrackable directories.
- Machine-local absolute hook paths in `.pre-commit-config.yaml` replaced by
  vendored scripts under `scripts/` (seed-guard entry also referenced a
  nonexistent module); hooks now run on any clone.
- `CITATION.cff` failed its own validator: unquoted `<<TODO: ...>>`
  placeholders broke YAML parsing; quoted.
- Stale `manifest.json` file SHAs (CHANGELOG.md, CLAUDE.md, README.md drifted
  at the ADR commit); all 11 refreshed via the LF-normalized SHA-256
  bootstrap convention.
- `uv.lock` line-ending churn on Windows pinned via `.gitattributes`.

### Added
- `uv.lock` committed (87 packages) — reproducible dependency resolution.
- `data/_manifest.json` (empty initial manifest) per the reproducibility
  contract; generator vendored at `scripts/build_data_manifest.py`.
- Bootstrap-integrity smoke tests at `tests/test_bootstrap_integrity.py`
  (manifest subdirs, ADR links, pyproject validity, data manifest,
  no machine-local hook paths).
- CI workflow `.github/workflows/ci.yml`: uv sync + pytest + ruff +
  data-manifest drift check on push/PR.
- ADR-0011: two-level data storage and provenance policy (machine-level raw
  store + project-level processed; shadow-ledger substrate sourcing from
  SKIE-Universe 1.0).
- `config/data_sources.yaml` registering upstream data sources with
  checksums.
- Founding governance: ADR-0001 through ADR-0010 under `docs/decisions/`
  (allocator as unit of inference; arsenal admission standard; shadow ledger;
  rolling evaluation regime; three-layer separation; execution fidelity tiers;
  two-tier discovery pipeline; integrity non-negotiables; Expert Card terminal
  deliverable; live-capital escalation schedule).
- Expert Card template at `docs/templates/expert_card_TEMPLATE.md` (ADR-0009).
- CLAUDE.md founding-governance section binding the ADR set as standing rules.
- Trial-register and burned-data-ledger stub schemas under `config/` (ADR-0008
  Decisions 5-6).
- 3-round audit-remediate loop on the founding governance: 11 majors
  confirmed and remediated (0 refuted), final verdict accept; trail at
  `docs/audits/audit_trail_2026-07-10_founding-adrs.md`.


## [0.0.1] - 2026-07-10

### Added
- Initial bootstrap via `/bootstrap-project --kind=quant`.
- Directory tree per SKIE-Universe canonical layout.
- `manifest.json` recording `bootstrap_script_git_head=fe9bcd1b6fee`.
- Pre-commit hooks registered: ruff, nbstripout, nbqa, seed-guard, citation-cff.
