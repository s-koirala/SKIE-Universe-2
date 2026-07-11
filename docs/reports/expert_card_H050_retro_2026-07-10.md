---
# Expert Card — machine-readable frontmatter (schema per ADR-0009 §3)
hid: H100                             # 2.0 reanalysis HID (Reanalysis block); 1.0 source HID = H050
card_version: 1
predecessor_card: null
design_md_sha256: 3d715b6d7ca4fcb43d25a4a3d91e134533a3b7b43000a0dce988fa96748e4b62   # 1.0 H050/design.md at 1.0 HEAD ce018515
repro_log_run_ids: [31d23ecd8e3842dd8ebd5687ce9c91d5]   # 1.0 ReproLog (13-field complete per source card)
data_span: { start: 2024-01-01, end: 2025-12-11 }        # OOS evidence span (ES to 2024-12-12; NQ to 2025-12-11)
instruments: [ES, NQ]
execution_tier: 0                     # retro-mapped: bar-close fills + bar-level cost model (ADR-0006)
trial_register_increment: 0           # retro card; no new scan run
disposition: re-specify-cost-bound
---

# Expert Card — H100 v1 (retro of 1.0 H050): HMM regime-gated LightGBM intraday directional signal, ES/NQ 1-min

Retro Expert Card per ADR-0009 Decision 5 (`P1-2.0-RETRO-CARD-1.0-REGISTER`).
Generated from SKIE-Universe 1.0 evidence only; no new computation was run.
Source of record: `SKIE-Universe@ce018515:
research/01_hypothesis_register/H050/H050_kpi_report_v1.md` (2026-05-04),
supplemented by the closure memo `SKIE-Universe@ce018515:
research/01_hypothesis_register/H050/INVESTIGATE-FAILURE-MODE-H050-HMM-GATING-HARM.md`
("INVESTIGATE memo" below). Every number below cites its 1.0 source section;
where the 1.0 record cannot populate a section, the gap is stated with the
concrete follow-up scan required — no value is invented.

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H100 (2.0 reanalysis of 1.0 H050) |
| 1.0 repo git HEAD at read time | `ce018515a667ee63aa2d40234305f8cb677f030b` (2026-07-10; per [config/data_sources.yaml](../../config/data_sources.yaml) `skie_universe_1_kpi_reports` registration) |
| 1.0 source report | `research/01_hypothesis_register/H050/H050_kpi_report_v1.md`, v1, 2026-05-04, 1.0 commit `d8c6acd` |
| design.md SHA-256 | `3d715b6d7ca4fcb43d25a4a3d91e134533a3b7b43000a0dce988fa96748e4b62` (1.0 `H050/design.md` at HEAD above) |
| ReproLog run_id(s) | `31d23ecd8e3842dd8ebd5687ce9c91d5` (1.0 `logs/reproducibility/`; annotation `repro-log-complete` per source §Methodological-correctness) |
| Data span | OOS: ES 2024-01-01 → 2024-12-12 (337,837 bars, ~866 RTH sessions, 1/2 folds); NQ 2024-01-01 → 2025-12-11 (673,274 bars, ~1,726 sessions, 2/3 folds) — source §Realized OOS |
| Instruments | ES, NQ (CME, 1-min RTH substrate `b3ee230a...`, 2015–2025) |
| Execution tier | 0 (ADR-0006 retro-mapping: bar-close fills, `nt8_es_nq_rth_v1` constant-tick cost prior applied as per-bar log-return drag; source §Realized OOS caveats) |
| Shadow-ledger partitions | none — pre-shadow-ledger evidence; backfill pending Phase C (ADR-0003 Decision 5) |
| Trial-register increment | 0 (no new scan; 1.0 family M=1 per source §7) |
| Mechanism citations (from 1.0 design.md §1) | [Hamilton 1989](https://doi.org/10.2307/1912559); [Baum et al. 1970](https://doi.org/10.1214/aoms/1177697196); [Guidolin & Timmermann 2007, JEDC 31(11):3503–3544](https://doi.org/10.1016/j.jedc.2006.12.004); [Ryou, Bae, Lee & Oh 2020, Sustainability 12(17):7031](https://doi.org/10.3390/su12177031); [Andersen & Bollerslev 1998](https://doi.org/10.2307/2527343) |

## 2. Failure-mode decomposition

All 1.0 H050 series are **net-of-cost by design** (design.md §1 line 30; cost
subtracted at bar level before `oos_returns.parquet` — source §Realized OOS
caveats, F-Q-1 fix). A pre-cost (gross) decomposition was **never emitted**;
this is the card's controlling evidence gap.

| Quantity | Value | CI | Method |
|---|---|---|---|
| Gross (pre-cost) edge | **not available** — 1.0 emitted net-of-cost series only | — | evidence gap; scan RC-H100-1 below |
| Net edge, gated−unconditional differential (per-bar Sharpe) | ES **−0.03714**; NQ **−0.02185** | ES [−0.04052, −0.03390]; NQ [−0.02455, −0.01903] — both exclude zero (negative) | LW2008 studentised stationary bootstrap (source §3) |
| Net edge, arm level (annualised Sharpe) | gated ES −14.28 / NQ −7.25; unconditional ES −2.63 / NQ −0.39 | not reported at arm level | source §4 |
| Net terminal wealth, realized OOS ($10K) | gated ES $1,898.23 (−81.02%), NQ $1,580.46 (−84.20%); uncond ES $5,630.64 (−43.69%), NQ $7,440.31 (−25.60%) | — | source §1 |
| Net terminal-wealth q05, forward 252-session bootstrap | gated ES $5,838.93 / NQ $7,181.29; uncond ES $7,646.47 / NQ $8,003.69; P(loss) 100% / 100% / 99.6% / 64.9% | q01–q99 per source §6 | iid bootstrap (PW2004 b=1.0); **understates tail risk** per source F-Q-3 caveat (regime dwell-time persistence destroyed) |
| Realized max-DD | gated ES 81.12% / NQ 84.36%; uncond ES 45.02% / NQ 35.05% | — | source §2 |
| Gate flip counts + transition rate | ES 102,472 transitions / 337,837 bars (**30.33%**, median active run 3 bars); NQ 79,237 / 673,274 (**11.77%**, median active run 7 bars) | — | INVESTIGATE memo §6.3 |
| Cost-drag attribution (net-based) | mean cost-drag per bar ES **−3.171e−6** = **1.87×** \|full-path uncond mean −1.700e−6\|; NQ **−2.485e−6** = **5.66×** \|−4.392e−7\| — "cost drag from whipsaw alone fully explains the gated-arm catastrophe" | — | INVESTIGATE memo §6.4 (`gated_return − unconditional_return × regime_indicator`); computed on net-of-cost series — NOT a pre-cost decomposition (see RC-H100-1) |
| Per-state selection deltas (net-based) | ES uncond-in-gate-state SR_ann −4.601 vs uncond-in-non-gate-state **+0.193**; NQ −0.523 vs −0.393 — gate state has WORSE per-bar Sharpe than the discarded state on both symbols | — | INVESTIGATE memo §6.1 |
| Cost share of gross | not derivable in ADR-0002 currency — the memo's §6.4 attribution is net-based; the **pre-cost (gross) series was never emitted** | — | `nt8_es_nq_rth_v1` v1 prior; gap → scan RC-H100-1 |
| Fold-stability | not computable: realized n_folds 1 (ES) and 2 (NQ) vs expected 2/3; `power-margin-low` | — | source §8 |

Classification (exactly one primary; binding numbers stated):
**`cost-bound`** — binding numbers: net differential CI excludes zero on the
negative side on both symbols (ES −0.03714 [−0.04052, −0.03390]); gate
transition rate **ES 30.33% / NQ 11.77% of bars** (INVESTIGATE memo §6.3);
and the memo's §6.4 attribution shows whipsaw cost-drag per bar exceeding
the entire unconditional signal magnitude (ES 1.87×, NQ 5.66× — "cost drag
from whipsaw alone fully explains the gated-arm catastrophe"; memo §6.6
verdict: H-c whipsaw STRONGLY SUPPORTED / PRIMARY). Secondary mode recorded
per memo §6.6: H-b anti-selection PARTIALLY SUPPORTED — the gate state has
worse per-bar Sharpe than the discarded state on both symbols (memo §6.1),
so even a zero-cost gate would have filtered in the wrong direction.
**Why this does not close RC-H100-1**: the memo's attribution is arithmetic
on the two *net-of-cost* arm series (cost-drag = gated − uncond × indicator
isolates the flip-cost differential between net arms); the ADR-0002 currency
— pre-cost per-cell edge of the underlying signal — was never emitted, so
the memo upgrades classification confidence but cannot substitute for the
pre-cost conditional-edge scan. Empirical confirmation of the memo's
prediction also awaits the paired variants H050.invert / H050.stable-state,
whose v1 emissions are smoke/placeholder with **no numeric results**
(`H050_invert_kpi_report_v1.md`, `H050_stable_state_kpi_report_v1.md`).

## 3. Conditional-edge panel

**No ADR-0002 (b) conditioning set exists**: the 1.0 design.md froze no regime
covariates for conditional-edge scanning, and no per-cell scan was ever run.
The only conditioning object in the 1.0 record is the HMM state itself — a
learned, single-feature (log-return emission) latent state, which ADR-0001
Decision 5 prohibits as a gate and which the 1.0 mechanism note (source
§Operator interpretation) assesses as backward-looking with no forward
predictive content. Correction: **none applied — no scan exists to correct.**

```yaml
conditional_edges:
  # Retro placeholder — no pre-registered conditioning cells were scanned in 1.0.
  # The only cell-like split available is HMM-state membership (INVESTIGATE memo §6.1
  # per-state stats on the unconditional signal): NET of cost, uncorrected, and NOT
  # admissible as ADR-0002 (c) evidence. gross_edge stays null — pre-cost never emitted.
  - cell: hmm_state=gate (high-mean/low-vol) (ES)   # net SR_ann -4.601 on uncond signal (memo §6.1)
    gross_edge: null                                # pre-cost never emitted
    ci_lower: null
    ci_upper: null
    corrected_significant: false
  - cell: hmm_state=non-gate (low-mean/high-vol) (ES)   # net SR_ann +0.193 on uncond signal (memo §6.1)
    gross_edge: null
    ci_lower: null
    ci_upper: null
    corrected_significant: false
  - cell: hmm_state=gate (NQ)                       # net SR_ann -0.523 (memo §6.1)
    gross_edge: null
    ci_lower: null
    ci_upper: null
    corrected_significant: false
  - cell: hmm_state=non-gate (NQ)                   # net SR_ann -0.393 (memo §6.1)
    gross_edge: null
    ci_lower: null
    ci_upper: null
    corrected_significant: false
```

| Conditioning cell | Gross edge | Net evidence (memo §6.1, uncorrected) | Corrected CI | Significant |
|---|---|---|---|---|
| ES gate state (uncond signal) | gap | SR_ann −4.601 | — | — |
| ES non-gate state (uncond signal) | gap | SR_ann **+0.193** (only net-positive state cell) | — | — |
| NQ gate state (uncond signal) | gap | SR_ann −0.523 | — | — |
| NQ non-gate state (uncond signal) | gap | SR_ann −0.393 | — | — |

**Required follow-up scans** (become 2.0 admission-scan prompts; each
increments the trial register per ADR-0008):

- **RC-H100-1 — pre-cost decomposition**: recompute gross (pre-cost) per-bar
  return series for both arms from 1.0 artifacts
  (`artifacts/runs/H050/31d23ecd.../{ES,NQ}/oos_returns.parquet` + cost model
  inversion, or re-run on the 2.0 shadow ledger), decomposing the gated−unconditional
  differential into selection (gross) vs cost-drag components. Still required
  despite the INVESTIGATE memo §6.4 attribution: the memo's decomposition is
  net-based and quantifies flip-cost between the two net arms; it does not
  yield the pre-cost per-cell edge ADR-0002 (c) needs.
- **RC-H100-2 — variant completion**: production runs of H050.invert (H-b)
  and H050.stable-state N ∈ {3,5,10,20} (H-c) per the 1.0 pre-registered
  designs; their KPI cards are currently numeric-empty.
- **RC-H100-3 — conditional-edge scan of the underlying unconditional LightGBM
  signal** over the ADR-0002 project-standard conditioning set (time-of-day,
  realized-vol percentile, variance-ratio state, macro-calendar proximity,
  spread/liquidity regime), Romano-Wolf corrected. The unconditional arm's
  near-noise net Sharpe (ES −2.63, NQ −0.39 annualised) does not preclude
  positive pre-cost cells.

## 4. Ensemble block

Arsenal snapshot: **0 admitted members at card time** (this is one of the five
founding retro candidates; no admission has occurred). Marginal-IR vs the
spanned arsenal and residual-correlation bounds are therefore **not defined**;
the ADR-0002 (d) bound derivation requires a non-empty arsenal covariance
estimate.

```yaml
ensemble:
  marginal_ir_estimate: null            # arsenal empty at card time
  residual_correlation_bound: null      # derivation requires arsenal covariance (ADR-0002 (d))
  correlations: []                      # cross-retro-candidate correlations: follow-up RC-XCORR-1
```

Derivation memo for the correlation bound: none yet — first admission defines
it. **Follow-up RC-XCORR-1**: compute pairwise net-of-cost residual
correlations among the five retro candidates from 1.0 OOS return artifacts
(H050/H052a/H054 share the ES substrate and the HMM stack; H054's secondary
statistic is algebraically dependent on H052a per `H054_kpi_report_v1.md` §3.1).

## 5. Stability profile

- Rolling-window edge series: **not available** — 1.0 emitted 1 (ES) / 2 (NQ)
  outer folds only; no rolling-origin series exists (ADR-0004 regime postdates
  1.0). Backfill via shadow ledger is the standing remedy.
- Change-points (CUSUM/BOCPD): **never run** on H050 series — gap; folds into
  scan RC-H100-1 output.
- Estimated edge half-life: n/a — no edge detected on the gated arm at any
  point in the OOS record.
- Decayed vs never-worked determination: **never-worked** on the available
  record — the gated arm underperforms the unconditional arm on every reported
  metric over the whole OOS span (terminal wealth, max-DD, win rate 32.9% vs
  39.4% ES / 35.5% vs 47.5% NQ, differential Sharpe CI excluding zero); there
  is no earlier in-record period of positive gated performance to decay from.

## 6. Disposition

```yaml
disposition: re-specify-cost-bound
binding_criterion: "Net gated-vs-unconditional differential per-bar Sharpe CI excludes zero on the negative side on both symbols (ES -0.03714 [-0.04052, -0.03390]; NQ -0.02185 [-0.02455, -0.01903]); gate transition rate ES 30.33% / NQ 11.77% of bars with per-bar whipsaw cost-drag of 1.87x (ES) / 5.66x (NQ) the full unconditional signal magnitude (INVESTIGATE memo section 6.3-6.4, net-based attribution); no pre-cost decomposition exists in the ADR-0002 currency."
```

The binding criterion is the significantly negative **net** differential
driven primarily by whipsaw cost-drag (memo §6.6: H-c PRIMARY; on NQ the
5.66× ratio binds at a moderate 11.77% flip rate, on ES the 30.33% flip rate
binds at 1.87×), with anti-selection secondary (memo §6.1: gate state has
worse per-bar net Sharpe than the discarded state on both symbols).
`archive-no-gross-edge` is unavailable: ADR-0002 (e) requires
demonstrated absence of positive pre-cost edge in every declared conditioning
cell, and no pre-cost series or conditioning scan exists. The re-specification
is already registered in 1.0 (H050.invert, H050.stable-state) and is adopted
here as scans RC-H100-1/2/3. Disposition changes to `archive-no-gross-edge`
if RC-H100-1 and RC-H100-3 find no positive pre-cost cell; to an admit
disposition if a corrected-significant positive pre-cost cell emerges.
Standing constraint regardless of outcome: ADR-0001 Decision 5 — the HMM
state may re-enter 2.0 only as an allocator covariate, never as a binary gate.

## 7. Burned-data entry

| OOS span consumed | Purpose | Mirrored to burned_data_ledger.yaml |
|---|---|---|
| ES 2024-01-01 → 2024-12-12 (1-min bars) | admission-scan (retro; consumed by 1.0 H050 walk-forward) | recorded 2026-07-10 in [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml) (`hid: H100, instrument: ES`; commit SHA pending — working tree uncommitted for audit round) |
| NQ 2024-01-01 → 2025-12-11 (1-min bars) | admission-scan (retro; consumed by 1.0 H050 walk-forward) | recorded 2026-07-10, same ledger (`hid: H100, instrument: NQ`) |

## 8. Priors update

1. Generative regime classification used as a binary position gate is
   evidence-confirmed harmful at 1-min cadence (net differential CI < 0, both
   symbols) — reinforces ADR-0001 Decision 5 for all queued hypotheses.
2. Single-feature (return-emission) HMM states carry no demonstrated forward
   content intraday; queued regime covariates must be feature-rich and enter
   as tilts only.
3. Whipsaw cost-drag dominates at both observed switching rates — 30.33%/bar
   (ES, 1.87× signal magnitude) and even 11.77%/bar (NQ, 5.66×) per memo
   §6.3–6.4 — queued high-frequency gating designs must report per-flip cost
   attribution at design time (dwell-time feasibility gate, ADR-0004
   Decision 6, is the standing control).
4. Bar-level iid bootstrap projections understate regime-persistent drawdown
   risk (realized −81% vs projected median −38% on ES gated); session-block
   resampling is the minimum standard for survival metrics.
5. The unconditional LightGBM microstructure signal is near-noise net at
   1-min (annualised −2.63/−0.39) but unmeasured pre-cost — cheap-execution
   re-specs remain live until RC-H100-1 reports.
