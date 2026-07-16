---
title: "RC-H101-1 — H101 first-hour-ORB admission scan disposition"
hypothesis_id: H101
scan_id: RC-H101-1
adr_refs: [ADR-0002, ADR-0003, ADR-0006, ADR-0007, ADR-0008, ADR-0009, ADR-0013]
date: 2026-07-16
status: DESCRIPTIVE (provisional; binding screening level DEFERRED)
disposition: provisional-archive-null (held descriptive; not certified, not archived)
seed: 20260716
harness: scripts/run_rc_h101_1_scan.py
artifact: reports/H101/rc_h101_1_scan.json
---

# RC-H101-1 — H101 first-hour-ORB admission scan disposition

## 0. One-line result

On the backfilled Tier-0 shadow ledger (ES/NQ, 2015–2025, primary-exclusion
substrate), the unconditional first-hour opening-range-breakout expert (H101,
`orb_first_hour@1.0.0`, `n_or`=12) carries **no admission-grade conditional gross
edge** in the pre-registered primary cell (high-realized-volatility sessions; the
*Lundström prior* — that ORB returns concentrate in high-volatility states — is
[Holmberg, Lönnbark & Lundström 2013, Finance Research Letters 10(1):27-33](https://doi.org/10.1016/j.frl.2012.09.001),
with the underlying volatility-state return decomposition in Lundström, "Day
trading returns across volatility states" (DiVA diva2:732318)). No conditioning
cell rejects under Romano-Wolf FWER control (every cell's adjusted p ≥ 0.17), the
primary cell does not beat its own matched-turnover random rotor on either
instrument (ES rotor p=0.558, NQ p=0.288), the KPSS stationarity assumption holds
(neither instrument rejects at 5%), and the primary-cell Sharpe sits below the
Deflated-Sharpe deflation benchmark (DSR 0.13 ES / 0.34 NQ, < 0.5). **Disposition:
provisional-archive-null, held descriptively** — no cell is certified or archived
because the binding `screening_error_rate_target` is DEFERRED (design §5/§8/§10).

## 1. Scope and what this scan does / does not decide

RC-H101-1 executes the H101 frozen design (§5B) admission scan (ADR-0002(c)): does
the unconditional first-hour ORB carry a **conditional GROSS (pre-cost) per-session
edge** in a pre-declared conditioning cell? It is the **first arsenal-admission
decision** in the SKIE-Universe-2 allocator program (H001 archived null → arsenal
size 0 before this scan).

- **Decides (descriptively):** the sign, magnitude, FWER-adjusted p-value, rotor
  percentile, KPSS stationarity verdict, and DSR of the ORB gross edge in each
  pre-registered cell.
- **Does NOT decide:** admission certification. The binding FWER/screening level is
  the project-wide `screening_error_rate_target`, which is null (deferred to the
  `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` cost-calibration memo, method-frozen
  2026-07-12, numeric level DEFERRED to the shadow-ledger backfill). Until it is set,
  **no cell is certified as a discovery**; every number below is descriptive.

Nothing here is a scalping or intrabar-execution claim: the ledger is Tier-0
bar-close (ADR-0006 D1), so ADR-0006 caps any reportable claim at Tier-0 fidelity.

## 2. Data and pipeline

- **Substrate:** `vendor_legacy_1min_roll_adjusted` (ES, NQ), roll-adjusted,
  primary-exclusion variant (December-roll windows and PIT-provisional bars
  excluded, not corrected — no new-data budget, operator decision 2026-07-16).
  5-minute aggregation; emission-valid bars only.
- **Ledger:** canonical `data/processed/shadow_ledger/`, `expert_id=orb_first_hour_k1.0@1.0.0`
  (Kelly fraction 1.0 = unit position → pre-cost ORB gross return). The full backfill
  materializes all four Kelly fractions; the admission scan reads k1.0 (the gross,
  size-neutral cell), since Kelly-fraction selection is BLOCKED on the two Decision-9
  memos.
- **Aggregation:** per-bar ledger `ret_gross` summed to per-SESSION gross return;
  entered mask = sessions the ORB traded (`ret_gross != 0` proxy — the Tier-0 ledger
  schema stores no explicit position/turnover column). No non-finite (ruin) session
  gross occurred on either instrument (0 excluded).
- **Conditioning covariates (per session, from the same substrate):** realized-vol
  proxy at the RTH open (full-sample tercile split → high/low-vol cells; a DESCRIPTIVE
  conditioning partition per ADR-0001-D5, not a gate — design §6's train-window-only
  moment rule binds gates, not descriptive covariates) and first-hour RTH return sign
  (up/down cells). Unconditional cell = all entered sessions.

Session counts after inner-join of ledger and covariates: ES n=2276, NQ n=2202.

## 3. Results

### 3.1 Conditioning cells (descriptive; Romano-Wolf StepM, FWER-adjusted)

Studentized one-sided statistic (H0: mean gross ≤ 0), FWER-adjusted p-value over the
5-cell family via the efficient step-down algorithm
([Romano & Wolf 2016](https://doi.org/10.1016/j.spl.2016.02.012); every cell receives
its monotone-enforced adjusted p, not only rejected cells). Seed 20260716,
N_bootstrap=1000, PW-selected stationary block (ES bl≈2.55, NQ bl≈3.15).

| Instrument | Cell | n | mean gross | Sharpe | t | RW-adj p | rejected |
|---|---|---:|---:|---:|---:|---:|:--:|
| ES | unconditional | 2276 | +6.6e-05 | +0.0095 | 0.45 | 0.612 | no |
| ES | **high_vol (PRIMARY)** | 763 | **−7.1e-05** | −0.0066 | −0.18 | 0.698 | no |
| ES | low_vol | 748 | +2.6e-05 | +0.0087 | 0.24 | 0.696 | no |
| ES | first_hour_up | 1203 | +2.0e-04 | +0.0311 | 1.08 | 0.355 | no |
| ES | first_hour_down | 1046 | −8.1e-05 | −0.0109 | −0.35 | 0.698 | no |
| NQ | unconditional | 2202 | +1.9e-04 | +0.0230 | 1.08 | 0.352 | no |
| NQ | **high_vol (PRIMARY)** | 747 | +2.3e-04 | +0.0179 | 0.49 | 0.597 | no |
| NQ | low_vol | 721 | −6.8e-05 | −0.0167 | −0.45 | 0.760 | no |
| NQ | first_hour_up | 1186 | +4.0e-04 | +0.0486 | 1.67 | 0.171 | no |
| NQ | first_hour_down | 1007 | −3.3e-05 | −0.0038 | −0.12 | 0.760 | no |

**Primary cell (high_vol, Lundström prior):** ES negative (t=−0.18), NQ positive but
far from rejection (t=0.49, adjusted p=0.597). The Lundström "ORB edge concentrates
in high-realized-vol sessions" prior is **not corroborated** on this substrate:
neither instrument's high-vol cell out-performs its own unconditional cell in a way
the FWER accounting survives, and on ES the high-vol cell is the *worst* of the vol
cells. Every cell's adjusted p ≥ 0.17.

**Strongest directional read:** the `first_hour_up` (momentum-continuation) cell —
NQ t=1.67 (adjusted p=0.171), ES t=1.08 (p=0.355). Directionally positive on both
instruments but **not descriptively significant** and, critically, **not a
pre-registered primary cell**; treating it as a discovery would be the exact post-hoc
cell-selection the Romano-Wolf family and the DSR are designed to penalize. It is
logged as a hypothesis-generating observation for a *separately pre-registered* future
scan, not a finding here.

### 3.2 Matched-turnover random rotor (ADR-0007, non-waivable)

Direction-mode rotor, N=2000, on the adjudicated **PRIMARY (high_vol)** cell (design
§10: the admitted cell's edge must beat the matched-turnover rotor). The unconditional
series is reported as a separate descriptive exhibit only.

| Instrument | cell | expert mean | expert percentile | rotor p |
|---|---|---:|---:|---:|
| ES | **high_vol (primary)** | −7.1e-05 | 0.443 | 0.558 |
| ES | unconditional (exhibit) | +6.6e-05 | 0.664 | 0.336 |
| NQ | **high_vol (primary)** | +2.3e-04 | 0.713 | 0.288 |
| NQ | unconditional (exhibit) | +1.9e-04 | 0.868 | 0.133 |

The primary cell does **not** beat its own matched-turnover rotor on either instrument
(ES p=0.558, NQ p=0.288). NQ's primary cell sits at only the 71st percentile of the
turnover-matched random-entry null. The ORB's entry *timing within high-vol sessions*
does not, on this evidence, add gross edge beyond a random rule of the same turnover.

### 3.3 Deflated Sharpe Ratio (ADR-0008, non-waivable) — primary cell

N_trials = 10 (the full instrument×cell selection surface; a lower bound on the true
historical trial count — the H052a retro lineage adds more — so the reported DSR is an
*upper* bound). σ_SR = 0.0227, the ddof=1 dispersion of the non-nested conditioning-cell
Sharpes pooled across both instruments (excludes the `unconditional` superset). The
primary-cell SE uses an **autocorrelation-adjusted effective sample size** — a
leading-order HAC *approximation* to the Lo-2002 time-series Sharpe SE (design §8):
Newey-West 1994 Bartlett-bandwidth variance-inflation of the return mean
(rules/quant-project.md HAC rule), `n_eff = n / VIF`. It captures the return-mean
long-run variance, not the exact Lo-2002 estimator (which also involves the
squared-return moments); adequate here as VIF is small and both DSR conclusions are
robust. Skew/kurtosis-adjusted
([Bailey & López de Prado 2014, J. Portfolio Management 40(5):94-107](https://doi.org/10.3905/jpm.2014.40.5.094)).

| Instrument | n | HAC VIF | n_eff | observed SR | benchmark SR | DSR |
|---|---:|---:|---:|---:|---:|---:|
| ES | 763 | 1.081 | 706 | −0.0066 | +0.0357 | 0.129 |
| NQ | 747 | 1.375 | 543 | +0.0179 | +0.0357 | 0.340 |

Both instruments' observed primary-cell Sharpe fall **below** the deflation benchmark
(the Sharpe a null strategy would achieve by chance given 10 trials at this effective
sample length and higher-moment profile). NQ's serial dependence is material (VIF=1.375,
i.e. the IID SE would have understated the SE by ~17%), which the HAC adjustment
absorbs. DSR < 0.5 on both → the primary-cell Sharpe is not distinguishable from the
selection-adjusted null. (PBO — see §3.5 — is DEFERRED, not computed.)

### 3.4 Stationarity (design §8) — KPSS + rolling-origin dispersion

**KPSS test** (design §8(a),
[Kwiatkowski, Phillips, Schmidt & Shin 1992](https://doi.org/10.1016/0304-4076(92)90104-Y);
auto lag=11) on the per-session gross series, run in **both** variants — level
`regression='c'` (the variant matching the constant-mean premise the block bootstrap /
Romano-Wolf / DSR stack actually relies on, reported as primary) and level+trend
`regression='ct'`:

| Instrument | level 'c' stat (5% crit 0.463) | reject? | trend 'ct' stat (5% crit 0.146) | reject? |
|---|---:|:--:|---:|:--:|
| ES | 0.089 | no | 0.076 | no |
| NQ | 0.320 | no | 0.068 | no |

Neither instrument rejects stationarity at 5% under **either** variant — the stack's
weak-stationarity presumption is **formally supported** (no §8 re-specify action
triggered). NQ's level statistic (0.320) is the nearest to its 5% critical value
(0.463) but does not reach it.

**Rolling-origin dispersion** (design §8(b)): the exhibit is computed over **22
full-span 6-month calendar bins (2015–2025)**, a superset of the §8(b) rolling-origin
folds (the §6 walk-forward defines ~15 post-2017-origin evaluation windows). The full-
span partition is reported here because the ORB expert is *stateless* (no fitted
train-window parameters), so per-window gross-edge dispersion is well-defined on every
6-month calendar block, not only post-origin folds; the KPSS §8(a) test is the primary
stationarity read and this is a supplementary exhibit. The per-window means alternate
sign around a near-zero level (mean-dispersion CV 7.6 ES / 4.5 NQ — a large CV driven
by a near-zero denominator, not a stationarity breach), consistent with the KPSS
non-rejection.

### 3.5 PBO — DEFERRED (not waived)

The Probability of Backtest Overfitting (design §8 / ADR-0008) is **deferred, not
computed**. Standard CSCV ([Bailey, Borwein, López de Prado & Zhu 2017, J. Comput.
Finance 20(4):39-69](https://doi.org/10.21314/JCF.2016.322)) requires a common-length
(T×N) performance matrix over alternative full-period strategy *configurations*. The
RC-H101-1 selection surface is not of that form: (a) the conditioning cells are session
*subsets* on different memberships (no common T), and (b) the configuration axis that a
CSCV would properly run over is the Kelly-fraction × cell grid, whose fraction axis is
BLOCKED on the two Decision-9 memos. PBO over that surface is materialized at the
shadow-ledger backfill once Kelly selection unblocks. It is deferred with the same rigor
as the screening-level deferral — **no admission is certified while it is outstanding**.

## 4. Disposition (design §10)

**provisional-archive-null, held DESCRIPTIVE.**

Mapping to the §10 decision rule:

- **admit-conditional** — NOT met. No cell has a Romano-Wolf-corrected positive gross
  edge (every adjusted p ≥ 0.17); the primary cell does not beat its own rotor; DSR is
  below benchmark on both instruments.
- **re-specify-cost-bound** — NOT reached. This path requires a *positive gross* edge
  that a cost model then eats. There is no admission-grade positive gross edge to begin
  with, so the cost path is not the binding constraint.
- **archive(null)** — this is the substantive result (`archive-no-gross-edge`,
  ADR-0002(e)): no corrected-significant positive gross cell on either instrument.

Per §10, the **binding certification awaits the deferred screening level** (and the
deferred PBO, §3.5), so the disposition is held **provisional/descriptive** rather than
executed as a final archive. H101 stays in the register as an open null-leaning
candidate; "fail" is not a disposition (ADR-0009). When `screening_error_rate_target` is
set and PBO materialized at the shadow-ledger backfill, this scan is re-run
bit-identically (seed 20260716) and the disposition finalized. On the current evidence,
no plausible screening level rescues an admission — every cell's adjusted p ≥ 0.17.

## 5. ADR-0002(d) non-redundancy note

Trivial at arsenal size 0 (H001 archived null). Had H101 admitted, it would have
**defined** the arsenal-covariance / marginal-log-wealth residual-correlation bound
that every later candidate is tested against. Since it does not admit, the arsenal
remains empty and the ADR-0002(d) anchor memo is **not** authored this scan. The known
structural dependence with H103 (same ORB rule on the complementary stress-state session
subset) remains deferred to RC-XCORR-1.

## 6. Reproducibility

- Harness: [scripts/run_rc_h101_1_scan.py](../../../scripts/run_rc_h101_1_scan.py),
  seed 20260716 (design §11), N_bootstrap=1000, N_rotors=2000.
- In-run ReproLog: emitted at `logs/reproducibility/repro_log_<run_id>.json` (git HEAD,
  pip-freeze SHA-256, dataset checksums from `data/_manifest.json`, seed, frozen-design
  SHA-256) before the scan runs — the artifact records the exact env + substrate.
- Machine artifact: [reports/H101/rc_h101_1_scan.json](../../../reports/H101/rc_h101_1_scan.json).
- Estimators: `romano_wolf_stepm`, `deflated_sharpe_ratio`, `matched_turnover_rotor`
  (confirmation-ladder modules, unit tests green); KPSS via statsmodels 0.14.6 (declared
  in the `data` extra so the pre-registered §8(a) test is runnable in the pinned env).
- Commit provenance via `/commit-with-provenance`.

## 7. What this closes and what it opens

- **Closes:** RC-H101-1 as a descriptive scan; the first arsenal-admission decision
  returns a provisional null. The confirmation-ladder machinery (Romano-Wolf, DSR,
  matched-turnover rotor, KPSS stationarity) is now exercised end-to-end on real ledger
  evidence. PBO is explicitly deferred (§3.5).
- **Opens (registered, not acted on here):**
  - The `first_hour_up` momentum-continuation observation → a *separately
    pre-registered* directional-cell scan (not a post-hoc rescue of H101).
  - Finalization of this disposition once `screening_error_rate_target` is set and PBO
    is materialized (post Kelly-unblock, shadow-ledger backfill).
  - H103 (stress-state ORB on the complementary subset) pre-registration, which tests
    whether the ORB edge lives in the sessions H101's cells excluded.
