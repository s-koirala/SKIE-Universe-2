---
name: ADR-0002 — Arsenal admission standard
description: Relaxed strategy-level criteria for admitting an expert to the arsenal — conditional gross edge plus non-redundancy; no standalone deployment burden
type: governance
status: accepted
date: 2026-07-10
supersedes: ""
superseded_by: ""
---

# ADR-0002 — Arsenal admission standard

## Context

With deployment inference moved to the allocator (ADR-0001), the strategy
level needs an admission standard that is deliberately looser than 1.0's gate
but still principled. The controlling example: a moving-average rule that is
profitable but does not beat buy-and-hold fails the 1.0 gate yet is a
legitimate expert — the literature arc is exactly this shape
([Brock, Lakonishok & LeBaron 1992](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x)
found MA rules profitable 1897–1986;
[Sullivan, Timmermann & White 1999](https://doi.org/10.1111/0022-1082.00163)
showed the best rule's in-sample performance survives Reality-Check
data-snooping correction over 1897–1986 but does not persist out-of-sample
1987–1996 — the edge decayed;
time-series momentum
([Moskowitz, Ooi & Pedersen 2012](https://doi.org/10.1016/j.jfineco.2011.11.003))
survives as a conditional, cross-asset phenomenon). Admission must capture
conditional value while preventing the arsenal from becoming an unaccounted
multiple-testing engine.

## Decision

An expert is **admitted** to the arsenal iff (a)–(d) all hold; it is
**archived** only under (e).

- **(a) Interface compliance.** The expert implements the canonical PIT-clean
  interface (`features_t → signal_t`, signal computable at time t from data
  available at t) and passes the leakage-canary suite (ADR-0008).
- **(b) Pre-declared conditioning set.** The regime covariates on which
  conditional edge will be scanned are frozen in the expert's design.md
  *before* any scan runs. The project-standard conditioning set (time-of-day
  bucket, realized-vol percentile, variance-ratio trend/range state,
  macro-calendar proximity, spread/liquidity regime) may be adopted by
  reference; extensions require pre-registration.
- **(c) Conditional gross edge.** Positive *pre-cost* edge in at least one
  declared conditioning cell, significant under multiplicity correction
  *within the scan*. Default correction: Romano-Wolf stepwise
  ([Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x)),
  implemented with a serial-dependence-preserving resampling scheme
  (stationary/block bootstrap per the ADR-0004 stack) so the bootstrap is
  robust both to the cross-cell dependence of overlapping conditioning cells
  and to the serial dependence of the underlying return series.
  Benjamini-Hochberg FDR
  ([Benjamini & Hochberg 1995](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x))
  is permitted only with a documented PRDS argument for the specific cell
  structure; absent that argument, the dependence-robust
  Benjamini-Yekutieli correction
  ([Benjamini & Yekutieli 2001](https://doi.org/10.1214/aos/1013699998))
  substitutes. The choice is registered per family in
  `config/multipletest_family.yaml`. The screening error-rate
  target is a registered family parameter selected once, project-wide, by
  explicit error-rate-cost analysis documented in a methodology memo — not
  a per-expert hand-tuned constant.
- **(d) Non-redundancy.** The expert's net-of-cost return series adds
  information to the existing arsenal: positive estimated marginal
  contribution to ensemble IR (Grinold-Kahn framework,
  [Grinold 1989](https://doi.org/10.3905/jpm.1989.409211)), or residual
  correlation with the spanned arsenal below the bound implied by the
  ensemble-variance budget. The bound is derived from the arsenal covariance
  estimate and documented per admission — never a fixed constant.
- **(e) Archive.** Only disposition `archive-no-gross-edge`: no positive
  pre-cost edge in *any* declared conditioning cell. All other failure modes
  (cost-bound, execution-bound, unstable, conditional-only) are re-specify or
  admit dispositions per the ADR-0009 taxonomy.

Explicitly **not required** for admission: unconditional net edge, beating
passive-long, standalone Sharpe significance, SPA membership.

Every admission scan — admit or reject — increments the family-wise trial
register (ADR-0008) and emits an Expert Card (ADR-0009).

## Consequences

- Positive: 1.0's archived hypotheses become retro-admissible; simple
  published rules (MA, ORB, TS-momentum) enter cheaply.
- Negative/obligation: arsenal growth inflates the allocator's selection
  space; the matched-turnover random-rotor benchmark (ADR-0007) is the direct
  control and is non-waivable.
- Obligation: conditional-edge scans are pre-registered — an unscanned
  covariate discovered post hoc requires a new admission cycle with a fresh
  trial-register entry.

## Alternatives considered

- **No admission standard (admit everything).** Rejected: dilutes allocator
  learning with pure-noise experts, inflates regret bound via N, and makes
  the trial register meaningless.
- **Keep net-edge (post-cost) requirement at admission.** Rejected: cost is a
  property of the position/execution layers (ADR-0005/0006); charging it at
  admission re-imports the 1.0 gate and kills cost-bound-but-informative
  experts a cheaper execution path could rescue.
- **Unconditional-edge requirement.** Rejected: contradicts the founding
  premise (conditional, transient edges) and the SMA/STW literature arc.

## References

- [Brock, Lakonishok & LeBaron 1992, J. Finance 47:1731-1764](https://doi.org/10.1111/j.1540-6261.1992.tb04681.x)
- [Sullivan, Timmermann & White 1999, J. Finance 54:1647-1691](https://doi.org/10.1111/0022-1082.00163)
- [Moskowitz, Ooi & Pedersen 2012, J. Financ. Econ. 104:228-250](https://doi.org/10.1016/j.jfineco.2011.11.003)
- [Romano & Wolf 2005, Econometrica 73:1237-1282](https://doi.org/10.1111/j.1468-0262.2005.00615.x)
- [Benjamini & Hochberg 1995, J. R. Stat. Soc. B 57:289-300](https://doi.org/10.1111/j.2517-6161.1995.tb02031.x)
- [Benjamini & Yekutieli 2001, Ann. Stat. 29:1165-1188](https://doi.org/10.1214/aos/1013699998)
- [Grinold 1989, J. Portfolio Manage. 15(3):30-37](https://doi.org/10.3905/jpm.1989.409211)
- [ADR-0001](ADR-0001-allocator-unit-of-inference.md), [ADR-0007](ADR-0007-two-tier-discovery-pipeline.md), [ADR-0008](ADR-0008-integrity-non-negotiables.md), [ADR-0009](ADR-0009-expert-card-terminal-deliverable.md)
