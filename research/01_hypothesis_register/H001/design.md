---
name: H001 — Small-n volatility×trend regime label as a non-redundant conditioning covariate
description: Pre-registered design doc for hypothesis H001
type: project
hypothesis_id: H001
tier: 3
status: designed  # designed | running | evaluated | archived(positive|null|negative)
owner: SKIE
created: 2026-07-16
citations: 10.1086/296565, 10.1093/rfs/1.1.41, 10.1016/j.jfineco.2011.11.003, 10.1111/j.1540-6261.1990.tb05110.x, 10.1007/BF01908075, 10.3905/jpm.1989.409211, 10.1111/j.1468-0262.2005.00615.x, 10.1086/296071, 10.1080/01621459.1994.10476870, 10.1016/S0169-2070(00)00065-0, 10.1016/j.ins.2011.12.028, 10.1081/ETC-120028836, 10.1080/07474930802459016, 10.1198/000313001300339897
external_doi: null
---

# H001 — Small-n volatility×trend regime label as a non-redundant conditioning covariate

This document is the pre-registration record for hypothesis H001. It is frozen at
`designed` status; any change after that point requires a new hypothesis ID.

H001 reframes the exploration-tier "meta-shift SMA(3)/StdDev(3)" prototype
(untracked working-tree scaffolding: `src/skie_universe2/signals/meta_shift_signal.py`,
`.../policy/meta_shift_policy.py`, `.../execution/tier1_intrabar.py`,
`explorations/meta_shift_exploration.py`) from a standalone directional scalping
strategy into a **conditioning covariate** in the sense of
[ADR-0001 Decision 5](../../../docs/decisions/ADR-0001-allocator-unit-of-inference.md)
(covariate / allocator-prior-tilt, never a position gate) and
[ADR-0002 Decision (b)/(d)](../../../docs/decisions/ADR-0002-arsenal-admission-standard.md)
(pre-declared conditioning set; non-redundancy). Under
[ADR-0001](../../../docs/decisions/ADR-0001-allocator-unit-of-inference.md) the
allocator is the unit of inference and there is no standalone strategy gate; a
pair of small-n indicators (one volatility, one trend) is therefore evaluated for
the information its regime label carries, not for a strategy P&L.

**Governance-imposed scope split (binding).** Two program blocks gate the
strategy-value question and are respected by construction here:

1. The **shadow ledger** (ADR-0003, the sole evidence source for any *conditional
   gross-edge* claim) is still being backfilled. Any ADR-0002(c) conditional-edge
   scan on expert return series is therefore **deferred** (§7, §10-Deferred).
2. **Geometric-growth ranking and Kelly-fraction selection are BLOCKED** until the
   two Decision-9 memos (`P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`,
   `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`) are numerically instantiated on
   the ledger, and the discovery-alpha level is an OUTPUT of the latter
   (`config/multipletest_family.yaml: screening_error_rate_target = null`). No arm
   of any scan below is declared a winner on geometric growth in this hypothesis.

The **primary** H001 analysis is a **covariate-layer information study** that needs
neither the shadow ledger nor Kelly selection: it measures whether the small-n
vol×trend regime partition carries structure *not already captured* by the
registered H900 HMM regime covariate (`regime_hmm_h900`) or the project-standard
variance-ratio state, for the forward **reversion vs continuation** structure the
user's premise targets. It runs on the same substrate H900 ran on
(`data/processed/vendor_legacy_1min_roll_adjusted/`). The conditional-gross-edge
scan and any growth ranking are pre-registered here but sequenced behind the
backfill.

## 1. Hypothesis

Let `S_vt(t)` be the small-n vol×trend regime label (§3, §5), `S_hmm(t)` the H900
filtered 4-state HMM label (`regime_hmm_h900`), and `S_vr(t)` the project-standard
variance-ratio trend/range state. Let the forward structure target be `Y(t)` =
the sign/magnitude of short-horizon return autocorrelation over the next `h` bars,
operationalized as the forward variance ratio `VR_h(t)` (§4).

