---
title: "RC-H103-1 — H103 stress-state-ORB admission scan disposition"
hypothesis_id: H103
scan_id: RC-H103-1
adr_refs: [ADR-0001, ADR-0002, ADR-0003, ADR-0006, ADR-0007, ADR-0008, ADR-0009, ADR-0013]
date: 2026-07-16
status: DESCRIPTIVE (screening level deferred; held provisional)
disposition: provisional-archive-null (no stress-cell edge; RC-XCORR-1 redundancy instrument-specific)
seed: 20260716
hmm_seed: 20260710
harness: scripts/run_rc_h103_1_scan.py
artifact: reports/H103/rc_h103_1_scan.json
design_sha256: 84d01a6b4ad0971fd518ffa3d325d7ec93d7e44ce28d5e97066ca974baa345aa
---

# RC-H103-1 — H103 stress-state-ORB admission scan disposition

## 0. One-line result

On the shared H101 {ES, NQ} Tier-0 shadow ledger, the first-hour ORB restricted to the
pre-registered STRESS cell (top realized-vol band, cut at the H900 HMM stationary
stress-occupancy p̂ = 0.190 ES / 0.214 NQ) carries **no admission-grade conditional gross
edge**: ES stress is *negative* (Sharpe −0.040), NQ weakly positive and far from rejection
(Romano-Wolf-adjusted p = 0.415, Šidák per-family level 0.0253), neither beats its
stress-restricted rotor, DSR < 0.5 both, and BOTH stress cells **fail the §8 25% precision
gate** (CI half-width 2.4–3.5× the point estimate — the mean is indistinguishable from
zero). The Ledoit-Wolf paired anti-gate differential (stress vs calm) is **not significant**
on either instrument (p = 0.33 ES / 0.95 NQ). RC-XCORR-1 non-redundancy vs H101 (net-of-cost)
is **instrument-specific**: ES is redundant (negative residual IR −0.018, and the ES ORB is
net-negative after costs), NQ is *technically* non-redundant but the residual IR is ≈ 0
(negligible marginal contribution). **Disposition: provisional-archive-null** — held
descriptive (screening level deferred); no cell certified.

## 1. Scope

RC-H103-1 executes the H103 frozen design (SHA `84d01a6b4ad0…`) §5(B) admission scan
(ADR-0002(c)): does the first-hour ORB carry conditional gross per-session edge in the
STRESS cell? H103 is the anti-gate conditioning of the SAME ORB rule H101 trades
unconditionally — it shares H101's single backfilled ledger, not a second expert (§4). It
directly tests the Lundström prior (ORB edge concentrated in high-vol sessions) that
RC-H101-1's high-vol tercile already failed to corroborate.

- **Descriptive**, per the deferred `screening_error_rate_target`: no cell certified; the
  disposition is provisional (matching the sibling RC-H101-1 label).
- **PBO DEFERRED** (design §3.5), not waived.
- Tier-0 bar-close ledger (ADR-0006) — no scalping/intrabar claim.

## 2. Stress-cell definition (design §3) and its leakage posture

Per instrument, the H900 4-state diagonal-Gaussian HMM (standardized [ret_5m,
log_rvol_5m_24h] emissions, seed 20260710, 5 EM restarts) was fit; the stress state is the
highest-log-rvol-mean state; p̂ = its stationary occupancy. The stress cell = sessions with
realized-vol percentile ≥ (1 − p̂).

| Instrument | p̂ (stationary) | empirical MAP occupancy | stress-cell n | fraction |
|---|---:|---:|---:|---:|
| ES | 0.190 | 0.195 | 437 | 19.2% |
| NQ | 0.214 | 0.219 | 481 | 21.8% |

