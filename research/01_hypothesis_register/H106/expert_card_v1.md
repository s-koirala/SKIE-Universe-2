---
# Expert Card - machine-readable frontmatter (schema per ADR-0009 §3)
hid: H106
card_version: 1
predecessor_card: null   # first card of a fresh forward candidate
design_md_sha256: "cb18e545ddb263cea7483932faba7661d4159de5d41affde4ff65aed2634d7b1"
repro_log_run_ids: [04547d701fca4e419f5dbffa47063fd0]
data_span: { start: 2015-01-05, end: 2025-12-05 }
instruments: [ES, NQ]
execution_tier: 0            # per ADR-0006
trial_register_increment: 10  # rc-h106-1 per-cell records
disposition: pool-hold-reconsider
---

# Expert Card - H106 v1: Variance-ratio range-state reversal expert (ES/NQ) - RC-H106-1 screen

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H106 |
| Scan | RC-H106-1 (ADR-0014 SCREEN; first cycle of a fresh forward candidate) |
| design.md SHA-256 | cb18e545ddb263ce… (full hash in frontmatter; frozen 2026-07-19 lineage) |
| ReproLog run_id | repro_log_04547d701fca4e419f5dbffa47063fd0.json |
| Screened (ReproLog UTC date) | 2026-07-19 |
| Data span | 2015-01-05 → 2025-12-05 (ledger session span, derived) |
| Instruments | ES, NQ |
| Execution tier | 0 (bar-close; ADR-0006 D2 forbidden-claims list binds per design §13) |
| Shadow-ledger partitions | expert_id=vr_range_reversal_k1.0@1.0.0 (canonical; ADR-0003) |
| Trial-register increment | rc-h106-1 (+10 per-cell records) |
| Screening level | 0.7400550140326007 (enacted; config/multipletest_family.yaml governs) |

## 2. Failure-mode decomposition

Screen-tier adjudication is GROSS (pre-cost) per ADR-0002(c)/ADR-0014 S-c;
no net claim is made at this tier. Cost posture (declared at freeze, design
§7): 1-bar-hold rule: per-session turnover one to two orders above the session-cadence experts; Tier-0 net at constant 1-tick slippage is expected strongly negative and is labeled 'high-turnover regime - cost-model floor' per design §7. Mechanism basis: short-horizon reversal in the registered VR(2)<1 range state (Lo-MacKinlay 1988, 10.1093/rfs/1.1.41; Lo-MacKinlay 1990, 10.1093/rfs/3.2.175); weekly-horizon transfer caveat declared (design §1).
Coverage: whole-session accrual on range-state bars; bar-level overlap vs the ORB pool is PARTIAL by design (§12(c) predicted 0.05-0.25) and CANNOT lift the ADR-0015 precondition against the ORB hash (M1 measured at disposition).

## 3. Conditional-edge panel

Conditioning set frozen in design §3 (pre-scan, ADR-0002(b)). Correction:
Romano-Wolf StepM within scan (seed 20260720), level = the enacted
`screening_error_rate_target` (0.7400550140326007; the config value governs); S-d
bounds DSR ≥ 1 − level, PBO ≤ level at gate N = 40; S-e per the
amended rule (all cells rule-based causal, observation lag 0; latent-state
latency UNATTAINABLE per P1-2.0-H900-BOCPD-WHITENED).

```yaml
conditional_edges:
  - cell: ES:unconditional
    gross_edge: 2.249769e-03
    rw_adj_pvalue: 0.000999
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: ES:vr_range_at_open
    gross_edge: 2.669807e-03
    rw_adj_pvalue: 0.000999
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: ES:vr_trend_at_open
    gross_edge: 1.226717e-03
    rw_adj_pvalue: 0.000999
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:high_vol
    gross_edge: 3.409505e-03
    rw_adj_pvalue: 0.000999
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: ES:low_vol
    gross_edge: 1.770368e-03
    rw_adj_pvalue: 0.000999
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: NQ:unconditional
    gross_edge: 1.075094e-03
    rw_adj_pvalue: 0.000999
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:vr_range_at_open
    gross_edge: 1.448092e-03
    rw_adj_pvalue: 0.000999
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:vr_trend_at_open
    gross_edge: 4.499819e-04
    rw_adj_pvalue: 0.080919
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:high_vol
    gross_edge: 2.009094e-03
    rw_adj_pvalue: 0.003996
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:low_vol
    gross_edge: 4.429156e-04
    rw_adj_pvalue: 0.080919
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
```

