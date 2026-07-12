---
name: ADR-0007 — Two-tier discovery pipeline
description: Cheap high-volume exploration tier feeding an allocator-level confirmation tier with a non-waivable benchmark ladder including a matched-turnover random rotor
type: governance
status: accepted
date: 2026-07-10
supersedes: ""
superseded_by: ""
amended_by: "ADR-0013 (proposed 2026-07-12)"
---

# ADR-0007 — Two-tier discovery pipeline

> **Amended by [ADR-0013](ADR-0013-aggressive-geometric-growth-mandate.md) (proposed 2026-07-12) — aggressive geometric-growth mandate.** Decisions 1/3 discovery alpha cost-tuned looser (FDR permitted for identification where justified) and the SPA/StepM family expanded by the Kelly-fraction dimension, and Decision 2 ladder adjudication re-anchored to geometric growth; SPA/StepM/DSR/PBO and the matched-turnover random rotor are retained non-waivable. Decisions are NOT rewritten here; the authoritative amendment record is the ADR-0013 amendment map. Enacted only on ADR-0013 acceptance; overfitting-detection/integrity clauses are retained non-waivable.

## Context

1.0's observed failure pattern — test one hypothesis expensively, observe a
null, archive — is a throughput problem, not an evidence problem. The 2.0
directive relaxes strategy-level judgment (ADR-0001/0002); this ADR states
where the shed constraints went. They were not deleted: they moved to the
allocator level, because selection bias is conserved — an arsenal of N
experts screened at lenient thresholds transfers a multiplicity burden of
order N to whatever object selects among them. The data-snooping literature
this project already enforces
([White 2000](https://doi.org/10.1111/1468-0262.00152);
[Hansen 2005](https://doi.org/10.1198/073500105000000063)) was developed for
exactly this structure.

## Decision

1. **Exploration tier.** Unlimited iteration volume. Tier-0 execution
   fidelity by default (ADR-0006). Screening thresholds per the registered
   screening error-rate target (ADR-0002 (c)). No capital claims; every
   output labeled
   `exploratory`. Every scan increments the family-wise trial register
   (ADR-0008) — lenient thresholds are permitted *because* the accounting is
   airtight, not instead of it.
2. **Confirmation tier (allocator level).** A capital-eligible allocator
   configuration must beat the full **benchmark ladder**, net of costs
   including its own switching costs, on rolling evaluation (ADR-0004):
   1. best single static expert (selected in-sample; evaluated OOS),
   2. equal-weight static blend,
   3. inverse-volatility static blend,
   4. flat (zero exposure),
   5. **random-switching rotor at matched turnover** — same switching
      frequency distribution, uniformly random expert choice.
3. Ladder inference, three components:
   - **SPA construction** ([Hansen 2005](https://doi.org/10.1198/073500105000000063)):
     one SPA test *per ladder benchmark* b ∈ {1,…,5}, each with benchmark = b
     and family = every allocator configuration evaluated (per the ADR-0008
     trial register). The family is always the candidate-configuration set,
     never the benchmark set. Rejection of the null against **every**
     benchmark — an intersection-union structure across the five tests — is
     necessary but not sufficient: SPA rejection establishes only the
     *existence* of an outperforming family member, not its identity.
     Identification follows: for each benchmark b, Romano-Wolf StepM
     ([Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x))
     over the same family identifies, with FWER control, the set of
     configurations outperforming b; the nominated configuration is
     capital-eligible only if it lies in the identified outperformer set for
     all five benchmarks.
   - **Deflated Sharpe** ([Bailey & López de Prado 2014](https://doi.org/10.3905/jpm.2014.40.5.094)):
     computed from the effective number of independent trials and the
     cross-trial Sharpe variance, both estimated from the register's
     per-trial records (ADR-0008 Decision 6) — a raw trial count is not a
     sufficient input.
   - **PBO exhibit** ([Bailey, Borwein, López de Prado & Zhu 2017](https://doi.org/10.21314/JCF.2016.322)):
     combinatorially symmetric cross-validation over the persisted
     trial-level performance matrix reconstructed from the register's
     return-series pointers.
4. **Benchmark 5 is non-waivable.** The matched-turnover random rotor is the
   direct test of the founding premise — that *selection* adds value beyond
   churn. An allocator that beats 1–4 but not 5 is a turnover artifact and is
   so dispositioned.
5. Promotion path: exploration evidence → arsenal admission (ADR-0002) →
   allocator inclusion → confirmation ladder → capital eligibility
   (ADR-0010). No stage may be skipped; each transition is recorded in the
   hypothesis register.

## Consequences

- Positive: iteration volume where it is cheap, statistical burden where the
  money is; "give up after one null" is replaced by high-throughput screening
  with honest labels.
- Positive: the ladder converts "does rotation work at all?" from philosophy
  into five testable comparisons.
- Negative: the confirmation tier is expensive and will reject most allocator
  configurations; this is the design working, not failing.
- Obligation: exploratory results are contagion-controlled — they may not be
  quoted outside exploration-tier documents without their tier label.

## Alternatives considered

- **Single-tier with intermediate thresholds everywhere.** Rejected:
  mediocre at both jobs — too strict to explore freely, too loose to certify
  capital.
- **Dropping SPA/DSR at confirmation ("optimistic paradigm" literally).**
  Rejected: the decades of null results are the asset class's base rate, not
  an artifact of the correction machinery; removing the machinery produces
  false discoveries at precisely the moment leverage (ADR-0005/0010) makes
  them ruinous.
- **Benchmark ladder without the random rotor.** Rejected: ladder items 1–4
  cannot distinguish selection skill from turnover/rebalancing effects;
  item 5 is the only control matched on churn.

## References

- [White 2000, Econometrica 68:1097-1126](https://doi.org/10.1111/1468-0262.00152)
- [Hansen 2005, J. Bus. Econ. Stat. 23:365-380](https://doi.org/10.1198/073500105000000063)
- [Romano & Wolf 2005, Econometrica 73:1237-1282](https://doi.org/10.1111/j.1468-0262.2005.00615.x)
- [Bailey & López de Prado 2014, J. Portfolio Manage. 40(5):94-107](https://doi.org/10.3905/jpm.2014.40.5.094)
- [Bailey, Borwein, López de Prado & Zhu 2017, J. Comput. Finance 20(4):39-69](https://doi.org/10.21314/JCF.2016.322) (online 2016; print issue 20(4) 2017; Crossref-verified 2026-07-10)
- [ADR-0002](ADR-0002-arsenal-admission-standard.md), [ADR-0004](ADR-0004-rolling-evaluation-regime.md), [ADR-0008](ADR-0008-integrity-non-negotiables.md), [ADR-0010](ADR-0010-live-capital-escalation.md)
