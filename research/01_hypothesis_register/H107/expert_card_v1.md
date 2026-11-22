---
# Expert Card - machine-readable frontmatter (schema per ADR-0009 §3)
hid: H107
card_version: 1
predecessor_card: null   # first card of a fresh forward candidate
design_md_sha256: "912198045de4bee2dbffebf9efaa2998c8553431c2898f1367cebf8fd24b1397"
repro_log_run_ids: [d117c7089a2240d19347ffd06b53ff44]
data_span: { start: 2015-01-05, end: 2025-12-05 }
instruments: [ES, NQ]
execution_tier: 0            # per ADR-0006
trial_register_increment: 14  # rc-h107-1 per-cell records
disposition: archive-no-persistent-window
---

# Expert Card - H107 v1: Session-VWAP x EMA(N) crossover grid (ES/NQ, 5-min, 22h) - RC-H107-1 screen

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H107 |
| Scan | RC-H107-1 (ADR-0014 SCREEN; first cycle of a fresh forward candidate) |
| design.md SHA-256 | 912198045de4bee2… (full hash in frontmatter; frozen 2026-11-22 lineage) |
| ReproLog run_id | repro_log_d117c7089a2240d19347ffd06b53ff44.json |
| Screened (ReproLog UTC date) | 2026-11-22 |
| Data span | 2015-01-05 → 2025-12-05 (ledger session span, derived) |
| Instruments | ES, NQ |
| Execution tier | 0 (bar-close; ADR-0006 D2 forbidden-claims list binds per design §13) |
| Shadow-ledger partitions | expert_id=vwap_ema9_cross_k1.0@1.0.0 (canonical; ADR-0003) |
| Trial-register increment | rc-h107-1 (+14 per-cell records) |
| Screening level | 0.7400550140326007 (enacted; config/multipletest_family.yaml governs) |

## 2. Failure-mode decomposition

Screen-tier adjudication is GROSS (pre-cost) per ADR-0002(c)/ADR-0014 S-c;
no net claim is made at this tier. Cost posture (declared at freeze, design
§7): stop-and-reverse crossover: multiple round trips per session; net under the ninjatrader_v1 schedule (E-mini + micro x plan x slippage scenario) is descriptive in the screen artifact and binds at VERDICT. Mechanism basis: intraday time-series momentum filter (practitioner rule; nearest peer-reviewed support Gao-Han-Li-Zhou 2018, 10.1016/j.jfineco.2018.05.009); EMA span a registered 7-point grid (design §4), cells = grid points.
Coverage: always-in 22h/session (flat 15:00-17:00 CT): accrual rows overlap EVERY pool member's rows (ORB RTH, H105 overnight, H106 whole-session) - no disjointness claim; M1 overlap to be measured.

## 3. Conditional-edge panel