| Cell | Gross edge | n | RW-adj p | DSR | PBO | Screen |
|---|---|---|---|---|---|---|
| ES:unconditional | 2.25e-03 | n=2312 | p=0.001 | DSR=0.981 | PBO=0.047 | PASS |
| ES:vr_range_at_open | 2.67e-03 | n=1640 | p=0.001 | DSR=0.995 | PBO=0.047 | PASS |
| ES:vr_trend_at_open | 1.23e-03 | n=671 | p=0.001 | DSR=0.147 | PBO=0.047 | no |
| ES:high_vol | 3.41e-03 | n=541 | p=0.001 | DSR=0.775 | PBO=0.047 | PASS |
| ES:low_vol | 1.77e-03 | n=585 | p=0.001 | DSR=1.000 | PBO=0.047 | PASS |
| NQ:unconditional | 1.08e-03 | n=2252 | p=0.001 | DSR=0.000 | PBO=0.200 | no |
| NQ:vr_range_at_open | 1.45e-03 | n=1422 | p=0.001 | DSR=0.006 | PBO=0.200 | no |
| NQ:vr_trend_at_open | 4.50e-04 | n=829 | p=0.081 | DSR=0.000 | PBO=0.200 | no |
| NQ:high_vol | 2.01e-03 | n=547 | p=0.004 | DSR=0.114 | PBO=0.200 | no |
| NQ:low_vol | 4.43e-04 | n=539 | p=0.081 | DSR=0.002 | PBO=0.200 | no |

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
| ES:unconditional | 15/15 windows estimable | positive-window fraction 1.000 |
| ES:vr_range_at_open | 15/15 windows estimable | positive-window fraction 1.000 |
| ES:vr_trend_at_open | 15/15 windows estimable | positive-window fraction 0.867 |
| ES:high_vol | 15/15 windows estimable | positive-window fraction 0.933 |
| ES:low_vol | 14/15 windows estimable | positive-window fraction 0.857 |
| NQ:unconditional | 15/15 windows estimable | positive-window fraction 0.867 |
| NQ:vr_range_at_open | 15/15 windows estimable | positive-window fraction 0.867 |
| NQ:vr_trend_at_open | 15/15 windows estimable | positive-window fraction 0.733 |
| NQ:high_vol | 15/15 windows estimable | positive-window fraction 0.867 |
| NQ:low_vol | 14/15 windows estimable | positive-window fraction 0.714 |

Change-points: none computed at the screen tier. Decayed vs never-worked:
the S-d persistence gates are the screen's separation of window from luck;
no decay dating is asserted.

## 6. Disposition

```yaml
disposition: pool-hold-reconsider
binding_criterion: "4 cell(s) passed S-a..S-e at level 0.7400550140326007 (ES:unconditional; ES:vr_range_at_open; ES:high_vol; ES:low_vol); VERDICT deferred (ADR-0015 ratified HOLD)"
```

Screen PASS: the expert enters the ADR-0014 provisional candidate pool as pool-hold-reconsider with the VERDICT DEFERRED under the ADR-0015 ratified operator HOLD. Re-adjudication triggers on any incumbent-set change. NOTHING is certified by this pass; pool entry is a queue position. The M1 realized-bar and session-level Jaccard vs the existing pool coverage are computed and REPORTED alongside this card (setup plan §2.3; the ADR-0015 label-based precondition governs; the lift is a named, dated operator action).

## 7. Burned-data entry

The screen consumes the 15 registered h900 evaluation windows per
instrument; each window is mirrored to `config/burned_data_ledger.yaml`
under `hid: H106` with `purpose: admission-screen` (ADR-0008 D5, per
evaluation window - scripted by the emitter, not hand-maintained).

## 8. Priors update

1. whole-session accrual on range-state bars; bar-level overlap vs the ORB pool is PARTIAL by design (§12(c) predicted 0.05-0.25) and CANNOT lift the ADR-0015 precondition against the ORB hash (M1 measured at disposition)
2. The screen ran at the enacted level with S-d persistence binding from
   the first cycle (no descriptive-level predecessor exists for this HID).
3. Latent-state conditioning remains unable to pass S-e
   (P1-2.0-H900-BOCPD-WHITENED verdict); every cell here is rule-based
   causal at lag 0.
4. The first VERDICT (at arsenal-building) authors the arsenal-covariance /
   residual-correlation bound memo (register gap 2).
5. Kelly-fraction selection stays blocked (grid materialized, none
   selected; bracketing verdict inconclusive-on-null-ledger).
