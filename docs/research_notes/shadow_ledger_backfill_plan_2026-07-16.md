# Shadow-ledger backfill — implementation plan

**DRAFT — for review.** This is a design note for operator review, not a
frozen method. No hypothesis design.md is frozen and no ledger partition is
written on the strength of this document. It plans the ADR-0003 shadow-ledger
backfill — the critical-path blocker for the allocator program (no
rolling-origin edge series exists anywhere in 1.0; retro-card register gap 3,
[docs/research_notes/retro_card_register_2026-07-10.md](retro_card_register_2026-07-10.md)).

Governing ADRs: [ADR-0003](../decisions/ADR-0003-shadow-ledger-canonical-object.md)
(canonical object), [ADR-0011](../decisions/ADR-0011-two-level-data-storage-and-provenance-policy.md)
(storage), [ADR-0006](../decisions/ADR-0006-execution-fidelity-tiers.md) (Tier-0
default), [ADR-0005](../decisions/ADR-0005-three-layer-separation.md) (layer
separation), [ADR-0002](../decisions/ADR-0002-arsenal-admission-standard.md)
(admission / covariates), [ADR-0008](../decisions/ADR-0008-integrity-non-negotiables.md)
(integrity non-negotiables).

## 0. What already exists (reuse; do not duplicate)

The backfill is mostly assembly of existing components. The one large piece —
the append-only writer — is **already built and audited**:

| Component | Module | Reused for |
|---|---|---|
| Ledger writer + schema + append-only + two-phase commit + ReproLog + manifest rebuild | [src/skie_universe2/ledger/shadow_ledger.py](../../src/skie_universe2/ledger/shadow_ledger.py) (`ShadowLedgerWriter`) | The entire storage/provenance layer of §1. **Do not re-implement.** |
| Feature pipeline: load → `apply_registered_exclusions` → `aggregate_5min` → `compute_emissions`; PIT canary | [src/skie_universe2/features/regime_emissions.py](../../src/skie_universe2/features/regime_emissions.py) | §2 features_t; §4 PIT canary |
| Tier-0 cost drag (`log(1−cost/notional)`, per-side, fail-closed from config) | [src/skie_universe2/costs/futures_rt_v1.py](../../src/skie_universe2/costs/futures_rt_v1.py) (`FuturesRtV1CostModel`) | §2 bar-level cost → `ret_net` |
| Tier-1 intrabar simulator (later tier promotion only) | [src/skie_universe2/execution/tier1_intrabar.py](../../src/skie_universe2/execution/tier1_intrabar.py) | NOT the backfill default; ADR-0006 Tier 0 is |
| Signal layer (example expert) | [src/skie_universe2/signals/meta_shift_signal.py](../../src/skie_universe2/signals/meta_shift_signal.py) | §2 signal_t reference shape |
| Position policy + Kelly sweep grid | [src/skie_universe2/policy/meta_shift_policy.py](../../src/skie_universe2/policy/meta_shift_policy.py) (`KELLY_FRACTION_GRID`) | §2 position target |
| Rolling-origin windows | [src/skie_universe2/eval/windows.py](../../src/skie_universe2/eval/windows.py) (`h900_windows`) | §2 walk-forward refit boundaries |
| Roll-adjusted 5-min substrate (ES, NQ) | `data/processed/vendor_legacy_1min_roll_adjusted/symbol={ES,NQ}/year=YYYY/part-0000.parquet` | §2 raw→feature input |
| ReproLog capture | [src/skie_universe2/utils/reproducibility.py](../../src/skie_universe2/utils/reproducibility.py) (`capture`) | §4 (writer already calls it internally) |
| Load→aggregate→emission→rolling-window orchestration pattern | [scripts/run_h900_dwell_study.py](../../scripts/run_h900_dwell_study.py), [scripts/run_h001_covariate_study.py](../../scripts/run_h001_covariate_study.py) | §2/§3 driver skeleton |

