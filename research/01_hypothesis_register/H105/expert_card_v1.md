---
# Expert Card - machine-readable frontmatter (schema per ADR-0009 §3)
hid: H105
card_version: 1
predecessor_card: null   # first card of a fresh forward candidate
design_md_sha256: "64753d968289e4227e28b729afac094d7930c98d84ca174809e80a51f4b6a7f5"
repro_log_run_ids: [69a9a8425b5046aa98291c72f66ef4e6]
data_span: { start: 2015-01-05, end: 2025-12-05 }
instruments: [ES, NQ]
execution_tier: 0            # per ADR-0006
trial_register_increment: 10  # rc-h105-1 per-cell records
disposition: pool-hold-reconsider
---

# Expert Card - H105 v1: Overnight/Globex session-drift expert (ES/NQ) - RC-H105-1 screen

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H105 |
| Scan | RC-H105-1 (ADR-0014 SCREEN; first cycle of a fresh forward candidate) |
| design.md SHA-256 | 64753d968289e422… (full hash in frontmatter; frozen 2026-07-19 lineage) |
| ReproLog run_id | repro_log_69a9a8425b5046aa98291c72f66ef4e6.json |
| Screened (ReproLog UTC date) | 2026-07-19 |
| Data span | 2015-01-05 → 2025-12-05 (ledger session span, derived) |
| Instruments | ES, NQ |
| Execution tier | 0 (bar-close; ADR-0006 D2 forbidden-claims list binds per design §13) |
| Shadow-ledger partitions | expert_id=overnight_session_drift_k1.0@1.0.0 (canonical; ADR-0003) |
| Trial-register increment | rc-h105-1 (+10 per-cell records) |
| Screening level | 0.7400550140326007 (enacted; config/multipletest_family.yaml governs) |

## 2. Failure-mode decomposition

Screen-tier adjudication is GROSS (pre-cost) per ADR-0002(c)/ADR-0014 S-c;
no net claim is made at this tier. Cost posture (declared at freeze, design
§7): one round-trip per session (turnover-matched to the ORB cadence); Tier-0 net at constant 1-tick slippage is labeled 'optimistic in thin ETH' per design §7. Mechanism basis: overnight risk premium (Boyarchenko-Larsen-Whelan 2023, 10.1093/rfs/hhad020; Lou-Polk-Skouras 2019, 10.1016/j.jfineco.2019.03.011) with the 2026 attenuation expectation pre-registered (design §1).
Coverage: overnight-ETH accrual rows, bar-disjoint from the ORB pool's RTH rows BY CONSTRUCTION (design §12(c) identity; M1 measured at disposition).

## 3. Conditional-edge panel

Conditioning set frozen in design §3 (pre-scan, ADR-0002(b)). Correction:
Romano-Wolf StepM within scan (seed 20260719), level = the enacted
`screening_error_rate_target` (0.7400550140326007; the config value governs); S-d
bounds DSR ≥ 1 − level, PBO ≤ level at gate N = 30; S-e per the
amended rule (all cells rule-based causal, observation lag 0; latent-state
latency UNATTAINABLE per P1-2.0-H900-BOCPD-WHITENED).

```yaml
conditional_edges:
  - cell: ES:unconditional
    gross_edge: 3.153546e-04
    rw_adj_pvalue: 0.036963
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:high_vol
    gross_edge: 7.156768e-04
    rw_adj_pvalue: 0.091908
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: ES:low_vol
    gross_edge: 2.427850e-04
    rw_adj_pvalue: 0.065934
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: ES:prior_rth_up
    gross_edge: 3.602522e-04
    rw_adj_pvalue: 0.035964
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: ES:prior_rth_down
    gross_edge: 3.134017e-04
    rw_adj_pvalue: 0.091908
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:unconditional
    gross_edge: 4.231210e-04
    rw_adj_pvalue: 0.009990
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:high_vol
    gross_edge: 7.364395e-04
    rw_adj_pvalue: 0.068931
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: NQ:low_vol
    gross_edge: 4.655236e-04
    rw_adj_pvalue: 0.013986
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: NQ:prior_rth_up
    gross_edge: 4.338071e-04
    rw_adj_pvalue: 0.013986
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: NQ:prior_rth_down
    gross_edge: 3.738796e-04
    rw_adj_pvalue: 0.068931
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
```

