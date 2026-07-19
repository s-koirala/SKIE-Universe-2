# SKIE-Universe-2 — Project-Local Rules

Inherits all user-global rules from `~/.claude/CLAUDE.md` plus the imported
cwd-scoped rule file: `rules/quant-project.md` (activated automatically when this
project's path matches the rule's cwd globs).

## Scope

Meta-strategy allocation research program (SKIE Universe 2.0). The unit of
statistical inference is the **allocator** (online strategy selection over an
arsenal of expert strategies), not the individual strategy — see ADR-0001.
Hypothesis-driven; pre-registered design.md per hypothesis; rolling-origin
evaluation over the shadow ledger with purge + embargo; Hansen SPA +
Romano-Wolf StepM identification + DSR + PBO gate at the allocator
confirmation tier only.

Capital posture is optimism + exponential (compounded) growth via a high-risk
methodology (ADR-0013, accepted 2026-07-12). The **primary decision/ranking metric is
geometric (compounded / Kelly log-wealth) growth** — mean log-wealth growth
rate — computed on the shadow ledger, replacing the lower-tail terminal-wealth
quantile as the binding objective. The position-layer **Kelly fraction is a
registered swept hyperparameter over {0.5, 0.75, 1.0, 1.25}**, reported for all
points; the winner is data-selected by best geometric growth over the joint
(allocator-config × Kelly-fraction) space, never hand-tuned. The BLOCKING
`P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` memo is frozen AND numerically
instantiated on-ledger (2026-07-17; grid-bracketing verdict
inconclusive-on-null-ledger, re-instantiated at first admission) — fraction
SELECTION remains a Phase-4 champion action and is additionally blocked on
arsenal ≥ 1. The lower-tail
terminal-wealth quantile is **demoted to a monitored, non-binding guardrail**
(still computed at the same bootstrap/block length and reported, but it informs
rather than vetoes). Discovery alpha (SPA / StepM FWER, or FDR where the cost
analysis supports it) is **cost-tuned looser** via the registered
error-rate-cost follow-up `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`
(missed compounding weighted above false discovery; the level is the analysis
output, not a constant — ENACTED 2026-07-17: `screening_error_rate_target`
= 0.7401, criterion retain-fwer). ADR-0002 admission is loosened toward aggressive
inclusion (conditional-edge + non-redundancy structure kept; non-redundancy
re-expressed on marginal log-wealth growth); **ADR-0014 (accepted 2026-07-17)
further re-composes admission into a singleton SCREEN → provisional pool + a
set-level VERDICT (marginal-geometric-growth on the ADR-0007 ladder), with
`pool-hold-reconsider` making screen-passing-but-unselected experts
reconsideration-eligible**; the ADR-0010 live-capital ramp is
steepened for a proven champion. The overfitting/integrity core —
Deflated-Sharpe, PBO, matched-turnover random rotor, PIT canaries, trial
register, ReproLog, shadow ledger — is **NON-WAIVABLE and more binding under
leverage**: an overfit champion at leverage ruins (negative geometric growth on
a fake edge) rather than merely underperforming, so aggression on sizing and
discovery is bought with strictly more conservative multiplicity accounting,
never weaker correction. The whole reframe is STATUS: accepted (enacted on
ADR-0013 acceptance, 2026-07-12); empirical enactment of the loosened discovery
targets and any swept Kelly-fraction selection on geometric growth remain gated
on the two BLOCKING Decision-9 calibration memos.

## Founding governance (binding; read before any research work)

The founding ADRs in [docs/decisions/](docs/decisions/) are standing rules:

