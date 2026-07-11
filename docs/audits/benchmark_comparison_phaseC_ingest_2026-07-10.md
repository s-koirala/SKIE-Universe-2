# Benchmark comparison — Phase C roll-adjusted ingest port vs 1.0 reference

- **Date:** 2026-07-10 (revised after the round-1 AND round-2
  audit-remediate cycles; supersedes prior revisions in place — the
  working tree is uncommitted).
- **Scope:** Numerical cross-validation of the ported
  [src/skie_universe2/data/ingest/vendor_legacy_1min_roll_adjusted.py](../../src/skie_universe2/data/ingest/vendor_legacy_1min_roll_adjusted.py)
  against the SKIE-Universe 1.0 reference output registered as
  `skie_universe_1_processed_roll_adjusted` in
  [config/data_sources.yaml](../../config/data_sources.yaml)
  (ADR-0011 Decision 2; CLAUDE.md Verification: confirm numerical
  results against a reference implementation).
- **Comparison script (committed evidence):**
  [scripts/audits/compare_benchmark_phaseC.py](../../scripts/audits/compare_benchmark_phaseC.py)
  — runnable via `uv run python scripts/audits/compare_benchmark_phaseC.py`;
  resolves the benchmark location from the registry entry; exit 0 iff
  bit-exact on shared columns.
- **Verdict:** **PASS — bit-exact on all shared columns.** ES and NQ agree
  row-for-row and value-for-value with the 1.0 output over the full
  overlapping range; maximum absolute deviation 0.0 on every shared float
  column. The 2.0 output additionally carries the `pit_provisional`
  metadata column (absent from 1.0; excluded from comparison by design —
  see "PIT-provisional flag" below).

## CRITICAL: shared substrate defect — bit-exactness is not correctness

**DEC_ROLL_LATE_COMMIT (round-1 audit QUANT-1-1, critical).** The
per-year vendor raw files contain only same-year-expiry contracts, so
the December volume-crossover into the next year's H (March) contract is
invisible until the next year's file begins. Empirically confirmed from
the run's committed roll events: **every ES and NQ Z→H roll 2016–2025
commits at the first January session** (2016-01-04, 2017-01-03,
2018-01-02, 2019-01-02, 2020-01-02, 2021-01-04, 2022-01-03, 2023-01-03,
2024-01-02, 2025-01-02 — 10 rolls per symbol, 20 total), ~3 weeks after
the true mid-December crossover (CME guidance: volume migrates ~8
calendar days before last-trade). Bars in each ~Dec-08→early-January
window carry a misattributed front-month.

Because the 1.0 reference was built from the same raw store, **the 1.0
output shares this defect — the bit-exact match above demonstrates port
fidelity only, not substrate correctness.** This is an inherited
substrate defect, not a port bug.

Dispositions taken (code cannot repair missing raw data):

1. Machine-readable records: per-run `coverage_gaps` list in the
   roll-adjusted provenance
   (`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260711.json`,
   **22 entries** after round-2 audit QUANT-2-2: 20 `late_committed_roll`
   entries — detected by contract EXPIRY-year comparison, robust to
   monthly-roll instruments, replacing the round-1 'H-in-January'
   heuristic — plus 2 `terminal_window` entries for ES/NQ Dec-2025,
   where the final in-sample front-month is a Z contract and the
   sample ends inside its expiry month with no successor roll, so the
   takeover is unobservable) and a standing `substrate_defects` field
   on the `vendor_skie_ninja_legacy_raw_1min` entry in
   [config/data_sources.yaml](../../config/data_sources.yaml).
2. `evidence_bar_eligible_returns` downgraded from `true` to
   `"conditional"` in provenance, with
   `evidence_bar_eligibility_conditions` naming this defect (and the
   PIT-provisional flag below).
3. **Registered operator-action follow-up `P1-2.0-DATABENTO-DEC-ROLL-REPULL`:**
   re-pull December-spanning windows (at minimum Dec 01 → Jan 15 around
   each year boundary, all affected symbols) from Databento GLBX.MDP3.
   Requires operator-authorized spend (1.0 ADR-0023 precedent); NOT
   executed in this cycle.

## PIT-provisional flag (round-1 audit QUANT-1-2)

