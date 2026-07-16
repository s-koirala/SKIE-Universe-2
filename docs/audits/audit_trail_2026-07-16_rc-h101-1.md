# Audit trail — RC-H101-1 admission scan + confirmation-ladder machinery

**Date:** 2026-07-16
**Deliverable:** RC-H101-1 (H101 first-hour-ORB arsenal-admission scan) — harness
[scripts/run_rc_h101_1_scan.py](../../scripts/run_rc_h101_1_scan.py), the Romano-Wolf
StepM estimator [src/skie_universe2/inference/romano_wolf.py](../../src/skie_universe2/inference/romano_wolf.py),
and the disposition report
[docs/reports/H101/RC-H101-1_admission_disposition_2026-07-16.md](../reports/H101/RC-H101-1_admission_disposition_2026-07-16.md).
**Loop:** audit-remediate-loop, 2 rounds (cap 3), parallel-specialist-ensemble.
**Terminal verdict:** ACCEPT (round-2 quant-auditor ACCEPT; round-2 code-reviewer
minors resolved; no surviving critical/major finding).

## Round 1 — 4 parallel auditors (quant, code-review, literature, format)

### quant-auditor (12 findings; the substantive branch)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F-1-1 | major | RW step-down `break`s at first non-rejection → lower cells (incl. primary) keep adjusted p=1.0 default (placeholder, not computed) | **FIXED** — every cell now gets its Romano-Wolf-2016 efficient adjusted p over the shrinking suffix; primary now ES 0.698 / NQ 0.597 |
| F-1-2 | major | Matched-turnover rotor run on the unconditional series, but disposition targets the primary high_vol cell (misaligned benchmark) | **FIXED** — rotor now on the primary cell; unconditional kept as exhibit; disposition gates on primary-cell rotor |
| F-1-3 | major | KPSS (§8a pre-registered) skipped, justified as "statsmodels absent" | **REFUTED-then-ACTIONED** — statsmodels genuinely absent from the project `uv run` venv (auditor tested a different interpreter; refuted by reproduced-check), so the "absent" claim was accurate; but KPSS is pre-registered → declared statsmodels in the `data` extra and RAN KPSS (both `c` and `ct`) |
| F-1-4 | major | PBO (§8/ADR-0008) claimed "exercised" but never computed | **FIXED** — PBO documented as DEFERRED (not waived) with a CSCV-inapplicability justification (cell subsets on different memberships; Kelly axis blocked); removed from "exercised" list |
| F-1-5 | major | DSR used IID Sharpe SE; design §8 mandates the Lo-2002 time-series variant | **FIXED** — HAC (Newey-West 1994 Bartlett) effective-n `n/VIF` fed to the DSR SE (labeled a leading-order approximation to the exact Lo-2002 estimator per round-2 F-2-2) |
| F-1-6 | major | DSR N_trials=5 excluded the 2nd instrument; sr_std over nested cells | **FIXED** — N_trials=10 (full instrument×cell surface, documented lower bound); sr_std over non-nested conditioning cells pooled across instruments |
| F-1-7 | minor | `k=5` stationarity blocks unregistered/unjustified | **FIXED** — 6-month rolling-origin windows (design §6 step); reconciled to §8(b) in round-2 F-2-1 |
| F-1-8 | minor | Full-sample vol tercile look-ahead | **DOCUMENTED** — descriptive conditioning partition (ADR-0001-D5 covariate, not a gate); §6 train-window rule binds gates only |
| F-1-9 | minor | No in-run ReproLog | **FIXED** — `reproducibility.capture(...).write()` emitted before the scan |
| F-1-10 | minor | `entered` proxy `ret_gross!=0` vs the position column | **REFUTED-then-PARTIAL** — the Tier-0 ledger schema has NO position/turnover column (refuted by schema inspection); the valid sub-part (non-finite ruin guard) actioned |
| F-1-11 | minor | PW block length selected on `gross[entered]` but RW resamples full `gross` | **FIXED** — block length now selected on the full resampled series |
| F-1-12 | major | End-to-end scan not independently reproduced by the auditor | **RESOLVED** — re-run bit-identically (deterministic); round-2 quant reproduced ES bit-identically and hand-reconciled the DSR chain |

### code-reviewer (10 findings)

F-1-1 (major, overlapping-cell test gap) **FIXED** (test added); F-1-3 (degenerate
constant-negative cell → t=0.0 misrank) **FIXED** (→ −inf, test added); F-1-4 (unused
`gross` param) **FIXED**; F-1-5 (`_MIN_CELL_N` not threaded) **FIXED**; F-1-7 (missing
docstrings) **FIXED**; F-1-8 (null/dtype safety) **FIXED** (null_count guard); F-1-2 /
F-1-6 / F-1-9 (edge-case tests, SeedSequence, loop vectorization) **LOGGED** (minor,
non-blocking; SEED+offset is the design §11 pre-registered convention); F-1-10
(sys.path.insert) **REFUTED** — `package = false` → skie_universe2 not installed; the
insertion is load-bearing (removing it breaks `uv run python scripts/...`).

