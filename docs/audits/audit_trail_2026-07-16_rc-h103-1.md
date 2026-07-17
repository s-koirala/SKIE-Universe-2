# Audit trail — RC-H103-1 stress-state-ORB admission scan + Ledoit-Wolf estimator

**Date:** 2026-07-16
**Deliverable:** the RC-H103-1 admission scan harness
[scripts/run_rc_h103_1_scan.py](../../scripts/run_rc_h103_1_scan.py), the new Ledoit-Wolf
(2008) studentized-bootstrap Sharpe-difference estimator
[src/skie_universe2/inference/ledoit_wolf_sharpe.py](../../src/skie_universe2/inference/ledoit_wolf_sharpe.py),
and the disposition report
[docs/reports/H103/RC-H103-1_admission_disposition_2026-07-16.md](../reports/H103/RC-H103-1_admission_disposition_2026-07-16.md).
**Design:** implements the FROZEN H103 design (SHA `84d01a6b4ad0…`).
**Loop:** audit-remediate-loop, 2 rounds (cap 3), parallel-specialist-ensemble.
**Terminal verdict:** ACCEPT (round-2 quant-auditor ACCEPT; no surviving critical/major).
**Disposition:** provisional-archive-null (no stress-cell edge; RC-XCORR-1 redundancy
instrument-specific — ES redundant, NQ zero-marginal). A POWERED-by-n but
precision-failing, redundancy-establishing null.

## Round 1 — quant + code auditors

### quant-auditor (6 major, 1 minor)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F-1-1 | major | RC-XCORR-1 computed on GROSS not the design-specified NET-OF-COST series | **FIXED** — ledger aggregates `ret_net`; RC-XCORR-1 uses net-of-cost series |
| F-1-2 | major | Marginal contribution was a crude equal-weight (0.5) Sharpe delta, not the Grinold marginal-IR; §10(iii) covariance-bound never computed | **FIXED** — replaced with the Grinold residual/appraisal IR (SR₁₀₃−ρ·SR₁₀₁)/√(1−ρ²) and the covariance-derived bound ρ·SR₁₀₁; the redundancy conclusion is now instrument-specific (ES redundant, NQ zero-marginal), correcting an earlier over-claim |
| F-1-3 | major | NQ power floor transported the ES anchor (n≥174) despite the design forbidding it; false "NQ re-derived" comment | **FIXED** — labeled ES-anchor-only; per-instrument n_ES/n_NQ re-derivation documented DEFERRED (certified-run); `exceeds_es_anchor` is a lower-bound check |
| F-1-4 | major | Full-sample HMM+percentile cutoff is genuine look-ahead for a POSITION-DEFINING indicator; the RC-H101-1 "descriptive precedent" analogy understated it | **FIXED** — docstring + report §2 state the leakage is genuine but ANTI-CONSERVATIVE for H0 (can only inflate stress edge), so the null is robust a fortiori; per-origin cutoff DEFERRED |
| F-1-5 | major | Disposition label "archive-null + redundant" overreached vs the deferred screening level and the RC-H101-1 precedent | **FIXED** — downgraded to "provisional-archive-null"; redundancy now instrument-specific, not a firm uniform claim |
| F-1-6 | major | The design §8 Ledoit-Wolf pairwise stress-vs-complement Sharpe comparison (the anti-gate differential) was absent | **FIXED** — built `ledoit_wolf_sharpe.py` (LW08 studentized stationary-block bootstrap; 10 tests) and wired the stress-vs-complement/-unconditional comparisons (§3.6; all non-significant) |
| F-1-7 | minor | §8 25% precision gate + stress-cell CI not computed | **FIXED** — stationary-bootstrap CI + half-width/point ratio; both cells FAIL the 25% gate (means indistinguishable from zero) |

### code-reviewer (1 major, 5 minor)

F-1-1 (major, unguarded stationary-vector extraction) **FIXED** (|Re|, _EPS-guarded denom,
np.clip p̂∈[0,1], empirical-occupancy fallback); F-1-2 (run_scan return schema undocumented)
**FIXED**; F-1-3 (n_nonfinite not carried) **FIXED**; F-1-4 (duplicated helpers) **LOGGED**
(acceptable under the non-package constraint); F-1-5 (inert `seed=` with restart_seeds)
**FIXED** (comment); F-1-6 (ddof inconsistency) **FIXED**.

## Round 2 — quant re-audit — verdict ACCEPT

The auditor independently benchmarked the LW delta-method gradient against numerical
differentiation (~9 digits) and the IID HAC SE against the influence-series reference. All
round-1 remediations verified. Six minors, all inert to the null disposition:

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F-2-1 | minor | The T/(T-4) d.o.f. factor was falsely attributed to LW08 (which has no such term); provably inert | **FIXED** — relabeled as a self-chosen inert small-sample adjustment (citation fidelity) |
| F-2-2 | minor | No committed numeric-benchmark test for the LW estimator (CLAUDE.md mandates benchmark confirmation) | **FIXED** — added a test pinning the HAC SE against the Lo-2002 closed form for independent IID-normal series (agree to <2% at n=2e5) |
| F-2-3 | minor | `adds_marginal_ir` unguarded for a net-negative base leg (SR₁₀₁<0) | **FIXED** — gated on `base_net_positive` (SR₁₀₁>0); inert here (ES already False) but now correct |
| F-2-4 | minor | Only the §10(iii) IR-positive branch computed, not the OR-variance-budget branch | **DOCUMENTED** — the single branch is strictly stricter (conservative), cannot flip a null; full branch is a certified-run refinement |
| F-2-5 | minor | LW block length borrowed from the unconditional-gross series, not its own influence series | **FIXED** — pass `block_length=None` so the estimator PW-auto-selects on its own influence series |
| F-2-6 | minor | Bartlett-NW HAC kernel vs LW08's QS-prewhitened; disclosed, internally consistent | **NO CHANGE** — documented deviation (project HAC default); prewhitening is a certified-run sensitivity |

## Residual risk (accepted)

- The full-sample stress cutoff is genuine look-ahead (position-defining), retained only
  because it is anti-conservative for H0; the leakage-clean per-origin cutoff is DEFERRED.
- Only the conservative §10(iii) IR-positive non-redundancy branch is exercised; the
  variance-budget branch is DEFERRED (cannot flip a null).
- The LW HAC SE (Bartlett-NW, no prewhitening) may differ modestly from LW08's canonical
  QS-prewhitened SE, but every LW comparison is far from significance (min p=0.33), and RW /
  DSR / rotor / precision / marginal-IR all independently corroborate the null.
- PBO, the screening/FWER level, the exact Lo-2002 TS Sharpe SE, and the per-instrument power
  floor remain DEFERRED (certified-run); nothing is certified.
