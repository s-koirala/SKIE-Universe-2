---
name: H900 — Dwell-time feasibility gate (regime sojourn vs cost break-even dwell)
description: Pre-registered design doc for hypothesis H900
type: project
hypothesis_id: H900
tier: 4
status: designed  # designed | running | evaluated | archived(positive|null|negative)
owner: SKIE
created: 2026-07-10
citations: 10.2307/1912559, 10.1093/biomet/41.1-2.100, 10.1080/01621459.1994.10476870, 10.1081/ETC-120028836, 10.1080/07474930802459016
external_doi: null
---

# H900 — Dwell-time feasibility gate (regime sojourn vs cost break-even dwell)

This document is the pre-registration record for hypothesis H900. It is frozen at
`designed` status; any change after that point requires a new hypothesis ID.

H900 is the **founding feasibility gate** mandated by
[ADR-0004 Decision 6](../../../docs/decisions/ADR-0004-rolling-evaluation-regime.md):
estimate the sojourn-time (dwell-time) distribution of candidate regime states on the
2.0 evidence-bar substrate and compare it against the break-even dwell implied by the
cost model (detection latency + cost payback). If median dwell does not exceed
break-even, the rotor premise fails empirically and that finding — not a remediation —
is the deliverable, reported before any allocator work proceeds.

## 1. Hypothesis

- **H0:** median regime dwell time D_med ≤ D_be (break-even dwell) for every
  BIC-selected regime model in the registered candidate family, at the central
  registered edge scenario (§7). Operationally: the 95% CI lower bound of D_med does
  not exceed D_be.
- **H1:** D_med > D_be for at least one BIC-selected regime model on at least one
  instrument, with the 95% CI lower bound of D_med above D_be at the central edge
  scenario — i.e., regimes persist long enough that a switching allocator can pay its
  detection latency and switching costs before the regime ends.
