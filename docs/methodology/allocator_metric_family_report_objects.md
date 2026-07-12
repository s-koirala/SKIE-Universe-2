# Allocator metric-family report objects (standing ADR-0004 contract)

**Status:** standing (amendable) · **Mandated by:** ADR-0004 Decisions 4, 5, 6 ·
**Founded by:** H900 dwell-time feasibility gate — verdict GO (2026-07-11).

Every allocator evaluation under the rolling-origin regime (ADR-0004) MUST
report the primary metric family below as a **time series across evaluation
windows** (ADR-0004 Decision 5), with change-point dates as first-class
reported objects. This document is the standing report-object contract; it is
the concrete checklist a `deliver-results` allocator report satisfies. It does
not restate the ADR — ADR-0004 remains the normative source — it fixes the
reporting obligation and records which members are *standing* (permanent,
founded by a completed gate) versus *pending* (member defined, no producer yet).

## Primary metric family (ADR-0004 Decision 4)

| # | Report object | Definition (ADR-0004 D4) | Status |
|---|---|---|---|
| 1 | Regret vs switching oracle | Regret vs the best-in-hindsight *switching* oracle (fixed-share comparator, Herbster & Warmuth 1998). | pending (allocator not yet built) |
| 2 | Turnover-adjusted net edge | Net of the ADR-0008 cost model, with allocator switching costs charged. | pending |
| 3 | **Detection latency** | Bars from estimated change-point to **allocator weight response** (ADR-0004 D4 endpoint); at the pre-allocator gate the standing proxy is detector-alarm delay (no allocator exists yet). | **standing** (see below) |
| 4 | **Regime dwell vs cost break-even margin** | Pooled dwell distribution vs break-even dwell `D_be = L_detect + c_switch/mu` (Decision 6). | **standing** (see below) |
| 5 | Terminal-wealth lower-tail quantile | Registered level (ADR-0005 risk-tolerance declaration) under stationary-bootstrap resampling (Politis & Romano 1994; block length Politis & White 2004 as corrected by Patton, Politis & White 2009). | pending |

Change-point dates (ADR-0004 D5) are first-class reported objects for members 3–4.

## Standing members founded by H900 (ADR-0004 Decision 6, §10 GO consequence)

The H900 gate returned **GO** (`design SHA 548f009ae505…`;
[report](../../reports/H900/H900_dwell_feasibility_report_2026-07-11.md)), whose
§10 consequence is: *"the dwell-time metric family becomes a standing ADR-0004
report object."* Members 3 and 4 are therefore standing, with the following
registered reporting contract:

### Member 4 — regime dwell vs cost break-even margin

- **Estimand:** pooled Kaplan-Meier median sojourn `D_med` of the **causal
  filtered** state sequence of the registered regime family
  ([regime_hmm_h900](../../config/conditioning_covariates.yaml)), out-of-sample
  across evaluation windows; session-continuous spell rule primary,
  session-truncated as sensitivity.
- **Comparison:** `D_be(mu) = L_detect + c_switch/mu` over the registered mu grid
  (H900 §7); H1 = pooled `D_med` 95% CI lower bound `> D_be(mu_central)`.
- **Precision gate:** CI half-width `< 25%` of the point estimate, else the
  window is `indeterminate — insufficient spells` (H900 §8).
- **Producer:** `scripts/run_h900_dwell_study.py`; inference via
  `src/skie_universe2/inference/survival.py` (KM) + `bootstrap.py` (stationary
  bootstrap, B=2000 — H900 §8; 1.0 H052a replication convention).

### Member 3 — detection latency (CUSUM primary + BOCPD sensitivity)

- **Primary (supervised) estimator:** LLR-CUSUM alarm delay against the filtered
  change-points (Page 1954; `inference/cusum.py`). H900: ES 3 / NQ 2 bars.
- **Sensitivity (unsupervised) estimator:** BOCPD (Adams & MacKay 2007;
  `inference/bocpd.py`, `P1-2.0-H900-BOCPD-SENSITIVITY`). H900: KM L_detect
  ES 66 / NQ 52 bars — a **corroboration-rate** result: BOCPD alarms on
  ~46–48% of filtered transitions at dwell-comparable latency and does not
  corroborate the rest.
- **Reporting obligation (standing):** allocator evaluations MUST report the
  detection latency under **both** the supervised and unsupervised estimators,
  and MUST budget switching costs against a realistic (unsupervised) latency,
  not the CUSUM oracle. The true live-unsupervised latency is unquantified
  pending the registered `P1-2.0-H900-BOCPD-WHITENED` variant; until it lands,
  reports carry the corroboration-rate caveat explicitly.

## Amendment rule

New standing members are added only when a completed, audit-accepted gate makes
them standing (as H900 did for members 3–4). Pending members become standing
when their producer + the allocator they measure are built and audit-accepted
(ADR-0007 confirmation ladder). Amendments are logged here with the founding
gate's provenance.

## References

- Herbster, M. & Warmuth, M. K. 1998. *Mach. Learn.* 32:151-178. https://doi.org/10.1023/A:1007424614876
- Politis, D. N. & Romano, J. P. 1994. *JASA* 89:1303-1313. https://doi.org/10.1080/01621459.1994.10476870
- Politis, D. N. & White, H. 2004. *Econom. Rev.* 23:53-70. https://doi.org/10.1081/ETC-120028836
- Patton, A., Politis, D. N. & White, H. 2009. *Econom. Rev.* 28:372-375 (correction to Politis & White 2004). https://doi.org/10.1080/07474930802459016
- Page, E. S. 1954. *Biometrika* 41(1/2):100-115. https://doi.org/10.1093/biomet/41.1-2.100
- Adams, R. P. & MacKay, D. J. C. 2007. arXiv:0710.3742. https://arxiv.org/abs/0710.3742
