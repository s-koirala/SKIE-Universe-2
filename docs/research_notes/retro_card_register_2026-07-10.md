# Retro Expert-Card register — closure of P1-2.0-RETRO-CARD-1.0-REGISTER (2026-07-10)

Five retroactive Expert Cards (ADR-0009 Decision 5) generated from the
SKIE-Universe 1.0 KPI report cards, as the first arsenal-admission candidates
and the dry run of the card template. All 1.0 evidence read at 1.0 repo HEAD
`ce018515a667ee63aa2d40234305f8cb677f030b` per the
[config/data_sources.yaml](../../config/data_sources.yaml)
`skie_universe_1_kpi_reports` registration. No new computation was run;
`trial_register_increment: 0` on every card. Backlog rows H100–H104
(Reanalysis block, Tier 5) added to [hypothesis_backlog.md](../../hypothesis_backlog.md)
with status `retro-card-emitted`.

Dispositions use the ADR-0009 §2.6 taxonomy. On a retro card the disposition
is the **candidate** determination the 1.0 evidence supports; actual arsenal
admission requires ADR-0002 (a)–(d), which no 1.0 run establishes (no 2.0
PIT-clean interface, no pre-registered conditioning-set scan, no Romano-Wolf
correction, no arsenal covariance). The scans listed below are the concrete
unlock conditions and become the 2.0 admission-scan prompts.

## Per-card digest

**H100 ← 1.0 H050** ([card](../reports/expert_card_H050_retro_2026-07-10.md)) —
`re-specify-cost-bound`. HMM regime-gating of a 1-min LightGBM directional
signal is the register's one significantly *negative* result: net
gated-vs-unconditional Sharpe differential CI excludes zero on the negative
side on both symbols (ES −0.03714 [−0.04052, −0.03390]; NQ −0.02185
[−0.02455, −0.01903]), realized −81%/−84% terminal wealth on the gated arms,
forward P(loss) 100%. The whole 1.0 record is net-of-cost. Gate transition
rates are per-symbol — **ES 30.33% / NQ 11.77% of bars** (1.0 INVESTIGATE
memo §6.3) — and the memo's §6.4 net-based attribution finds whipsaw
cost-drag of 1.87× (ES) / 5.66× (NQ) the full unconditional signal magnitude,
its §6.6 verdict ranking H-c whipsaw PRIMARY and H-b anti-selection secondary
(the gate state has worse per-bar net Sharpe than the discarded state on
both symbols, §6.1). That attribution is net-based, so the ADR-0002 pre-cost
decomposition (RC-H100-1) is still outstanding, and the 1.0-registered
discriminating variants (H050.invert, H050.stable-state) remain numeric-empty
smoke/placeholder cards. `archive-no-gross-edge` is unavailable without the
pre-cost decomposition. Standing 2.0 constraint either way: ADR-0001
Decision 5 (regime states as covariates only, never gates).

**H101 ← 1.0 H052a** ([card](../reports/expert_card_H052a_retro_2026-07-10.md)) —
`arsenal-admit-conditional`. The HMM gate increment was a non-significant
null (LW2008 CIs cover zero, both symbols) and filtered the wrong direction;
the informative object is the **unconditional first-hour ORB**, net-positive
on NQ (+0.855 annualised Sharpe, +10.61% realized over 369 sessions, forward
P(loss) 18.56%) — and net-positive implies pre-cost-positive, giving the
cleanest gross-edge lower bound in the register. Admitted form drops the HMM
gate; literature-anchored (Holmberg-Lönnbark-Lundström 2013; Tsai et al.
2019). Derived cost share of gross is material but **basis-indeterminate on
the 1.0 record** — NQ ≈13% (notional basis, formula-consistent) to ≈83%
(account-dollar basis); ES ≈74–99% — and the 1.0 card's quoted ≈3e-4
per-session drag is internally inconsistent with its own
`log(1 − cost/notional)` formula at its own stated notionals (Round-2
finding QUANT-2-2); the pre-cost admission framing and RC-H101-1 basis
reconciliation are therefore essential.

**H102 ← 1.0 H053** ([card](../reports/expert_card_H053_retro_2026-07-10.md)) —
`re-specify-cost-bound`. The only cost-free (hence directly gross) evidence
set: all four model arms point-positive (realized up to +10.8% NQ-LightGBM;
CPCV medians all positive) but the source card's own cost prior (10–20%/yr
on $10k) exceeds the best arm's ≈5.3%/yr gross — cost dominance over a
fragile gross edge (CPCV q05 < 0 on every arm; DSR ∈ [−3.81, −3.29];
calibration gate failed on all arms). Cost decomposition and a corrected
conditional-edge scan decide between admit and archive.

