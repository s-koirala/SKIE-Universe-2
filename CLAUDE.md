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
(allocator-config × Kelly-fraction) space, never hand-tuned — but no fraction is
selected on geometric growth until the BLOCKING `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`
memo is frozen (interior maximum / grid bracketing / ruin handling on the
shadow-ledger fat-tailed distribution). The lower-tail
terminal-wealth quantile is **demoted to a monitored, non-binding guardrail**
(still computed at the same bootstrap/block length and reported, but it informs
rather than vetoes). Discovery alpha (SPA / StepM FWER, or FDR where the cost
analysis supports it) is **cost-tuned looser** via the registered
error-rate-cost follow-up `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`
(missed compounding weighted above false discovery; the level is the analysis
output, not a constant). ADR-0002 admission is loosened toward aggressive
inclusion (conditional-edge + non-redundancy structure kept; non-redundancy
re-expressed on marginal log-wealth growth); the ADR-0010 live-capital ramp is
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

The ten founding ADRs in [docs/decisions/](docs/decisions/) are standing rules:

| ADR | Mandate |
|---|---|
| [ADR-0001](docs/decisions/ADR-0001-allocator-unit-of-inference.md) | Allocator is the unit of inference; strategy-level deployment gates abolished |
| [ADR-0002](docs/decisions/ADR-0002-arsenal-admission-standard.md) | Arsenal admission: conditional gross edge + non-redundancy; no standalone burden |
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
  **METHOD FROZEN 2026-07-12**: interior-maximum / grid-bracketing / ruin-handling
  derivation + reference estimator [src/skie_universe2/inference/kelly_growth.py](src/skie_universe2/inference/kelly_growth.py)
  + 30 tests + memo [docs/methodology/kelly_growth_concavity_ruin_2026-07-12.md](docs/methodology/kelly_growth_concavity_ruin_2026-07-12.md)
  (3-round audit accept). NUMERIC on-ledger instantiation (f*, grid-bracketing
  verdict, P(ruin), f_0) DEFERRED to the step-4 backfill; no Kelly fraction is
  selected until then.
- `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` (BLOCKING per ADR-0013) —
  **METHOD FROZEN 2026-07-12**: error-rate-cost decision-theoretic derivation +
  reference estimator [src/skie_universe2/inference/discovery_alpha.py](src/skie_universe2/inference/discovery_alpha.py)
  + 28 tests + memo [docs/methodology/discovery_alpha_cost_calibration_2026-07-12.md](docs/methodology/discovery_alpha_cost_calibration_2026-07-12.md)
  (2-round audit accept). NUMERIC alpha level / pi1 / lambda / FWER-vs-FDR criterion
  DEFERRED to the step-4 backfill; no target enacted and config left with OUTPUT
  placeholders until then.
- `P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE` (BLOCKING per ADR-0012): error-rate-cost
  calibration of the geometric-growth dethroning margin (ADR-0012 Decision 3) and
  the champion-dwell floor (Decision 5). ADR-0012 is accepted, but the dethroning
  rule is non-operational until this memo is frozen with its ReproLog emitted —
  until then no champion dethroning is certifiable.
- `P1-2.0-H900-BOCPD-WHITENED` (**METHOD FROZEN 2026-07-14**, finalized from
  PARKED; 2-round audit-remediate accept): the AR(1)-prewhitening primitive
  [src/skie_universe2/inference/whitening.py](src/skie_universe2/inference/whitening.py)
  + 13 tests + memo
  [docs/methodology/whitening_ar_robust_bocpd_2026-07-13.md](docs/methodology/whitening_ar_robust_bocpd_2026-07-13.md)
  are frozen. Prewhitening the near-unit-root (ρ≈0.997) log-rvol removes the
  by-construction autocorrelation and keeps real shifts detectable, but does NOT
  control false alarms at the Bayes operating point (~0.43). The ROC-wide "no
  accurate-and-timely operating point" NO-GO rests on the PRIOR on-ledger ROC
  probe (net≈26pp @ L_detect≈45; ~4 bars→noise, session_handoff §2), which is
  documented but NOT reproducibly preserved; a reproducible on-ledger prewhitened
  ROC re-run is DEFERRED to the shadow-ledger backfill. So the H900
  supervised-detection-dependence is robust on the frozen synthetic +
  documented-prior evidence, on-ledger confirmation deferred.
- Carried: `P1-2.0-RETRO-CARD-1.0-REGISTER` (open; **ADR-0013 re-adjudication
  addendum added 2026-07-14** — metric currency reconciled to geometric growth,
  lower-tail quantile demoted to guardrail, Kelly sweep + cost-tuned discovery
  applied; numeric re-adjudication deferred to the shadow-ledger backfill);
  `P1-2.0-DATABENTO-DEC-ROLL-REPULL` (operator-only vendor spend);
  `P1-2.0-ROLL-SYMBOL-EXPAND` and the QUANT-3-2 terminal-window generalization
  (post shadow-ledger backfill).

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

Progress (as of 2026-07-12):

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