The stationary p̂ and the empirical causal-filter MAP occupancy agree to ~0.5pp, validating
the cutoff. **Leakage posture (honest):** this descriptive scan fits the HMM and cuts the
percentile on the FULL sample. Because the stress indicator *defines* H103's positions
(multiplicative, §4) — not merely slicing an unconditional strategy for reporting, as
RC-H101-1's tercile did — the full-sample cutoff is **genuine look-ahead** relative to the
registered per-rolling-origin train-window cutoff (design §3/§6;
`config/conditioning_covariates.yaml` reference_distribution =
`training_window_empirical_cdf`). It is retained here ONLY because the leakage is
**anti-conservative for H0** — it can only *inflate* apparent stress edge — so a
null/negative stress result is robust to it a fortiori. The leakage-clean per-origin cutoff
is the CERTIFIED-run version, deferred with the screening level and PBO. The realized
stress fraction (~19–22%) is far above the 1.0 H054 realized fire rate (2.95%, n_anti=7).

## 3. Results

### 3.1 Conditioning cells (descriptive; per-instrument Romano-Wolf StepM)

Studentized one-sided statistic (H0: mean gross ≤ 0), FWER-adjusted p over the 5-cell
family per instrument (Romano-Wolf 2005/2016), seed 20260716, N_bootstrap=1000. The
cross-instrument (2-family) screening threshold is the Šidák per-family level **0.0253** at
α=0.05 (design §5(B)); nothing approaches it.

| Instrument | Cell | n | mean gross | Sharpe | RW-adj p | rejected |
|---|---|---:|---:|---:|---:|:--:|
| ES | unconditional | 2276 | +6.6e-05 | +0.0095 | 0.493 | no |
| ES | **stress (PRIMARY)** | 437 | **−5.1e-04** | −0.0402 | 0.794 | no |
| ES | non_stress | 1839 | +2.0e-04 | +0.0435 | 0.097 | no |
| ES | first_hour_up | 1203 | +2.0e-04 | +0.0311 | 0.295 | no |
| ES | first_hour_down | 1046 | −8.1e-05 | −0.0109 | 0.769 | no |
| NQ | unconditional | 2202 | +1.9e-04 | +0.0230 | 0.341 | no |
| NQ | **stress (PRIMARY)** | 481 | +4.1e-04 | +0.0293 | 0.415 | no |
| NQ | non_stress | 1721 | +1.3e-04 | +0.0223 | 0.402 | no |
| NQ | first_hour_up | 1186 | +4.0e-04 | +0.0486 | 0.172 | no |
| NQ | first_hour_down | 1007 | −3.3e-05 | −0.0038 | 0.551 | no |

**The Lundström prior is contradicted, not merely unconfirmed.** On ES the stress cell is
the *worst* cell (Sharpe −0.040), and the **non_stress** cell is the *best* (Sharpe +0.044,
RW-adj p 0.097 — the nearest any cell comes to rejection): on ES the ORB gross edge lives in
CALM sessions, the direction *opposite* the prior. On NQ the stress cell is weakly positive
(0.029) with no concentration over unconditional. Both RC-H101-1 (high-vol tercile, null)
and RC-H103-1 (top-p̂ stress band, null/negative) converge on this.

### 3.2 Matched-turnover rotor (ADR-0007) — restricted to stress sessions

Direction-mode rotor, N=2000, on the STRESS-cell gross series (design §7).

| Instrument | stress mean | expert percentile | rotor p |
|---|---:|---:|---:|
| ES | −5.1e-04 | 0.194 | 0.806 |
| NQ | +4.1e-04 | 0.739 | 0.261 |

Neither stress cell beats its own stress-restricted rotor (ES is *below* the random-entry
median; NQ p=0.261).

### 3.3 Deflated Sharpe (ADR-0008) — stress cell

N_trials = 20 = RC-H103-1 surface (2×5) PLUS the full RC-H101-1 same-ledger surface (10,
design §8). σ_SR = 0.0305 over the non-nested cells pooled across instruments. HAC
(Newey-West 1994) effective n.

| Instrument | n | n_eff | observed SR | benchmark SR | DSR |
|---|---:|---:|---:|---:|---:|
| ES | 437 | 391 | −0.0402 | +0.058 | 0.023 |
| NQ | 481 | 332 | +0.0293 | +0.058 | 0.301 |

Both far below the deflation benchmark; DSR < 0.5 → stress-cell Sharpe indistinguishable
from the selection-adjusted null.

### 3.4 Stationarity (design §8) — KPSS

Level KPSS ('c', primary read) does not reject at 5% (ES 0.056, NQ 0.298; 5% crit 0.463) —
the block-bootstrap stack's weak-stationarity premise holds; no §8 re-specify.