Trial family = the registered EMA-span grid (design §4; 7 spans x 2 instruments; each cell = one grid point's own ledger, no conditioning cells; no span selected at the screen). Correction:
Romano-Wolf StepM within scan (seed 20261122), level = the enacted
`screening_error_rate_target` (0.7400550140326007; the config value governs); S-d
bounds DSR ≥ 1 − level, PBO ≤ level at gate N = 87; S-e per the
amended rule (all cells rule-based causal, observation lag 0; latent-state
latency UNATTAINABLE per P1-2.0-H900-BOCPD-WHITENED).

```yaml
conditional_edges:
  - cell: ES:ema3
    gross_edge: -1.566447e-04
    rw_adj_pvalue: 0.762238
    significant_at_level: false
    directional_positive: false
    s_c_pass: false
    screen_pass_all_gates: false
  - cell: ES:ema5
    gross_edge: 1.356226e-04
    rw_adj_pvalue: 0.352647
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:ema9
    gross_edge: 1.929298e-04
    rw_adj_pvalue: 0.306693
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:ema13
    gross_edge: 9.093618e-05
    rw_adj_pvalue: 0.427572
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:ema21
    gross_edge: 1.662926e-04
    rw_adj_pvalue: 0.337662
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:ema34
    gross_edge: 2.459908e-04
    rw_adj_pvalue: 0.228771
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:ema55
    gross_edge: 2.531615e-04
    rw_adj_pvalue: 0.228771
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:ema3
    gross_edge: 3.079127e-04
    rw_adj_pvalue: 0.223776
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:ema5
    gross_edge: 4.246971e-04
    rw_adj_pvalue: 0.115884
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:ema9
    gross_edge: 4.333796e-04
    rw_adj_pvalue: 0.110889
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:ema13
    gross_edge: 3.158166e-04
    rw_adj_pvalue: 0.223776
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:ema21
    gross_edge: 2.523008e-04
    rw_adj_pvalue: 0.253746
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:ema34
    gross_edge: 2.439633e-04
    rw_adj_pvalue: 0.253746
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:ema55
    gross_edge: 1.485092e-04
    rw_adj_pvalue: 0.253746
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
```

| Cell | Gross edge | n | RW-adj p | DSR | PBO | Screen |
|---|---|---|---|---|---|---|
| ES:ema3 | -1.57e-04 | n=2405 | p=0.762 | DSR=0.000 | PBO=0.496 | no |
| ES:ema5 | 1.36e-04 | n=2405 | p=0.353 | DSR=0.000 | PBO=0.496 | no |
| ES:ema9 | 1.93e-04 | n=2405 | p=0.307 | DSR=0.000 | PBO=0.496 | no |
| ES:ema13 | 9.09e-05 | n=2405 | p=0.428 | DSR=0.000 | PBO=0.496 | no |
| ES:ema21 | 1.66e-04 | n=2405 | p=0.338 | DSR=0.000 | PBO=0.496 | no |
| ES:ema34 | 2.46e-04 | n=2405 | p=0.229 | DSR=0.000 | PBO=0.496 | no |
| ES:ema55 | 2.53e-04 | n=2405 | p=0.229 | DSR=0.000 | PBO=0.496 | no |
| NQ:ema3 | 3.08e-04 | n=2406 | p=0.224 | DSR=0.000 | PBO=0.446 | no |
| NQ:ema5 | 4.25e-04 | n=2406 | p=0.116 | DSR=0.000 | PBO=0.446 | no |
| NQ:ema9 | 4.33e-04 | n=2406 | p=0.111 | DSR=0.000 | PBO=0.446 | no |
| NQ:ema13 | 3.16e-04 | n=2406 | p=0.224 | DSR=0.000 | PBO=0.446 | no |
| NQ:ema21 | 2.52e-04 | n=2406 | p=0.254 | DSR=0.000 | PBO=0.446 | no |
| NQ:ema34 | 2.44e-04 | n=2406 | p=0.254 | DSR=0.000 | PBO=0.446 | no |
| NQ:ema55 | 1.49e-04 | n=2406 | p=0.254 | DSR=0.000 | PBO=0.446 | no |

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
| ES:ema3 | 15/15 windows estimable | positive-window fraction 0.400 |
| ES:ema5 | 15/15 windows estimable | positive-window fraction 0.467 |
| ES:ema9 | 15/15 windows estimable | positive-window fraction 0.533 |
| ES:ema13 | 15/15 windows estimable | positive-window fraction 0.333 |
| ES:ema21 | 15/15 windows estimable | positive-window fraction 0.400 |
| ES:ema34 | 15/15 windows estimable | positive-window fraction 0.533 |
| ES:ema55 | 15/15 windows estimable | positive-window fraction 0.533 |
| NQ:ema3 | 15/15 windows estimable | positive-window fraction 0.600 |
| NQ:ema5 | 15/15 windows estimable | positive-window fraction 0.600 |
| NQ:ema9 | 15/15 windows estimable | positive-window fraction 0.600 |
| NQ:ema13 | 15/15 windows estimable | positive-window fraction 0.467 |
| NQ:ema21 | 15/15 windows estimable | positive-window fraction 0.467 |
| NQ:ema34 | 15/15 windows estimable | positive-window fraction 0.600 |
| NQ:ema55 | 15/15 windows estimable | positive-window fraction 0.533 |

Change-points: none computed at the screen tier. Decayed vs never-worked:
the S-d persistence gates are the screen's separation of window from luck;
no decay dating is asserted.

## 6. Disposition

```yaml
disposition: archive-no-persistent-window
binding_criterion: "no cell passed the S-a..S-e conjunction at level 0.7400550140326007"
```

Screen FAIL: no persistent, ex-ante-selectable window at the enacted level; archived as archive-no-persistent-window. Reconsideration requires a fresh registered cycle.

## 7. Burned-data entry

The screen consumes the 15 registered h900 evaluation windows per
instrument; each window is mirrored to `config/burned_data_ledger.yaml`
under `hid: H107` with `purpose: admission-screen` (ADR-0008 D5, per
evaluation window - scripted by the emitter, not hand-maintained).

## 8. Priors update

1. always-in 22h/session (flat 15:00-17:00 CT): accrual rows overlap EVERY pool member's rows (ORB RTH, H105 overnight, H106 whole-session) - no disjointness claim; M1 overlap to be measured
2. The screen ran at the enacted level with S-d persistence binding from
   the first cycle (no descriptive-level predecessor exists for this HID).
3. Latent-state conditioning remains unable to pass S-e
   (P1-2.0-H900-BOCPD-WHITENED verdict); every cell here is rule-based
   causal at lag 0.
4. The first VERDICT (at arsenal-building) authors the arsenal-covariance /
   residual-correlation bound memo (register gap 2).
5. Kelly-fraction selection stays blocked (grid materialized, none
   selected; bracketing verdict inconclusive-on-null-ledger).
