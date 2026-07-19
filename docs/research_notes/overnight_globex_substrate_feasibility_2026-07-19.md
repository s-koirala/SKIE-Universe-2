# Overnight/Globex substrate feasibility check (P3-A)

*Run date: 2026-07-19.*

**Feasibility record (of record; not a frozen design.md).** Executes the two
pre-registration feasibility gates for the overnight/Globex forward expert —
the first mechanism in the operator-ratified Phase-3 sourcing priority
([program_roadmap_2026-07-17.md](program_roadmap_2026-07-17.md) Phase 3;
[od_g setup plan](od_g_spread_liquidity_setup_plan_2026-07-18.md) §3 rank 1,
§7 open item "Overnight/Globex substrate check"). No hypothesis design.md is
frozen, no ledger partition is written, no trial-register family is
incremented, and no OOS span is consumed by this check (coverage
characterization only; no signal is evaluated).

- **Harness:** [scripts/run_overnight_substrate_check.py](../../scripts/run_overnight_substrate_check.py)
- **Result artifact:** [reports/P3A_overnight_substrate/overnight_substrate_check.json](../../reports/P3A_overnight_substrate/overnight_substrate_check.json)
- **ReproLog:** `logs/reproducibility/repro_log_5e370d881cbe4f289c21ea596bc07449.json`
  (run `5e370d881cbe`, the round-1-remediated re-run — bit-identical
  statistics to the initial run `45ce4594e92b`; dataset checksum = the
  provenance `output_frame_sha256` `3ae9cc03dfc2…`)
- **Substrate:** `data/processed/vendor_legacy_1min_roll_adjusted` (ADR-0011),
  primary exclusion variant (`pit_provisional` + `coverage_gaps` excluded) via
  the same `apply_registered_exclusions` path every study harness uses.

## 1. Question 1 — ETH-bars check: **PASS (GO)**

**The roll-adjusted store carries the full CME Globex (ETH) session; it is not
RTH-filtered.** Post-exclusion, on the 5-minute evidence grid (H900 §3
aggregation rule reused verbatim from the backfill driver):

| Quantity (per CME session) | ES | NQ |
|---|---|---|
| Sessions (post-exclusion) | 2,449 | 2,450 |
| Overnight-ETH 5-min bars — median [p05, p95] | 186 [186, 186] | 186 [185, 186] |
| RTH 5-min bars — median [p05, p95] | 78 [78, 78] | 78 [78, 78] |
| Post-RTH ETH 5-min bars — median | 9 | 9 |
| Sessions with ≥1 overnight-ETH bar | 2,448 / 2,449 | 2,449 / 2,450 |
| Total overnight-ETH 5-min bars | 452,433 | 451,431 |

The overnight-ETH segment (local ≥ 18:00 prior day or < 09:30
America/New_York, within the CME session assigned by the shared
`cme_session_date_expr` rule) shows **exactly the theoretical full-coverage
count**: 15.5 h × 12 bars/h = 186 five-minute bars, at the median AND both
tail quantiles. The 1-minute substrate shows the same structure (930-minute
overnight segment; hour-17 local carries only 2,521 ES / 2,286 NQ residual
1-minute bars across 228 ES / 196 NQ sessions — holiday/early-close
schedule variants, recorded as `halt_anomaly`, <0.1% of post-exclusion rows;
562 ES / 526 NQ bars on the 5-minute grid). Session segments are
bar-disjoint from
the 78-bar RTH window **by construction** — the disjointness basis the
ADR-0015 precondition needs, established before any scan (setup plan §3
rank-1 argument, now verified on the store).

**Consequence for the backfill path:** the canonical ledger loader
(`run_shadow_ledger_backfill.py::_load_valid_bars`) applies **no RTH
filter** — ETH bars already flow through exclusions → 5-min aggregation →
H900 emissions → `emission_valid`. An overnight expert needs **no new
substrate materialization**: it is a new `Expert` implementation over the
identical valid-bar stream (ADR-0003 counterfactual completeness: the ORB
expert simply held direction 0 on these bars).

## 2. Question 2 — December/Globex blind spot (declared-blind-spot input)

Quantified from the provenance `coverage_gaps` register (22 entries, defect
`DEC_ROLL_LATE_COMMIT`) against the store's actual CME session dates. The
registered exclusions remove, **per instrument**:

