---
name: H101 — Unconditional first-hour opening-range breakout (ES/NQ), shadow-ledger admission
description: Pre-registered 2.0 design doc for hypothesis H101 (re-specification of 1.0 H052a)
type: project
hypothesis_id: H101
tier: 5
status: designed  # designed | running | evaluated | archived(positive|null|negative)
owner: SKIE
created: 2026-07-16
citations: 10.1016/j.frl.2012.09.001, 10.1109/ACCESS.2019.2899177, 10.1093/rfs/1.1.41, 10.1111/j.1468-0262.2005.00615.x, 10.1080/01621459.1994.10476870, 10.1016/j.jempfin.2008.03.002, 10.2469/faj.v58.n4.2453, 10.1016/0304-4076(92)90104-Y
external_doi: null
---

# H101 — Unconditional first-hour opening-range breakout (ES/NQ), shadow-ledger admission

This document is the pre-registration record for hypothesis H101 (the 2.0
re-specification of 1.0 H052a). It is frozen at `designed` status; any change
after that point requires a new hypothesis ID.

H101 is the first forward **arsenal-admission candidate** (ADR-0002) executed on
the 2.0 shadow ledger, promoted from the retro Expert Card
([docs/reports/expert_card_H052a_retro_2026-07-10.md](../../../docs/reports/expert_card_H052a_retro_2026-07-10.md),
disposition `arsenal-admit-conditional`). Per that card the admitted form is the
**unconditional first-hour opening-range breakout** — the HMM gate is dropped on
H052a's own evidence (gate increment null; filters the wrong direction) and per
[ADR-0001 Decision 5](../../../docs/decisions/ADR-0001-allocator-unit-of-inference.md),
and the 1.0 PT/SL/timestop label grid is dropped (retro-card priors-update #5:
that grid added selection noise, inner-CV Sharpe negative at its optimum). What
remains is the simple published rule the ADR-0002 Context literature arc favors.

Two objects are pre-registered: (A) the **H101 ORB expert** (a Layer-1 signal
producer conforming to the `Expert` contract) backfilled to the shadow ledger
(ADR-0003), and (B) the **RC-H101-1 admission scan** — the ADR-0002(c)
conditional-gross-edge test on that ledger, with the primary cell family set by
the Lundström high-volatility prior (retro card §3).

**Governance blocks respected by construction.** Growth-based ranking and
Kelly-fraction selection are BLOCKED until the two Decision-9 Kelly memos are
numerically instantiated; the discovery/FWER screening level is the DEFERRED
project-wide `screening_error_rate_target`. So the ledger materializes all four
Kelly fractions and the admission scan runs and is reported **descriptively** —
no arm is certified and no fraction selected until those unblock.

## 1. Hypothesis

- **H0:** the unconditional first-hour ORB has no positive pre-cost (gross)
  per-session edge in any pre-declared conditioning cell (§3) on either
  instrument, at the ADR-0002(c) multiplicity-corrected level once the deferred
  screening level is set. Operationally, the Romano-Wolf-corrected lower bound on
  the mean gross per-session ORB return is ≤ 0 in every cell.
- **H1:** ∃ a conditioning cell on ≥1 instrument with a Romano-Wolf-corrected
  positive gross per-session ORB edge — i.e. the breakout carries conditional
  gross edge admissible under ADR-0002(c). The **primary pre-registered cell
  family** is high-realized-volatility sessions (Lundström prior; retro card §3),
  the direction opposite the rejected non-stress HMM gate.