**To be built:** (a) an expert-interface contract (§5 open decision), (b) a
Tier-0 bar-close execution+counterfactual-return helper
`src/skie_universe2/execution/tier0_barclose.py` (small; currently only Tier 1
exists), (c) the population driver `scripts/run_shadow_ledger_backfill.py`, and
(d) per-expert `design.md` freeze + `config/covariates.yaml` registration.

## 1. Ledger schema (ADR-0003) and storage (ADR-0011)

The schema is **already frozen** in
[shadow_ledger.py](../../src/skie_universe2/ledger/shadow_ledger.py) (`_CORE_COLUMNS`,
`_core_schema`) and validated on write. The backfill conforms to it rather than
redefining it. Core columns (all non-nullable, in order):

| Column | Dtype | ADR-0003 mapping |
|---|---|---|
| `expert_id` | Utf8 | Versioned `{name}@{version}` (must contain `@`; version bump = new identity, Decision 3) |
| `asset` | Utf8 | Root symbol (ES, NQ), matches substrate partition |
| `bar_ts` | Datetime(us, UTC) | The bar the counterfactual return **accrues over** (unique per partition) |
| `session_date` | Date | CME session date of `bar_ts` (partition key; recomputed + checked via `cme_session_date_expr`) |
| `ret_gross` | Float64 | Counterfactual **pre-cost** log-return of the expert's position over the bar (ADR-0002(c)/ADR-0008 D2: gross reported alongside net) |
| `ret_net` | Float64 | `ret_gross` minus bar-level cost drag (ADR-0008 D2: log-return drag at bar level, never flat-dollar) |
| `cost_model_id` | Utf8 | `futures_rt_v1` (+ version) — provenance chain |
| `fidelity_tier` | Int64 | **0** for the backfill (ADR-0006 Tier-0 bar-close default); closed set {0,1,2} |
| `cov_*` | Float64 | Zero+ pre-registered conditioning covariates as **wide** columns (ADR-0003 D6 / ADR-0008 D4); exact-set enforced per expert family against [config/covariates.yaml](../../config/covariates.yaml) |

Design mapping of `signal_t` / `position target` to schema: the ledger stores
the **realized counterfactual return** (`ret_gross`/`ret_net`), not the
intermediate signal or target directly. Per ADR-0005 layer separation and the
writer's look-ahead note, the signal/target are the *producer's* internal state;
what enters evidence is the position-weighted per-bar return. **Open decision
OD-4** (§5): whether to additionally register `cov_signal_strength` /
`cov_target_position` as wide covariate columns for attribution, or keep them in
a sidecar. Recommendation: keep the ledger core minimal (schema is frozen and
audited) and carry signal/target as a gitignored per-run attribution sidecar
under `data/interim/`, not as `cov_` columns (those are reserved for ADR-0002(b)
conditioning covariates, not diagnostics).

**Storage / partitioning (ADR-0011 D6, already implemented):**
- Location: `data/processed/shadow_ledger/` (project-level *processed*, derived,
  reproducible, **never committed** — ADR-0011 D5/D6).
- Partition keys: `expert_id={id}/asset={A}/session_date={YYYY-MM-DD}`, one
  `part-0000.parquet` per partition.
- Machine-raw store is untouched: input is the already-materialized
  `data/processed/vendor_legacy_1min_roll_adjusted/` (itself derived from the
  registered `~/datasets/` raw store per
  [config/data_sources.yaml](../../config/data_sources.yaml)). The backfill is
  processed→processed; it does **not** re-ingest raw (that was Phase C) and does
  **not** write into `~/datasets/`.
- Per-partition SHA-256 (`file_sha256` + canonical `frame_sha256`) roll-ups land
  in `data/processed/shadow_ledger/_rollups/rollups.jsonl` and
  `data/_manifest.json` (manifest builder re-run by the writer). Commit policy:
  only `_manifest.json` is committed (ADR-0011 D5).

## 2. What to backfill first, and the per-bar population procedure

