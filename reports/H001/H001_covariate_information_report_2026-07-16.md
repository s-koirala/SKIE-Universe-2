# H001 — Small-n volatility×trend regime label as a conditioning covariate

**KPI / disposition report (ADR-0009 covariate card).** Terminal deliverable for
hypothesis **H001** (frozen design
[research/01_hypothesis_register/H001/design.md](../../research/01_hypothesis_register/H001/design.md),
SHA-256 `6c875b789898…`).

**Disposition: `archive(null)`** — the small-n vol×trend regime label does **not**
carry robust, material, non-redundant **out-of-sample predictive** information
about forward reversion/continuation beyond the registered H900 HMM covariate
(`regime_hmm_h900`) and the project-standard variance-ratio state. The covariate
is **not promoted** to the ADR-0002(b) conditioning registry. Null result retained
per the non-loss policy (ADR-0009: "fail is not a disposition").

Run: ReproLog `repro_log_e97678dfddf64306876ad5a34efb2956`, seed 20260716,
git HEAD at run recorded, substrate `vendor_legacy_1min_roll_adjusted` (ES, NQ),
2015-01-02 → 2025-12-31, primary exclusion variant.

## 1. Question

Does the small-n vol×trend 4-state label `S_vt` (frozen design §3–§5: a
training-window median-split volatility sub-state × trend-sign sub-state, over a
`{2,3,4,5,8}` window grid × 4 trend families × 4 vol families = 400 arms) add
**non-redundant** information about the forward reversion/continuation structure
`Y_h` (the §4 self-normalizing within-window variance-ratio proxy, sign-labelled,
horizons h∈{6,12}) **beyond** `Z = {S_hmm, S_vr}`? Primary statistic: the §5
conditional mutual information `I(Y; S_vt | Z)` (Miller-Madow) with the §5 nested
out-of-sample predictive-information delta as the artifact guard.

## 2. Methods

Per instrument × 15 rolling-origin windows (H900 §2, 24m train / 6m step / first
origin 2017-01-01; purge = 288 bars; PW-selected embargo): `S_hmm` = the
registered 4-state diagonal-Gaussian HMM MAP filtered state (causal warm-started
filter); `S_vr` = causal Lo-MacKinlay variance-ratio trend/range state; `Y_h` =
forward-VR sign label. Per arm: leakage-safe emitter (`S_vt`), then on the
out-of-sample eval slice the Miller-Madow CMI, adjusted-Rand/AMI redundancy, and
the nested train→eval predictive-information delta (saturated cell-frequency
model, the MLE of a logistic on `Z`-cells vs `Z×S_vt` joint cells). Binding pooled
CMI = n-weighted average of per-window Miller-Madow CMI; 95% CI via the §8
pooled-bar-level stationary bootstrap shifted onto the MM-corrected scale. **H1
(per arm/instrument/horizon):** CMI 95% CI lower bound > 0 **AND** mean OOS
`delta_logloss` > 0.

The discovery/FWER screening level is the DEFERRED project-wide
`screening_error_rate_target` (`config/multipletest_family.yaml`, `null`), so the
scan is **descriptive** — no arm is certified as a discovery (design §8/§10).

## 3. Results

1600 arm-horizon records (400 arms × 2 horizons × 2 instruments).

| Metric | ES | NQ |
|---|---|---|
| CMI(MM) nats — median (min…max) | 6.6e-4 (1.4e-4 … 1.4e-3) | 4.6e-4 (1.1e-4 … 9.7e-4) |
| Candidate arms (MM-CMI > 0) | 800 / 800 | 800 / 800 |
| **H1 arms** (CI>0 **and** OOS delta>0) | **283 / 800** | **0 / 800** |
| OOS `delta_logloss` — median (max) | −3.8e-5 (2.0e-4) | −1.4e-4 (**−2.4e-5**) |
| OOS `delta_mcfadden` — max | 3.4e-4 | **−3.9e-5** |
| ARI vs `S_hmm` (max) | 0.081 | 0.080 |
| ARI vs `S_vr` (max) | 0.005 | 0.001 |

- **The out-of-sample guard fails.** Only **17.7%** of all 1600 arm-horizons have
  a positive mean OOS `delta_logloss`; on **NQ every arm is negative** (max
  −2.4e-5), i.e. adding `S_vt` *worsens* honest out-of-sample prediction on NQ
  without exception. This is exactly the §5 artifact the nested delta is designed
  to catch — "a covariate informative in-sample but not improving honest OOS
  prediction fails H1."
- **The in-sample CMI is a large-N residual, not signal.** MM-corrected CMI is
  tiny-positive everywhere (~1e-4–1e-3 nats ≈ 1e-4–1.4e-3 bits). At ~1e5 pooled
  eval bars per arm even a negligible association clears the CI>0 bar, so the
  candidate count (800/800) and the ES H1 count carry no material weight — the
  binding screening level (deferred) is what would weigh this against the 400-arm
  multiplicity.
