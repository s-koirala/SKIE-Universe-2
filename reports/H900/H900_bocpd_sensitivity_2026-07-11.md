# H900 BOCPD Detection-Latency Sensitivity

**Closes** [H900_dwell_feasibility_report_2026-07-11.md](H900_dwell_feasibility_report_2026-07-11.md)
§6 deviation 1 and the §9 follow-up `P1-2.0-H900-BOCPD-SENSITIVITY`.
**Date:** 2026-07-11 · **HID:** H900 · **Governance:** ADR-0004 D6, ADR-0008.
**Provenance:** ReproLog `repro_log_c5ffb83db9f8…`; design SHA
`548f009ae505…` (unchanged; this is a registered post-hoc sensitivity, not a
design change). **Audit:** [audit_trail_2026-07-11_h900-bocpd-sensitivity.md](../../docs/audits/audit_trail_2026-07-11_h900-bocpd-sensitivity.md)
(3-round audit-remediate). **Reproduction:**
[check_h900_bocpd_reproduction.py](../../scripts/audits/check_h900_bocpd_reproduction.py) — PASS.

## 1. Question

The frozen design §7 registers CUSUM (Page 1954) as the primary detection-latency
estimator and BOCPD (Adams & MacKay 2007) as its sensitivity detector, both
measuring "alarm delay against the filtered change-points." Deviation 1 deferred
BOCPD. This report computes it and asks: **does the H900 GO survive when detection
latency is measured by an unsupervised detector instead of the supervised CUSUM?**

CUSUM is supervised — it resets at each known change-point τ and tests the *known*
successor density against the incumbent, alarming in 1–3 bars. A live regime rotor
has neither the change time nor the successor identity. BOCPD is the unsupervised
counterpart: it infers a change from the emission stream alone.

## 2. Method (as run)

