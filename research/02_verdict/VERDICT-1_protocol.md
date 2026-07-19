# VERDICT-1 — First-admission set-level VERDICT protocol (pre-registered)

*Drafted and frozen 2026-07-19 under the ADR-0015 lift authorization
(banner record of 2026-07-19; realized-bar basis operative). This document
is the pre-registered protocol ADR-0014 Decision 2 requires: no verdict
statistic is computed before this protocol's SHA-256 is recorded via
emit-repro-log and the audit-remediate loop has ACCEPTED it. Any change
after freeze is a registered addendum with its own SHA, never an edit.*

**Governing decisions:** ADR-0014 D2 (set-level verdict; estimand), D3
(reconsideration), D4 (multiplicity conserved), D6 (queue); ADR-0007 D2/D3
(five-benchmark ladder; SPA + StepM + DSR/PBO); ADR-0013 (geometric-growth
currency; Kelly sweep unselected; non-waivable core); ADR-0002(d) as
amended (non-redundancy evaluated here); ADR-0015 + ADR-0017 (lift record;
realized-bar input); ADR-0008 (register, burned data, ReproLog, PIT);
ADR-0009 (dispositions; "fail" prohibited); ADR-0003 (ledger sole evidence
source).

**Queue (verdict-readiness memo §3, authorized 2026-07-19):** 1. H106
(`vr_range_reversal_k*@1.0.0`), 2. H105 (`overnight_session_drift_k*@1.0.0`),
3. re-adjudication of the held ORB hash (H101+H103,
`orb_first_hour_k*@1.0.0`) on each incumbent-set change (ADR-0014 D3). The
incumbent set S updates after each admission; each adjudication is
registered before it runs (§6) and dispositioned when it completes (§8).

---

## 1. Estimand (ADR-0014 D2, sequential)

For candidate C adjudicated against incumbent set S at Kelly arm
f ∈ {0.5, 0.75, 1.0, 1.25}:

- **Member session return:** `r_{i,f,s}` = the sum of ledger `ret_net` rows
  of expert i's arm f in session s (bar log-returns sum to the session log
  return exactly; Tier-0, `cost_model_id: futures_rt_v1`). Gross analogs
  reported alongside; the adjudicated currency is NET (D2 "net of costs").