### 3.5 §8 precision gate — BOTH cells FAIL

Report-eligibility (design §8): the stress-cell gross-edge CI half-width must be < 25% of
|point estimate| (the inherited H900/H001 CONSORT-style reporting convention). Stationary
block-bootstrap CI on the stress-cell mean gross:

| Instrument | point (mean gross) | 95% CI | half-width | half-width / \|point\| | meets 25% gate |
|---|---:|---:|---:|---:|:--:|
| ES | −5.1e-04 | [−1.8e-03, +6.8e-04] | 1.24e-03 | 2.43 | **no** |
| NQ | +4.1e-04 | [−1.1e-03, +1.8e-03] | 1.44e-03 | 3.49 | **no** |

Both fail decisively: the CI half-width is 2.4–3.5× the point estimate, i.e. the stress-cell
mean is **statistically indistinguishable from zero**. "Powered" (n ≥ the ES anchor, §3.8)
refers to *sample size*, NOT estimate precision — at this near-zero effect the estimate is
imprecise regardless of n. This is the binding report-eligibility constraint the design §8
anticipated.

### 3.6 Ledoit-Wolf anti-gate differential (design §8) — not significant

The 2.0 analogue of the 1.0 H054 anti-minus-unconditional differential: a Ledoit & Wolf
2008 studentized time-series (stationary block) bootstrap of the paired Sharpe difference
(stress vs complement / unconditional, net-of-cost, on the realizable H103 series). The legs
are algebraically dependent, so the paired studentized bootstrap is required.

| Instrument | comparison | Sharpe diff | studentized stat | p-value | 95% CI |
|---|---|---:|---:|---:|---:|
| ES | stress − non_stress | −0.028 | −0.97 | 0.330 | [−0.086, +0.029] |
| ES | stress − unconditional | −0.008 | −0.59 | 0.535 | [−0.032, +0.017] |
| NQ | stress − non_stress | +0.002 | +0.07 | 0.950 | [−0.066, +0.070] |
| NQ | stress − unconditional | −0.003 | −0.21 | 0.825 | [−0.031, +0.024] |

No paired comparison is significant. On ES the stress cell is descriptively worse than calm
(diff −0.028) but the paired test does not reject (p=0.326); on NQ there is no difference.
The anti-gate differential — the central H054-lineage statistic — carries no signal.

### 3.7 RC-XCORR-1 non-redundancy vs H101 (ADR-0002(d), MANDATORY, per-instrument, NET-OF-COST)

H103's realizable net-of-cost per-session series (ORB net masked to stress sessions, flat
elsewhere) vs H101's unconditional net-of-cost series, per instrument. The Grinold marginal
IR is the residual (appraisal) ratio of H103 after projecting out H101,
(SR_103 − ρ·SR_101)/√(1−ρ²); it is positive iff SR_103 > ρ·SR_101 (the covariance-DERIVED
non-redundancy bound, §10(iii), never a fixed constant).

| Instrument | net SR H101 | net SR H103 | corr ρ | bound ρ·SR_101 | residual IR | adds? |
|---|---:|---:|---:|---:|---:|:--:|
| ES | −0.0164 | −0.0238 | 0.798 | −0.0131 | **−0.0179** | no |
| NQ | +0.0144 | +0.0113 | 0.785 | +0.0113 | **+0.0000** | (barely) |

**Redundancy is instrument-specific, not uniform** (correcting an earlier over-claim):

- **ES: redundant.** The residual IR is negative (−0.018) — H103 *detracts* from an
  H101-holding portfolio. Note the ES ORB is itself **net-negative** after Tier-0 costs
  (SR_101 = −0.016), so both legs lose net; H103 adds nothing.
- **NQ: technically non-redundant, but negligibly.** SR_103 (0.0113) barely exceeds the
  bound (0.0113); the residual IR is ≈ 0.0000 — the marginal contribution to the ensemble IR
  is indistinguishable from zero. H103 is not *spanned* by H101 on NQ, but it adds no
  meaningful diversification.