The persistence guard retroactively relabels the effective front-month
over `[challenger_start, commit)` using up to `window_days - 1` future
sessions, and the commit-session label itself (challenger, not the
causal incumbent-persists default) is decided using that session's own
full-session volume — decidable only at session close (round-2 audit
QUANT-2-4). Remediation option (b)/(a) was taken to preserve the
benchmark: the roll boundary and all numerical outputs are unchanged,
and every bar in `[challenger_start, commit]` INCLUSIVE (plus rejected
challenger windows) carries `pit_provisional = true` (ES: 291,959
bars, NQ: 289,587 bars ≈ 7.9% — the ~5 sessions of each of the 43
rolls per symbol). Downstream contract: the ADR-0008 PIT canary suite
and all walk-forward folds must exclude flagged bars or re-resolve
them causally; recorded in provenance (`pit_provisional_note`,
condition `PIT_PROVISIONAL_BARS`).

## Provenance of the two sides

| Side | Artifact | Git HEAD at read/write | Engine |
|---|---|---|---|
| 2.0 (this repo) | `data/processed/vendor_legacy_1min_roll_adjusted/` (`symbol=ES`, `symbol=NQ`) | `0a6be3b51faf88a591204617190b412cc29a02b5` (worktree, pre-commit) | polars 1.40.0 (pinned), Python 3.12.13 |
| 1.0 reference | registry entry `skie_universe_1_processed_roll_adjusted` (`~/Documents/SKIE-Universe/data/processed/vendor_legacy_1min_roll_adjusted/`, materialized 2026-06-02, module v0.4.0) | `ce018515a667ee63aa2d40234305f8cb677f030b` (1.0 repo at read time) | polars 1.40.0, Python 3.11 |

Both sides derive from the same machine-level raw store (registry entry
`vendor_skie_ninja_legacy_raw_1min`, `~/datasets/vendor_skie_ninja_legacy/raw_1min/`):
the 1.0 pipeline's fetch stage *copied* CSVs into that store and read
them back; the 2.0 pipeline reads the identical bytes in place (fetch
adapted per ADR-0011 Decision 1, fail-closed on missing canonical files
per audit CODE-1-5; per-file SHA-256 recorded in
[data/_manifest.json](../../data/_manifest.json) and in
`data/processed/_provenance/vendor_legacy_1min_20260711.json`).

## Input-span decision

The 2.0 roll-adjusted run was materialized with
`--start 2015-01-01 --end 2025-12-31`, matching the input span of the
1.0 benchmark run (its provenance
`vendor_legacy_1min_roll_adjusted_20260602.json` lists source
partitions `year=2015..year=2025` only). This is a requirement of the
comparison, not a limitation of the port: the cumulative
back-adjustment factor of *every* historical bar depends on the full
roll history (module docstring "Point-in-time caveat"), so extending
the span to 2026H1 changes all adjusted levels by construction and
would make level-exactness untestable. The 2026H1 extension is a
one-command rerun (`--end 2026-06-30`) to be executed as its own
provenance-logged materialization when the dwell-time study window is
frozen; the upstream `vendor_legacy_1min` stage already carries the
2026 partitions.

## Method

Script: [scripts/audits/compare_benchmark_phaseC.py](../../scripts/audits/compare_benchmark_phaseC.py)
(committed; replaces the round-0 scratchpad script per audit
REPRODUCIBILITY-1-1). Per symbol:

1. Read all partitions on both sides; sort by `ts_event`.
2. Compare row counts, spans; identify shared vs side-only columns; the
   comparison is restricted to the shared set (2.0-only:
   `pit_provisional`).
3. Restrict both sides to the overlapping `ts_event` range; inner-join
   on `ts_event` (unique per (symbol, ts_event) by schema).
4. Null/NaN integrity gate (round-2 audit REPRODUCIBILITY-2-2):
   exactness requires ZERO nulls on every shared column and ZERO NaNs
   on every shared float column of BOTH frames (null-skipping
   arithmetic would otherwise mask null-vs-value or NaN
   discrepancies); label comparisons are null-safe (`eq_missing`).
   Verified clean on both sides for both symbols.
5. Exactness on shared columns: max absolute deviation on
   `open/high/low/close/adjustment_factor/unadjusted_close/volume`;
   mismatch counts on `front_contract_symbol`, `roll_flag`.

Determinism expectation: the methodology is deterministic (no RNG;
integer volume sums; IEEE-754 ratio products in fixed order), so with
identical inputs and the same pinned polars version the port must be
exact on shared columns — any deviation would have been treated as a
port defect.

## Results (post-remediation re-materialization, 2026-07-10)

