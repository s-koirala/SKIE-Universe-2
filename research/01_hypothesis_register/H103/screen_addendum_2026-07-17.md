# H103 screen addendum — RC-H103-2 (ADR-0014 SCREEN re-run protocol)

**Status: FROZEN at registration (2026-07-17), before any screen computation.**
Parent design: [design.md](design.md) (frozen SHA `84d01a6b4ad0…`, 2026-07-16) —
**unchanged estimand**; this addendum adds the ADR-0014 screen machinery and
enacts the design's OWN registered certified-run refinement (the leakage-clean
per-rolling-origin stress cutoff, design §3/§6;
[RC-H103-1 disposition](../../../docs/reports/H103/RC-H103-1_admission_disposition_2026-07-16.md) §2/§7).
Governing: [ADR-0014](../../../docs/decisions/ADR-0014-provisional-candidate-pool-screen-verdict.md)
Decisions 1/3; ADR-0002 as amended; ADR-0008; ADR-0009.

**Why no new HID:** same rationale as the H101 addendum (ADR-0014 Decision 3
re-adjudication; append-only card chain). Scan id: **RC-H103-2**; register
family: `rc-h103-2`; Expert Card: `expert_card_v2`.

## Screen gates

- **(S-a)** identical to the H101 addendum (shared expert implementation and
  ledger; the canary re-run is shared evidence).
- **(S-b) Conditioning set — the CERTIFIED-run stress construction.** Cells
  {unconditional, stress, non_stress, first_hour_up, first_hour_down} per the
  frozen design §3, with the stress cell now computed LEAKAGE-CLEAN per
  rolling origin (design §6; `config/conditioning_covariates.yaml`
  `reference_distribution: training_window_empirical_cdf`): per 6-month
  evaluation window, the HMM stress-occupancy cutoff p̂ and the realized-vol
  percentile reference CDF are fit on the TRAINING span only (the design §6
  splitter VERBATIM: 24-month training window ending at the origin, first
  origin 2017-01-01, 15 windows per instrument, purge 288 bars), then applied
  to the window's sessions. HMM: the H900 registered family (4-state diag, standardized
  [ret_5m, log rvol_5m_24h]), **HMM seed 20260710** with the design's 5
  restart seeds — unchanged. Because the stress indicator DEFINES H103's
  positions, the full-sample cutoff of RC-H103-1 was registered anti-
  conservative leakage; a certifiable screen pass requires this clean
  construction. Sessions before the first origin carry no cell label and are
  excluded from the stress/non_stress cells (reported).
- **(S-c)** Estimand unchanged (per-session pre-cost gross edge per cell);
  Romano-Wolf StepM per instrument over the 5-cell family, **seed 20260716**
  (design §11), N_bootstrap 1000; pass iff mean gross > 0 AND RW-adjusted
  p < the enacted level (0.7401 at freeze). The cross-instrument Šidák union of the frozen design §5(B) is
  REPORTED as a diagnostic; the screen's binding level is the enacted
  project-wide budget (ADR-0014 S-c as instantiated 2026-07-17).
- **(S-d)** identical machinery to the H101 addendum as remediated in audit
  round 2 (DSR ≥ 1 − level = 0.2599 at freeze, gate N_trials = 20 with
  correlation-adjusted N_eff reported; PBO ≤ level = 0.7401 at freeze via
  CSCV S=16 on the per-instrument T×5 NaN-masked matrix with the
  member-only Sharpe score_fn; the config value governs; per-cell growth
  series over the registered h900 evaluation windows; the S-d/S-e stages
  are deterministic — no stage seed).
- **(S-e) Ex-ante selectability (amended at freeze).** Identical rule to the
  H101 addendum (as amended): the latent-state unsupervised latency is
  UNATTAINABLE per the reproducible 1c emission (rule v2: no accurate,
  non-degenerate operating point), so latent-state cells fail S-e outright; the H103 cells are rule-based causal covariates (the design
  §3 ADR-0001-D5 construction — membership set by the realized-vol percentile
  rule, never by the HMM state), so each cell's S-e latency input is its
  structural observation lag (0 RTH bars for the session-start stress /
  non-stress / unconditional cells; 12 for the first-hour-sign cells), and
  PASS = median consecutive-session membership run x 78 RTH bars/session >=
  that lag (structurally non-binding for these rule-based cells — the
  gate's discriminating power is reserved for latent-state cells, which
  fail outright; acknowledged per audit round 2, QUANT-2-9). The `detection_cost_caveat` of the registered covariate applies
  verbatim; the UNATTAINABLE latent-state verdict is recorded on every cell.

## Disposition rule

Identical to the H101 addendum (pass → pool entry + card v2 + registers,
STOP before verdict; fail → `archive-no-persistent-window` with sub-reason).
The RC-XCORR-1 non-redundancy input is NOT part of the screen (ADR-0014 moves
(d) to the set-level verdict); its RC-H103-1 per-instrument result stands as
recorded verdict-tier evidence, untouched here.

## Register / integrity commitments

Identical to the H101 addendum, with family `rc-h103-2`, this addendum's
SHA-256 in the run ReproLog, and the RC-H103-2 spans mirrored to the
burned-data ledger. Evidence source: the SHARED canonical k1.0 ledger
(ADR-0003; H103 is the same backfilled expert restricted to the stress cell,
design §4).