**Scope (first pass):** the ADR-0002-shaped retro-card candidates on the
**existing ES/NQ 5-min roll-adjusted substrate** — the only substrate that
exists in-project today. From the retro register
([retro_card_register_2026-07-10.md](retro_card_register_2026-07-10.md)) the
cleanest conditional-edge candidates are **H101 (unconditional first-hour ORB,
NQ-positive)** and **H103 (first-hour ORB × HMM-stress cell)** — both are
signal-layer objects expressible on ES/NQ 5-min bars, and both are explicitly
"admission turns on powered accumulation via the shadow ledger". H100/H102/H104
are cost-bound / integrity-incomplete / unregistered-universe and are **not**
first-pass. The already-coded `meta_shift_sma3_std3_v1`
([meta_shift_signal.py](../../src/skie_universe2/signals/meta_shift_signal.py)) is
the **pipeline smoke-test expert** — run it first end-to-end to validate the
driver before the retro candidates, but it is not itself an admission candidate
until its own design.md is frozen.

**Substrate span:** the H900 sample `2015-01-02 .. 2025-12-31`, ES + NQ, primary
exclusion variant (drop `pit_provisional` + registered December-roll coverage
gaps via `apply_registered_exclusions`). This reuses the exact load/exclude/
aggregate path of [run_h900_dwell_study.py](../../scripts/run_h900_dwell_study.py)
lines 291-327.

**Append-only population, per (expert × asset × bar), Tier 0 (ADR-0006 D1):**

1. **features_t.** Load 1-min → `apply_registered_exclusions` → `aggregate_5min`
   → `compute_emissions` (reused verbatim). All features are trailing-window /
   PIT-clean by construction (module docstring; canary in §4). Rolling-origin
   refit boundaries from `h900_windows()` with purge = `MAX_FEATURE_LOOKBACK_BARS`
   (288) and Politis-White embargo — identical to H900/H001 so the ledger is
   walk-forward-consistent (ADR-0004; any expert with a trained component refits
   per window at the origin, filters causally into the eval span).
2. **signal_t.** Expert emits direction + calibrated strength at bar close of
   bar t **from data ≤ t only** (ADR-0005 Layer 1; enforced by the interface
   contract of OD-1 + the §4 canary). No sizing, no fills.
3. **position target.** Position policy maps `signal_t` → signed target for the
   swept Kelly fraction (ADR-0005 Layer 2; `KELLY_FRACTION_GRID = {0.5, 0.75,
   1.0, 1.25}`, ADR-0013 D3). **Every Kelly fraction is a distinct `expert_id`
   suffix** (e.g. `..._k0.5@1.0.0`) so the joint (config × fraction) space is
   materialized and later data-selected on geometric growth — never hand-picked
   (CLAUDE.md; selection itself is BLOCKED on the two Kelly memos, so the
   backfill *materializes all four* and selects none).
4. **Tier-0 execution + counterfactual return.** Position set at close(t)
   accrues the **close(t)→close(t+1) log return** of the roll-adjusted series:
   `ret_gross_t = target_position_t · r_{t+1}` where `r_{t+1} =
   log(close_{t+1}/close_t)` on the retained-bar series (the same `ret_5m`
   convention as [regime_emissions.py](../../src/skie_universe2/features/regime_emissions.py),
   null across December-roll gaps). This is the **critical PIT alignment**: the
   return realized over (t, t+1] is paired with a target decided at t — no
   look-ahead. The bar the row is keyed on (`bar_ts`) is the accrual bar t+1
   (writer semantics: "the bar the counterfactual return accrues over").
5. **Bar-level cost.** On any change in target position (turnover
   `|Δposition_t|`), apply `FuturesRtV1CostModel.switch_drag_notional` as a
   log-return drag scaled by turnover: `ret_net_t = ret_gross_t −
   turnover_t · c_switch(asset, reference_price)`. `cost_model_id =
   "futures_rt_v1"`. Costs apply at Tier 0 (ADR-0006 D4: cost model at *every*
   tier). New helper `execution/tier0_barclose.py` owns steps 4-5 (bar-close
   fill + turnover-scaled drag) so it is unit-testable in isolation.
6. **Write.** Accumulate rows per (expert_id, asset, session_date), hand the
   frame to `ShadowLedgerWriter.write_partitions(df, rng_seed=SEED,
   hypothesis_id=...)`. Validation, staging, atomic promote, ReproLog, roll-ups,
   manifest rebuild are all handled by the writer.

