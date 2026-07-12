# H900 — Dwell-time feasibility report (founding go/no-go, ADR-0004 Decision 6)

**Verdict: GO** (primary registered analysis; inclusive sensitivity variant also GO).

Regime sojourns on the 2.0 evidence-bar substrate are long enough — relative to
detection latency plus switching-cost payback at the registered central edge
scenario — for the allocator/rotor premise to survive its founding empirical
gate. The H1 criterion holds on **both** instruments (design requires ≥ 1).

This report presents the round-1-audit-remediated production run of
2026-07-11 (ReproLog run `efd8dcb1bf67`). It supersedes the round-1 run
(`3264085ca65e`, retained in `logs/reproducibility/` for the audit trail),
which carried two defects corrected here: a block-length-selector sign guard
(QUANT-1-1, §3.2 disclosure) and an exchange-fee misannotation
(LITERATURE-1-2, §4).

## 0. Provenance header

| Field | Value |
|---|---|
| Hypothesis | H900 — dwell-time feasibility gate ([design](../../research/01_hypothesis_register/H900/design.md), frozen, tier 4 methodology gate) |
| Design SHA-256 at execution | `548f009ae505816a1b2aeb8693681224e080449b458013e87d6f3df3c8f4c43c` (matches freeze) |
| ReproLog | [logs/reproducibility/repro_log_efd8dcb1bf674382988b89db97a0776c.json](../../logs/reproducibility/repro_log_efd8dcb1bf674382988b89db97a0776c.json) — 13 registered fields + 2 provenance-integrity extension fields (`git_dirty: true`, `working_tree_hash`; round-1 audit REPRODUCIBILITY-1-1: the recorded `git_head` does NOT pin this pre-commit run, so the dirty flag + content hash of all modified/untracked files record what actually ran); `config_resolved_sha256` = design SHA; `model_hash` = SHA-256 over the explicit list of the 8 output files written by this run (round-1 audit CODE-1-4) |
| RNG seed | 20260710 (design §11); EM restart *i* seeded `seed + i`, *i* ∈ 0..4 |
| Substrate | `data/processed/vendor_legacy_1min_roll_adjusted/` (ES+NQ 1-min, 2015-01-02 → 2025-12-31, multiplicative-ratio roll-adjusted, Phase C port per ADR-0011); per-file SHA-256 in ReproLog `dataset_checksums` (23 entries from [data/_manifest.json](../../data/_manifest.json)) |
| Data vendor + snapshot | Databento-sourced legacy 1-min store (`vendor_skie_ninja_legacy_raw_1min`, [config/data_sources.yaml](../../config/data_sources.yaml)); processed snapshot 2026-07-11 ([provenance](../../data/processed/_provenance/vendor_legacy_1min_roll_adjusted_20260711.json)) |
| Runner | [scripts/run_h900_dwell_study.py](../../scripts/run_h900_dwell_study.py) (`--variant both`, all 15 windows) |
| Outputs | `reports/H900/h900_{spells,latency}_{primary,inclusive}.parquet`, `h900_window_summary_{primary,inclusive}.csv`, `h900_verdict_{primary,inclusive}.json`, `run_log.txt` |
| Sensitivity regeneration (round-2 audit QUANT-2-1) | Verdict JSONs extended 2026-07-11 with the session-truncated pooled-bootstrap block via `--regen-sensitivity` (ReproLog [repro_log_bc5b16aef8ae4ed487868879632ccc9f.json](../../logs/reproducibility/repro_log_bc5b16aef8ae4ed487868879632ccc9f.json); inputs = archived spells-parquet SHA-256s; seed 20260710). No refit: the §8 bootstrap is a pure function of the archived spells + seed, and a guard recomputed the continuous-rule pooled estimates from the same parquet and asserted equality with the archived verdict values before rewriting (all 4 instrument×variant cells reproduced; run log) |
| Multiplicity | Singleton family `h900-dwell-time-feasibility` in [config/multipletest_family.yaml](../../config/multipletest_family.yaml); no correction due (design §8) |
| Burned data | 15 evaluation windows × {ES, NQ} recorded in [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml) (spans tile 2017-01-01 → 2024-07-01) |
| ADR-0008 leakage canary | PASS — features at bar t bit-invariant to arbitrary mutation of bars > t on the real ES substrate (run log); causal-filter prefix gate enforced by ported unit tests; a negative-control unit test proves the canary fires on an injected future-shifted feature |

Backtest-reporting checklist (quant rules): universe = {ES, NQ} (design §2);
rebalance frequency = n/a (no strategy is traded — distributional gate);
transaction cost model = `futures_rt_v1` (§4 below); survivorship bias = n/a
(continuous-contract index futures, no delisting universe); Sharpe / Sortino /
MaxDD / turnover / capacity = n/a at this tier (no return stream is produced;
the deliverable is the sojourn-vs-break-even comparison mandated by ADR-0004
Decision 6).

