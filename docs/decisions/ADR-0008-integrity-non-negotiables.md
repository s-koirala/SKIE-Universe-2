---
name: ADR-0008 — Integrity non-negotiables carried from 1.0
description: PIT/leakage canaries, bar-level costs, ReproLog provenance, pre-registered conditioning sets, burned-data ledger, and the family-wise trial register apply at every tier including exploration
type: governance
status: accepted
date: 2026-07-10
supersedes: ""
superseded_by: ""
---

# ADR-0008 — Integrity non-negotiables carried from 1.0

## Context

2.0 relaxes *judgment* on individual strategies (ADR-0001/0002/0007). This
ADR enumerates what does not relax, and why: the items below are integrity
controls — they prevent evidence from being fabricated by leakage, free
lunches from omitted costs, or discoveries from unaccounted multiplicity.
Relaxing them does not produce more discoveries, only false ones. They bind
at every tier, including exploration, because a corrupted exploratory result
poisons admission evidence and the shadow ledger downstream.

## Decision

The following apply to every run, every tier, every expert, without
exception:

1. **Point-in-time discipline + leakage canaries.** Every feature computable
   at time t from data available at t; purge and embargo at every fold/refit
   boundary per
   [López de Prado 2018, *Advances in Financial Machine Learning*, Wiley](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086)
   (*practitioner*) Ch. 7; the 1.0 three-canary suite (fold-boundary
   invariant, label-horizon purge check, fit-call observer) is lifted as an
   integration-test precondition for any expert entering the shadow ledger.
2. **Bar-level cost application.** The per-side cost model applied as a
   log-return drag at the bar level in every simulated return series — never
   flat-dollar at horizon, never omitted "for screening." Gross-edge
   admission scans (ADR-0002) report pre-cost numbers *alongside* net, from
   the same ledger rows.
3. **ReproLog provenance.** Every artifact-producing run emits the 13-field
   ReproLog (git HEAD, pip-freeze SHA-256, dataset checksums, RNG seed, model
   hash) per the user-global reproducibility contract; commits use
   provenance trailers.
4. **Pre-registration of conditioning sets.** Any covariate scan (admission,
   allocator tilt, sizing study) declares its covariate set and correction
   method *before* the scan runs
   ([Nosek et al. 2018](https://doi.org/10.1073/pnas.1708274114)); post-hoc
   covariates require a fresh registered cycle.
5. **Burned-data ledger.** Every OOS span consumed by any HID is recorded in
   `config/burned_data_ledger.yaml`; a burned span is dead to successor
   hypotheses' confirmation-tier evidence. Rolling evaluation (ADR-0004)
   burns faster than 1.0 — the ledger is updated per evaluation window, not
   per project phase.
6. **Family-wise trial register.** `config/multipletest_family.yaml` per the
   multipletest-gate convention, with a schema extension beyond the raw
   count: every scan appends a per-trial record carrying (i) the HID/scan
   identifier, (ii) the trial's Sharpe estimate, (iii) a return-series
   pointer (shadow-ledger partition reference, ADR-0003), and (iv)
   clustering metadata sufficient to estimate the effective number of
   independent trials. Rationale: Deflated Sharpe requires N_eff and the
   cross-trial Sharpe variance, and PBO requires the trial-level performance
   matrix — neither is computable from a count (ADR-0007 Decision 3).
   Nothing is exempt as "just exploratory."
7. **Append-only evidence.** Shadow-ledger immutability (ADR-0003) and
   Expert Card permanence (ADR-0009): dispositions are amended by successor
   records, never edited in place.

## Consequences

- Positive: exploration can be aggressive precisely because these rails make
  its outputs trustworthy inputs.
- Negative: overhead on every run; mitigated by the fact that all seven items
  have working 1.0 implementations to lift (canary suite, cost modules,
  ReproLog emitters, multipletest-gate).
- Obligation: lifting the 1.0 implementations follows the sibling-repo
  audit-and-lift protocol (1.0 ADR-0016); each lift is audited before use.

## Alternatives considered

- **Exempting the exploration tier from the trial register.** Rejected: DSR
  is only as honest as the trial count; an uncounted screen is a silent
  multiplicity subsidy to the confirmation tier.
- **Cost-free screening with costs applied at confirmation.** Rejected:
  ranks experts by gross edge inflated in proportion to turnover, which
  anti-selects for the scalping frequencies where costs bind hardest.
- **Trusting 1.0 code without re-audit at lift time.** Rejected: 1.0's own
  audit history (leakage refactors, cost-application fixes) demonstrates the
  base rate of latent defects.

## References

- [López de Prado 2018, *Advances in Financial Machine Learning*, Wiley](https://www.wiley.com/en-us/Advances+in+Financial+Machine+Learning-p-9781119482086) (*practitioner*)
- [Nosek, Ebersole, DeHaven & Mellor 2018, PNAS 115:2600-2606](https://doi.org/10.1073/pnas.1708274114)
- SKIE-Universe 1.0: leakage-canary suite (`src/skie_ninja/backtest/`), cost
  modules (`src/skie_ninja/backtest/costs/`), ReproLog emitters, ADR-0016
  sibling-repo audit-and-lift protocol (sibling repo).
- [ADR-0002](ADR-0002-arsenal-admission-standard.md), [ADR-0003](ADR-0003-shadow-ledger-canonical-object.md), [ADR-0007](ADR-0007-two-tier-discovery-pipeline.md), [ADR-0009](ADR-0009-expert-card-terminal-deliverable.md)
