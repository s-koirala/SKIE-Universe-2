---
type: deliverable_spec
slug: h107-screen
session_id: 469c1ea1-c771-4e19-aa6b-d51b3bcc59c4
date: 2026-11-22
session_objective: Execute the frozen H107 (RC-H107-1) ADR-0014 SCREEN on the canonical shadow ledger and gate the resulting disposition + Expert Card through audit-remediate-loop, stopping before any verdict/Kelly/span selection.
---

# Deliverables

- [x] `C:\Users\skoir\Documents\SKIE-Universe-2\reports\H107\rc_h107_1_screen.json`
  - state: RC-H107-1 screen executed on the canonical k1.0 ledger for all 7 EMA spans x {ES, NQ}; S-a..S-e stages, per-grid-point statistics, per-window growth, descriptive NinjaTrader net columns, and a single disposition field (`pool-hold-reconsider` | `archive-no-persistent-window`) all present.
  - check: `uv run python scripts/run_screen_h107.py` exits 0 and the file is valid JSON carrying 14 grid-point records (7 spans x 2 instruments) plus the disposition.

- [x] `C:\Users\skoir\Documents\SKIE-Universe-2\research\01_hypothesis_register\H107\expert_card_v1.md`
  - state: ADR-0009 Expert Card v1 emitted from the screen JSON; register family `rc-h107-1` carries exactly 14 trial records; burned-data spans appended under `hid: H107`; on PASS, one 4-Kelly-fraction pool-record set per passing grid point appended, keyed to that grid point's ledger id.
  - check: `uv run python scripts/emit_screen_expert_card_v1.py --hid H107` exits 0; `config/multipletest_family.yaml` family `rc-h107-1` `trials` length == 14.

- [x] `C:\Users\skoir\Documents\SKIE-Universe-2\docs\audits\audit_trail_h107-screen_2026-11-22.md`
  - state: audit-remediate-loop trail for the H107 screen disposition — per-round specialist findings, adversarial refute-gate adjudications, remediations, and termination condition recorded.
  - check: file exists, written this session, references the RC-H107-1 screen JSON and the Expert Card, and records a terminal `converged | stalled | capped` state.

# Delegation

- agent: quant-auditor
  objective: Determine whether the RC-H107-1 screen statistics are computed and applied faithfully to the frozen design §5/§8 — panel Romano-Wolf StepM over the 7-span columns per instrument (joint resample, cross-span dependence preserved), DSR with HAC n_eff and the §8 n_trials_gate(87)/dispersion surface, CSCV PBO on the T x 7 grid matrix, exact per-session turnover recovery, and the gate conjunction (S-c AND S-d AND S-e) at the runtime-read enacted level 0.7400550140326007.
  output: Structured findings list (severity x {subject|apparatus}, file:line, concrete defect, suggested remediation), each through the adversarial refute gate; empty list if clean.
  sources: reports/H107/rc_h107_1_screen.json; src/skie_universe2/screening/grid_screen.py; src/skie_universe2/screening/screen_spine.py; src/skie_universe2/inference/{romano_wolf.py,deflated_sharpe.py,pbo.py}; scripts/run_screen_h107.py; research/01_hypothesis_register/H107/design.md; config/multipletest_family.yaml.
  excluded: citation validity (literature-check); reproducibility envelope (reproducibility-verifier); the frozen design itself (immutable post-freeze — audit the run against it, not it).

- agent: reproducibility-verifier
  objective: Determine whether the H107 backfill + screen run is reproducible — 13-field ReproLog emitted per run, substrate checksums bound in the screen ReproLog (digest over the 7 grid ledgers' partition hashes), design SHA-256 912198045de4 recorded, seed 20261122 determinism, and the design §11 run sequence re-runnable from the pinned env.
  output: Structured findings list (same schema as above), each refute-gated; empty list if clean.
  sources: logs/reproducibility/repro_log_*.json (this session's runs); scripts/run_shadow_ledger_backfill.py; scripts/run_screen_h107.py; research/01_hypothesis_register/H107/design.md §11; data/_manifest.json.
  excluded: statistical-method fidelity (quant-auditor); citation checks (literature-check).

- agent: literature-check
  objective: Verify the single registered support citation (Gao, Han, Li & Zhou 2018, J. Financ. Econ. 129(2):394-414, doi 10.1016/j.jfineco.2018.05.009) is real and correctly attributed, and confirm the design/Expert Card do NOT over-claim it as support for the exact VWAP/EMA crossover rule (the design already flags it as nearest-peer / practitioner-rule, Crossref PENDING).
  output: Per-citation finding (exists / attribution correct / scope of claim), refute-gated; empty if clean.
  sources: WebFetch/WebSearch for the DOI; research/01_hypothesis_register/H107/design.md §1; research/01_hypothesis_register/H107/expert_card_v1.md; hypothesis_backlog.md H107 row.
  excluded: method fidelity, reproducibility, the screen numbers.

# Self-executed

- git pull --ff-only origin main; uv sync --all-extras  (reason: integration/env setup — not a new method/module/analysis/revised-claim deliverable per audit-remediate-loop "When to invoke"; a clean fast-forward of upstream-committed, already-audited code)
- uv run pytest (H107 suites + sanity)  (reason: running existing committed tests, not authoring a deliverable — "When to invoke" excludes non-deliverable mechanical steps)
- run_shadow_ledger_backfill.py (smoke + canonical) -> screen -> emit  (reason: execution of a FROZEN, upstream-audited pre-registered protocol (design SHA 912198045de4, immutable); the deliverable that requires the loop is the disposition/Expert Card OUTPUT, which is delegated-audited above, not the mechanical run that produces it)