**Counterfactual completeness (ADR-0003 D1).** "Every expert × asset × bar,
traded or not" means a row for **every valid emission bar**, including flat
bars (`target=0 → ret_gross=0, ret_net=0`). Do not sparsify flat bars — the
full-information experts guarantee (O(√(T ln N)) regret) depends on the complete
counterfactual record.

## 3. Integration with existing pipelines (concrete reuse points)

- **Ingest / substrate:** none re-run. Consume the Phase C output at
  `data/processed/vendor_legacy_1min_roll_adjusted/` via the `_load_bars_1min`
  scan-glob idiom ([run_h900_dwell_study.py](../../scripts/run_h900_dwell_study.py)
  L171-182), reading `ts_event, open, high, low, close, volume,
  unadjusted_close, pit_provisional`.
- **Features:** import `apply_registered_exclusions`, `aggregate_5min`,
  `compute_emissions`, `exclusion_windows_from_provenance`,
  `MAX_FEATURE_LOOKBACK_BARS`, `pit_canary_future_mutation` from
  [regime_emissions.py](../../src/skie_universe2/features/regime_emissions.py).
  `unadjusted_close` is threaded through as the §step-5 notional reference price
  for the cost model (same passthrough contract H900 uses, CODE-2-1).
- **Windows/embargo:** `h900_windows()` +
  `politis_white_block_length(...,"stationary")` from
  [inference/bootstrap.py](../../src/skie_universe2/inference/bootstrap.py), exactly
  as H001 does (L313-327).
- **Conditioning covariates:** for a regime-conditioned candidate (H103), the
  `cov_regime_state_h900` column is produced by the registered 4-state diag HMM
  causal filter — reuse H001's fit+warm-started-filter block
  ([run_h001_covariate_study.py](../../scripts/run_h001_covariate_study.py)
  L329-337) verbatim; register the column in
  [config/covariates.yaml](../../config/covariates.yaml) under the expert family
  at design freeze (candidate spec already in
  [config/conditioning_covariates.yaml](../../config/conditioning_covariates.yaml)
  `regime_hmm_h900`). Honor the ADR-0001-D5 covariate-not-gate constraint and the
  `detection_cost_caveat` (budget realistic unsupervised switch latency, not the
  CUSUM oracle).
- **Cost:** `FuturesRtV1CostModel.from_config(paths.config / "instruments.yaml")`.
- **Writer:** `ShadowLedgerWriter().write_partitions(...)`.

## 4. Reproducibility (ADR-0008)

- **ReproLog:** emitted automatically by `write_partitions` (13-field, per batch,
  `run_id` = journaled batch id, partition `frame_sha256` in
  `dataset_checksums`). The driver additionally emits a top-level ReproLog for
  the run as a whole (design.md SHA in `config_resolved_sha256`), matching the
  H900/H001 "ReproLog FIRST" idiom
  ([run_h900_dwell_study.py](../../scripts/run_h900_dwell_study.py) L967-980).
- **PIT canary on the feature→signal chain (ADR-0008 D1).** Two gates: (a) the
  existing `pit_canary_future_mutation` on the feature pipeline (features before
  a cut invariant to mutation of bars after it); (b) a **new signal-layer canary**
  — assert `signal(bars[:t]) == signal(bars)[:t]` (prefix-invariance of the
  emitted signal series), the supervised analogue the writer's look-ahead note
  makes the producer's obligation. This is the interface-contract precondition
  (§5 OD-1) for any expert entering the ledger; wire it as an integration-test
  gate in the driver before the first write, mirroring the H900 canary gate.
- **Determinism / seed:** single registered `SEED` (RNG only via
  `np.random.default_rng(SEED)`; per-window restart seeds `SEED+i` where a model
  refit is involved, as in H900). No wall-clock in any numeric path. `rng_seed`
  is a required (non-defaulted) argument to `write_partitions`.
- **No look-ahead:** guaranteed structurally by the (t → t+1) accrual pairing
  (§2 step 4), trailing-only features, training-window-only standardization
  moments, causal filter with purge+embargo at refit boundaries, and the two
  canaries.
