# AR-robust (prewhitened) BOCPD: does removing the by-construction rvol autocorrelation rescue the H900 detection NO-GO? — method freeze

**Status:** METHOD FROZEN this session (2026-07-13) · deliverable finalized from
PARKED · follow-up `P1-2.0-H900-BOCPD-WHITENED` · **primitive frozen; NO-GO
robustness rests on the prior on-ledger ROC probe (§4), reproducible on-ledger
re-run DEFERRED** (the H900 GO remains supervised-detection-dependent).
Addresses the autocorrelation-bias deviation left open by the step-2 BOCPD
sensitivity
([reports/H900/H900_bocpd_sensitivity_2026-07-11.md](../../reports/H900/H900_bocpd_sensitivity_2026-07-11.md)
§4, §6 deviation 1, §9).

This memo freezes the prewhitening primitive
([src/skie_universe2/inference/whitening.py](../../src/skie_universe2/inference/whitening.py))
and its unit tests
([tests/test_whitening.py](../../tests/test_whitening.py)), and records the
demonstration that settles the sign of the autocorrelation bias the step-2
sensitivity flagged as unverified. As with the two Kelly method-freezes
([kelly_growth_concavity_ruin_2026-07-12.md](kelly_growth_concavity_ruin_2026-07-12.md),
[discovery_alpha_cost_calibration_2026-07-12.md](discovery_alpha_cost_calibration_2026-07-12.md)),
the estimator's mathematical properties are demonstrated by the frozen unit
tests rather than by ad-hoc numbers embedded here. Each **synthetic** figure
below names the frozen test that reproduces it and is
illustrative-on-representative-substrate (deterministic step inputs and synthetic
near-unit-root AR(1) segments), never an on-ledger operating point. The one
exception is the **on-ledger** ROC in §4 (net ≈ 26 pp, `L_detect ≈ 45` vs ≈ 4
bars): it is cited from the prior investigation
([session_handoff_2026-07-12.md](../research_notes/session_handoff_2026-07-12.md) §2)
and is explicitly flagged as documented-but-not-reproducibly-preserved (§5),
pending the deferred re-run.

## 1. The question and why it was BLOCKING for the NO-GO reading

The step-2 unsupervised BOCPD sensitivity returned NO-GO — the Adams & MacKay
(2007) detector corroborates only ~half of the HMM-filtered regime changes at
dwell-comparable latency, so unsupervised change-point detection cannot stand
in for the supervised HMM the H900 dwell-feasibility GO relies on. The step-2
report (§6 deviation 1, §4) flagged one unquantified threat to that reading: the
detector's emission vector includes `log_rvol_5m_24h`, which is **autocorrelated
by construction** — it is the log of a 288-bar overlapping rolling sum of squared
returns, so consecutive 5-minute bars share ~287/288 of their terms and the
lag-1 autocorrelation is ρ ≈ 287/288 ≈ 0.997 (near unit root). The Adams-MacKay
NIG predictive assumes iid-within-run emissions; feeding it a near-unit-root
series **over-counts incumbent-run evidence** (the predictive keeps being
"surprised" in the same direction), which biases the detection latency `L_detect`
by a direction the step-2 report could not sign. If whitening the emission were
to collapse `L_detect` below the break-even dwell, the NO-GO would be an artifact
of misspecification rather than a real property of unsupervised detection. Per
§9 this was registered as `P1-2.0-H900-BOCPD-WHITENED` and the "upper bound"
reading of the NO-GO was held open pending it.

## 2. The primitive — AR(1) prewhitening on within-run innovations

The classical remedy for monitoring an autocorrelated process is to **prewhiten**:
fit the incumbent serial-dependence model, filter the series to its innovations,
and run the unchanged detector on the (approximately white) innovations, where
the iid predictive is correctly specified (Alwan & Roberts 1988; Runger &
Willemain 1995; the residual/prewhitened control-chart construction, itself the
Box & Jenkins 1976 prewhitening step).

`whiten_ar1` applies the per-dimension AR(1) innovation filter

```
w_t = (z_t − φ_d · z_{t−1}) / sqrt(1 − φ_d²),      w_0 = z_0.        (W1)
```

The `1/sqrt(1 − φ²)` factor renormalizes the innovation to the marginal variance
of a unit-variance AR(1), so the whitened series is ~unit-variance white and the
BOCPD unit-scale NIG prior stays appropriate.

`ar1_within_run` estimates φ by pooled least squares over consecutive-bar pairs
**that lie in the same filtered state**, after demeaning each contiguous run.
This is the load-bearing design choice: φ must capture the *incumbent-run* serial
dependence the detector's predictive must match, **not** the *between-run* level
shifts it must detect. Estimating φ off cross-boundary pairs would fold the
regime changes into the nuisance coefficient and blunt the detector — the exact
circularity the H900 estimand must avoid. For `log_rvol` the within-run estimate
reproduces the structural ρ ≈ 0.997; it is fixed by the feature definition, not
fit to the dwell outcome, so it introduces no circularity with the `L_detect` /
verdict estimand.

