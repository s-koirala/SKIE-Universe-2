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
