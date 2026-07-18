---
# Expert Card - machine-readable frontmatter (schema per ADR-0009 §3)
hid: H101
card_version: 2
predecessor_card: docs/reports/expert_card_H052a_retro_2026-07-10.md
design_md_sha256: "a7c5c9178f66dd493ad45089d244ce7425d56d829146a4070fe46d7f49a1da26"
screen_addendum_sha256: "4f644fec7558ddca4f21e6a93dca5ef775d8b23be6328b2d67e134aacd4d9f64"
repro_log_run_ids: [7804ac45138f4b248de30283e1c0d7f8]
data_span: { start: 2015-01-05, end: 2025-12-05 }
instruments: [ES, NQ]
execution_tier: 0            # per ADR-0006
trial_register_increment: 10  # rc-h101-2 per-cell records
disposition: pool-hold-reconsider
---

# Expert Card - H101 v2: Unconditional first-hour ORB (ES/NQ) - ADR-0014 screen re-run

## 1. Provenance header

| Field | Value |
|---|---|
| HID | H101 |
| Scan | RC-H101-2 (ADR-0014 SCREEN; estimand of the frozen 2026-07-16 design) |
| design.md SHA-256 | a7c5c9178f66dd49… (full hash in frontmatter; freeze prefix verified) |
| Screen addendum SHA-256 | 4f644fec7558ddca… (frozen 2026-07-17) |
| ReproLog run_id | repro_log_7804ac45138f4b248de30283e1c0d7f8.json |
| Screened (ReproLog UTC date) | 2026-07-18 |
| Data span | 2015-01-05 → 2025-12-05 (per-instrument ledger max) |
| Instruments | ES, NQ |
| Execution tier | 0 (bar-close; ADR-0006 — no scalping/intrabar claim) |
| Shadow-ledger partitions | expert_id=orb_first_hour_k1.0@1.0.0 (canonical; ADR-0003) |
| Trial-register increment | rc-h101-2 (+10 per-cell records) |
| Screening level | 0.7400550140326007 (enacted 2026-07-17; config/multipletest_family.yaml governs) |

## 2. Failure-mode decomposition

Screen-tier adjudication is GROSS (pre-cost) per ADR-0002(c); the net/cost
decomposition is a VERDICT-tier object. Same-ledger reference: docs/reports/H101/RC-H101-1_admission_disposition_2026-07-16.md
(net-of-cost decomposition: VERDICT-tier object; the same-ledger RC-1 records carry the Tier-0 net series (see the doc reference above)).

Classification: `conditional-only` — the gross edge concentrates in specific
declared cells (ES:first_hour_up; NQ:high_vol; NQ:first_hour_up); the unconditional stream is not
selection-distinguishable at the S-d gate (unconditional DSR
ES 0.056; NQ 0.201 at the gate trial count N=20).

## 3. Conditional-edge panel

Conditioning set frozen in the parent design §3 (2026-07-16, pre-scan,
ADR-0002(b)); screen protocol frozen 2026-07-17 (addendum). Correction:
Romano-Wolf StepM within scan (seed 20260716; the S-c stage reproduces the RC-1 statistics bit-identically (10/10 cells)),
level = the enacted
`screening_error_rate_target` (0.7400550140326007; the config value governs); S-d
bounds DSR ≥ 1 − level, PBO ≤ level at gate N = 20; S-e per the
amended rule (rule-based causal cells: structural observation lag;
latent-state latency UNATTAINABLE per P1-2.0-H900-BOCPD-WHITENED).

```yaml
conditional_edges:
  - cell: ES:unconditional
    gross_edge: 6.606312e-05
    rw_adj_pvalue: 0.612388
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:high_vol
    gross_edge: -7.061773e-05
    rw_adj_pvalue: 0.698302
    significant_at_level: true
    directional_positive: false
    s_c_pass: false
    screen_pass_all_gates: false
  - cell: ES:low_vol
    gross_edge: 2.620936e-05
    rw_adj_pvalue: 0.696304
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: ES:first_hour_up
    gross_edge: 2.045118e-04
    rw_adj_pvalue: 0.354645
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: ES:first_hour_down
    gross_edge: -8.091646e-05
    rw_adj_pvalue: 0.698302
    significant_at_level: true
    directional_positive: false
    s_c_pass: false
    screen_pass_all_gates: false
  - cell: NQ:unconditional
    gross_edge: 1.930809e-04
    rw_adj_pvalue: 0.351648
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: false
  - cell: NQ:high_vol
    gross_edge: 2.258089e-04
    rw_adj_pvalue: 0.597403
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: NQ:low_vol
    gross_edge: -6.771038e-05
    rw_adj_pvalue: 0.760240
    significant_at_level: false
    directional_positive: false
    s_c_pass: false
    screen_pass_all_gates: false
  - cell: NQ:first_hour_up
    gross_edge: 3.986550e-04
    rw_adj_pvalue: 0.170829
    significant_at_level: true
    directional_positive: true
    s_c_pass: true
    screen_pass_all_gates: true
  - cell: NQ:first_hour_down
    gross_edge: -3.294973e-05
    rw_adj_pvalue: 0.760240
    significant_at_level: false
    directional_positive: false
    s_c_pass: false
    screen_pass_all_gates: false
```