- **φ recovery / white-input null / within-run exclusion:** `test_ar1_recovers_known_phi`
  (known φ = 0.9 recovered to ±0.03), `test_white_input_phi_near_zero`
  (white input → |φ| < 0.05), `test_within_run_excludes_change_bars` (a Δ = 20
  cross-boundary join does not pull φ toward 1; recovered φ = 0.5 ± 0.05).
- **Whitening removes serial correlation:** `test_whitening_removes_autocorrelation`
  (φ = 0.95 input → residual lag-1 autocorrelation |r| < 0.05).

## 3. Whitening keeps real regime changes detectable (the "timely" axis)

A level shift of magnitude δ at the run boundary maps, under (W1), to an
innovation

```
w_shift = δ / sqrt(1 − φ²),                                          (W2)
```

i.e. it is **amplified** by `1/sqrt(1 − φ²)` relative to the raw shift magnitude
— for φ = 0.99 a factor of ≈ 7.1×. Three distinct quantities follow, and the
frozen test asserts each so the memo does not conflate them:

- the **spike** at the shift bar, `δ/sqrt(1−φ²)`, which for δ = 3 is ≈ **21.3**
  in stable-innovation-sd units (the whitened stable innovations are ~unit
  variance);
- the **steady** post-shift innovation `δ·sqrt((1−φ)/(1+φ))`, ≈ **0.21** for
  δ = 3;
- their ratio, **exactly `1/(1−φ) = 100`** (W3) — independent of δ.

So whitening does **not** hide genuine regime changes — it makes them larger. A
real shift stays detectable; only the nuisance serial correlation is removed.
The amplification is tested **deterministically** on a unit step input (no RNG),
avoiding any single-seed fragility:

```
spike / steady_innovation = 1 / (1 − φ).                            (W3)
```

- **Amplification (deterministic):** `test_level_shift_amplification_exact`
  asserts (W2) and (W3) to numerical tolerance on a step input — the load-bearing,
  seed-free statement of "real shifts survive whitening." (`1/sqrt(1−φ²) = 7.089`;
  `δ/sqrt(1−φ²) = 21.27`; `1/(1−φ) = 100` for φ = 0.99, δ = 3.)
- **Amplification (distributional):** `test_level_shift_amplified_in_expectation`
  asserts the median over 400 seeds of `w_shift / stable_sd` matches δ/sqrt(1−φ²)
  (theory 21.27; **reproduced median ≈ 20.15**, 5.3% off, inside rtol 0.10). It
  also documents the caveat that a **single** near-unit-root realization can mask
  the shift: with φ = 0.99 the pre-shift series is near-random-walk (σ = 1, max
  wander ≈ 2.9 over 300 bars ≈ the δ = 3 shift), so ~1% of seeds put the
  innovation below the stable band by chance. Detectability is a property of the
  sampling distribution, not of any one segment — which is precisely why the
  previous single-seed assertion (seed 4, ratio 0.40) was a mis-specified test,
  not a primitive defect.

**On φ.** All frozen tests use φ = 0.99 as a conservative near-unit-root proxy
for the structural `log_rvol` autocorrelation ρ ≈ 0.997. Both the amplification
`1/sqrt(1−φ²)` (7.1× at 0.99 vs 12.9× at 0.997) and the alarm rate are monotone
increasing in φ, so 0.99 **lower-bounds** the effect; a test at 0.997 would only
sharpen §3 and §4, never soften them.

## 4. What the frozen tests show, and where the NO-GO robustness actually rests

**One reproducible ROC point (frozen, synthetic).** At the Bayes operating point
(`alarm_prob = 0.5`) the two rate tests fix a single (false-positive,
true-positive) point on near-unit-root synthetic substrate:

- **False alarms not controlled** — `test_whitened_false_alarm_not_controlled`:
  on stable segments with a label flip but no distributional change, whitened
  BOCPD alarms at **≈ 0.43** (Wilson 95% lower bound ≈ 0.36). The conventional
  significance reference is 0.05 (the Shewhart 3-σ control-chart false-alarm rate
  is stricter still, ≈ 0.0027); the whitened rate exceeds **both**. The earlier
  `< 0.30` expectation was a made-up threshold on a noisy n = 40 estimate
  (±0.15 Wald half-width) and is removed.
- **Real shifts detected** — `test_whitened_true_change_detection_rate`: on a
  clean δ = 3 shift the detection rate is **≈ 0.95** (Wilson lower bound ≈ 0.90).
  `test_whitened_detection_rate_across_shift_sizes` freezes the detection rate at
  δ ∈ {0.5, 1.0, 3.0} (realized ≈ 0.82 / 0.86 / 0.95, each with Wilson lower
  bound > 0.5), so the detector stays non-degenerate down to δ = 0.5;
  `test_true_change_still_detected_after_whitening` adds a ≤ 10-bar latency
  spot-check.