**H103 ← 1.0 H054** ([card](../reports/expert_card_H054_retro_2026-07-10.md)) —
`arsenal-admit-conditional`. The register's cleanest ADR-0002-shaped object:
first-hour ORB traded only in the HMM stress state (a proto realized-vol
conditioning cell), point-positive on every metric on fresh 2025 OOS
(annualised +0.573 vs −0.057 unconditional; +3.50% terminal wealth; forward
P(loss) 29.24% vs 52.50%; max-DD 3.19% vs 6.99%) at n_anti = 7 trades —
structurally below the design-derived n ≥ 174 for 80% power. Two-window
consistency with the H052a stress-subset reading weakly favors
"works, underpowered." Admission turns entirely on powered accumulation via
the shadow ledger.

**H104 ← 1.0 H055** ([card](../reports/expert_card_H055_retro_2026-07-10.md)) —
`arsenal-admit-conditional`, **on an explicitly post-hoc basis**. Largest
pre-cost point edge in the register, concentrated in the MGC cell across all
four aggressive-sizing configs (MPPM(ρ=1) +0.185…+0.263; cell ROI +58…+87%)
— but MGC is **excluded from the frozen design §2 universe** ({ES, NQ, MES,
MNQ}) and SIL is absent from the design entirely, so the flagship cell is an
unregistered universe extension; the realized sweep window (to 2026-05-15)
also runs ~5 months past the registered OOS edge (2025-12-03 ES / 2025-12-19
NQ). The frozen §1 H_1 (LW2008 strict tri-benchmark net-Sharpe dominance per
instrument-class) was never evaluated; the KPI cards' MPPM/Calmar/PF vector
is a post-freeze ADR-0017/0018/0024 paradigm substitution, whose own PF > 1.1
component is unmet even on MGC (max 1.04). Under that substituted vector the
verdict is null at basket level on ES/NQ/SIL (ES cell-level indeterminate —
one positive sized cell, C3, not robust across configs). Also the least
integrity-complete candidate: leakage canary deferred, 13-field ReproLog
absent (`repro-log-incomplete` per the 2026-05-18 v1 corrigendum,
incorporated), known-optimistic next-bar-open entry vs the design's
limit-at-wick semantic (a Tier-2 claim class per ADR-0006), no MPPM CI, no
multiplicity correction over the 5-config × 4-symbol selection surface, cost
deliberately zero, and a documented v1↔v2 reconciliation failure (four
discrepant v1-column cells; worst: C5 basket quoted −10.0%/+3.5% where v1
Table 1 reports −6.6%/+3.0%). The 1.0 MGC investigation memo
(`INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS.md`,
2026-05-19, incorporated as a source of record) sharpens the stability
picture: cell-level MGC sub-window ROI C2 +13.44% / C9 +7.61% / C5 +8.52% /
C3 −4.75% (sidecar `cd95ebdb`), with §7a assessing "regime-conditional
underperformance has started" on C3 (decay onset ≈ 2026-Q2) — fragility
localizes in the always-on super-Kelly position layer, partially absorbable
by decay-adaptive sizing; and its §6.5/§7d fixed-cell hindsight-bias caveat
(Phase O.7.5 precedent: hindsight fixed-cell H062 C3 MGC −94% failed
walk-forward CV) binds the +87% headline to exploration-tier status pending
walk-forward inner-CV.

## Follow-up scan list (future admission-scan prompts)

Every scan below increments the trial register (`config/multipletest_family.yaml`)
when run, per ADR-0008; conditioning sets must be frozen per ADR-0002 (b)
before scanning.