## 1. Registered decision rule and its application

Design §10, quoted verbatim:

> **If H1 criterion met** (CI lower bound of D_med > D_be(μ=1.2e-4) for the
> BIC-selected model on ≥1 instrument): **GO** — archive(positive); the
> allocator program proceeds; dwell-time metric family becomes a standing
> ADR-0004 report object; the winning regime family is registered as the
> candidate conditioning covariate set for ADR-0002 admission scans.

with the §8 precision gate: *"the pooled D_med 95% CI half-width must be < 25%
of the point estimate for the primary (BIC-selected) cell, else the verdict is
'indeterminate — insufficient spells'"* and §8 alpha = 0.05 (decision uses the
one-sided lower bound).

Application (primary variant, BIC-selected cell = 4-state diag on every window
of both instruments; one 5-minute bar = 5 minutes):

| Instrument | Pooled D_med (bars) | 95% bootstrap CI | CI half-width | Precision gate (< 25% × D_med) | L_detect (bars) | c_switch (notional) | D_be(μ=1.2e-4) (bars) | CI lower > D_be | H1 |
|---|---|---|---|---|---|---|---|---|---|
| ES | **12** (60 min) | [10.0, 14.0] | 2.0 | 2.0 < 3.0 → pass | 3 | 1.741e-4 | **4.45** | 10.0 > 4.45 → yes | **met** |
| NQ | **9** (45 min) | [8.0, 10.0] | 1.0 | 1.0 < 2.25 → pass | 2 | 6.472e-5 | **2.54** | 8.0 > 2.54 → yes | **met** |

H1 met on both instruments (≥ 1 required) with both precision gates passed →
**GO — archive(positive)**. Consequences per §10: the dwell-time metric family
becomes a standing ADR-0004 report object, and the winning regime family —
**Gaussian HMM, 4 states, diagonal covariance, on standardized
(ret_5m, log rvol_5m_24h) emissions** (selected in 30/30 window × instrument
fits; §3.3) — is registered as the candidate conditioning covariate set for
ADR-0002 admission scans.

Estimand note: D_med is the pooled Kaplan-Meier median sojourn of the
**causal filtered** state sequence measured out-of-sample in the 15 evaluation
windows, under the §2 session-continuous spell rule.

## 2. Methods (executed protocol)

- **Evidence bars:** 1-min roll-adjusted bars aggregated to 5-min
  (open=first/high=max/low=min/close=last/volume=sum; label = window start;
  a bar labelled t covers [t, t+5m) and is observable at t+5m — bar-count
  indexing carries no look-ahead, asserted by the canary).
- **Registered exclusions (primary):** `pit_provisional` bars and the 22
  December-roll `DEC_ROLL_LATE_COMMIT` / `terminal_window` coverage-gap windows
  from the substrate-defect register, removed on CME session dates via the
  shared session rule ([src/skie_universe2/utils/sessions.py](../../src/skie_universe2/utils/sessions.py)).
  Sensitivity variant includes them (§5.2).
- **Features (design §3):** `ret_5m@1.0.0` (adjusted close-to-close log
  return), `rvol_5m_24h@1.0.0` (sqrt of rolling sum of squared 5-min returns
  over trailing 288 bars, full-window requirement); emission vector
  (ret_5m, log rvol_5m_24h) standardized with training-window moments only.
  Registry: [src/skie_universe2/features/regime_emissions.py](../../src/skie_universe2/features/regime_emissions.py).
- **Windows (design §2/§6):** 15 rolling-origin windows, 24-month train,
  6-month step, first origin 2017-01-01; purge = 288 bars dropped from the
  train end; embargo = Politis-White (PPW 2009-corrected) automatic block
  length on the training return series, skipped at the eval start (per-window
  values in T1; range 4–67 bars ES, 1–48 bars NQ after the §3.2 selector
  correction).
- **Estimator (design §5):** ported 1.0 Gaussian HMM (log-space Baum-Welch,
  k-means++ warm start, label-switch canonicalization by emission-mean rank);
  grid n_states {2,3,4} × cov {diag, full}; 5 EM restarts per cell, restart
  seeds 20260710+i; BIC (train in-window log-likelihood) selects per window per
  instrument; **all 360 cell fits converged; zero dead-state and zero PD-ridge
  events** (design §9 recording).
- **State inference:** causal forward filter ONLY (`filter_states_from_prior`),
  warm-started from the train-fold terminal log-α propagated across the
  purge+embargo gap (Hamilton-filter prediction step; 1.0 fold-continuity
  rule). No smoothing, no Viterbi, anywhere.
