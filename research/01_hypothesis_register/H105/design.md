---
name: H105 — Overnight/Globex session-drift expert (ES/NQ), shadow-ledger screen
description: Pre-registered design doc for hypothesis H105 (first fresh forward expert of the Phase-3 sourcing priority; the ADR-0015 disjointness candidate)
type: project
hypothesis_id: H105
tier: 3
status: designed  # designed | running | evaluated | archived(positive|null|negative)
owner: SKIE
created: 2026-07-19
citations: 10.1093/rfs/hhad020, 10.1016/j.jfineco.2019.03.011, 10.59576/lse.20260701, 10.1111/j.1468-0262.2005.00615.x, 10.1080/01621459.1994.10476870, 10.1081/ETC-120028836, 10.1080/07474930802459016, 10.3905/jpm.2014.40.5.094, 10.21314/JCF.2016.322, 10.2469/faj.v58.n4.2453, 10.1016/j.jempfin.2008.03.002, 10.1016/0304-4076(92)90104-Y, 10.1198/000313001300339897, 10.2307/2297912
external_doi: null
---

# H105 — Overnight/Globex session-drift expert (ES/NQ), shadow-ledger screen

This document is the pre-registration record for hypothesis H105 — the first
**fresh forward** expert of the operator-ratified Phase-3 sourcing priority
(principal direction 2026-07-19: (1) overnight/Globex, (2) mean-reversion) and
the designated **ADR-0015 disjointness candidate**: its competence window is
**bar-disjoint from the 78-bar RTH ORB session by construction**, which is the
property the ratified pool-HOLD verdict precondition requires (≥ 2 distinct
`expert_hash` values with non-overlapping coverage vectors). It is frozen at
`designed` status; any change after that point requires a new hypothesis ID.

Two objects are pre-registered: (A) the **H105 overnight-drift expert** (a
Layer-1 signal producer conforming to the `Expert` contract) backfilled to the
shadow ledger (ADR-0003), and (B) the **RC-H105-1 screen** — the ADR-0014
singleton SCREEN (S-a…S-e) at the **ENACTED** screening level (read from
[config/multipletest_family.yaml](../../../config/multipletest_family.yaml)
at runtime; never transcribed).

**Governance blocks respected by construction.** Kelly-fraction selection is
BLOCKED (Phase-4 champion action; arsenal ≥ 1 plus the registered
re-instantiation) — all four fractions are materialized, none selected. The
set-level VERDICT is under the ratified ADR-0015 operator HOLD: a screen pass
disposes `pool-hold-reconsider` and STOPS. Meeting the verdict precondition is
REPORTED, never acted on (ADR-0015 Decision 3).

## 1. Hypothesis

- **H0:** the long-overnight position (held over the overnight ETH segment,
  §4) has no positive pre-cost (gross) per-session edge in any pre-declared
  conditioning cell (§3) on either instrument at the enacted ADR-0014 (S-c)
  Romano-Wolf-corrected level, or no cell survives the (S-d) persistence /
  (S-e) selectability gates.
- **H1:** ∃ a conditioning cell on ≥ 1 instrument whose overnight gross edge
  passes (S-c) at the enacted level AND survives (S-d)/(S-e) — a persistent,
  ex-ante-selectable overnight competence window admitting H105 to the
  provisional candidate pool.