So RC-XCORR-1 does not clear H103 as a value-adding separate member on either instrument (ES
redundant; NQ zero-marginal). The high return correlation (~0.79) reflects that H103's
sessions are a strict subset of H101's.

### 3.8 Power (design §8)

Both stress cells exceed the n≥174 ES-anchor sample-size floor (ES 437, NQ 481). Per design
§8 this is the ES anchor ONLY; the per-instrument n_ES/n_NQ re-derivation from each
instrument's own effect/variance (retrospective power forbidden, Hoenig & Heisey 2001) is a
**certified-run step, DEFERRED**. So `exceeds_es_anchor` is a lower-bound sample-size check,
not the certified per-instrument floor — and §3.5 shows the estimate is imprecise regardless
of n.

## 4. Disposition (design §10)

**provisional-archive-null (no descriptive positive stress-cell edge; held descriptive).**

- **admit-conditional** — NOT met: no cell has a Romano-Wolf-corrected positive gross edge
  (every RW-adj p ≥ 0.10, Šidák level 0.0253); the stress cell does not beat its rotor;
  DSR < 0.5; the cells fail the 25% precision gate; the LW anti-gate is non-significant.
- **redundant-with-H101 (ADR-0002(d))** — instrument-specific: MET on ES (negative residual
  IR), NOT met on NQ (residual IR ≈ 0, technically non-redundant but zero-marginal). Because
  it is not met on all instruments, the disposition is NOT labeled uniformly
  redundant-with-H101; the redundancy is reported per instrument.
- **archive(null)** — the substantive result: no corrected-significant positive gross stress
  cell on either instrument (`archive-no-gross-edge`, ADR-0002(e)).

Held **provisional / descriptive** pending the deferred screening level (matching the
RC-H101-1 precedent). No plausible screening level rescues an admission (every stress-cell
RW-adj p ≥ 0.42, the cells fail report-eligibility, and the stress edge adds no marginal IR
over H101). H103 stays in the register; "fail" is not a disposition (ADR-0009).

## 5. What this establishes

- The **Lundström "ORB edge concentrates in high-vol sessions" prior is contradicted** on
  this substrate — decisively on ES (edge in calm, not stress), unsupported on NQ. RC-H101-1
  (tercile) and RC-H103-1 (HMM-occupancy band) converge.
- The **anti-gate re-specification of 1.0 H054 does not survive**: no stress-cell edge, an
  imprecise (zero-indistinguishable) estimate, a non-significant anti-gate differential, and
  no marginal IR over the unconditional ORB (ES redundant, NQ zero-marginal).
- The arsenal remains **empty** (H101 provisional-null, H103 provisional-archive-null); no
  ADR-0002(d) covariance anchor is authored.

## 6. Reproducibility

- Harness [scripts/run_rc_h103_1_scan.py](../../../scripts/run_rc_h103_1_scan.py), scan seed
  20260716, HMM seed 20260710 (H900 §11), N_bootstrap=1000, N_rotors=2000.
- In-run ReproLog `logs/reproducibility/repro_log_<run_id>.json` (git HEAD, pip-freeze
  SHA-256, dataset checksums, seeds, H103 frozen-design SHA-256).
- Machine artifact [reports/H103/rc_h103_1_scan.json](../../../reports/H103/rc_h103_1_scan.json).
- Estimators: `romano_wolf_stepm`, `deflated_sharpe_ratio`, `matched_turnover_rotor`,
  `sharpe_ratio_difference_test` (Ledoit-Wolf 2008, new; 9 tests); HMM via the ported H900
  `GaussianHMM` (4-state diag); KPSS via statsmodels.

## 7. Opens

- The `non_stress`/`first_hour_up` cells (ES calm-session ORB edge, RW-adj p 0.097; NQ
  first-hour momentum, p 0.172) are directionally positive but not descriptively significant
  and NOT pre-registered primaries — logged as hypothesis-generating for a *separately
  pre-registered* scan, not a post-hoc rescue.
- The leakage-clean per-rolling-origin stress cutoff, the exact Lo-2002 TS Sharpe SE, the
  per-instrument freeze-time power-floor re-derivation, and PBO are the CERTIFIED-run
  refinements, deferred with the screening level.