- **Dwell spells:** sojourn run-lengths of the filtered MAP state path;
  right-censored at window edges; first spell of each contiguous segment
  excluded as left-censored (start unobserved); session-continuous rule
  primary, session-truncated variant as sensitivity (§5.3).
- **Inference (design §8):** per-window KM median with Greenwood-variance
  Brookmeyer-Crowley CI; pooled median via stationary bootstrap
  (Politis-Romano 1994) over the chronological spell sequence, PW automatic
  block length (ES 1.73, NQ 2.97 on the pooled spell-duration sequences),
  B = 2000 (1.0 H052a bootstrap convention), percentile CI, alpha 0.05.
- **Detection latency (design §7):** one-sided log-likelihood-ratio CUSUM
  (Page 1954) per filtered transition (successor-vs-incumbent emission
  densities under the fitted model), started at the filtered change-point;
  threshold h_i = log ARL0_i with ARL0_i = model-implied incumbent expected
  sojourn 1/(1−a_ii) (Lorden 1971 ARL0 ≥ e^h bound; Moustakides 1986
  optimality); delay right-censored at sojourn end when no alarm; L_detect =
  pooled KM median delay. Censoring is informative — bounding sensitivity in
  §5.5 (round-1 audit QUANT-1-2).
- **Cost model (design §7):** `futures_rt_v1`
  ([src/skie_universe2/costs/futures_rt_v1.py](../../src/skie_universe2/costs/futures_rt_v1.py)) —
  one switch = exit incumbent + enter successor = 2 sides; per-side cost =
  commission + exchange fee + NFA fee + 1-tick slippage prior from
  [config/instruments.yaml](../../config/instruments.yaml). Exchange fee
  $1.38/side (CME E-mini non-member electronic, eff. 2024-02-01,
  broker-notice sourced — **erratum vs the 1.0-carried $1.18** whose
  "Individual Member" annotation failed source verification; round-1 audit
  LITERATURE-1-2): ES $14.75/side → $29.50/switch, NQ $7.25/side →
  $14.50/switch. c_switch = −log(1 − cost/notional), notional = median
  unadjusted close over the pooled evaluation spans × multiplier (ES: price
  3390.00 × $50; NQ: 11203.00 × $20). Formula cross-check: under the legacy
  1.0 fee inputs the model reproduces the design §7 bracket drags (ES
  1.2126e-4 @4800; NQ 4.1471e-5 @17000; pinned in
  [tests/test_futures_rt_v1.py](../../tests/test_futures_rt_v1.py)).

## 3. Results — ADR-0004 metric family as time series

### 3.1 Per-window dwell (primary variant, BIC-selected cell, session-continuous rule)

Median dwell of the filtered state sequence per evaluation window (KM median,
bars; Greenwood 95% CI; right-censoring at window edges). Every window selected
**4-diag** by BIC.

**ES**

| Window | Eval span | n_spells | n_events | KM median (bars) | 95% CI | Embargo (bars) |
|---|---|---|---|---|---|---|
| 0 | 2017-01→2017-07 | 156 | 153 | 29 | [12, 62] | 6 |
| 1 | 2017-07→2018-01 | 118 | 116 | 39 | [9, 86] | 6 |
| 2 | 2018-01→2018-07 | 250 | 247 | 13 | [8, 28] | 9 |
| 3 | 2018-07→2019-01 | 289 | 287 | 9 | [5, 13] | 5 |
| 4 | 2019-01→2019-07 | 365 | 362 | 9 | [6, 14] | 8 |
| 5 | 2019-07→2020-01 | 274 | 272 | 21 | [12, 34] | 7 |
| 6 | 2020-01→2020-07 | 129 | 127 | 22 | [7, 39] | 6 |
| 7 | 2020-07→2021-01 | 335 | 333 | 7 | [4, 12] | 67 |
| 8 | 2021-01→2021-07 | 236 | 234 | 7 | [4, 17] | 56 |
| 9 | 2021-07→2022-01 | 263 | 261 | 15 | [7, 24] | 57 |
| 10 | 2022-01→2022-07 | 412 | 409 | 6 | [5, 9] | 56 |
| 11 | 2022-07→2023-01 | 189 | 187 | 43 | [25, 71] | 6 |
| 12 | 2023-01→2023-07 | 337 | 334 | 11 | [6, 16] | 4 |
| 13 | 2023-07→2024-01 | 226 | 224 | 11 | [5, 21] | 4 |
| 14 | 2024-01→2024-07 | 141 | 139 | 31 | [9, 71] | 4 |

**NQ**