- **Mechanism:** the overnight risk premium in equity index futures. E-mini
  S&P 500 futures returns accrue disproportionately overnight, with the drift
  concentrated in specific overnight windows (around the European open),
  documented on 1998–2020 ES futures by
  [Boyarchenko, Larsen & Whelan 2023, Rev. Financ. Stud. 36(9):3502-3547](https://doi.org/10.1093/rfs/hhad020)
  (~3.7%/yr accruing in the 02:00–03:00 ET window alone over their sample;
  mechanism: dealer inventory management after end-of-day order imbalances);
  the overnight-vs-intraday return decomposition (and its cross-sectional
  "tug of war") is documented by
  [Lou, Polk & Skouras 2019, J. Financ. Econ. 134:192-213](https://doi.org/10.1016/j.jfineco.2019.03.011).
- **Pre-registered attenuation expectation (a priori, before any scan):** the
  same authors report the effect **attenuated to ≈ zero in 2021–2025** (the
  02:00–03:00 ET window "averaged close to zero since 2021"; end-of-day
  order-imbalance dispersion compressed by more than half —
  [Boyarchenko, Larsen & Whelan 2026, "The Disappearing Overnight Drift", Liberty Street Economics](https://doi.org/10.59576/lse.20260701),
  *Federal Reserve Bank of New York blog; commentary, not peer-reviewed*).
  Consequence declared at freeze: the later rolling-origin windows
  (origins ≥ 2021) are EXPECTED a priori to carry weaker edge than the
  earlier ones. The (S-d) PBO/DSR persistence gate adjudicates exactly this
  question; a screen fail driven by post-2020 attenuation is the mechanism's
  documented decay, not a design defect, and is dispositioned
  `archive-no-persistent-window` honestly.
- **Primary citations:** Boyarchenko, Larsen & Whelan 2023
  (10.1093/rfs/hhad020); Lou, Polk & Skouras 2019
  (10.1016/j.jfineco.2019.03.011); Romano & Wolf 2005
  (10.1111/j.1468-0262.2005.00615.x, the screen FWER machinery).

## 2. Universe and sample period

- **Instruments:** ES, NQ (2.0 roll-adjusted continuous-contract evidence
  bars, `data/processed/vendor_legacy_1min_roll_adjusted/`, ADR-0011),
  identical substrate to H900/H001/H101/H103.
- **Frequency:** 5-minute bars aggregated from the 1-minute substrate (H900
  §3 aggregation rule by reference; the backfill driver's `_load_valid_bars`
  path reused verbatim).
- **Session structure:** the CME session (session D = 17:00 CT day D-1 →
  16:00 CT day D, the shared `cme_session_date_expr` rule) is partitioned
  into segments by NY-local time-of-day (DST-aware): **overnight ETH**
  `[18:00, 09:30)` (the competence window), RTH `[09:30, 16:00)`, post-RTH
  ETH `[16:00, 17:00)`. The P3-A feasibility check
  ([overnight_globex_substrate_feasibility_2026-07-19.md](../../../docs/research_notes/overnight_globex_substrate_feasibility_2026-07-19.md),
  ReproLog run `45ce4594e92b`) verified the store carries the overnight
  segment at full coverage: **186 five-minute overnight bars/session at the
  median on both instruments** (ES 186 [p05 186, p95 186]; NQ 186 [p05 185,
  p95 186] — the NQ 5th percentile is one bar short of the full count;
  186 = 15.5 h × 12 bars/h, an arithmetic identity of the exchange
  schedule, not a tunable). `ETH_BARS_PER_SESSION = 186` is the segment
  dwell constant (the ETH analog of the screen harness's
  `RTH_BARS_PER_SESSION = 78`). DST-transition Sundays (~2 sessions/yr)
  carry 174/198-bar overnight segments; they are retained (the rule is
  time-of-day-causal and unaffected).
- **Sample period:** 2015-01-02 → end of materialized span. **The processed
  evidence substrate ends 2025-12-03 (ES) / 2025-12-05 (NQ)** (P3-A §2
  fact 2: ES raw truncation + the NQ terminal-window exclusion; the 2026H1
  raw extension is not materialized).
- **Exclusions (registered a priori):** identical to H900/H101 §2 — (a)
  `pit_provisional` bars; (b) `substrate_defects[DEC_ROLL_LATE_COMMIT]`
  windows per the provenance `coverage_gaps` register (primary variant).
  No inclusive-variant sensitivity is run for H105: December windows carry a
  misattributed front-month in the exact segment this expert trades, so
  "inclusion" would be a corrupted-substrate exhibit, not a sensitivity.
- **DECLARED DECEMBER/GLOBEX BLIND SPOT (binding on every claim).** From the
  P3-A quantification (§2 of the feasibility record): the registered
  exclusions remove **91 ES / 101 NQ sessions (3.32% / 3.66%)** — the same
  mid-December → early-January window every year (10 windows 2015/16 …
  2024/25, plus the NQ 2025 terminal window) — and **69.0% (ES) / 67.8%
  (NQ) of every excluded bar is an overnight-ETH bar** (ES 79,278 of
  114,962; NQ 83,571 of 123,173): the December roll's volume crossover
  happens in Globex sessions.
  Consequences declared at freeze: (i) **year-end overnight behaviour is
  structurally unobservable** to this design — the excluded band is the same
  calendar window every year, so no rolling window ever observes it; (ii)
  every H105 claim is **conditional-grade** on the exclusion-filtered
  substrate (rule of record 2026-07-19); (iii) **DR-1/DR-2**
  (`P1-2.0-DATABENTO-DEC-ROLL-REPULL`, operator-only spend, quote-ready) is
  prerequisite for December-inclusive or confirmation-grade overnight
  evidence, and a post-repair re-backfill is a NEW ledger materialization
  (append-only successor partitions per OD-F), not an edit.
- **Roll-handling:** roll-adjusted continuous contract; close-to-close
  adjusted log returns (return-based features only — PIT-safe on this
  derivative; adjusted levels are not, per the provenance
  `level_use_pit_safe: false`).

## 3. Features and conditioning set

- **ADR-0002(b) conditioning set (frozen before the scan).** Per-session
  covariates, all decided at the CLOSE of the session's first
  overnight-segment bar (the first bar labeled ≥ 18:00 NY — the entry
  decision point, ≈ 18:05), all causal:
  - `rvol_entry` — the H900 emission `rvol_5m_24h` (288-bar trailing realized
    vol, registered feature `rvol_5m_24h@1.0.0`) evaluated at the overnight
    entry bar. **High/low cells use the CERTIFIED leakage-clean per-origin
    construction** (the H103 RC-2 precedent, `_h103_stress_labels` idiom):
    per registered rolling window (§6), the eval-span session's `rvol_entry`
    is scored against the TRAIN-window empirical CDF of `rvol_entry`;
    `high_vol` iff percentile ≥ 2/3, `low_vol` iff ≤ 1/3 (the RC-H101-1
    tercile bands, re-expressed per-origin). Membership is therefore
    computable AT the segment entry from data available then (the trailing
    statistic + the already-frozen train-window CDF) — genuinely lag-0 and
    ex-ante-selectable, unlike a full-sample cutoff (the construction class
    the H103 `expert_card_v3` record convicted; pre-freeze audit finding
    QUANT-1-1). Consequence: the vol cells are defined only on the
    leakage-clean labeled span — the union of the 15 registered
    rolling-window EVAL spans (2017-01-01 → the last window's eval_end,
    ≈ 2024-07); sessions outside that span (pre-origin, and the post-2024-07
    tail beyond the registered window family) belong to neither vol cell.
    This is the H103 RC-2 labeled-span property, inherited, not new.
  - `prior_rth_sign` — the sign of the **prior CME session's** RTH
    log-return, defined exactly as `log(close(15:55-labeled bar) /
    close(09:25-labeled bar))` of the prior session from the same 5-minute
    substrate (the 09:25 label close = the RTH open; the 15:55 label close
    ≈ the RTH close). Fully realized before 16:00 of the prior calendar
    day, i.e. ≥ 2 hours before the overnight entry. Sessions carry
    **undefined** sign — and belong to NEITHER sign cell (remaining in
    `unconditional` and, where labeled, the vol cells) — in two cases, with
    no fallback substituted: (i) the prior session lacks either label
    (holiday early closes, ~9/yr, last RTH label ≈ 12:55); (ii) **the
    immediately-preceding trading session is absent** — the prior available
    session is more than 4 calendar days back (# justify: 4 = the maximum
    ordinary CME weekend-plus-single-holiday spacing, Friday → Tuesday; any
    longer gap indicates a registered exclusion window or truncation, and a
    weeks-stale "prior RTH" is not the covariate this design registers —
    pre-freeze audit finding QUANT-1-6). Motivated by the Lou-Polk-Skouras intraday-vs-overnight
    tug-of-war structure and the Boyarchenko order-imbalance mechanism
    (imbalance forms at the prior close).
- **Pre-registered cell family (5 cells × 2 instruments = 10 trials, one
  trial-register record each):** `unconditional` (PRIMARY), `high_vol`
  (rvol_entry ≥ the per-origin train-window-CDF upper tercile — the §3
  leakage-clean construction above), `low_vol` (≤ the per-origin lower
  tercile), `prior_rth_up`, `prior_rth_down`. # justify: the cell-family structure
  (unconditional + vol terciles + a design-motivated sign covariate) is
  inherited VERBATIM from the RC-H101 family shape for cross-candidate
  comparability; the primary is `unconditional` because the documented
  headline effect (Boyarchenko 2023) is the unconditional overnight drift —
  unlike H101, no conditional-concentration prior is imposed.
- **(S-e) classification of every cell — rule-based causal, stated lags.**
  All five cells are **rule-based causal** functions of realized data
  available at the overnight-segment entry: cell membership is decided at
  segment entry with **observation lag 0 bars** (`unconditional`: vacuous;
  `high_vol`/`low_vol`: rvol_entry is a trailing statistic at the entry bar;
  `prior_rth_up`/`prior_rth_down`: the prior session's RTH return is
  realized hours earlier). **No latent-state cell exists in this design**
  (a latent-state cell fails S-e outright per the amended screen rule —
  latent-state unsupervised latency UNATTAINABLE,
  `P1-2.0-H900-BOCPD-WHITENED` on-ledger run 2026-07-17; the
  supervised-CUSUM oracle latency remains forbidden as an input). S-e test:
  cell dwell (median consecutive-session run × `ETH_BARS_PER_SESSION` = 186)
  ≥ observation lag (0) — the same functional form as the RC-*-2 screens
  with the ETH segment length substituted. **Stated plainly: with every
  registered cell at lag 0, S-e is definitionally satisfied for this design
  and cannot discriminate** — it is retained as a reported gate (dwell and
  lag recorded per cell; the pool schema requires the quantities, and a
  future latent-state cell would fail it), not as a rejector of any cell
  registered here.
- **`cov_*` ledger registration (same commit as this freeze).** The
  `overnight_session_drift` expert family is registered in
  [config/covariates.yaml](../../../config/covariates.yaml) with the
  **empty covariate set** (`covariates: []`): the H105 ledger partitions
  carry NO `cov_` columns, and the screen computes the §3 covariates inline
  from the substrate at scan time (the RC-H101-2/RC-H103-2 precedent — the
  leakage-clean path; a materialized full-sample percentile column would be
  the leaked construction the H103 exhibit already convicted). Any future
  promotion of a §3 covariate to a ledger column is a new registration.

## 4. Signal construction (the overnight-drift rule)

The H105 expert emits a per-bar Layer-1 signal (direction ∈ {-1,0,1},
strength) from data ≤ t only (`Expert` contract; prefix-invariance canary,
§11). The rule is a **pure time-of-day function** — stateless, trivially
causal:

1. **Direction:** +1 (LONG) on every bar whose NY-local label time ∈
   `[18:00, 09:25)`; 0 otherwise. # justify: the long direction is the
   documented drift sign on index futures (Boyarchenko 2023 — ES futures,
   the instrument class here; Lou-Polk-Skouras 2019 document the
   overnight-vs-intraday decomposition on US individual stocks — the
   cross-sectional "tug of war" — cited for the decomposition structure,
   not as index-futures sign evidence); no short leg is registered — the
   mechanism is a risk premium, not a timing signal.
2. **Accrual window (Tier-0 semantics, stated exactly).** Under the Tier-0
   counterfactual (row *t* carries the return the position decided at *t−1*
   earned over (t−1, t]), flagging labels `[18:00, 09:25)` yields: entry at
   the close of the first bar labeled ≥ 18:00 (≈ 18:05, the first tradable
   close after the Globex reopen — the 18:00 auction itself is not tradable
   at Tier 0), exit at the close of the 09:25-labeled bar (≈ 09:30, the RTH
   open). **Every accrual row of this expert is labeled inside
   `(18:00, 09:30)` — strictly inside the overnight ETH segment.** The
   estimand is therefore the ≈18:05 → ≈09:30 close-to-close overnight
   drift, a conservative subset of the literature's 16:00-cash-close-to-open
   object (the 16:00→18:05 shoulder is not claimed).
3. **Strength:** constant 1.0 on held bars (no calibration claim; position
   size is the Layer-2 Kelly fraction). NaN strength never emitted.
4. **One round-trip per session** (enter once, exit once): |Δposition| = 2
   per session — turnover-matched to the ORB experts' per-session round
   trip, which keeps the eventual verdict-tier matched-turnover rotor
   comparison structurally aligned.
5. **Gap robustness:** direction is 0 on every label in `[09:25, 18:00)`,
   so no exposure ever accrues across a session-boundary data gap (excluded
   December windows, weekends, the ES 2025-12-03 truncation): the last bar
   before any such gap is un-flagged by construction.

**PIT property:** direction(t) depends only on the bar's own timestamp;
strength is constant. Enforced by the §11 signal-layer prefix-invariance
canary before any ledger write.

## 5. Estimator — ledger backfill + ADR-0014 screen

- **(A) Shadow-ledger backfill (ADR-0003, Tier 0).** The H105 expert ×
  {ES, NQ} × the registered Kelly sweep {0.5, 0.75, 1.0, 1.25} (each a
  distinct `expert_id` = `overnight_session_drift_k{f}@1.0.0`, ADR-0013 D3;
  grid from [policy/kelly_sweep.py](../../../src/skie_universe2/policy/kelly_sweep.py))
  is backfilled by `scripts/run_shadow_ledger_backfill.py`: signal → Layer-2
  Kelly sizing → Tier-0 bar-close execution + `futures_rt_v1` cost
  (`tier0_barclose.py`, exact levered log return, ruin representable) →
  append-only `ShadowLedgerWriter` (new partitions only; `fidelity_tier = 0`
  recorded per ADR-0006 D5). Counterfactual completeness: a row for every
  valid bar, flat bars included.
- **(B) RC-H105-1 screen (ADR-0014, at the enacted level).** On the
  backfilled k1.0 ledger (fraction-invariant statistics, unit exposure —
  RC-*-2 convention), aggregate the per-session overnight gross log-return
  and run the five-gate screen:
  - **(S-a)** interface compliance + the two PIT canaries (§11).
  - **(S-b)** the §3 frozen conditioning set.
  - **(S-c)** conditional gross edge: Romano-Wolf StepM
    ([Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x))
    over the 5-cell family per instrument, stationary block bootstrap
    ([Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870))
    with Politis-White automatic block length on the chronological
    per-session sequence; PASS iff mean gross > 0 AND RW-adjusted p < the
    enacted level. **The level is read from
    `config/multipletest_family.yaml:screening_error_rate_target` at
    runtime** (currently 0.7400550140326007, criterion retain-fwer; the
    config governs — never transcribed into code).
  - **(S-d)** window persistence: DSR ≥ 1 − level and PBO ≤ level, both
    bounds **derived at runtime from the same config read** (the enacted
    provisional operational proxies, memo §A.6.2); DSR per
    [Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094)
    with HAC-adjusted n_eff and the §8 trial count/dispersion construction;
    PBO per
    [Bailey, Borwein, López de Prado & Zhu 2017](https://doi.org/10.21314/JCF.2016.322)
    **CSCV with S = 16 contiguous row-blocks on the NaN-masked T × 5
    per-session member-only-Sharpe matrix over the full joined session
    panel** (the RC-*-2 screen construction, verbatim); the 15 registered
    rolling windows enter S-d only as the per-window growth exhibit
    (`per_window_growth`), not as the CSCV partition.
  - **(S-e)** ex-ante selectability per §3 (all cells rule-based causal,
    lag 0, segment dwell 186 bars/session).
  - Every cell evaluation (pass or fail) appends a per-trial record to the
    new `rc-h105-1` family in `config/multipletest_family.yaml`
    (registered at freeze with empty trials; ADR-0008 D6), and every
    consumed OOS evaluation window is mirrored to
    `config/burned_data_ledger.yaml` under `hid: H105` per window
    (ADR-0008 D5). **Implementing path (named):** both appends, the
    script-generated Expert Card, and the pool-ledger records are emitted
    by [scripts/emit_screen_expert_card_v1.py](../../../scripts/emit_screen_expert_card_v1.py)
    (the v1 counterpart of the RC-*-2 emitter), run at the disposition
    step immediately after the screen harness.
- **What the screen does NOT do:** no rotor comparison, no set-level
  verdict, no non-redundancy test, no Kelly-fraction selection — all
  verdict-tier objects under the ADR-0015 HOLD.

## 6. Splitter

- **Rolling-origin (ADR-0004):** the registered H900 window family by
  reference (`eval/windows.py::h900_windows()`): 24-month train, 6-month
  step, first origin 2017-01-01, **15 windows × 2 instruments**. The
  overnight rule is stateless (no trained component); the rolling structure
  defines the OOS evaluation folds for the screen's edge series and the
  (S-d) CSCV matrix. Covariate constructions with training-window inputs
  (none in this design beyond the descriptive terciles, §3) follow the H001
  §6 convention.
- **`purge` / `embargo`:** purge = `MAX_FEATURE_LOOKBACK_BARS` (288) at
  window boundaries; embargo = Politis-White automatic block length (H900
  §6 by reference). The H105 signal is memoryless (time-of-day only) and
  the per-session return is session-local — well within the purge.

## 7. Cost model

- **`cost_model_id`:** `futures_rt_v1` — bar-level per-side log-return drag
  at Tier 0 (ADR-0006 D4). One round-trip per session → turnover 2 per
  session; per-unit drag = `switch_drag_notional / 2` (`tier0_barclose.py`
  convention), notional basis.
- **Declared cost caveat:** `slippage_ticks_per_side` is a constant 1-tick
  conservative floor (`P1-H052A-COST-CALIBRATION-EMPIRICAL` carried).
  Overnight ETH liquidity is thinner than RTH liquidity, so the constant is
  **more optimistic overnight than intraday**; the screen's (S-c) estimand
  is pre-cost gross (no net claim), and every net figure in the Expert Card
  is labeled "Tier-0, constant-1-tick-slippage, optimistic in thin ETH".
- **Fidelity tier:** 0 (bar-close), recorded per ledger row.

## 8. Gate thresholds

- **Binding screen level:** the ENACTED `screening_error_rate_target` read
  from config at runtime (§5); (S-d) bounds derived from it at runtime.
  No screen constant is transcribed into code or this document's normative
  sections.
- **Descriptive CIs (implemented in the screen harness §8 block):**
  stationary bootstrap ([Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870))
  with the automatic block length of
  [Politis & White 2004](https://doi.org/10.1081/ETC-120028836) (as
  corrected by [Patton, Politis & White 2009](https://doi.org/10.1080/07474930802459016)),
  on the
  primary cell's per-session gross returns; single-strategy Sharpe SE via
  the HAC-effective-sample-size approximation to the
  autocorrelation-adjusted variant of
  [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453) (the RC-H101-1
  documented leading-order approximation: SE ≈ √((1 + SR²/2)/n_eff),
  n_eff = n/VIF with the
  [Newey & West 1994](https://doi.org/10.2307/2297912) data-dependent
  Bartlett bandwidth); any pairwise
  cell/instrument Sharpe comparison via
  [Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002)
  (none pre-registered for this scan; available at re-adjudication).
  `alpha` = 0.05 two-sided for descriptive CIs. # justify: conventional
  descriptive-CI level (H900/H101 §8 precedent); the binding discovery
  level is the enacted config value, not 0.05.
- **Stationarity diagnostic (registered a priori; implemented in the screen
  harness §8 block via the RC-H101-1 `_kpss_stationarity` helper, both
  'c' and 'ct' variants):** KPSS
  ([Kwiatkowski, Phillips, Schmidt & Shin 1992](https://doi.org/10.1016/0304-4076(92)90104-Y))
  on the per-session gross-return series per instrument, plus the 15-window
  per-window edge-dispersion exhibit. A rejection is reported, not silently
  bootstrapped over (H101 §8 handling by reference). Given the §1
  pre-registered attenuation expectation, the per-window exhibit is the
  PRIMARY stability read for H105.
- **Precision (implemented in the screen harness §8 block):** primary-cell
  gross-edge CI half-width < 25% of the point estimate for
  report-eligibility. # justify: inherited VERBATIM from the
  H900/H001/H101 §8 CONSORT-style precision convention (qualitative
  reporting threshold, not tuned); avoids retrospective power
  ([Hoenig & Heisey 2001](https://doi.org/10.1198/000313001300339897)).
- **DSR trial count AND dispersion (matched surfaces):**
  `N_TRIALS_GATE = 30` — the register's full distinct instrument × cell
  screen surface after this family registers (the RC-*-2 convention applied
  to the grown register: rc-h101-2 (10) + rc-h103-2 (10) + rc-h105-1 (10)).
  The raw count binds the gate (conservative under ADR-0014 Decision 4);
  the correlation-adjusted N_eff is reported alongside. **The cross-trial
  Sharpe dispersion `sr_std` fed to the E[max] deflation term is estimated
  over the SAME surface the count claims** (pre-freeze audit finding
  QUANT-1-4): the union of the register's recorded non-`unconditional`
  trial Sharpes (`sharpe_estimate` fields of the rc-h101-2 / rc-h103-2
  families, read from config at runtime — 16 values) and the current
  scan's 8 sigma-cell Sharpes; `unconditional` trials are excluded from
  the dispersion per the standing non-nested-cell convention (they remain
  in the count).

## 9. Stopping rule

- **Fixed design:** backfill H105 × 2 instruments × 4 Kelly fractions over
  the full materialized span; run RC-H105-1 once over the frozen §3 cell
  set. No cell added, no window added, no parameter varied post-freeze. The
  entry/exit labels (§4) are frozen; no sweep over segment boundaries
  exists or may be added.
- **Max folds:** 15 rolling windows × 2 instruments.
- **Degenerate cells** (n below the ddof floor in any window): reported,
  never re-run (H900 §9 convention).
- **Power gate (pre-data):** the `power-analysis` step runs AFTER this
  freeze and BEFORE the backfill. If the binding cells cannot reach the §8
  precision at the available session counts, STOP — record the
  span-cost-zero null (mission P3-B.5; setup-plan §5.2 precedent).

## 10. Decision rule (ADR-0014 dispositions)

- **`pool-hold-reconsider`:** screen PASS (≥ 1 cell surviving S-a…S-e) →
  pool-ledger append (one record per Kelly fraction, generated from Expert
  Card §§3-5), verdict DEFERRED under the ADR-0015 ratified HOLD. The
  ADR-0015 label-based verdict precondition plus the **M1 realized-bar AND
  session-level Jaccard** (§12) are computed and REPORTED to the operator;
  the lift is a named, dated operator action.
- **`archive-no-persistent-window`:** screen FAIL in every cell
  (`archive-no-gross-edge` as sub-reason where applicable). Terminal but
  register-kept; "fail" is not a disposition (ADR-0009).
- Terminal deliverable either way: the script-generated 8-section H105
  Expert Card (ADR-0009) + trial-register increments + burned-data mirror.

## 11. Reproducibility commitments

- **git HEAD (at run):** auto-populated
- **`uv pip freeze` sha (at run, 64-hex):** auto-populated
- **RNG seed:** 20260719  # justify: pre-registered fresh seed for the H105
  scan family (date-derived, H900/H001 idiom). One seed per scan;
  INDEPENDENT same-seed PCG64 Generators per stage and per instrument
  (`np.random.default_rng(20260719)` for the S-c StepM stream, a dedicated
  one for the §8 CI, a dedicated one for any §8 pairwise contrast —
  dedicated so exhibits cannot perturb the S-c stream; instruments share
  the construction, the RC-*-2 convention). Deterministic; not modified
  post-hoc.
- **Dataset checksums:** the `data/processed/vendor_legacy_1min_roll_adjusted/`
  per-file SHA-256 entries from `data/_manifest.json` at run time; identical
  substrate to H900/H001/H101/H103.
- **PIT canaries (ADR-0008 D1):** (a) the feature-pipeline
  `pit_canary_future_mutation`; (b) the signal-layer
  `assert_prefix_invariant` cut-sweep on the H105 expert, run in the
  backfill driver before any write (S-a).
- **Reproducibility log path:** `logs/reproducibility/repro_log_<run_id>.json`
  (ShadowLedgerWriter per-batch + driver run-level with this design.md SHA
  in `config_resolved_sha256`).
- **Burned-data ledger (ADR-0008 D5):** RC-H105-1 consumes the 15 rolling
  OOS windows × 2 instruments; each is recorded in
  `config/burned_data_ledger.yaml` under `hid: H105` per evaluation window.
- **Design.md SHA at freeze:** auto-populated by /preregister

## 12. Mechanism distinctness and expected overlap (setup-plan M3(a)–(c))

- **(a) Entry-rule non-nesting.** The H105 rule is a pure time-of-day
  function (§4) with no opening-range input, no breakout test, and no
  function of any RTH price level: it is not expressible as a
  re-parameterised ORB (which is a function of the first-hour RTH range).
  Distinct mechanism class: risk-premium harvest vs breakout continuation.
- **(b) Covariate near-collinearity, declared.** `rvol_entry` (overnight
  entry) and the ORB screens' rvol-at-RTH-open are the same underlying
  24-hour trailing statistic sampled ~15.5 h apart — high rank correlation
  is EXPECTED and declared (it predicts session-level coverage overlap, not
  bar-level). `prior_rth_sign` vs ORB's `first_hour_up`: distinct objects
  (full prior RTH session vs first hour of the same session), positive
  association expected, declared.
- **(c) Pre-scan expected-overlap prediction (quoted verbatim at
  disposition, M1 both granularities):**
  - **Bar-level realized-bar Jaccard vs the entire ORB pool coverage:
    EXACTLY 0** — an identity, not an estimate: every H105 accrual row is
    labeled inside (18:00, 09:30) (§4.2); every ORB-pool accrual row is
    labeled inside [10:35, 16:00) (breakout after the 12-bar opening range,
    flat at 15:55). The intersection of the label sets is empty. Any
    post-scan measured value ≠ 0 falsifies the implementation, not the
    prediction.
  - **Session-level Jaccard vs the ORB pool: HIGH — predicted ≈ 0.75–0.95.**
    H105 is active essentially every session (unconditional overnight
    hold); the ORB experts are active on breakout sessions (the substantial
    majority). The two experts trade the same trading dates on the same
    instruments; session-level overlap is near-complete by construction and
    is REPORTED (M1) so the operator's disjointness judgment is made on the
    bar-level axis the ADR-0015 precondition needs, with the session-level
    number beside it, per the setup plan §2.3 (bar-disjoint but
    session-identical = still limited diversification at session cadence —
    stated, not hidden).

## 13. Execution layer (ADR-0005 D3 / ADR-0006) — Tier 0, market-at-close

- **Execution:** Tier 0 — market order at bar close, via
  [tier0_barclose.py](../../../src/skie_universe2/execution/tier0_barclose.py);
  `fidelity_tier: 0` recorded in every ledger row (ADR-0006 D5) and
  `execution_tier: 0` in the pool record provenance.
- **ADR-0006 Decision 2 (reproduced verbatim):** "**Reportability rule.** A
  performance claim is unreportable above its simulated tier's ceiling:
  limit-order/interbar/scalping claims below Tier 2, and pyramiding/stop
  exhibits below Tier 1, may appear only in exploration-tier material
  explicitly labeled with their tier."
- **Forbidden-claims list binding every H105 artifact (Form-A idiom, setup
  plan §1):** any spread capture, any passive/limit fill, any
  queue-position or adverse-selection argument, any scalping hold-time
  claim, any liquidity-provision framing, any interbar entry. None of these
  is reportable from H105 output at Tier 0, and no downgraded variant is
  run in their place.
- **Negative clause (verbatim per the operator instruction):** *"this
  expert makes no fill-timing claim; if the mechanism's premise later
  requires one, the promotion is an ADR-0006 D3 stage gate, not an
  amendment to this section."* In particular, the 18:00-reopen and
  09:30-open **auctions are not claimed**: entry/exit are bar-close market
  orders at ≈18:05 / ≈09:30 close prices (§4.2).
- **ADR-0016 Decision 10 classification (declared at freeze, D10(c)).** A
  future Tier-2 (or Tier-1) re-evaluation of H105 with realistic
  session-boundary execution — same entry/exit semantics (market at the
  first/last segment bar close), same conditioning set, same claim classes,
  execution fidelity upgraded only — tests the **unchanged estimand**:
  case **D10(a)**, a tier promotion of the same HID via an append-only
  execution-tier addendum (own registered SHA; frozen sections untouched).
  If a successor design instead claims the 18:00/09:30 **auction fills**,
  opening-minutes limit entries, or any fill-timing object, the estimand
  changes: case **D10(b)**, successor HID, with H105's burned spans dead to
  it (ADR-0008 D5).
