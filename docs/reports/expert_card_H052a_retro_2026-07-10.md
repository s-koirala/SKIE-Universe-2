---
# Expert Card — machine-readable frontmatter (schema per ADR-0009 §3)
hid: H101                             # 2.0 reanalysis HID; 1.0 source HID = H052a
card_version: 1
predecessor_card: null
design_md_sha256: 345b8f991c8585f1cd41414b75864c85e9755b8be4044ca7cf85e0f570f8efb9   # 1.0 H052a/design.md at 1.0 HEAD ce018515
repro_log_run_ids: [184eccd67bf24d71990265d39c28daf0]   # 1.0 ReproLog (13-field complete per source card)
data_span: { start: 2023-07-01, end: 2024-12-31 }        # OOS evidence span (test fold, both symbols)
instruments: [ES, NQ]
execution_tier: 0                     # retro-mapped: session-cadence market fills + futures_orb_v1 cost model (ADR-0006)
trial_register_increment: 0           # retro card; no new scan run
disposition: arsenal-admit-conditional
---

# Expert Card — H101 v1 (retro of 1.0 H052a): first-hour opening-range breakout, ES/NQ session cadence (HMM gate evaluated and rejected)

Retro Expert Card per ADR-0009 Decision 5 (`P1-2.0-RETRO-CARD-1.0-REGISTER`).
Generated from SKIE-Universe 1.0 evidence only; no new computation was run.
Source of record: `SKIE-Universe@ce018515:
research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md`
(2026-05-05). All source numbers are **net-of-cost** (design.md §1 + §7,
`futures_orb_v1` per-session log-return drag); net values are used below as
**lower bounds on gross** where a gross statement is needed (cost drag ≥ 0
by construction).

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H101 (2.0 reanalysis of 1.0 H052a) |
| 1.0 repo git HEAD at read time | `ce018515a667ee63aa2d40234305f8cb677f030b` (2026-07-10; per [config/data_sources.yaml](../../config/data_sources.yaml) `skie_universe_1_kpi_reports` registration) |
| 1.0 source report | `research/01_hypothesis_register/H052a/H052a_kpi_report_v1.md`, v1, 2026-05-05, 1.0 commit `0aa9258` |
| design.md SHA-256 | `345b8f991c8585f1cd41414b75864c85e9755b8be4044ca7cf85e0f570f8efb9` (1.0 `H052a/design.md` at HEAD above; §15.1 errata addendum included) |
| ReproLog run_id(s) | `184eccd67bf24d71990265d39c28daf0` (`repro-log-complete` per source §Methodological-correctness) |
| Data span | Train 2020–2022, val 2023-H1; OOS test 2023-07-01 → 2024-12-31 (ES 371 / NQ 369 sessions) — source §Realized OOS |
| Instruments | ES, NQ (CME; substrate `b3ee230a...` + VIX daily `0a0e9f25...`) |
| Execution tier | 0 (ADR-0006 retro-mapping: 1 market round-trip per session at bar prices; cost $29.10 ES / $14.10 NQ r/t incl. 1-tick slippage prior; source §8) |
| Shadow-ledger partitions | none — pre-shadow-ledger evidence; backfill pending Phase C (ADR-0003 Decision 5) |
| Trial-register increment | 0 (1.0 family M=1; source §7) |
| Mechanism citations (from 1.0 design.md §1 + §15.1 errata) | ORB profitability on futures: [Holmberg, Lönnbark & Lundström 2013, Finance Research Letters 10(1):27–33](https://doi.org/10.1016/j.frl.2012.09.001); [Tsai et al. 2019, IEEE Access 7:32061–32071](https://doi.org/10.1109/ACCESS.2019.2899177); Zarattini, Barbon & Aziz 2024 ([SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284)). Regime-switching: [Hamilton 1989](https://doi.org/10.2307/1912559); [Guidolin & Timmermann 2007](https://doi.org/10.1016/j.jedc.2006.12.004). *DOI correction*: the 1.0 design §15.1 errata chain records the Tsai DOI as 10.1109/ACCESS.2019.2899852, which does not resolve; the correct registered DOI is 10.1109/ACCESS.2019.2899177 (IEEE Xplore 8641124) — the frozen 1.0 file is not amended |

## 2. Failure-mode decomposition

The 1.0 test object was the **HMM gate increment** (T_H052a = SR_gated −
SR_uncond), which returned a non-significant null; the informative admission
evidence is the **unconditional ORB arm**, whose NQ cell is net-positive.

| Quantity | Value | CI | Method |
|---|---|---|---|
| Gross (pre-cost) edge | not separately emitted; **net values below are lower bounds on gross** | — | cost drag applied per session; **source-internal inconsistency flagged**: the 1.0 card quotes drag "≈ 3e-4" for both symbols (§Realized OOS caveats), but its own formula `log(1 − cost_round_trip/notional)` at its own stated notionals gives ES $29.10/$240k ≈ **1.21e-4** and NQ $14.10/$340k ≈ **4.15e-5** — the ≈3e-4 is consistent only with a far lower ES price level (stale figure) |
| Net edge, unconditional arm (annualised Sharpe) | ES **+0.173**; NQ **+0.855** | arm-level CI not reported in source | source §4 |
| Net edge, gate increment T_H052a (per-session) | ES −0.01840; NQ −0.03417 | ES [−0.06762, +0.02604]; NQ [−0.12321, +0.00326] — both cover zero | LW2008 studentised bootstrap, n=2000 (source §3) |
| Net terminal wealth, realized OOS ($10K) | uncond ES $10,161.33 (+1.61%), NQ **$11,061.27 (+10.61%)**; gated ES $9,905.85 (−0.94%), NQ $10,338.73 (+3.39%) | — | source §1 |
| Net terminal-wealth q05, forward 252-session bootstrap | uncond ES $9,136.67 / NQ $9,442.41; P(loss) 42.94% / **18.56%**; gated ES $9,118.69 (P(loss) 54.84%) / NQ $9,116.80 (37.12%) | q01–q99 per source §6 | PW2004-selected iid/stationary bootstrap at native session cadence (no bar-vs-session caveat; source §6) |
| Realized max-DD | uncond ES 6.68% / NQ 7.95%; gated ES 6.99% / NQ 11.83% | — | source §2 |
| Cost share of gross (derived; **basis-indeterminate on the 1.0 record**) | NQ uncond ≈ **13%** (notional basis, formula-consistent: drag 4.15e-5 vs mean net ln(1.1061)/369 ≈ 2.73e-4) to ≈ **83%** (account-dollar basis: $14.10/$10,000 = 1.41e-3/session); ES uncond ≈ **74%** (notional: drag 1.21e-4 vs net 4.3e-5) to ≈ **99%** (account-dollar: $29.10/$10,000 = 2.91e-3) | — | **derived here**, basis-labeled; supersedes this card's Round-1 52%/87% point values, which rested on the 1.0 card's internally inconsistent ≈3e-4 quote; exact reconciliation deferred to RC-H101-1 |
| Fold-stability | not computable: single outer fold by design (n_folds 1/1); `power-margin-met` but no cross-window dispersion exists | — | source §Cross-validation methodology |

Classification (exactly one primary; binding numbers stated):
**`conditional-only`** — net edge is concentrated in one cell of the
instrument dimension (NQ uncond +0.855 annualised, +10.61% realized,
P(loss) 18.56%) while ES uncond is marginal (+0.173; derived cost share
≈ 74–99% of gross across bases) and the HMM gate increment is
indistinguishable from zero on
both symbols (LW2008 CIs cover zero). Secondary observation: the gate filters
marginally-positive sessions, not the loss tail (ES 10.2% / NQ 4.3% sessions
gated out; source §5), and inner-CV Sharpe at the label-grid optimum is
negative on both symbols (−0.667 ES / −1.294 NQ; source §8) — the label-grid
selection layer, not the breakout signal, is the unstable component.

## 3. Conditional-edge panel

**No ADR-0002 (b) conditioning set exists** in the 1.0 design; the frozen 1.0
covariate objects were the HMM emission features (realized variance,
first-hour sign, gap size, DOW, ETH pre-RTH return, VIX join), consumed by
the gate rather than scanned per-cell. The 1.0 mechanism note (source
§Operator interpretation) plus the design §15.1 Erratum-3 prior art
(Lundström vol-state-conditioning) jointly predict edge concentration in
**high-realized-vol / positive-first-hour** sessions — the opposite direction
of the BIC-selected non-stress gate. Correction: **none applied — no scan
exists to correct.**

```yaml
conditional_edges:
  # Retro evidence — instrument-level cells only; NET of cost (lower bound on gross);
  # uncorrected; NOT admissible as ADR-0002 (c) evidence until scan RC-H101-1 runs.
  - cell: instrument=NQ, unconditional-ORB
    gross_edge: 0.000273        # per-session log-return, NET lower bound (derived: ln(1.1061)/369; source §1)
    ci_lower: null              # arm-level CI not reported in 1.0
    ci_upper: null
    corrected_significant: false
  - cell: instrument=ES, unconditional-ORB
    gross_edge: 0.000043        # per-session log-return, NET lower bound (derived: ln(1.0161)/371; source §1)
    ci_lower: null
    ci_upper: null
    corrected_significant: false
```

| Conditioning cell | Gross edge | Corrected CI | Significant |
|---|---|---|---|
| instrument=NQ (uncond ORB) | ≥ +2.7e-4/session net (derived) | none — uncorrected | not established |
| instrument=ES (uncond ORB) | ≥ +4.3e-5/session net (derived) | none — uncorrected | not established |

**Required follow-up scan RC-H101-1** (admission scan; increments trial
register): pre-cost per-session ORB returns on the 2.0 shadow ledger over the
ADR-0002 project-standard conditioning set — realized-vol percentile,
variance-ratio trend/range state, macro-calendar proximity, spread/liquidity
regime, plus first-hour sign as a design-motivated extension (pre-registered)
— Romano-Wolf corrected. The Lundström-direction prediction (edge in
high-vol cells) is the pre-registered primary cell family.

## 4. Ensemble block

Arsenal snapshot: **0 admitted members at card time** (founding retro
candidate).

```yaml
ensemble:
  marginal_ir_estimate: null            # arsenal empty at card time
  residual_correlation_bound: null      # derivation requires arsenal covariance (ADR-0002 (d))
  correlations: []                      # cross-retro-candidate correlations: follow-up RC-XCORR-1
```

Derivation memo for the correlation bound: none yet — first admission defines
it. Known structural dependence to resolve at RC-XCORR-1: H054 trades the
same first-hour ORB on the complementary (stress-state) session subset and
its secondary statistic is algebraically dependent on H052a
(`H054_kpi_report_v1.md` §"T_H054_b primary"); an H101/H103 pair admitted
together must be correlation-checked on the session-overlap cells.

## 5. Stability profile

- Rolling-window edge series: **not available** — single outer fold
  (2023-07-01 → 2024-12-31); no rolling-origin evaluation exists.
- Change-points (CUSUM/BOCPD): **never run** — gap; folds into RC-H101-1.
- Estimated edge half-life: n/a — no within-record decay measurement is
  possible from one fold.
- Decayed vs never-worked determination: **indeterminate on the 1.0 record**;
  external literature anchors the signal class as persistent-through-2013+
  on index futures ([Holmberg et al. 2013](https://doi.org/10.1016/j.frl.2012.09.001);
  [Tsai et al. 2019](https://doi.org/10.1109/ACCESS.2019.2899177) report >8%
  annual, p<0.03, five index-futures markets 2003–2013), and the 1.0 NQ cell
  is consistent with those magnitudes on 2023-H2–2024 data. Rolling
  confirmation is what RC-H101-1 adds.

## 6. Disposition

```yaml
disposition: arsenal-admit-conditional
binding_criterion: "Net (hence gross lower-bound) positive edge in the NQ unconditional-ORB cell: +0.855 annualised Sharpe, +10.61% realized OOS over 369 sessions, forward P(loss) 18.56% — positive net implies positive pre-cost edge in at least one cell; multiplicity-corrected cell significance not yet established (no 1.0 scan ran)."
```

Candidate disposition per the ADR-0009 taxonomy; admission becomes effective
only when ADR-0002 (a)–(d) are established: (a) PIT-clean 2.0 interface port
+ leakage-canary suite (1.0 `leakage-canary-pass` is evidence but not the 2.0
suite), (b)+(c) scan RC-H101-1 with Romano-Wolf correction, (d) trivial at an
empty arsenal but re-checked against RC-XCORR-1. The **admitted form is the
unconditional first-hour ORB** (simple published rule per the ADR-0002
Context literature arc); the HMM gate is dropped on H052a's own evidence
(gate increment null; filters the wrong direction) and per ADR-0001
Decision 5. Disposition would fall back to `archive-no-gross-edge` only if
RC-H101-1 finds no corrected-significant positive pre-cost cell on either
symbol.

## 7. Burned-data entry

| OOS span consumed | Purpose | Mirrored to burned_data_ledger.yaml |
|---|---|---|
| ES 2023-07-01 → 2024-12-31 (session cadence) | admission-scan (retro; consumed by 1.0 H052a walk-forward) | recorded 2026-07-10 in [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml) (`hid: H101, instrument: ES`; commit SHA pending — working tree uncommitted for audit round) |
| NQ 2023-07-01 → 2024-12-31 (session cadence) | admission-scan (retro; same run) | recorded 2026-07-10, same ledger (`hid: H101, instrument: NQ`) |

## 8. Priors update

1. Unconditional first-hour ORB on NQ is the strongest single net-positive
   cell in the 1.0 register (+0.855 annualised, P(loss) 18.6%) — it anchors
   the first admission scan and is the cheapest live expert candidate
   (pure-C#-implementable per source §Operator interpretation).
2. BIC-selected "non-stress" HMM states filter toward consensus-low-vol
   sessions — the wrong direction for breakout edge (Lundström prior art);
   queued vol-conditioning must be scanned as covariate cells, not learned
   gates.
3. Session-cadence cost share of derived gross is material but
   **basis-indeterminate on the 1.0 record, bounded ≈13–99%** (NQ ≈13%
   notional-basis to ≈83% account-dollar; ES ≈74–99%), and the 1.0 card's
   own ≈3e-4 drag quote is inconsistent with its own cost formula —
   admission scans must be pre-cost per ADR-0002, and RC-H101-1 must
   reconcile the cost basis before any net claim.
4. ES is the systematically weaker sibling of NQ for this signal class
   (+0.173 vs +0.855) — instrument is a first-class conditioning dimension
   for queued intraday hypotheses.
5. Label-grid inner-CV optima with negative CV Sharpe (−0.667/−1.294)
   indicate the PT/SL/timestop grid adds selection noise, not fit — queued
   ORB re-specs should shrink or drop that grid.
