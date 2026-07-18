---
# Expert Card - machine-readable frontmatter (schema per ADR-0009 §3)
hid: H103
card_version: 2
predecessor_card: docs/reports/expert_card_H054_retro_2026-07-10.md
design_md_sha256: "84d01a6b4ad0971fd518ffa3d325d7ec93d7e44ce28d5e97066ca974baa345aa"
screen_addendum_sha256: "532047a3753e8d84acb5c5114bdda8796f1663fb245feb6cc2c9a57c90d12a20"
repro_log_run_ids: [b257f65cd6794f788d3a0ae3708b2b9b]
data_span: { start: 2015-01-05, end: 2025-12-05 }
instruments: [ES, NQ]
execution_tier: 0            # per ADR-0006
trial_register_increment: 10  # rc-h103-2 per-cell records
disposition: pool-hold-reconsider
---

# Expert Card - H103 v2: Stress-state anti-gate ORB (ES/NQ) - ADR-0014 screen re-run

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H103 |
| Scan | RC-H103-2 (ADR-0014 SCREEN; estimand of the frozen 2026-07-16 design) |
| design.md SHA-256 | 84d01a6b4ad0971f… (full hash in frontmatter; freeze prefix verified) |
| Screen addendum SHA-256 | 532047a3753e8d84… (frozen 2026-07-17) |
| ReproLog run_id | repro_log_b257f65cd6794f788d3a0ae3708b2b9b.json |
| Screened (ReproLog UTC date) | 2026-07-18 |
| Data span | 2015-01-05 → 2025-12-05 (per-instrument ledger max) |
| Instruments | ES, NQ |
| Execution tier | 0 (bar-close; ADR-0006 — no scalping/intrabar claim) |
| Shadow-ledger partitions | expert_id=orb_first_hour_k1.0@1.0.0 (canonical; ADR-0003) |
| Trial-register increment | rc-h103-2 (+10 per-cell records) |
| Screening level | 0.7400550140326007 (enacted 2026-07-17; config/multipletest_family.yaml governs) |

## 2. Failure-mode decomposition

Screen-tier adjudication is GROSS (pre-cost) per ADR-0002(c); the net/cost
decomposition is a VERDICT-tier object. Same-ledger reference: docs/reports/H103/RC-H103-1_admission_disposition_2026-07-16.md
(net-of-cost per the RC-1 RC-XCORR-1 block (ES: net SR H101 -0.0164 / H103 -0.0238, residual IR -0.0179; NQ: net SR H101 0.0144 / H103 0.0113, residual IR 0.0000)).

**Construction-dependence exhibit (binding for prior interpretation):** RC-H103-1's headline ES stress finding (mean -5.09e-04, n=437, leaked full-sample cutoff) REVERSES under the certified leakage-clean per-origin construction (mean 1.03e-04, n=313, screen PASS). The RC-1 'Lundstrom prior contradicted' verdict was rendered on the leaked cell and is CONSTRUCTION-DEPENDENT; both records stand (append-only), and the screen's construction is the certified one.

Classification: `conditional-only` — the gross edge concentrates in specific
declared cells (ES:stress; ES:first_hour_up; NQ:non_stress; NQ:first_hour_up); the unconditional stream is not
selection-distinguishable at the S-d gate (unconditional DSR
ES 0.050; NQ 0.186 at the gate trial count N=20).

## 3. Conditional-edge panel

Conditioning set frozen in the parent design §3 (2026-07-16, pre-scan,
ADR-0002(b)); screen protocol frozen 2026-07-17 (addendum). Correction:
Romano-Wolf StepM within scan (seed 20260716; the S-c stage reproduces the RC-1 statistics bit-identically for 6/10 cells (the unchanged constructions); ES:stress, ES:non_stress, NQ:stress, NQ:non_stress differ by the certified leakage-clean per-origin construction (see the §2 exhibit)),
level = the enacted
`screening_error_rate_target` (0.7400550140326007; the config value governs); S-d
bounds DSR ≥ 1 − level, PBO ≤ level at gate N = 20; S-e per the
amended rule (rule-based causal cells: structural observation lag;
latent-state latency UNATTAINABLE per P1-2.0-H900-BOCPD-WHITENED).

```yaml
conditional_edges:
  - cell: ES:unconditional
    gross_edge: 6.606312e-05
    rw_adj_pvalue: 0.616384
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:stress
    gross_edge: 1.029491e-04
    rw_adj_pvalue: 0.616384
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: ES:non_stress
    gross_edge: 6.556211e-05
    rw_adj_pvalue: 0.616384
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:first_hour_up
    gross_edge: 2.045118e-04
    rw_adj_pvalue: 0.377622
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: ES:first_hour_down
    gross_edge: -8.091646e-05
    rw_adj_pvalue: 0.656344
    significant_at_level: true
    directional_positive: false
    s_c_pass: false
    screen_pass_all_gates: false
  - cell: NQ:unconditional
    gross_edge: 1.930809e-04
    rw_adj_pvalue: 0.310689
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:stress
    gross_edge: 1.367515e-05
    rw_adj_pvalue: 0.680320
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:non_stress
    gross_edge: 3.229474e-04
    rw_adj_pvalue: 0.168831
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: NQ:first_hour_up
    gross_edge: 3.986550e-04
    rw_adj_pvalue: 0.168831
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: NQ:first_hour_down
    gross_edge: -3.294973e-05
    rw_adj_pvalue: 0.680320
    significant_at_level: true
    directional_positive: false
    s_c_pass: false
    screen_pass_all_gates: false
```

