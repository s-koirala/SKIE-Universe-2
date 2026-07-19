---
name: H106 — Variance-ratio range-state reversal expert (ES/NQ), shadow-ledger screen
description: Pre-registered design doc for hypothesis H106 (second fresh forward expert of the Phase-3 sourcing priority; mean-reversion direction)
type: project
hypothesis_id: H106
tier: 3
status: designed  # designed | running | evaluated | archived(positive|null|negative)
owner: SKIE
created: 2026-07-19
citations: 10.1093/rfs/1.1.41, 10.1093/rfs/3.2.175, 10.1111/j.1468-0262.2005.00615.x, 10.1080/01621459.1994.10476870, 10.1081/ETC-120028836, 10.1080/07474930802459016, 10.3905/jpm.2014.40.5.094, 10.21314/JCF.2016.322, 10.2469/faj.v58.n4.2453, 10.1016/j.jempfin.2008.03.002, 10.1016/0304-4076(92)90104-Y, 10.1198/000313001300339897, 10.2307/2297912
external_doi: null
---

# H106 — Variance-ratio range-state reversal expert (ES/NQ), shadow-ledger screen

This document is the pre-registration record for hypothesis H106 — the
**second fresh forward** expert of the operator-ratified Phase-3 sourcing
priority (mean-reversion, rank 2; run regardless of H105's outcome per the
mission's two-shots rule). It is frozen at `designed` status; any change
after that point requires a new hypothesis ID.

Two objects are pre-registered: (A) the **H106 range-state reversal expert**
(a Layer-1 signal producer conforming to the `Expert` contract) backfilled
to the shadow ledger (ADR-0003), and (B) the **RC-H106-1 screen** — the
ADR-0014 singleton SCREEN at the ENACTED level (read from
[config/multipletest_family.yaml](../../../config/multipletest_family.yaml)
at runtime).

**Governance blocks respected by construction.** No Kelly-fraction
selection; no set-level VERDICT (ADR-0015 ratified HOLD); a screen pass
disposes `pool-hold-reconsider` and STOPS. Unlike H105, H106's realized-bar
coverage is **NOT disjoint from the ORB pool by construction** — §12
declares the expected partial overlap and the M1 measurement obligation;
H106 does not by itself satisfy the ADR-0015 non-overlapping-coverage
precondition against the ORB hash and is not claimed to.

## 1. Hypothesis

- **H0:** the range-state one-bar contrarian signal has no positive
  pre-cost per-session edge in any pre-declared conditioning cell (§3) on
  either instrument at the enacted (S-c) level, or no cell survives
  (S-d)/(S-e).
- **H1:** ∃ a cell on ≥ 1 instrument passing S-a…S-e — a persistent,
  ex-ante-selectable mean-reversion competence window admitting H106 to the
  provisional pool.
- **Mechanism:** short-horizon return reversal where the variance-ratio
  statistic indicates negative first-order autocorrelation. **In
  population**, VR(2) − 1 equals the first-lag autocorrelation of the
  return series
  ([Lo & MacKinlay 1988, Rev. Financ. Stud. 1(1):41-66](https://doi.org/10.1093/rfs/1.1.41));
  the trailing 288-bar sample statistic ESTIMATES that quantity (finite-
  sample bias terms exist and are not corrected — the state is a
  conditioning partition, not an estimator of record). For a **zero-mean**
  AR(1) — per-bar drift is negligible relative to per-bar volatility at
  the 5-minute scale (|μ| ≪ σ; the H900 anchor μ ≈ 1.2e-4/session vs
  per-bar σ ~ 1e-3) — negative ρ1 makes the one-step conditional mean's
  sign opposite the last return: the myopic contrarian direction.
  **Lo & MacKinlay 1990
  ([Rev. Financ. Stud. 3(2):175-205](https://doi.org/10.1093/rfs/3.2.175))
  decompose expected contrarian PORTFOLIO profits into an own-autocovariance
  term ("overreaction"), a cross-autocovariance (lead-lag) term, and a
  cross-sectional mean-dispersion term; their empirical conclusion is that
  for equity portfolios the LEAD-LAG cross term, not own-autocorrelation,
  dominates.** For a SINGLE instrument the cross and dispersion terms
  vanish, so a one-asset contrarian rule's expected profit is positive iff
  the own first-order autocovariance is negative — the term this design's
  VR gate isolates. LM90's portfolio-level dominance finding therefore
  does NOT transfer as support here; the single-instrument
  own-autocovariance channel is exactly what the screen tests. The state
  partition is **already built and registered**
  ([variance_ratio_state.py](../../../src/skie_universe2/features/variance_ratio_state.py);
  project-standard set, `config/conditioning_covariates.yaml`) — the
  cheapest freeze of the four approved directions (setup plan §3 rank 2).
- **A-priori caveat (declared):** the LM88/LM90 evidence is
  weekly-horizon equity portfolios; its transfer to 5-minute index-futures
  bars is the hypothesis under test, not an established result. The
  registered VR construction (window 288 bars, q = 2) is inherited from the
  project's registered feature, not tuned to this outcome.
- **Primary citations:** Lo & MacKinlay 1988 (10.1093/rfs/1.1.41);
  Lo & MacKinlay 1990 (10.1093/rfs/3.2.175); Romano & Wolf 2005
  (10.1111/j.1468-0262.2005.00615.x).

## 2. Universe and sample period

Identical to H105 §2 by reference (same substrate, same 5-minute
aggregation, same exclusions, same processed-store end dates
2025-12-03 ES / 2025-12-05 NQ), including the **declared December/Globex
blind spot** (91 ES / 101 NQ sessions, 3.32% / 3.66%; the P3-A record
[overnight_globex_substrate_feasibility_2026-07-19.md](../../../docs/research_notes/overnight_globex_substrate_feasibility_2026-07-19.md)
§2 verbatim). H106's domain is the **whole CME session** (all segments),
so the blind spot binds it the same way it binds H105's overnight window;
every H106 claim is conditional-grade on the exclusion-filtered substrate,
with DR-1/DR-2 prerequisite for December-inclusive / confirmation-grade
evidence.

## 3. Features and conditioning set

- **Signal-internal state (Layer-1 input, causal):**
  `variance_ratio_state(log_returns, window=288, q=2)` computed on the
  contiguous valid-bar return sequence as stored (the same
  continuous-sequence convention as the registered `rvol_5m_24h`; session
  gaps contribute 1-2 cross-gap returns among 288 — documented, not
  special-cased). State at bar *t* uses returns ≤ *t* only (trailing
  window; warm-up = UNDETERMINED → flat). This is a **rule-based causal**
  feature, not a latent state — signal-internal conditioning on it is the
  mechanism itself (ADR-0005 Layer 1 may consume registered features
  causally; the ADR-0001 D5 gate prohibition targets the latent HMM
  covariate, which this design does not use anywhere).
- **ADR-0002(b) conditioning set (screen cells, per-session, all decided
  at the close of the session's first overnight-segment bar — the entry
  decision point):**
  - `rvol_entry` — `rvol_5m_24h` at the session's first overnight-segment
    bar (identical construction to H105 §3). **High/low cells use the
    CERTIFIED leakage-clean per-origin construction** (H105 §3 / H103 RC-2
    precedent): eval-span sessions scored against the TRAIN-window
    empirical CDF per registered rolling window, tercile bands ≥ 2/3 /
    ≤ 1/3; never a full-sample cutoff (the convicted construction class).
    Vol cells are defined only on the labeled span — the union of the 15
    registered rolling-window EVAL spans (2017-01-01 → ≈ 2024-07); sessions
    outside it belong to neither vol cell (the H103 RC-2 labeled-span
    property, inherited).
  - `vr_state_at_open` — the `variance_ratio_state` value at the session's
    first overnight-segment bar (range / trend / undetermined). Trailing
    statistic; computed on the SAME exclusion-filtered `emission_valid`
    bar sequence the backfilled expert consumes (both pipelines share the
    backfill driver's valid-bar construction, so the screen's state
    sequence and the expert's signal-internal state coincide by
    construction).
- **Pre-registered cell family (5 cells × 2 instruments = 10 trials):**
  `unconditional`, `vr_range_at_open` (PRIMARY — the mechanism's own
  state, per the LM88/LM90 prior that contrarian profit lives where
  negative autocorrelation obtains), `vr_trend_at_open` (contrast),
  `high_vol`, `low_vol`. Sessions whose at-open VR state is UNDETERMINED
  belong to neither VR cell (warm-up only).
- **(S-e) classification:** all five cells are rule-based causal with
  **observation lag 0 bars** (membership decided at the entry bar's close
  from trailing data). No latent-state cell exists in this design. Dwell
  metric: median consecutive-session membership run × the median
  full-session bar count (273 = 186 overnight + 78 RTH + 9 post-RTH, the
  P3-A per-session medians). As in H105 §3: with every cell at lag 0, S-e
  is definitionally satisfied and cannot discriminate — retained as a
  reported gate, not a rejector of any cell registered here.
- **`cov_*` ledger registration (same commit as this freeze):** the
  `vr_range_reversal` family registers the **empty** covariate set in
  [config/covariates.yaml](../../../config/covariates.yaml) (H105
  precedent: screen covariates computed inline at scan time; no `cov_`
  columns materialized).

## 4. Signal construction (the range-state reversal rule)

The H106 expert emits a per-bar Layer-1 signal from data ≤ t only:

1. **Return and state:** r_t = log(close_t / close_{t−1});
   s_t = `variance_ratio_state`(r_{≤t}) with the registered window/lag
   (288, 2).
2. **Direction:** −sign(r_t) if s_t = RANGE and r_t ≠ 0 and the bar's
   NY-local label ≠ the session's terminal label (see 3); else 0. One-bar
   hold: the position decided at close(t) accrues over (t, t+1] and is
   re-decided every bar.
3. **No cross-gap accrual:** direction is forced 0 on bars labeled
   `ETH_HALT_START − BAR_MINUTES` (= 16:55 NY, the last 5-minute label
   before the daily maintenance halt — derived from exchange constants,
   not a tunable). The session's last bar is therefore never held, so no
   position accrues across the halt, the weekend, or an exclusion gap.
   **Documented limitation (ORB precedent):** holiday early-close sessions
   (~9/yr) end before 16:55; a position decided at their true last bar
   accrues the gap to the next session's first bar. Same limitation as
   `orb_first_hour.py` (its docstring); negligible over the backfill and
   not special-cased.
4. **Strength:** constant 1.0 where direction ≠ 0 (no calibration claim).
5. **Turnover:** up to 2 units per bar (sign flip); the per-session
   turnover is data-dependent and large relative to ORB/H105 — declared
   here, reported in the card §6; the screen's (S-c) estimand is pre-cost
   gross and makes no net claim (the Tier-0 net at constant 1-tick
   slippage is expected strongly negative for a 1-bar-hold rule and is
   reported as such, labeled).

**PIT property:** direction(t) is a function of returns ≤ t and the bar's
own label; enforced by the §11 prefix-invariance canary before any write.

## 5. Estimator — ledger backfill + ADR-0014 screen

Identical machinery to H105 §5 by reference, with:

- expert_id family `vr_range_reversal_k{f}@1.0.0` × {ES, NQ} × the
  registered Kelly sweep, via `run_shadow_ledger_backfill.py`; new
  append-only partitions; `fidelity_tier = 0`.
- **RC-H106-1 screen** on the k1.0 ledger, executed by the packaged spine
  ([screening/screen_spine.py](../../../src/skie_universe2/screening/screen_spine.py) —
  the shared RC-*-2 stage sequence; harness
  [run_screen_h106.py](../../../scripts/run_screen_h106.py) supplies only
  the frozen spec + covariates): S-a canary; S-b = §3 cells; S-c
  Romano-Wolf StepM per instrument over the 5-cell family (seed §11;
  N_bootstrap 1000; Politis-White stationary block length); S-d DSR ≥
  1 − level and PBO ≤ level — PBO via **CSCV S = 16 contiguous row-blocks
  on the NaN-masked T × 5 per-session member-only-Sharpe matrix over the
  full joined session panel** (the RC-*-2 construction; the 15 registered
  windows enter only the per-window growth exhibit) — bounds derived at
  runtime from the config read; S-e per §3 (all lags 0). Level READ from
  `config/multipletest_family.yaml` at runtime.
- **DSR trial count AND dispersion (matched surfaces, H105 §8 rule):**
  `N_TRIALS_GATE = 40` — the register's full distinct instrument × cell
  screen surface after this family registers (rc-h101-2 10 + rc-h103-2 10
  + rc-h105-1 10 + rc-h106-1 10); raw count binds; the cross-trial
  dispersion pools the register's recorded non-`unconditional` trial
  Sharpes of those families (read at runtime) with the current scan's 8
  sigma cells; correlation-adjusted N_eff reported. **Run-order
  PRECONDITION (registered):** RC-H106-1 runs only AFTER the RC-H105-1
  screen and its disposition emitter have appended the `rc-h105-1` trial
  records; the spine FAILS CLOSED (RuntimeError) on a named dispersion
  family with zero recorded trials rather than silently under-pooling
  (round-2 audit QUANT-2-3).
- Every cell evaluation appends a per-trial record to the new `rc-h106-1`
  family (registered at freeze with empty trials); every consumed OOS
  window mirrored to `config/burned_data_ledger.yaml` under `hid: H106`.
  **Implementing path (named):** both appends, the script-generated Expert
  Card, and the pool records are emitted by
  [scripts/emit_screen_expert_card_v1.py](../../../scripts/emit_screen_expert_card_v1.py)
  at the disposition step.

## 6. Splitter

H105 §6 by reference (h900_windows(): 24-month train, 6-month step, first
origin 2017-01-01, 15 windows × 2 instruments; purge 288 bars; PW embargo).
The H106 signal's only stateful input is the trailing 288-bar VR window —
exactly the purge length.

## 7. Cost model

H105 §7 by reference (`futures_rt_v1`, Tier 0, notional basis), with the
H106-specific declaration: the 1-bar-hold rule's turnover is one to two
orders of magnitude above the session-cadence experts', so the constant
1-tick-per-side drag compounds proportionally; **no net claim is made at
the screen**, and the card's net figures are labeled "Tier-0,
constant-1-tick-slippage, high-turnover regime — cost-model floor, see
`P1-H052A-COST-CALIBRATION-EMPIRICAL`".

## 8. Gate thresholds

H105 §8 by reference (enacted runtime level; descriptive alpha 0.05; KPSS
'c'+'ct' + per-window dispersion exhibit; 25% precision
report-eligibility convention on the primary cell; Lo-2002 HAC Sharpe SE —
all implemented in the shared spine's §8 block), with `N_TRIALS_GATE = 40`
and the matched dispersion surface per §5, **plus one registered pairwise
contrast**: the Ledoit-Wolf 2008 studentized-bootstrap Sharpe difference
between `vr_range_at_open` and `vr_trend_at_open` per instrument
(cell-masked-to-zero paired series over the common entered index — the
RC-H103-1 construction), descriptive at alpha 0.05: the mechanism's own
state-contrast exhibit.

## 9. Stopping rule

- **Fixed design:** backfill H106 × 2 instruments × 4 fractions over the
  full span; run RC-H106-1 once over the frozen §3 cells. No parameter
  varied post-freeze; the VR window/lag are the registered feature
  constants and may not be swept.
- **Max folds:** 15 windows × 2 instruments. Degenerate cells reported,
  never re-run.
- **Power gate (pre-data):** after this freeze and before the backfill; if
  the binding cells cannot reach the §8 precision on the available
  substrate, STOP and record the span-cost-zero null.

## 10. Decision rule (ADR-0014 dispositions)

H105 §10 by reference: `pool-hold-reconsider` on screen PASS (verdict
DEFERRED under the ADR-0015 HOLD; M1 both-granularity Jaccard REPORTED) or
`archive-no-persistent-window` on FAIL; script-generated 8-section Expert
Card either way.

## 11. Reproducibility commitments

- **git HEAD / pip-freeze SHA (at run):** auto-populated
- **RNG seed:** 20260720  # justify: pre-registered fresh seed for the
  H106 scan family (date-derived, distinct from H105's 20260719 so the two
  scans' bootstrap draws are independent). One seed per scan; INDEPENDENT
  same-seed PCG64 Generators per stage and per instrument (S-c StepM; §8
  CI; the §8 Ledoit-Wolf contrast — dedicated so exhibits cannot perturb
  the S-c stream; instruments share the construction, the RC-*-2
  convention). Deterministic; not modified post-hoc.
- **Dataset checksums:** `data/_manifest.json` entries for the
  roll-adjusted substrate at run time (identical substrate to H105).
- **PIT canaries:** feature-pipeline `pit_canary_future_mutation` +
  signal-layer `assert_prefix_invariant` on the H106 expert in the
  backfill driver before any write (S-a).
- **ReproLog:** per-batch (ShadowLedgerWriter) + run-level with this
  design.md SHA as `config_resolved_sha256`.
- **Burned-data ledger:** RC-H106-1's 15 windows × 2 instruments recorded
  under `hid: H106` per evaluation window.
- **Design.md SHA at freeze:** auto-populated by /preregister

## 12. Mechanism distinctness and expected overlap (setup-plan M3(a)–(c))

- **(a) Entry-rule non-nesting.** The reversal rule is a function of the
  prior bar's return sign and the trailing VR state — no opening-range
  input, no breakout level, no session-phase anchor. It is not a
  re-parameterised ORB; mechanism class contrarian vs continuation, and
  its gating state (VR range) is the **complement** of the trend
  condition breakout continuation exploits.
- **(b) Covariate near-collinearity, declared.** `rvol_entry` is shared
  with H105's construction (same statistic, same bar) — declared. VR state
  and realized vol are related but distinct constructs (autocorrelation
  sign vs magnitude); their association over training windows is REPORTED
  at the scan (declared here, computed there).
- **(c) Pre-scan expected-overlap prediction (quoted verbatim at
  disposition, M1 both granularities):**
  - **Bar-level realized-bar Jaccard vs the ORB pool coverage: PARTIAL,
    predicted ≈ 0.05–0.25.** NOT an identity — both experts accrue on RTH
    bars. Structure of the prediction: ORB accrual rows are RTH labels
    [10:35, 15:55] on breakout sessions (~65 bars ≈ 24% of a session's
    273); H106 accrues on range-state bars across ALL segments (the
    high-frequency prevalence of VR(2) < 1 on this substrate is NOT
    established by the cited literature — LM88's weekly-horizon headline
    is VR > 1 for index/portfolio returns — so the band is a structural
    guess, declared as such and measured at the scan; only ~28.6% of
    session bars are RTH at all). The
    intersection is ORB-held RTH bars that are simultaneously range-state
    — a minority of each side's active set. A measured value far above
    the band (≳ 0.4) would say the reversal expert is effectively an
    RTH-overlap twin; far below (≈ 0) would say range-state and
    ORB-holding almost never coincide. Either informs the operator's
    disjointness judgment; neither is certified.
  - **Session-level Jaccard: HIGH — predicted ≈ 0.85–1.0** (a 24h
    state-gated rule is active almost every session; ORB is active on most
    sessions). Reported beside the bar-level number (setup plan §2.3).
  - **Consequence, stated plainly:** H106 CANNOT pair with the ORB hash to
    lift the ADR-0015 precondition on the bar-disjointness axis; its
    pairing value is with **H105** (H106's RTH+ETH coverage vs H105's
    ETH-only coverage still overlap in the overnight segment where H106 is
    range-state-active — the H105↔H106 pairwise M1 is therefore ALSO
    reported at disposition). H106's primary contribution is pool breadth
    and a mechanism-class diversifier, adjudicated on ADR-0013 currency at
    a future verdict.

## 13. Execution layer (ADR-0005 D3 / ADR-0006) — Tier 0, market-at-close

H105 §13 by reference, in full force: Tier-0 market-at-close via
`tier0_barclose.py`; the ADR-0006 Decision 2 reportability rule reproduced
there verbatim binds every H106 artifact; the forbidden-claims list (any
spread capture, any passive/limit fill, any queue-position or
adverse-selection argument, any scalping hold-time claim, any
liquidity-provision framing, any interbar entry) applies with one
H106-specific emphasis: **a 1-bar-hold reversal is precisely the strategy
class most inflated by optimistic fill assumptions (ADR-0016 Context), so
the no-fill-timing negative clause is load-bearing here** — *"this expert
makes no fill-timing claim; if the mechanism's premise later requires one,
the promotion is an ADR-0006 D3 stage gate, not an amendment to this
section."*

**ADR-0016 Decision 10 classification (declared at freeze, D10(c)).** A
future higher-tier re-evaluation with the same bar-close market semantics
(fidelity upgraded only) is the **unchanged estimand**: case **D10(a)**,
same-HID promotion via append-only execution-tier addendum. Any successor
claiming limit entries at reversal extremes, intrabar fills, or hold-time
objects (the H104-adjacent class) **changes the estimand**: case
**D10(b)**, successor HID, H106's burned spans dead to it (ADR-0008 D5).