| Window | Eval span | n_spells | n_events | KM median (bars) | 95% CI | Embargo (bars) |
|---|---|---|---|---|---|---|
| 0 | 2017-01→2017-07 | 173 | 170 | 11 | [4, 21] | 7 |
| 1 | 2017-07→2018-01 | 332 | 330 | 6 | [4, 12] | 9 |
| 2 | 2018-01→2018-07 | 339 | 336 | 7 | [5, 9] | 12 |
| 3 | 2018-07→2019-01 | 341 | 339 | 5 | [4, 7] | 7 |
| 4 | 2019-01→2019-07 | 436 | 433 | 7 | [5, 9] | 2 |
| 5 | 2019-07→2020-01 | 375 | 373 | 14 | [8, 22] | 2 |
| 6 | 2020-01→2020-07 | 192 | 189 | 12 | [6, 22] | 1 |
| 7 | 2020-07→2021-01 | 385 | 383 | 7 | [5, 11] | 45 |
| 8 | 2021-01→2021-07 | 348 | 345 | 6 | [4, 10] | 48 |
| 9 | 2021-07→2022-01 | 266 | 264 | 12 | [6, 26] | 47 |
| 10 | 2022-01→2022-07 | 287 | 284 | 10 | [6, 14] | 47 |
| 11 | 2022-07→2023-01 | 230 | 228 | 22 | [12, 56] | 9 |
| 12 | 2023-01→2023-07 | 323 | 320 | 12 | [7, 22] | 1 |
| 13 | 2023-07→2024-01 | 258 | 256 | 19 | [12, 28] | 1 |
| 14 | 2024-01→2024-07 | 204 | 202 | 12 | [5, 25] | 2 |

Time-variation reading (ADR-0004 Decision 5: no single terminal number): ES
per-window medians span 6–43 bars (30 min–3.6 h); dwell lengthens in the
low-vol regimes of 2017 (w0–w1) and the 2022-H2 / 2024-H1 windows (w11, w14)
and compresses to 6–9 bars in 2018-H2–2019-H1 and 2020-H2–2022-H1. NQ is
uniformly shorter-dwelling (5–22 bars). Per-window Greenwood CI lower bounds
sit above the central-scenario D_be in **13/15 ES windows** (the exceptions
are w7 and w8, whose CI lower bounds of 4 bars fall below D_be = 4.45) and
**15/15 NQ windows** — the pooled GO is not carried by a single episode. The
training-window PW block lengths also spike to ~45–67 bars in the 2020-H2 →
2022-H1 windows (long-memory volatility episodes), which the embargo absorbs
by construction.

### 3.2 Pooled dwell, precision gate, detection latency

Primary variant, BIC-selected cells pooled chronologically:

| Quantity | ES | NQ | Method |
|---|---|---|---|
| Pooled spells (events) | 3720 (3685) | 4489 (4452) | usable spells; left-censored firsts excluded |
| Pooled KM median dwell | **12 bars = 60 min** | **9 bars = 45 min** | KM (right-censored) |
| 95% CI (stationary bootstrap, B=2000) | [10.0, 14.0] | [8.0, 10.0] | PR 1994 + PW block length (ES b=1.73, NQ b=2.97); 0 undefined replicates |
| Precision gate (§8, half-width < 25%) | 2.0 < 3.0 → **pass** | 1.0 < 2.25 → **pass** | registered |
| Transitions (CUSUM alarms) | 3720 (2912; 78.3%) | 4489 (3665; 81.6%) | non-alarmed censored at sojourn end |
| Detection latency L_detect (KM median) | **3 bars = 15 min** | **2 bars = 10 min** | Page 1954 LLR-CUSUM |
| Latency KM q25/q50/q75/q90 (bars) | 1 / 3 / 6 / 11 | 1 / 2 / 5 / 9 | pooled distribution |

Round-1 selector-defect disclosure (audit QUANT-1-1): the round-1 run's
Politis-White block-length selector carried a 1.0-ported sign guard that
short-circuited to b = 1 whenever the flat-top spectral sum Ĝ ≤ 0, although Ĝ
enters PW 2004 eq. 9 only squared (the `arch` reference implementation applies
no sign guard). Most round-1 embargoes and both pooled spell-bootstrap block
lengths (reported as 1.00) were fallback outputs. The corrected selector
yields ES b = 1.73 / NQ b = 2.97 on the pooled spell sequences and the T1
embargo column above. The pooled dwell medians and CIs are insensitive to the
defect: recomputing the pooled bootstrap with fixed block lengths b ∈ {1, 2,
3, 4, 5} (same seed, B = 2000) reproduces **identical** medians and CIs on
both instruments (ES 12 [10.0, 14.0]; NQ 9 [8.0, 10.0]).

### 3.3 Model selection uniformity