- **H0 (primary — redundancy):** conditioning on `S_vt` adds no information about
  `Y` beyond `{S_hmm, S_vr}`. Operationally, the conditional-mutual-information
  lower bound `I(Y ; S_vt | S_hmm, S_vr) ≤ 0` (its rolling-origin 95% CI lower
  bound does not exceed 0), AND `S_vt` does not improve out-of-sample forward-`Y`
  prediction over the `{S_hmm, S_vr}`-only baseline (nested log-loss / R² delta 95%
  CI lower bound ≤ 0).
- **H1 (primary):** `I(Y ; S_vt | S_hmm, S_vr) > 0` with 95% CI lower bound above
  0 for at least one grid arm surviving the §8 multiplicity correction, AND a
  positive nested out-of-sample forward-`Y` predictive-information delta on the
  same arm — i.e., the small-n vol×trend label is a **non-redundant** conditioning
  covariate for reversion/continuation.
- **Mechanism:** the sign and magnitude of short-horizon return autocorrelation are
  volatility-state dependent — higher-volatility states exhibit weaker/negative
  autocorrelation (reversion), lower-volatility states weaker mean reversion /
  relatively more continuation — documented in
  [LeBaron 1992](https://doi.org/10.1086/296565) (autocorrelation-volatility
  relation) and consistent with short-horizon reversal
  ([Jegadeesh 1990](https://doi.org/10.1111/j.1540-6261.1990.tb05110.x)) versus
  time-series continuation
  ([Moskowitz, Ooi & Pedersen 2012](https://doi.org/10.1016/j.jfineco.2011.11.003)),
  measured through the variance-ratio lens
  ([Lo & MacKinlay 1988](https://doi.org/10.1093/rfs/1.1.41)). A small-n
  vol×trend label is a fast, low-latency estimator of that state; the empirical
  question is whether its construction adds information beyond the slower
  HMM/variance-ratio covariates already registered.
- **Primary citations:** LeBaron 1992 (10.1086/296565); Lo & MacKinlay 1988
  (10.1093/rfs/1.1.41); Jegadeesh 1990 (10.1111/j.1540-6261.1990.tb05110.x);
  Moskowitz, Ooi & Pedersen 2012 (10.1016/j.jfineco.2011.11.003); Hubert & Arabie
  1985 partition comparison (10.1007/BF01908075).

## 2. Universe and sample period

Adopted **by reference** from the H900 frozen design
([research/01_hypothesis_register/H900/design.md](../H900/design.md) §2), to keep
the covariate comparison on an identical substrate to the incumbent
`regime_hmm_h900`:

- **Instruments:** ES, NQ (2.0 roll-adjusted continuous-contract evidence bars,
  `data/processed/vendor_legacy_1min_roll_adjusted/`, ADR-0011).
- **Frequency:** 5-minute bars aggregated from the 1-minute substrate (H900 §3
  aggregation rule, by reference).
- **Session(s):** RTH and ETH both retained; H900 session rule by reference.
- **Sample period:** 2015-01-02 → 2025-12-31 (full materialized span).
- **Rolling-origin windows (ADR-0004 Decision 2):** 24-month training, 6-month
  step, first origin 2017-01-01 — identical to H900 §2 so window-by-window
  covariate comparability holds. All information/prediction deltas are computed
  out-of-sample on the 6-month test slice that follows each training window.
  # justify: identical to H900 §2 (24m stable-BIC floor; 6m ADR-0004 cadence);
  reused, not re-tuned.
- **Exclusions (registered a priori):** identical to H900 §2 — (a) `pit_provisional`
  bars; (b) `substrate_defects[DEC_ROLL_LATE_COMMIT]` windows excluded in primary,
  included in sensitivity.
- **Roll-handling:** roll-adjusted continuous contract; close-to-close adjusted log
  returns (H900 §2 by reference).

## 3. Features

All features causal (data ≤ t only; no smoothing), versioned in the 2.0 feature
registry at implementation. The registered object is the **vol×trend regime label**
built from one volatility indicator and one trend indicator, each over a small
window `n`. The indicator families and window grid are the pre-registered scan
surface (§5, §8).

- **Trend-indicator family (small-n), `T_fam × n_t`:**
  - `sma_slope` — sign/level of the SMA(`n_t`) first difference (the prototype's
    indicator).
  - `ema` — EMA(`n_t`) vs price (span = `n_t`).
  - `kama` — Kaufman adaptive MA(`n_t`) (efficiency-ratio-weighted; practitioner
    estimator, [Kaufman 2020 *Trading Systems and Methods*, 6th ed. (ISBN 9781119605355)](https://www.wiley.com/en-us/Trading+Systems+and+Methods%2C+6th+Edition-p-9781119605355), *practitioner*).
  - `linreg_slope` — slope of an OLS fit over the trailing `n_t` bars.
- **Volatility-indicator family (small-n), `V_fam × n_v`:**
  - `rolling_std` — rolling sample StdDev(`n_v`) of log returns (the prototype's
    indicator; ddof=1, requires `n_v ≥ 2`).
  - `atr` — average true range over `n_v` bars (needs OHLC).
  - `parkinson` — Parkinson high-low range vol over `n_v` bars
    ([Parkinson 1980](https://doi.org/10.1086/296071)).
  - `realized_vol` — √(rolling sum of squared log returns over `n_v` bars).
- **Window grid `n_v, n_t ∈ {2, 3, 4, 5, 8}`.**
  # justify: bracketed strictly BELOW the H900 dwell floor. H900 §10 established
  median regime dwell D_med = 9-12 bars (ES pooled 12 [10,14]; NQ 9 [8,10]). A
  regime-change label intended to react *faster* than the dwell it partitions must
  have window well below that floor; the lower edge n=2 is the ddof=1 StdDev
  minimum, the upper edge n=8 is the largest window still strictly below the NQ
  median dwell (9). Interior spacing is unit steps over the dense fast-reaction
  region {2,3,4,5} plus a single upper probe at n=8; 6 and 7 are omitted
  deliberately — they are near-duplicates of 5 and 8 for a rank/sign discretizer
  (§5) and would inflate the arm family (and thus the FWER penalty, §8) without
  adding a materially different reaction speed. The grid is derived from a frozen
  prior result, not tuned to the H001 outcome; it is fixed at pre-registration
  (§9).
- **Registered comparison covariates (frozen conditioning set, ADR-0002(b)):**
  - `S_hmm` = `regime_hmm_h900` (4-state diag-Gaussian HMM MAP filtered state;
    [config/conditioning_covariates.yaml](../../../config/conditioning_covariates.yaml)).
  - `S_vr` = project-standard `variance_ratio_state` (Lo & MacKinlay 1988
    trend/range), computed at the H900 5-minute frequency.

PIT property: the pit-canary skill (ADR-0008) is run on the full feature pipeline
before the production run; every indicator, the state discretizer (§5), and the
forward target (§4) are recomputed from the causal pipeline only.

## 4. Label construction

The forward-structure target `Y(t)` (the reversion-vs-continuation object) is a
**per-observation within-window realized variance-ratio proxy** over horizon `h`.
Let `r_{t+1}, …, r_{t+h}` be the `h` five-minute log returns in the forward window
`(t, t+h]`. Define

`VR_h(t) = (Σ_{i=1}^{h} r_{t+i})² / (h · RV_h(t))`, with
`RV_h(t) = (1/h) Σ_{i=1}^{h} r_{t+i}²` the within-window realized per-bar variance.

The numerator is the squared cumulative `h`-bar return; the denominator is `h`
times the forward-window realized per-bar variance, so `VR_h(t)` is
**self-normalizing** — it isolates serial-correlation shape from the volatility
*level* (both numerator and denominator scale with variance), and it is bounded in
`[0, h]` (Cauchy-Schwarz). Under a random walk `E[VR_h] ≈ 1`; `VR_h < 1` ⇒ negative
serial correlation (reversion), `VR_h > 1` ⇒ positive serial correlation
(continuation). This is a **single-observation proxy** for the serial-correlation
structure that the full-sample overlapping-block variance ratio of
[Lo & MacKinlay 1988](https://doi.org/10.1093/rfs/1.1.41) estimates in aggregate;
it is deliberately noisy per `t` (one draw), and the reversion/continuation signal
lives in its *conditional mean* `E[VR_h | S]`, which the CMI and nested-prediction
estimators (§5) recover by aggregating over many `t`. It is not the full-sample
Lo-MacKinlay `VR(q)` statistic and is not attributed as such. # justify: the
denominator is the forward-window realized variance (not a training-window
constant), removing any train-vs-forward variance ambiguity and any conditional
heteroskedasticity confound; `Y` is a forward *target* only (never a feature),
purged per §6.
- **Sensitivity variant:** an overlapping-sub-block VR over `q ∈ {2,3}` inside a
  `2h`-bar forward window (closer to the Lo-MacKinlay overlapping-block estimator),
  reported alongside the primary single-window proxy. Its forward-label span is `2h`
  bars, so it takes the horizon-aware purge `2h` (§6), not `h`.
- **Degenerate-window rule (registered a priori):** `VR_h(t)` is `0/0` when the
  forward realized variance `RV_h(t)=0`, i.e. all `h` forward log-returns are
  exactly zero (possible on flat/illiquid ETH 5-minute bars, which §2 retains). Any
  `t` with `RV_h(t)=0` (equivalently `Σ r_{t+i}²=0`) is **dropped** from both the
  CMI and the nested-prediction samples for that horizon; the dropped-bar count and
  its incidence by session (RTH/ETH) are reported. # justify: an a-priori exclusion
  of an undefined target, registered before the run per the H900 §2
  exclusion-registration convention; not an outcome-dependent filter.

- **Horizon `h ∈ {6, 12}` five-minute bars** (30 min, 60 min).
  # justify: `h=12` (primary) sits inside the ES median-dwell CI [10,14] (H900 §3),
  so it measures forward structure over roughly one regime sojourn. `h=6` is a
  deliberate **sub-dwell early-structure probe**, explicitly BELOW the dwell floor
  (NQ median 9, CI [8,10]): reversion/continuation frequently manifests in the
  first half of a sojourn, before the regime ends, so the shorter horizon tests
  whether the label carries structure that resolves faster than the full dwell.
  The two horizons therefore bracket "within one sojourn" (12) and "first
  half-sojourn" (6); neither is the H900 dwell range itself (9-12) — that
  characterization is corrected here. Both reported; fixed at pre-registration.
- **Look-ahead control:** `Y(t)` uses data in `(t, t+h]` and is therefore a
  forward label; it is used ONLY as a prediction/association *target*, never as a
  feature. The evaluation `purge` (§6) removes the `h`-bar forward overlap between
  train and test so no test-window target leaks into training. The state labels
  `S_vt, S_hmm, S_vr` are strictly causal (≤ t).
- This is not a triple-barrier trade label; there is no position or cost here. The
  supervised object is forward realized structure, not a trade outcome.
  # justify: the primary claim is covariate information (ADR-0002(d) non-redundancy),
  not a trade P&L; the P&L claim is the deferred conditional-edge scan (§7, §10).

## 5. Estimator

**State construction (`S_vt`), magic-number-free by construction.** For each grid
arm `(T_fam, V_fam, n_t, n_v)`:

- **Volatility sub-state** ∈ {contract, expand}: the chosen volatility indicator is
  below (contract) or at/above (expand) its **training-window median**. The split
  point is the training-window median only (no eval leakage), a rank statistic, not
  a tuned threshold — replacing the prototype's `STDDEV_LOW_LOOKBACK=10` /
  `STDDEV_CONSEC_RISE=2` constants.
- **Trend sub-state** ∈ {up, down}: sign of the chosen trend indicator (slope sign,
  or price-vs-MA sign for `ema`/`kama`) — a sign statistic, no threshold.
- **Regime label `S_vt` ∈ {contract-up, contract-down, expand-up, expand-down}**
  (4 categorical states), plus `undetermined` during the leading `max(n_v, n_t)-1`
  warm-up bars. This is the pure covariate emitter: it outputs a per-bar state
  only, no direction/strength/size (those belonged to the demoted strategy layer).
  # justify: the 4-state contract/expand × up/down partition is the minimal faithful
  encoding of the prototype's reversal(=vol-contract)/momentum(=vol-expand+cross)
  logic as a covariate; the reversal/momentum *interpretation* is now an output of
  the §4 test (which state predicts VR<1 vs VR>1), not an assumed label. Note the
  prototype's assumed mapping (low-vol/contract → reversal, high-vol/expand →
  momentum) is the OPPOSITE of the §1 LeBaron mechanism (high-vol → weaker/negative
  autocorrelation → reversion); the design does not assume either direction — §4
  measures empirically which state predicts VR<1 vs VR>1, so the mechanism sign is
  a result, not a pre-registered assumption, and the two statements are reconciled
  by the test rather than by fiat.

**Information estimators (primary):**

- **Redundancy vs registered covariates (partition comparison):** adjusted Rand
  index ([Hubert & Arabie 1985](https://doi.org/10.1007/BF01908075)) and adjusted
  mutual information ([Vinh, Epps & Bailey 2010, JMLR 11:2837-2854](https://www.jmlr.org/papers/v11/vinh10a.html))
  between `S_vt` and each of `S_hmm`, `S_vr` — descriptive overlap, reported per
  window.
- **Conditional mutual information** `I(Y ; S_vt | S_hmm, S_vr)` estimated on
  discretized `Y` (sign-of-`VR_h − 1` binary, plus a 3-bin magnitude variant as
  sensitivity), with a Miller-Madow bias correction. The null is a **conditional
  (stratified) restricted permutation**: `Y` is permuted ONLY within strata of the
  conditioning set `Z = {S_hmm, S_vr}` (within-`Z`-cell shuffles), which preserves
  `p(Y | Z)` while breaking only the `Y`–`S_vt` link — the correct reference for the
  conditional null `Y ⊥ S_vt | Z`. A global (unstratified) permutation of `Y` would
  additionally destroy the `Y`–`Z` dependence, drawing the null from `p(Y)p(S_vt,Z)`
  and altering the occupied-cell counts (hence the Miller-Madow plug-in bias),
  inflating Type-I; it is explicitly NOT used. Restricted-permutation surrogate per
  [Runge 2018, AISTATS PMLR 84:938-947](https://proceedings.mlr.press/v84/runge18a.html).
  This is the primary decision statistic (§8).
- **Nested out-of-sample predictive-information delta:** multinomial/logistic model
  of `Y`-sign on `{S_hmm, S_vr}` (baseline) vs `{S_hmm, S_vr, S_vt}` (augmented);
  test-slice log-loss and McFadden-R² deltas. This is the information-theoretic
  analogue of the ADR-0002(d) non-redundancy criterion — the marginal information
  a covariate adds beyond the spanned set, the covariate-layer counterpart of the
  marginal-IR / fundamental-law framing of
  [Grinold 1989](https://doi.org/10.3905/jpm.1989.409211) that ADR-0002(d) invokes
  for return-series non-redundancy. Guards against a CMI artifact — a covariate that
  is informative in-sample but does not improve honest OOS prediction fails H1.

**No outcome-based tuning:** window grid, indicator families, discretizer
(median/sign), horizons, and estimators are all fixed at pre-registration; nothing
in §3-§5 is selected on the H001 outcome.

## 6. Splitter

- **Splitter:** rolling-origin per §2 (Tashman 2000; Bergmeir & Benítez 2012), all
  deltas computed on the out-of-sample 6-month test slice after each training
  window. State discretizer moments (§5 median split) and any model coefficients
  are estimated on the training slice only.
- **`purge` (horizon-aware):** `max(feature_lookback, forward_window)` bars at each
  train/test boundary, where `feature_lookback = max(n_v, n_t)` and `forward_window`
  is the full forward-label span — `h` for the primary single-window target and
  `2h` for the `2h`-bar overlapping-sub-block sensitivity variant (§4). The
  forward-label span (not `feature_lookback`, which is ≤ 8) is the binding term and
  removes the entire forward-target overlap; a fixed `h` purge would leak the
  `(h, 2h]` tail of the sensitivity variant's label into the training slice, so the
  purge is matched to each target's own horizon (López de Prado 2018, ch. 7 — purge
  spans the full forward-label horizon).
- **`embargo`:** Politis-White 2004 (PPW 2009-corrected) automatic block length on
  the training-window 5-minute return series (H900 §6 by reference).
- **CPCV:** not applicable (single forward target, time-ordered evaluation).

## 7. Cost model — scope statement

- **Primary analysis (covariate information):** no cost model — it measures
  covariate information about forward realized structure, not a traded return.
  Execution fidelity (ADR-0006) does not bind because no execution-dependent claim
  is made.
- **Deferred conditional-gross-edge scan (ADR-0002(c)):** when the shadow ledger
  (ADR-0003) is backfilled, conditional *pre-cost* edge of arsenal experts is
  scanned over the `S_vt` cells with Romano-Wolf correction within the scan
  ([Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x)). Cost
  model `futures_rt_v1` (H900 §7) applies at the position/execution layer, not at
  admission (ADR-0002 Consequences). **Switching-cost / detection-latency caveat
  (binding):** any regime-conditioned rotor built on `S_vt` must budget switch cost
  at a *realistic unsupervised* detection latency, never the supervised-CUSUM
  oracle — H900 BOCPD sensitivity showed a live detector corroborates only ~46-48%
  of filtered transitions; under the ADR-0013 leverage mandate an oracle latency
  manufactures fake compounded edge (ruin), so this tightens as the Kelly fraction
  rises. Inherited verbatim in intent from `regime_hmm_h900.detection_cost_caveat`.
- **Scalping-claim ceiling (ADR-0006):** no scalping hold-time or limit-order claim
  is made or reportable at any tier in H001; the demoted directional prototype
  (`meta_shift_policy`, `tier1_intrabar`) is retained only as exploration-tier
  smoke-test infrastructure, explicitly labeled Tier 1 and out of scope for this
  hypothesis's evidence.

## 8. Gate thresholds

- **`alpha`:** 0.05 (two-sided CIs; H1 decision uses the one-sided lower bound).
  # justify: conventional two-sided nominal level; this governs ONLY the descriptive
  per-arm CIs. The binding discovery/FWER level is NOT 0.05 — it is the deferred
  project-wide `screening_error_rate_target` OUTPUT of
  `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` (currently `null`), so no discovery
  is certified at 0.05 or any level until that memo is instantiated (§10). 0.05 is
  therefore not a discovery threshold and not an H001-tuned constant.
- **CI method:** stationary bootstrap ([Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870))
  with automatic block length (Politis & White 2004; Patton, Politis & White 2009),
  matching the ADR-0004 inference stack, resampled over the **pooled bar-level
  statistic-contribution series** (per-bar CMI/log-loss contributions within each
  test slice), NOT over the 15 rolling-window summaries. # justify: 15 window
  summaries is too few points for reliable automatic block-length selection and
  stationary-bootstrap CIs; bootstrapping the bar-level contribution series (as H900
  bootstraps bar/spell-level statistics for its dwell CIs, H900 §8) keeps the
  effective sample large and the block length estimable, while windows remain the
  out-of-sample evaluation unit. CMI significance additionally checked against the
  §5 **conditional (within-`Z`-cell) restricted-permutation** null — `Y` permuted
  only within strata of `Z = {S_hmm, S_vr}`, preserving `p(Y | Z)` (Runge 2018) —
  never a global permutation.
- **Multiplicity (`bh_threshold` analogue):** the scan is
  `T_fam(4) × V_fam(4) × n_t(5) × n_v(5) = 400` arms × 2 horizons. FWER control by
  **Romano-Wolf stepwise** ([Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x))
  with the serial-dependence-preserving block bootstrap (ADR-0002(c) default), over
  the full arm family. Registered as a **new family** `h001-volxtrend-covariate` in
  [config/multipletest_family.yaml](../../../config/multipletest_family.yaml)
  (`correction: romano-wolf`). The screening/FWER **level** is NOT set here: it is
  the OUTPUT of the project-wide `screening_error_rate_target`
  (`P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`), currently `null`; until that
  memo is numerically instantiated the scan is **run and fully reported as
  descriptive**, and no arm is certified as a discovery (§10). # justify: the
  discovery-error target is a registered project parameter, never a per-hypothesis
  constant (ADR-0002(c)). **Null coherence (registered):** when the screening level
  is instantiated, the Romano-Wolf FWER null MUST be generated by the same joint
  within-`Z`-cell restricted permutation used for the per-arm CMI null (§5), not by
  the bar-level block bootstrap, so the family-wise conditional null stays coherent
  with the per-arm conditional null `Y ⊥ S_vt | Z`; the block bootstrap furnishes
  the per-arm descriptive CIs only. This binds the deferred certification step; it
  does not affect the descriptive run.
- **`dsr_activation_size` / PBO:** the primary object is CMI/predictive-information,
  not a Sharpe-selection surface, so DSR/PBO do not bind the primary. They DO bind
  the deferred conditional-edge scan (ADR-0007/0008), which appends every arm to the
  trial register and runs the matched-turnover random rotor and PBO before any arm
  informs allocation.
- **Precision target:** for the primary CMI decision, the pooled `I(Y;S_vt|·)` 95%
  CI half-width must be < 25% of the point estimate on the reported arm, else the
  verdict is "indeterminate — insufficient windows" rather than GO/NO-GO (H900 §8
  precision-framing convention; avoids retrospective power, Hoenig & Heisey 2001).
  # justify: the 25% half-width fraction is inherited VERBATIM from the H900 §8
  precision convention (CONSORT-style precision framing), not an H001-tuned constant;
  it is a qualitative reporting convention, not an empirically derived threshold, and
  is carried unchanged for cross-hypothesis comparability with H900.

## 9. Stopping rule

- **Stop criterion:** fixed design — all 400 arms × 2 horizons × 15 rolling windows
  × 2 instruments, then stop. No arm added, no window added, no horizon added,
  no grid growth post-freeze.
- **Max folds:** 15 windows (fixed by §2 arithmetic), × 2 instruments.
- **Wall-clock budget:** one production run; a non-converged model cell (§5 nested
  logistic) is reported non-converged, never re-run with different settings.

## 10. Decision rule

**Primary (runnable now, ledger-independent):**

- **If H1 met** (∃ arm with `I(Y;S_vt|S_hmm,S_vr)` 95% CI lower bound > 0 AND
  positive nested OOS predictive-information delta, surviving §8 multiplicity once
  the screening level is set; reported descriptively until then): **GO** —
  `S_vt` (the specific reported arm's family/window) is registered as a
  **candidate** ADR-0002(b) conditioning-covariate extension in
  [config/conditioning_covariates.yaml](../../../config/conditioning_covariates.yaml)
  alongside `regime_hmm_h900` (status `candidate`, not `adopted`; adoption requires
  an admitted expert conditioning on it). The reversal/continuation
  *interpretation* of each state is reported (which state predicts VR<1 vs VR>1).
- **If H0 not rejected on any arm:** **NO-GO** — archive(null); the small-n
  vol×trend label is redundant with the registered HMM/variance-ratio covariates
  for forward reversion/continuation; finding retained per the non-loss policy. The
  demoted directional prototype is not promoted.
- **If precision (§8) unmet:** archive(null, indeterminate-precision) with the
  registered follow-up to extend the substrate (more symbols/years), not the grid.

**Deferred (sequenced behind the shadow-ledger backfill + the two BLOCKING Kelly
memos):**

- The ADR-0002(c) **conditional-gross-edge** scan of arsenal experts over the
  `S_vt` cells, and any **geometric-growth** comparison of `S_vt`-conditioned vs
  HMM-conditioned vs unconditioned allocation, run only after the ledger is
  backfilled and both Kelly memos are numerically instantiated. No Kelly fraction
  is selected and no growth winner is declared in H001.

Null results stay in the register; "fail" is not a disposition (ADR-0009). Whatever
the disposition, the terminal deliverable is an Expert/Covariate Card (ADR-0009
adapted for a covariate).

## 11. Reproducibility commitments

- **git HEAD (at run):** auto-populated
- **`uv pip freeze` sha (at run, 64-hex):** auto-populated
- **RNG seed:** 20260716  # justify: pre-registered; bootstrap/permutation seeds
  derived as seed + replicate_index; do not modify post-hoc
- **Dataset checksums (frozen at pre-reg from `data/_manifest.json`):** the
  `data/processed/vendor_legacy_1min_roll_adjusted/` per-file SHA-256 entries as of
  the freeze commit (manifest itself SHA-referenced by the freeze ReproLog);
  identical substrate to H900.
- **Reproducibility log path:** `logs/reproducibility/repro_log_<run_id>.json`
- **Design.md SHA at freeze:** auto-populated by /preregister (R3-2a)