### literature-check (1 finding)

F-1-1 (minor, "Lundström prior" unattributed) **FIXED** — cited to
[Holmberg, Lönnbark & Lundström 2013, FRL 10(1):27-33](https://doi.org/10.1016/j.frl.2012.09.001)
+ Lundström (DiVA diva2:732318). All six method DOIs (Romano-Wolf 2005, Politis-Romano
1994, Ledoit-Wolf 2008, Lo 2002, KPSS 1992, Bailey-LdP 2014 DSR) verified against
Crossref and correctly attributed.

### format-auditor (6 findings)

F-1-1 (major, `k=5` bare literal) **FIXED** (named + reconciled); F-1-2 (major,
N_BOOTSTRAP/N_ROTORS justify tags label role not value) **FIXED** (MC-standard-error
value justification added); F-1-3/F-1-4 (SEED+1 offset, 1e-12 epsilons) **FIXED**
(`_EPS` named; §11 convention noted); F-1-5 (filename convention) **ACCEPTED** as the
RC-series scan-id form; F-1-6 (DSR/Lundström citation format) **FIXED**. No
identity-hygiene exposure.

## Round 2 — quant + code re-audit of the remediation

### quant-auditor — verdict **ACCEPT**

Reproduced ES bit-identically; hand-reconciled the full DSR chain (DSR=0.129 at N=10,
0.217 at N=5, both n_eff=706, VIF=1.081); confirmed the NW-1994 HAC VIF, the RW-2016
efficient adjusted-p (incl. ±inf degenerate branch), rotor-on-primary, KPSS, DSR
N=10/non-nested-sigma, block-length-on-full-series, and ReproLog all correct.

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F-2-1 | minor | §8(b) exhibit = 22 full-span 6-month bins vs the registered ~15 rolling-origin folds | **RECONCILED** — report §3.4 now states it is a full-span partition (stateless ORB → well-defined on every 6-month block), supplementary to the primary KPSS read |
| F-2-2 | minor | `n/VIF` is a leading-order HAC approximation, not the exact Lo-2002 TS Sharpe SE | **RELABELED** — helper docstring + report §3.3 now call it the NW-1994 effective-n approximation to Lo-2002 |
| F-2-3 | minor | Only trend `ct` KPSS run; the level `c` variant matches the constant-mean bootstrap premise | **FIXED** — both `c` (primary) and `ct` now run and reported; neither rejects at 5% |

### code-reviewer — minors resolved

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F-2-1 | major | `main()` summary print subscripts `deflated_sharpe['dsr']` which `_scan_dsr` can set to None → post-persist TypeError crash | **FIXED** — guarded `dsr_str = ... if dsr else "n/a"` |
| F-2-2 | minor | `warnings.simplefilter("ignore")` too broad | **FIXED** — narrowed to `InterpolationWarning` |
| F-2-3 | minor | `_cell_sharpe` returns 0.0 for a constant cell (mis-scores a constant-negative cell in the sigma pool) | **FIXED** — returns nan (dropped cleanly from the sigma pool; mirrors the romano_wolf convention) |
| F-2-4 | minor | Bare `dict` return types | **LOGGED** — type-precision polish, deferred (non-blocking) |
| F-2-5 | minor | Test hardcodes the `501` bootstrap-grid divisor | **FIXED** — divisor now tracks `n_boot` |

## Reproducibility-gap fix (discovered during commit scoping, not an audit finding)

The already-committed backfill driver (f1a9207) imported `policy.meta_shift_policy`
(the ADR-0013 Kelly grid) from an **untracked** module → HEAD unbuildable on a fresh
clone. Closed by extracting the registered grid to a clean governance module
[src/skie_universe2/policy/kelly_sweep.py](../../src/skie_universe2/policy/kelly_sweep.py)
and rewiring the backfill import — without enshrining the demoted meta_shift scalping
prototype (that cleanup remains a separate follow-up).

## Residual risk (accepted)

- **PBO deferred** (not waived): materialized once Kelly selection unblocks at the
  shadow-ledger backfill; no admission is certifiable while outstanding.
- **Screening/FWER level deferred**: the scan is descriptive; no cell is certified.
  On the evidence, no plausible level rescues an admission (every adjusted p ≥ 0.17).
- **DSR N_trials=10 is a lower bound** on the true historical trial count (H052a retro
  lineage adds more) → the reported DSR is an upper bound; DSR<0.5 on both instruments
  regardless.
- **False-strategy-theorem independence** is violated by overlapping cells
  (conservative direction — over-counts effective trials).
- **Lo-2002 SE approximation**: the HAC effective-n captures the mean LRV, not the
  exact squared-return dynamics; VIF small (≤1.375), disposition robust.