- **The ES "H1" set is marginal and fragile.** Among the 283 ES H1 arms the OOS
  delta is positive in a median of only **53%** of the 15 windows
  (`frac_windows_delta_pos` ≈ 0.53 — coin-flip), the mean improvement is negligible
  (median `delta_logloss` 5.2e-5, max 2.0e-4 → ≤0.03% of the 0.69-nat baseline;
  max McFadden ΔR² 3.4e-4), and the arms are scattered across all trend families
  (ema/linreg/sma/kama) with no concentration — consistent with noise, not a
  specific mechanism.
- **Not instrument-robust.** Mechanical H1 appears on ES only and vanishes
  entirely on NQ — the opposite of a robust conditional edge.
- **Non-redundant but immaterial.** ARI vs `S_hmm` ≤ 0.081 and vs `S_vr` ≤ 0.005
  confirm `S_vt` is a genuinely distinct partition from the registered covariates —
  it is simply not a *predictively informative* one out-of-sample.

Top ES arm by OOS delta: `ema × atr`, n_t=2, n_v=3, h=12 — CMI 7.1e-4 nats, OOS
`delta_logloss` 2.0e-4, positive in 67% of windows. Even the best arm is
practically negligible.

## 4. Interpretation

The mechanical §10 rule is met by the letter on ES (283 arms clear CI>0 AND
delta>0), but this is (a) a **descriptive** result under a deferred screening level
(no certification), (b) driven by the **large-N** inflation of statistical
significance for a negligible effect, (c) contradicted by the design's own
**out-of-sample guard** (delta negative for 82% of arm-horizons and *all* of NQ),
and (d) **not instrument-robust** (0 H1 on NQ). The substantive, effect-size-aware,
instrument-robust reading is a **null**: the small-n vol×trend label carries a
tiny in-sample conditional association that does not generalize to out-of-sample
predictive value. The prototype's premise — that an SMA/StdDev vol×trend regime
adds edge-relevant information beyond the existing regime covariates — does not
survive rigorous out-of-sample, multi-instrument testing.

The LeBaron 1992 mechanism (volatility-state-dependent autocorrelation) is real in
the literature, but at this substrate/frequency the small-n label's incremental
contribution beyond the HMM regime and the variance-ratio state is not materially
predictive out-of-sample.

## 5. Disposition & consequences

- **`archive(null)`.** `S_vt` is **not** registered as an ADR-0002(b) candidate
  conditioning covariate (contrast the H900 GO consequence, which registered
  `regime_hmm_h900`). No arsenal admission scan proceeds from H001.
- The demoted directional prototype (`meta_shift_signal`/`policy`) is **not**
  revived — the covariate reframe that motivated its retention returns null.
- The frozen design, estimator library
  ([covariate_information.py](../../src/skie_universe2/inference/covariate_information.py),
  [variance_ratio_state.py](../../src/skie_universe2/features/variance_ratio_state.py)),
  and harness are retained as reusable infrastructure for future covariate-value
  studies.

## 6. Deviations (logged)

- (a) `S_vr` window/lag instantiated to repo scales (288 / 2) — the project-standard
  `variance_ratio_state` is not numerically pinned in the registry.
- (b) Train/eval purge = 288 bars (`MAX_FEATURE_LOOKBACK_BARS`), conservatively
  exceeding the design §6 nominal `max(max(n_v,n_t), h)`.
- (c) Bootstrap CI computed for candidate arms (binding MM-CMI > 0) only.
- (d) The CMI gate uses the Miller-Madow-corrected estimate; the plug-in estimate
  (positively biased at large N) is reported as `cmi_plugin` for transparency only.
- (e) The within-Z-cell permutation p-value is **illustrative only** (anti-conservative
  on the overlapping-window target; excluded from the H1 decision), computed for the
  top-6 arms by CMI as a diagnostic exhibit.
- (f) Inclusive exclusion variant not run (primary only); reported here as a
  registered follow-up if the disposition is ever revisited.

## 7. Reproducibility

Seed 20260716; design SHA-256 `6c875b789898…` (frozen pre-registration); ReproLog
`repro_log_e97678dfddf64306876ad5a34efb2956` (git HEAD, `uv pip freeze` SHA-256,
per-file dataset SHA-256 for the roll-adjusted substrate, `model_hash` over the
text scan artifacts). Scan tables:
[reports/H001/h001_scan_primary.csv](h001_scan_primary.csv) /
`.parquet`; verdict [reports/H001/h001_verdict_primary.json](h001_verdict_primary.json).
Code 2-round audit-remediate accept
([docs/audits/audit_trail_2026-07-16_h001-run-phase.md](../../docs/audits/audit_trail_2026-07-16_h001-run-phase.md)).

## 8. Residual risks / follow-ups

- **Deferred certification.** The binding screening/FWER level is the project-wide
  `screening_error_rate_target` (deferred to the shadow-ledger backfill). Even were
  it instantiated, the negligible effect sizes and OOS-guard failure make a
  material positive certification implausible.
- **`S_vr` parameterization sensitivity** (window/lag 288/2) is a registered
  follow-up; given the OOS-guard failure is uniform on NQ and dominant on ES, the
  null is unlikely to be sensitive to it.
- **Inclusive variant + additional instruments** (registered follow-ups) would
  strengthen the null but are not required to reach it.
- **Second-order CI width:** the MM-correction location shift does not propagate its
  own `O(K/2N)` sampling variability into the CI width — negligible at this N and
  immaterial to a null disposition.