BIC selected **4 states + diagonal covariance in all 30 window × instrument
fits** (60/60 including the inclusive variant). BIC decreased monotonically in
n_states across the registered grid in every window, i.e. the selection sits
at the registered grid ceiling. This uniformity cuts both ways: it makes the
"BIC-selected model" well-defined and stable across seven years of regimes (a
prerequisite for registering the family as an ADR-0002 conditioning set), but
it also means richer models were never rejected — see Limitations (§6,
grid-ceiling item) for the directional evidence.

## 4. Break-even frontier (design §7)

D_be(μ) = L_detect + c_switch/μ, notional basis (primary; the account-dollar
basis is the registered sensitivity column). Central scenario μ = 1.2e-4 per
5-min bar. Primary variant:

| μ (per bar) | ES D_be (bars) | ES CI-low 10.0 > D_be? | NQ D_be (bars) | NQ CI-low 8.0 > D_be? |
|---|---|---|---|---|
| 1e-5 | 20.41 | no | 8.47 | no |
| 4e-5 | 7.35 | yes | 3.62 | yes |
| **1.2e-4 (central)** | **4.45** | **yes** | **2.54** | **yes** |
| 2.7e-4 | 3.64 | yes | 2.24 | yes |

Cost inputs (post-LITERATURE-1-2 fee erratum, §2): ES switch $29.50 →
c_switch = 1.741e-4 (notional @ median unadjusted price 3390.00); NQ switch
$14.50 → c_switch = 6.472e-5 (@ 11203.00). The fee correction ($1.18 →
$1.38/side) moved the central D_be by +0.02 bars (ES) / +0.02 bars (NQ)
relative to the round-1 schedule — immaterial to the verdict.
Account-dollar sensitivity basis ($10K account, 1.0 KPI convention): ES
2.954e-3, NQ 1.451e-3 per switch — on that basis D_be(1.2e-4) would be 27.6
bars (ES) / 14.1 bars (NQ), i.e. **the gate would fail on both instruments if
edges are account-dollar-denominated**; the registered formula-consistent
basis is notional (QUANT-2-2), but this basis dependence is carried forward
as a standing caveat for ADR-0002 scans.