| Metric | ES | NQ |
|---|---|---|
| Rows (2.0) | 3,694,534 | 3,659,532 |
| Rows (1.0 ref) | 3,694,534 | 3,659,532 |
| Shared columns + dtypes | identical (11 cols) | identical (11 cols) |
| 2.0-only columns (not compared) | `pit_provisional` | `pit_provisional` |
| Span (both) | 2015-01-01T23:00Z → 2025-12-03T23:59Z | 2015-01-01T23:00Z → 2025-12-19T14:29Z |
| Overlap join | 3,694,534 rows; 0 unmatched either side | 3,659,532 rows; 0 unmatched either side |
| max abs dev — open/high/low/close | 0.0 | 0.0 |
| max abs dev — adjustment_factor | 0.0 | 0.0 |
| max abs dev — unadjusted_close | 0.0 | 0.0 |
| max abs dev — volume | 0 | 0 |
| front_contract_symbol mismatches | 0 | 0 |
| roll_flag mismatches | 0 | 0 |
| nulls / NaNs (both sides, shared cols) | 0 / 0 | 0 / 0 |
| **Bit-exact on shared columns** | **yes** | **yes** |

Algorithmic audit trail also matches the 1.0 provenance exactly
(2.0 `vendor_legacy_1min_roll_adjusted_20260711.json` vs 1.0
`vendor_legacy_1min_roll_adjusted_20260602.json`):

| Audit quantity | ES | NQ | Matches 1.0 |
|---|---|---|---|
| Committed rolls | 43 | 43 | yes |
| window_days / codes | 5 / H,M,U,Z | 5 / H,M,U,Z | yes |
| Bars dropped (non-front) | 19,854 | 26,085 | yes |
| Rejected oscillations | 0 | 0 | yes |
| pit_provisional bars (2.0 only, [start, commit] inclusive) | 291,959 | 289,587 | n/a (1.0 lacks the flag) |

Ingest run stats (2.0, post-remediation `--force` re-materialization):

| Stage | Rows in | Rows out | Runtime |
|---|---|---|---|
| `vendor_legacy_1min` (ES+NQ, 22 CSVs incl. 2026H1) | 7,784,769 CSV rows | 7,784,769 (24 symbol/year partitions) | 27.5 s |
| `vendor_legacy_1min_roll_adjusted` (ES+NQ, 2015–2025) | 7,400,005 (3,714,388 ES + 3,685,617 NQ) | 7,354,066 (3,694,534 ES + 3,659,532 NQ; 45,939 non-front bars dropped) | 68.7 s |

ReproLogs (staged with this document per audit REPRODUCIBILITY-1-1):

- `logs/reproducibility/repro_log_47656a205ec34cb1baf1e6000503e79a.json`
  — roll-adjusted materialization (seed 42, deterministic pipeline — no
  RNG consumed; `config_resolved_sha256` = SHA-256 of
  config/instruments.yaml per audit A).
- `logs/reproducibility/repro_log_7d2967fe00704f099f54c70c7b015849.json`
  — upstream `vendor_legacy_1min` materialization
  (`config_resolved_sha256` = SHA-256 of config/data_sources.yaml).
- `logs/reproducibility/repro_log_a3c1c917f57e4d888354b653b32b3f26.json`
  — this comparison/audit run (emitted after the doc revision; carries
  the doc SHA-256 in `dataset_checksums`).

## Port fidelity statement

Every algorithmic function (`_session_date_expr` — now delegating to the
shared `utils/sessions.py` rule, `detect_raw_front_month_by_day`,
`apply_persistence_guard`, `detect_roll_events`,
`compute_roll_ratio_afml`, `_adjust_one_symbol`, `validate` cross-row
invariants, two-phase-commit `write_processed`) was ported numerically
verbatim from 1.0 v0.4.0; adaptations and audited additions:

1. Imports (`skie_ninja.*` → `skie_universe2.*`).
2. Fetch stage of the upstream `vendor_legacy_1min` job: locate-in-place
   from the registered machine-level store instead of copy-from-sibling
   (ADR-0011 Decision 1), gated by the `config/data_sources.yaml`
   registry (Decision 3), fail-closed on missing canonical files with an
   explicit provenance-recorded `--allow-missing` opt-in (audit CODE-1-5).
3. Strict fail-closed config loaders: missing/malformed
   `config/instruments.yaml` or absent per-symbol `roll_rule` keys raise
   `RollConfigError` instead of silently defaulting; defaults are
   reachable only via the explicit test-override constructor args
   (audit CODE-1-1/QUANT-1-4/REPRODUCIBILITY-1-4). The resolved config's
   SHA-256 is recorded in the ReproLog `config_resolved_sha256`.