| Year (window start) | Window | ES sessions | ES 1-min bars (overnight-ETH) | NQ sessions | NQ 1-min bars (overnight-ETH) |
|---|---|---|---|---|---|
| 2015 | 2015-12-08 → 2016-01-04 | 10 | 12,982 (9,068) | 10 | 11,117 (7,260) |
| 2016 | 2016-12-08 → 2017-01-03 | 8 | 10,033 (6,992) | 8 | 8,422 (5,420) |
| 2017 | 2017-12-08 → 2018-01-02 | 7 | 8,588 (5,979) | 7 | 7,768 (5,185) |
| 2018 | 2018-12-08 → 2019-01-02 | 10 | 12,343 (8,428) | 10 | 12,309 (8,394) |
| 2019 | 2019-12-08 → 2020-01-02 | 11 | 13,545 (9,199) | 11 | 13,601 (9,254) |
| 2020 | 2020-12-08 → 2021-01-04 | 10 | 12,999 (9,086) | 10 | 12,818 (8,909) |
| 2021 | 2021-12-08 → 2022-01-03 | 9 | 11,909 (8,309) | 9 | 11,756 (8,158) |
| 2022 | 2022-12-08 → 2023-01-03 | 8 | 10,483 (7,335) | 8 | 10,423 (7,276) |
| 2023 | 2023-12-08 → 2024-01-02 | 7 | 8,273 (5,575) | 7 | 8,262 (5,563) |
| 2024 | 2024-12-08 → 2025-01-02 | 11 | 13,807 (9,307) | 11 | 13,825 (9,327) |
| 2025 terminal | 2025-12-08 → end of sample | **0** | 0 (0) | **10** | 12,872 (8,825) |
| **Total** | | **91 (3.32%)** | **114,962 (79,278)** | **101 (3.66%)** | **123,173 (83,571)** |

(Session shares are of the 2,745 ES / 2,756 NQ pre-exclusion sessions in the
processed store.)

Three facts the design.md must state verbatim:

1. **The blind spot is structurally non-random and lands hardest on this
   mechanism.** The same mid-December → early-January window is removed every
   year, and **69.0% (ES) / 67.8% (NQ) of every excluded bar is an
   overnight-ETH bar** (79,278 of 114,962 ES; 83,571 of 123,173 NQ) — the
   roll's volume crossover happens in Globex sessions (cost sheet §2.1.4).
   Year-end overnight behaviour is unobservable to this project until
   DR-1/DR-2.
2. **The processed evidence substrate ends 2025-12-03 (ES) / 2025-12-05
   (NQ)** (UTC bar-dates; the final ES bar at 23:59 UTC belongs to CME
   session 2025-12-04 under the session-date rule — the convention behind
   the JSON's "sample ends 2025-12-04" annotation). The ES 2025 raw file
   truncates at 2025-12-03 (registered
   asymmetry, cost sheet §2.1.2), so the ES terminal-window exclusion removes
   **zero** further sessions from the processed store; NQ loses 10
   (2025-12-08 → 2025-12-19). The cost sheet's larger terminal-tail figures
   (115 ES / 126 NQ bar-dates through 2026-05) are **raw-store** losses: the
   2026H1 raw extension has never been materialized into the roll-adjusted
   derivative (ingest ran with `--end 2025-12-31`), so recovery of that tail
   requires DR-2 **plus** a re-materialization, not exclusion-lifting alone.
3. **The `pit_provisional` exclusion removes a further ~200 full sessions per
   instrument** (291,959 ES / 289,587 NQ 1-min bars; quarterly roll-resolution
   windows under the persistence guard). This is not December-specific and is
   shared by every existing screen (H101/H103 precedent) — it is recorded here
   so the overnight design's session count (≈ 2,449/2,450) is derived, not
   assumed.

**Rule of record (operator-ratified 2026-07-19, carried unchanged):** a
**conditional-grade** overnight screen runs NOW on the exclusion-filtered
substrate with this blind spot declared in the design; **DR-1/DR-2 is
prerequisite only for December-inclusive or confirmation-grade overnight
evidence** ([cost sheet](databento_pull_spec_cost_sheet_2026-07-18.md)
§2.1.4/§5(c); [setup plan](od_g_spread_liquidity_setup_plan_2026-07-18.md) §3
rank 1, audit finding QUANT-1-4 reconciliation).

## 3. Verdict

**P3-A gate: GO.** ETH bars are present at full-session coverage on both
instruments; the December/Globex blind spot is quantified and declarable; the
existing backfill/screen machinery consumes the substrate unchanged. The
overnight/Globex expert proceeds to `/hypothesis-new` → `/preregister` with
§2 of this note as the declared-blind-spot section input. STOP condition
("ETH bars absent → substrate acquisition is operator ground") did **not**
trigger.

## 4. Limitations

- Segment classification uses fixed NY-local exchange constants
  (`[09:30, 16:00)` RTH; 18:00 reopen); holiday early-close sessions appear
  as reduced post-RTH/halt counts (228 ES / 196 NQ sessions carry
  `halt_anomaly` bars) and are not separately modeled here — the expert design must be robust to
  short sessions (it will see them as fewer overnight bars, p05 = 185–186
  shows the effect is negligible at the 5-min grid).
- Session dates use the shared `cme_session_date_expr` rule, which does not
  advance weekend/holiday boundaries; the store shows no weekend-stub session
  inflation (2,449 sessions ≈ 11 × ~250 trading days, minus exclusions).
- Bar counts here are coverage quantities only; nothing in this check
  measures edge, and none of its numbers may be quoted as evidence of one.
