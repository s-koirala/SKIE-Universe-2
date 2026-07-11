---
# Expert Card — machine-readable frontmatter (schema per ADR-0009 §3)
hid: H103                             # 2.0 reanalysis HID; 1.0 source HID = H054
card_version: 1
predecessor_card: null
design_md_sha256: 33bc88b23c755b3c0730d147a6ed9a94abed22ac6691005685a84ca7596ae0a9   # 1.0 H054/design.md at 1.0 HEAD ce018515
repro_log_run_ids: [dd916fc67b504c528fda7abbde6700f1]   # 1.0 ReproLog (13-field complete per source card)
data_span: { start: 2025-01-01, end: 2025-12-03 }        # OOS evidence span (ES-only fresh 2025 fold)
instruments: [ES]
execution_tier: 0                     # retro-mapped: session-cadence market fills + futures_orb_v1 cost model (ADR-0006)
trial_register_increment: 0           # retro card; no new scan run
disposition: arsenal-admit-conditional
---

# Expert Card — H103 v1 (retro of 1.0 H054): anti-gate (stress-state-only) first-hour ORB, ES session cadence

Retro Expert Card per ADR-0009 Decision 5 (`P1-2.0-RETRO-CARD-1.0-REGISTER`).
Generated from SKIE-Universe 1.0 evidence only; no new computation was run.
Source of record: `SKIE-Universe@ce018515:
research/01_hypothesis_register/H054/H054_kpi_report_v1.md`
(2026-05-05). H054 is the inverse-gate companion of H052a: it trades the
first-hour ORB **only** on sessions the HMM classifies into the stress state
(highest realized-vol emission mean) — i.e. it is, in 2.0 vocabulary, a
direct probe of conditional edge in a realized-vol-regime cell. All source
numbers are **net-of-cost** (`futures_orb_v1`, $29.10 ES r/t); net values are
used as lower bounds on gross where needed.

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H103 (2.0 reanalysis of 1.0 H054) |
| 1.0 repo git HEAD at read time | `ce018515a667ee63aa2d40234305f8cb677f030b` (2026-07-10; per [config/data_sources.yaml](../../config/data_sources.yaml) `skie_universe_1_kpi_reports` registration) |
| 1.0 source report | `research/01_hypothesis_register/H054/H054_kpi_report_v1.md`, v1, 2026-05-05, 1.0 commit `66dab5d` |
| design.md SHA-256 | `33bc88b23c755b3c0730d147a6ed9a94abed22ac6691005685a84ca7596ae0a9` (1.0 `H054/design.md` at HEAD above) |
| ReproLog run_id(s) | `dd916fc67b504c528fda7abbde6700f1` (`repro-log-complete` per source §Methodological-correctness) |
| Data span | Train 2020-01-01 → 2022-12-31, val 2023-H1; OOS ES 2025-01-01 → 2025-12-03 (237 sessions; H052a's 2023-07→2024-12 OOS deliberately untouched per source §Cross-validation) |
| Instruments | ES only at v1 (CME; substrate `b3ee230a...` + VIX daily) |
| Execution tier | 0 (ADR-0006 retro-mapping: 1 market round-trip per active session at bar prices; 1-tick slippage prior) |
| Shadow-ledger partitions | none — pre-shadow-ledger evidence; backfill pending Phase C (ADR-0003 Decision 5) |
| Trial-register increment | 0 (1.0 family M=1; cross-hypothesis family construction was deferred in 1.0) |
| Mechanism citations (from 1.0 design.md §1) | Regime-switching: [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196). Stress-period return structure (Phase-0-flagged as intraday-silent): [Bollerslev, Tauchen & Zhou 2009, RFS 22(11):4463–4492](https://doi.org/10.1093/rfs/hhp008); [Cochrane 2011, J. Finance 66(4):1047–1108](https://doi.org/10.1111/j.1540-6261.2011.01671.x); Hurst-Ooi-Pedersen 2017 (JPM 44(1):15–29; stress-period TSMOM, directionally consistent, different signal class). Empirical motivation (load-bearing per source): H052a KPI report v1 |

## 2. Failure-mode decomposition

| Quantity | Value | CI | Method |
|---|---|---|---|
| Gross (pre-cost) edge | not separately emitted; **net values below are lower bounds on gross** | — | cost applied per-session (source §caveats) |
| Net edge, anti-gated arm T_H054_b (per-session Sharpe, PRIMARY) | **+0.0362** (annualised **+0.573**) | Opdyke 2007 95% CI **[−0.0327, +0.1050]** — covers zero | Opdyke 2007 higher-moment asymptotic with HAC adjustment (source §3) |
| Net edge, differential T_H054_a = anti − uncond (per-session, secondary) | +0.0398 (annualised +0.630) | LW2008 [−0.0411, +0.1394] — covers zero | LW2008 studentised bootstrap (source §3.1) |
| Net terminal wealth, realized OOS ($10K) | anti **$10,349.81 (+3.50%)**; uncond $9,946.31 (−0.54%) | — | source §1 |
| Net terminal-wealth q05, forward 252-session bootstrap | anti **$9,402.22** (P(loss) 29.24%); uncond $8,481.31 (P(loss) 52.50%) | q01–q99 per source §6 | iid bootstrap (PW2004 b=1.0); anti-arm empirical distribution built from **7 trades** (source §caveats) |
| Realized max-DD | anti **3.19%**; uncond 6.99% | — | source §2 |
| Cost share of gross (derived; **basis-indeterminate on the 1.0 record**) | anti arm ≈ **2%** (notional basis, formula-consistent: drag \|log(1 − 29.10/240,000)\| ≈ 1.21e-4 per active session vs mean net ln(1.035)/7 ≈ 4.91e-3) to ≈ **37%** (account-dollar basis: 7 × $29.10 = $203.70 vs net +$349.81 → gross ≈ $553.51) | — | **derived here**, basis-labeled (Round-1 stated the 37% without its account-dollar basis label); the shared `futures_orb_v1` cost quote in the H052a source card is internally inconsistent (see H101 card §2), so basis reconciliation defers to RC-H103-1 |
| Fold-stability | not computable: single outer fold; deeper constraint is **n_anti = 7 trades / 237 sessions (2.95% fire rate)** vs design.md §9.2 required n ≥ 174 → `power-margin-low` (structural, pre-declared in design §9.5) | — | source §5 + §8 |
| Hansen SPA (M=1 degenerate) | T_SPA 0.670, p = 0.285 — non-trivial (d̄ > 0), fails α=0.05 | — | source §7 |

Classification (exactly one primary; binding numbers stated):
**`conditional-only`** — the expert *is* a conditioning cell: positive
net point estimates on every reported metric within the stress-state cell
(annualised +0.573 vs unconditional −0.057; terminal wealth +3.50% vs
−0.54%; forward P(loss) 29.24% vs 52.50%; max-DD 3.19% vs 6.99%), with a
structurally wide CI ([−0.0327, +0.1050]) driven by the 7-trade sample. Per
the pre-registered expectation note (design §9.5, quoted in source §3):
"consistent-with-noise-given-low-trade-count, NOT anti-gate hypothesis
falsified."

## 3. Conditional-edge panel

The stress-state gate is the 1.0 analogue of an ADR-0002 realized-vol-
percentile cell, but the 2.0 conditioning set was **not frozen in the 1.0
design and no per-cell scan with multiplicity correction ran** (family M=1).
Correction: **none applied — no scan exists to correct.**

```yaml
conditional_edges:
  # Retro evidence — single 1.0-defined regime cell; NET of cost (lower bound on gross);
  # single-cell family (uncorrected); NOT admissible as ADR-0002 (c) evidence
  # until scan RC-H103-1 reaches the design-required n and applies RW correction.
  - cell: hmm_stress_state=2 (highest realized-vol emission), instrument=ES   # state index 2 per source §8 "HMM stress_state | 2"
    gross_edge: 0.0362              # per-session net Sharpe, lower bound on gross (source §3)
    ci_lower: -0.0327               # Opdyke 2007 95% CI, UNCORRECTED single-cell
    ci_upper: 0.1050
    corrected_significant: false
  - cell: complement (non-stress sessions), instrument=ES
    gross_edge: null                # arm is flat by construction on these sessions; uncond arm net Sharpe -0.0036 (source §3.1)
    ci_lower: null
    ci_upper: null
    corrected_significant: false
```

| Conditioning cell | Gross edge | Corrected CI | Significant |
|---|---|---|---|
| stress-state sessions (ES) | ≥ +0.0362/session net Sharpe (7 trades) | none — uncorrected single cell | not established (CI covers zero) |
| non-stress sessions (ES) | not traded (flat); uncond whole-sample net −0.0036 | — | — |

**Required follow-up scan RC-H103-1** (admission scan; increments trial
register): pooled multi-instrument (ES + NQ + MES + MNQ per source §Operator
options) pre-cost ORB returns on the 2.0 shadow ledger, conditioned on the
ADR-0002 project-standard set with realized-vol percentile as the
pre-registered primary covariate (replacing the learned HMM state per
ADR-0001 Decision 5), Romano-Wolf corrected, accumulated until the
stress-cell trade count reaches the design-derived n ≥ 174. Note the 2025
fire rate (2.95%) came in far below the design estimate (10%) — the scan must
also test whether the vol-percentile cell definition, not the HMM, controls
that gap.

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
it. Structural notes for RC-XCORR-1: (i) H103 trades the complement of the
session set an H101 (H052a-descendant) expert would favor — a candidate
**diversifier pairing** whose joint behavior must be measured, not assumed;
(ii) H054's secondary statistic is algebraically dependent on H052a (source
§3.1); (iii) acknowledged partial OOS overlap with H053
(`data-overlap-h053-acknowledged`, source annotations).

## 5. Stability profile

- Rolling-window edge series: **not available** — single outer fold, 7
  active trades; no meaningful rolling series can exist at this n.
- Change-points (CUSUM/BOCPD): **never run**; n=7 makes change-point
  inference vacuous — remedied only by RC-H103-1 accumulation.
- Estimated edge half-life: n/a — no decay measurement possible.
- Decayed vs never-worked determination: **indeterminate at n=7**; the
  directional finding (positive stress-cell point estimates on fresh 2025
  OOS, consistent with the H052a-implied stress-subset reading on 2023–2024
  data) is two-window-consistent, which weakly favors "works, underpowered"
  over "never-worked" — but the 1.0 record cannot support more than that
  sentence.

## 6. Disposition

```yaml
disposition: arsenal-admit-conditional
binding_criterion: "Positive net (hence gross lower-bound) point estimates across every reported metric inside the pre-declared stress-state cell (annualised Sharpe +0.573; terminal wealth +3.50%; forward P(loss) 29.24% vs 52.50% unconditional) at n_anti = 7 trades — below the design-derived n ≥ 174 for 80% power, so cell significance is structurally unestablishable from the 1.0 record."
```

Candidate disposition per the ADR-0009 taxonomy; this is the cleanest
ADR-0002-shaped object in the 1.0 register — a conditional-edge claim in a
(proto-)pre-declared regime cell with no standalone-profitability pretension.
Admission becomes effective only when (a) the PIT-clean 2.0 interface port +
leakage-canary suite pass (1.0 ran 17/17 PIT tests — supporting but not the
2.0 suite), (b)+(c) RC-H103-1 reaches the required n and the stress cell
survives Romano-Wolf correction, (d) RC-XCORR-1 clears the H101 pairing.
Falls back to `archive-no-gross-edge` only if the accumulated pre-cost
stress-cell edge is non-positive at adequate power.

## 7. Burned-data entry

| OOS span consumed | Purpose | Mirrored to burned_data_ledger.yaml |
|---|---|---|
| ES 2025-01-01 → 2025-12-03 (session cadence) | admission-scan (retro; consumed by 1.0 H054 walk-forward) | recorded 2026-07-10 in [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml) (`hid: H103, instrument: ES`; commit SHA pending — working tree uncommitted for audit round) |

## 8. Priors update

1. The stress/high-vol regime cell is the single most promising conditional-
   edge locus in the 1.0 register (positive on every metric, two-window
   consistent) — it is the pre-registered primary covariate for the first
   2.0 admission scans (H101, H103).
2. Regime-cell fire rates estimated in-sample transfer poorly (design 10% vs
   realized 2.95%) — queued conditional designs must power on the
   *pessimistic* fire-rate bound, not the point estimate.
3. Rule-based covariate cells (realized-vol percentile) must replace learned
   HMM states in 2.0 scans (ADR-0001 Decision 5); H054's evidence is
   agnostic between the two — the scan should measure the delta.
4. Low-fire-rate conditional experts are cheap to shadow (7 trades/yr) but
   slow to power — the shadow ledger (ADR-0003) is the only affordable
   accumulation path; live/paper accumulation would take decades.
5. Derived cost share on the 7-trade anti arm spans ≈2% (notional basis) to
   ≈37% (account-dollar basis) — basis-indeterminate on the 1.0 record but
   potentially material for sparse-fire experts at retail account scale;
   position-layer sizing (ADR-0005) plus RC-H103-1 basis reconciliation, not
   signal redesign, are the correct levers.
