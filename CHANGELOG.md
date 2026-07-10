# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
