---
name: H103 — Stress-state-only (anti-gate) first-hour opening-range breakout (ES+NQ), shadow-ledger admission
description: Pre-registration design doc for hypothesis H103 (2.0 re-specification of 1.0 H054); FROZEN 2026-07-16 (ES+NQ; 3-round audit-remediate accept)
type: project
hypothesis_id: H103
tier: 5
status: designed  # designed | running | evaluated | archived(positive|null|negative)
owner: SKIE
created: 2026-07-16
citations: 10.1093/rfs/hhp008, 10.1111/j.1540-6261.2011.01671.x, 10.2307/1912559, 10.1016/j.frl.2012.09.001, 10.1109/ACCESS.2019.2899177, 10.1093/rfs/1.1.41, 10.1111/j.1468-0262.2005.00615.x, 10.1016/j.spl.2016.02.012, 10.1080/01621459.1994.10476870, 10.1016/j.jempfin.2008.03.002, 10.2469/faj.v58.n4.2453, 10.1016/0304-4076(92)90104-Y, 10.1198/000313001300339897, 10.3905/jpm.1989.409211, 10.21314/JCF.2016.322
external_doi: null
---

> **FROZEN 2026-07-16 (`designed`).** This design is pre-registered and immutable:
> instrument scope ES+NQ (operator decision 2026-07-16), 3-round audit-remediate
> accept. Any change after this freeze requires a new hypothesis ID. The frozen
> SHA-256 is recorded in `hypothesis_backlog.md` and the pre-registration ReproLog.

# H103 — Stress-state-only (anti-gate) first-hour opening-range breakout (ES+NQ), shadow-ledger admission

This document is the FROZEN pre-registration record for hypothesis H103 (the 2.0
re-specification of 1.0 H054), held at `designed` status; any change after this
freeze requires a new hypothesis ID.

H103 is a forward **arsenal-admission candidate** (ADR-0002) on the 2.0 shadow
ledger, promoted from the retro Expert Card
([docs/reports/expert_card_H054_retro_2026-07-10.md](../../../docs/reports/expert_card_H054_retro_2026-07-10.md),
disposition `arsenal-admit-conditional`). Per that card, H103 is the **anti-gate**
(stress-state-only) form of the first-hour opening-range breakout: the SAME
first-hour ORB signal as H101, but taken **only** on high-realized-volatility
(stress) sessions. In 1.0 vocabulary H054 traded the ORB solely on sessions the
HMM classified into its highest realized-vol emission state; in 2.0 vocabulary
this is a direct probe of conditional gross edge inside a realized-vol-regime
cell — the Lundström-predicted edge direction (edge concentrated in high-vol
sessions; retro card §8 priors #1), i.e. the direction opposite the non-stress
HMM gate that H052a's evidence rejected.

**Algebraic dependence on H101 (binding).** H103 is NOT an independent expert.
It applies the identical ORB rule to a **subset** of the same sessions H101
trades unconditionally, so its per-session return series is algebraically
dependent on H101's (retro card §4: H054's differential statistic is
algebraically dependent on the unconditional H052a arm; the stress cell is a
sub-selection of the shared session set). Therefore the ADR-0002(d)
non-redundancy requirement and the **RC-XCORR-1 cross-correlation check against
H101 are MANDATORY before the H101+H103 pair is admitted** — pre-registered
explicitly in §5, §8, and §10. This is the single most important governance
constraint distinguishing H103 from H101.

Two objects are pre-registered: (A) the **stress-cell conditioning** of the
H101 ORB expert's shadow ledger — H103 shares H101's single backfilled ORB
ledger (ADR-0003), it is NOT a second expert with a duplicate backfill (§4); and
(B) the **RC-H103-1 admission scan** — the ADR-0002(c) conditional-gross-edge
test restricted to the stress cell, with the primary cell defined by a
data-driven realized-vol threshold (§3).

**Governance blocks respected by construction.** Growth-based ranking and
Kelly-fraction selection are BLOCKED until the two Decision-9 Kelly memos are
numerically instantiated; the discovery/FWER screening level is the DEFERRED
project-wide `screening_error_rate_target`. So the ledger materializes all four
Kelly fractions and the admission scan runs and is reported **descriptively** —
no arm is certified and no fraction is selected until those unblock.

## 1. Hypothesis

- **H0:** the first-hour ORB has no positive pre-cost (gross) per-session edge in
  the pre-declared stress-state cell (§3) on either instrument (ES, NQ), at the
  ADR-0002(c) multiplicity-corrected level (joint ES+NQ cell family) once the
  deferred screening level is set.
  Operationally, the Romano-Wolf-corrected lower bound on the mean gross
  per-session ORB return **inside the stress cell** is ≤ 0.
