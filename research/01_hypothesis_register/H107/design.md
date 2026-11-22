---
name: H107 — Session-VWAP × EMA(N) crossover grid (ES/NQ, 5-min, 22h window), shadow-ledger screen
description: Pre-registered design doc for hypothesis H107 (principal-proposed practitioner intraday trend rule; EMA span a registered grid)
type: project
hypothesis_id: H107
tier: 2
status: designed  # designed | running | evaluated | archived(positive|null|negative)
owner: SKIE
created: 2026-11-22
citations: 10.1016/j.jfineco.2018.05.009, 10.1111/j.1468-0262.2005.00615.x, 10.1080/01621459.1994.10476870, 10.3905/jpm.2014.40.5.094, 10.21314/JCF.2016.322
external_doi: null
---

# H107 — Session-VWAP × EMA(N) crossover grid (ES/NQ, 5-min, 22h window)

Pre-registration record for the principal-proposed strategy (2026-11-22:
"VWAP + 9 EMA crossover on the 5 min time frame"), with the principal's
specification decisions of the same day:

1. **EMA period is grid-searched** (§4) — every grid point is a registered
   trial; no point is hand-picked.
2. **Trading window:** flat at 15:00 CT, reopen at 17:00 CT; 24-hour trading
   otherwise; Sunday 17:00 CT open (CME futures hours) (§4). Times are read as
   Central Time because "Sundays 1700 open (futures hours)" is the CME Globex
   Sunday open, which is 17:00 CT (18:00 ET).
3. **No regime bias in this hypothesis.** A bull/bear/range bias layer is a
   separately pre-registered SUCCESSOR hypothesis, designed after this screen
   (§1, "Registered successor").
4. **Platform = NinjaTrader:** the `ninjatrader_v1` cost schedule for ES, NQ,
   MES, MNQ is registered (§7).

Two objects are pre-registered (the H105/H106 shape): (A) the H107 expert
grid ([vwap_ema_cross.py](../../../src/skie_universe2/experts/vwap_ema_cross.py))
backfilled to the shadow ledger (ADR-0003); (B) the **RC-H107-1** ADR-0014
singleton SCREEN at the ENACTED level, read from
[config/multipletest_family.yaml](../../../config/multipletest_family.yaml) at
runtime. Frozen at `designed`; any change after freeze requires a new HID.

**Governance blocks respected by construction.** Kelly-fraction selection is
BLOCKED (Phase-4 champion action) — all four fractions materialized, none
selected. EMA-span selection is likewise NOT performed at the screen: every
grid point that passes enters the pool; choosing among them is a
verdict-tier action reported with its PBO. A screen pass disposes
`pool-hold-reconsider` and STOPS — VERDICT entry is a separate, named
operator authorization (VERDICT-1 precedent).

## 1. Hypothesis

- **H0:** for every registered EMA span N and both instruments, the
  stop-and-reverse position sign(EMA_N − session VWAP) over the 22h trading
  window has no positive pre-cost per-session edge at the enacted
  Romano-Wolf-corrected level, or no grid point survives (S-d)/(S-e).
- **H1:** ∃ (N, instrument) passing (S-c) AND (S-d) AND (S-e) — a persistent
  gross edge admitting H107 to the provisional candidate pool.
