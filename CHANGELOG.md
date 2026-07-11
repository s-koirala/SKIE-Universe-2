# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