- **H1:** the stress-state cell carries a Romano-Wolf-corrected positive gross
  per-session ORB edge — the breakout's conditional gross edge is concentrated in
  high-realized-volatility sessions (the Lundström prior; retro card §8 priors
  #1), admissible under ADR-0002(c). The **primary pre-registered cell** is the
  top realized-vol band (§3); the complement (non-stress) cell is reported as the
  contrast, mirroring the H054 anti-gate-vs-unconditional decomposition.
- **Mechanism:** opening-range breakouts capture intraday momentum/continuation
  following first-hour price discovery — documented on S&P 500 (and crude oil)
  futures by
  [Holmberg, Lönnbark & Lundström 2013, Finance Research Letters 10(1):27-33](https://doi.org/10.1016/j.frl.2012.09.001)
  (ORB gross profitability; S&P 500 futures is the index-futures leg directly
  relevant here) and [Tsai et al. 2019, IEEE Access 7:32061-32071](https://doi.org/10.1109/ACCESS.2019.2899177)
  (open-access; specific magnitudes not reproduced here — only Crossref-verified
  title/venue/year/pages asserted). The **conditioning direction** (edge concentrated
  in high-vol sessions specifically) is carried from the companion same-author work
  Lundström, "Day trading returns across volatility states" (Umeå Economic Studies /
  DiVA diva2:732318), which reports the high-minus-low volatility-state ORB return
  decomposition; and is motivated by the variance-risk-premium / stress-state return
  structure of [Bollerslev, Tauchen & Zhou 2009, RFS 22(11):4463–4492](https://doi.org/10.1093/rfs/hhp008)
  and [Cochrane 2011, J. Finance 66(4):1047–1108](https://doi.org/10.1111/j.1540-6261.2011.01671.x):
  risk compensation (and thus the return available to a directional continuation
  rule) is elevated in high variance-risk-premium / stress states — NOT the narrower
  claim that realized returns track realized volatility (BTZ's predictor is the
  variance risk premium, implied minus expected realized variance, not realized vol
  itself).
  BTZ 2009 is Phase-0-flagged in the 1.0 source as intraday-silent (it concerns
  the equity variance risk premium at monthly horizon, not the intraday ORB) —
  it motivates the *conditioning direction*, not the *intraday signal*; that
  scope caveat is carried verbatim and must not be overstated at freeze. The
  regime-switching apparatus H054 used to define "stress" derives from
  [Hamilton 1989](https://doi.org/10.2307/1912559); in 2.0 the learned HMM state
  is REPLACED by a rule-based realized-vol cell per ADR-0001 Decision 5 (§3).
- **Primary citations:** Bollerslev, Tauchen & Zhou 2009 (10.1093/rfs/hhp008,
  conditioning-direction mechanism); Holmberg, Lönnbark & Lundström 2013
  (10.1016/j.frl.2012.09.001) and Tsai et al. 2019 (10.1109/ACCESS.2019.2899177,
  the ORB signal class); Lo & MacKinlay 1988 (10.1093/rfs/1.1.41, the
  variance-ratio conditioning state); Romano & Wolf 2005
  (10.1111/j.1468-0262.2005.00615.x, the admission-scan FWER).

## 2. Universe and sample period

- **Instruments:** **ES and NQ** (operator decision 2026-07-16). The 1.0 H054 retro
  evidence is ES-only (retro card frontmatter `instruments: [ES]`, §1), and ES is
  therefore the **retro-comparability anchor**; NQ is added as the pre-registered
  cross-instrument robustness leg, matching the RC-H101-1 admission scan (ES+NQ) that
  H103 is structurally paired with (same ORB rule, complementary session subset) and
  the H001 covariate study (ES+NQ). Adding NQ doubles the RC-H103-1 cell family (both
  instruments × the §3 cells); this is registered **before** the scan runs. The
  multiplicity accounting (§5(B)) runs Romano-Wolf per-instrument (within-instrument
  FWER over the §3 cells) and controls the cross-instrument (2-family) multiplicity by
  a conservative Šidák union bound at the deferred screening level — jointly covering
  the whole ES+NQ family, not a single per-instrument look.
  The stress-cell cutoff (§3, the H900 HMM stress-occupancy anchor) is calibrated
  **per instrument** on each instrument's own training-window HMM occupancy — NQ's
  cutoff is NOT borrowed from ES. The micro contracts (MES/MNQ, retro card §3) remain
  candidate additions deferred to a later operator decision. Substrate: 2.0
  roll-adjusted continuous-contract evidence bars,
  `data/processed/vendor_legacy_1min_roll_adjusted/` (ADR-0011), identical to
  H101/H900 to keep the ledger on one substrate.
- **Frequency:** 5-minute bars aggregated from the 1-minute substrate (H900 §3
  aggregation rule by reference).
- **Session:** **RTH only** for the ORB. RTH = the local-time window
  `[09:30, 16:00)` in `America/New_York` (DST-aware via the tz conversion of
  `ts_event`; the CME equity-index regular session, an exchange constant, not a
  tunable) — identical to H101 §2. Bars outside RTH are flat (position 0), but the
  ledger's per-bar counterfactual is written for every valid bar
  (counterfactual completeness, ADR-0003 D1). H103 additionally holds position 0
  on every **non-stress session** by construction (§4).
- **Sample period:** 2015-01-02 → 2025-12-31 (full materialized span). Note: the
  1.0 H054 OOS was ES 2025-01-01 → 2025-12-03, 237 sessions, with only
  **n_anti = 7 active (stress) trades** (2.95% fire rate); the full-span 2.0
  backfill is the accumulation path the retro card §8 priors #4 identifies as the
  only affordable way to reach adequate power (§8 power floor).
- **Exclusions (registered a priori):** identical to H900/H101 §2 —
  (a) `pit_provisional` bars; (b) `substrate_defects[DEC_ROLL_LATE_COMMIT]`
  windows excluded in primary, included in the inclusive-variant sensitivity.
  December-roll windows remain *excluded*, not *corrected* (no Databento repull —
  operator decision 2026-07-16).
- **Roll-handling:** roll-adjusted continuous contract; close-to-close adjusted
  log returns (H900 §2 by reference).

## 3. Features and conditioning set — the STRESS-STATE definition (key design decision)

The **stress-state cell definition is the central design decision of H103** and
is fixed here before any scan. Two candidate operationalizations exist; the
choice, the primary, and the threshold are pre-registered data-drivenly (no
arbitrary cutoff).

- **Session structure (per RTH session, causal):** the opening-range window is
  the first `n_or` RTH bars; `OR_high`/`OR_low` are the running high/low over that
  window. # justify: `n_or = 12` five-minute bars = the first 60 minutes — the
  "first-hour" opening range registered VERBATIM in the 1.0 H054/H052a design and
  carried unchanged for comparability with the retro evidence; a session-structure
  constant from the source signal definition, not tuned against the H103 outcome.
  Identical to H101 §3/§4 (shared expert).

- **Primary stress-cell definition (rule-based realized-vol percentile — ADR-0001
  D5 compliant).** The stress cell is the set of RTH sessions whose
  **pre-session trailing realized-volatility percentile** lies in the top band.
  Per retro card §8 priors #3, the 2.0 scan MUST replace the learned HMM state
  with a rule-based covariate cell (ADR-0001 Decision 5: a latent-state model may
  tilt priors / define scan cells but never gate; H050 precedent). The covariate
  is the project-standard `realized_vol_percentile`
  ([config/conditioning_covariates.yaml](../../../config/conditioning_covariates.yaml)),
  computed causally (trailing window ending at/before session start, PIT-clean).

  **Reference-window registration (PIT / purge, binding).** The
  `realized_vol_percentile` covariate is defined by two windows, both registered
  here so the §6 purge covers them: (i) the per-session realized-vol INPUT is the
  registered `rvol_5m_24h` (a trailing 24-hour = 288-bar causal window ending at/
  before session start — the H900 emission feature, ≤ `MAX_FEATURE_LOOKBACK_BARS`=288,
  so the 288-bar purge covers it exactly); (ii) the percentile REFERENCE distribution
  is the **training-window empirical CDF** of that input (recomputed per rolling
  origin, §6), NOT a trailing cross-boundary window — so the eval-session percentile
  is scored against a frozen train-window CDF and is PIT-clean by construction, with
  no train/eval strength-borrowing. The registry entry
  [config/conditioning_covariates.yaml](../../../config/conditioning_covariates.yaml)
  `realized_vol_percentile` is updated at freeze to record this
  input-window/reference-CDF specification.

  **ADR-0001 D5 compliance (the anti-gate is a RULE-BASED conditional expert).**
  D5 prohibits only a LATENT-generative regime model acting as a binary position
  gate. H103's per-session stress membership (§4) is set by the **rule-based**
  realized-vol percentile cell, not by any latent state; the H900 HMM enters ONLY
  to set the scalar train-window occupancy CUTOFF (an ADR-0002/registry-authorized
  scan-cell definition), never the per-session membership. So the §4 position
  restriction is an ADR-0002 conditional-only expert (admissible), not a D5-barred
  latent gate. This distinction is what keeps the HMM from being smuggled back in
  as a gate via its occupancy cutoff.

  **Threshold — data-driven, not arbitrary.** Let p̂ be the **stationary
  (unconditional) occupancy probability of the H900 HMM's stress state** — the
  fraction of sessions the registered `regime_hmm_h900` 4-state Gaussian HMM
  (highest log-`rvol_5m_24h` emission mean state) spends in its stress regime,
  estimated on the training window only. **The stress cell is the set of sessions
  whose train-window realized-vol percentile is ≥ (1 − p̂)** — i.e. the top-p̂
  fraction of sessions by realized-vol percentile (equivalently, rank ≥ the
  (1−p̂)-quantile of the train-window rvol distribution). This reproduces the HMM
  stress state's own mass p̂ as a rule-based top-band cell. # justify: this ties
  the percentile cutoff to the regime model that *defined* "stress" in 1.0
  H054 — the vol-percentile cell is calibrated to reproduce the HMM stress state's
  own mass, so it is a rule-based re-expression of the same event rather than a
  hand-picked quantile. The estimate is a training-window output (recomputed per
  rolling origin, §6), never an eval-window quantity, so it carries no
  look-ahead. If the HMM stress occupancy is unstable across training windows,
  the cutoff is reported per-window (not pooled) and the instability is flagged
  (§8 stationarity diagnostic). This anchoring also directly measures the retro
  card §3 concern that the 2.95% realized fire rate came in far below the 1.0
  design's 10% estimate: the delta between the HMM-implied occupancy and the
  realized stress-cell fire rate is a pre-registered RC-H103-1 exhibit.

- **Registered secondary / delta covariate (the learned HMM state).** The
  registered `regime_hmm_h900` covariate (the 4 filtered MAP states, causal
  forward filter) is scanned as a **secondary** conditioning covariate so the
  scan measures the HMM-vs-rule delta the retro card §8 priors #3 requires
  ("H054's evidence is agnostic between the two — the scan should measure the
  delta"). Per ADR-0001 D5 and the covariate registry's `adr_0001_d5_compliance`
  clause, the HMM state enters ONLY as a scan-cell covariate, NEVER as a position
  gate; its `detection_cost_caveat` (unsupervised detection latency, not the
  supervised CUSUM oracle) is carried into any switch-cost accounting.

- **ADR-0002(b) conditioning set (frozen before the scan).** The RC-H103-1 scan
  conditions on the project-standard set (realized-vol percentile [primary],
  time-of-day bucket, variance-ratio trend/range state [Lo & MacKinlay 1988],
  macro-calendar proximity, spread/liquidity regime) plus the two pre-registered
  extensions used in H101: the registered `regime_hmm_h900` covariate and
  **first-hour sign** (the sign of the RTH first-hour return). All covariates are
  causal (≤ session start / ≤ bar t), PIT-clean. The **primary cell is the top
  realized-vol band** (the stress cell); all cells are reported.

## 4. Signal construction — H103 is a CONDITIONING of H101's shared ledger, not a new expert

**Pre-registered decision: H103 does NOT introduce a second expert.** It reuses
H101's `OrbFirstHourExpert` (the single Layer-1 ORB signal producer) and its
single shadow-ledger backfill. H103 is **defined by the stress-cell restriction
applied at scan time** (RC-H103-1, §5) to the same ledger rows, plus the flat-on-
non-stress-session position semantics below. Rationale: the H103 ORB rule is
bit-identical to H101's; materializing a second expert would duplicate the ledger
and manufacture a spurious second trial-register entry for the same signal. This
choice is precisely *why* the algebraic dependence with H101 is unavoidable and
the RC-XCORR-1 non-redundancy gate (§10) is mandatory: H103's traded sessions are
a strict subset of H101's.

The shared expert emits a per-bar Layer-1 signal (direction ∈ {-1,0,1}, strength)
from data ≤ t only (`Expert` contract; prefix-invariance canary, §11). Per RTH
session:

1. **Opening range:** over the first `n_or = 12` RTH bars, track `OR_high` =
   running max high, `OR_low` = running min low. No position during the OR window
   (direction 0).
2. **Breakout entry (first only):** from the first RTH bar after the OR window
   (local time ≥ 10:30), the **first** bar whose **close** exceeds `OR_high`
   (established up to the prior bar) sets direction = +1 (LONG) from that bar's
   close; the first whose close is below `OR_low` sets direction = −1 (SHORT).
   Only the first breakout of the session is taken (one round-trip per session).
3. **Hold and exit:** hold the entered direction to the **last RTH bar** of the
   session; direction returns to 0 at/after the session's final RTH bar.
4. **No-breakout sessions:** direction 0 for the whole session.
5. **Strength:** constant 1.0 on held bars (no calibrated confidence; the 1.0
   PT/SL/timestop grid is dropped, retro-card priors #5-analogue). # justify:
   constant strength = no calibration claim; position size is the Layer-2 Kelly
   fraction, not a signal-strength taper.

**Stress-cell restriction (the H103 view).** H103's realized position on a
session is the shared ORB position **multiplied by the session's stress-cell
indicator** — i.e. flat on every non-stress session, identical to the shared ORB
on stress sessions. Because the stress indicator is a session-level PIT-clean
covariate known at/before session start (§3), this restriction introduces no
look-ahead and is a pure conditioning of the shared ledger, not a new signal. The
multiplicative stress indicator is a **rule-based** (realized-vol percentile) cell,
NOT a latent-state gate (ADR-0001 D5 compliance argued in §3): it is an ADR-0002
conditional-only expert, admissible, with the HMM entering only via the scalar
train-window cutoff, never the per-session membership.

**PIT property:** OR_high/OR_low use only RTH bars ≤ t within the session; the
breakout test uses close(t) vs the OR established up to t−1; the stress indicator
uses only pre-session trailing data. Enforced by the §11 signal-layer
prefix-invariance canary.

## 5. Estimator — shared-ledger backfill + RC-H103-1 stress-cell admission scan

- **(A) Shadow-ledger backfill (ADR-0003, Tier 0) — SHARED with H101.** The
  H101 ORB expert × **{ES, NQ}** × the four Kelly fractions {0.5, 0.75, 1.0, 1.25}
  (each a distinct `expert_id`, ADR-0013 D3) is backfilled once by
  `scripts/run_shadow_ledger_backfill.py`: signal → position policy (Layer 2) →
  Tier-0 bar-close execution + `futures_rt_v1` cost (Layer 3, `tier0_barclose.py`,
  exact levered log return with ruin representable) → append-only
  `ShadowLedgerWriter`. **H103 adds NO new backfill** — it reads the shared H101
  {ES, NQ} ledger rows (the RC-H101-1 canonical backfill, `expert_id=orb_first_hour_k*@1.0.0`,
  `asset ∈ {ES, NQ}`, already materialized 2026-07-16). The design pre-registers that
  no duplicate ledger is written for the shared ORB signal; H103 is a *conditioning*
  of that ledger, not a second expert.
- **(B) RC-H103-1 admission scan (ADR-0002(c)).** On the backfilled **{ES, NQ}**
  ledger, restrict to each instrument's **stress cell** (§3 primary, per-instrument
  cutoff §3) and its complement, aggregate the pre-cost per-session ORB return, and
  scan conditional gross edge over the §3 cells. **Correction:** Romano-Wolf stepwise
  ([Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x);
  per-hypothesis adjusted p via the efficient step-down of
  [Romano & Wolf 2016](https://doi.org/10.1016/j.spl.2016.02.012)) with a
  serial-dependence-preserving stationary block bootstrap
  ([Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870)) over
  the chronological per-session sequence (ADR-0002(c) default). **Multiplicity —
  per-instrument RW with a cross-instrument union bound (buildable, conservative).**
  The Romano-Wolf step-down runs PER INSTRUMENT on that instrument's single
  calendar-ordered per-session `gross` vector (the validated RC-H101-1 estimator
  `romano_wolf_stepm`, one series per symbol — NOT an unbuilt joint-panel resampler),
  controlling the within-instrument FWER over the §3 cells. The CROSS-instrument
  multiplicity (the two instruments are two families for the §10 "positive on either
  instrument" decision) is controlled by a **Šidák union bound** across the two
  per-instrument families: an instrument's cell is a screening rejection only if its
  RW-adjusted p ≤ 1 − (1 − α_screen)^(1/2), where α_screen is the DEFERRED project
  `screening_error_rate_target`. This over-controls the joint FWER (independent
  per-instrument resampling treats the two families as independent, which — given the
  strong positive ES–NQ dependence — inflates the effective test count and is therefore
  CONSERVATIVE, the correct direction under the ADR-0013 "more binding multiplicity
  under leverage" mandate). Validity does NOT hinge on a positive-orthant-dependence
  condition: the assumption-free Bonferroni union — reject-if-either at α_screen/2 per
  family, joint FWER ≤ 2·(α_screen/2) = α_screen for any dependence — is the fallback
  bound, and the Šidák level 1−(1−α_screen)^(1/2) ≈ α_screen/2 differs from it only
  negligibly, so the scheme controls the joint FWER regardless of the exact ES–NQ
  dependence class. A future exact joint calendar-aligned (ES,NQ)-panel RW
  (common block index preserving contemporaneous cross-instrument dependence) is a
  registered efficiency extension, not required for this admission gate. Registered as
  the family `RC-H103-1` in `config/multipletest_family.yaml` (both per-instrument
  sub-families + the Šidák union rule).
  **Prior correlated trial (ADR-0008 trial register, binding):** the RC-H101-1
  `high_vol` cell (top realized-vol TERCILE) was already scanned null on this exact
  shared ledger (ES mean −7.1e-5, worst of the vol cells; NQ RW-adj p 0.597, rotor
  p 0.288). H103's primary stress cell (the top realized-vol BAND at the §3
  HMM-occupancy cutoff) is a correlated re-test of the same vol-conditioning on the
  same ledger, NOT an independent first look; it is registered as a prior correlated
  trial in the trial register and folded into the §8 DSR N_trials deflation (§8). The
  scan increments the trial register (ADR-0008).
- **(C) Non-redundancy vs H101 (ADR-0002(d)) — MANDATORY RC-XCORR-1.** Because
  H103's traded sessions are a strict subset of H101's (§4), the pair is NOT
  admitted until the **RC-XCORR-1 cross-correlation check** measures the residual
  correlation / marginal-IR contribution of H103's net-of-cost per-session return
  series against H101's, against the ensemble-variance bound derived from the
  arsenal covariance (ADR-0002(d); never a fixed constant). Pre-registered as a
  required exhibit, operationalized in §10. This is the H103 analogue of the
  known structural dependence H101 §5 deferred to RC-XCORR-1.
- **Multiplicity/discovery level:** the screening/FWER level is the DEFERRED
  project-wide `screening_error_rate_target` (null); the scan runs and is reported
  **descriptively**; no cell is certified as a discovery until it is set.

## 6. Splitter

- **Rolling-origin (ADR-0004):** 24-month training, 6-month step, first origin
  2017-01-01 (the 24-month training, 6-month step, and 2017-01-01 first origin are
  all carried VERBATIM from the H900 §2 / ADR-0004 rolling-origin convention — a
  structural walk-forward constant, NOT H103-tuned), 15 windows × 2 instruments
  (ES, NQ) = 30 folds. The ORB rule
  is stateless, so it produces its signal causally over the whole span; the
  rolling-origin structure defines the walk-forward folds for the admission scan's
  edge series, and the conditioning covariates that carry training-window moments
  (realized-vol percentile, the stress-cutoff HMM-occupancy anchor of §3, the HMM
  state fit) are computed **train-window-only** (H001 §6 convention). The
  stress-cell cutoff (§3) is recomputed per origin from the training window's HMM
  stress occupancy — never from the eval window.
- **`purge` / `embargo`:** purge = `MAX_FEATURE_LOOKBACK_BARS` (288) at window
  boundaries; embargo = Politis-White automatic block length on the training
  5-minute returns (H900/H001 §6 by reference). The ORB signal is session-local
  (≤ 1 RTH day), well within the purge; the trailing-vol covariate lookback is
  covered by the 288-bar purge.
- **Matched-turnover random rotor (ADR-0007, non-waivable):** the admission scan
  benchmarks the stress-cell ORB edge against a matched-turnover random-entry
  rotor **restricted to the same stress sessions** on the same ledger — a
  stress-cell breakout claim must beat random entries at matched turnover *within
  the stress cell*, not merely against a whole-sample rotor. Registered as a
  required confirmation-ladder exhibit.

## 7. Cost model

- **`cost_model_id`:** `futures_rt_v1` — bar-level per-side log-return drag applied
  at Tier 0 (ADR-0006 D4: cost at every tier). One round-trip per traded (stress)
  session → turnover 2 per traded session; per-unit drag =
  `switch_drag_notional / 2` (`tier0_barclose.py` convention). Notional basis
  (H900 §7 primary); account-dollar basis reported as a sensitivity.
- **Cost-basis reconciliation (RC-H103-1 obligation, retro card §2/§8 priors #5).**
  The 1.0 H054 cost share is basis-indeterminate on the source record (≈2%
  notional basis to ≈37% account-dollar basis on the 7-trade anti arm); the
  admission scan reports pre-cost edge (ADR-0002) and the formula-consistent
  notional-basis drag (ES ≈1.21e-4, NQ ≈4.15e-5 per active session — H101 §7 basis,
  from the retro card §2 derivation) alongside the account-dollar basis,
  basis-labeled — resolving the 1.0 indeterminacy. The NQ account-dollar basis has
  no 1.0 anti-arm anchor (the retro card is ES-only), so NQ's basis is resolved by
  the scan itself rather than reconciled to a 1.0 record. Sparse-fire experts at retail account scale can carry a
  materially higher account-dollar cost share (retro card §8 priors #5); the
  scan reports both so the position-layer (ADR-0005), not the signal, is the
  cost lever.
- **Fidelity tier:** 0 (bar-close). Scalping/limit claims out of scope (ADR-0006).

## 8. Gate thresholds

- **`alpha`:** 0.05 (two-sided CIs; H1 uses the one-sided lower bound) for
  descriptive per-cell CIs. # justify: conventional level for the descriptive CIs;
  the binding discovery/FWER level is the DEFERRED `screening_error_rate_target`,
  not 0.05 — no cell is certified until it is set (ADR-0002(c)).
- **CI method:** stationary bootstrap (Politis & Romano 1994), PW automatic block
  length, over the chronological per-session gross-return sequence within the
  stress cell; Ledoit-Wolf studentized bootstrap
  ([Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002)) for the
  stress-vs-complement (and any pairwise) Sharpe comparison — this is the 2.0
  analogue of the H054 anti-minus-unconditional differential statistic
  (retro card §2), and it is algebraically dependent, so the studentized bootstrap
  over the paired per-session series is required; single-strategy Sharpe CI via
  the **autocorrelation-adjusted (time-series) variant** of
  [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453).
- **Stationarity diagnostic (registered a priori).** Before the block bootstrap
  runs, register: (a) a KPSS level+trend test
  ([Kwiatkowski, Phillips, Schmidt & Shin 1992](https://doi.org/10.1016/0304-4076(92)90104-Y))
  on the stress-cell per-session gross-return series, and (b) a rolling-origin
  sub-window mean/variance stability exhibit AND a **stress-cell occupancy
  stability exhibit** (the per-window realized fire rate vs the HMM-occupancy
  anchor of §3 — directly tests the retro card §3 concern that the 1.0 design's
  10% fire-rate estimate transferred poorly to the realized 2.95%). **Action if
  rejected:** reported, not silently bootstrapped over; the affected span is
  dispositioned per the ADR-0009 re-specify path and the per-window dispersion
  becomes the primary stability read.
- **Power floor (n_anti; retro card §2/§6 — H103-specific, binding).** The 1.0
  record established the stress arm at **n_anti = 7 trades** (237 sessions, 2.95%
  fire rate) against a design-derived requirement of **n ≥ 174** stress-cell
  trades for 80% power — a structural `power-margin-low`. RC-H103-1 therefore
  **accumulates the stress-cell trade count over the full 2015–2025 backfill** and
  is **not certifiable until the stress-cell active-trade count reaches the
  design-derived floor** (the re-derived power-analysis floor at freeze; the
  n ≥ 174 figure is the **ES anchor only**, carried from the 1.0 design §9.2 which
  is ES-only, and re-verified by the `power-analysis` skill at the registered
  effect/alpha/power before running — retrospective power is forbidden,
  [Hoenig & Heisey 2001](https://doi.org/10.1198/000313001300339897)). **The floor
  is per-instrument-derived:** freeze-time power analysis yields (n_ES, n_NQ) from
  EACH instrument's own effect-size/variance estimate; the ES effect size is NOT
  transported to NQ (NQ has no 1.0 stress-arm evidence), so n_NQ is derived from NQ's
  own training-window stress-cell moments. If the full-span
  accumulation still falls short of the floor, the disposition is
  `conditional-only / power-margin-low` (not archive), continuing accumulation on
  the shadow ledger (retro card §8 priors #4: the ledger is the only affordable
  accumulation path). **Per instrument (ES+NQ):** the n ≥ 174 floor is applied to
  **each instrument's own stress-cell trade count** — an instrument is certifiable
  only when ITS stress cell clears the floor; ES and NQ may reach it at different
  times (NQ's stress-occupancy and fire rate are calibrated on NQ's own training
  window, §3), and the disposition is reported per instrument.
- **DSR (ADR-0008, non-waivable):** the scan reports the Deflated Sharpe Ratio over
  the conditioning-cell selection surface, more binding under the ADR-0013 leverage
  mandate. **N_trials** counts the full RC-H103-1 selection surface (both instruments
  × §3 cells) PLUS the **entire RC-H101-1 same-ledger surface** already scanned on
  this exact shared ledger (RC-H101-1 self-declared N_trials=10, itself "a lower
  bound … the H052a retro lineage adds more"). The whole RC-H101-1 surface — not only
  its directly-correlated `high_vol` cell — is folded in, because every RC-H101-1 cell
  is a prior look at the same ledger; this is the conservative choice (over-counting
  the shared-ledger lineage can only raise the deflation benchmark). The sr_std
  cross-trial dispersion is estimated over the non-nested conditioning cells (RC-H101-1
  §3.3 convention). The vol-conditioning re-test is thus never deflated as an
  independent first look.
- **PBO — DEFERRED, not waived (ADR-0008):** the sibling RC-H101-1 (§3.5) established
  that CSCV/PBO ([Bailey, Borwein, López de Prado & Zhu 2017](https://doi.org/10.21314/JCF.2016.322))
  is structurally inapplicable on this exact surface — the conditioning cells are
  session subsets on different memberships (no common T for the CSCV matrix), and the
  configuration axis CSCV would run over is the Kelly-fraction grid, which is BLOCKED
  on the two Decision-9 memos. H103 inherits the identical obstruction: PBO is deferred
  with the same rigor as the screening-level deferral — **no admission is certified
  while it is outstanding** — and is materialized at the shadow-ledger backfill once the
  common-T Kelly×cell matrix exists.
- **Non-redundancy gate vs H101 (ADR-0002(d); binding, see §10):** the RC-XCORR-1
  residual-correlation / marginal-IR bound must be cleared before the H101+H103
  pair is admitted — a mandatory gate, not a report object, given the algebraic
  dependence.
- **Precision:** the stress-cell gross-edge CI half-width must be < 25% of the
  point estimate for the cell to be report-eligible. # justify: the 25% fraction
  is inherited VERBATIM from the H900/H101 §8 CONSORT-style precision convention
  (a qualitative reporting threshold, not H103-tuned); avoids retrospective power
  (Hoenig & Heisey 2001). Given the §8 power floor this is expected to be the
  binding report-eligibility constraint at low accumulated n.

## 9. Stopping rule

- **Fixed design:** consume the shared H101 {ES, NQ} backfill × 4 Kelly fractions
  over the full 2015–2025 span; run RC-H103-1 once over the frozen §3 cell set with the
  stress cell as primary. No cell added, no window added, no re-run with different
  ORB parameters or a different stress cutoff post-freeze.
- **Max folds:** 15 rolling windows (§6 arithmetic) × 2 instruments (ES, NQ) = 30.
- **Accumulation exception (pre-registered):** if the stress-cell trade count is
  below the §8 power floor at first run, the scan continues to accumulate on the
  shadow ledger (retro card §8 priors #4) and re-reports descriptively; this is
  accumulation of the *same* frozen design on new bars, not a re-specification.
- **Non-convergence / degenerate cells:** reported, never re-run (H900 §9
  convention).

## 10. Decision rule

- **admit-conditional** (ADR-0002/0009): the stress cell shows Romano-Wolf-
  corrected positive gross edge (once the screening level is set), stress-cell
  precision met at the §8 power floor, the edge beats the stress-restricted
  matched-turnover random rotor, **AND the RC-XCORR-1 non-redundancy gate against
  H101 clears** — then H103 (stress-state-only ORB) is admitted to the arsenal
  conditional on that cell.
- **MANDATORY H101-dependence correlation gate (RC-XCORR-1 — operationalized).**
  Because H103 is algebraically dependent on H101 (strict session subset, §4), the
  pair is admitted only if H103's net-of-cost per-session return series clears the
  ADR-0002(d) non-redundancy bound against the H101 series. **Operationalization —
  PER INSTRUMENT (ES, NQ).** Because H103's traded sessions are a strict subset of
  H101's *within* each instrument, RC-XCORR-1 is computed per instrument and the pair
  is admitted per instrument (consistent with the §8 per-instrument power floor and
  the §10 "positive on either instrument" decision): for each of ES and NQ,
  (i) compute the H103-vs-H101 per-session return correlation on that instrument's
  aligned shadow ledger and its stationary-block-bootstrap CI; (ii) compute H103's
  estimated **marginal contribution to ensemble IR** given H101 already in the
  arsenal ([Grinold 1989, J. Portfolio Management 15(3):30-37](https://doi.org/10.3905/jpm.1989.409211)
  framework, per ADR-0002(d)); (iii) admit the pair on that instrument only if the
  marginal IR contribution is positive OR the residual correlation is below the
  ensemble-variance-budget bound derived from that instrument's (H101, H103)
  covariance estimate — the bound is derived and documented per admission per
  instrument, never a fixed constant. If
  H103 fails the bound (its stress-cell edge is spanned by H101), the disposition
  is **redundant-with-H101** — H103 is NOT separately admitted; the stress
  conditioning is instead recorded as a property of the already-admitted H101
  ledger (a diversifier-pairing negative result, retro card §4 structural note (i)).
- **re-specify-cost-bound:** positive gross stress-cell edge but net-negative
  after `futures_rt_v1` at the reconciled basis — re-spec (ADR-0009), not archive.
- **conditional-only / power-margin-low:** positive stress-cell point estimates but
  the accumulated trade count is below the §8 power floor — continue shadow
  accumulation (the 1.0 H054 state; retro card §6), provisional disposition, not
  archive.
- **archive(null):** no corrected-significant positive gross stress cell on either
  instrument (ES, NQ) (falls back to `archive-no-gross-edge`, ADR-0002(e)) — only at
  adequate power.
- The **binding certification** awaits the deferred screening level and the §8
  power floor; until then the scan is descriptive and the disposition provisional.
  Null results stay in the register; "fail" is not a disposition (ADR-0009).
  Terminal deliverable: the updated H103 Expert Card (ADR-0009).

## 11. Reproducibility commitments

- **git HEAD (at run):** auto-populated
- **`uv pip freeze` sha (at run, 64-hex):** auto-populated
- **RNG seed:** 20260716  # justify: pre-registered; bootstrap/rotor seeds derived
  as seed + replicate_index; do not modify post-hoc
- **Dataset checksums (frozen at pre-reg from `data/_manifest.json`):** the
  `data/processed/vendor_legacy_1min_roll_adjusted/` per-file SHA-256 entries as of
  the freeze commit; identical substrate to H900/H101 (ES and NQ) — the frozen
  per-file SHA-256 set covers both instruments' processed files.
- **PIT canaries (ADR-0008 D1):** (a) the feature-pipeline `pit_canary_future_mutation`
  (including the stress-cell indicator, which must be pre-session-computable);
  (b) the signal-layer `assert_prefix_invariant` cut-sweep on the shared ORB
  expert (`experts/base.py`), run in the backfill driver before any write.
- **Reproducibility log path:** `logs/reproducibility/repro_log_<run_id>.json`
  (the `ShadowLedgerWriter` emits the per-batch ReproLog; the RC-H103-1 driver
  emits the run-level one with this design.md SHA in `config_resolved_sha256`).
- **Burned-data ledger (ADR-0008 D5):** RC-H103-1 consumes the OOS windows it
  scans and records them in `config/burned_data_ledger.yaml` per ADR-0004 window
  (the retro card §7 already recorded the 1.0 ES 2025-01-01 → 2025-12-03 span
  under `hid: H103, instrument: ES`; the NQ span is burned by this scan and recorded
  under `hid: H103, instrument: NQ`).
- **Design.md SHA at freeze:** the SHA-256 over this file's frozen content is
  recorded in `hypothesis_backlog.md` (H103 row, `frozen_sha256=`) and in the
  pre-registration ReproLog `config_resolved_sha256` — not embedded here (that would
  be self-referential). To verify the freeze, recompute this file's SHA-256 and
  compare to the backlog/ReproLog value.
</content>
</invoke>