| Scan ID | Card | Prompt |
|---|---|---|
| RC-H100-1 | H100 | Pre-cost decomposition of the H050 gated vs unconditional per-bar series (from 1.0 `artifacts/runs/H050/31d23ecd.../oos_returns.parquet` or shadow-ledger re-materialization): separate selection (gross) from cost-drag. Still required despite the 1.0 INVESTIGATE memo §6.4 attribution, which is arithmetic on the two net-of-cost arms and does not yield the pre-cost per-cell edge ADR-0002 (c) needs. |
| RC-H100-2 | H100 | Production runs of the 1.0-registered H050.invert and H050.stable-state (N ∈ {3,5,10,20}) variants; their v1 cards are numeric-empty. |
| RC-H100-3 | H100 | Romano-Wolf-corrected conditional-edge scan of the unconditional 1-min LightGBM signal over the ADR-0002 project-standard conditioning set. |
| RC-H101-1 | H101 | Pre-cost per-session unconditional-ORB conditional-edge scan (ADR-0002 standard set + pre-registered first-hour-sign extension; Lundström-direction high-vol cells as primary family), Romano-Wolf corrected, ES + NQ. |
| RC-H102-1 | H102 | Apply the bar-level cost model to the H053 Stage-3 v4 OOS series (per-session log-return drag); emit net terminal-wealth / Calmar / profit-factor; quantify the cost-bound classification. |
| RC-H102-2 | H102 | Pre-cost conditional-edge scan of the H053 arms over the ADR-0002 standard set (LightGBM arms primary), Romano-Wolf corrected; registers the retro 2-model × 2-symbol × CPCV trials in the family. |
| RC-H103-1 | H103 | Pooled ES + NQ + MES + MNQ pre-cost ORB scan with realized-vol percentile replacing the learned HMM stress state (ADR-0001 Decision 5), Romano-Wolf corrected, accumulated on the shadow ledger to n ≥ 174 stress-cell trades; also test the fire-rate gap (design 10% vs realized 2.95%). |
| RC-H104-1 | H104 | Signal-layer (unsized, per ADR-0005 separation) wick-rejection conditional-edge scan over ADR-0002 standard set + instrument, pre-cost, Romano-Wolf corrected. The registered retro-trial surface MUST include, as researcher degrees of freedom: the 1.0 5-config × 4-symbol sweep surface; the window extension (realized OOS to 2026-05-15, ~5 months past the registered 2025-12-03/19 edge); and the universe extension (MGC, SIL unregistered — fresh admission cycle with a new trial-register entry per ADR-0002's post-hoc obligation). |
| RC-H104-2 | H104 | Cost-model application to the MGC cells (3,000–10,000 trades/config) — first-order cost-share estimate. 1.0 lineage: `P1-H055-COST-EMPIRICAL-CALIBRATION`, BLOCKING-BEFORE-PAPER-TRADE per the H055 MGC investigation memo §7a. |
| RC-H104-3 | H104 | Integrity closure (blocking before any H104 admission): PIT-canary suite, 13-field ReproLog wire, limit-fill-at-wick entry semantic, MPPM(ρ=1) CI primitive, walk-forward inner-CV (1.0 lineage: `P1-H055-OPTUNA-INNER-CV-IMPL`; fixed-cell hindsight-bias caveat per MGC memo §6.5/§7d, Phase O.7.5 walk-forward-refutation precedent), and v1↔v2 numeric reconciliation (discrepant v1-column cells: C5 OOS −10.0% vs v1's −6.6%; C5 sub-window +3.5% vs +3.0%; C3 sub-window −4.1% vs −4.4%; C2 sub-window +4.0% vs +4.1%). |
| RC-XCORR-1 | all | Pairwise net-of-cost residual correlations among the five retro candidates from 1.0 OOS return artifacts (H101/H103 session-complement pairing; H054↔H052a algebraic dependence; H053 window nested in the ORB first hour; H104 the sole non-equity-index / mean-reversion candidate). Feeds ADR-0002 (d) once the first admission defines the covariance bound. |

## Cross-cutting evidence gaps (all five cards)

1. No 1.0 hypothesis has a pre-registered ADR-0002 (b) conditioning set —
   every §3 panel is a declared gap plus a scan, not a filled table.
2. Arsenal is empty at card time — every §4 ensemble block is null-valued by
   construction; the first admission must produce the correlation-bound
   derivation memo.
3. No rolling-origin edge series exists anywhere in 1.0 (single/few folds,
   or CPCV dispersion without time order) — §5 stability profiles rest on
   window splits and external literature; the ADR-0004 regime plus ADR-0003
   shadow-ledger backfill is the systematic remedy.
4. Burned-data mirror entries for all 11 consumed OOS spans (H100 ×2,
   H101 ×2, H102 ×2, H103 ×1, H104 ×4) were **recorded 2026-07-10** in
   [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml),
   exactly as tabulated in each card's §7 (Round-1 remediation; commit SHA
   pending — working tree left uncommitted for the audit round).
5. Registration-conformance retro-review is itself a finding class: the H055
   KPI cards misquote their own frozen design (window, universe, H_1) — retro
   cards must always be checked against the frozen design.md, not only
   against the KPI cards (Round-1 finding QUANT-1-1).

---

## ADR-0013 re-adjudication addendum (2026-07-14)

**Why this addendum exists.** This register was authored 2026-07-10, before the
aggressive geometric-growth mandate [ADR-0013](../decisions/ADR-0013-aggressive-geometric-growth-mandate.md)
and the champion-challenger [ADR-0012](../decisions/ADR-0012-standing-incumbent-allocator.md)
were accepted (2026-07-12). Its metric currency is therefore old-paradigm — every
disposition, dominance test, and cost-bound above is expressed in **net-Sharpe /
LW2008 tri-benchmark CIs, terminal-wealth q05 lower-tail quantile, and
MPPM/Calmar/PF**. ADR-0013 changes the objective, so the register's *admission
protocol* (not its recorded 1.0 evidence, which is frozen) must be re-expressed.
This addendum performs the **metric-currency reconciliation** only; the **numeric
re-adjudication is DEFERRED/BLOCKED** (see "Deferral" below). `P1-2.0-RETRO-CARD-1.0-REGISTER`
stays **OPEN**.

**Paradigm delta applied to the admission protocol.**

1. **Ranking/dominance metric.** The binding admission and ranking criterion is
   now **geometric (compounded / Kelly log-wealth) growth** — mean log-wealth
   growth rate on the ADR-0003 shadow ledger — replacing the net-Sharpe LW2008
   tri-benchmark dominance the 1.0 frozen designs used. LW2008 studentized
   bootstrap CIs remain the *pairwise comparison* instrument, but on the
   log-wealth-growth statistic, not annualized Sharpe.
2. **Lower-tail quantile demoted.** The terminal-wealth q05 lower-tail quantile
   (H100/H104 dispositions lean on it) is now a **monitored, non-binding
   guardrail** (ADR-0013): still computed at the same block-bootstrap length and
   reported, but it informs rather than vetoes. A card is no longer archived
   *solely* because q05 < 0; it is judged on mean log-wealth growth, with q05 as
   context.
3. **Kelly fraction swept, not fixed.** Every card's position layer is evaluated
   over the registered Kelly-fraction grid **{0.5, 0.75, 1.0, 1.25}** (ADR-0013
   Decision 3), the winner data-selected on geometric growth per the frozen
   [kelly_growth](../methodology/kelly_growth_concavity_ruin_2026-07-12.md)
   estimator. This **replaces H104's ad-hoc super-Kelly / C3 sizing configs** and
   H050's "fractional-Kelly-with-tail-binding" default with a registered sweep.
4. **Non-redundancy re-expressed.** ADR-0002 (d) non-redundancy (RC-XCORR-1)
   is re-expressed on **marginal log-wealth growth** contribution to the
   allocator, not net-of-cost Sharpe residual correlation; admission is loosened
   toward aggressive inclusion (conditional-edge + non-redundancy structure kept).
5. **Discovery alpha cost-tuned looser.** The Romano-Wolf FWER correction stamped
   on every RC-* scan is superseded by the cost-tuned discovery target of the
   frozen [discovery_alpha](../methodology/discovery_alpha_cost_calibration_2026-07-12.md)
   memo (SPA/StepM FWER, or FDR where the cost analysis supports it); the level
   is the analysis output, not a constant, and missed compounding is weighted
   above false discovery.
6. **Integrity core is MORE binding, never weaker.** DSR, PBO, the
   matched-turnover random rotor, PIT canaries, the trial register, ReproLog, and
   the shadow ledger stay **non-waivable and strictly more binding under leverage**
   (ADR-0013): an overfit champion sized by the Kelly sweep does not merely
   underperform, it earns **negative geometric growth (ruin)** on a fake edge.
   The H104/RC-H104-3 integrity closure (leakage canary, ReproLog, walk-forward
   inner-CV, v1↔v2 reconciliation) is thus **hard-blocking**, and H102's failed
   DSR ∈ [−3.81, −3.29] / calibration gate is a stronger reject at leverage, not
   a softer one.

**Per-card re-adjudication direction** (disposition currency updated; numeric
verdict deferred):

| Card | 1.0 currency (superseded) | Direction under ADR-0013 |
|---|---|---|
| H100 ← H050 | net-Sharpe differential CI < 0; −81/−84% terminal wealth | Gated arms are **ruinous negative log-wealth growth** — a *stronger* reject at leverage. `re-specify-cost-bound` stands; RC-H100-1 pre-cost decomposition still required to rank the *unconditional* signal on marginal log-wealth growth. |
| H101 ← H052a | unconditional NQ ORB +0.855 Sharpe / +10.61% realized | Cleanest **positive geometric-growth** candidate; rank on log-wealth growth over the Kelly sweep. Basis-indeterminate cost (RC-H101-1) still blocks. |
| H102 ← H053 | cost dominance; CPCV q05<0; DSR∈[−3.81,−3.29] | q05 demoted to guardrail, but the failed DSR/calibration integrity gate is **more binding under leverage**; fragile edge → ruin risk if sized. `re-specify-cost-bound` stands. |
| H103 ← H054 | HMM-stress ORB point-positive, n_anti=7 ≪ 174 | Strongest ADR-0002-shaped conditional object; admission turns on **powered geometric-growth accumulation** on the shadow ledger over the Kelly sweep. `arsenal-admit-conditional` direction retained. |
| H104 ← H055 | post-hoc MGC +58…+87% ROI, super-Kelly configs | Largest pre-cost edge **but** unregistered universe extension + integrity-incomplete + super-Kelly C3 decay — the exact overfit-at-leverage → **ruin** case ADR-0013 makes hard-blocking. Kelly sweep replaces super-Kelly configs; RC-H104-3 integrity closure is blocking-before-admission. |

**Deferral (BLOCKING).** No admission and no Kelly-fraction selection on
geometric growth is certified by this addendum. Numeric re-adjudication is gated
on **all** of: (a) the ADR-0003 shadow-ledger backfill (step-4) that materializes
the per-card marginal log-wealth-growth series — no rolling-origin edge series
exists in 1.0 (gap 3 above); (b) the on-ledger NUMERIC instantiation of both
BLOCKING Kelly memos (f*, P(ruin), f_0; discovery alpha level, π1, FWER-vs-FDR
criterion), still deferred per [CLAUDE.md](../../CLAUDE.md); and (c) the
`P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE` margin/dwell freeze before any of these
candidates could dethrone a standing champion (ADR-0012). Until then the RC-*
scan list stands with its **structure** intact and its **metric currency**
updated to geometric growth per this addendum.

---

## H103 stress-record correction addendum (2026-07-18)

**Lundström high-vol-concentration prior
([Holmberg, Lönnbark & Lundström 2013, FRL 10(1):27-33](https://doi.org/10.1016/j.frl.2012.09.001)):
UNRESOLVED as of 2026-07-18.** The RC-H103-1 "contradicted" reading
(2026-07-16) was rendered on a **leaked** stress-cell construction
(full-sample realized-vol percentile cutoff): ES stress mean gross
−5.0922e-04/session, n = 437 sessions, bootstrap stat −0.8404. The certified
**leakage-clean per-origin** construction (RC-H103-2, frozen 2026-07-17)
re-measures the same cell at +1.0295e-04/session, n = 313 sessions, stat
+0.1544. Neither statistic is distinguishable from zero. A sign flip under a
leakage repair, on 28% less data, is **not corroboration and not powered to
resolve the prior** (powered null at the design-registered n ≥ 174 floor;
unpowered for the far smaller observed effect) — it is a
construction-dependence exhibit (the two records differ in both boundary
estimation and classified session coverage; the flip is not attributable to
leakage alone), and the prior is neither contradicted nor supported by the
records on file. Correction of record:
[expert_card_v3.md](../../research/01_hypothesis_register/H103/expert_card_v3.md).

**WITHDRAWN:** the H103 per-card digest's two-window stress-subset consistency
argument (verbatim from the digest above: "Two-window consistency with the
H052a stress-subset reading weakly favors "works, underpowered"" — the quoted
verb is the 1.0-era claim being withdrawn, reproduced here only for exact
identification) is withdrawn as support for the prior — its 2.0-side
leg descends from the leaked construction lineage. The 1.0 evidence itself
stays frozen exactly as recorded above; only the consistency *argument* is
withdrawn. The H052a retro card's Lundström-direction prediction reading
(card §§ cited above) inherits the same UNRESOLVED status.