| ADR | Mandate |
|---|---|
| [ADR-0001](docs/decisions/ADR-0001-allocator-unit-of-inference.md) | Allocator is the unit of inference; strategy-level deployment gates abolished |
| [ADR-0002](docs/decisions/ADR-0002-arsenal-admission-standard.md) | Arsenal admission: conditional gross edge + non-redundancy; no standalone burden (amended by ADR-0014 → split into a singleton SCREEN → provisional pool + a set-level VERDICT; screen-pass/verdict-non-select = `pool-hold-reconsider`) |
| [ADR-0003](docs/decisions/ADR-0003-shadow-ledger-canonical-object.md) | Shadow ledger (every expert × asset × bar, counterfactual, append-only) is the sole evidence source |
| [ADR-0004](docs/decisions/ADR-0004-rolling-evaluation-regime.md) | Rolling-origin evaluation only; metric family incl. regret vs switching oracle; dwell-time feasibility gate first |
| [ADR-0005](docs/decisions/ADR-0005-three-layer-separation.md) | Signal / position-policy / execution layer separation; fractional Kelly with registered lower-tail-quantile binding (amended by ADR-0013 to the swept-fraction {0.5,0.75,1.0,1.25} / geometric-growth form; quantile demoted to guardrail); no cross-layer tuning |
| [ADR-0006](docs/decisions/ADR-0006-execution-fidelity-tiers.md) | Execution tiers 0/1/2; scalping/limit-order claims unreportable below Tier 2 |
| [ADR-0007](docs/decisions/ADR-0007-two-tier-discovery-pipeline.md) | Exploration tier (cheap, labeled) + confirmation ladder incl. non-waivable matched-turnover random rotor |
| [ADR-0008](docs/decisions/ADR-0008-integrity-non-negotiables.md) | PIT canaries, bar-level costs, ReproLog, pre-registered scans, burned-data ledger, trial register — every tier |
| [ADR-0009](docs/decisions/ADR-0009-expert-card-terminal-deliverable.md) | Expert Card (8 sections) is the mandatory terminal deliverable; "fail" is not a disposition |
| [ADR-0010](docs/decisions/ADR-0010-live-capital-escalation.md) | Live size earned by live-vs-shadow tracking on a pre-declared escalation schedule |
| [ADR-0011](docs/decisions/ADR-0011-two-level-data-storage-and-provenance-policy.md) | Two-level data storage: machine-level raw store + project-level processed; upstreams registered in [config/data_sources.yaml](config/data_sources.yaml); no cross-repo processed imports |
| [ADR-0012](docs/decisions/ADR-0012-standing-incumbent-allocator.md) (accepted) | Standing incumbent allocator (champion-challenger): the current best allocator configuration is the live default + live-capital anchor; a challenger dethrones it only via the ADR-0007 ladder by a geometric-growth-improvement margin after a minimum champion dwell (accepted 2026-07-12; sits atop ADR-0013; dethroning rule non-operational until `P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE` frozen) |
| [ADR-0013](docs/decisions/ADR-0013-aggressive-geometric-growth-mandate.md) (accepted) | Aggressive geometric-growth mandate: geometric (compounded/Kelly log-wealth) growth becomes the primary objective; Kelly fraction a registered swept hyperparameter {0.5,0.75,1.0,1.25} winner data-selected; lower-tail terminal-wealth quantile demoted to a monitored non-binding guardrail; discovery alpha cost-tuned looser; ADR-0002 admission loosened; ADR-0010 ramp steepened; DSR/PBO/rotor/canaries/register/ReproLog/ledger non-waivable and more binding under leverage. Amends ADRs 0002/0004/0005/0007/0010 |
| [ADR-0014](docs/decisions/ADR-0014-provisional-candidate-pool-screen-verdict.md) (accepted) | Provisional candidate pool (screen/verdict split): ADR-0002 admission split into a singleton SCREEN (persistent, ex-ante-selectable competence window → provisional pool) + a set-level VERDICT (marginal geometric-growth on the ADR-0007 ladder); screen-pass/verdict-non-select = `pool-hold-reconsider` (reconsideration-eligible, re-adjudicated on incumbent-set change); pool-priority ranking a standing-monitored OUTPUT (`P1-2.0-POOL-PRIORITY-CALIBRATE`), path-maxima barred; resolves the empty-arsenal cold-start. Amends ADRs 0002/0004/0007/0009 (accepted 2026-07-17) |
| [ADR-0015](docs/decisions/ADR-0015-ratified-pool-hold-verdict-precondition.md) (accepted) | Ratified pool HOLD + verdict precondition: the set-level VERDICT is held until ≥ 2 distinct `expert_hash` values with non-overlapping coverage vectors exist (operator-directed, provisional; reporting-check-only checker [check_verdict_precondition.py](scripts/audits/check_verdict_precondition.py)); the lift is a named, dated operator authorization (accepted 2026-07-18) |
| [ADR-0016](docs/decisions/ADR-0016-tier2-execution-fidelity-scoping.md) (accepted) | Tier-2 execution-fidelity scoping: queue-position + fill-probability model class (not book replay); bounded MBO sample validates an MBP-10-derived model applied at scale; fill assumption SWEPT (pessimistic/central/optimistic; every (config × fill-assumption) pair a registered trial; claims must survive the whole range incl. the pessimistic endpoint); staged A→D gates, first spend at stage B (named operator authorization; three recordable states authorized/declined/undecided); Decision 10 promotion-vs-successor rule (unchanged estimand = same-HID promotion via append-only execution-tier addendum; changed estimand = successor HID under ADR-0008 D5 — OD-G Form B is the successor-HID case). Accepted 2026-07-19 by principal direction, stage A only — authorizes no spend, builds nothing |

Open follow-ups registered at founding: `P1-2.0-RETRO-CARD-1.0-REGISTER`
(retro-card H050/H052a/H053/H054/H055 from 1.0 KPI reports — first admission
candidates); dwell-time feasibility study per ADR-0004 Decision 6 is the
first registered analysis and go/no-go for the allocator program.
(`P1-2.0-CITE-DOI-VERIFY-PBO-2017` closed 2026-07-10: Crossref verified
10.21314/JCF.2016.322 → Bailey, Borwein, López de Prado & Zhu, J. Comput.
Finance 20(4):39-69, during the round-1 audit.)

The `P1-2.0-RETRO-CARD-1.0-REGISTER` register is drafted at
[docs/research_notes/retro_card_register_2026-07-10.md](docs/research_notes/retro_card_register_2026-07-10.md).
The dwell-time feasibility go/no-go is **CLOSED GO** (H900,
[docs/reports/H900/H900_dwell_feasibility_report_2026-07-11.md](docs/reports/H900/H900_dwell_feasibility_report_2026-07-11.md)),
opening the allocator program. Open follow-ups registered this session
(2026-07-12):