- **Mechanism (Tier 2 — practitioner rule, weak direct evidence).** An
  intraday time-series-momentum filter: EMA_N above the session's
  volume-weighted mean price means recent prices trade above the session's
  average cost basis. Nearest peer-reviewed support: intraday momentum in
  the S&P 500 ETF —
  [Gao, Han, Li & Zhou 2018, J. Financ. Econ. 129(2):394-414](https://doi.org/10.1016/j.jfineco.2018.05.009)
  (first-half-hour return predicts last-half-hour return; stronger on
  high-volatility days). That evidence concerns one specific within-day
  horizon, not a VWAP/EMA crossing rule; no peer-reviewed source for this
  exact rule is registered (practitioner VWAP-trend write-ups are not cited
  as support). Citation Crossref verification: PENDING (standing
  `CITE-DOI-VERIFY` convention; does not gate the screen).
- **A-priori expectations (registered before any scan):**
  1. **Cost-dominated.** A 5-minute stop-and-reverse crossover whipsaws
     around VWAP in range-bound periods: several reversals per session are
     expected, more for small N. The SCREEN is on gross edge; net binds at
     the VERDICT — the H106 "net-not-monetizable" failure mode is the modal
     expected outcome, worst for MES/MNQ (fees ≈ 3× an E-mini's per $ of
     notional, §7).
  2. **Small-N spans are noise-dominated.** EMA_3/EMA_5 track price within a
     bar or two, so the rule degenerates toward sign(price − VWAP) with
     maximal turnover.
  3. **Redundancy.** H107 is in the market ~22h/session, so its accrual rows
     overlap every pool member (ORB RTH rows, H105 overnight rows, H106
     whole-session rows). It cannot supply a disjoint coverage vector;
     marginal log-wealth growth vs the incumbent set is the binding
     verdict-tier question.
- **Registered successor (regime bias), declared now.** The principal
  intends a follow-up hypothesis that partitions time into
  bullish / bearish / range periods and restricts H107 to long-only /
  short-only / flat accordingly. Binding constraints declared here so the
  successor cannot launder H107's multiplicity:
  (a) it is a NEW HID with its own frozen design, registered BEFORE any
  regime-conditioned H107 statistic is computed (the RC-H107-1 artifact
  reports no regime split, by construction);
  (b) its regime labels must be ex-ante computable (rule-based causal with a
  stated observation lag; latent-state/HMM labels fail S-e outright per the
  `P1-2.0-H900-BOCPD-WHITENED` verdict; full-sample cutoffs are the
  convicted construction class — per-origin train-window CDFs only);
  (c) it re-uses H107's burned windows, which the burned-data ledger records,
  and its trials add to the cumulative DSR count (H107's 14 included);
  (d) it inherits H107's EMA grid only if it pre-declares how one or more
  spans are chosen without looking at regime-conditioned results.

## 2. Universe and sample period

- **Instruments:** ES and NQ continuous roll-adjusted 5-minute substrate
  (`vendor_legacy_1min_roll_adjusted`, the registered H900 §2 grid and
  exclusion filter — the backfill driver's `_load_valid_bars`), identical to
  H105/H106. **MES and MNQ** are evaluated on their parent's ledger (ES/NQ):
  same underlying index and price path at 1/10 the multiplier, so the gross
  edge is identical by construction and only the per-notional cost differs
  (§7). No separate micro substrate is ingested.
- **Sample:** the full backfilled span (2015 → substrate end 2025-12);
  screen evidence = the registered h900 rolling-window family (§6).
  Conditional-grade: the December-roll blind spot (DEC_ROLL_LATE_COMMIT) is
  declared; the DR-1/DR-2 repaired substrate is the prerequisite for
  confirmation-grade evidence.

## 3. Features and conditioning set

- **No conditioning cells.** The S-c family is the EMA-span grid (§4/§5),
  not a cell partition; each grid point's "cell" is every session of its own
  ledger stream. # justify: principal direction — regime conditioning is
  the registered successor (§1), not part of H107.
- **(S-e):** every grid point is a rule-based causal expert with
  observation lag 0 → S-e definitionally satisfied (reported, not
  discriminating; H105 §3 statement applies verbatim).
- **`cov_*` registration:** family `vwap_ema_cross` in
  [config/covariates.yaml](../../../config/covariates.yaml) with
  `covariates: []` (no ledger covariate columns).

## 4. Signal construction

Exactly as implemented in
[vwap_ema_cross.py](../../../src/skie_universe2/experts/vwap_ema_cross.py)
(tests [test_vwap_ema_cross_expert.py](../../../tests/test_vwap_ema_cross_expert.py)):

1. **EMA_N** of the 5-min close, alpha = 2/(N+1), run continuously over the
   contiguous stored bar sequence (charting-platform convention), seeded at
   the first close.
2. **EMA span grid (registered):** N ∈ {3, 5, 9, 13, 21, 34, 55} (7 points).
   # justify: log-spaced (~1.6× ratio, Fibonacci-like) spans covering 15 min
   to ~4.6 h of 5-min bars, containing the principal-specified 9 (the
   PRIMARY grid point, used only for the S-c block length and the §8
   exhibits — it has no privileged gate). A wider/denser grid adds trials
   for every candidate's DSR count; 7 points span the plausible range at
   ~1.6× resolution.
3. **VWAP:** CME-trading-session-anchored: cumulative
   Σ(typical·volume)/Σ(volume), typical = (H+L+C)/3, over every bar of the
   current CME session (session opens 17:00 CT = 18:00 ET; Sunday's 17:00 CT
   open starts Monday's session), reset at each session boundary. Bars in
   the flat window still enter the VWAP (it is a market statistic, not a
   position statistic).
4. **Direction** = sign(EMA_N − VWAP) at every decision bar inside the
   trading window; 0 on ties or undefined VWAP (zero cumulative session
   volume). Always-in inside the window (stop-and-reverse: each crossover
   reverses the position).
5. **Trading window:** decisions only on NY-local labels outside
   [15:55, 18:00) ET. Under Tier-0 accrual (a position decided at close(t)
   earns (t, t+1]) the last held label 15:50 ET earns to 16:00 ET = **15:00
   CT (flat)**, and the first new position is decided at the close of the
   18:00 ET = **17:00 CT reopen** bar. Weekends follow from the same rule
   (flat Friday 15:00 CT → Sunday 17:00 CT). Held decision labels per
   session: 263 (18:00 → 15:50 ET labels, 21 h 55 min; audit-measured).
6. **Strength** 1.0 on held bars. No stop-loss / target / time-stop (each
   would be a swept dimension adding trials; not registered).
7. **Documented limitation (ORB/H106 precedent; pre-freeze audit
   finding 3, verified by execution):** holiday early-close sessions
   (~9/yr) are not special-cased (no exchange holiday calendar in-repo).
   Because the last bar before an early halt (e.g. 13:15 ET) lies INSIDE the
   trading window, the held position accrues the full gap to the next
   reopen, booked to the next session's `session_date` — and the worst
   cases (Black Friday, Christmas Eve, July 3) span a whole weekend or
   holiday. Weekends, ordinary daily halts and December exclusion windows
   are clean (their last pre-gap bar is in the flat window). These gap
   sessions are a known contaminant of the gross series: the screen
   artifact does not exclude them; a holiday-calendar flatten is a
   registered follow-up and would require a new HID.
8. **VWAP is built from VALID bars only (audit finding 4).** The substrate
   pipeline drops the 288-bar emission warm-up after each December
   exclusion window and at series start, and excludes `pit_provisional`
   1-min bars; in those sessions the VWAP anchor starts mid-session or has
   holes. Documented, not corrected (the expert sees exactly what the
   ledger backfill feeds it).

**PIT:** EMA is a causal recursion; VWAP a causal cumulative sum within the
session; the window is a function of the bar's own timestamp. Enforced by the
prefix-invariance canary for every grid point before any ledger write
(backfill driver) and again at screen time (S-a).

## 5. Estimator — ledger backfill + RC-H107-1 screen

- **(A) Backfill (ADR-0003, Tier 0).** 7 spans × {ES, NQ} × the registered
  Kelly sweep {0.5, 0.75, 1.0, 1.25} → expert ids
  `vwap_ema{N}_cross_k{f}@1.0.0` (56 ledger streams), via
  `scripts/run_shadow_ledger_backfill.py --expert h107` (bars loaded once per
  instrument, every span signalled on the same substrate): signal → Layer-2
  Kelly sizing → Tier-0 bar-close execution + `futures_rt_v1` cost →
  append-only `ShadowLedgerWriter`.
- **(B) RC-H107-1 screen** (`scripts/run_screen_h107.py`; statistics in
  [grid_screen.py](../../../src/skie_universe2/screening/grid_screen.py),
  which reuses the packaged spine's public helpers). On the k1.0 ledgers
  (unit exposure), per instrument, build the T × 7 panel of per-session
  gross log-returns (inner join on session_date across the 7 spans):
  - **(S-a)** expert-contract compliance + prefix-invariance canary for all
    7 spans on the last 5,000 valid bars of the substrate.
  - **(S-c)** Romano-Wolf StepM over the 7 grid columns per instrument —
    the frozen PANEL estimator `romano_wolf_stepm_panel` (VERDICT-1;
    rows resampled jointly, cross-span dependence preserved), stationary
    bootstrap (Politis & Romano 1994) with the Politis-White block length of
    the primary (EMA_9) column, 1,000 replicates, seed 20261122; PASS iff
    mean gross > 0 AND adjusted p < the enacted level.
  - **(S-d)** DSR ≥ 1 − level (Bailey & López de Prado 2014; HAC n_eff;
    n_trials_gate and dispersion per §8) AND PBO ≤ level, PBO = CSCV
    (Bailey et al. 2017; S = 16 contiguous row-blocks) on the T × 7 grid
    matrix — exactly the probability that the in-sample-best span
    underperforms the median span out of sample; one PBO per instrument,
    shared by its 7 grid points.
  - **(S-e)** lag-0 rule-based → pass (reported).
  - Per-window growth (15 registered windows) reported per grid point.
- **Appends (ADR-0008 D5/D6), named implementing path:**
  `scripts/emit_screen_expert_card_v1.py --hid H107` appends the 14
  per-grid-point trial records to `rc-h107-1`, the per-window burned spans
  under `hid: H107`, the script-generated Expert Card v1, and (on PASS)
  **one pool-record set (4 Kelly fractions) per passing grid point**, each
  keyed to that grid point's own ledger id (`ledger_slice` suffix
  `:grid=emaN`) — so no span is selected at the screen (audit finding 1).
- **Resumable backfill:** an (expert, instrument) whose 4 Kelly streams
  already exist is skipped; a partial set aborts for operator inspection
  (append-only ledger; audit finding 2).
- **What the screen does NOT do:** no span selection, no rotor, no set-level
  verdict, no non-redundancy test, no Kelly selection, no regime split.

## 6. Splitter

H900 rolling-origin family by reference (`eval/windows.py::h900_windows()`:
24-month train / 6-month step / first origin 2017-01-01, 15 windows × 2
instruments). The rule is stateless (no fit). The S-c/S-d statistics use the
full joined session panel (the RC-*-2 / H105 construction) — **including the
2015-2016 sessions before the first origin**, which the burned-data mirror
(15 eval windows) does not record; a gap inherited from H105/H106 and
disclosed here (audit). The windows enter as the per-window growth exhibit
and the burned-data mirror. Purge 288
bars (`MAX_FEATURE_LOOKBACK_BARS`); embargo Politis-White (H900 §6).

## 7. Cost model

- **Ledger (unchanged, append-only):** `futures_rt_v1`
  ([config/instruments.yaml](../../../config/instruments.yaml)) —
  `ret_net` in the ledger.
- **Registered NinjaTrader schedule `ninjatrader_v1`**
  ([config/cost_schedules/ninjatrader_v1.yaml](../../../config/cost_schedules/ninjatrader_v1.yaml)),
  binding for any H107 verdict-tier net claim; DESCRIPTIVE at the screen.
  All-in per side (commission + exchange/NFA + clearing; NinjaTrader table
  as of 2026-08-14): ES/NQ Free $2.87, Monthly $2.57, Lifetime $2.17;
  MES/MNQ Free $0.94, Monthly $0.84, Lifetime $0.64. Slippage per side:
  central ES/MES 0.5 tick, NQ/MNQ 1.0 tick; pessimistic ES/MES 1.5, NQ/MNQ
  2.0 ticks. Per the ADR-0016 swept-assumption rule, a net claim must
  survive the pessimistic endpoint.
- **Net columns (12 per grid point per instrument):** {E-mini, micro} ×
  {free, monthly, lifetime} × {central, pessimistic}. Per-session turnover
  is recovered EXACTLY from the ledger, turnover = (gross − net) /
  per-unit `futures_rt_v1` drag (Tier-0 net is linear in turnover;
  verified on a synthetic ledger in
  [test_run_screen_h107.py](../../../tests/test_run_screen_h107.py)); variant
  net = gross − turnover × that variant's per-unit notional drag at the same
  median reference price.
- Fixed costs (platform $99/mo or $1,499 lifetime; CME L1 data $12/mo
  bundle) are not per-trade drag and are excluded from the per-session net.

## 8. Gate thresholds

- Level, DSR bound and PBO bound read at runtime from
  `config/multipletest_family.yaml` (`screening_error_rate_target`; never
  transcribed).
- **n_trials_gate = 87** (frozen): the register's 73 recorded trials at
  freeze (h900 1; rc-h101-2 10; rc-h103-2 10; rc-h105-1 10; rc-h106-1 10;
  first-admission-verdict 32) + this scan's 14 (7 spans × 2 instruments).
  The correlation-adjusted effective count (mean pairwise grid correlation)
  is reported alongside, not substituted.
- **Dispersion surface:** recorded non-`unconditional` trial Sharpes of
  rc-h101-2, rc-h103-2, rc-h105-1, rc-h106-1 (32; fail-closed if any family
  is empty) + the 14 current grid Sharpes. Stated plainly (audit finding 6):
  this surface omits the h900 and first-admission-verdict records that ARE
  in the 87 count, so count and dispersion are not on an identical surface;
  the larger count with the narrower dispersion is the conservative
  direction for DSR. The correlation-adjusted effective count
  (`n_eff_corr_adjusted_reported`, from the mean pairwise grid correlation)
  is reported per instrument, never substituted.
- **Turnover recovery (audit finding 9):** exact given the backfill's
  reference price, which the screen recomputes from the substrate; the
  ReproLog binds the substrate checksums, so a substrate change between
  backfill and screen is detectable (re-run both if it occurs).
- §8 exhibit: KPSS on the primary (EMA_9) column per instrument.

## 9. Stopping rule

Single pre-registered scan over the full grid. No re-scan with a modified
grid, window or rule under this HID.

## 10. Decision rule (ADR-0014 dispositions)

- ≥ 1 grid point passes S-a…S-e → `screen-pass` → `pool-hold-reconsider`
  (4 pool records, one per Kelly fraction, keyed to the head passing grid
  point's ledger id; all passing points listed). VERDICT entry requires a
  named operator authorization.
- S-c passes somewhere but S-d fails → `archive-no-persistent-window`.
- No S-c pass → `archive-no-persistent-window (archive-no-gross-edge)`.
- Every disposition emits the ADR-0009 Expert Card ("fail" is not a
  disposition). Net columns are reported in every case.

## 11. Reproducibility and run sequence (data machine)

```bash
uv sync --all-extras
uv run pytest tests/test_vwap_ema_cross_expert.py tests/test_grid_screen.py tests/test_run_screen_h107.py
uv run python scripts/run_shadow_ledger_backfill.py --smoke --expert h107 --instruments ES
uv run python scripts/run_shadow_ledger_backfill.py --expert h107          # canonical ledger
uv run python scripts/run_screen_h107.py                                     # reports/H107/rc_h107_1_screen.json
uv run python scripts/emit_screen_expert_card_v1.py --hid H107               # register + burned + card (+ pool)
```

13-field ReproLog per run (the screen binds the substrate checksums, a
digest over each of the 7 grid ledgers' partition hashes, this design's
SHA-256, the register config and the cost schedule). Design SHA recorded in
the backlog at freeze.

## 12. Mechanism distinctness and expected overlap

- vs **ORB (H101/H103):** same trend-following sign class over RTH; H107's
  RTH rows ⊇ ORB's accrual hours → high realized-bar overlap and positive
  return correlation expected on breakout days.
- vs **H105 overnight drift:** H107 is in the market through the overnight
  segment (H105's rows) with a SIGNED position; overlap in rows is total
  over 18:00–09:30 ET, correlation sign undetermined.
- vs **H106 VR range reversal:** opposite mechanism (momentum vs one-bar
  contrarian) on overlapping rows — the only pool member H107 could
  plausibly diversify (negative correlation expected in range states).
- Consequence: H107 cannot help the ADR-0015/0017 coverage-disjointness
  precondition; its case rests entirely on marginal growth at the verdict.
  **Label caveat (audit finding 8):** grid cell labels (`ES:ema5`, …) look
  label-disjoint from every pool member to the label-based
  `check_verdict_precondition.py`; that label count is NOT evidence of
  disjoint coverage for H107 — the ADR-0017 realized-bar overlap report
  governs.

## 13. Execution layer

Tier 0, market-at-bar-close fills. No limit-order or scalping claim is
reportable below Tier 2 (ADR-0006/ADR-0016). NinjaTrader live execution is
NOT modelled beyond the §7 cost schedule; ADR-0010 live-vs-shadow tracking
governs any future live use.