| Cell | Gross edge | n | RW-adj p | DSR | PBO | Screen |
|---|---|---|---|---|---|---|
| ES:unconditional | 3.15e-04 | n=2404 | p=0.037 | DSR=0.137 | PBO=0.543 | no |
| ES:high_vol | 7.16e-04 | n=566 | p=0.092 | DSR=0.477 | PBO=0.543 | PASS |
| ES:low_vol | 2.43e-04 | n=599 | p=0.066 | DSR=0.564 | PBO=0.543 | PASS |
| ES:prior_rth_up | 3.60e-04 | n=1222 | p=0.036 | DSR=0.467 | PBO=0.543 | PASS |
| ES:prior_rth_down | 3.13e-04 | n=1025 | p=0.092 | DSR=0.242 | PBO=0.543 | no |
| NQ:unconditional | 4.23e-04 | n=2405 | p=0.010 | DSR=0.210 | PBO=0.217 | no |
| NQ:high_vol | 7.36e-04 | n=594 | p=0.069 | DSR=0.428 | PBO=0.217 | PASS |
| NQ:low_vol | 4.66e-04 | n=559 | p=0.014 | DSR=0.788 | PBO=0.217 | PASS |
| NQ:prior_rth_up | 4.34e-04 | n=1239 | p=0.014 | DSR=0.512 | PBO=0.217 | PASS |
| NQ:prior_rth_down | 3.74e-04 | n=1020 | p=0.069 | DSR=0.231 | PBO=0.217 | no |

## 4. Ensemble block

Arsenal snapshot: EMPTY (0 members at card time; ADR-0002(d) non-redundancy
is a VERDICT-tier object under the ADR-0015 HOLD).

```yaml
ensemble:
  marginal_ir_estimate: null   # undefined at |arsenal| = 0 (ADR-0014)
  residual_correlation_bound: null  # authored by the first admission
  known_dependencies:
    - "shares the ES/NQ roll-adjusted substrate with the ORB pool (H101/H103)"
    - "M1 realized-bar/session Jaccard vs pool coverage reported at disposition"
```

## 5. Stability profile

Per-cell rolling-origin growth over the registered h900 evaluation windows
(screen artifact `per_window_growth`; null = no member session in that
window; stateless expert - every window is untrained data):

| Cell | Coverage | Persistence read |
|---|---|---|
| ES:unconditional | 15/15 windows estimable | positive-window fraction 0.867 |
| ES:high_vol | 15/15 windows estimable | positive-window fraction 0.867 |
| ES:low_vol | 14/15 windows estimable | positive-window fraction 0.643 |
| ES:prior_rth_up | 15/15 windows estimable | positive-window fraction 0.733 |
| ES:prior_rth_down | 15/15 windows estimable | positive-window fraction 0.867 |
| NQ:unconditional | 15/15 windows estimable | positive-window fraction 0.867 |
| NQ:high_vol | 15/15 windows estimable | positive-window fraction 0.867 |
| NQ:low_vol | 14/15 windows estimable | positive-window fraction 0.786 |
| NQ:prior_rth_up | 15/15 windows estimable | positive-window fraction 0.733 |
| NQ:prior_rth_down | 15/15 windows estimable | positive-window fraction 0.733 |

Change-points: none computed at the screen tier. Decayed vs never-worked:
the S-d persistence gates are the screen's separation of window from luck;
no decay dating is asserted.

## 6. Disposition

```yaml
disposition: pool-hold-reconsider
binding_criterion: "6 cell(s) passed S-a..S-e at level 0.7400550140326007 (ES:high_vol; ES:low_vol; ES:prior_rth_up; NQ:high_vol; NQ:low_vol; NQ:prior_rth_up); VERDICT deferred (ADR-0015 ratified HOLD)"
```

Screen PASS: the expert enters the ADR-0014 provisional candidate pool as pool-hold-reconsider with the VERDICT DEFERRED under the ADR-0015 ratified operator HOLD. Re-adjudication triggers on any incumbent-set change. NOTHING is certified by this pass; pool entry is a queue position. The M1 realized-bar and session-level Jaccard vs the existing pool coverage are computed and REPORTED alongside this card (setup plan §2.3; the ADR-0015 label-based precondition governs; the lift is a named, dated operator action).

## 7. Burned-data entry

The screen consumes the 15 registered h900 evaluation windows per
instrument; each window is mirrored to `config/burned_data_ledger.yaml`
under `hid: H105` with `purpose: admission-screen` (ADR-0008 D5, per
evaluation window - scripted by the emitter, not hand-maintained).

## 8. Priors update

1. overnight-ETH accrual rows, bar-disjoint from the ORB pool's RTH rows BY CONSTRUCTION (design §12(c) identity; M1 measured at disposition)
2. The screen ran at the enacted level with S-d persistence binding from
   the first cycle (no descriptive-level predecessor exists for this HID).
3. Latent-state conditioning remains unable to pass S-e
   (P1-2.0-H900-BOCPD-WHITENED verdict); every cell here is rule-based
   causal at lag 0.
4. The first VERDICT (at arsenal-building) authors the arsenal-covariance /
   residual-correlation bound memo (register gap 2).
5. Kelly-fraction selection stays blocked (grid materialized, none
   selected; bracketing verdict inconclusive-on-null-ledger).