So on **clean, large synthetic shifts** the whitened detector is not degenerate —
TP (~0.95) sits well above FP (~0.43). Whitening removes the by-construction
serial correlation (§2) and keeps real shifts detectable (§3); it does **not**,
at this operating point, buy a low false-alarm rate. This is one ROC *point*, not
a ROC *curve*: the frozen tests do not sweep `alarm_prob`, so they cannot on their
own establish "no operating point is accurate **and** timely."

**Where the NO-GO robustness rests (prior on-ledger probe, not reproduced here).**
The decision-relevant question is not clean synthetic shifts but the **subtle
on-ledger regime changes** at usable latency. The prior investigation swept the
full net-detection-vs-hazard ROC on the archived filtered sequences and found
**no operating point simultaneously accurate and timely**: best discrimination
(net ≈ 26 pp) needs `L_detect ≈ 45` bars; forcing latency down to ≈ 4 bars
collapses the detector to noise — there is no elbow
([session_handoff_2026-07-12.md](../research_notes/session_handoff_2026-07-12.md) §2).
That on-ledger ROC — over real, subtle changes — is what supports the NO-GO
robustness; the synthetic tests here are consistent with it (high false alarms at
the one point they measure) but do not reproduce it. It reconciles with step-2,
where unsupervised BOCPD corroborates only ~0.47 (46–48%) of regime changes at
dwell-comparable latency
([H900_bocpd_sensitivity_2026-07-11.md](../../reports/H900/H900_bocpd_sensitivity_2026-07-11.md) §4);
removing the autocorrelation specification threat did not lift that into an
accurate-and-timely regime. (The earlier draft cited a "~0.76–0.81 corroboration
rate" here; that figure is **withdrawn** — it is not reproduced by any frozen
test and its provenance is undetermined. It is *not* the step-2 corroboration /
alarm figure, which is ~0.47 as cited above, so no reattribution is asserted.)

**Net.** Prewhitening the near-unit-root `log_rvol` is available and correctly
specified, and at the Bayes operating point it does not control false alarms.
The step-2 "upper bound" caveat is addressed in the direction that supports the
NO-GO — the prior on-ledger ROC probe found the autocorrelation bias was not what
produced it — but that probe's artifact is not preserved reproducibly (§5), so a
reproducible on-ledger prewhitened ROC/latency re-run is the **deferred**
confirmation, not a claim these synthetic tests settle on their own.

## 5. Consequence for H900 and scope of this freeze

The H900 dwell-feasibility GO
([reports/H900/H900_dwell_feasibility_report_2026-07-11.md](../../reports/H900/H900_dwell_feasibility_report_2026-07-11.md))
is **supervised-detection-dependent**. On the evidence assembled here — the
frozen primitive + synthetic operating-point tests (§3–§4) and the prior
on-ledger ROC probe (§4) — that dependence is robust to the one specification
threat that could have overturned it: an AR-robust (prewhitened) unsupervised
detector still shows no accurate-and-timely operating point over real regime
changes and cannot substitute for the supervised HMM. The allocator program
proceeds on the supervised regime family already registered as the ADR-0002
conditioning covariate
([config/conditioning_covariates.yaml](../../config/conditioning_covariates.yaml)),
carrying the standing, quantified detection-latency charge against the ~half of
regime changes a live unsupervised detector would corroborate.

**Scope and the deferred confirmation.** This freeze is method-level: the
primitive and its properties are frozen and demonstrated on representative
substrate. The `reports/H900_bocpd_run/` outputs are **content-identical after
newline normalization** (CRLF vs LF only) to the tracked step-2 non-whitened
outputs — i.e. a reproduction of the step-2 run, **not** a distinct whitened
on-ledger artifact — so the prior on-ledger whitened ROC (§4: net ≈ 26 pp,
`L_detect ≈ 45` vs ≈ 4 bars) is **documented but not reproducibly preserved**
here. A reproducible on-ledger prewhitened ROC/latency re-run is therefore the
**deferred** confirmation, downstream of the shadow-ledger backfill; until it is
run and logged, NO-GO robustness rests jointly on the frozen synthetic
operating-point evidence and the documented prior probe, not on a reproducible
on-ledger number.

## References

- Adams, R. P. & MacKay, D. J. C. 2007. *Bayesian Online Changepoint Detection.*
  arXiv:0710.3742. https://arxiv.org/abs/0710.3742
- Box, G. E. P. & Jenkins, G. M. 1976. *Time Series Analysis: Forecasting and
  Control.* Holden-Day. (Prewhitening.)
- Alwan, L. C. & Roberts, H. V. 1988. "Time-Series Modeling for Statistical
  Process Control." *J. Bus. Econ. Stat.* 6(1):87–95.
  https://doi.org/10.1080/07350015.1988.10509640
- Runger, G. C. & Willemain, T. R. 1995. "Model-based and Model-free Control of
  Autocorrelated Processes." *J. Qual. Technol.* 27(4):283–292.
  https://doi.org/10.1080/00224065.1995.11979608
- Wilson, E. B. 1927. "Probable Inference, the Law of Succession, and Statistical
  Inference." *J. Am. Stat. Assoc.* 22(158):209–212.
  https://doi.org/10.1080/01621459.1927.10502953 (score-interval for the
  false-alarm rate.)
