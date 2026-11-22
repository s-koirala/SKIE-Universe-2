---
name: H107 — Session-VWAP × EMA(9) crossover expert (ES/NQ, 5-min RTH), shadow-ledger screen
description: DRAFT pre-registration for hypothesis H107 (principal-proposed practitioner intraday trend rule); NOT frozen — no data contact permitted until /preregister freezes the SHA
type: project
hypothesis_id: H107
tier: 2
status: draft  # draft → designed (on /preregister freeze) | running | evaluated | archived(...)
owner: SKIE
created: 2026-11-22
citations: 10.1016/j.jfineco.2018.05.009, 10.1111/j.1468-0262.2005.00615.x, 10.1080/01621459.1994.10476870, 10.3905/jpm.2014.40.5.094, 10.21314/JCF.2016.322
citation_verification: PENDING (Crossref check required before freeze)
external_doi: null
---

# H107 — Session-VWAP × EMA(9) crossover expert (ES/NQ, 5-min RTH)

**STATUS: DRAFT.** This file is the working pre-registration for the
principal-proposed strategy (2026-11-22: "VWAP + 9 EMA crossover on the 5-min
time frame"). No ledger backfill, screen, or any look at H107 returns is
permitted until the design is frozen via `/preregister` (ADR-0008: pre-registered
scans; every evaluation is a trial-register record). Choices marked
**[OPEN-n]** are the principal's to confirm; each is set to the stated default.
Any change after freeze requires a new HID.

Two objects are pre-registered, mirroring H105/H106: (A) the H107 expert
([vwap_ema_cross.py](../../../src/skie_universe2/experts/vwap_ema_cross.py),
`Expert` contract, prefix-invariance canary) backfilled to the shadow ledger
(ADR-0003) over ES+NQ × the registered Kelly sweep; (B) the **RC-H107-1**
ADR-0014 singleton SCREEN (S-a…S-e) on the packaged
[screen spine](../../../src/skie_universe2/screening/screen_spine.py) at the
ENACTED level read from `config/multipletest_family.yaml` at runtime.

Governance respected by construction: no Kelly fraction selected (Phase-4
champion action); a screen pass disposes `pool-hold-reconsider` and STOPS —
set-level VERDICT entry is a separate, operator-authorized event (VERDICT-1
precedent).

## 1. Hypothesis

- **H0:** the RTH stop-and-reverse position sign(EMA9 − session VWAP) has no
  positive pre-cost per-session edge in any pre-declared cell (§3) on either
  instrument at the enacted Romano-Wolf-corrected level, or no cell survives
  (S-d)/(S-e).
- **H1:** ∃ a cell on ≥ 1 instrument passing (S-c) at the enacted level AND
  (S-d)/(S-e).
- **Mechanism (Tier 2 — practitioner rule, weak direct evidence).** The rule is
  an intraday time-series-momentum filter: EMA9 (≈45-minute half-life-scale
  smoother of price) above the session's volume-weighted mean price means
  recent prices trade above the session's average cost basis. The nearest
  peer-reviewed support is intraday momentum in index futures/ETFs —
  [Gao, Han, Li & Zhou 2018, J. Financ. Econ. 129(2):394-414](https://doi.org/10.1016/j.jfineco.2018.05.009)
  (first-half-hour return predicts last-half-hour return on SPY; stronger on
  high-volatility days). That evidence is about a specific within-day
  horizon, not a VWAP/EMA crossing rule; no peer-reviewed source for this
  exact rule is registered. Practitioner VWAP-trend write-ups exist (SSRN
  working papers, not peer-reviewed) and are not cited as support.
- **A-priori expectations (registered before any scan):**
  1. **Cost-dominated.** A 5-minute stop-and-reverse crossover whipsaws around
     VWAP in range-bound sessions; expected several reversals/session, each a
     round trip at Tier-0 `futures_rt_v1`. The SCREEN is on gross edge; the
     VERDICT is net — the H106 "net-not-monetizable" failure mode is the
     modal expected outcome. The per-session flip count is a registered
     report object (§5).
  2. **Redundancy with ORB (H101/H103).** Both are RTH intraday trend
     followers; on breakout days they hold the same sign. Expected realized-bar
     overlap with the ORB pool is HIGH (H107 is in-market every RTH bar except
     15:55). Non-redundancy (marginal log-wealth growth vs the incumbent set)
     is the binding verdict-tier question, not the screen.
  3. **Opening bias.** EMA9 carries overnight state while VWAP re-anchors at
     09:30, so the first ~5-10 RTH bars hold the overnight-drift sign until
     the EMA catches up — a mechanical link to H105's overnight segment that
     the §12 overlap report must state.

## 2. Universe and sample period

ES, NQ continuous roll-adjusted 5-minute substrate (the registered H900 §2 grid
and exclusion filter), identical to H105/H106. Conditional-grade: the
December-roll blind spot (DEC_ROLL_LATE_COMMIT) is declared; DR-1/DR-2 repaired
substrate is the prerequisite for confirmation-grade evidence.

## 3. Features and conditioning set

Per-session covariates decided at the close of the 09:30-labeled bar (the
first decision bar), all causal, lag 0:

- `rvol_entry` — `rvol_5m_24h@1.0.0` at the first RTH bar; `high_vol` /
  `low_vol` via the CERTIFIED per-origin train-window-CDF terciles (H103 RC-2 /
  H105 §3 construction, verbatim; full-sample terciles forbidden).
- `overnight_sign` — sign of log(close(09:25 label) / close(prior session
  15:55 label)); undefined (neither sign cell) under the H105 §3 rules
  (missing label; prior session > 4 calendar days back). Motivated by
  expectation 3 (opening bias).
- **Cell family [OPEN-1] (5 cells × 2 instruments = 10 trials):**
  `unconditional` (PRIMARY), `high_vol`, `low_vol`, `overnight_up`,
  `overnight_down`. `high_vol` is the mechanism-favoured cell (Gao et al.
  2018 high-vol concentration) but is NOT made primary — no concentration
  prior is imposed.
- (S-e): all cells rule-based causal, lag 0 → S-e definitionally satisfied
  (reported, not discriminating; H105 §3 statement applies verbatim).
- `cov_*` registration: `vwap_ema9_cross` family with `covariates: []` (screen
  computes §3 inline — leakage-clean path).

## 4. Signal construction

Exactly as implemented in
[vwap_ema_cross.py](../../../src/skie_universe2/experts/vwap_ema_cross.py):

1. **EMA9** of 5-min close, alpha = 2/10, continuous over the contiguous
   stored bar sequence (all segments), seeded at the first close.
   **[OPEN-2]** default = continuous (charting convention). Alternative:
   RTH-only EMA reset each session (removes the opening bias, expectation 3).
2. **VWAP** RTH-anchored at the first bar labeled ≥ 09:30 NY, cumulative
   Σ(typical·vol)/Σvol, typical = (H+L+C)/3, reset each NY session date.
   **[OPEN-3]** default = RTH anchor. Alternative: Globex-session anchor
   (18:00) — would make the rule a 24h expert and change the estimand.
3. **Direction** = sign(EMA9 − VWAP) on decision bars labeled [09:30, 15:55);
   0 on ties / undefined VWAP / 15:55 label / outside RTH. Always-in during
   RTH (stop-and-reverse). **[OPEN-4]** default = always-in. Alternative:
   enter only on a *fresh* cross (flat from 09:30 until the first sign change)
   — fewer trades, smaller n.
4. **Strength** 1.0 on held bars. No stop-loss / target / time-stop grid
   (each would be a swept dimension adding trials; not registered).
5. **No extra parameters.** Span 9 is the principal's specification, not a
   tuned value; no span grid is registered (a grid would be a forking-paths
   family requiring its own trial accounting).

PIT: EMA is a causal recursion, VWAP a causal cumulative sum; enforced by the
prefix-invariance canary (tests:
[test_vwap_ema_cross_expert.py](../../../tests/test_vwap_ema_cross_expert.py)).

## 5. Estimator — backfill + RC-H107-1 screen

H105 §5 verbatim with the substitutions: expert ids
`vwap_ema9_cross_k{f}@1.0.0`, f ∈ {0.5, 0.75, 1.0, 1.25}; screen family
`rc-h107-1` (registered with empty trials at freeze); burned-data ledger
`hid: H107`; per-session statistic = RTH gross log-return of the k1.0 stream.
S-c Romano-Wolf StepM over the 5-cell family per instrument (stationary
bootstrap, Politis-White block); S-d DSR ≥ 1 − level and PBO ≤ level from the
same runtime config read (CSCV S = 16 on the T × 5 member-only-Sharpe panel);
DSR trial count = the cumulative register count at run time (includes the 72
VERDICT-1 trials and the 10 new H107 screen trials).

**Additional registered report objects (descriptive, not gates):** per-session
flip count distribution; gross-minus-net drag per session under
`futures_rt_v1`; fraction of RTH bars long/short.

## 6. Splitter

H900 rolling-origin family by reference (24-month train / 6-month step /
first origin 2017-01-01, 15 windows × 2 instruments); purge 288 bars, embargo
Politis-White. Rule is stateless.

## 7. Cost model

`futures_rt_v1` at Tier 0, bar-level, per-flip (turnover 2 per reversal; 1 at
the session's first entry and final exit). Net is reported at the screen as a
descriptive object; it binds at the verdict.

## 8. Gate thresholds

Inherited from the enacted level (no transcription): S-c RW-adj p < level;
S-d DSR ≥ 1 − level, PBO ≤ level; §8 25% precision exhibit per RC-*-2.

## 9-10. Stopping and decision rule

Single pre-registered scan. Any cell passes S-a…S-e → `pool-hold-reconsider`
(pool records × 4 fractions; Expert Card v1 script-generated). No cell passes →
`provisional-archive-null` with an ADR-0009 Expert Card ("fail" is not a
disposition). No re-scan with modified rules under this HID.

## 11. Reproducibility

13-field ReproLog per run; data manifest check; signal-layer prefix-invariance
canary + ledger look-ahead canary before any ledger write; design SHA recorded
in the backlog at freeze.

## 12. Mechanism distinctness and expected overlap

- vs **ORB (H101/H103)**: same RTH segment, same trend sign class → HIGH
  expected realized-bar overlap and return correlation; must be measured (M1
  report extended to H107), not assumed. Distinct `expert_hash` but likely
  low marginal growth.
- vs **H105 overnight drift**: accrual-row disjoint (H107 accrues only inside
  RTH), but signal-linked through the continuous EMA [OPEN-2].
- vs **H106 VR range reversal**: opposite mechanism (momentum vs
  contrarian) over overlapping RTH bars — the only pool member H107 could
  plausibly diversify.

## 13. Execution layer

Tier 0, market-at-close fills. No limit-order / scalping claim is reportable
(ADR-0006: below Tier 2).

## Pre-freeze checklist

- [ ] Principal confirms [OPEN-1]…[OPEN-4]
- [ ] Crossref verification of cited DOIs
- [ ] `rc-h107-1` family + `vwap_ema9_cross` covariate registration (same commit as freeze)
- [ ] Screen harness `scripts/run_screen_h107.py` on the spine + backfill-driver registration
- [ ] `/preregister` audit-remediate rounds → freeze SHA → backlog row
- [ ] Data access: the backfill needs the machine-level raw store (`~/datasets` / `SKIE_SHARED_DATA`), not present in the cloud container
