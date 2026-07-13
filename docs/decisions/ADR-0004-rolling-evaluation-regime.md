---
name: ADR-0004 — Rolling evaluation regime
description: Static single-fold OOS evaluation is prohibited; evaluation is rolling-origin, reported as a time series with regret, latency, dwell-time, and the registered lower-tail terminal-wealth quantile as the primary metric family
type: evaluation
status: accepted
date: 2026-07-10
supersedes: "SKIE-Universe 1.0 single-fold walk-forward disposition convention (sibling repo; not amended in place)"
superseded_by: ""
amended_by: "ADR-0013 (accepted 2026-07-12)"
---

# ADR-0004 — Rolling evaluation regime

> **Amended by [ADR-0013](ADR-0013-aggressive-geometric-growth-mandate.md) (accepted 2026-07-12) — aggressive geometric-growth mandate.** Decision 4 primary metric becomes geometric (compounded/Kelly log-wealth) growth swept over the Kelly grid {0.5, 0.75, 1.0, 1.25} with the lower-tail terminal-wealth quantile demoted to a monitored non-binding guardrail, and Decision 3 refit-cadence selection re-anchored to out-of-window geometric growth; bootstrap/CV machinery retained. The front-matter `description` metric headline — which still names the lower-tail terminal-wealth quantile as the primary metric family — is likewise amended: the primary/ranking metric is geometric (compounded/Kelly log-wealth) growth reported across the (config × Kelly-fraction) grid {0.5, 0.75, 1.0, 1.25}, with the lower-tail quantile among the monitored non-binding guardrails. Decisions are NOT rewritten here; the authoritative amendment record is the ADR-0013 amendment map. Enacted on ADR-0013 acceptance (2026-07-12); overfitting-detection/integrity clauses are retained non-waivable.

## Context

1.0's evaluation cadence (multi-year train, one static OOS fold, terminal
number) is slower than the phenomenon under study. If regimes and edges turn
over at weekly-to-monthly frequency, a paradigm that re-estimates yearly
measures an average across regimes and reports it as a constant. The
meta-strategy premise is *only testable* under an evaluation regime whose
resolution is finer than the claimed edge lifetime.

## Decision

1. **Static single-fold OOS evaluation is prohibited** for any allocator or
   expert claim in this repository.
2. Evaluation is **rolling-origin** ([Tashman 2000](https://doi.org/10.1016/S0169-2070(00)00065-0);
   [Bergmeir & Benítez 2012](https://doi.org/10.1016/j.ins.2011.12.028)) over
   the shadow ledger, with purge and embargo at every refit boundary carried
   verbatim from 1.0 conventions (ADR-0008).
3. **Refit cadence is a selected parameter, not a chosen one**: candidate
   cadences are evaluated by nested rolling-origin CV on allocator
   out-of-window regret, and the selection rationale is documented in a
   methodology memo. Hand-set cadences are prohibited.
4. **Primary metric family** (every evaluation reports all of):
   - regret vs the best-in-hindsight *switching* oracle (fixed-share
     comparator, [Herbster & Warmuth 1998](https://doi.org/10.1023/A:1007424614876));
   - turnover-adjusted net edge (net of the ADR-0008 cost model, with
     allocator switching costs charged);
   - detection latency — bars from estimated change-point
     ([Page 1954](https://doi.org/10.1093/biomet/41.1-2.100) CUSUM;
     [Adams & MacKay 2007](https://arxiv.org/abs/0710.3742) BOCPD) to
     allocator weight response;
   - regime dwell-time vs cost break-even margin (Decision 6);
   - terminal-wealth lower-tail quantile (level per the ADR-0005 registered
     risk-tolerance declaration) under stationary-bootstrap resampling
     ([Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870))
     with automatic block length per
     [Politis & White 2004](https://doi.org/10.1081/ETC-120028836) as
     corrected by
     [Patton, Politis & White 2009](https://doi.org/10.1080/07474930802459016)
     (lifting 1.0 `inference/bootstrap.py`, which implements the corrected
     formulas), with Sharpe CIs per the quant-rules stack
     (Lo 2002 / Opdyke 2007 / Ledoit-Wolf 2008).
5. **No single terminal number is a disposition.** Report cards present the
   metric family as time series across evaluation windows; change-point dates
   are first-class reported objects.
6. **Founding feasibility gate.** The first registered analysis of the
   project is the dwell-time study: estimate the sojourn-time distribution of
   candidate regime states and compare against the break-even dwell implied
   by the cost model (detection latency + cost payback). If median dwell does
   not exceed break-even, the rotor premise fails empirically and the finding
   is reported as such before any allocator work proceeds.

## Consequences

- Positive: decay becomes observable; "worked then stopped" is a reportable
  object with a date, not a folk memory.
- Positive: evaluation resolution matches the premise being tested.
- Negative: compute multiplies by number of evaluation windows; mitigated by
  Tier-0 default fidelity (ADR-0006) and ledger reuse (ADR-0003).
- Obligation: every OOS window consumed is recorded in the burned-data ledger
  (ADR-0008); rolling evaluation burns data faster than 1.0 and the register
  must keep up.

## Alternatives considered

- **Retain single-fold with a shorter fold.** Rejected: one short fold has
  worse variance and still cannot expose time-variation; the problem is fold
  *count*, not fold length.
- **Anchored-only (expanding) evaluation.** Rejected as sole mode: expanding
  windows average over regimes by construction; permitted as a sensitivity
  exhibit alongside rolling windows.
- **Continuous online evaluation without discrete refits.** Deferred: proper
  anytime-valid inference (e-processes/confidence sequences) is attractive
  but nonstandard in this stack; revisit by ADR when tooling matures.

## References

- [Tashman 2000, Int. J. Forecast. 16:437-450](https://doi.org/10.1016/S0169-2070(00)00065-0)
- [Bergmeir & Benítez 2012, Inf. Sci. 191:192-213](https://doi.org/10.1016/j.ins.2011.12.028)
- [Herbster & Warmuth 1998, Mach. Learn. 32:151-178](https://doi.org/10.1023/A:1007424614876)
- [Page 1954, Biometrika 41:100-115](https://doi.org/10.1093/biomet/41.1-2.100)
- [Adams & MacKay 2007, arXiv:0710.3742](https://arxiv.org/abs/0710.3742)
- [Lo 2002, Financ. Anal. J. 58(4):36-52](https://doi.org/10.2469/faj.v58.n4.2453);
  [Opdyke 2007, J. Asset Manage. 8:308-336](https://doi.org/10.1057/palgrave.jam.2250084);
  [Ledoit & Wolf 2008, J. Empir. Finance 15:850-859](https://doi.org/10.1016/j.jempfin.2008.03.002)
- [Politis & Romano 1994, J. Am. Stat. Assoc. 89:1303-1313](https://doi.org/10.1080/01621459.1994.10476870);
  [Politis & White 2004, Econom. Rev. 23:53-70](https://doi.org/10.1081/ETC-120028836);
  [Patton, Politis & White 2009, Econom. Rev. 28:372-375](https://doi.org/10.1080/07474930802459016)
- [ADR-0003](ADR-0003-shadow-ledger-canonical-object.md), [ADR-0006](ADR-0006-execution-fidelity-tiers.md), [ADR-0008](ADR-0008-integrity-non-negotiables.md)