- `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` (BLOCKING per ADR-0013) —
  **METHOD FROZEN 2026-07-12; NUMERIC INSTANTIATED 2026-07-17** (on-ledger,
  RECORD only): interior-maximum / grid-bracketing / ruin-handling derivation +
  reference estimator [src/skie_universe2/inference/kelly_growth.py](src/skie_universe2/inference/kelly_growth.py)
  + 30 tests + memo [docs/methodology/kelly_growth_concavity_ruin_2026-07-12.md](docs/methodology/kelly_growth_concavity_ruin_2026-07-12.md)
  (3-round audit accept; numeric addendum §B). On-ledger numbers (per-session
  `orb_first_hour_k1.0` streams): concavity exhibited (in-sample peak exactly
  f=1.0, g''<0 all grid points), P(ruin)=0 at every grid point (CIs [0,0]),
  f_0 = 1.978–1.990 (thin-tail benchmark 2.0; grid top 1.25 inside the
  positive-growth region in sample), ES/net DEGENERATE (no favourable bet),
  OOS f** edge-pinned with growth CIs including zero everywhere →
  **grid-bracketing verdict: inconclusive-on-null-ledger**, re-instantiation at
  the first admission a registered standing condition. NO Kelly fraction
  selected (Phase-4 champion action; additionally blocked on arsenal ≥ 1).
- `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` (BLOCKING per ADR-0013) —
  **METHOD FROZEN 2026-07-12; NUMERIC INSTANTIATED 2026-07-17** (round-1
  audit-remediated): error-rate-cost decision-theoretic derivation + reference
  estimator [src/skie_universe2/inference/discovery_alpha.py](src/skie_universe2/inference/discovery_alpha.py)
  + 28 tests + memo [docs/methodology/discovery_alpha_cost_calibration_2026-07-12.md](docs/methodology/discovery_alpha_cost_calibration_2026-07-12.md)
  (2-round audit accept; numeric addendum §A). ENACTED:
  `screening_error_rate_target` = 0.7401 (RD4 MPRR posterior-null cutoff t*,
  median of the 24-point enactment band over instrument × mu-anchor × H_dem
  {1,2,4} windows × r_backstop {0, 0.3332}; band [0.5096, 0.8867]; bootstrap
  95% CI [0.4239, 1.0000]; full precision in
  [config/multipletest_family.yaml](config/multipletest_family.yaml), which
  governs); criterion **retain-fwer** at every registered family size
  (Romano-Wolf stays; no BH; `prds_argument_ref` null). ADR-0014 (S-d) bounds
  resolve: DSR ≥ 0.2599, PBO ≤ 0.7401 — enacted as PROVISIONAL OPERATIONAL
  PROXIES of the posterior-null budget (documented scale-transfer deviation,
  addendum §A.6.2), with §A.8 standing re-instantiation conditions (first
  admission; live-outcome r_backstop; per-family RD5 re-decision).
- `P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE` (BLOCKING per ADR-0012): error-rate-cost
  calibration of the geometric-growth dethroning margin (ADR-0012 Decision 3) and
  the champion-dwell floor (Decision 5). ADR-0012 is accepted, but the dethroning
  rule is non-operational until this memo is frozen with its ReproLog emitted —
  until then no champion dethroning is certifiable.
- `P1-2.0-H900-BOCPD-WHITENED` (**METHOD FROZEN 2026-07-14; ON-LEDGER NUMERIC
  2026-07-17**): the AR(1)-prewhitening primitive
  [src/skie_universe2/inference/whitening.py](src/skie_universe2/inference/whitening.py)
  + 13 tests + memo
  [docs/methodology/whitening_ar_robust_bocpd_2026-07-13.md](docs/methodology/whitening_ar_robust_bocpd_2026-07-13.md)
  are frozen; the DEFERRED reproducible on-ledger prewhitened ROC re-run is now
  EXECUTED ([scripts/run_h900_whitened_roc.py](scripts/run_h900_whitened_roc.py),
  hazard sweep on the archived filtered sequences, per-transition TP vs
  stable-run label-flip FP, KM latency). Verdict: **net detection ≤ 0 at every
  operating point on both instruments** — the latent-state unsupervised
  detection latency is **UNATTAINABLE** (no accurate operating point at any
  latency), the strongest form of the H900 supervised-detection dependence.
  The documented prior probe's net≈26pp @ L≈45 is NOT reproduced (at L≈45 the
  measured net is ≈ −13pp ES / −7pp NQ) and is SUPERSEDED by this reproducible
  record; the qualitative NO-GO is reproduced and strengthened. ADR-0014 (S-e)
  consumes the verdict per the amended screen rule: latent-state cells fail
  S-e outright; rule-based causal covariate cells carry their structural
  observation lag. The interim filtered-sequence substrate is now SHA-256-bound
  in the run ReproLog (provenance repair).
- Carried: `P1-2.0-RETRO-CARD-1.0-REGISTER` (open; **ADR-0013 re-adjudication
  addendum added 2026-07-14** — metric currency reconciled to geometric growth,
  lower-tail quantile demoted to guardrail, Kelly sweep + cost-tuned discovery
  applied; numeric re-adjudication deferred to the shadow-ledger backfill);
  `P1-2.0-DATABENTO-DEC-ROLL-REPULL` (operator-only vendor spend; **elevated
  2026-07-19** to quote-ready top purchase priority — DR-1/DR-2 spec in
  [databento_pull_spec_cost_sheet_2026-07-18.md](docs/research_notes/databento_pull_spec_cost_sheet_2026-07-18.md));
  `P1-2.0-ROLL-SYMBOL-EXPAND` and the QUANT-3-2 terminal-window generalization
  (post shadow-ledger backfill).

