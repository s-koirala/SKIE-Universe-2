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

## Founding governance (binding; read before any research work)

The ten founding ADRs in [docs/decisions/](docs/decisions/) are standing rules:

| ADR | Mandate |
|---|---|
| [ADR-0001](docs/decisions/ADR-0001-allocator-unit-of-inference.md) | Allocator is the unit of inference; strategy-level deployment gates abolished |
| [ADR-0002](docs/decisions/ADR-0002-arsenal-admission-standard.md) | Arsenal admission: conditional gross edge + non-redundancy; no standalone burden |
| [ADR-0003](docs/decisions/ADR-0003-shadow-ledger-canonical-object.md) | Shadow ledger (every expert × asset × bar, counterfactual, append-only) is the sole evidence source |
| [ADR-0004](docs/decisions/ADR-0004-rolling-evaluation-regime.md) | Rolling-origin evaluation only; metric family incl. regret vs switching oracle; dwell-time feasibility gate first |
| [ADR-0005](docs/decisions/ADR-0005-three-layer-separation.md) | Signal / position-policy / execution layer separation; fractional Kelly with registered lower-tail-quantile binding; no cross-layer tuning |
| [ADR-0006](docs/decisions/ADR-0006-execution-fidelity-tiers.md) | Execution tiers 0/1/2; scalping/limit-order claims unreportable below Tier 2 |
| [ADR-0007](docs/decisions/ADR-0007-two-tier-discovery-pipeline.md) | Exploration tier (cheap, labeled) + confirmation ladder incl. non-waivable matched-turnover random rotor |
| [ADR-0008](docs/decisions/ADR-0008-integrity-non-negotiables.md) | PIT canaries, bar-level costs, ReproLog, pre-registered scans, burned-data ledger, trial register — every tier |
| [ADR-0009](docs/decisions/ADR-0009-expert-card-terminal-deliverable.md) | Expert Card (8 sections) is the mandatory terminal deliverable; "fail" is not a disposition |
| [ADR-0010](docs/decisions/ADR-0010-live-capital-escalation.md) | Live size earned by live-vs-shadow tracking on a pre-declared escalation schedule |
| [ADR-0011](docs/decisions/ADR-0011-two-level-data-storage-and-provenance-policy.md) | Two-level data storage: machine-level raw store + project-level processed; upstreams registered in [config/data_sources.yaml](config/data_sources.yaml); no cross-repo processed imports |

Open follow-ups registered at founding: `P1-2.0-RETRO-CARD-1.0-REGISTER`
(retro-card H050/H052a/H053/H054/H055 from 1.0 KPI reports — first admission
candidates); dwell-time feasibility study per ADR-0004 Decision 6 is the
first registered analysis and go/no-go for the allocator program.
(`P1-2.0-CITE-DOI-VERIFY-PBO-2017` closed 2026-07-10: Crossref verified
10.21314/JCF.2016.322 → Bailey, Borwein, López de Prado & Zhu, J. Comput.
Finance 20(4):39-69, during the round-1 audit.)

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
uv venv && uv sync
uv run pre-commit install
uv run pytest
```

## Project state

- **Kind:** quant
- **Bootstrap date:** 2026-07-10
- **Python version pin:** `>=3.11,<3.13`
- **Bootstrap script HEAD:** `fe9bcd1b6fee` (see `manifest.json`)

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