| Cell | Gross edge | n | RW-adj p | DSR | PBO | Screen |
|---|---|---|---|---|---|---|
| ES:unconditional | 6.61e-05 | n=2276 | p=0.616 | DSR=0.050 | PBO=0.730 | no |
| ES:stress | 1.03e-04 | n=313 | p=0.616 | DSR=0.304 | PBO=0.730 | PASS |
| ES:non_stress | 6.56e-05 | n=1236 | p=0.616 | DSR=0.133 | PBO=0.730 | no |
| ES:first_hour_up | 2.05e-04 | n=1203 | p=0.378 | DSR=0.330 | PBO=0.730 | PASS |
| ES:first_hour_down | -8.09e-05 | n=1046 | p=0.656 | DSR=0.036 | PBO=0.730 | no |
| NQ:unconditional | 1.93e-04 | n=2202 | p=0.311 | DSR=0.186 | PBO=0.442 | no |
| NQ:stress | 1.37e-05 | n=318 | p=0.680 | DSR=0.255 | PBO=0.442 | no |
| NQ:non_stress | 3.23e-04 | n=1180 | p=0.169 | DSR=0.571 | PBO=0.442 | PASS |
| NQ:first_hour_up | 3.99e-04 | n=1186 | p=0.169 | DSR=0.555 | PBO=0.442 | PASS |
| NQ:first_hour_down | -3.29e-05 | n=1007 | p=0.680 | DSR=0.063 | PBO=0.442 | no |

## 4. Ensemble block

Arsenal snapshot: EMPTY (0 members at card time; the ADR-0002(d)
non-redundancy test is a VERDICT-tier object, deferred until an incumbent
set exists).

```yaml
ensemble:
  marginal_ir_estimate: null   # undefined at |arsenal| = 0 (ADR-0014)
  residual_correlation_bound: null  # authored by the first admission
  known_dependencies:
    - "H101/H103 share the k1.0 ledger (session-complement structure; RC-XCORR-1)"
```

## 5. Stability profile

Per-cell rolling-origin growth over the registered h900 evaluation windows
(screen artifact `per_window_growth`; null = the cell has no member session
in that window; stateless expert — every window is untrained data):

| Cell | Coverage | Persistence read |
|---|---|---|
| ES:unconditional | 15/15 windows estimable | positive-window fraction 0.600 |
| ES:stress | 14/15 windows estimable | positive-window fraction 0.500 |
| ES:non_stress | 15/15 windows estimable | positive-window fraction 0.600 |
| ES:first_hour_up | 15/15 windows estimable | positive-window fraction 0.733 |
| ES:first_hour_down | 15/15 windows estimable | positive-window fraction 0.467 |
| NQ:unconditional | 15/15 windows estimable | positive-window fraction 0.667 |
| NQ:stress | 13/15 windows estimable | positive-window fraction 0.615 |
| NQ:non_stress | 15/15 windows estimable | positive-window fraction 0.800 |
| NQ:first_hour_up | 15/15 windows estimable | positive-window fraction 0.667 |
| NQ:first_hour_down | 15/15 windows estimable | positive-window fraction 0.467 |

Change-points: none computed at the screen tier (the RC-1 KPSS and
rolling-dispersion exhibits stand; CUSUM/BOCPD change-point dating is a
verdict-tier stability object). Decayed vs never-worked: the S-d
persistence gates (DSR/PBO at the enacted bounds) are the screen's
separation of window from luck; no decay dating is asserted.

## 6. Disposition

```yaml
disposition: pool-hold-reconsider
binding_criterion: "4 cell(s) passed S-a..S-e at level 0.7400550140326007 (ES:stress; ES:first_hour_up; NQ:non_stress; NQ:first_hour_up); VERDICT deferred (|arsenal| = 0)"
```

Screen PASS: the expert enters the ADR-0014 provisional candidate pool as pool-hold-reconsider with the VERDICT DEFERRED (|arsenal| = 0 - the set-level marginal-geometric-growth adjudication requires an incumbent set and runs at the first-admission protocol). Re-adjudication triggers on any incumbent-set change (fresh trial-register increment + appended card version). NOTHING is certified by this pass; pool entry is a queue position.

## 7. Burned-data entry

| OOS span consumed | Purpose | Mirrored to burned_data_ledger.yaml |
|---|---|---|
| 2015-01-05 → 2025-12-05 ES+NQ | admission-scan | recorded 2026-07-17 (H103) |

## 8. Priors update

1. The enacted-level screen separates cells the then-null-level RC-1 could
   not: persistence (S-d) now binds where descriptive significance did not.
2. The passing windows are: calm (non-stress) conditional; first-hour momentum-continuation; stress-band conditional (leakage-clean per-origin) - the pool's first coverage vector; disjoint-window forward experts remain the priority (they cover cells no ORB variant reaches).
3. Latent-state (HMM-cell) conditioning cannot pass S-e until a working
   unsupervised detector exists (P1-2.0-H900-BOCPD-WHITENED verdict).
4. The first VERDICT (at arsenal-building) must author the
   arsenal-covariance / residual-correlation bound memo (register gap 2).
5. Kelly-fraction selection stays blocked (grid materialized, none selected;
   bracketing verdict inconclusive-on-null-ledger).
