---
# Expert Card — machine-readable frontmatter (schema per ADR-0009 §3)
hid: H104                             # 2.0 reanalysis HID; 1.0 source HID = H055
card_version: 1
predecessor_card: null
design_md_sha256: ded53acc96f5ae9d4691efd5101784519592dee555e6f94a8e25c5313b66ee50   # 1.0 H055/design.md at 1.0 HEAD ce018515
repro_log_run_ids: [v2_sweep_20260518T220351Z]   # 1.0 sweep sidecar run id; canonical 13-field ReproLog ABSENT (repro-log-incomplete)
data_span: { start: 2024-01-01, end: 2026-05-15 }  # realized sweep OOS right edge (v1 §Table 1, substrate b93e544); registered design §2 OOS ends 2025-12-03 (ES+MES) / 2025-12-19 (NQ+MNQ) — realized window is a ~5-month post-hoc extension
instruments: [ES, NQ, MGC, SIL]       # as SWEPT; frozen design §2 universe is {ES, NQ, MES, MNQ} — MGC explicitly excluded, SIL absent: post-hoc extension
execution_tier: 0                     # retro-mapped; design specifies limit-at-wick scalping (Tier-2 claim class) — see §1 note
trial_register_increment: 0           # retro card; no new scan run
disposition: arsenal-admit-conditional
---

# Expert Card — H104 v1 (retro of 1.0 H055): wick-rejection mean-reversion scalp with aggressive-sizing sweep, 4-symbol swept basket

Retro Expert Card per ADR-0009 Decision 5 (`P1-2.0-RETRO-CARD-1.0-REGISTER`).
Generated from SKIE-Universe 1.0 evidence only; no new computation was run.
Sources of record (1.0 repo at HEAD `ce018515`, prefix
`research/01_hypothesis_register/H055/`), in precedence order:
`H055_kpi_report_v2.md` (2026-05-18, canonical-substrate re-emission;
supersedes v1), `H055_kpi_report_v1_corrigendum_2026-05-18.md` (binding
correction: annotation `repro-log-present` → **`repro-log-incomplete`**;
numerical claims unaffected), `H055_kpi_report_v1.md` (detail tables not
restated in the v2 delta card), and the closure memo
`INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS.md` (2026-05-19,
`complete-no-further-action`; "MGC memo" below — per-config MGC cell
decomposition on the canonical substrate, sidecar `cd95ebdb...`, plus the
decay-onset and fixed-cell-hindsight-bias assessments bearing directly on
the flagship MGC cell). **All H055 numbers are PRE-COST**
(`cost-zero-v1-pre-cost-research-only`, v2 frontmatter) — the native currency
of the ADR-0002 gross-edge admission standard, with the registration and
integrity caveats below.

