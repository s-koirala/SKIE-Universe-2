# Audit trail — Phase C evidence substrate + shadow-ledger writer

- **Deliverable:** numerical-fidelity port of the 1.0 roll-adjusted
  continuous-contract ingest (`src/skie_universe2/data/ingest/`), shadow-ledger
  writer per ADR-0003 (`src/skie_universe2/ledger/shadow_ledger.py`), ADR-0011
  registry-refusal gate, ES+NQ substrate materialization
  (`data/processed/vendor_legacy_1min_roll_adjusted/`, gitignored; provenance
  committed), committed benchmark comparison
  ([scripts/audits/compare_benchmark_phaseC.py](../../scripts/audits/compare_benchmark_phaseC.py)).
- **Pattern:** audit-remediate loop (Workflow engine), 3 rounds (cap), branches:
  code-reviewer, quant-auditor, reproducibility-verifier, literature-check.
  Adversarial refute gate on every critical/major; 2 findings refuted total.
- **Benchmark:** bit-exact on all shared columns vs the registered 1.0
  reference (max abs dev 0.0; null/NaN integrity gates), ES 3,694,534 /
  NQ 3,659,532 joined rows — a PORT-FIDELITY claim only; both sides share the
  DEC_ROLL_LATE_COMMIT substrate defect (see below).

## Round 1 — block (15 confirmed, 1 refuted QUANT-1-3, 17 minors)

Highlights (full list in the round-1 workflow journal):

- **QUANT-1-1 (critical):** per-year vendor pulls contain only same-year-expiry
  contracts, so every Z→H December roll 2016–2025 commits ~3 weeks late at the
  first January session. Inherited from the raw store — the 1.0 reference
  shares it (bit-exactness ≠ correctness). Dispositioned: machine-readable
  `coverage_gaps` in provenance, `substrate_defects` entry in
  config/data_sources.yaml, evidence eligibility downgraded to conditional,
  operator follow-up `P1-2.0-DATABENTO-DEC-ROLL-REPULL` (Databento spend gated
  on operator authorization; no code patch — the defect is in the substrate).
- **QUANT-1-2:** persistence-guard retroactive front-month relabel uses up to
  window_days−1 future sessions → per-bar `pit_provisional` flag added
  (numerical outputs unchanged); PIT canary must exclude flagged bars.
- Fail-open config loaders, silent provenance degradation, fail-open fetch,
  ledger batch atomicity, TOCTOU/lost-append concurrency, session_date
  integrity, covariate registry (config/covariates.yaml), evidence chain
  committed, AFML/Carver/CSI citation corrections, identity hygiene.

## Round 2 — block (7 confirmed, 1 refuted REPRO-2-1, 20 minors); code-reviewer + literature-check accept

- **QUANT-2-1 (critical):** `contract_id_full` keyed on bar-calendar-year
  fabricated roll events for year-straddling contracts (reproduced end-to-end
  on a synthetic MCL fixture: real 2.8% year-boundary return erased). Latent
  for ES/NQ only because of the per-year sharding defect. Fixed: expiry-year
  derivation (CME month-code parse, decade-inferred), collision guard active
  for all instruments, year-straddle regression test.
- **QUANT-2-2:** coverage-gap detector missed terminal December windows and
  non-H roll codes → generalized; provenance now emits 22 gaps
  (20 `late_committed_roll` + 2 `terminal_window` for ES/NQ Dec-2025).
- **QUANT-2-3:** two-phase-commit rollback left claimed-but-unpromoted
  partition dirs that wedged retries → claimed-list tracking + retry test.
- **QUANT-2-4:** `pit_provisional` extended to the commit session inclusive
  (label decidable only at session close); metadata-only, re-materialized.
- **QUANT-2-5 / REPRO-2-3:** failure-path + concurrency test coverage added
  (mid-promote rollback, staging failure, append contention, lock timeout) —
  17 new tests.
- **REPRO-2-2:** benchmark script was null/NaN-blind → null_count/is_nan gates
  on both frames, null-safe label comparison; re-run bit-exact.

## Round 3 — verdict: ACCEPT (all four branches; cap reached)

Verified this round: expiry-year derivation property-tested against an
analytic oracle (0/2000 mismatches), year-straddle test validity, terminal-gap
semantics for the ES/NQ scope, rollback retry path. 105 tests pass; ruff
clean; benchmark exit 0; manifest --check passes.

## Documented residuals (minors; latent, mostly metals-expansion-scoped)

- CODE-3-1..5 (assert-narrowing under `-O`, two annotation gaps, rollback
  snapshot memory pattern, SystemExit in helper).
- QUANT-3-1: collision-guard threshold 6 should be 10 under expiry-year
  semantics (latent — current derivation cannot produce gaps 1–9).
- QUANT-3-2: terminal-window rule encodes the equity-index quarterly calendar;
  must be generalized per-instrument **before** `P1-2.0-ROLL-SYMBOL-EXPAND`
  (MCL/MGC/SIL materialization) — registered as a blocking precondition there.
- Round-1/2 logged minors as recorded in the workflow journals.

## Registered operator follow-ups

| ID | Action | Gate |
|---|---|---|
| P1-2.0-DATABENTO-DEC-ROLL-REPULL | Re-pull December-spanning windows (Dec 01→Jan 15 per year boundary, all symbols) from Databento GLBX.MDP3 | Operator-authorized spend (1.0 ADR-0023 precedent) |
| P1-2.0-ROLL-SYMBOL-EXPAND | Materialize MCL/MGC/SIL | Blocked on QUANT-3-2 terminal-rule generalization |
