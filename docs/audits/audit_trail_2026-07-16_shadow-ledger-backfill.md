# Audit trail — shadow-ledger backfill foundational build

**Deliverable:** the shadow-ledger backfill infrastructure (backfill plan
[docs/research_notes/shadow_ledger_backfill_plan_2026-07-16.md](../research_notes/shadow_ledger_backfill_plan_2026-07-16.md)
milestones M0–M2) —
[experts/base.py](../../src/skie_universe2/experts/base.py) (OD-1 interface
contract), [execution/tier0_barclose.py](../../src/skie_universe2/execution/tier0_barclose.py)
(Tier-0 execution helper), [experts/reference.py](../../src/skie_universe2/experts/reference.py)
(reference smoke expert), and [scripts/run_shadow_ledger_backfill.py](../../scripts/run_shadow_ledger_backfill.py)
(driver), with tests.

**Mechanism:** [audit-remediate-loop](../../../.claude/skills/audit-remediate-loop)
via the Workflow engine (`.py` routing → code-reviewer, quant-auditor,
reproducibility-verifier, adversarial refute gate) on the M0/M1 contract + Tier-0
helper (run `wf_8ac00395-4a6`), plus **end-to-end runtime validation** of the M2
driver on the current ES/NQ substrate.

**Outcome:** round-1 audit on M0/M1 raised **2 majors + 10 minors**, all
remediated; both majors verified fixed with new tests. The M2 driver + reference
expert are validated by an executed smoke run (below) rather than a separate audit
round (a driver-scope audit is a recommended follow-up).

## Round 1 (M0/M1) — proceed-with-remediation (2 majors, 0 refuted, 10 minors); code-reviewer ACCEPT

| ID | Branch | Issue | Disposition |
|---|---|---|---|
| QUANT-1-1 | quant | **Tier-0 gross return used the linear `pos·r`** — only exact for `\|pos\|=1`, and CANNOT represent ruin at leverage (Kelly sweep reaches 1.25): a wipeout `1+pos·(exp(r)−1)≤0` stays finite as `pos·r`, biasing the geometric-growth estimate the Kelly sweep turns on. | **Fixed** — exact levered log return `log1p(pos·expm1(r))`; wipeout-or-worse (`arg ≤ −1`) surfaces as `−inf`. New tests: exact-short, leverage-exact-not-linear, ruin-is-`−inf` |
| REPRODUCIBILITY-1-1 | repro | **Causality canary tested a single cut** — a data-dependent leak whose source and target both sit inside the prefix escapes (demonstrated: output[3]←close[20] missed at cut≥25). | **Fixed** — `assert_prefix_invariant` sweeps a cut grid; new test proves a point leak a single cut misses is caught by the grid |
| CODE-1-1 / QUANT-1-3 / REPRODUCIBILITY-1-2 | code/quant/repro | `expert_id` `{name}@{version}` contract unenforced | **Fixed** — `assert_valid_expert_id` (exactly one `@`, non-empty name+version), called by the canary gate; parametrized test |
| CODE-1-2 | code | `direction` int8 coercion lossy (0.9→0 passes) | **Fixed** — reject non-integer-valued direction before cast |
| CODE-1-3 / QUANT-1-4 | code/quant | `SignalSeries` accepted `±inf` strength (only finite mask checked) | **Fixed** — NaN allowed (warm-up), `±inf` rejected, `[0,1]` enforced |
| CODE-1-4 | code | undocumented boundary conventions (start_position, final-bar turnover, linear-in-turnover cost) | **Fixed** — documented in the module docstring |
| QUANT-1-2 | quant | per-side drag = round-trip/2 applied linearly (nonlinear-drag approximation) | **Documented** — the standard matched-turnover linear-in-contracts convention, noted as intentional |
| QUANT-1-5 / REPRODUCIBILITY-1-3 | quant/repro | canary single-cut semantics; final-bar turnover never charged | **Fixed / documented** — multi-cut sweep; final-bar boundary documented (negligible over a long backfill) |

## M2 driver — runtime validation (executed on current data)

Operator decision (2026-07-16): run on the **existing ES/NQ roll-adjusted
substrate** (primary-exclusion variant; December-roll windows excluded, not
corrected — no new-data budget). The `--smoke` run of the reference expert ×
{ES,NQ} × 4 Kelly fractions to an isolated scratch ledger:

- **64 partitions, 15,992 rows** written via the append-only `ShadowLedgerWriter`
  two-phase commit; the signal-layer PIT canary passed on each instrument.
- Read-back: exact 8-column `_CORE_COLUMNS` schema, `fidelity_tier=0`, all four
  Kelly fractions materialized as distinct `expert_id`s (selection deferred per the
  two BLOCKING Kelly memos), `ret_gross` all finite, `ret_net ≤ ret_gross` (cost
  drag applied), mean net ≈ −2e-5 (the trivial reference rule loses slightly after
  costs — expected).

This proves the full population chain (load → exclude → aggregate → emissions →
expert signal → Kelly-swept position → Tier-0 counterfactual → writer) works
end-to-end on current data.

## Residual risk / follow-ups

- **Driver-scope audit** (position-policy mapping `target = direction·strength·kelly`,
  cost `per_unit = switch_drag_notional/2`, per-bar accrual keying) is validated by
  the smoke read-back but not by a dedicated audit round — recommended before the
  first *real* backfill.
- **First real evidence backfill needs a frozen-design expert.** `meta_shift` is
  demoted (H001 null) and the reference expert produces no evidence; **H101** (the
  first candidate) requires its 2.0 `design.md` frozen (the ORB entry/exit rule)
  before its partitions enter the canonical ledger (plan M3).
- **Trained experts** refit per rolling window (the contract's `fit` hook); the
  smoke uses a stateless expert so signals over the whole series — the driver's
  per-window refit loop is exercised only when a trained expert is added.
- **December-roll windows remain excluded**, not corrected (no Databento repull) —
  a documented substrate limitation carried from H900/H001.

Tests: 32 passing across the contract, Tier-0 helper, and reference expert. Lint
clean.