> **Registration-conformance note (binding for this card).** The frozen 1.0
> design.md (SHA `ded53acc...`; §1–§7 preserved verbatim through every §17
> amendment) registers: **universe** {ES, NQ, MES, MNQ} with "CL, MCL, MGC,
> MYM ... EXCLUDED at v1" (§2; SIL appears nowhere in the design); **OOS
> window** 2024-01-01 → 2025-12-03 (ES+MES) / 2024-01-01 → 2025-12-19
> (NQ+MNQ) (§2); **H_1** = strict LW2008 studentized stationary-bootstrap CI
> dominance of net Sharpe over three benchmarks (buy-and-hold, TSMOM per
> Moskowitz-Ooi-Pedersen 2012, matched no-skill bootstrap) per
> instrument-class {ES+MES} and {NQ+MNQ}, BH-FDR across the four
> instrument-class siblings (§1). The KPI cards' "H_1" vector
> (MPPM(ρ=1) > 0; Calmar > 0.5; PF > 1.1; R-multiple-mean > 0; payoff-shape
> ≠ skew-negative) is a **post-freeze paradigm substitution** from 1.0
> ADR-0017/0018/0024 (amendments of 2026-05-08+, design §17), not the frozen
> registration. The v2 card's quoted window end "2026-06-30" appears in
> neither the frozen design nor the v1 card (v1 states 2026-05-15) — a
> KPI-card misquote of its own registration, and the MGC memo restates the
> same unregistered window end a third time (its §1 anchor, §6.1 table
> caption, and §6.4 "only 2.5 years" framing) — the misquote propagated
> through the 1.0 evidence chain. Consequences: (i) all MGC and
> SIL evidence below — including the flagship MGC cell — is an
> **unregistered post-hoc extension of the pre-reg universe**; (ii) the
> realized window runs ~5 months past the registered right edge
> (**window extension**); (iii) both extensions are researcher degrees of
> freedom that must enter the trial-register surface at RC-H104-1; (iv) the
> registered universe members MES/MNQ were never swept at all.

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H104 (2.0 reanalysis of 1.0 H055) |
| 1.0 repo git HEAD at read time | `ce018515a667ee63aa2d40234305f8cb677f030b` (2026-07-10; per [config/data_sources.yaml](../../config/data_sources.yaml) `skie_universe_1_kpi_reports` registration) |
| 1.0 source reports | v2 (2026-05-18, commit `a5766fd`, substrate `317429e4...`) + v1 corrigendum + v1 (2026-05-15/16, commit `07d58a4`, substrate `b93e544...`) + MGC memo `INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS.md` (2026-05-19, closed `complete-no-further-action`; v2-sweep sidecar `cd95ebdb...`) |
| design.md SHA-256 | `ded53acc96f5ae9d4691efd5101784519592dee555e6f94a8e25c5313b66ee50` (1.0 `H055/design.md` at HEAD above; frozen 2026-05-06; §1–§7 immutable) |
| ReproLog run_id(s) | `v2_sweep_20260518T220351Z` — **`repro-log-incomplete`**: sweep sidecar carries 3 of 13 ReproLog fields; canonical `logs/reproducibility/{run_id}.json` absent; retrofit was BLOCKING-BEFORE-V3 in 1.0 (`P1-H055-REPROLOG-WIRE`) and remains a 2.0 admission blocker |
| Data span | **Registered** (design §2): OOS 2024-01-01 → 2025-12-03 (ES+MES) / 2025-12-19 (NQ+MNQ). **Realized sweep**: 2024-01-01 → 2026-05-15 (v1 §Table 1, substrate `b93e544`) — post-hoc window extension; v2 re-emission window not restated in the v2 card (gap). Sub-window exhibit: 2026-04-01 → 2026-05-15 |
| Instruments | Swept: ES, NQ, MGC, SIL (5 sizing configs v1/C2/C3/C9/C5). Registered universe: {ES, NQ, MES, MNQ}; **MGC excluded / SIL absent from the frozen design §2** (post-hoc extension); MES/MNQ never swept |
| Execution tier | 0 as simulated (next-bar-open market entries). **Reportability caveat (ADR-0006)**: the design's limit-at-wick-extreme scalp is a Tier-2 claim class; the v1 simulator's next-bar-open simplification "admits more trades" than the limit semantic (v1 §Table 9 caveats) — all numbers are exploration-tier only |
| Shadow-ledger partitions | none — pre-shadow-ledger evidence; backfill pending Phase C (ADR-0003 Decision 5) |
| Trial-register increment | 0 (1.0 sweep reported as M=1 degenerate; the 5-config × 4-symbol selection surface **plus the window- and universe-extension degrees of freedom** are registered as retro trials at RC-H104-1 time) |
| Mechanism citations (from 1.0 design.md §1) | TSMOM trend gate: [Moskowitz, Ooi & Pedersen 2012, JFE 104(2):228–250](https://doi.org/10.1016/j.jfineco.2011.11.003); level memory: [Bouchaud, Gefen, Potters & Wyart 2004, Quant. Finance 4(2):176–190](https://doi.org/10.1080/14697680400000022); realized-vol regime: [Andersen, Bollerslev, Diebold & Labys 2003](https://doi.org/10.1111/1468-0262.00418); fractional Kelly: [MacLean, Thorp & Ziemba 2010](https://doi.org/10.1142/7598); MPPM: [Goetzmann, Ingersoll, Spiegel & Welch 2007, RFS](https://doi.org/10.1093/rfs/hhm025); wick/NR7/squeeze components flagged *practitioner* in design §1 |

## 2. Failure-mode decomposition

Survival-constrained metric vector (post-freeze 1.0 ADR-0017-era paradigm)
carried as reported; the frozen §1 net-Sharpe tri-benchmark dominance test
was never evaluated by either KPI emission (no benchmark arms were run) —
itself an evidence gap. Substrate tags: values marked **[v1/b93e544]** are
from the v1 emission (sibling-worktree substrate `b93e544`); values marked
**[v2/317429e4]** are from the canonical-substrate re-emission.

| Quantity | Value | CI | Method |
|---|---|---|---|
| Gross (pre-cost) edge — MPPM(ρ=1), strongest cells [v2/317429e4] | MGC-C3 **+0.263**; MGC-C5 +0.243; MGC-C2 +0.206; MGC-C9 +0.185; ES-C3 +0.099 — **all MGC cells post-hoc universe extension**; (NQ-C2 +0.175 [v1/b93e544], n=8 trades) | **none — CI primitive never built** (1.0 `P1-H055-MPPM-RHO-1-CI-PRIMITIVE`, still open at v2) | MPPM(ρ=1) point estimates per GISW 2007 |
| Gross basket terminal ROI, realized OOS [v2/317429e4] | C3 **+20.2%**; C2 +18.5%; C9 **+13.9%**; v1-config −0.6%; C5 −9.3% | — | v2 §Basket comparison † |
| Gross per-symbol extremes | MGC-C3 +87.0% [v2 quotes +87% on canonical substrate; per-cell table v1/b93e544]; ES-C3 +23.1%, ES-C5 −53.5%, SIL-C5 −46.6%, NQ-C3 −21.1% [v1/b93e544] | — | realized OOS $10K cells |
| 2026 sub-window basket ROI [v2/317429e4] | C9 **+2.5%**; C2 +4.1%; C3 **−4.4%**; C5 +3.4% | — | 6-week recent sub-window exhibit |
| Survival metrics, best cells [v2/317429e4, MGC memo §6.1 (sidecar `cd95ebdb`); consistent with v1/b93e544 values] | MGC-C9 Calmar **+0.861**, PF 1.040, R-mean +0.011; MGC-C3 Calmar +0.706, PF 1.024 | — | ADR-0017-era vector. Note the substituted vector's own PF > 1.1 component is **not met** on any MGC cell (max 1.040) |
| MGC per-config sub-window ROI (2026-04 → 2026-05) [v2/317429e4, MGC memo §6.1] | C2 **+13.44%**; C5 +8.52%; C9 **+7.61%**; C3 **−4.75%** (full-OOS per-config: C3 +87.04%, C5 +77.19%, C2 +72.37%, C9 +58.04%, v1-config −1.22%) | — | MGC memo §6.1 cell-level decomposition; §7a: "regime-conditional underperformance has started" on C3 |
| Payoff shape [v2/317429e4] | τ_3 ∈ [+0.06, +0.14] all cells → `skew-positive`/`skew-flat`; no skew-negative cell (ATR stop truncates left tail) | — | L-skewness per v2 §L-skewness / ADR-0019 lineage |
| Realized max-DD [v1/b93e544] | MGC-C3 37.3%; MGC-C9 21.4%; SIL-C5 64.5%; ES-C3 41.0% | — | per-cell realized |
| Net (post-cost) edge | **not computed — cost model deliberately zero** (`cost-zero-v1-pre-cost-research-only`); with 7,625–10,321 MGC trades over ~2.4 yr, cost drag is first-order | — | evidence gap; scan RC-H104-2 |
| Frozen §1 H_1 (net-Sharpe tri-benchmark strict dominance, LW2008) | **never evaluated** — no benchmark arms in either emission | — | evidence gap; registered-H_1 status is UNTESTED, not null |
| Fold-stability | single-path walk-forward (`cpcv-not-applied-single-path-wf`, v1 §4); internal probes: basket sign flip on C3 (+20.2% vs −4.4%) [v2/317429e4] + MGC memo §6.1 per-config cell-level sub-window decomposition (row above). **Fixed-cell hindsight-bias caveat** (memo §6.5/§7d): H055 is a single-cell single-config sweep, not per-fold inner-CV; the Phase O.7.5 precedent shows a hindsight fixed-cell result (H062 C3 MGC −94%) failing to survive walk-forward CV (walk-forward cum_mppm +1.67, qualitatively different) — the +87% headline "is qualitatively comparable to a fixed-cell H062 result" until inner-CV lands | — | v2 basket table + MGC memo §6.1/§6.5/§7 |
| Win rates [v1/b93e544] | uniformly < 50% across all cells (36–48%); expectancy from R:R asymmetry ≈ 1.33R | — | v1 §Table 5 |

† **v1↔v2 reconciliation failure (recorded finding).** Checking every
v1-column cell of the v2 comparison table against the v1 card's own Table 1
basket rows yields four exact mismatches plus one approximation: C5 OOS ROI
quoted **−10.0%** vs v1's **−6.6%** ($37,350 on $40,000 basket); C5
sub-window **+3.5%** vs **+3.0%**; C3 sub-window **−4.1%** vs **−4.4%**;
C2 sub-window **+4.0%** vs **+4.1%**; v1-config OOS quoted "~−0.5%" vs
−0.6% (approximation-marked). C2/C3/C9 OOS ROI and C9 sub-window agree.
The v1 card is internally self-consistent; the v2-substrate values
themselves (e.g. C5 −9.3%/+3.4%) are unaffected. Numeric v1↔v2
reconciliation is added to the RC-H104-3 integrity-closure scan.

Classification (exactly one primary; binding numbers stated):
**`conditional-only`** — positive pre-cost edge concentrates in one
instrument cell (MGC: MPPM +0.185…+0.263 and ROI +58…+87% across all four
aggressive-sizing configs [v2/317429e4]) while ES/NQ/SIL are null-to-negative
at basket level under the same signal (v2 verdict: "H_1 PARTIALLY-CONFIRMED
on MGC-only (cell-conditional; not basket-level); H_1 NULL on ES + NQ + SIL"
— a verdict on the **substituted** post-freeze vector, not the frozen §1
H_1, which was never evaluated). The MGC cell is **outside the frozen
design's universe** — its evidentiary status is post-hoc exploration, one
rung below even an uncorrected in-registration cell. The sub-window sign
flip on C3 flags sizing-layer fragility (super-Kelly), not signal-cell
fragility (C9's decay-adaptive sizing keeps the sub-window positive).

## 3. Conditional-edge panel

**No ADR-0002 (b) conditioning set exists**: the 1.0 sweep conditions on
instrument × sizing-config, not on regime covariates; no multiplicity
correction was applied to the 5-config × 4-symbol selection surface (the
best-cell ranking is a post-hoc maximum); and two of the four swept
instruments sit outside the frozen universe. Correction: **none applied —
no scan exists to correct.**

```yaml
conditional_edges:
  # Retro evidence — instrument cells under the C9 (decay-adaptive) and C3 (super-Kelly)
  # sizing configs; PRE-COST; point estimates only (no CI primitive existed);
  # selection-surface uncorrected; MGC/SIL cells are POST-HOC EXTENSIONS of the
  # frozen design §2 universe; NOT admissible as ADR-0002 (c) evidence until RC-H104-1.
  - cell: instrument=MGC, sizing=C3_superkelly   # POST-HOC: MGC excluded by frozen design §2
    gross_edge: 0.263               # MPPM(rho=1) point estimate (v2 §Strongest cells; substrate 317429e4)
    ci_lower: null                  # P1-H055-MPPM-RHO-1-CI-PRIMITIVE never built
    ci_upper: null
    corrected_significant: false
  - cell: instrument=MGC, sizing=C9_bocd_stepup  # POST-HOC: same
    gross_edge: 0.185
    ci_lower: null
    ci_upper: null
    corrected_significant: false
  - cell: instrument=ES, sizing=C3_superkelly    # in-registration instrument; post-hoc window extension applies
    gross_edge: 0.099
    ci_lower: null
    ci_upper: null
    corrected_significant: false
  - cell: instrument=NQ, sizing=C2_fullkelly     # in-registration instrument; n=8 trades (v1 Table 5)
    gross_edge: 0.175               # v1 Table 3 (substrate b93e544; v2 delta card does not restate)
    ci_lower: null
    ci_upper: null
    corrected_significant: false
```

| Conditioning cell | Gross edge (MPPM ρ=1, pt est) | Corrected CI | Significant | Registration status |
|---|---|---|---|---|
| MGC × C3 | +0.263 [v2] | none | not established | **post-hoc universe extension** |
| MGC × C9 | +0.185 [v2] | none | not established | **post-hoc universe extension** |
| ES × C3 | +0.099 [v2] | none | not established | in-registration instrument; window extended |
| NQ × C2 | +0.175 [v1], n=8 trades | none | not established | in-registration instrument; window extended |

**Required follow-up scans**:

- **RC-H104-1 — signal-layer conditional-edge scan**: separate signal from
  sizing per ADR-0005 three-layer separation (the C-config Kelly multipliers
  are position-layer policy, not signal evidence); scan the unsized
  wick-rejection signal pre-cost over the ADR-0002 standard conditioning set
  + instrument, Romano-Wolf corrected. The retro trial surface registered in
  the family MUST include, as researcher degrees of freedom: (i) the 1.0
  5-config × 4-symbol sweep surface; (ii) the **window extension** (realized
  OOS to 2026-05-15, ~5 months past the registered 2025-12-03/19 edge);
  (iii) the **universe extension** (MGC, SIL unregistered). MGC/SIL enter as
  a fresh admission cycle with a new trial-register entry per the ADR-0002
  obligation on post-hoc discoveries.
- **RC-H104-2 — cost application**: bar-level cost model on the MGC cells
  (3,000–10,000 trades) — the cost-share estimate that decides whether the
  MGC edge survives any execution path. 1.0 lineage:
  `P1-H055-COST-EMPIRICAL-CALIBRATION`, which the MGC memo §7a flags as
  **BLOCKING-BEFORE-PAPER-TRADE** ("do not advance MGC C3 ... until [it]
  lands"; the H062 Phase O.16 cost-realism re-ranking showed cost
  subtraction is a load-bearing primitive).
- **RC-H104-3 — integrity closure** (blocking, inherited from 1.0):
  PIT-canary suite (`leakage-canary-deferred` at v2), 13-field ReproLog wire,
  limit-fill-at-wick semantic (removes the known optimistic entry bias),
  MPPM CI primitive, walk-forward inner-CV (1.0 lineage:
  `P1-H055-OPTUNA-INNER-CV-IMPL`, BLOCKING per design §11.2 and per the MGC
  memo §7a fixed-cell-hindsight caveat), **and v1↔v2 numeric reconciliation**
  (the v2 card's v1-column misquotes documented in §2 †).

## 4. Ensemble block

Arsenal snapshot: **0 admitted members at card time** (founding retro
candidate).

```yaml
ensemble:
  marginal_ir_estimate: null            # arsenal empty at card time
  residual_correlation_bound: null      # derivation requires arsenal covariance (ADR-0002 (d))
  correlations: []                      # cross-retro-candidate correlations: follow-up RC-XCORR-1
```

Derivation memo for the correlation bound: none yet — first admission defines
it. Structural note for RC-XCORR-1: H104 is the only retro candidate with
non-equity-index evidence (MGC, SIL — both post-hoc) and the only
mean-reversion signal class — a priori the strongest diversifier candidate
of the five, pending measured residual correlations and resolution of the
registration status of its strongest cells.

## 5. Stability profile

- Rolling-window edge series: **not available as a rolling-origin series** —
  single-path walk-forward. Internal splits: full-OOS vs the 6-week 2026
  sub-window at basket level, **plus the MGC memo §6.1 cell-level per-config
  sub-window decomposition** (MGC sub-window ROI: C2 +13.44%, C5 +8.52%,
  C9 +7.61%, C3 **−4.75%**; sidecar `cd95ebdb`, substrate `317429e4`) — the
  sub-window negativity is specific to the always-on super-Kelly config, not
  uniform across sizing.
- Change-points (CUSUM/BOCPD): not run as inference; the C9 config *uses*
  BOCD internally for sizing decay-adaptation, and its cell-level sub-window
  survival (MGC C9 +7.61% vs C3 −4.75%; memo §6.4: "BOCD effectively
  absorbed the 2026 Q1–Q2 underperformance") is indirect evidence that a
  decay episode occurred within the OOS span and is partially absorbable by
  the position layer.
- Estimated edge half-life: a decay *rate* is still not estimable from the
  available windows, but the **onset is approximately dated** by the MGC
  memo: §7a assesses "regime-conditional underperformance has started" on
  MGC C3 in the 2026-04 → 2026-05 sub-window, and §6.4 reads "the
  2026-onward period appears regime-changed" — decay-onset ≈ 2026-Q2,
  half-life pending rolling evaluation.
- Decayed vs never-worked determination: **worked-then-decay-onset on MGC**
  (strongly positive 2024–2025, memo-dated regime-conditional
  underperformance from ≈2026-Q2, partially absorbable by decay-adaptive
  sizing; post-hoc instrument). Per the v2 verdict, the substituted-vector
  H_1 is null at **basket** level on ES, NQ and SIL; at cell level the
  determination differs by instrument: **ES is INDETERMINATE** — it has one
  positive sized cell (C3: MPPM +0.099 [v2], realized +23.1% [v1/b93e544])
  that is not robust across sizing configs (ES-C2 −1.0%, ES-C9 −0.8%,
  ES-C5 −53.5% [v1/b93e544]); **never-worked is supported for NQ** (its
  single positive-MPPM cell, C2 at +0.175 [v1/b93e544], rests on n=8 trades
  — not evidentially meaningful) **and for SIL** (no material positive
  cell under any config). Rolling evaluation (ADR-0004) on the shadow
  ledger is the determination mechanism.

## 6. Disposition

```yaml
disposition: arsenal-admit-conditional
binding_criterion: "Pre-cost gross edge concentrated in the MGC cell across all four aggressive-sizing configs (MPPM(rho=1) +0.185 to +0.263; realized ROI +58% to +87%) — a POST-HOC extension of the frozen design §2 universe ({ES, NQ, MES, MNQ}; MGC excluded, SIL absent) evaluated on a ~5-month post-hoc window extension; point estimates only, no CI, no multiplicity correction, PIT canary and 13-field ReproLog outstanding; the frozen §1 net-Sharpe tri-benchmark H_1 was never evaluated."
```

Candidate disposition per the ADR-0009 taxonomy — the MGC cell is the
largest pre-cost point-estimate edge in the 1.0 register and ADR-0002
charges no cost at admission. Its basis is explicitly **post-hoc**: outside
the registered universe, past the registered window, selected as the maximum
of an uncorrected 5×4 sweep — under ADR-0002 this requires a *fresh*
admission cycle (RC-H104-1) with the extensions registered as trials, not a
continuation of the 1.0 registration. It is also the least
integrity-complete candidate: admission cannot proceed past (a) until
RC-H104-3 closes (leakage canary deferred, ReproLog incomplete per the v1
corrigendum, known-optimistic entry fill, v1↔v2 misquotes), and (c) requires
RC-H104-1's corrected scan. Two further caveats from the MGC memo bind this
rationale: (i) **fixed-cell hindsight bias** (memo §6.5/§7d) — H055 is a
single-cell sweep, and the Phase O.7.5 precedent (hindsight fixed-cell H062
C3 MGC −94% vs walk-forward cum_mppm +1.67) shows headline fixed-cell
numerics of this class can fail walk-forward CV outright; absent
`P1-H055-OPTUNA-INNER-CV-IMPL` (folded into RC-H104-3) the +87% is a
fixed-cell result, not an inferential one; (ii) **decay onset** (memo §7a)
— MGC C3 sub-window underperformance has already started (−4.75%,
2026-Q2), so the admission scan must be evaluated under the ADR-0004
rolling regime, not on the full-window headline. Falls back to
`archive-no-gross-edge` only if the corrected signal-layer scan finds no
positive pre-cost cell; a cost-dominated-but-real MGC edge would instead
move to `re-specify-cost-bound` after RC-H104-2 (1.0 lineage
`P1-H055-COST-EMPIRICAL-CALIBRATION`, BLOCKING-BEFORE-PAPER-TRADE per memo
§7a).

## 7. Burned-data entry

Recorded 2026-07-10 in [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml)
(commit SHA pending — changes uncommitted for the audit round). Spans are the
**realized** sweep windows (which exceed the registered window; the
registration-conformance note in the header governs their evidentiary
status). MES/MNQ were registered but never swept — no span burned.

| OOS span consumed | Purpose | Mirrored to burned_data_ledger.yaml |
|---|---|---|
| ES 2024-01-01 → 2026-05-15 (5-min intraday) | admission-scan (retro; consumed by 1.0 H055 v1+v2 sweeps) | recorded 2026-07-10 (`hid: H104, instrument: ES`) |
| NQ 2024-01-01 → 2026-05-15 (5-min intraday) | admission-scan (retro; same) | recorded 2026-07-10 (`hid: H104, instrument: NQ`) |
| MGC 2024-01-01 → 2026-05-15 (5-min intraday; post-hoc instrument) | admission-scan (retro; same) | recorded 2026-07-10 (`hid: H104, instrument: MGC`) |
| SIL 2024-01-01 → 2026-05-15 (5-min intraday; post-hoc instrument) | admission-scan (retro; same) | recorded 2026-07-10 (`hid: H104, instrument: SIL`) |

## 8. Priors update

1. MGC (micro gold) hosts the largest pre-cost point edge in the 1.0
   register (+87% cell ROI; MPPM +0.263) **but as an unregistered post-hoc
   universe extension** — the first diversifier-oriented scans should start
   there under a fresh, properly registered admission cycle.
2. Sizing policy and signal must be decomposed before inference (ADR-0005):
   the same signal ranges from +20.2% to −9.3% basket ROI across Kelly
   configs — 1.0's config-coupled evidence overstates signal certainty.
3. Decay-adaptive sizing (BOCD step-up) dominated static super-Kelly on
   survival metrics in the recent window (+2.5% vs −4.4%) — supports
   ADR-0005's registered fractional-Kelly-with-tail-binding as the default
   position layer.
4. ATR-stop truncation produced no skew-negative cell (τ_3 ≥ +0.06
   everywhere) — left-tail-truncated payoff shapes are achievable by
   construction and should be a standing screen (ADR-0019 lineage), not a
   discovery.
5. Integrity and registration debt compound silently: a formal corrigendum
   (ReproLog misannotation), a v2 card misquoting both its own frozen
   registration (window, universe, H_1) and its predecessor's numbers —
   2.0's non-negotiables (ADR-0008) must gate emission, not be retrofitted.