- **Estimand:** per-transition-anchored. For each filtered transition `i→j` at τ,
  BOCPD runs over the local window `[τ_prev, τ_next)` — it enters τ with the
  incumbent sojourn established (the "when" a live rotor's clock would have), but
  is *not* told the successor `j` (the "what"). Delay = bars from τ to the alarm,
  right-censored at the successor sojourn end (same convention as CUSUM).
- **Detector:** faithful port of SKIE-Universe 1.0 `bocd.py` (Adams & MacKay 2007
  Algorithm 1: NIG conjugate, Student-t predictive, log-space run-length
  recursion), generalized to the 2-D diagonal emission by summing per-dimension
  log-predictives. Model-light: consumes the standardized emissions `z`, not the
  HMM densities.
- **Hazard:** `H = 1/median(eval-window filtered dwell)` — the observed
  regime-switching cadence. This is the **optimistic, liberal** calibration chosen
  for 2.0. It is eval-fold, hence biases the break-even comparison *conservatively*
  (longer dwell → smaller hazard → larger L_detect → larger D_be), so it **cannot
  manufacture a GO** (unit-tested: `test_smaller_hazard_never_detects_sooner`).
- **Alarm:** posterior mass ≥ 0.5 that the current run began at or after τ (the
  Bayes-optimal 0-1-loss boundary — a decision rule, not a tuned parameter). The
  run-length MAP reports BOCPD's own change-*location* estimate.

## 3. Result

**CUSUM verdict GO (reproduced bit-identically); BOCPD sensitivity verdict NO-GO,
both variants.**

| Variant · Inst | dwell median [CI] | CUSUM L_detect · D_be · H1 | BOCPD KM L_detect · D_be · H1 | BOCPD alarm rate | BOCPD **uncensored** median delay |
|---|---|---|---|---|---|
| primary · ES | 12 [10,14] | 3 · 4.45 · **✓** | 66 · 67.5 · ✗ | 1701/3720 = 46% | **10** |
| primary · NQ | 9 [8,10] | 2 · 2.54 · **✓** | 52 · 52.5 · ✗ | 2157/4489 = 48% | **5** |
| inclusive · ES | 12 [9,14] | 2 · 3.45 · **✓** | 66 · 67.4 · ✗ | 1987/4162 = 48% | 9 |
| inclusive · NQ | 8 [7,9] | 2 · 2.54 · **✓** | 47 · 47.5 · ✗ | 2570/5303 = 48% | 5 |

D_be at central μ = 1.2e-4; H1 = (pooled dwell CI-low > D_be). Change-location
reporting: per-alarm `true_cp_ts`/`detected_cp_ts` are archived in
`h900_bocpd_latency_*.parquet`; the median localization error on this run is
0 min (the MAP change-time typically coincides with the true transition bar) —
a diagnostic, not gated by the verdict (QUANT-2-3).

## 4. Interpretation — the NO-GO is a *corroboration-rate* result, not a *speed* result

The KM L_detect (47–66) sits far above the dwell (8–12), which reads as "the rotor
is too slow." The **uncensored** median delay refines this decisively: among the
~46–48% of filtered transitions BOCPD *does* alarm on, the median delay is **5–10
bars — comparable to the regime dwell itself.** BOCPD detects fast when it detects.

The gap is the **detection rate.** ~52–54% of the HMM's filtered-MAP transitions
never trigger a BOCPD alarm within their sojourn; Kaplan-Meier treats those as
censored, inflating the median to 47–66. **This run cannot attribute the missed
fraction** (QUANT-2-4): a non-alarming transition is either (a) a "soft"
filtered-MAP flip with no genuine emission-distribution change, or (b) a genuine
change the model-light detector is underpowered to see — confounded by the
detector's own registered iid misspecification (§5.2). The two readings are not
separated here; the whitened variant (`P1-2.0-H900-BOCPD-WHITENED`) is needed to
distinguish HMM over-segmentation from detector underpowering.

So the honest reading of the founding gate:
- **On the supervised CUSUM latency (the registered primary), H900 is GO** — the
  frozen decision object reproduces exactly (L_detect 2–3, D_be 2.5–4.5, dwell
  CI-low 8–10; GO with a ~5.5-bar margin robust to L_detect CI, per refuted
  finding QUANT-1-4).
- **A live unsupervised rotor alarms on only ~half of the filtered transitions**
  (at dwell-comparable latency when it does), and does not corroborate the other
  half from the emission stream alone. **The GO is supervised-detection-dependent;**
  its live realizability rests on how the allocator treats — and how much the
  detector's underpowering explains — the ~half of filtered transitions BOCPD
  does not confirm.

## 5. Caveats (registered)

1. **Informative censoring (QUANT-1-3 / QUANT-2-1 / QUANT-3-1):** the censoring
   time is the successor sojourn length, not independent of detection difficulty
   across pooled transition types; the pooled KM median is **not**
   distribution-free. The uncensored median (§3) does **not** mitigate this — it
   is the alarm-selected fast-detection subsample (biased **low**), the
   complement of the censored non-alarming transitions. The KM median's bias
   direction is *conditional on §4's unresolved attribution*: **if** the censored
   fraction is dominated by signal-free soft flips (reading (a)), KM is biased
   **high** and the two medians bracket the estimand; **under reading (b)** the
   missed transitions' realized latency is effectively non-detection, so KM —
   right-censored as if detection eventually occurs — does **not** upper-bound
   the truth and the two do not bracket it. This run does not separate (a) from
   (b); either way the NO-GO magnitude depends on how non-detection is scored.
2. **iid-within-run misspecification (QUANT-1-5 / QUANT-2-2):** the NIG
   predictive assumes iid observations within a run, but the `log_rvol_5m_24h`
   emission is autocorrelated *by construction* (288-bar overlapping rolling
   window). The net direction on L_detect is **expected-but-unverified**:
   positive autocorrelation over-counts incumbent-run evidence (slower alarm →
   upward bias), but an iid predictive also under-estimates variance
   (post-change looks more surprising → faster alarm) — the effects oppose. The
   sign is settled only by the registered whitened/AR-robust variant
   (`P1-2.0-H900-BOCPD-WHITENED`); until then the "upper bound" reading of KM
   L_detect is a hypothesis, not a proven bound.
3. **Hazard is optimistic-liberal but robust in direction:** the NO-GO also holds
   under the parameter-free `anchored_hazard` (the stationary mean pooled
   inter-switch interval `1 / sum_i pi_i (1 - a_ii)`, i.e. the reciprocal of the
   occupancy-weighted switch rate; archived-data cross-check L_detect ES 94 /
   NQ 76), so it is not a
   hazard-circularity artifact.

## 6. Consequence for the program

H900 remains **archive(positive) / GO** on the registered CUSUM object — the
allocator program proceeds. This sensitivity attaches a standing, quantified
caveat that the **first ADR-0002 admission scans and any allocator regret
evaluation must budget realistic (unsupervised) detection**: switch costs should
be charged against the ~half of regime changes a live detector corroborates, at
dwell-comparable latency, not against the CUSUM oracle's 1–3 bars. Carried to the
allocator confirmation tier via `P1-2.0-H900-BOCPD-WHITENED` and the
switch-cost-realism note in the arsenal-admission lineage. Under the proposed
aggressive-geometric-growth mandate ([ADR-0013](../../docs/decisions/ADR-0013-aggressive-geometric-growth-mandate.md),
status: proposed) this switch-cost-budgeting obligation is not a risk-aversion
residual but a geometric-growth protection: assuming the CUSUM-oracle 1–3-bar
latency inflates the apparent compounded (log-wealth) edge, and an overstated
edge over-bets and drives negative geometric growth (ruin) at the swept
Kelly fractions ≥ 1×, so the obligation to charge switch costs against the
realistically corroborated ~half of regime changes STRENGTHENS — not weakens —
under the mandate.
