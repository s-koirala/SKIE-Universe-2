# Databento data-pull specification and cost-estimation sheet

**Living planning note (of record; not a frozen design.md).**

*Last updated: 2026-07-18.*

No hypothesis design.md is frozen, no ledger partition is written, and **no
vendor order is placed** on the strength of this document. Its sole purpose is
to make every outstanding vendor-data request **precise enough that the operator
can obtain a quote** — dataset code, schema, symbol set, date range, and a
derived volume estimate per line item.

> **PRICING DISCLAIMER (binding on this document).** Every price cell in this
> sheet is `TBD — operator to quote`. No dollar figure, per-GB rate, credit
> cost, or license-tier price appears anywhere in this note, and none may be
> added by an agent. Databento bills **per byte consumed** and the byte count
> depends on dataset × schema × symbol count × date range × license tier, none
> of which this repo can price. The quoting mechanism is the operator running
> `Historical.metadata.get_billable_size` and `Historical.metadata.get_cost`
> against the exact request parameters tabulated in §4
> ([get_cost](https://databento.com/docs/api-reference-historical/metadata/metadata-get-cost),
> [get_billable_size](https://databento.com/docs/api-reference-historical/metadata/metadata-get-billable-size),
> [metered pricing](https://databento.com/docs/api-reference-historical/basics/metered-pricing)).

Governing ADRs:
[ADR-0011](../decisions/ADR-0011-two-level-data-storage-and-provenance-policy.md)
(two-level storage + upstream registry),
[ADR-0006](../decisions/ADR-0006-execution-fidelity-tiers.md) (execution
tiers), [ADR-0003](../decisions/ADR-0003-shadow-ledger-canonical-object.md)
(shadow ledger), [ADR-0008](../decisions/ADR-0008-integrity-non-negotiables.md)
(integrity). Tactical context:
[backfill_admission_plan_2026-07-17.md](backfill_admission_plan_2026-07-17.md)
§5 (OD-B, OD-C, OD-D, OD-G),
[program_roadmap_2026-07-17.md](program_roadmap_2026-07-17.md).

---

## 0. Verification status of vendor facts asserted here

| Fact | Status | Basis |
|---|---|---|
| Dataset code `GLBX.MDP3` = CME Globex MDP 3.0 | **verified** | [databento.com/datasets/GLBX.MDP3](https://databento.com/datasets/GLBX.MDP3) (direct fetch) |
| Schema `mbo` (market-by-order, full order-book replay, tick-by-tick with full depth) exists on GLBX.MDP3 | **verified** | same page (direct fetch) |
| Schema `mbp-10` (market-by-price, 10 depth levels) exists on GLBX.MDP3 | **verified** (2026-07-19) | dataset-page schema list (MBO, MBP-1, MBP-10, TBBO, Trades, OHLCV-*) fetched during the round-1 argument audit |
| Schema `ohlcv-1m` | **verified** (2026-07-19) | dataset-page schema list (audit fetch), corroborated by this repo's own vendor chain string in [config/data_sources.yaml](../../config/data_sources.yaml) and the raw files on disk |
| GLBX.MDP3 history begins **2010-06-06** | **verified** (2026-07-19) | dataset-page JSON-LD `temporalCoverage: 2010-06-06/..` (audit fetch); not load-bearing — every priced row spans ≥ 2015 |
| Extended pre-`2017-05-21` GLBX history is MDP2-era with reduced schema availability (status schema unavailable) | **confirmed in direction (2026-07-19); exact cutoff OPEN** | dataset page: "Since March 2017, MDP 3.0 has changed from providing aggregated depth at every price level … to providing full granularity of every order event" — order-level (MBO-quality) data does not exist before ~2017-03. Date discrepancy (page: March 2017; this row's carried figure: 2017-05-21) is for the operator to pin with the vendor. **The material risk for any MBO pull covering 2015–2017 stands** |
| Billing is per byte consumed | **verified (indirect)** | Databento metered-pricing doc title/snippet; exact rates deliberately not recorded |

Everything in §1–§3 that is derived from **repo/store data** is marked
`[derived]` with its derivation; those figures are reproducible from the paths
cited and are not vendor assertions.

---

## 1. Category 1 — Tier-2 tick data (new capability)

### 1.1 Why this exists, and its governance status

[ADR-0006](../decisions/ADR-0006-execution-fidelity-tiers.md) Decision 2 makes
limit-order, interbar-entry, and scalping-hold-time claims **unreportable below
Tier 2**. No Tier-2 substrate exists in this project. The live consequence is
recorded as **OD-G** in
[backfill_admission_plan_2026-07-17.md](backfill_admission_plan_2026-07-17.md)
§5: an operator-approved forward mechanism direction (spread/liquidity-regime)
cannot be screened in its native form, only as a Tier-0 directional expert that
*conditions* on a spread covariate while taking liquidity at bar close. H104's
limit-fill-at-wick semantic (§4.3 of the same note) is the second blocked
claim class.

> **Ordering of record (updated 2026-07-19).** This sheet was drafted
> 2026-07-18 *before* ADR-0016 was drafted later the same day; the original
> note here ("ADR-0016 does not exist as of 2026-07-18") was true at drafting
> and is preserved in git history.
> [ADR-0016](../decisions/ADR-0016-tier2-execution-fidelity-scoping.md) now
> exists and is **accepted (2026-07-19, stage A only — no spend authorized;
> stage B requires its own named, dated operator authorization)**. The staged
> A→D structure below originated here as a proposal and is now governed by
> ADR-0016 Decision 6 — **where wording differs, the ADR governs** (audit
> finding QUANT-1-5).

### 1.2 MBO vs MBP-10 — the concrete trade-off

Both schemas describe the same book; they differ in whether **individual orders
retain identity**.

- **`mbp-10`** (market-by-price, 10 levels) publishes the book *aggregated per
  price level*: at each level you get price, aggregate resting size, and the
  order count. You can see that 400 contracts sit at the best bid across 12
  orders. You **cannot** see where a hypothetical order of yours would sit in
  that queue, because the individual orders that compose the 400 are not
  distinguishable and their arrival order is not recoverable.
- **`mbo`** (market-by-order) publishes every individual order event with an
  order ID — add, modify, cancel, trade. The full queue at each price is
  reconstructible in arrival order, so a simulated order's **queue position**
  and its evolution (how much size ahead of it cancels vs trades) is directly
  computable. This is precisely the quantity ADR-0006 Tier 2 names ("queue
  position model for limit orders").

Consequence for the fill model: a limit order at the best bid fills only when
the queue ahead of it clears. With MBP-10 you must *model* that clearing with
an assumption (e.g. proportional/FIFO-approximate depletion of aggregate size);
with MBO you can *measure* it. The adverse-selection asymmetry ADR-0006 warns
about — that the fills most readily granted are the ones where the market blew
through the level — is exactly the regime where an MBP-10-derived queue proxy
is least reliable, because cancellations ahead of you concentrate there.

MBO is also **the most expensive schema per unit time** on this venue (every
order event, not one snapshot per level per change). Buying MBO across two
instruments for a decade is a terabyte-scale, open-ended purchase — see §1.5.

### 1.3 The staged approach, and why it bounds the purchase

The staged structure converts "buy a decade of MBO and hope the queue model
works" into a sequence of small, individually-refusable decisions:

| Stage | Question it answers | Vendor spend |
|---|---|---|
| **A** | Scope + ADR: fix the fill-model class, data strategy, reportability delta, overfitting guard, and validation criteria (ADR-0016 Decision 6 stage A). **DONE — ADR-0016 accepted 2026-07-19** | none (repo work) |
| **B** | Does an **MBP-10-derived** queue proxy reproduce **MBO** ground-truth queue position and fill outcomes closely enough to be usable? (bounded validation pull — the FIRST and ONLY spend decision at this stage) | **small, bounded** (this sheet, row T2-B) |
| **C** | Given B's answer, does the queue model pass the pre-fixed validation criteria — ADR-0016 D5 **(V-a)** MBO cross-validation under the externally pre-registered bound-generating rule + **(V-b)** stylized-fact reproduction + the ADR-0008 PIT canary? (Live-fill reconciliation is a **standing re-validation condition** per V-c, *not* a stage-C gate: it withholds confirmation-grade under the ADR-0006 Obligation but cannot gate a build that precedes live capital — stage-table mirrored to the ADR 2026-07-19, audit finding QUANT-1-5) | none (repo work) |
| **D** | Broad substrate purchase at the schema B proved sufficient | **large; contingent on B and C** (rows T2-D1…D4) |

The decision B buys is worth far more than B costs: **if MBP-10 reproduces MBO
well enough, stage D can be bought in `mbp-10` instead of `mbo`**, which is the
single largest cost lever in this entire sheet. If it does not, D is bought in
`mbo` with the failure quantified rather than assumed, or the Tier-2 programme
is abandoned with a bounded loss.

### 1.4 Stage B — bounded validation pull (specification)

- **Dataset:** `GLBX.MDP3`
- **Schemas:** `mbo` **and** `mbp-10` over the **identical window and symbol**
  (both are required; the whole point is the cross-validation)
- **Symbol:** **ES front month only.** ES is the most liquid instrument in the
  registered universe, which makes it the *hardest* case for a queue proxy
  (deepest queues, most cancellation churn) and therefore the conservative
  validation target. Adding NQ at stage B buys a second draw from the same
  mechanism at roughly double the cost; defer it to stage D.
- **Proposed span: two blocks of 5 consecutive CME sessions = 10 sessions
  total — PROVISIONAL pending the ADR-0016 Decision-5 validation-power
  specification** (D6 stage B: span/symbols/size pre-registered against it;
  the structural arguments below justify ≥ 5 sessions per block and ≥ 2
  blocks, not the specific total — audit finding QUANT-1-9).

**Justification of the length (and why it is 10 and not "a day" or "a month"):**

1. **5 consecutive sessions = one full Mon–Fri cycle.** Intraday liquidity and
   cancellation intensity have a day-of-week component; a single session cannot
   separate queue-model error from day-of-week composition. One complete weekly
   cycle is the minimum window over which the proxy error can be reported with
   a day-of-week breakdown.
2. **Two blocks, not one, because the queue proxy's failure mode is
   regime-dependent.** Aggregate-size depletion behaves differently when
   cancellation dominates (calm) than when trades dominate (stress) — the exact
   asymmetry §1.2 identifies. A single-regime validation would certify the proxy
   on the regime where it is easiest.
3. **Block selection is rule-based, not hand-picked** (CLAUDE.md: zero
   arbitrary thresholds). The two blocks are selected **from the existing
   1-minute substrate before the pull** by the registered regime machinery:
   block 1 = a 5-session run in the **calm/non-stress** state, block 2 = a
   5-session run in the **stress** state, per the registered H900 4-state HMM
   stationary stress occupancy already used as the ADR-0002 conditioning
   covariate ([config/conditioning_covariates.yaml](../../config/conditioning_covariates.yaml);
   ES stress occupancy p̂ ≈ 0.19 per RC-H103-1). The selection script is a
   prerequisite deliverable of stage B and its output dates go into the design
   record before the order is placed.
4. **Mandatory exclusions on both blocks:** no block may overlap a registered
   `DEC_ROLL_LATE_COMMIT` window (§2.1), a contract-roll week, or a
   `pit_provisional=true` span; and **every block must lie at or after the
   confirmed GLBX order-level-granularity date (~2017-03; vendor page "Since
   March 2017" — operator to pin the exact cutoff, §0)**, since a block
   outside that span has no MBO ground truth and voids the validation
   purpose of the pull (audit finding QUANT-1-14). This keeps stage B
   independent of the defect repair in §2.
5. **The total session count is an OUTPUT of the stage-B validation-power
   specification (ADR-0016 D5/D6), not a derived bound.** The stage-B estimand
   is a *within-session* fill/queue-error distribution with thousands of order
   events per session; it is not a low-frequency return statistic needing
   years of history. Precision on the proxy-error distribution is governed by
   event count, not calendar span — which bounds the answer in sessions rather
   than months; the specific total awaits the power specification, with 10 the
   provisional planning figure *(reworded 2026-07-19 — the prior "upper bound
   on what the decision needs" claim carried no power computation; audit
   findings QUANT-1-9 / QUANT-2-3)*.

**Exact dates: deliberately not fixed in this note.** They are the output of the
rule in (3) run at pull time, so that the window is selected by a registered
criterion rather than by an author's recollection of which weeks were volatile.
For pricing, run `metadata.get_billable_size` on **two rule-selected candidate
blocks — one calm, one stress — separately** and report both: event (hence
byte) volume plausibly differs by regime, which is the very premise of the
two-block design, so a single "any 10 sessions" quote could under-price the
stress block. Stage-B pricing is quotable before the final dates are fixed,
using candidate blocks from the rule in (3). *(Reworded 2026-07-19: the prior
"any 10 sessions / byte count insensitive within a regime" instruction rested
on an in-repo-unverifiable claim — audit finding QUANT-1-9.)*

**Volume estimate:** **NOT DERIVABLE FROM THIS REPO.** The repo holds no
tick-level data of any kind — only `ohlcv-1m` (§2.2) — so there is no basis
here for an MBO or MBP-10 record count or byte count, and none is asserted.
`metadata.get_billable_size` on the exact parameters above is the correct
source and is cheap to call.

### 1.5 Stage D — broad pull (contingent on stage C succeeding)

Priced as **alternatives, not a sequence** — the operator picks one after stage
B tells them which schema is sufficient.

| Tier | Schema | Symbols | Span | Notes |
|---|---|---|---|---|
| **T2-D1** | `mbp-10` | ES | 2023-01-01 → 2025-12-31 (3 yr) | Cheapest viable Tier-2 substrate. Only valid if stage B clears the proxy. Matches the span where the existing 1-min store is contiguous |
| **T2-D2** | `mbp-10` | ES, NQ | 2023-01-01 → 2025-12-31 | Both registered instruments; enables the per-instrument robustness the project requires everywhere else (RC-H103-1 precedent) |
| **T2-D3** | `mbp-10` | ES, NQ | 2015-01-01 → 2025-12-31 (11 yr) | Full alignment with the existing 1-min substrate span. Carries the **confirmed-in-direction** MDP2-era caveat (exact cutoff OPEN, ~2017-03 vs 2017-05-21) for the 2015–~2017 portion (§0) |
| **T2-D4** | `mbo` | ES | 2023-01-01 → 2025-12-31 | Fallback if stage B refutes the MBP-10 proxy. Order-level ground truth, single instrument, shortest span |

> **Terabyte-scale warning (explicit).** `mbo` over the **full 2015–2025 span
> for both ES and NQ** — every add/modify/cancel/trade event on the two most
> actively quoted futures on CME Globex for eleven years — is a
> **terabyte-scale** purchase and is deliberately **not offered as a priced
> option** in this sheet. It should not be requested without stage B, stage C,
> and a written statement of which specific claim requires it. It also carries a
> non-trivial storage obligation on the machine-level store, which currently
> holds ≈1.7 GB total [derived: `du -sh ~/datasets/vendor_skie_ninja_legacy/raw_1min/`].

---

## 2. Category 2 — the held backlog

### 2.1 `P1-2.0-DATABENTO-DEC-ROLL-REPULL` — the December-roll repair (PRIMARY)

**Status: held since 2026-07-10. Severity `critical` in the registry. This is a
defect in the substrate every existing result in this project already rests on.**

#### 2.1.1 The defect

From [config/data_sources.yaml](../../config/data_sources.yaml),
`substrate_defects[0]`, id `DEC_ROLL_LATE_COMMIT`, severity `critical`,
confirmed 2026-07-10 (round-1 audit QUANT-1-1): the per-year ES/NQ raw files
contain **only same-year-expiry contracts**, so the December volume crossover
into the next year's H (March) contract is invisible until the next year's file
begins. Every Z→H roll 2016–2025 therefore commits at the **first January
session**, ~3 weeks after the true mid-December crossover (equity-index roll convention — volume
migrates ~8 calendar days before last trade; the registry's "CME guidance"
attribution is unpinned, an official CME source is to be recorded at repair
registration — audit finding LITERATURE-1-4). The registry is explicit that the
1.0 bit-exact benchmark match therefore demonstrates **port fidelity, not
substrate correctness**, and that the defect must **not** be patched in code.

**[derived] The defect is confirmed independently in the store, and it is total,
not partial.** Scanning December bars for next-year expiries across every ES/NQ
file in `~/datasets/vendor_skie_ninja_legacy/raw_1min/`:

- `ES_2020_1min_databento.csv` ends at `2020-12-18 14:29` on `ESZ0` — the file
  stops at the Z last-trade, and no `ESH1` bar exists anywhere in it.
- The multi-year undated files, which might have been expected to escape the
  sharding, do **not**: `ES_1min_databento.csv` (spanning 2023-01-02 →
  2024-12-19) contains in December **only** `ESZ3` (2023-12) and `ESZ4`
  (2024-12); `NQ_1min_databento.csv` likewise only `NQZ3` / `NQZ4`. **Zero H
  contract bars exist in any December, in any ES/NQ file in the store.**

**[derived] The defect is specific to the ES/NQ year-sharded pull pattern and
is structurally avoidable.** The MGC and SIL files were pulled as single
continuous multi-year requests and **do** carry next-expiry contracts in
December: `MGC_1min_databento.csv` December-2023 top symbols are `MGCG4`,
`MGCJ4`, `MGCG4-MGCJ4` (Feb/Apr-2024 expiries and their spread);
`SIL_1min_databento.csv` December-2023 top symbols are `SILH4`, `SILF4`,
`SILF4-SILH4`. **Recommendation: place the repair as one continuous
multi-year request per symbol, not as per-year requests** — the sharding, not
the vendor, is the cause.

#### 2.1.2 Affected boundaries, exact windows, symbols [derived]

The authoritative machine-readable register is
`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260711.json`,
field `coverage_gaps` — **22 entries**: 10 `late_committed_roll` events per
instrument (ES, NQ) plus 1 `terminal_window` event per instrument.

| # | Boundary | Symbol | Old → new contract | Registered defect window (`expected_crossover_window`) | Committed roll date (wrong) |
|---|---|---|---|---|---|
| 1 | 2015/16 | ES | ESZ5_2015 → ESH6_2016 | 2015-12-08 .. 2016-01-04 | 2016-01-04 |
| 2 | 2016/17 | ES | ESZ6_2016 → ESH7_2017 | 2016-12-08 .. 2017-01-03 | 2017-01-03 |
| 3 | 2017/18 | ES | ESZ7_2017 → ESH8_2018 | 2017-12-08 .. 2018-01-02 | 2018-01-02 |
| 4 | 2018/19 | ES | ESZ8_2018 → ESH9_2019 | 2018-12-08 .. 2019-01-02 | 2019-01-02 |
| 5 | 2019/20 | ES | ESZ9_2019 → ESH0_2020 | 2019-12-08 .. 2020-01-02 | 2020-01-02 |
| 6 | 2020/21 | ES | ESZ0_2020 → ESH1_2021 | 2020-12-08 .. 2021-01-04 | 2021-01-04 |
| 7 | 2021/22 | ES | ESZ1_2021 → ESH2_2022 | 2021-12-08 .. 2022-01-03 | 2022-01-03 |
| 8 | 2022/23 | ES | ESZ2_2022 → ESH3_2023 | 2022-12-08 .. 2023-01-03 | 2023-01-03 |
| 9 | 2023/24 | ES | ESZ3_2023 → ESH4_2024 | 2023-12-08 .. 2024-01-02 | 2024-01-02 |
| 10 | 2024/25 | ES | ESZ4_2024 → ESH5_2025 | 2024-12-08 .. 2025-01-02 | 2025-01-02 |
| 11 | 2025/26 | ES | ESZ5_2025 → (unobserved) | 2025-12-08 .. *terminal window; ES sample ends 2025-12-04* | never committed |
| 12–22 | same 11 boundaries | NQ | NQZ5_2015 → NQH6_2016 … NQZ5_2025 → (unobserved) | identical dates to rows 1–11 | identical to rows 1–11 |

**Count: 10 affected year-boundaries per instrument × 2 instruments = 20
late-committed rolls, plus 2 terminal-window events (Dec 2025) = 22 registered
gaps.**

**Pull windows (registry-mandated minimum: Dec 01 → Jan 15 around each year
boundary, all affected symbols):**

| Boundary | Pull window | Calendar days | Store-present bar-dates today (Dec 01–31 / Jan 01–15) | Dark span between last Dec bar and first Jan bar (calendar days) |
|---|---|---|---|---|
| 2015/16 | 2015-12-01 → 2016-01-15 | 46 | ES 16 / 12; NQ 16 / 12 | 15 (last 2015-12-18 → first 2016-01-03) |
| 2016/17 | 2016-12-01 → 2017-01-15 | 46 | 14 / 12 (both) | 16 (2016-12-16 → 2017-01-02) |
| 2017/18 | 2017-12-01 → 2018-01-15 | 46 | 13 / 13 (both) | 16 (2017-12-15 → 2018-01-01) |
| 2018/19 | 2018-12-01 → 2019-01-15 | 46 | 16 / 13 (both) | 12 (2018-12-19 → 2019-01-01) |
| 2019/20 | 2019-12-01 → 2020-01-15 | 46 | 17 / 13 (both) | 12 (2019-12-19 → 2020-01-01) |
| 2020/21 | 2020-12-01 → 2021-01-15 | 46 | 16 / 12 (both) | 15 (2020-12-18 → 2021-01-03) |
| 2021/22 | 2021-12-01 → 2022-01-15 | 46 | 15 / 12 (both) | 15 (2021-12-17 → 2022-01-02) |
| 2022/23 | 2022-12-01 → 2023-01-15 | 46 | 14 / 12 (both) | 16 (2022-12-16 → 2023-01-02) |
| 2023/24 | 2023-12-01 → 2024-01-15 | 46 | 12 / 13 (both) | 17 (2023-12-14 → 2024-01-01) |
| 2024/25 | 2024-12-01 → 2025-01-15 | 46 | 17 / 13 (both) | 12 (2024-12-19 → 2025-01-01) |
| *2025/26 (optional 11th)* | 2025-12-01 → 2026-01-15 | 46 | **ES 3** / 13; NQ 17 / 13 | **ES 28** (2025-12-03 → 2026-01-01); NQ 12 |

All bar-date counts and dark spans `[derived]` by scanning `ts_event` dates in
the raw CSVs. Dates are UTC bar-dates as stored (the Sunday-evening Globex open
carries the Sunday date), not CME session dates — the two differ by the
session-date rule applied downstream.

**Additional [derived] defect surfaced while deriving this table, not in the
registry:** `ES_2025_1min_databento.csv` terminates at **2025-12-03**, whereas
`NQ_2025_1min_databento.csv` runs to **2025-12-19**. ES is missing ~16
bar-dates of December 2025 that NQ has, independent of the roll defect. Any
2025/26 repull must therefore cover ES from 2025-12-04, and this asymmetry
should be added to the registry's defect block.

- **Symbols to request:** ES and NQ, **and critically the next-year H contract
  in each window** — i.e. for boundary Y/Y+1 the request must resolve `ESZ{Y}`,
  `ESH{Y+1}`, `NQZ{Y}`, `NQH{Y+1}` **and the Z–H calendar spread** (the store's
  MGC/SIL precedent shows Databento returns spread symbols such as
  `MGCG4-MGCJ4` in the same pull; the roll-detection logic consumes outright
  volume, but the spread rows arrive with the request and count toward billed
  bytes). Requesting by raw symbol alone reproduces the defect; the request must
  use a parent/continuous resolution that returns all active expiries in the
  window.
- **Schema:** `ohlcv-1m` — matching the existing store exactly
  ([config/data_sources.yaml](../../config/data_sources.yaml) vendor chain
  `Databento GLBX.MDP3 ohlcv-1m -> per-symbol/per-year CSV`). No higher schema
  is needed for the repair; the defect is contract attribution, not intrabar
  detail.

#### 2.1.3 Volume estimate [derived, with stated assumptions]

Basis, all derived from the current store:

- Mean bar-dates in a complete 31-day month (ES 2019–2021, months 01/03/05/07/08/10):
  **26.44**. Measured Jan 01–15 bar-dates: **12–13**. So one Dec 01 → Jan 15
  window ≈ **38–39 bar-dates**, vs 46 calendar days.
- December `ohlcv-1m` rows per bar-date in the current (single-front-contract)
  store: **ES 1,131**, **NQ 1,098**; bytes per bar-date **ES 84.9 KB**,
  **NQ 84.4 KB** (≈78 bytes/row CSV).

Derivation for the 10-boundary, 2-instrument request:

- Instrument-windows: 10 × 2 = **20**; instrument-bar-dates: 20 × 38.5 ≈ **770**
- Single-contract-equivalent rows: 770 × ~1,115 ≈ **860 k rows** ≈ **67 MB CSV**
- **Assumption (flagged, not derived):** a corrected pull returns the Z and H
  outrights plus their calendar spread simultaneously, so multiply by **2–3×**
  → **≈ 1.7–2.6 M `ohlcv-1m` rows ≈ 130–200 MB CSV**.
- Compression reference `[derived]`: MGC CSV 432,368,327 B vs its `.dbn.zst`
  69,103,919 B ⇒ **≈ 0.16×**, so the same request in DBN/Zstd ≈ **21–32 MB**.
- Including the optional 11th boundary: 22 instrument-windows → 847
  instrument-bar-dates, scale the above by 1.10×.

This is a **small** pull by any measure — roughly a tenth of the existing
1.7 GB store — which is the strongest argument for doing it first.

#### 2.1.4 Why this is load-bearing, and what the exclusion silently costs

**The defect is currently mitigated by EXCLUSION, not by CORRECTION.** The
provenance record marks the substrate `evidence_bar_eligible: "conditional"`
with condition `DEC_ROLL_LATE_COMMIT`: *"Evidence over those windows is not
confirmation-grade until the re-pull follow-up P1-2.0-DATABENTO-DEC-ROLL-REPULL
lands."* Every study harness in the repo implements that condition by dropping
the windows —
[run_h001_covariate_study.py](../../scripts/run_h001_covariate_study.py),
[run_h900_dwell_study.py](../../scripts/run_h900_dwell_study.py),
[run_rc_h101_1_scan.py](../../scripts/run_rc_h101_1_scan.py),
[run_rc_h103_1_scan.py](../../scripts/run_rc_h103_1_scan.py) all call
`apply_registered_exclusions(..., exclude_coverage_gaps=True)`
([features/regime_emissions.py](../../src/skie_universe2/features/regime_emissions.py)).

**[derived] What that costs, in bar-dates dropped from every derivative:**

| Exclusion class | ES | NQ |
|---|---|---|
| 10 December-roll windows (2015/16 … 2024/25) | **110** bar-dates | **110** bar-dates |
| Terminal window (2025-12-08 → end of sample, open-ended `date.max`) | **115** bar-dates | **126** bar-dates |
| Total excluded | **225** | **236** |
| Substrate 2015–2025 bar-dates present | 3,293 | 3,307 |
| December-roll exclusion as share of the 2015–2025 substrate | **3.34 %** | **3.33 %** |

Three consequences, stated plainly:

1. **It silently costs coverage in every study.** ~3.3 % of every instrument's
   history is removed from the H001 covariate study, the H900 dwell study, the
   RC-H101/H103 screens, and the shadow ledger. It is not a random 3.3 % — it is
   the **same calendar window every year**, so year-end effects are structurally
   unobservable to this project.
2. **The whole post-2025-12-08 tail is gone too.** The terminal-window entries
   are open-ended through `date.max`, so 115 ES / 126 NQ bar-dates covering
   2025-12-08 → 2026-05-14 (the 2026H1 extension) are excluded as well. The
   effective usable sample ends in early December 2025 despite the store
   reaching May 2026.
3. **It is load-bearing for any overnight/Globex mechanism.** The roll happens
   *overnight* — the volume crossover into the H contract occurs in Globex
   sessions, not the RTH open. "Overnight/Globex" is one of the four
   operator-approved forward mechanism directions
   ([backfill_admission_plan_2026-07-17.md](backfill_admission_plan_2026-07-17.md)
   §3), and it is the direction most likely to satisfy the ADR-0015
   non-overlapping-coverage precondition that currently blocks the set-level
   verdict. A mechanism whose competence window is the overnight session cannot
   be screened **December-inclusively or at confirmation grade** on a
   substrate whose overnight contract attribution is misassigned for three
   weeks a year and whose repair windows are dropped; a conditional-grade
   screen on the exclusion-filtered substrate remains possible with the blind
   spot declared in the design (§5(c)). **The
   repair is a plausible prerequisite of the Phase-3 critical path, not a
   housekeeping item.**

### 2.2 `P1-2.0-ROLL-SYMBOL-EXPAND` — **NOT a vendor purchase** [derived]

Registered in
[docs/audits/audit_trail_2026-07-10_phaseC-substrate-shadow-ledger.md](../audits/audit_trail_2026-07-10_phaseC-substrate-shadow-ledger.md)
as: *"Materialize MCL/MGC/SIL — blocked on QUANT-3-2 terminal-rule
generalization."*

**The data is already on disk. This item requires zero vendor spend.** Verified
in `~/datasets/vendor_skie_ninja_legacy/raw_1min/`:

| Symbol | File | Size | Coverage `[derived from first/last ts_event]` |
|---|---|---|---|
| MGC | `MGC_1min_databento.csv` (+ `.dbn.zst`) | 432.4 MB (69.1 MB zst) | 2015-01-01 → 2025-12-30 |
| MGC | `MGC_2026H1_1min_databento.csv` | 38.5 MB | 2026-01-01 → 2026-05-14 |
| SIL | `SIL_1min_databento.csv` (+ `.dbn.zst`) | 197.5 MB (30.6 MB zst) | 2015-01-01 → 2025-12-30 |
| SIL | `SIL_2026H1_1min_databento.csv` | 30.4 MB | 2026-01-01 → 2026-05-14 |
| MCL | `MCL_1min_databento.csv` (+ `.dbn.zst`) | 266.9 MB (45.0 MB zst) | 2021-07-11 → 2025-12-30 |

Blocker is **QUANT-3-2**: the terminal-window roll rule encodes the
equity-index quarterly calendar and must be generalized per-instrument before
these symbols can be materialized. That is repo work, not spend. **This row
appears in the cost sheet at cost `n/a — no purchase required`, solely to stop
it being mistaken for a held purchase.**

### 2.3 OD-B — MES/MNQ micro siblings (**a genuinely new purchase**)

**OD-B as written** in
[backfill_admission_plan_2026-07-17.md](backfill_admission_plan_2026-07-17.md)
§5: *"RC-H103-1 proposed ES+NQ+MES+MNQ pooling to reach n ≥ 174 stress-cell
trades; confirm the micro siblings are in the intended universe (RC-H103-1 ran
ES+NQ only)."*

**[derived] The stated justification does not survive checking against
RC-H103-1, and this must be resolved before the purchase is priced.** The
disposition
([RC-H103-1](../reports/H103/RC-H103-1_admission_disposition_2026-07-16.md) §3.8)
records: *"Both stress cells exceed the n≥174 ES-anchor sample-size floor (ES
437, NQ 481)."* The n ≥ 174 floor is **already met on ES and NQ alone**. The
pooling proposal itself IS on the tracked record — the RC-H103-1 scan spec in
[retro_card_register_2026-07-10.md](retro_card_register_2026-07-10.md) reads
*"Pooled ES + NQ + MES + MNQ pre-cost ORB scan … accumulated on the shadow
ledger to n ≥ 174 stress-cell trades"*, and
[H103/design.md](../../research/01_hypothesis_register/H103/design.md) carries
*"the micro contracts (MES/MNQ, retro card §3) remain candidate additions
deferred to a later operator decision"* — but the **as-executed** RC-H103-1
met the floor on ES+NQ alone, so the pooling rationale is **obsolete rather
than absent**. §3.8 further notes the per-instrument floor re-derivation is a
*deferred, certified-run* step and that the estimate is imprecise *regardless of
n* — so more sample is not the binding constraint RC-H103-1 identified.
*(Corrected 2026-07-19: the prior sentence "MES and MNQ appear nowhere in the
tracked repo (the only hits are in an untracked local brief)" was false —
audit finding QUANT-1-10.)*

The defensible justification for buying MES/MNQ is therefore **instrument
breadth / rolling-origin robustness across symbols** (the stated rationale of
`P1-2.0-ROLL-SYMBOL-EXPAND` in
[session_handoff_2026-07-12.md](session_handoff_2026-07-12.md) §6.6), **not**
reaching a sample-size floor. Two caveats the operator should weigh before
spending:

- MES/MNQ are **micro contracts on the same underlying indices as ES/NQ**. They
  are near-perfectly correlated with their full-size siblings, so they add
  almost nothing on the ADR-0002(d) / ADR-0014-verdict non-redundancy axis and
  **cannot** supply the non-overlapping coverage vector that ADR-0015 requires.
  They buy execution-scale realism (smaller tick value, different queue
  dynamics, different retail flow mix), not diversification.
- MES/MNQ launched in **May 2019**, so no 2015–2018 history exists at any price;
  a pull can only cover ~2019→present. *(Launch date asserted from general
  knowledge — **UNVERIFIED**; operator should confirm the first available date
  via `metadata` before quoting a start date.)*

**Specification if purchased:** `GLBX.MDP3`, schema `ohlcv-1m`, symbols MES +
MNQ, span 2019 (first available) → 2025-12-31, as a **single continuous
multi-year request per symbol** (the MGC/SIL pattern) so it does not inherit
`DEC_ROLL_LATE_COMMIT`. **[derived] volume estimate:** at the ES/NQ store rate of
≈85 KB/bar-date and ≈305 bar-dates/yr, ~7 years × 2 symbols ≈ 4,270
instrument-bar-dates ≈ **360 MB CSV / ≈ 58 MB DBN-zst**, before any
multi-expiry multiplier.

### 2.4 OD-C / H104 — MGC and SIL: **the data is already in the raw store** [derived — checked, not assumed]

**Checked directly, as instructed.** `config/data_sources.yaml` →
`vendor_skie_ninja_legacy_raw_1min.symbols` = `[ES, NQ, MCL, MGC, SIL]`, and
`coverage_note` states *"MCL/MGC/SIL full-history CSV + .dbn.zst."* Verified on
disk against the file listing in §2.2: **MGC and SIL are present, full history
2015-01-01 → 2025-12-30 plus a 2026H1 extension, in both CSV and `.dbn.zst`
form.**

**Therefore: H104's blocker is NOT missing data.** No MGC/SIL purchase is
required, and none appears in the cost sheet. H104's actual blockers, per
[backfill_admission_plan_2026-07-17.md](backfill_admission_plan_2026-07-17.md)
§4.3, are:

1. **RC-H104-3 integrity closure — hard-blocking before any scan:** PIT-canary
   suite, ReproLog wire, limit-fill-at-wick semantics, MPPM CI, walk-forward
   inner CV, v1↔v2 reconciliation.
2. **Universe registration:** MGC/SIL sit outside the frozen §2 universe, so
   H104 requires a **fresh admission cycle** with its own trial-register entry
   covering the 5-config × 4-symbol sweep, the ~5-month window extension, and
   the universe extension.
3. **A Tier-2 dependency (links back to §1):** the limit-fill-at-wick semantic
   is a Tier-2 claim class under ADR-0006 and is unreportable until a Tier-2
   substrate exists. H104 is therefore the *second* consumer of the §1 purchase
   — though note stage B/D as specified are **ES-only**; an H104 Tier-2 claim
   would need MGC/SIL tick data, which is **not** specified or priced here.
4. **QUANT-3-2** terminal-rule generalization (§2.2) gates materialization.

### 2.5 Other held data items found in the repo

| Item | Held? | Vendor spend? | Note |
|---|---|---|---|
| **2023/2024 ES & NQ per-year files** | **[derived] latent gap** | possibly | No `ES_2023/2024` or `NQ_2023/2024` per-year files exist; that span is covered only by the undated `ES_1min_databento.csv` / `NQ_1min_databento.csv` (2023-01-02 → 2024-12-19). Coverage looks continuous, but the naming/provenance is inconsistent with every other year and the registry's `file_pattern`. **Audit before buying anything** — this may be a bookkeeping issue, not a data gap |
| **ES December 2025 truncation** | **[derived] new** | yes (folds into the 2025/26 repull row) | ES ends 2025-12-03 vs NQ 2025-12-19 (§2.1.2) |
| **`P1-2.0-CITE-DOI-VERIFY-PBO-2017`** | closed 2026-07-10 | no | Not a data item |
| **`P1-2.0-RETRO-CARD-1.0-REGISTER`** | open | no | Reads 1.0 reports in place (`skie_universe_1_kpi_reports`, `usable_as_evidence: false`); no data copied, no purchase |
| **`skie_universe_1_processed_roll_adjusted`** | reference-only | no | ADR-0011 Decision 2 forbids cross-repo processed import; benchmark only |
| **Macro-calendar / economic-release data** | **implied, unregistered** | **unknown — likely yes** | "macro-calendar-conditioned" is an operator-approved forward mechanism direction (§3 of the backfill plan) and its pre-registration gate names *"PIT-calendar availability"*. **No calendar source is registered in `config/data_sources.yaml` and none is in the store.** This is a real, unpriced dependency of one of four approved forward directions. It is likely not a Databento product; flagged for the operator to scope separately |

---

## 3. Priority rationale

1. **DEC-roll repair first.** It is the only item that fixes a `critical` defect
   in the substrate **every existing result already rests on**. It is currently
   mitigated by exclusion, which costs 3.3 % of each instrument's history in a
   structurally non-random band plus the entire post-2025-12-08 tail (§2.1.4). It
   is also, by the derivation in §2.1.3, **the smallest pull in this sheet**
   (~130–200 MB CSV, ~21–32 MB compressed). Highest value-per-byte by a wide
   margin, and a plausible prerequisite of the overnight/Globex forward
   mechanism that Phase 3's critical path wants.
2. **Tier-2 stage B second.** New capability, deliberately bounded (10 ES
   sessions), and the decision it buys — MBP-10 sufficiency — determines the
   cost of everything downstream in §1. Buying it *before* the DEC-roll repair
   would be defensible only if OD-G were the binding constraint; it is not,
   because the verdict is under an ADR-0015 hold that only a forward
   disjoint-coverage expert can lift.
3. **MES/MNQ third, and only after §2.3's justification is repaired.** As
   argued, micros cannot satisfy ADR-0015's non-overlapping-coverage
   requirement, and the sample-size rationale on record does not hold up.
4. **Tier-2 stage D last, contingent on B and C.** Any stage-D tier bought
   before B is an unbounded purchase against an unvalidated model.

---

## 4. Consolidated cost sheet

**Every price cell is `TBD — operator to quote` (see the pricing disclaimer at
the head of this note). Quote each row by passing its Dataset / Schema / Symbols
/ Date-range cells to `metadata.get_billable_size` and `metadata.get_cost`.**

| Item | Purpose / what it unblocks | Dataset | Schema | Symbols | Date range | Derivable volume estimate | Priority | Blocking dependency | Est. cost |
|---|---|---|---|---|---|---|---|---|---|
| **DR-1** December-roll repair, core | Repairs `DEC_ROLL_LATE_COMMIT` (`critical`); restores 110 excluded bar-dates/instrument (3.3 % of substrate); makes overnight/Globex mechanisms December-inclusive / confirmation-grade screenable; converts exclusion → correction | `GLBX.MDP3` | `ohlcv-1m` | ES, NQ — Z and next-year H outrights **+ Z–H calendar spread**, via parent/continuous resolution | 10 windows: Dec 01 → Jan 15 across boundaries 2015/16 … 2024/25 (46 cal. days each; ≈38–39 bar-dates each; 20 instrument-windows) | **[derived]** ~860 k single-contract-equivalent rows ≈ 67 MB CSV; ×2–3 for Z+H+spread ⇒ **≈1.7–2.6 M rows, 130–200 MB CSV / 21–32 MB DBN-zst** | **1** | Operator spend auth only (1.0 ADR-0023 precedent). Register the upstream in `config/data_sources.yaml` first (ADR-0011 D3) | **TBD — operator to quote** |
| **DR-2** December-roll repair, 2025/26 boundary + ES tail | Closes the 11th boundary and the **[derived] new** ES-2025 truncation (ES ends 2025-12-03 vs NQ 2025-12-19); recovers the 115 ES / 126 NQ bar-dates currently excluded by the open-ended terminal window | `GLBX.MDP3` | `ohlcv-1m` | ES, NQ (ESZ5/ESH6, NQZ5/NQH6 + spreads) | 2025-12-01 → 2026-01-15 (ES effectively from 2025-12-04) | **[derived]** ≈ 0.10 × DR-1 ⇒ **≈170–260 k rows, 13–20 MB CSV** | **1** (bundle with DR-1) | as DR-1 | **TBD — operator to quote** |
| **T2-B** Tier-2 stage B validation pull | Answers "is `mbp-10` a sufficient Tier-2 substrate?" — the single largest cost lever in this sheet; unblocks OD-G and the ADR-0006 tier-promotion gate | `GLBX.MDP3` | **`mbo` AND `mbp-10`, same window** | ES front month only | 10 CME sessions = 2 × 5-session blocks (one calm, one stress, selected ex-ante by the registered H900 HMM state; excludes roll weeks, DEC-roll windows, `pit_provisional` spans) | **NOT DERIVABLE from this repo** — no tick data present. Use `metadata.get_billable_size` | **2** | Named, dated **stage-B operator authorization** (ADR-0016 accepted 2026-07-19, stage A only — spend NOT yet authorized); block-selection script; ADR-0011 D3 registration before ingest; blocks ≥ ~2017-03 (§0 feed-era constraint) | **TBD — operator to quote** |
| **MX-1** MES/MNQ micro siblings | Instrument-breadth / rolling-origin robustness (OD-B, `P1-2.0-ROLL-SYMBOL-EXPAND` rationale). **Not** a sample-size fix — see §2.3 | `GLBX.MDP3` | `ohlcv-1m` | MES, MNQ | first available (≈2019, **UNVERIFIED**) → 2025-12-31, single continuous request per symbol | **[derived]** ~4,270 instrument-bar-dates × ≈85 KB ⇒ **≈360 MB CSV / ≈58 MB DBN-zst** (before multi-expiry multiplier) | **3** | §2.3 justification must be repaired first; cannot satisfy ADR-0015 coverage precondition | **TBD — operator to quote** |
| **T2-D1** Tier-2 broad, minimal | Cheapest Tier-2 substrate: ES limit-order/queue claims reportable | `GLBX.MDP3` | `mbp-10` | ES | 2023-01-01 → 2025-12-31 | NOT DERIVABLE | **4** | **Contingent on T2-B proving the MBP-10 proxy, and on stage C** | **TBD — operator to quote** |
| **T2-D2** Tier-2 broad, both instruments | Adds NQ → per-instrument robustness at Tier 2 | `GLBX.MDP3` | `mbp-10` | ES, NQ | 2023-01-01 → 2025-12-31 | NOT DERIVABLE | **4** | as T2-D1 | **TBD — operator to quote** |
| **T2-D3** Tier-2 broad, full span | Tier-2 span aligned to the full 1-min substrate | `GLBX.MDP3` | `mbp-10` | ES, NQ | 2015-01-01 → 2025-12-31 | NOT DERIVABLE | **4** | as T2-D1, **plus** the confirmed-in-direction MDP2-era caveat (exact cutoff OPEN, ~2017-03 vs 2017-05-21) for the 2015 → ~2017 span (§0) | **TBD — operator to quote** |
| **T2-D4** Tier-2 broad, order-level fallback | Order-level ground truth if T2-B refutes the MBP-10 proxy | `GLBX.MDP3` | `mbo` | ES | 2023-01-01 → 2025-12-31 | NOT DERIVABLE — **substantially larger than any `mbp-10` row** | **4** | as T2-D1 | **TBD — operator to quote** |
| *(not offered)* MBO, ES+NQ, 2015–2025 | — | `GLBX.MDP3` | `mbo` | ES, NQ | 2015-01-01 → 2025-12-31 | **terabyte-scale** — deliberately not offered; do not request without stages B and C and a written claim justification | — | — | **not quoted by design** |
| **RSE-1** MCL/MGC/SIL materialization (`P1-2.0-ROLL-SYMBOL-EXPAND`) | Extends the universe to metals/energy | *(already in store)* | `ohlcv-1m` | MCL, MGC, SIL | 2015-01-01 → 2026-05-14 (MCL from 2021-07-11) | **[derived]** already on disk: 432/197/267 MB CSV + `.dbn.zst` | — | **QUANT-3-2** terminal-rule generalization (repo work) | **n/a — no purchase required** |
| **H104-DATA** MGC/SIL for H104 | H104 wick-rejection scalp | *(already in store)* | `ohlcv-1m` | MGC, SIL | 2015-01-01 → 2026-05-14 | **[derived]** present, full history, CSV + `.dbn.zst` | — | **NOT a data blocker.** RC-H104-3 integrity closure + universe registration + (for the wick-fill claim) a Tier-2 substrate | **n/a — no purchase required** |
| **CAL-1** PIT macro-economic calendar | Prerequisite of the macro-calendar-conditioned forward mechanism direction; its pre-registration gate names "PIT-calendar availability" | **unregistered — none in `config/data_sources.yaml`** | n/a | n/a | n/a | unknown | **flagged** | Source selection + ADR-0011 registration; likely **not** a Databento product | **TBD — operator to scope, then quote** |

---

## 5. Close-out

### (a) Recommended purchase sequence

1. **DR-1 + DR-2 together, as one order.** Same schema, same instruments,
   adjacent windows; splitting them wastes a request cycle and leaves the
   open-ended terminal-window exclusion in place.
2. **T2-B** (`mbo` + `mbp-10`, ES, 10 sessions provisional) — after the
   block-selection script and the stage-B validation-power specification
   exist, and on the **named, dated stage-B operator authorization**
   (stage-A scoping / ADR ratification: DONE — ADR-0016 accepted 2026-07-19).
3. **Exactly one of T2-D1 … T2-D4** — chosen by T2-B's result, gated on stage C.
4. **MX-1** — only if the §2.3 justification is repaired and the operator still
   wants micro-contract breadth.
5. **CAL-1** — scope the source before quoting; it is probably a different
   vendor entirely.

### (b) What each purchase unblocks

- **DR-1/DR-2** → converts the `critical` substrate defect from *excluded* to
  *corrected*; restores 3.3 % of each instrument's history plus the entire
  post-2025-12-08 tail; removes the December blind spot that makes year-end
  effects unobservable; makes an **overnight/Globex** forward mechanism
  December-inclusive / confirmation-grade screenable — and that is the
  direction most likely to supply the disjoint coverage vector the ADR-0015
  hold requires (a conditional-grade screen can precede the repair, blind spot
  declared — §5(c)). Also flips
  `evidence_bar_eligible` from `conditional` toward unconditional for the first
  time.
- **T2-B** → the MBP-10-sufficiency decision, hence the price of all Tier-2
  work; resolves **OD-G** (whether the spread/liquidity mechanism can be
  screened natively or only as a Tier-0 conditioning form).
- **T2-D*** → the actual Tier-2 substrate; makes limit-order / interbar /
  scalping claims reportable under ADR-0006 D2 for the first time; a
  precondition (in a symbol set not yet specified) of H104's wick-fill claim.
- **MX-1** → cross-symbol rolling-origin robustness; **does not** unblock the
  ADR-0015 verdict precondition.
- **CAL-1** → the macro-calendar-conditioned forward mechanism direction.

### (c) Prerequisite relationships

- **T2-B is a hard prerequisite of every T2-D tier.** Buying stage D first
  converts a bounded purchase back into the open-ended one the staging exists to
  prevent.
- **Stage C (repo work: queue model + its validation gates) sits between B and
  D**; ADR-0006's obligation that the Tier-2 fill model be validated against
  live fills (ADR-0010 tracking) is a *further* gate before Tier-2 output is
  confirmation-grade.
- **DR-1/DR-2 are prerequisites of December-inclusive or confirmation-grade
  overnight/Globex evidence**, and — because the exclusion windows are dropped
  from the shadow ledger itself — of any re-backfill intended to be
  December-complete. A conditional-grade overnight screen CAN run today on the
  exclusion-filtered substrate, with the structurally non-random
  December/Globex blind spot (§2.1.4) declared in the design *(reconciled
  2026-07-19 with the setup plan §3 — audit finding QUANT-1-4)*.
- **QUANT-3-2 (terminal-rule generalization) gates RSE-1 and H104-DATA**; both
  are repo work with zero spend.
- **Nothing gates DR-1.** It is purchasable today, subject only to operator
  authorization.
- **T2-B is gated on the ADR-0016 stage-B authorization** (named, dated,
  operator-only) plus the Decision-7 upstream registration and the
  block-selection script. The former "ADR ratification" gate is satisfied:
  ADR-0016 accepted 2026-07-19, stage A only; tier promotion itself follows
  ADR-0006 D3 as scoped by ADR-0016 Decision 10.

### (d) Operator-only spend and ADR-0011 obligations

**All vendor purchases in this sheet are operator-only.** Precedent: **OD-D**
in [backfill_admission_plan_2026-07-17.md](backfill_admission_plan_2026-07-17.md)
§5 and the registry's own repair note — *"Requires operator-authorized spend
(1.0 ADR-0023 precedent)"* — reinforced by
[session_handoff_2026-07-12.md](session_handoff_2026-07-12.md) §6.6: *"DEC-roll
repull is operator-only vendor spend and stays out of the agent path."* No agent
may place an order, enter payment details, or authorize a download against a
metered account. This note's function ends at producing quotable specifications.

**ADR-0011 obligations, in order, for every purchase above:**

1. **Register the upstream in
   [config/data_sources.yaml](../../config/data_sources.yaml) BEFORE ingest**
   (Decision 3 — *"ingest modules must refuse sources absent from the
   registry"*). A repaired December pull is a **new** source entry (different
   pull pattern, different retrieval date, different coverage), not an edit to
   the existing `vendor_skie_ninja_legacy_raw_1min` block; the existing block's
   `substrate_defects` entry is updated to reference the superseding source
   rather than deleted, so the defect stays in the record. Any Tier-2 purchase
   is a new source entry with its own license-status verification.
2. **Raw files land in the machine-level store `~/datasets/`, never in the
   repo** (Decision 1). Nothing under `data/` is committed except
   `_manifest.json`, `expectations.yaml`, `.gitkeep`, and explicitly declared
   exceptions (Decision 5).
3. **Checksum at retrieval:** every new raw file carries a retrieval-time
   provenance sidecar with its SHA-256 (Decision 4); per-file SHA-256 of
   anything materialized under `data/` goes into `data/_manifest.json` at ingest
   via `scripts/build_data_manifest.py`, with `--check` in CI.
4. **Data flows raw → processed, one direction** (Decision 1). The repaired
   December windows are re-materialized through the in-project ingest module;
   the defect is **not** patched in code — the registry says so explicitly, and
   the repaired substrate must reproduce the roll detection from corrected raw
   inputs.
5. **Re-run the affected derivatives after ingest.** Correcting the substrate
   changes the roll-adjusted bars, hence the shadow ledger (ADR-0003 is
   append-only: a corrected substrate implies new partitions, old ones
   deprecated — OD-F), hence every screen statistic computed on it. The repair
   is not free downstream, and that re-run cost should be weighed alongside the
   vendor quote.
