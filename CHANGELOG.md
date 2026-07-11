# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