μ-dependence: at the most pessimistic registered scenario (μ = 1e-5) the gate
fails on both instruments — expected behavior per design §7 ("smaller μ makes
D_be arbitrarily large and the gate unpassable, which is the correct
behavior"). The GO therefore asserts feasibility **conditional on conditional
net edges of at least ~4e-5 per bar existing**, which is what ADR-0002
admission scans must establish.

## 5. Sensitivity exhibits

### 5.1 All grid cells (registered §5 sensitivity)

Median across windows of the per-window KM medians (bars), primary variant;
`sel` = windows selected by BIC; all cells converged in all windows:

| Instr | 2-diag | 2-full | 3-diag | 3-full | 4-diag (sel 15/15) | 4-full |
|---|---|---|---|---|---|---|
| ES | 5 | 5 | 8 | 9 | **13** | 15 |
| NQ | 5 | 5 | 6 | 5 | **11** | 9 |

Coarser state partitions produce *shorter* filtered sojourns here (more of the
short-dwell churn is absorbed into a single broad state whose filtered path
flips more often near its internal boundary). Even at the most pessimistic
cells (median-of-medians 5 bars, per-window minima 4), the per-window medians
sit at/above the central-scenario D_be for NQ and near it for ES; the
registered decision object remains the BIC-selected cell.

### 5.2 Exclusion variant (design §2 sensitivity: pit_provisional + December-roll windows INCLUDED)

| Quantity | ES incl. | NQ incl. | vs primary |
|---|---|---|---|
| Pooled KM median (bars) | 12 | 8 | ES unchanged; NQ −1 |
| 95% CI | [9.0, 14.0] | [7.0, 9.0] | overlapping |
| Precision gate | pass (2.5 < 3.0) | pass (1.0 < 2.0) | — |
| L_detect (bars) | 2 | 2 | ES −1 |
| D_be(1.2e-4) (bars) | 3.45 | 2.54 | — |
| Per-window CI-low > D_be | 14/15 | 15/15 | — |
| H1 | met | met | — |
| **Verdict** | | | **GO** (unchanged) |

The December-roll substrate defect does not drive the finding.

### 5.3 Session-truncated spell rule (design §2 sensitivity)

Pooled KM medians with the registered §8 CI method (stationary bootstrap over
the chronological truncated-rule spell sequence, PW automatic block length,
B = 2000, seed 20260710), BIC-selected cells — persisted in the verdict JSONs'
`session_truncated_sensitivity` block:

| Variant | ES | NQ |
|---|---|---|
| primary | 49 bars CI [35.0, 69.0] (n = 5239, 29.4% censored; PW block ≈ **99.9** bars) | 32 bars CI [24.0, 41.0] (n = 6007, 25.7% censored; block ≈ **86.1**) |
| inclusive | 53 bars CI [38.0, 75.0] (block ≈ 112.3) | 29 bars CI [23.0, 39.0] (block ≈ 93.6) |

versus 12 / 9 bars (primary) under the continuous rule. Two disclosures
(round-2 audit QUANT-2-1):

1. Earlier drafts of this section quoted pooled **Greenwood** CIs (ES
   [43, 56], NQ [28, 37]) — a method departure from the registered §8
   pooled-CI method that was neither disclosed nor archived. The
   registered-method bootstrap CIs above are materially wider and are now
   the persisted artifact values; the Greenwood figures are retained here
   only as a method comparison (Greenwood understates the CI because it
   ignores the serial dependence the bootstrap blocks capture).
2. The auto-selected block lengths (~86–112 bars, vs 1.7–3.0 for the
   continuous rule) are themselves diagnostic: session truncation
   manufactures long runs of near-identical, session-capped fragment
   durations from each overnight-persistent spell, inducing strong serial
   dependence in the fragmented duration sequence. The wide blocks are the
   bootstrap correctly propagating that rule-induced dependence into the CI.

The truncated variant measures a different estimand — within-session sojourn
fragments — and its median is dominated by overnight-persistent spells
fragmenting into session-length pieces (fragments of long spells outnumber
the short interior spells), while its censored fraction rises from ~0.9% to
~29% (ES) and ~0.8% to ~26% (NQ). Both rules
clear D_be at the central scenario even at their bootstrap CI lower bounds;
the primary (continuous) rule is the registered decision object.

### 5.4 Account-dollar cost basis

Reported in §4 — the registered sensitivity column; verdict-relevant only if
future edge estimates arrive account-dollar-denominated.

### 5.5 Latency-censoring bound (round-1 audit QUANT-1-2)

The CUSUM delay censoring is informative: the same emission stream drives
both the detector increment and the sojourn end, so transitions that never
alarm (ES 21.7%, NQ 18.4% of transitions — the **miss rate**, itself a
rotor-relevant metric: roughly one in five regime shifts ends before the
detector confirms it) are not censored at random, and the KM latency median
in §3.2 is not a distribution-free estimate. Bounding sensitivity:

- **Worst case** (every censored transition assigned delay = +inf): the
  latency distribution is identified only up to its alarm fraction (q ≈ 0.783
  ES / 0.816 NQ); the worst-case median is **unchanged at 3 bars (ES) / 2
  bars (NQ)** because the alarm fraction exceeds 1/2 and the KM median sits
  far below the censoring quantile.
- **Stress statement**: even doubling L_detect outright (6 bars ES / 4 bars
  NQ) gives D_be(1.2e-4) = 7.45 (ES) / 4.54 (NQ), still below the pooled CI
  lower bounds (10.0 / 8.0) — **GO stands under the bound**.

## 6. Deviations from the frozen design (each justified; none affects the registered decision object's definition)

1. **BOCPD sensitivity detector deferred.** Design §7 names BOCPD
   (Adams & MacKay 2007) as the *sensitivity* detector for L_detect; only the
   primary CUSUM was implemented. Justification: implementation cost
   disproportionate for a sensitivity exhibit at this tier (the 1.0 `bocd.py`
   lift requires its own audit cycle per ADR-0008), and the CUSUM latency
   enters D_be additively where the margin is wide (§5.5 stress statement).
   **Registered follow-up: `P1-2.0-H900-BOCPD-SENSITIVITY`** — run BOCPD
   latency on the archived filtered sequences (no refit needed) before the
   first ADR-0002 scan consumes the regime family.
2. **CUSUM detector parameterization.** The design registers "CUSUM (Page
   1954) alarm delay against the filtered change-points" but no detector
   parameters. Implemented as the parameter-free LLR-CUSUM: increment =
   log b_j(y_t) − log b_i(y_t) under the fitted emission densities (Page's
   SPRT scheme; minimax-optimal per Moustakides 1986), threshold
   h_i = log ARL0_i with ARL0_i = 1/(1−a_ii), the fitted model's incumbent
   expected sojourn (Lorden 1971: ARL0 ≥ e^h). All inputs come from the
   training fit; nothing is tuned against the dwell outcome; anchoring the
   false-alarm horizon to the regime cadence is the conservative direction
   (larger h → longer measured latency → larger D_be).
3. **Latency censoring refinement.** "Median CUSUM alarm delay" is computed as
   the KM median with non-alarmed transitions right-censored at the observed
   sojourn end (delay convention: bars consumed from the change-point, ≥ 1);
   §5.5 reports the informative-censoring bound (QUANT-1-2).