| Cell | Gross edge | n | RW-adj p | DSR | PBO | Screen |
|---|---|---|---|---|---|---|
| ES:unconditional | 6.61e-05 | n=2276 | p=0.612 | DSR=0.056 | PBO=0.493 | no |
| ES:high_vol | -7.06e-05 | n=763 | p=0.698 | DSR=0.092 | PBO=0.493 | no |
| ES:low_vol | 2.62e-05 | n=748 | p=0.696 | DSR=0.181 | PBO=0.493 | no |
| ES:first_hour_up | 2.05e-04 | n=1203 | p=0.355 | DSR=0.346 | PBO=0.493 | PASS |
| ES:first_hour_down | -8.09e-05 | n=1046 | p=0.698 | DSR=0.040 | PBO=0.493 | no |
| NQ:unconditional | 1.93e-04 | n=2202 | p=0.352 | DSR=0.201 | PBO=0.216 | no |
| NQ:high_vol | 2.26e-04 | n=747 | p=0.597 | DSR=0.280 | PBO=0.216 | PASS |
| NQ:low_vol | -6.77e-05 | n=721 | p=0.760 | DSR=0.056 | PBO=0.216 | no |
| NQ:first_hour_up | 3.99e-04 | n=1186 | p=0.171 | DSR=0.573 | PBO=0.216 | PASS |
| NQ:first_hour_down | -3.29e-05 | n=1007 | p=0.760 | DSR=0.068 | PBO=0.216 | no |

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
| ES:high_vol | 15/15 windows estimable | positive-window fraction 0.533 |
| ES:low_vol | 13/15 windows estimable | positive-window fraction 0.462 |
| ES:first_hour_up | 15/15 windows estimable | positive-window fraction 0.733 |
| ES:first_hour_down | 15/15 windows estimable | positive-window fraction 0.467 |
| NQ:unconditional | 15/15 windows estimable | positive-window fraction 0.667 |
| NQ:high_vol | 15/15 windows estimable | positive-window fraction 0.667 |
| NQ:low_vol | 14/15 windows estimable | positive-window fraction 0.286 |
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
binding_criterion: "3 cell(s) passed S-a..S-e at level 0.7400550140326007 (ES:first_hour_up; NQ:high_vol; NQ:first_hour_up); VERDICT deferred (|arsenal| = 0)"
```

Screen PASS: the expert enters the ADR-0014 provisional candidate pool as pool-hold-reconsider with the VERDICT DEFERRED (|arsenal| = 0 - the set-level marginal-geometric-growth adjudication requires an incumbent set and runs at the first-admission protocol). Re-adjudication triggers on any incumbent-set change (fresh trial-register increment + appended card version). NOTHING is certified by this pass; pool entry is a queue position.

## 7. Burned-data entry

| OOS span consumed | Purpose | Mirrored to burned_data_ledger.yaml |
|---|---|---|
| 2015-01-05 → 2025-12-05 ES+NQ | admission-scan | recorded 2026-07-17 (H101) |

## 8. Priors update

1. The enacted-level screen separates cells the then-null-level RC-1 could
   not: persistence (S-d) now binds where descriptive significance did not.
2. The passing windows are: first-hour momentum-continuation; high-realized-vol conditional - the pool's first coverage vector; disjoint-window forward experts remain the priority (they cover cells no ORB variant reaches).
3. Latent-state (HMM-cell) conditioning cannot pass S-e until a working
   unsupervised detector exists (P1-2.0-H900-BOCPD-WHITENED verdict).
4. The first VERDICT (at arsenal-building) must author the
   arsenal-covariance / residual-correlation bound memo (register gap 2).
5. Kelly-fraction selection stays blocked (grid materialized, none selected;
   bracketing verdict inconclusive-on-null-ledger).