- **Set functional (admission-tier, declared):** the session-rebalanced
  equal-weight blend
  `g_f(U)_s = log(1 + (1/|U|) Σ_{i∈U} (e^{r_{i,f,s}} − 1))` — the
  canonical 1/N aggregator ([DeMiguel, Garlappi & Uppal 2009,
  Rev. Financ. Stud. 22(5):1915-1953](https://doi.org/10.1093/rfs/hhm075))
  and itself ladder benchmark 2, so the functional is never tuned toward
  the candidate. This is the ADMISSION-tier set functional only; Phase-4
  allocator configurations are a separate, not-here-authorized
  confirmation.
- **Marginal delta stream (the estimand):**
  `Δ_{f,s} = g_f(S ∪ {C})_s − g_f(S)_s`, per session, over the §3 OOS
  evaluation sessions. **Joint panel geometry (audit QUANT-2-2):** the two
  instruments' session axes are INNER-JOINED on common session dates, so
  the adjudicated joint panel has one row per common OOS session date and
  `2 instruments × 4 arms = 8` columns (registered order:
  instrument-major, arm-minor — `ES:k0.5 … ES:k1.25, NQ:k0.5 … NQ:k1.25`).
  The multivariate stationary bootstrap draws ONE session-index sequence
  per replicate applied to all 8 columns, so the null models serial,
  cross-arm AND cross-instrument (contemporaneous ES/NQ) dependence — the
  end-to-end concatenation of an earlier draft is REPLACED (it stacked the
  two instruments as rows ~T apart, where a block bootstrap with expected
  block ≪ T downweights the contemporaneous covariance to ≈0 and overstates
  N_eff anti-conservatively). Per-instrument exhibits are reported. **Degenerate
  first case |S| = 0:** `g_f(∅)_s ≡ 0`, so Δ = the candidate's own blend
  (= its own stream) — adjudicated against the null-allocator rungs (§2;
  the ADR-0014 Alternatives first-arm form: no standalone-profitability
  test beyond the rotor/flat null comparisons plus persistence).
- **Cost note (declared):** member-internal costs (incl. each member's own
  turnover) are inside `ret_net`; the static EW blend adds no
  allocator-level switching, and cross-member netting of same-instrument
  positions is NOT modeled (a Tier-0 session-cadence simplification; the
  un-modeled netting would LOWER true costs, so the blend's net is
  conservative on that term). Session-cadence rebalancing drift is
  second-order and not modeled; both statements carry to every artifact.
- **ADR-0002(d) non-redundancy is this estimand:** a redundant candidate
  has Δ ≈ 0 against the set that already spans it; the Grinold marginal-IR
  view stays the demoted monitored guardrail (reported, non-binding).

## 2. The ladder (ADR-0007 D2 — all five, with degenerate instantiations stated)

All benchmarks are constructed over the augmented universe U = S ∪ {C} at
arm f, per rolling origin (§3): in-sample quantities use TRAIN-span
sessions only (strictly < origin; the certified per-origin discipline).

| # | Benchmark `B_j` | Construction | Degenerate instantiation |
|---|---|---|---|
| 1 | Best single static expert | Per origin: the member with max train-span summed session log-return; OOS = its eval-span stream (in-sample-selected, OOS-evaluated) | |U|=1: identical to the candidate → differential ≡ 0 → **DEGENERATE-IDENTICAL, recorded, excluded from the §2.2 IU set with reason** |
| 2 | Equal-weight static blend | `g_f(U)` | Coincides with the §1 set functional at EVERY set size → the **identity anchor**: recorded as trivially matched, never tested (the functional is the benchmark — this is why EW was chosen as the functional). **Scope note (audit QUANT-1-3):** this identity-anchor status is a DECLARED ADR-0007 D2 degenerate instantiation scoped to the ADMISSION tier only; at Phase-4 confirmation the adjudicated objects are allocator configurations, EW returns as a LIVE tested rung against them, and the full five-rung IU is restored |
| 3 | Inverse-volatility static blend | Weights ∝ 1/σ̂_i, σ̂_i = train-span std of member session net returns, per origin; renormalized | |U|=1: identical → DEGENERATE-IDENTICAL, recorded, excluded |
| 4 | Flat | Zero position: `g ≡ 0` | Never degenerate. At |S|=0 the flat-rung differential EQUALS the marginal delta (§1) — recorded once, tested once |
| 5 | Matched-turnover rotor (NON-WAIVABLE) | The frozen `matched_turnover_rotor` (direction mode) on the CANDIDATE's per-session net stream at arm f with its entered mask — the candidate-level selection-skill control (RC-H101-1 precedent), retained at every set size | Never degenerate; never waived |

**2.1 Per-rung inference (frozen estimators only).** For each
non-degenerate rung j ∈ {1, 3, 4} (as available at |U|): the differential
panel `d_{j,(inst,f),s} = g_f(U)_s − g_f(B_j)_s` over the **8 columns**
(instrument × arm; §1 geometry); one **Hansen SPA** test per rung over the
8-column panel
([hansen_spa.py](../../src/skie_universe2/inference/hansen_spa.py), frozen
2026-07-19, consistent p primary) and one **panel Romano-Wolf StepM**
identification per rung
(`romano_wolf_stepm_panel`, frozen 2026-07-19). Rung 5 (rotor): the frozen
rotor p-value per **column**, run on that column's OWN-instrument OOS net
stream (no cross-instrument concatenation — the RC-H101/H103 per-instrument
precedent), the union over all 8 columns controlled by **Šidák**
(`p_adj = 1 − (1 − p)^8`; the RC-H103-1 cross-union precedent) — the rotor
is a distributional null over its own Monte-Carlo draw, not a fixed
benchmark stream, so SPA does not apply to it (deviation stated, machinery
frozen). The Šidák adjustment
([Šidák 1967, J. Am. Stat. Assoc. 62(318):626-633](https://doi.org/10.1080/01621459.1967.10482935))
is exact under independence and conservative under the positive dependence
the columns of one candidate carry — stated, accepted. The
**marginal panel** (§1 Δ) additionally gets its own SPA + panel-StepM (at
|S| = 0 it coincides with rung 4; computed once).

**2.2 Admission conjunction (all at the ENACTED level, read from
`config/multipletest_family.yaml` at runtime; bounds derived from it):**

1. **Marginal existence:** SPA consistent-p on the 8-column Δ panel < level.
2. **Ladder IU:** `max_j` SPA consistent-p over the non-degenerate rungs
   {1, 3, 4}∩available < level (intersection-union: every rung must be
   beaten; the max-p comparison needs no further cross-rung correction —
   an IUT that rejects iff every component level-α test rejects has size
   ≤ α, [Berger 1982, Technometrics 24(4):295-300](https://doi.org/10.1080/00401706.1982.10487790)),
   AND the rotor rung: `min` Šidák-adjusted rotor p over the 8 columns < level.
3. **Column qualification:** a column (instrument × arm) qualifies iff it
   is StepM-identified (adjusted p ≤ level) on the Δ panel AND on every
   non-degenerate rung panel AND its Šidák-adjusted rotor p < level.
   Admission requires ≥ 1 qualifying column. **The qualifying-column set is
   REPORTED — it identifies (instrument, arm) pairs and selects NO Kelly
   fraction** (§5).
4. **Persistence (non-waivable core):** for the best-qualifying column (max
   StepM statistic; reported for all columns): DSR ≥ 1 − level on the
   column's Δ Sharpe (HAC-adjusted n_eff; trial count and dispersion per
   §6), and PBO ≤ level via CSCV with the member-only-Sharpe scorer on the
   (OOS session × 8 column) Δ matrix. # justify: S = 16 CSCV splits — the
   configuration of [Bailey, Borwein, López de Prado & Zhu 2017](https://doi.org/10.21314/JCF.2016.322)
   and the frozen RC-*-2 S-d precedent (C(16,8) = 12,870 splits); the
   8-column matrix gives an 8-rank statistic — coarse but strictly finer
   than the earlier 4-arm form, and finer than the screen-tier 5-column
   precedent.
5. Ledoit-Wolf pairwise differentials: NONE pre-registered for VERDICT-1
   (available to a future registered addendum only).

**Error-rate semantics, stated plainly (audit QUANT-1-4):** clauses 1–3
report NOMINAL p-values that are unconditional on the same-substrate
screen-passage event (the candidate reached this verdict because it passed
a screen on these very eval spans); the screen→verdict selection is
absorbed only through clause 4's cumulative-trial DSR deflation (§3(ii),
§6). This is the best available construction on a single substrate and its
limits are declared, not hidden.

A candidate failing any clause is **NOT admitted** (§8 disposition); a
no-admission outcome is valid and terminal for this session.

## 3. Windows, spans, and the span-admissibility rule (audit-gated)

- **Windows:** the registered h900 rolling family, identical to every
  RC screen (`eval/windows.py::h900_windows()`: 24-month train, 6-month
  step, first origin 2017-01-01, 15 windows/instrument; purge 288 bars at
  the bar level for any bar-level fit; benchmark 1/3 fitting is
  session-level on train sessions strictly < origin, the screen-precedent
  session-level discipline). **OOS evaluation sessions = the union of the
  15 eval spans** (origin → eval_end), per instrument; the per-window Δ
  growth vector (15 entries) is a required exhibit.
- **Already-burned spans, enumerated:** all four queue HIDs carry
  burned-data records over exactly these eval spans (H101/H103:
  admission-scan/screen records of 2026-07-10/17; H105/H106: the 30
  scripted `admission-screen` window-spans each, 2026-07-19). There is no
  unburned reserve on the sole in-project substrate.
- **Span-admissibility rule (explicit, the protocol's registered
  decision):** (i) **Same-HID screen→verdict reuse is ADMISSIBLE and
  declared** — the screen and verdict are stages of ONE registered
  admission cycle per HID (ADR-0007 D5 promotion path as amended by
  ADR-0014: exploration → screen → pool → verdict; the ADR-0008 D5 force
  is against SUCCESSOR hypotheses, and a hypothesis is not its own
  successor). (ii) **Cross-candidate shared-substrate testing is
  ADMISSIBLE and declared** — the four HIDs are distinct mechanisms sharing
  the program's only substrate, exactly as their four screens already did.
  **Selection-bias accounting, attributed precisely (audit QUANT-1-4):**
  span exclusivity is impossible without new data; the selection created by
  screen→verdict progression on shared spans is absorbed ONLY through the
  register — every verdict trial is registered (§6) and enters the
  cumulative-trial DSR deflation of §2.2 clause 4, itself an enacted
  PROVISIONAL OPERATIONAL PROXY of the posterior-null budget (memo
  §A.6.2). The joint session-aligned bootstraps model serial, cross-arm
  AND cross-instrument (contemporaneous ES/NQ) dependence WITHIN each
  tested panel (the 8-column geometry of §1); they do not and cannot
  condition on the screen-passage event, and no clause claims they do.
  (iii) **The ADR-0016
  D10(b)/ADR-0008 D5 successor force is UNTOUCHED** — a same-mechanism
  successor HID (e.g. OD-G Form B after Form A) still inherits dead spans.
  This rule is registered here as an audit-gated decision, not an implicit
  reuse. (iv) Each adjudication mirrors its consumed windows to
  `config/burned_data_ledger.yaml` under its HID with
  `purpose: admission-verdict`, per window per instrument.
- **H105 substrate grade:** every H105 window on the current substrate is
  CONDITIONAL-GRADE (§7).

## 4. Costs and execution tier

Tier-0 ledger evidence only; `cost_model_id: futures_rt_v1`;
**every net figure carries the "Tier-0, constant-1-tick-slippage" label**
(and for H106 the §7 high-turnover caveat); the ADR-0006 D2 reportability
rule binds every artifact. Allocator-level cost statement per §1.

## 5. Kelly sweep — carried UNSELECTED

All four registered fractions {0.5, 0.75, 1.0, 1.25} are computed and
reported on every statistic (panels are 4-arm by construction). The
qualifying-arm set (§2.2) is a REPORTED identification, not a selection:
no artifact designates a chosen fraction; Kelly-winner selection remains a
Phase-4 champion action outside this session's authorization (ADR-0013 D3;
the 2026-07-19 authorization record).

## 6. Multiplicity — registered BEFORE any statistic

- **Family:** `first-admission-verdict` in
  `config/multipletest_family.yaml`, registered in the same commit as this
  freeze with empty trials and the **pre-registered surface rule**: per
  adjudication, trials = (candidate × 8 columns [instrument × arm] × the
  non-degenerate inference objects at the then-current |U|), enumerated by
  branch (the 8-column geometry of §1; audit QUANT-2-2):
  - |U| = 1 (first adjudication, H106): marginal/flat panel (8
    column-trials) + rotor rung (8) → **16 trials**.
  - |U| = 2 (second adjudication if the first admitted): marginal (8) +
    rungs 1, 3, 4 (24) + rotor (8) → **40 trials**. Same for each
    held-member re-adjudication at its then-current |U|.
  - No-admission branches: the SAME surface is consumed and registered
    (the trials ran); subsequent adjudications proceed at unchanged |U|.
  Per-trial records (identifier
  `VERDICT:{HID}:A{adjudication_index}:{instrument}:k{arm}:{object}` — the
  instrument keeps every column-trial unique, and the adjudication index
  makes every append unique across re-adjudications of the same HID (audit
  QUANT-1-6); the rotor trials are declaredly Sharpe-LESS
  (distributional null; the h900 non-Sharpe-trial precedent), so at |U|=1
  8 of the 16 trials carry a null `sharpe_estimate` and at |U|≥2 8 of the
  40 do. **Count-vs-dispersion divergences, both disclosed (audit
  REPRODUCIBILITY-3-1):** within the CURRENT adjudication surface the count
  and dispersion differ only by this rotor exception (the 16/40 columns
  carry no `unconditional` cell). Over the CUMULATIVE screen base the DSR
  raw count additionally retains the 8 `:unconditional` screen cells that
  the dispersion pool excludes (the standing nested-cell convention of
  `register_trial_sharpes`, H105 audit QUANT-1-4) — so the cumulative
  count/dispersion difference is the rotor exception PLUS that inherited
  `:unconditional` exclusion. No computed statistic changes; both
  divergences are methodologically intended. Sharpe of the tested
  differential, ledger
  pointers, clustering metadata) are appended by the disposition emitter at
  adjudication time — the family + surface rule registered here BEFORE any
  statistic is computed.
- **Reconciliation with `allocator-confirmation-kelly-sweep` (registered
  exactly once, never duplicated):** ADR-0014 D4 extends the accepted
  (config × Kelly) family by the pool-selection dimension. That single
  logical family is registered across two blocks by scope: the accepted
  `allocator-confirmation-kelly-sweep` block carries the Phase-4
  (allocator-config × Kelly) confirmation trials (none yet); THIS block
  carries the pool/admission-verdict dimension. No trial appears in both;
  DSR trial counts at the verdict use the CUMULATIVE register surface
  (screen families 40 + verdict trials appended to date + the current
  adjudication's surface), raw count binding, dispersion pooled over the
  same surface's recorded Sharpes (the matched-surface rule of the RC-*-1
  screens, spine `register_trial_sharpes` extended with this family).
- **Criterion (§A.8(3) re-decision, recorded BEFORE adjudication):**
  **retain-fwer stands as the incumbent.** The registered re-decision rule:
  at this family's first swept scan the cross-trial dependence is measured
  (pairwise-complete correlations of the trial differential streams,
  recorded in the family block); a move to FDR/BH would require BOTH a
  documented PRDS/BY justification (`prds_argument_ref` non-null) AND a
  cost-analysis case, neither of which is pre-supposed — absent that
  affirmative case the criterion REMAINS retain-fwer. The measured
  dependence is appended to the family block at adjudication time.
- **Level:** `screening_error_rate_target` read at runtime (full-precision
  file value governs); DSR ≥ 1 − level, PBO ≤ level derived from the same
  read. (The §A.8(1) re-derivation on first admission — Work-Plan D(b) —
  supersedes the level for SUBSEQUENT queue adjudications; see §9.)

## 7. Labeling (binding on every artifact)

- **H105:** every VERDICT-1 artifact touching H105 is labeled
  **CONDITIONAL-GRADE** (December/Globex blind spot inside its competence
  window; 91 ES / 101 NQ excluded sessions; 69.0%/67.8% of excluded bars
  overnight-ETH), with the **REGISTERED re-adjudication on the
  DR-1/DR-2-repaired ledger** stated: a FUTURE-SESSION adjudication event
  under this protocol (or a registered addendum), fresh trial-register
  increment, appended card version (ADR-0014 D3) — never an automatic
  pipeline step.
- **H106:** any admission record carries verbatim: *"net-not-monetizable
  caveat: the screened edge is pre-cost; at the Tier-0
  constant-1-tick-per-side cost floor the 1-bar-hold rule's net is deeply
  negative (memo §5(i)); admission is an allocator-unit judgment (ADR-0001)
  on marginal set contribution, not a tradable-standalone claim; the
  empirical slippage calibration (`P1-H052A-COST-CALIBRATION-EMPIRICAL`)
  and/or ADR-0016 Tier-2 work is where monetizability resolves."*
  The §1 net currency makes this caveat LOAD-BEARING for H106: its ledger
  `ret_net` carries the full turnover drag.
- All artifacts: "Tier-0, constant-1-tick-slippage"; nothing here is
  confirmation of live-capital eligibility (ADR-0010 untouched).

## 8. Dispositions (append-only)

- **Admitted:** pool ledger appends a NEW record per (HID × arm) with
  `disposition.value: admitted-arsenal-member`,
  `last_adjudicated_against` = the incumbent-set description, and the
  verdict statistics in the `complementarity` block
  (`marginal_growth_delta` now non-null); Expert Card version bump
  (append-only successor; ADR-0009); the arsenal membership register
  `config/arsenal.yaml` is CREATED at the first admission (append-only;
  authored with the D(c) covariance-anchor memo) and appended thereafter.
- **Not selected:** `pool-hold-reconsider` re-affirmed with
  `last_adjudicated_against` updated (fresh appended pool records + card
  bump; ADR-0014 D3). "Fail" is prohibited (ADR-0009).
- Every adjudication: ReproLog (13-field; `config_resolved_sha256` = THIS
  protocol's frozen SHA), per-window burned-span mirror, per-trial register
  appends, disposition report under `docs/reports/VERDICT-1/`.

## 9. Sequencing, triggers, and stop rule

Queue order per the authorization. **Upon the FIRST admission and BEFORE
any subsequent adjudication:** the Work-Plan D triggers fire — (a) Kelly
concavity/ruin grid-bracketing re-instantiation on the admitted ledger
(frozen `kelly_growth.py`; §B memo addendum); (b) discovery-alpha §A.8(1)
re-instantiation on the realized admitted stream (frozen method, fresh
ReproLog, the enacted level RE-DERIVED and committed; **subsequent
adjudications run at the re-derived level** — carrying the old level
forward would require an explicit operator-visible deviation record here);
(c) the arsenal-covariance / residual-correlation anchor memo (the
ADR-0002(d) object); (d) `P1-2.0-POOL-PRIORITY-CALIBRATE` first data
points. After the queue completes (0, 1, or more admissions): STOP —
Phase-4 entry, champion certification, and Kelly-winner selection are NOT
authorized (drafted `proposed` only).

## 10. Integrity commitments

- **Estimators:** ONLY the frozen `src/skie_universe2/inference/` set:
  `hansen_spa.py` + `romano_wolf_stepm_panel` (both frozen 2026-07-19,
  memos + tests + audit), `romano_wolf.py` (masked, screens),
  `deflated_sharpe.py`, `pbo.py`, `matched_turnover_rotor.py`,
  `ledoit_wolf_sharpe.py` (reserved), `kelly_growth.py` (trigger (a));
  block length via the frozen Politis-White selector, taken as the MAX over
  the two instruments' registered-unit (k1.0) delta columns of each tested
  panel (the longer block is conservative for both instruments;
  deterministic — audit QUANT-2-5).
- **Seed:** `SEED_VERDICT = 20260721` — pre-registered fresh seed for the
  verdict family (date-derived, H900/H001 idiom; distinct from 20260716/
  19/20 so screen and verdict draws are independent). One seed governs all
  stages; the SPA and panel-StepM stages each use a fresh
  `default_rng(SEED_VERDICT)` per panel, and the rotor stage uses per-column
  Generators seeded `SEED_VERDICT + 1 + idx`, `idx` = the registered column
  position 0…7 (decorrelating the 8 column-level Monte-Carlo rotor draws;
  the RC-*-2 per-stage convention — audit QUANT-2-6/REPRODUCIBILITY-2-3).
  Deterministic; not modified post-hoc.
- **PIT/leakage surface:** the verdict consumes realized ledger rows only;
  the sole in-sample surfaces are benchmark 1/3 train-span
  selection/weights, computed per origin from the registered 24-month
  ROLLING train span (`train_start ≤ session < origin`, both bounds
  binding — the RollingWindow contract and screen precedent; audit
  QUANT-2-1) — pinned by a no-future-dependence test in the harness test
  suite that perturbs a LATER window's eval span and asserts BOTH B1
  selection and B3 weights over an earlier window are bit-identical.
- **ReproLog:** run-level per adjudication with this protocol's SHA as
  `config_resolved_sha256`; dataset checksums bind the substrate, the
  candidate + incumbent ledger partitions (manifest digests), the level
  config, and this protocol file.
- **Freeze:** this file's SHA-256 recorded via emit-repro-log at freeze;
  changes → registered addendum with its own SHA (ADR-0016 D10(a) idiom),
  never an edit.