4. Provenance hardening: output-frame hash failures are logged and
   recorded (`output_frame_sha256_error`) — never silently substituted
   by the input hash (audit CODE-1-2/QUANT-1-10a); `coverage_gaps`,
   conditional eligibility, `pit_provisional` (above); path keys are
   repo-/~-relative (`portable_key`) so committed artifacts carry no OS
   username (audit L).
5. `--symbols` CLI flag (Phase C scope = ES/NQ; MCL/MGC/SIL rerun later).
6. Expiry-year contract keying (round-2 audit QUANT-2-1, critical):
   `contract_id_full` appends the contract's EXPIRY year (derived from
   the code's trailing year digits + bar year; `_expiry_year_expr`)
   instead of the bar calendar year, so a physical contract straddling
   a calendar-year boundary (routine for monthly-roll MCL/MGC/SIL, and
   for ES/NQ once the December re-pull lands) maps to ONE key instead
   of being split into a fabricated roll whose ratio equals the
   contract's own year-boundary overnight return. The derivation guard
   (`_assert_no_consecutive_year_collision`, re-targeted to derived
   expiry years) now runs for ALL instruments and cannot
   false-positive on legitimate spanning. On the current ES/NQ
   per-year shards no contract straddles a year boundary, so the
   materialized output is unchanged — re-verified bit-exact against
   the 1.0 benchmark below. Year-straddle regression tests added
   (fabricated-roll absence + boundary-return preservation).
7. pit_provisional extended to the commit session (round-2 QUANT-2-4)
   and the commit-batch/rollback machinery of the shadow ledger gained
   claimed-dir rollback + failure-path/concurrency tests (round-2
   QUANT-2-3, QUANT-2-5/REPRODUCIBILITY-2-3) — ledger-side only, no
   effect on this comparison.
8. Citation corrections (audit LITERATURE-1-1/2/3): the multiplicative
   ratio adjustment is attributed to mlfinlab
   `get_futures_roll_series(method='relative')` — AFML §2.4.3's own text
   prescribes additive gap adjustment (Snippet 2.2 `rollGaps`) and is
   cited only for the roll-event/anchor-bar definitions; the Carver
   reference is corrected to *Advanced Futures Trading Strategies*
   (Harriman House, 2023, ISBN 978-0857199683); the CSI citation is
   corrected to the Unfair Advantage manual "Back-Adjusted Contracts"
   section alongside the Norgate continuous-futures methodology page,
   with the caveat that both vendors default to difference-based
   adjustment (only their uniform-scalar-OHLC + unadjusted-volume
   operational convention is borrowed).

The 1.0 distribution-drift check (`check_distribution_stability`) was
not ported into the CLI post-write step: it compared new-vs-prior
snapshots within one output tree, and a fresh materialization has no
prior snapshot by construction; this document plus the committed
comparison script are the cross-repo drift control for the initial
materialization.

Bit-exactness of the shared columns confirms no numerical drift was
introduced by any of these adaptations.

## Follow-ups

- **`P1-2.0-DATABENTO-DEC-ROLL-REPULL` (operator action, critical):**
  re-pull December-spanning raw windows to repair DEC_ROLL_LATE_COMMIT;
  registered in config/data_sources.yaml `substrate_defects`. Requires
  Databento spend authorization; not executable by the agent.
- `P1-2.0-ROLL-2026H1-EXTEND`: re-materialize roll-adjusted ES/NQ with
  `--end 2026-06-30` once the dwell-time study window is frozen
  (levels change by construction; returns preserved).
- `P1-2.0-ROLL-SYMBOL-EXPAND`: MCL/MGC/SIL materialization
  (`--symbols MCL MGC SIL`; instruments.yaml roll rules already lifted).
- `P1-2.0-PIT-PROVISIONAL-CANARY-WIRING`: wire the `pit_provisional`
  exclusion into the ADR-0008 PIT canary suite when it is lifted from
  1.0 (the flag is emitted now; enforcement lands with the canaries).
- Carried 1.0 method follow-ups: `P1-ROLL-METHOD` (volume vs OI
  crossover), `P1-ROLL-ANCHOR` (anchor sensitivity),
  `P1-LEVEL-USE-POLICY` (per-fold level re-materialization enforcement
  via the ADR-0008 PIT canaries).
