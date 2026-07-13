# SKIE-Universe-2

Meta-strategy allocation research program (SKIE Universe 2.0): online
strategy selection over an arsenal of expert strategies, with the allocator —
not the individual strategy — as the unit of statistical inference. Founding
governance: ADR-0001..0010 under [docs/decisions/](docs/decisions/).

## SKIE Universe 2.0 — capital philosophy

2.0 is reframed from a risk-averse tail-protection posture to **optimism +
exponential (compounded/geometric) growth pursued through a high-risk
methodology**. The primary decision/ranking metric is **geometric growth =
Kelly-optimal log-wealth growth rate**. The Kelly fraction is a registered
hyperparameter swept over the grid {0.5, 0.75, 1.0, 1.25} — bracketing the
estimation-error-adjusted geometric-growth optimum from half-Kelly (the
estimation-error shrink point) through leveraged, so the data-selected winner is
not structurally floored above the growth optimum — with the winning fraction
data-selected by best geometric growth over the joint (config × fraction) space.
The lower-tail terminal-wealth quantile is demoted from the binding decision
metric to a monitored, non-binding guardrail (still computed and reported; it
informs, it does not veto).

The overfitting/integrity core — Deflated Sharpe, PBO, the matched-turnover
random rotor, PIT canaries, the family-wise trial register, the ReproLog, and
the shadow ledger — is **non-waivable and more important under leverage**: an
overfit champion at leverage does not merely underperform, it ruins via negative
geometric growth, so these gates are the backstop that licenses the looser
admission screen and steeper ramp. See
[ADR-0013](docs/decisions/ADR-0013-aggressive-geometric-growth-mandate.md)
(proposed).

## Residual risk (founding audit, 2026-07-10)

The founding ADR set passed a 3-round audit-remediate loop (final verdict
accept, both branches; trail at
[docs/audits/audit_trail_2026-07-10_founding-adrs.md](docs/audits/audit_trail_2026-07-10_founding-adrs.md)).
Standing residual: governance prose constrains nothing numerically until
implementation — the SPA/StepM/DSR/PBO constructions, registered quantile
level + horizon, TOST α/power calibration, and per-trial register schema must
be re-audited against the ADR text at first implementation. Five logged
minors remain open (see trail §Open).

## Project status

As of 2026-07-12 the dwell-time feasibility gate (ADR-0004 Decision 6, the
program's first registered go/no-go) is **CLOSED GO** (H900), opening the
allocator program. H900 BOCPD detection-latency sensitivity is closed: the
CUSUM verdict reproduces bit-identically while unsupervised BOCPD is NO-GO both
variants, so the H900 GO is **supervised-detection-dependent** (robust to
whitening). The winning 4-state diagonal-Gaussian HMM is registered as the
ADR-0002 candidate conditioning covariate, with dwell/detection-latency as
standing ADR-0004 report objects. The aggressive geometric-growth governance
reframe (ADR-0012 champion-challenger + ADR-0013 mandate) is **proposed**;
enactment is gated on ADR-0013 acceptance and the two BLOCKING Kelly follow-ups
(`P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`,
`P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`). Full session detail and next
steps: [docs/research_notes/session_handoff_2026-07-12.md](docs/research_notes/session_handoff_2026-07-12.md).

## Status

| Field | Value |
|---|---|
| Kind | `quant` |
| Python | `>=3.11,<3.13` |
| License | `MIT` |
| Bootstrap date | `2026-07-10` |
| Dotfiles HEAD | `fe9bcd1b6fee` |

## Layout

```
SKIE-Universe-2/
├── src/                  # source-layout package
├── tests/                # pytest suite
├── scripts/              # one-shot entrypoints
├── notebooks/            # exploratory (stripped via nbstripout)
├── data/
│   ├── raw/              # read-only vendor pulls (gitignored)
│   ├── interim/          # lossy transforms (gitignored)
│   ├── processed/        # analysis-ready (gitignored)
│   └── external/         # reference data
├── docs/
│   ├── audits/           # audit-remediate-loop trails
│   ├── decisions/        # ADRs (Nygard/MADR)
│   ├── literature/       # primary-source PDFs + notes
│   ├── methodology/      # method memos, derivations
│   ├── reports/          # stakeholder-facing reports
│   ├── research_notes/   # dated memos
│   └── templates/        # reusable doc templates
├── artifacts/
│   ├── models/           # versioned model binaries
│   └── runs/             # run aggregate outputs
├── runs/                 # top-level run outputs (SKIE-Universe convention)
├── research/             # hypothesis-register / analysis-stage subdirs
├── reports/              # rendered reports
├── config/               # validated configs (pydantic / yaml)
├── logs/
│   └── reproducibility/  # ReproLog records + pip-freeze archive
├── outputs/              # scratch outputs (NOT artifacts)
├── CLAUDE.md             # project-local Claude rules
├── CHANGELOG.md          # Keep-a-Changelog 1.1.0
├── CITATION.cff          # CFF v1.2.0
├── LICENSE
├── pyproject.toml        # PEP 621
├── .gitignore
├── .pre-commit-config.yaml
└── manifest.json         # bootstrap reproducibility anchor
```

## Setup

```bash
# Create venv from project pyproject.toml
uv venv && uv sync

# Install pre-commit hooks (seed-guard, citation-cff)
uv run pre-commit install

# Run tests
uv run pytest

# Check data manifest integrity
python ~/.claude/scripts/build_data_manifest.py --check
```

## Reproducibility

This project follows the 13-field ReproLog contract documented at
`~/.claude/skills/emit-repro-log/SKILL.md`. Every artifact-producing run
records:

- git HEAD
- pip freeze SHA-256 (full 64-hex, archived under `logs/reproducibility/env/`)
- dataset checksums from `data/_manifest.json`
- RNG seed
- model commit hash

Commits use `/commit-with-provenance --role=<role>` which emits
`Repro-Log-Path:` and `Repro-Log-SHA256:` trailers per ICMJE 2026 AI-assistance
disclosure.

## Citation

See [CITATION.cff](CITATION.cff) (CFF v1.2.0) for machine-readable citation
metadata. To add a reference to the bibliography:

```bash
# Via /cite-add slash command (resolves via CrossRef MCP)
/cite-add 10.1093/jamiaopen/ooy012
```

## Architecture decisions

See [docs/decisions/](docs/decisions/) for ADR records (Nygard/MADR format).
New decisions via `/adr-new "<title>"`.

## License

See [LICENSE](LICENSE).
