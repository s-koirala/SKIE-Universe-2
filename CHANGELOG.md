# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed (aggressive geometric-growth mandate — PROPOSED, pending enactment, 2026-07-12)
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
  every round. **All governance is PROPOSED — no amendment is enacted until the
  principal moves ADR-0012/0013 proposed → accepted and applies the amendment
  map in place.**

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