4. **Left-censored first spells excluded from KM.** Design §8 registers
   right-censoring at window edges; the first spell of a window began before
   the window (left truncation, not right censoring — Klein & Moeschberger
   2003 §3.4). Treating its observed part as complete would bias the median
   down; treating it as right-censored would misstate the risk set. 1–2
   spells per window per segment are dropped (< 1% of spells).
5. **Warm-started evaluation filter.** The eval-window causal filter is seeded
   from the training-window terminal log-α propagated purge+embargo transition
   steps (ported 1.0 fold-continuity rule; Hamilton-filter prediction step).
   Strictly causal; a cold π start would add O(dwell) warm-up bias to the
   first spells instead.
6. **Window boundaries at UTC midnight.** The design registers calendar
   dates; half-open UTC-date boundaries applied to `ts_event` are the
   deterministic interpretation, identical on write and read.
7. **Defect-gap handling in features.** Returns spanning a registered
   exclusion gap are nulled and the rvol window restarts (classifier: valid-bar
   gap > 7 calendar days, a structural bound separating the ~3.5-week
   December-roll gaps from ≤ 4-day natural closures — not a tuned parameter);
   spell extraction runs per contiguous segment with edge censoring at the
   defect gaps.
8. **Cost-schedule registration into config/instruments.yaml.** Design §7
   declares the CME retail schedule "as registered in config/instruments.yaml",
   but the Phase C lift had deferred fee fields to the execution subpackage.
   The ES/NQ contract-spec + fee fields (and the 1.0 futures_orb_v1 1-tick
   slippage prior) were lifted from
   SKIE-Universe@ce018515:config/instruments.yaml — with the exchange-fee
   erratum of §2 applied (round-1 audit LITERATURE-1-2: $1.38 non-member
   eff. 2024-02-01 replaces the unverifiable "$1.18 Individual Member"
   annotation).
9. **Notional reference price.** The design fixes the drag formula but not the
   price in `notional = price × multiplier`. Used: median `unadjusted_close`
   over the pooled evaluation spans per instrument (actual traded price level,
   not the roll-adjusted series; deterministic, data-driven). Per-window
   frontier variation from this choice is second-order (at the central μ, the
   c_switch/μ term spans ~0.9–2.1 bars ES / ~0.3–1.1 bars NQ across the 15
   per-window median prices).
10. **Restart-seed rule via an additive port extension.** The 1.0
    `GaussianHMM.fit` derives restart seeds through `SeedSequence` with early
    exit; the design registers restarts `seed + i` exactly. `fit` gained an
    optional `restart_seeds` parameter (no other behavioral change; ported
    tests all green, extension unit-tested).
11. **Eval-span arithmetic.** The registered 15 windows tile evaluation data
    2017-01-01 → 2024-07-01; 2024-07 → 2025-12 is not consumed as evaluation
    evidence (design §9 forbids window growth). It remains unburned for
    successor hypotheses.
12. **Environment note.** numba (required to make the 15×6×5 EM grid
    computationally feasible; 1.0 kernel port) constrains numpy < 2.5 → lock
    moved numpy 2.5.1 → 2.4.6. Full pre-existing test suite (including the
    Phase C frame-hash fidelity tests) green under the new pin.
13. **Terminal-window coverage-gap parsing.** The two December-2025
    `terminal_window` register entries carry a prose upper bound; they are
    excluded open-ended through end of sample (outside every H900 window
    either way).
14. **Block-length selector correction (registered deviation from the 1.0
    port).** Round-1 audit QUANT-1-1: the 1.0-ported PW selector's Ĝ ≤ 0 sign
    guard was removed (Ĝ enters eq. 9 squared; `arch` reference behavior).
    §3.2 discloses the round-1 impact and the b ∈ [1,5] CI-invariance check.

Registered sensitivities NOT computed: **BOCPD latency only** (deviation 1).
All other registered sensitivities (grid cells, exclusion-inclusion variant,
session-truncated rule, account-dollar basis) are reported above, plus the
audit-added latency-censoring bound (§5.5).

## 7. Limitations

- **December-roll substrate defect.** 10 December windows per instrument are
  excluded in the primary analysis (repair follow-up
  `P1-2.0-DATABENTO-DEC-ROLL-REPULL`); dwell behavior *inside* those windows
  is unmeasured. The inclusion sensitivity (§5.2) bounds the impact on the
  pooled estimates (verdict unchanged).
- **Tier-0 execution fidelity (ADR-0006).** c_switch uses the static
  fee schedule + 1-tick-per-side slippage prior; no queue position, market
  impact, or regime-dependent slippage. Scalping/limit-order refinements are
  out of scope below Tier 2; a slippage escalation raises c_switch roughly
  proportionally (at 2× the 1-tick prior, ES central D_be ≈ 5.7 bars — still
  below the CI lower bound of 10).