- **Mechanism:** opening-range breakouts capture intraday momentum/continuation
  following the price discovery of the first session hour — documented on index
  futures by [Holmberg, Lönnbark & Lundström 2013](https://doi.org/10.1016/j.frl.2012.09.001)
  and [Tsai et al. 2019](https://doi.org/10.1109/ACCESS.2019.2899177) (reports
  positive, statistically-significant timely-ORB profitability across index-futures
  markets; specific magnitudes not reproduced here — full text paywalled, only the
  Crossref-verified title/venue/year are asserted), and re-confirmed post-2013 by
  Zarattini, Barbon & Aziz 2024 ([SSRN 4729284](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4729284),
  *working paper*). The 1.0 NQ cell (+10.61% realized OOS over 369 sessions,
  forward P(loss) 18.6%) is directionally consistent with that literature.
- **Primary citations:** Holmberg, Lönnbark & Lundström 2013 (10.1016/j.frl.2012.09.001);
  Tsai et al. 2019 (10.1109/ACCESS.2019.2899177 — the DOI corrected from the 1.0
  §15.1 errata's non-resolving 10.1109/ACCESS.2019.2899852, per the retro card);
  Lo & MacKinlay 1988 (10.1093/rfs/1.1.41, the variance-ratio conditioning state);
  Romano & Wolf 2005 (10.1111/j.1468-0262.2005.00615.x, the admission-scan FWER).

## 2. Universe and sample period

- **Instruments:** ES, NQ (2.0 roll-adjusted continuous-contract evidence bars,
  `data/processed/vendor_legacy_1min_roll_adjusted/`, ADR-0011), adopted by
  reference from H900/H001 §2 to keep the ledger on the identical substrate.
- **Frequency:** 5-minute bars aggregated from the 1-minute substrate (H900 §3
  aggregation rule by reference).
- **Session:** **RTH only** for the ORB (the 1.0 signal is an RTH first-hour
  breakout). RTH = the local-time window `[09:30, 16:00)` in `America/New_York`
  (DST-aware via the tz conversion of `ts_event`; the CME equity-index regular
  session, an exchange constant, not a tunable). Bars outside RTH are not part of
  the ORB signal (position flat), but the ledger's per-bar counterfactual is
  written for every valid bar (counterfactual completeness, ADR-0003 D1) — the
  ORB position is simply 0 outside its held intraday window.
- **Sample period:** 2015-01-02 → 2025-12-31 (full materialized span).
- **Exclusions (registered a priori):** identical to H900 §2 — (a) `pit_provisional`
  bars; (b) `substrate_defects[DEC_ROLL_LATE_COMMIT]` windows excluded in primary,
  included in the inclusive-variant sensitivity. December-roll windows remain
  *excluded*, not *corrected* (no Databento repull — operator decision 2026-07-16).
- **Roll-handling:** roll-adjusted continuous contract; close-to-close adjusted
  log returns (H900 §2 by reference).

## 3. Features and conditioning set

- **Session structure (per RTH session, causal):** the opening-range window is
  the first `n_or` RTH bars; `OR_high`/`OR_low` are the running high/low over that
  window. # justify: `n_or = 12` five-minute bars = the first 60 minutes — the
  "first-hour" opening range registered VERBATIM in the 1.0 H052a design and carried
  unchanged for comparability with the retro evidence; a session-structure constant
  from the source signal definition, not tuned against the H101 outcome. (The ORB
  *class* is literature-supported — Holmberg 2013, Tsai 2019, Zarattini 2024 — but
  the specific 60-minute length is the H052a definition; Zarattini uses a 5-minute
  opening range and does not authorize the 60-minute window.)
- **ADR-0002(b) conditioning set (frozen before the scan).** The RC-H101-1
  admission scan (§5) conditions on the project-standard set
  ([config/conditioning_covariates.yaml](../../../config/conditioning_covariates.yaml)):
  realized-vol percentile, variance-ratio trend/range state (Lo & MacKinlay 1988),
  macro-calendar proximity, spread/liquidity regime — plus two pre-registered
  extensions: the registered `regime_hmm_h900` covariate, and **first-hour sign**
  (the sign of the RTH first-hour return), a design-motivated ORB covariate (retro
  card §3). All covariates are causal (≤ session start / ≤ bar t), PIT-clean.
- **Primary cell family:** high-realized-vol sessions (Lundström prior). All cells
  reported; the high-vol family is the pre-registered primary (§10).

## 4. Signal construction (the ORB rule)

The H101 expert emits a per-bar Layer-1 signal (direction ∈ {-1,0,1}, strength)
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
   Close-confirmation (not intra-bar touch) keeps the signal computable at bar
   close and Tier-0-fillable without look-ahead.
3. **Hold and exit:** hold the entered direction to the **last RTH bar** of the
   session; direction returns to 0 at/after the session's final RTH bar (flat into
   ETH/overnight). One entry, one exit per session.
4. **No-breakout sessions:** direction 0 for the whole session.
5. **Strength:** constant 1.0 on the held bars (full conviction; the simple
   unconditional ORB has no calibrated confidence — the 1.0 PT/SL/timestop grid is
   dropped per retro-card priors #5). # justify: constant strength = no
   calibration claim; the position size is the Layer-2 Kelly fraction, not a
   signal-strength taper.

**PIT property:** OR_high/OR_low use only RTH bars ≤ t within the session; the
breakout test uses close(t) vs the OR established up to t−1; no future bar enters
any bar's direction. Enforced by the §11 signal-layer prefix-invariance canary.

## 5. Estimator — ledger backfill + admission scan

- **(A) Shadow-ledger backfill (ADR-0003, Tier 0).** The H101 expert × {ES, NQ} ×
  the four Kelly fractions {0.5, 0.75, 1.0, 1.25} (each a distinct `expert_id`,
  ADR-0013 D3) is backfilled by `scripts/run_shadow_ledger_backfill.py`: signal →
  position policy (Layer 2) → Tier-0 bar-close execution + `futures_rt_v1` cost
  (Layer 3, `tier0_barclose.py`, exact levered log return with ruin representable)
  → append-only `ShadowLedgerWriter`. Counterfactual completeness: a row for every
  valid bar, flat bars included.
- **(B) RC-H101-1 admission scan (ADR-0002(c)).** On the backfilled ledger,
  aggregate the pre-cost per-session ORB return and scan conditional gross edge
  over the §3 cells. **Correction:** Romano-Wolf stepwise
  ([Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x)) with a
  serial-dependence-preserving stationary block bootstrap
  ([Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870)) over
  the chronological per-session sequence (the ADR-0002(c) default), registered as
  a new family in `config/multipletest_family.yaml`. Increments the trial register
  (ADR-0008). **Non-redundancy (ADR-0002(d)):** trivial at an empty arsenal (H001
  archived null; arsenal size 0) — the first admission **defines** the
  arsenal-covariance / residual-correlation bound memo every later candidate is
  tested against; the known structural dependence with H103 (same ORB on the
  complementary session subset) is deferred to RC-XCORR-1.
- **Multiplicity/discovery level:** the screening/FWER level is the DEFERRED
  project-wide `screening_error_rate_target` (null); the scan runs and is reported
  **descriptively**; no cell is certified as a discovery until it is set.

## 6. Splitter

- **Rolling-origin (ADR-0004):** 24-month training, 6-month step, first origin
  2017-01-01 (H900 §2 by reference), 15 windows × 2 instruments. The unconditional
  ORB rule is stateless (no trained component), so it produces its signal causally
  over the whole span; the rolling-origin structure defines the walk-forward
  evaluation folds for the admission scan's edge series, and the conditioning
  covariates (realized-vol percentile, HMM state) that DO have training-window
  moments/fits are computed train-window-only (H001 §6 convention).
- **`purge` / `embargo`:** purge = `MAX_FEATURE_LOOKBACK_BARS` (288) at window
  boundaries; embargo = Politis-White automatic block length on the training
  5-minute returns (H900/H001 §6 by reference). The ORB signal itself is
  session-local (≤ 1 RTH day), well within the purge.
- **Matched-turnover random rotor (ADR-0007, non-waivable):** the admission scan
  benchmarks the ORB edge against a matched-turnover random-entry rotor on the same
  ledger — a breakout claim must beat random session-cadence entries at matched
  turnover. Registered as a required confirmation-ladder exhibit.

## 7. Cost model

- **`cost_model_id`:** `futures_rt_v1` — bar-level per-side log-return drag applied
  at Tier 0 (ADR-0006 D4: cost at every tier). One round-trip per session (entry +
  RTH-close exit) → turnover 2 per traded session; per-unit drag =
  `switch_drag_notional / 2` (`tier0_barclose.py` convention). Notional basis
  (H900 §7 primary); account-dollar basis reported as a sensitivity.
- **Cost-basis reconciliation (RC-H101-1 obligation, retro card §3/priors #3):**
  the 1.0 card's ≈3e-4 drag quote is inconsistent with its own formula; the
  admission scan reports pre-cost edge (ADR-0002) and the formula-consistent
  notional-basis drag (ES ≈1.21e-4, NQ ≈4.15e-5 per session) alongside the
  account-dollar basis, basis-labeled — resolving the 1.0 indeterminacy.
- **Fidelity tier:** 0 (bar-close). Scalping/limit claims out of scope (ADR-0006).

## 8. Gate thresholds

- **`alpha`:** 0.05 (two-sided CIs; H1 uses the one-sided lower bound) for
  descriptive per-cell CIs. # justify: conventional level for the descriptive CIs;
  the binding discovery/FWER level is the DEFERRED `screening_error_rate_target`,
  not 0.05 — no cell is certified until it is set (ADR-0002(c)).
- **CI method:** stationary bootstrap (Politis & Romano 1994), PW automatic block
  length, over the chronological per-session gross-return sequence; Ledoit-Wolf
  studentized bootstrap ([Ledoit & Wolf 2008](https://doi.org/10.1016/j.jempfin.2008.03.002))
  for any pairwise cell/instrument Sharpe comparison; single-strategy Sharpe CI via
  the **autocorrelation-adjusted (time-series) variant** of
  [Lo 2002](https://doi.org/10.2469/faj.v58.n4.2453) (the per-session series carries
  serial dependence; the IID Sharpe-CI variant would understate the SE).
- **Stationarity diagnostic (registered a priori).** The bootstrap / Romano-Wolf /
  Lo-2002 stack presumes weak stationarity of the per-session gross-return series,
  which the block length addresses only for serial dependence, not cross-regime
  level/variance shifts over 2015-2025. Before the block bootstrap runs, register:
  (a) a KPSS level+trend stationarity test
  ([Kwiatkowski, Phillips, Schmidt & Shin 1992](https://doi.org/10.1016/0304-4076(92)90104-Y))
  on the per-session gross-return series per instrument, and (b) a rolling-origin
  sub-window mean/variance stability exhibit (the 15 walk-forward windows' per-window
  gross-edge dispersion). **Action if rejected:** a stationarity rejection is
  reported, not silently bootstrapped over — the affected span is dispositioned per
  the ADR-0009 re-specify path (the block bootstrap CI is reported with the
  non-stationarity flagged as a caveat, and the per-window dispersion becomes the
  primary stability read rather than the pooled CI).
- **DSR / PBO (ADR-0008, non-waivable):** the admission scan reports the Deflated
  Sharpe Ratio and the Probability of Backtest Overfitting over the conditioning-cell
  selection surface; both are more binding under the ADR-0013 leverage mandate.
- **Precision:** the primary-cell gross-edge CI half-width must be < 25% of the
  point estimate for the cell to be report-eligible. # justify: the 25% fraction is
  inherited VERBATIM from the H900/H001 §8 CONSORT-style precision convention (a
  qualitative reporting threshold, not an empirically-derived or H101-tuned
  constant); avoids retrospective power (Hoenig & Heisey 2001).

## 9. Stopping rule

- **Fixed design:** backfill H101 × 2 instruments × 4 Kelly fractions over the full
  2015-2025 span; run RC-H101-1 once over the frozen §3 cell set. No cell added, no
  window added, no re-run with different ORB parameters post-freeze.
- **Max folds:** 15 rolling windows (§6 arithmetic) × 2 instruments.
- **Non-convergence / degenerate cells:** reported, never re-run (H900 §9 convention).

## 10. Decision rule

- **admit-conditional** (ADR-0002/0009): ∃ cell with Romano-Wolf-corrected positive
  gross edge (once the screening level is set), primary-cell precision met, and the
  edge beats the matched-turnover random rotor — H101 (unconditional ORB) is
  admitted to the arsenal conditional on that cell; its ledger becomes the arsenal
  anchor and the ADR-0002(d) covariance-bound memo is authored.
- **re-specify-cost-bound:** positive gross edge but net-negative after
  `futures_rt_v1` at the reconciled basis — re-spec disposition (ADR-0009), not
  archive; the edge is real but the Tier-0 cost path eats it (a Tier-2 execution
  study could rescue it).
- **archive(null):** no corrected-significant positive gross cell on either
  instrument (falls back to `archive-no-gross-edge`, ADR-0002(e)).
- The **binding certification** awaits the deferred screening level; until then the
  scan is descriptive and the disposition is provisional. Null results stay in the
  register; "fail" is not a disposition (ADR-0009). Terminal deliverable: the
  updated H101 Expert Card (ADR-0009).

## 11. Reproducibility commitments

- **git HEAD (at run):** auto-populated
- **`uv pip freeze` sha (at run, 64-hex):** auto-populated
- **RNG seed:** 20260716  # justify: pre-registered; bootstrap/rotor seeds derived
  as seed + replicate_index; do not modify post-hoc
- **Dataset checksums (frozen at pre-reg from `data/_manifest.json`):** the
  `data/processed/vendor_legacy_1min_roll_adjusted/` per-file SHA-256 entries as of
  the freeze commit; identical substrate to H900/H001.
- **PIT canaries (ADR-0008 D1):** (a) the feature-pipeline `pit_canary_future_mutation`;
  (b) the signal-layer `assert_prefix_invariant` cut-sweep on the H101 ORB expert
  (`experts/base.py`), run in the backfill driver before any write.
- **Reproducibility log path:** `logs/reproducibility/repro_log_<run_id>.json`
  (the `ShadowLedgerWriter` emits the per-batch ReproLog; the driver emits the
  run-level one with this design.md SHA in `config_resolved_sha256`).
- **Burned-data ledger (ADR-0008 D5):** RC-H101-1 consumes the OOS windows it scans
  and records them in `config/burned_data_ledger.yaml` per ADR-0004 window (the
  retro card already recorded the 1.0 ES/NQ 2023-H2–2024 spans under `hid: H101`).
- **Design.md SHA at freeze:** auto-populated by /preregister (R3-2a)