Open follow-up registered 2026-07-17 (on ADR-0014 acceptance):

- `P1-2.0-POOL-PRIORITY-CALIBRATE` (**standing, monitored; non-blocking** — pool
  ordering is a queue, not a certification gate): the pool-priority ranking
  weights (ADR-0014 Decision 6) are the OUTPUT of a supervised calibration on the
  project's own accruing verdict history, revisited each monitoring checkpoint
  with CIs — never a literature constant. A structural coverage-novelty-first
  cold-start rule governs until it has verdict outcomes.

## Reproducibility contract

Every artifact-producing run in this project emits a 13-field ReproLog at
`logs/reproducibility/repro_log_{run_id}.json` per the
[emit-repro-log](https://github.com/s-koirala/dotfiles/tree/main/claude/skills/emit-repro-log)
skill. All commits use
[/commit-with-provenance](https://github.com/s-koirala/dotfiles/tree/main/claude/commands/commit-with-provenance.md)
with `--role={idea|code|prose|audit|multi}` per ICMJE 2026 disclosure.

Dataset provenance: `data/_manifest.json` (managed by
`scripts/build_data_manifest.py`, vendored from
`~/.claude/scripts/build_data_manifest.py` in s-koirala/dotfiles). Run
`--check` mode in CI to detect drift.

## Quickstart

```bash
uv venv && uv sync --all-extras   # --all-extras: runtime libs live under the data/models extras (REPRODUCIBILITY-1-1)
uv run pre-commit install
uv run pytest
```

## Project state

- **Kind:** quant
- **Bootstrap date:** 2026-07-10
- **Python version pin:** `>=3.11,<3.13`
- **Bootstrap script HEAD:** `fe9bcd1b6fee` (see `manifest.json`)

Progress (as of 2026-07-19):

- **Dwell-time feasibility gate (ADR-0004 Decision 6) — CLOSED GO.** H900
  established dwell-time separation feasible; first registered analysis, opens
  the allocator program.
  [docs/reports/H900/H900_dwell_feasibility_report_2026-07-11.md](docs/reports/H900/H900_dwell_feasibility_report_2026-07-11.md).
- **H900 BOCPD detection-latency sensitivity — CLOSED.** CUSUM verdict GO
  reproduced bit-identically via
  [scripts/audits/check_h900_bocpd_reproduction.py](scripts/audits/check_h900_bocpd_reproduction.py)
  against the Adams-MacKay 2007 port
  [src/skie_universe2/inference/bocpd.py](src/skie_universe2/inference/bocpd.py);
  unsupervised BOCPD is NO-GO both variants (L_detect ≫ dwell), so the H900 GO
  is **supervised-detection-dependent** (robust to AR-whitening on the frozen +
  documented-prior evidence, reproducible on-ledger re-run deferred — see the
  `P1-2.0-H900-BOCPD-WHITENED` method-freeze below).
  [docs/reports/H900/H900_bocpd_sensitivity_2026-07-11.md](docs/reports/H900/H900_bocpd_sensitivity_2026-07-11.md).
- **Conditioning set registered.** Winning 4-state diagonal-Gaussian HMM (on
  standardized `ret_5m`, log `rvol_5m_24h`) registered as the ADR-0002
  candidate conditioning covariate (ADR-0001-D5 covariate-not-gate);
  dwell/detection-latency registered as standing ADR-0004 report objects.
  [config/conditioning_covariates.yaml](config/conditioning_covariates.yaml),
  [docs/methodology/allocator_metric_family_report_objects.md](docs/methodology/allocator_metric_family_report_objects.md).
- **Governance reframe (ADR-0012/0013) — STATUS: accepted (enacted 2026-07-12).**
  Geometric-growth mandate + champion-challenger + 18-row amendment map now
  in-force; ADR-0012/0013 status `accepted`, the five amended-ADR banners flipped
  to `accepted`, and the amendment map is the authoritative record (decision
  bodies not rewritten in place). Two BLOCKING Kelly follow-ups still gate any
  growth-based fraction selection, and a third (`P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE`)
  gates champion dethroning (see Open follow-ups above).
- **Kelly calibration memos — METHOD FROZEN (2026-07-12).** Both BLOCKING
  Decision-9 memos are method-frozen: reference estimators
  [kelly_growth.py](src/skie_universe2/inference/kelly_growth.py) (concavity /
  interior-max / ruin; 30 tests) and
  [discovery_alpha.py](src/skie_universe2/inference/discovery_alpha.py)
  (decision-theoretic loss / threshold / FWER-vs-FDR; 28 tests), each with a
  methodology memo under [docs/methodology/](docs/methodology/) and audit-remediate
  accept. The derivations + estimators + tests are pre-registered on representative
  fat-tailed substrate; the NUMERIC on-ledger operating points (f*, P(ruin), f_0,
  alpha level, pi1, criterion) are DEFERRED to the step-4 shadow-ledger backfill —
  no Kelly fraction is selected and no discovery target is enacted until then.
- **H900 BOCPD whitening — METHOD FROZEN (2026-07-14).** `P1-2.0-H900-BOCPD-WHITENED`
  finalized from PARKED (2-round audit-remediate accept): AR(1)-prewhitening
  primitive [whitening.py](src/skie_universe2/inference/whitening.py) + 13 tests +
  memo [whitening_ar_robust_bocpd_2026-07-13.md](docs/methodology/whitening_ar_robust_bocpd_2026-07-13.md).
  Whitening removes the by-construction autocorrelation and keeps real shifts
  detectable but does not control false alarms at the Bayes operating point; the
  NO-GO robustness rests on the prior on-ledger ROC probe, with a reproducible
  on-ledger re-run DEFERRED. Same session: the 2026-07-13 handoff-review findings
  were reconciled (Findings 4 & 6 refuted-in-container, 1–3/5 actioned), an
  identity-hygiene leak fixed, and the retro-card register given an ADR-0013
  metric-currency addendum.
- **H001 — EXECUTED, disposition `archive(null)` (2026-07-16).** First forward
  core hypothesis: the exploration-tier SMA(3)/StdDev(3) "meta-shift" prototype was
  reframed from a directional scalping strategy into an ADR-0001-D5 conditioning
  covariate and tested for ADR-0002(d) non-redundancy vs the H900 HMM covariate +
  variance-ratio state on forward reversion/continuation. Design frozen (SHA
  `6c875b789898…`, 3-round audit accept); pure covariate emitter + estimator
  library ([covariate_information.py](src/skie_universe2/inference/covariate_information.py),
  [variance_ratio_state.py](src/skie_universe2/features/variance_ratio_state.py),
  [regime_covariate.py](src/skie_universe2/signals/regime_covariate.py)) + harness
  ([run_h001_covariate_study.py](scripts/run_h001_covariate_study.py)) 2-round audit
  accept; primary ES+NQ × 400 arms × 15 windows run (Miller-Madow CMI + nested OOS
  predictive delta, rolling-origin, horizon-aware purge). **Null:** the small-n
  vol×trend label carries only a tiny in-sample MM-CMI (~1e-4 nats, a large-N
  residual) that FAILS the out-of-sample predictive guard — OOS delta negative for
  82% of arm-horizons and ALL of NQ (0/800 H1); ES H1 283/800 but marginal and not
  instrument-robust. NOT promoted to the ADR-0002(b) registry. Report:
  [reports/H001/H001_covariate_information_report_2026-07-16.md](reports/H001/H001_covariate_information_report_2026-07-16.md).
  The prototype's premise (SMA/StdDev vol×trend adds edge-relevant info) does not
  survive rigorous OOS multi-instrument testing against the registered regime
  covariates.
- **Shadow ledger populated + first arsenal-admission machinery (2026-07-16).** The
  canonical append-only shadow ledger (ADR-0003) is populated with the first
  forward expert: `OrbFirstHourExpert` (first-hour opening-range breakout,
  [orb_first_hour.py](src/skie_universe2/experts/orb_first_hour.py)) backfilled over
  ES+NQ × 4 Kelly fractions (5.2M rows) via
  [run_shadow_ledger_backfill.py](scripts/run_shadow_ledger_backfill.py) through the
  Expert-contract / Tier-0 exact-levered-return execution stack
  ([tier0_barclose.py](src/skie_universe2/execution/tier0_barclose.py), ruin
  representable). The confirmation-ladder estimators are built and tested:
  Romano-Wolf StepM ([romano_wolf.py](src/skie_universe2/inference/romano_wolf.py)),
  Deflated Sharpe ([deflated_sharpe.py](src/skie_universe2/inference/deflated_sharpe.py)),
  PBO/CSCV ([pbo.py](src/skie_universe2/inference/pbo.py)), matched-turnover rotor
  ([matched_turnover_rotor.py](src/skie_universe2/inference/matched_turnover_rotor.py)),
  and Ledoit-Wolf 2008 studentized-bootstrap Sharpe-difference
  ([ledoit_wolf_sharpe.py](src/skie_universe2/inference/ledoit_wolf_sharpe.py)). The
  registered Kelly grid was extracted to
  [policy/kelly_sweep.py](src/skie_universe2/policy/kelly_sweep.py) (governance
  constant, decoupled from the demoted meta_shift prototype; closes a HEAD-unbuildable
  repro gap). `statsmodels` declared for the KPSS §8(a) test.
- **H101 (unconditional first-hour ORB) — FROZEN + EXECUTED, `provisional-archive-null`
  (2026-07-16).** 2.0 re-spec of 1.0 H052a; design frozen (SHA `a7c5c9178f66`, 2-round
  audit). Admission scan RC-H101-1 (ADR-0002(c), primary cell = high-realized-vol,
  Lundström prior) on the backfilled ledger: **no admission-grade conditional gross
  edge** — every Romano-Wolf-adjusted p ≥ 0.17, the primary cell does not beat its
  matched-turnover rotor, DSR < 0.5 both instruments, KPSS confirms stationarity; PBO
  and the screening level DEFERRED (nothing certified). 2-round audit accept (caught a
  Romano-Wolf step-down placeholder-p bug, a rotor/cell misalignment, a skipped KPSS,
  IID-vs-HAC Sharpe SE, and a wrong DSR trial count — all fixed).
  [RC-H101-1 disposition](docs/reports/H101/RC-H101-1_admission_disposition_2026-07-16.md).
- **H103 (stress-state anti-gate ORB, ES+NQ) — FROZEN + EXECUTED,
  `provisional-archive-null` (2026-07-16).** 2.0 anti-gate re-spec of 1.0 H054;
  instrument scope ES+NQ (operator decision); design frozen (SHA `84d01a6b4ad0`,
  3-round audit — resolved a critical ES→ES+NQ estimator gap, a forking-paths
  multiplicity issue vs RC-H101-1, and an unbuilt joint-panel-FWER claim re-specified to
  per-instrument Romano-Wolf + a Šidák cross-instrument union). Admission scan RC-H103-1
  on the SHARED H101 ledger: stress cell = top-p̂ realized-vol band (p̂ = H900 HMM
  stationary stress occupancy, ES 0.190 / NQ 0.214). **No admission-grade stress edge**
  (ES Sharpe −0.040, NQ +0.029, every RW-adj p ≥ 0.42); BOTH cells FAIL the §8 25%
  precision gate (means indistinguishable from zero); the Ledoit-Wolf anti-gate
  differential (stress vs calm) is non-significant. RC-XCORR-1 (net-of-cost, Grinold
  residual IR): redundancy **instrument-specific** — ES redundant (residual IR −0.018;
  ES ORB net-negative after costs), NQ zero-marginal (residual IR ≈0). The **Lundström
  high-vol-concentration prior is CONTRADICTED** (ES ORB edge is in CALM sessions)
  *(superseded 2026-07-18: that reading was rendered on the RC-1 LEAKED full-sample
  stress construction; the certified leakage-clean RC-2 re-measurement flips the ES
  stress mean positive on 28% less data — standing status **UNRESOLVED**, correction
  of record [expert_card_v3](research/01_hypothesis_register/H103/expert_card_v3.md))*.
  2-round audit accept. [RC-H103-1 disposition](docs/reports/H103/RC-H103-1_admission_disposition_2026-07-16.md).
- **Arsenal status: EMPTY; provisional POOL populated (2026-07-17).** The RC-1
  singleton scans returned nulls under the then-null screening level; under the
  ADR-0014 screen re-runs at the ENACTED level (RC-H101-2 / RC-H103-2, below)
  BOTH candidates carry persistent, ex-ante-selectable windows and sit in the
  provisional candidate pool as `pool-hold-reconsider` (VERDICT deferred at
  |arsenal| = 0). No ADR-0002(b) member is admitted, no covariance anchor is
  authored, nothing is certified; Kelly-fraction selection remains blocked.
- **Admission re-composed — ADR-0014 provisional candidate pool (accepted +
  enacted 2026-07-17).** [ADR-0014](docs/decisions/ADR-0014-provisional-candidate-pool-screen-verdict.md)
  splits ADR-0002 admission into a singleton SCREEN (persistent,
  ex-ante-selectable competence window → provisional pool) and a set-level VERDICT
  (marginal geometric-growth on the ADR-0007 ladder); screen-pass/verdict-non-select
  experts are `pool-hold-reconsider` (reconsideration-eligible, re-adjudicated on
  incumbent-set change), resolving the empty-arsenal cold-start and making the
  H101/H103 nulls held, not terminal. Pool-ledger schema
  [config/pool_ledger_schema.yaml](config/pool_ledger_schema.yaml) — ranking
  weights an OUTPUT of the standing-monitored `P1-2.0-POOL-PRIORITY-CALIBRATE`,
  path-maxima barred from ranking; the S-e latency input, BLOCKED at acceptance,
  was QUANTIFIED 2026-07-17 by the `P1-2.0-H900-BOCPD-WHITENED` on-ledger run
  (latent-state latency UNATTAINABLE; rule-based causal cells carry their
  structural observation lag — amended screen rule).
  Amendment map enacted (banners + `amended_by` on ADR-0002/0004/0007/0009;
  decision bodies not rewritten in place). 2-round audit-remediate accept
  ([audit trail](docs/audits/audit_trail_2026-07-17_adr0014-pool-ledger.md), incl. a
  self-caught YAML parse fix). Forward planning consolidated into
  [program_roadmap_2026-07-17.md](docs/research_notes/program_roadmap_2026-07-17.md)
  (Phase 0–5) + [backfill_admission_plan_2026-07-17.md](docs/research_notes/backfill_admission_plan_2026-07-17.md);
  the two superseded 2026-07-16 scoped notes archived under
  `docs/research_notes/archive/`.
- **Phase 1 — the three BLOCKING numeric calibrations INSTANTIATED (2026-07-17).**
  All three Decision-9/S-e gates moved from numeric-deferred to on-ledger
  numbers (audit-remediate round 1 applied; see the follow-up bullets above for
  the values): discovery-alpha level ENACTED (`screening_error_rate_target` =
  0.7401, retain-fwer, S-d bounds DSR ≥ 0.2599 / PBO ≤ 0.7401 as provisional
  operational proxies), Kelly concavity/ruin RECORDED
  (inconclusive-on-null-ledger bracketing verdict; ES/net degenerate; no
  fraction selected), and the H900 whitened on-ledger ROC EXECUTED
  reproducibly (latent-state unsupervised latency UNATTAINABLE; prior probe
  superseded; S-e amended rule enacted in the screen addenda). Standing
  re-instantiation conditions registered (first admission; live-outcome
  backstop; per-family RD5 re-decision). Certification machinery is now
  EXECUTABLE; nothing is certified.
- **Phase 2 — first SCREEN pass executed; empty-arsenal cold-start resolved as
  POOL entries (2026-07-17).** The frozen RC-H101-2 / RC-H103-2 protocols ran
  on the canonical k1.0 ledger at the enacted level ([harness](scripts/run_screen_h101_h103.py);
  S-c reproduces the RC-1 statistics bit-identically at seed 20260716):
  **both SCREEN PASS.** H101: 3 passing cells (ES/first_hour_up DSR 0.346;
  NQ/high_vol 0.280; NQ/first_hour_up 0.573; PBO 0.216–0.493). H103 (with the
  CERTIFIED leakage-clean per-origin stress construction, p̂ ≈ 0.18, 15
  windows/instrument): 4 passing cells (ES/stress 0.304 — the clean ES stress
  mean flips POSITIVE vs the RC-1 leaked cell, a recorded
  construction-dependence exhibit; ES/first_hour_up 0.330; NQ/non_stress
  0.571; NQ/first_hour_up 0.555; NQ/stress misses S-d by 0.004). Both dispose
  `pool-hold-reconsider`; Expert Cards v2 emitted (script-generated), the
  pool ledger materialized ([pool_ledger.jsonl](data/processed/pool_ledger/pool_ledger.jsonl),
  8 records = 2 HIDs × 4 fractions), and per-cell trial records appended to
  the `rc-*-2` register families. **STOPPED before any set-level VERDICT**
  (|arsenal| = 0; the verdict is now under the ratified operator HOLD — see the
  2026-07-18 bullet below).
  2-round audit-remediate accept (trail: [audit_trail_2026-07-17_phase1-numeric-calibrations.md](docs/audits/audit_trail_2026-07-17_phase1-numeric-calibrations.md)).
- **Pool HOLD ratified; reproduction gate closed; H103 stress record corrected;
  roadmap re-ordered to forward sourcing (2026-07-18).** Four-part
  consolidation session (each deliverable audit-remediate accepted):
  (1) [ADR-0015](docs/decisions/ADR-0015-ratified-pool-hold-verdict-precondition.md)
  **accepted 2026-07-18** (drafted `proposed`, accepted by principal direction
  the same day; not self-accepted), recording the
  operator-ratified HOLD of the set-level VERDICT — grounds: effective pool
  set size ~1 (all 8 records share one `expert_hash`), multiplicity/burned-data
  cost for zero information, and the sole rotor comparison on record already
  failed; an operator-directed, provisional `verdict_precondition` (≥ 2
  distinct expert hashes with non-overlapping coverage vectors;
  reporting-check-only) added to the pool-ledger schema with checker
  [check_verdict_precondition.py](scripts/audits/check_verdict_precondition.py)
  — **BLOCKED: `distinct_expert_hash_count = 1`** (10 tests).
  (2) The enacted discovery-alpha level is under an executable reproduction
  gate: [check_discovery_alpha_reproduction.py](scripts/audits/check_discovery_alpha_reproduction.py)
  re-ran the frozen generator — **REPRODUCED exactly** (frozen == fresh ==
  0.7400550140326007, 0 field mismatches over the whole artifact, exit 0) —
  plus 14 enactment-coupling tests (MPRR identity, members-only band median,
  seed-reproducible bootstrap, full-precision config coupling, computed S-d
  bounds) and 2 checker exit-code-contract tests; memo §A.9. (3) H103 ES stress standing statement corrected to
  **UNRESOLVED** (construction-dependent sign flip: leaked −5.09e-04/n=437 vs
  leakage-clean +1.03e-04/n=313, neither distinguishable from zero) via
  append-only [expert_card_v3](research/01_hypothesis_register/H103/expert_card_v3.md);
  Lundström prior UNRESOLVED in the retro register; covariate
  `construction_dependence_note` registered. (4) Roadmap/plan re-ordered:
  Phases 1–2 COMPLETE (verdict = ratified HOLD), **Phase-3 disjoint-window
  forward sourcing is THE GATING item** (retro queue demoted — ORB-adjacent,
  cannot supply a non-overlapping coverage vector); OD-A resolved (first
  admission target = fresh forward expert), OD-G opened (spread/liquidity
  ADR-0006 tier reportability). Arsenal EMPTY; nothing certified; no Kelly
  fraction selected; STOPPED before Step-5 mechanism work for operator review.
- **OD-G adjudicated; ADR-0016 ACCEPTED (stage A); forward-sourcing priority
  fixed; DEC-roll repair elevated (2026-07-19).** The three OD-G deliverables
  (proposed ADR-0016, OD-G setup plan, Databento pull-spec/cost sheet) passed
  a 15-agent argument-validity audit — 12 majors confirmed and remediated in
  place, 1 critical REFUTED at the adversarial gate (the alleged ADR-0006
  live-fill contradiction dissolves as a build-gate vs confirmation-grade
  distinction), 7 minors logged/fixed
  ([audit trail](docs/audits/audit_trail_2026-07-19_odg-deliverables-argument-audit.md)).
  By principal direction 2026-07-19:
  **[ADR-0016](docs/decisions/ADR-0016-tier2-execution-fidelity-scoping.md)
  accepted** (stage A only — NO spend authorized; new Decision 10 resolves
  promotion-vs-successor: OD-G Form B = successor HID); **OD-G Form A
  DEFERRED** out of Step-5 (weakest disjointness, proxy fork, its spans are
  Form B's); **forward-sourcing priority: (1) overnight/Globex,
  (2) mean-reversion**, macro third, OD-G last; **DR-1/DR-2 December-roll
  repair elevated to quote-ready top purchase priority** (operator-only
  spend, not yet authorized; prerequisite for December-inclusive /
  confirmation-grade overnight evidence — a conditional-grade overnight
  screen can run now on the exclusion-filtered substrate with the blind spot
  declared). ADR-0015 HOLD unchanged; arsenal EMPTY; nothing certified; no
  Kelly fraction selected. Next: overnight/Globex ETH-substrate check →
  `/hypothesis-new` → `/preregister` → backfill → screen.
- **Phase 3 forward batch EXECUTED — pool at 3 distinct hashes; ADR-0015
  precondition MET (label-based, reporting-only); M1 exposes a label/realized
  inversion (2026-07-19, roadmap-execution session).** (1) **P3-A GO**: the
  roll-adjusted store carries full Globex ETH (186 five-min overnight
  bars/session at the median both instruments); December/Globex blind spot
  quantified (91 ES / 101 NQ sessions, 3.32%/3.66%; 69.0%/67.8% of excluded
  bars are overnight-ETH; processed substrate ends 2025-12-03 ES /
  2025-12-05 NQ) — [feasibility record](docs/research_notes/overnight_globex_substrate_feasibility_2026-07-19.md),
  2-round audit accept; session-segment classifier single-sourced in
  [utils/sessions.py](src/skie_universe2/utils/sessions.py). (2) **H105
  (overnight session drift; Boyarchenko-Larsen-Whelan 2023 RFS + the 2026
  attenuation expectation pre-registered) and H106 (VR range-state reversal;
  Lo-MacKinlay 1988/1990, single-instrument own-autocovariance channel)
  frozen** (SHAs `64753d968289…`, `cb18e545ddb2…`) after a 3-round
  audit-remediate ACCEPT ([trail](docs/audits/audit_trail_2026-07-19_h105-h106-preregistration.md))
  that forced the packaged screen spine
  ([screening/screen_spine.py](src/skie_universe2/screening/screen_spine.py)),
  the CERTIFIED per-origin vol-cell construction (full-sample terciles
  convicted again), matched DSR count/dispersion surfaces, in-spine §8
  exhibits, and a restored frozen HAC bandwidth cap (refuter-reproduced
  crash). (3) Both backfilled (5.196M rows × 2 experts, canaries PASS) and
  **both SCREEN PASS at the enacted level**: RC-H105-1 six cells (ES+NQ
  high/low-vol, prior-RTH-up; the unconditional overnight drift is present
  gross, p=0.037/0.010, but fails the S-d DSR bound — the persistent
  windows are conditional), RC-H106-1 four ES cells (ES:low_vol DSR 1.000,
  PBO 0.047; range-state gross ≈ 2.2× trend-state per the mechanism prior;
  ALL NQ cells fail S-d). v1 Expert Cards script-generated; pool now **16
  records / 4 HIDs / 3 distinct `expert_hash`**; `rc-h105-1`/`rc-h106-1`
  trial families +20 records; burned ledger +60 scripted window-spans.
  (4) **Verdict precondition MET (exit 0, reporting-only)** via the
  label-disjoint (ORB, H106) pair — but the
  [M1 report](reports/M1_overlap/m1_realized_overlap.json) INVERTS it:
  ORB↔H105 realized-bar Jaccard = **0.0 exactly** (the frozen §12(c)
  identity confirmed) yet label-BLOCKED by the `NQ:high_vol` name
  collision, while ORB↔H106 shares 8.9% of realized bars. Operator brief:
  [verdict_readiness_memo_2026-07-19.md](docs/research_notes/verdict_readiness_memo_2026-07-19.md)
  (cold-start queue H106 > H105 > H101 > H103 with H106's
  net-not-monetizable caveat; **DR-1/DR-2 now BINDING for
  confirmation-grade adjudication of H105**). ADR-0015 HOLD in force —
  STOPPED at the operator gate: the `lift_action` + first-admission VERDICT
  authorization are named, dated operator actions; nothing certified, no
  Kelly fraction selected, arsenal EMPTY.

## Directory layout

See `manifest.json` for the canonical subdir list. Key conventions:

- `data/{raw,interim,processed,external}/` — read-only raw → analysis-ready
  pipeline; per-file SHA in `data/_manifest.json`.
- `docs/{audits,decisions,literature,methodology,reports,research_notes,templates}/`
  — durable documentation.
- `artifacts/{models,runs}/` — versioned binary outputs.
- `logs/reproducibility/` — ReproLog records + pip-freeze archive.
- `research/`, `reports/` — work-in-progress and final reports.
- `runs/` — top-level run outputs (SKIE-Universe convention; coexists with
  `artifacts/runs/`).

## Identity hygiene

This project's local git config sets `user.email` per the bootstrap. Real-name
identifiers must never appear in committed files unless explicitly intended.