- **CUSUM-only detection latency** (deviation 1); BOCPD may report longer
  latencies for gradual transitions. The latency-censoring bound (§5.5)
  covers the missing-alarm channel but not detector-family risk.
- **μ-scenario dependence.** D_be is hyperbolic in μ; the GO is conditional on
  conditional net edges ≳ 4e-5 per bar (notional basis) existing. The gate
  fails at μ = 1e-5 by design. The basis caveat of §4 (account-dollar) stands.
- **Grid ceiling / model granularity.** BIC selected the 4-state grid maximum
  in all 60 fits, so richer models were never rejected and the registered
  family sits at the boundary of the search space. Within the registered grid
  the observed pattern (§5.1) is that filtered dwell **lengthens** with state
  count (ES median-of-medians 5 → 8 → 13 bars for 2 → 3 → 4 states; NQ
  5 → 6 → 11) — i.e. the ceiling was conservative *in-grid*, coarser
  partitions dwell shorter — but extrapolating that monotonicity beyond
  n = 4 is untested: a finer partition could either continue to separate
  persistent structure or begin splitting states into short-lived
  sub-regimes. Any richer grid is a new hypothesis (design freeze); the GO is
  a statement about the registered model family, not an unbounded regime
  taxonomy. [Direction corrected per round-1 audit QUANT-1-3.]
- **Filtered-state estimand.** Dwell is measured on the causal filter's MAP
  path — the operationally relevant object for an allocator (it is what a
  live system observes) — not on latent "true" regimes; filter chatter near
  posterior boundaries shortens measured dwell relative to smoothed-state
  sojourns (conservative direction for the gate).
- **Left-truncation exclusion** (deviation 4) discards the longest-running
  boundary spells' partial information; direction of any residual bias is
  upward-neutral (excluded spells are length-biased samples).
- **Greenwood/Brookmeyer-Crowley CIs on heavily tied integer durations** are
  approximate; every POOLED CI in this report — the §3.2 decision CIs and the
  §5.3 session-truncated sensitivity — is stationary-bootstrap-based (the
  registered §8 method). Greenwood appears only in the per-window exhibits
  (T1) and the explicitly labeled §5.3 method comparison.

## 8. Metric-family mapping (ADR-0004 Decision 4)

Reported here: regime dwell-time vs cost break-even margin (Decision 6 object;
time series + pooled), detection latency (time series pooled to distribution,
plus miss rate per §5.5). Not applicable at this pre-allocator gate: regret vs
switching oracle, turnover-adjusted net edge, terminal-wealth lower-tail
quantile — these require an allocator and become reportable objects from the
first ADR-0007 exploration cycle onward. Note: under the proposed
aggressive-geometric-growth mandate ([ADR-0013](../../docs/decisions/ADR-0013-aggressive-geometric-growth-mandate.md),
status: proposed) the terminal-wealth lower-tail quantile is demoted from the
primary/binding wealth metric to a monitored, non-binding guardrail, and
geometric (compounded/Kelly log-wealth) growth becomes the new primary
decision/ranking metric; when this metric family becomes reportable it is
computed and reported under that demotion (no change to any figure in this
report).

## 9. Follow-ups registered by this report

- `P1-2.0-H900-BOCPD-SENSITIVITY` — **CLOSED 2026-07-11** (deviation 1). BOCPD
  sensitivity computed: CUSUM GO reproduced bit-identically, but BOCPD (unsupervised)
  verdict NO-GO both variants — the GO is supervised-detection-dependent. Detailed
  in [H900_bocpd_sensitivity_2026-07-11.md](H900_bocpd_sensitivity_2026-07-11.md).
  Refined finding: NO-GO is a corroboration-rate result (BOCPD confirms ~46-48% of
  filtered transitions, at dwell-comparable latency), not a detection-speed result.
- `P1-2.0-H900-BOCPD-WHITENED` — **NEW** (registered by the BOCPD sensitivity audit,
  QUANT-1-5): whitened/AR-robust BOCPD variant to remove the iid-within-run
  misspecification on the autocorrelated log_rvol emission, which biases L_detect
  upward. Carried to the allocator confirmation tier.
- Winning regime family (4-state diag Gaussian HMM on standardized
  (ret_5m, log rvol_5m_24h)) → candidate conditioning covariate set for
  ADR-0002 admission scans (per §10 GO consequence).
- Basis reconciliation caveat (§4) carried to the first admission scan that
  quotes a net edge (`RC-H101-1` lineage).
- Detector miss rate (ES 21.7% / NQ 18.4% of transitions end before CUSUM
  confirmation, §5.5) → standing input to the ADR-0004 detection-latency
  metric family and to allocator dwell-time feasibility at finer cadences.