- **Burned-data ledger (ADR-0008 D5):** the backfill *materializes* counterfactual
  evidence; it does not itself consume an OOS span for a confirmation decision, so
  it does not burn spans. Downstream admission scans reading the ledger do — they
  update [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml)
  per ADR-0004 window, not this driver.

## 5. Sequencing / milestones and OPEN DECISIONS for operator input

**Milestones:**

1. **M0 — Expert-interface contract (OD-1).** Freeze a `Protocol`/ABC:
   `features_t → signal_t` returning a per-bar (direction, strength) series with
   the prefix-invariance canary as an admission precondition. Adapt the existing
   `meta_shift` signal to it as the reference implementation.
2. **M1 — Tier-0 execution helper.** Build + unit-test
   `execution/tier0_barclose.py` (bar-close counterfactual return + turnover-scaled
   `futures_rt_v1` drag). Analytic/reference-value tests against hand-computed
   single-bar returns.
3. **M2 — Driver + smoke expert.** `scripts/run_shadow_ledger_backfill.py` runs
   `meta_shift_sma3_std3_v1` × {ES,NQ} × 4 Kelly fractions end-to-end on a short
   date slice (`--max-windows`), both canaries green, ledger partitions written +
   read-back-validated. This proves the assembly before any admission candidate.
4. **M3 — Retro candidates (H101, H103).** Freeze each candidate's design.md
   (`/preregister`), register its `cov_*` set in `config/covariates.yaml`, backfill
   full 2015-2025 ES/NQ × 4 fractions.
5. **M4 — Audit.** Run the `audit-remediate-loop` on the driver + first ledger
   output (quant-auditor + reproducibility-verifier + code-reviewer) before the
   backfill is declared evidence-eligible.

**Open decisions needing operator input:**

- **OD-1 (expert-interface contract).** Exact signature of the pluggable expert
  (`features_t → signal_t`), how trained-component refit is expressed per
  rolling window, and whether the contract is a `Protocol` or ABC. Blocks M0.
- **OD-2 (symbol/date scope).** Confirm first-pass = ES + NQ, 2015-2025, primary
  exclusion variant only (vs also inclusive variant, vs waiting for
  `P1-2.0-DATABENTO-DEC-ROLL-REPULL` to repair the `DEC_ROLL_LATE_COMMIT`
  substrate defect — the December-roll windows are currently *excluded*, not
  *corrected*, [config/data_sources.yaml](../../config/data_sources.yaml)). MES/MNQ
  and the ADR-0002 universe extension are out of first-pass scope.
- **OD-3 (machine-raw store / re-ingest).** Confirm the backfill reads the
  existing `data/processed/vendor_legacy_1min_roll_adjusted/` and does **not**
  re-materialize from `~/datasets/` (ADR-0011: processed→processed). If the
  operator wants the ledger to terminate its provenance chain at raw, that is a
  separate re-ingest run, not this driver.
- **OD-4 (signal/target persistence).** Ledger `cov_*` columns are reserved for
  ADR-0002(b) conditioning covariates; recommend carrying signal_strength /
  target_position as a gitignored `data/interim/` attribution sidecar rather than
  polluting the frozen ledger schema. Operator to confirm.
- **OD-5 (incremental re-run / correction policy).** The ledger is append-only;
  the writer refuses existing partitions and requires `deprecate` + a new
  `expert_id@version` for corrections (ADR-0003 D3). Confirm the operational
  cadence: is the backfill a single full run, or incremental per-window appends
  (session_date partitioning supports either)? A code change to an expert = a
  version bump = a full re-backfill of that family into new partitions, old ones
  deprecated (not overwritten). Confirm this is the intended correction workflow.
- **OD-6 (Kelly-fraction materialization).** Confirm all four fractions are
  backfilled as separate `expert_id`s now (selection deferred), consistent with
  the two BLOCKING Kelly memos gating any geometric-growth fraction selection
  (CLAUDE.md). This inflates partition count 4× per expert — acceptable given
  Tier-0 cost and the append-only requirement.
```