- **Mechanism:** discrete persistent regimes in equity-index futures returns/volatility
  (Markov-switching persistence, [Hamilton 1989](https://doi.org/10.2307/1912559);
  regime persistence and its economic sources surveyed in
  [Ang & Timmermann 2012](https://doi.org/10.1146/annurev-financial-110311-101808)).
  The allocator premise (ADR-0001) requires sojourn times materially longer than
  detection latency plus cost payback; this is an empirical property of the substrate,
  testable without any expert strategy.
- **Primary citations:** Hamilton 1989 (10.2307/1912559); Ang & Timmermann 2012
  (10.1146/annurev-financial-110311-101808); Page 1954 CUSUM
  (10.1093/biomet/41.1-2.100); Adams & MacKay 2007 BOCPD (arXiv:0710.3742).

## 2. Universe and sample period

- **Instruments:** ES, NQ (2.0 roll-adjusted continuous-contract evidence bars,
  `data/processed/vendor_legacy_1min_roll_adjusted/`, materialized by the Phase C
  ingest per ADR-0011).
- **Frequency:** 5-minute bars aggregated from the 1-minute substrate (aggregation
  rule registered in §3; justify: 1.0 regime work operated on 5-minute aggregates;
  dwell measured in 5-minute bars converts directly to minutes).
- **Session(s):** RTH and ETH both retained; session boundaries per the CME session
  rule shared with the shadow-ledger util. Dwell times are not split across the
  daily maintenance break — a sojourn interrupted by session close and resumed in the
  same state next session counts as one spell (sensitivity: session-truncated variant).
- **Sample period:** 2015-01-02 → 2025-12-31 (full materialized span).
- **Rolling-origin estimation windows (ADR-0004 Decision 2):** training window
  24 months, step 6 months, first origin 2017-01-01 — yielding 15 evaluation windows;
  dwell distributions reported per window as a time series, pooled only as a summary
  exhibit. # justify: 24m ≈ the shortest window that gave stable BIC selection in the
  1.0 HMM toolkit validation (1.0 audit trail 2026-04-23 cycle-3); step 6m matches the
  ADR-0004 metric-family reporting cadence; neither is tuned against the outcome.
- **Exclusions (registered a priori):** (a) bars flagged `pit_provisional` by the
  Phase C ingest (persistence-guard PIT windows); (b) the December-roll late-commit
  windows recorded in the substrate-defect register
  (`config/data_sources.yaml: substrate_defects[DEC_ROLL_LATE_COMMIT]`) — primary
  analysis excludes them; sensitivity includes them.
- **Roll-handling note:** roll-adjusted continuous contract (multiplicative ratio,
  Phase C port); returns computed on adjusted close-to-close log returns.

## 3. Features

HMM emission features, computed causally (data ≤ t only), versioned in the 2.0
feature registry at implementation:

- **`ret_5m@1.0.0`** — 5-minute adjusted log return.
- **`rvol_5m_24h@1.0.0`** — realized volatility: rolling sum of squared 5-minute log
  returns over the trailing 288 five-minute bars (24 hours), square-rooted.
  # justify: 24h trailing window is the 1.0 H052a emission-feature convention
  (feature set at SKIE-Universe@ce018515 src/skie_ninja/features/h052a/features.py);
  carried unchanged to preserve comparability with the 1.0 regime evidence.

Emission vector is (ret_5m, log rvol_5m_24h), standardized per training window using
training-window moments only. PIT property: pit-canary skill run on the feature
pipeline before the production run (ADR-0008).

## 4. Label construction

Not applicable — H900 is an unsupervised state-estimation study; there is no trade
label and no triple-barrier structure. # justify: ADR-0004 Decision 6 defines the
deliverable as a distributional comparison (sojourn distribution vs break-even dwell),
not a supervised prediction task. The `purge` analogue for the splitter (§6) is the
maximum feature lookback (288 bars).

## 5. Estimator

- **Model class:** Gaussian HMM, ported 1.0 toolkit
  (SKIE-Universe@ce018515 src/skie_ninja/models/regime/: log-space Baum-Welch,
  k-means++ warm start, label-switch canonicalization, causal `filter_states` as the
  sole inference path).
- **Hyperparameter grid (fixed):** n_states ∈ {2, 3, 4} × covariance ∈ {diag, full}.
  # justify: {2,3} × {diag,full} is the 1.0 H052a registered grid; 4 states added
  because dwell-time is the object of interest here and a 3-state ceiling could
  censor short-dwell structure — one increment, registered a priori, not tuned.
- **Selection:** BIC per training window (1.0 `selection.py` convention). The
  BIC-selected model per window per instrument is the unit of dwell analysis; all
  grid cells reported as sensitivity.
- **Search protocol:** exhaustive over the 6-cell grid (no stochastic search).
  EM restarts: 5 per cell with registered seed sequence derived from the §11 seed.
  # justify: restart count follows the 1.0 toolkit default validated in its cycle-3
  audit; deterministic seed derivation seed+i keeps the run exactly reproducible.
- **Loss / metric:** in-window log-likelihood → BIC for selection; no outcome-based
  tuning (dwell results never feed back into model choice — that would be selecting
  the answer).

## 6. Splitter

- **Splitter choice:** rolling-origin windows per §2 (Tashman 2000;
  Bergmeir & Benítez 2012). State inference within a window uses causal filtering
  only; no smoothing (`filter_states`, never forward-backward smoothed states, per
  the 1.0 anti-look-ahead gate).
- **`embargo` selection method:** between consecutive windows, embargo = the
  Politis-White 2004 (PPW 2009-corrected) automatic block length computed on the
  training-window 5-minute return series (lifting 1.0 `inference/bootstrap.py`).
- **`purge` derivation:** purge = 288 bars (maximum feature lookback, §3) at every
  window boundary.
- **CPCV:** not applicable (no supervised labels).

## 7. Cost model — break-even dwell derivation

- **`cost_model_id`:** `futures_rt_v1` — bar-level round-trip log-return drag
  log(1 − cost_rt / notional), notional basis (formula-consistent basis per the
  Phase B round-2 finding QUANT-2-2; the account-dollar basis is reported as a
  sensitivity column). Commission + spread schedule: CME retail schedule as
  registered in [config/instruments.yaml](../../../config/instruments.yaml)
  (ported from 1.0 with CME-cited fees).
- **Break-even dwell (registered formula):**
  D_be(μ) = L_detect + c_switch / μ, where
  - L_detect = median detection latency in bars, estimated per §5's filtered state
    sequence: CUSUM (Page 1954) alarm delay against the filtered change-points,
    with BOCPD (Adams & MacKay 2007) as sensitivity detector;
  - c_switch = one round-trip drag (exit incumbent + enter successor position) under
    `futures_rt_v1`;
  - μ = assumed per-bar conditional net edge of the successor expert.
- **Registered μ scenario grid (from the Phase B retro-card record, basis-labeled):**
  μ ∈ {1e-5, 4e-5, 1.2e-4, 2.7e-4} per 5-minute bar equivalent.
  # justify: brackets the formula-consistent notional-basis drags and the H101
  net-edge evidence (NQ unconditional ORB ≈2.7e-4 per session mean net, H052a v1;
  ES/NQ drag 1.21e-4/4.15e-5 per QUANT-2-2 recomputation); central scenario for the
  §1 decision is μ = 1.2e-4. A regime rotor only pays if edges of at least
  drag-magnitude exist conditionally — smaller μ makes D_be arbitrarily large and the
  gate unpassable, which is the correct behavior.
- **Slippage model version:** none beyond the registered spread component at this
  tier (Tier-0 fidelity per ADR-0006; limit-order/scalping claims out of scope).

## 8. Gate thresholds

- **`alpha`:** 0.05 (two-sided CIs; decision uses the one-sided lower bound).
- **CI method:** median dwell per window via Kaplan-Meier (right-censoring at window
  edges for spells in progress) with Greenwood-based CI; pooled-median CI via
  stationary bootstrap (Politis & Romano 1994) over spell sequences with automatic
  block length (Politis & White 2004; Patton, Politis & White 2009).
- **`bh_threshold`:** not applicable — single pre-registered analysis; H900 is
  registered in `config/multipletest_family.yaml` as a singleton family (methodology
  gate), so no BH correction is due. Any post-hoc scan on this substrate joins the
  family and triggers the multipletest-gate.
- **`dsr_activation_size`:** not applicable (no Sharpe-family selection surface).
- **Power target:** descriptive feasibility gate; precision requirement registered
  instead of power: the pooled D_med 95% CI half-width must be < 25% of the point
  estimate for the primary (BIC-selected) cell, else the verdict is "indeterminate —
  insufficient spells" rather than go/no-go. # justify: precision-based reporting for
  non-comparative estimation (CONSORT-style precision framing); avoids retrospective
  power (Hoenig & Heisey 2001, 10.1198/000313001300339897).

## 9. Stopping rule

- **Stop criterion:** fixed design — all 15 rolling windows × 2 instruments × 6 grid
  cells, then stop. No extension, no additional windows, no grid growth.
- **Max folds:** 15 windows (fixed by §2 arithmetic).
- **Max wall-clock budget:** one production run; if EM non-convergence occurs in a
  cell, the cell is reported non-converged (dead-state/PD-ridge event recording per
  the 1.0 toolkit), never re-run with different settings.

## 10. Decision rule

- **If H1 criterion met** (CI lower bound of D_med > D_be(μ=1.2e-4) for the
  BIC-selected model on ≥1 instrument): **GO** — archive(positive); the allocator
  program proceeds; dwell-time metric family becomes a standing ADR-0004 report
  object; the winning regime family is registered as the candidate conditioning
  covariate set for ADR-0002 admission scans.
- **If H1 criterion not met on any instrument:** **NO-GO** — archive(null); the
  rotor premise fails empirically at the registered cost/edge scenarios; finding
  reported per ADR-0004 Decision 6 before any allocator work; program pivot decision
  escalates to the operator (e.g., slower-cadence allocation or Tier-2 execution
  fidelity work to lower c_switch).
- **If precision requirement (§8) unmet:** archive(null, indeterminate-precision)
  with the registered follow-up to extend the substrate (more symbols/years), not
  the window count.
- Null results stay in the register per the non-loss policy; "fail" is not a
  disposition (ADR-0009).

## 11. Reproducibility commitments

- **git HEAD (at run):** auto-populated
- **`uv pip freeze` sha (at run, 64-hex):** auto-populated
- **RNG seed:** 20260710  # justify: pre-registered; EM restart seeds derived as
  seed + restart_index; do not modify post-hoc
- **Dataset checksums (frozen at pre-reg from `data/_manifest.json`):** the
  `data/processed/vendor_legacy_1min_roll_adjusted/` per-file SHA-256 entries as of
  the freeze commit (manifest itself SHA-referenced by the freeze ReproLog).
- **Reproducibility log path:** `logs/reproducibility/repro_log_<run_id>.json`
- **Design.md SHA at freeze:** auto-populated by /preregister (R3-2a)
