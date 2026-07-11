---
# Expert Card — machine-readable frontmatter (schema per ADR-0009 §3)
hid: H102                             # 2.0 reanalysis HID; 1.0 source HID = H053
card_version: 1
predecessor_card: null
design_md_sha256: d5bd21d8f511b87cf9d00a121a8615be549ddb345a38f732485d8ccf0e3da67d   # 1.0 H053/design.md at 1.0 HEAD ce018515
repro_log_run_ids: [fe051383e6c146bea93051b816c7e0a1]   # 1.0 ReproLog (Stage-3 v4 canonical run; complete per source card)
data_span: { start: 2024-01-03, end: 2025-12-18 }        # OOS evidence span (ES to 2025-12-03; NQ to 2025-12-18)
instruments: [ES, NQ]
execution_tier: 0                     # retro-mapped: session-window market fills, COST MODEL NOT APPLIED (gross series)
trial_register_increment: 0           # retro card; no new scan run
disposition: re-specify-cost-bound
---

# Expert Card — H102 v1 (retro of 1.0 H053): 09:45→10:30 ET multi-timeframe regression with opening-bar mediator, ES/NQ

Retro Expert Card per ADR-0009 Decision 5 (`P1-2.0-RETRO-CARD-1.0-REGISTER`).
Generated from SKIE-Universe 1.0 evidence only; no new computation was run.
Source of record: `SKIE-Universe@ce018515:
research/01_hypothesis_register/H053/H053_kpi_report_v3.md`
(2026-05-03; supersedes v1/v2, which are preserved history). Distinctive
evidence property: H053 is the only retro candidate whose 1.0 series are
**cost-free (gross)** — "Cost model: NOT applied — these are cost-free upper
bounds" (source §3.1 caveats) — so its numbers speak directly to the
ADR-0002 pre-cost admission currency.

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H102 (2.0 reanalysis of 1.0 H053) |
| 1.0 repo git HEAD at read time | `ce018515a667ee63aa2d40234305f8cb677f030b` (2026-07-10; per [config/data_sources.yaml](../../config/data_sources.yaml) `skie_universe_1_kpi_reports` registration) |
| 1.0 source report | `research/01_hypothesis_register/H053/H053_kpi_report_v3.md`, v3, 2026-05-03, 1.0 commit `0d1fb08` |
| design.md SHA-256 | `d5bd21d8f511b87cf9d00a121a8615be549ddb345a38f732485d8ccf0e3da67d` (1.0 `H053/design.md` at HEAD above) |
| ReproLog run_id(s) | `fe051383e6c146bea93051b816c7e0a1` (`repro-log-complete` per source §Methodological-correctness) |
| Data span | OOS: ES 2024-01-03 → 2025-12-03 (367 sessions); NQ 2024-01-03 → 2025-12-18 (372 sessions) — source §Realized OOS |
| Instruments | ES, NQ (CME; substrate `bc06b4e1...`) |
| Execution tier | 0 (ADR-0006 retro-mapping: session-window fills at bar prices; **no cost model** — reportable as exploration-tier gross only) |
| Shadow-ledger partitions | none — pre-shadow-ledger evidence; backfill pending Phase C (ADR-0003 Decision 5) |
| Trial-register increment | 0 (1.0 SPA family m=2 already registered in 1.0; no new scan) |
| Mechanism citations (from 1.0 design.md §1) | [Lou, Polk & Skouras 2019, JFE 134(1):192–213](https://doi.org/10.1016/j.jfineco.2019.03.011); [Heston, Korajczyk & Sadka 2010, J. Finance 65(4):1369–1407](https://doi.org/10.1111/j.1540-6261.2010.01573.x); [Andersen, Bollerslev, Diebold & Labys 2003, Econometrica 71(2):579–625](https://doi.org/10.1111/1468-0262.00418); mediation: [Imai, Keele & Tingley 2010](https://doi.org/10.1037/a0020761) |

## 2. Failure-mode decomposition

Four model arms (ES/NQ × ElasticNet/LightGBM) vs passive-long; 45-path CPCV.

| Quantity | Value | CI | Method |
|---|---|---|---|
| Gross (pre-cost) edge — CPCV OOS path-median Sharpe vs passive | ES-EN +0.393; ES-LGB +0.634; NQ-EN +1.714; NQ-LGB +0.213 | [q05, q95]: ES-EN [−1.425, +3.931]; ES-LGB [−2.276, +3.258]; NQ-EN [−3.234, +3.606]; NQ-LGB [−3.752, +1.977] — all straddle zero | CPCV n_paths=45 (source §Sharpe-vs-passive) |
| Gross edge — LW2008 differential vs AR(1) bench (annualised) | ES-EN +0.625; ES-LGB +1.953; NQ-EN +1.468; NQ-LGB +1.894 | none exclude zero (e.g. ES-LGB [−0.506, +4.362]) | LW2008 studentised bootstrap (source §Sharpe-vs-bench) |
| Gross terminal wealth, realized OOS ($10K) | ES-EN $9,683 (−3.2%); ES-LGB $10,643 (+6.4%); NQ-EN $10,617 (+6.2%); NQ-LGB **$11,078 (+10.8%)**; passive ES $9,996 / NQ $10,129 | — | source §Realized OOS |
| Gross terminal-wealth q05, forward 252-session bootstrap | NQ-LGB $9,569 (P(loss) 15.7%); ES-LGB $9,636 (18.8%); NQ-EN $9,314 (27.4%); ES-EN $8,990 (67.6%) | q01–q99 per source table | iid bootstrap, PW2004 b=1.0, seed 1042 (source §Forward projection) |
| Realized max-DD | ES-EN 10.2%; ES-LGB 4.5%; NQ-EN 5.6%; NQ-LGB 3.7% | — | source §Realized OOS |
| Net (post-cost) edge | **never computed** — cost-aware re-run tracked as 1.0 `P1-H053-COST-EMPIRICAL`, never executed | — | evidence gap; scan RC-H102-1 |
| Cost share of gross (derived, order-of-magnitude) | projected cost drag "$1,000–$2,000 over 252 sessions on a $10k account" (source §3.1 caveat) = 10–20%/yr vs best-arm realized gross ≈ 5.3%/yr (NQ-LGB +10.8% over ~2 yr) → **cost prior exceeds gross on every arm (share > 100%)** | — | **derived here** from the two cited source figures; not a 1.0-reported statistic |
| Fold-stability (CPCV path dispersion) | path-Sharpe q05 negative on all 4 arms; KS-monotonicity `not-converged` on all arms; DSR ∈ [−3.81, −3.29] when active | — | source §Sharpe-vs-passive + §Other KPIs |
| Calibration | BSS flat-to-negative (−0.010 … −0.145); reliability out-of-band on all 4 arms | — | source §Other KPIs — the pre-registered categorical-table deliverable failed its calibration gate |

Classification (exactly one primary; binding numbers stated):
**`cost-bound`** — gross edge is point-positive on all four model arms
(realized +6.2% to +10.8% on three of four; CPCV medians all positive) but
the 1.0 report's own cost prior (10–20%/yr on a $10k account) exceeds the
best arm's ≈5.3%/yr realized gross, so the expert as specified cannot survive
its own cost model. Secondary classification `fold-unstable` is close behind
and is recorded: CPCV q05 < 0 on every arm, KS not converged, DSR ∈ [−3.81,
−3.29] — the gross point estimates carry heavy selection-dispersion risk.

## 3. Conditional-edge panel

**No ADR-0002 (b) conditioning set exists** in the 1.0 design; the nearest
1.0 objects are (i) the model-arm × instrument cells reported above and
(ii) the pre-registered categorical archetype-bias table, which failed its
calibration gate (BSS ≤ 0, reliability out-of-band on all arms) and so
provides no usable cell evidence. Correction: **none applied — no scan exists
to correct.** (The 1.0 SPA family m=2 p-values 0.367/0.290, source §Other
KPIs, are family-level, not per-cell.)

```yaml
conditional_edges:
  # Retro evidence — model-arm × instrument cells; GROSS (cost-free) per source;
  # CPCV path-quantile intervals are dispersion bands, not corrected CIs;
  # NOT admissible as ADR-0002 (c) evidence until scan RC-H102-2 runs.
  - cell: instrument=NQ, arm=LightGBM
    gross_edge: 1.021               # realized-path annualised Sharpe (source §Realized OOS, dagger note)
    ci_lower: null                  # corrected CI: none — uncorrected CPCV band [-3.752, +1.977] on path median
    ci_upper: null
    corrected_significant: false
  - cell: instrument=ES, arm=LightGBM
    gross_edge: 0.874               # realized-path annualised Sharpe (source §Realized OOS)
    ci_lower: null
    ci_upper: null
    corrected_significant: false
  - cell: instrument=NQ, arm=ElasticNet
    gross_edge: 0.596
    ci_lower: null
    ci_upper: null
    corrected_significant: false
  - cell: instrument=ES, arm=ElasticNet
    gross_edge: -0.452
    ci_lower: null
    ci_upper: null
    corrected_significant: false
```

| Conditioning cell | Gross edge (realized-path ann. Sharpe) | Corrected CI | Significant |
|---|---|---|---|
| NQ × LightGBM | +1.021 | none — uncorrected | not established |
| ES × LightGBM | +0.874 | none — uncorrected | not established |
| NQ × ElasticNet | +0.596 | none — uncorrected | not established |
| ES × ElasticNet | −0.452 | none — uncorrected | not established |

**Required follow-up scans**:

- **RC-H102-1 — cost decomposition**: apply the bar-level cost model
  (per-session log-return drag per 1.0 F-CONV-2 rule) to the Stage-3 v4 OOS
  series and re-emit net terminal-wealth/Calmar/profit-factor; confirms or
  refutes the cost-bound classification quantitatively.
- **RC-H102-2 — conditional-edge scan**: pre-cost per-session strategy
  returns over the ADR-0002 project-standard conditioning set, Romano-Wolf
  corrected; the LGB arms are the pre-registered primary cells.

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
it. Overlap to resolve at RC-XCORR-1: H053's 09:45–10:30 ET window sits
inside the H052a/H054 first-hour-ORB session and shares the ES/NQ substrate;
H054's data_requirements acknowledged partial OOS overlap with H053
(`H054_kpi_report_v1.md`, `data-overlap-h053-acknowledged`).

## 5. Stability profile

- Rolling-window edge series: **not available as a time-ordered series** —
  1.0 used CPCV over the OOS region (45 combinatorial paths), which yields a
  dispersion distribution, not a rolling-origin trajectory.
- Change-points (CUSUM/BOCPD): **never run** — gap; folds into RC-H102-2.
- Estimated edge half-life: n/a — no time-ordered edge series exists to fit
  decay on.
- Decayed vs never-worked determination: **indeterminate**; the CPCV path
  dispersion (q05 < 0 on all arms, KS not converged) means the 1.0 record
  cannot distinguish a weak persistent edge from path-lucky noise, let alone
  date a decay. The mechanism literature window (Lou-Polk-Skouras intraday
  cross-section) is documented through the mid-2010s; recency confirmation is
  exactly what the rolling regime adds.

## 6. Disposition

```yaml
disposition: re-specify-cost-bound
binding_criterion: "Best-arm realized gross ≈ +10.8% over ~2 years (≈5.3%/yr, NQ-LightGBM) vs the source card's own projected cost drag of $1,000–$2,000 per 252 sessions on $10k (10–20%/yr): cost prior exceeds gross on every arm; gross point estimates positive but CPCV q05 < 0 and DSR ∈ [−3.81, −3.29] on all arms."
```

The binding criterion is cost dominance over a positive but statistically
fragile gross edge. Under ADR-0002 this is expressly **not** an archive
outcome (cost is a position/execution-layer property; "cost-bound-but-
informative experts a cheaper execution path could rescue" — ADR-0002
Alternatives). Re-specification paths, in registered order: (i) RC-H102-1
cost decomposition on micro contracts / lower-cost execution to quantify the
actual net; (ii) RC-H102-2 conditional-edge scan — a corrected-significant
positive pre-cost cell flips the disposition to `arsenal-admit-conditional`;
(iii) if RC-H102-2 finds no positive pre-cost cell, disposition falls to
`archive-no-gross-edge`. The failed calibration gate (BSS ≤ 0 on all arms)
independently blocks any probability-forecast use of this expert; only the
directional-signal form is a candidate.

## 7. Burned-data entry

| OOS span consumed | Purpose | Mirrored to burned_data_ledger.yaml |
|---|---|---|
| ES 2024-01-03 → 2025-12-03 (session cadence, 09:45–10:30 ET window) | admission-scan (retro; consumed by 1.0 H053 Stage-3 v4 CPCV) | recorded 2026-07-10 in [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml) (`hid: H102, instrument: ES`; commit SHA pending — working tree uncommitted for audit round) |
| NQ 2024-01-03 → 2025-12-18 (session cadence, same window) | admission-scan (retro; same run) | recorded 2026-07-10, same ledger (`hid: H102, instrument: NQ`) |

## 8. Priors update

1. Cost dominance, not signal absence, is the binding failure of the 1.0
   intraday-window regression class — queued low-edge/high-frequency designs
   must clear a cost-vs-gross feasibility check at design time.
2. CPCV path dispersion with all-positive medians and all-negative q05 is the
   canonical fold-unstable signature — allocator-level evaluation (ADR-0001)
   is the correct consumer of such experts, not standalone gates.
3. Isotonic/Platt-calibrated probability outputs failed uniformly (BSS ≤ 0,
   reliability out-of-band) — queued hypotheses should not promise calibrated
   probabilities from 45-minute-window returns at this sample size.
4. LightGBM arms dominated ElasticNet on 3 of 4 gross cells but carry
   bridge-mediated deployment cost — expert-interface design should keep the
   pure-C#-implementable linear arm as the cheap sibling.
5. DSR ∈ [−3.81, −3.29] across cells quantifies the selection-inflation
   burden of a 2-model × 2-symbol × CPCV search — the 2.0 trial register
   (ADR-0008) must carry these retro trials when the admission scan runs.
