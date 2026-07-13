---
name: ADR-0005 — Three-layer separation: signal / position policy / execution
description: Signals emit direction and calibrated confidence only; sizing, pyramiding, and Kelly-fraction logic live in a separately gated position-policy layer; execution assumptions live in a third layer; cross-layer tuning is prohibited
type: architecture
status: accepted
date: 2026-07-10
supersedes: ""
superseded_by: ""
amended_by: "ADR-0013 (accepted 2026-07-12)"
---

# ADR-0005 — Three-layer separation: signal / position policy / execution

> **Amended by [ADR-0013](ADR-0013-aggressive-geometric-growth-mandate.md) (accepted 2026-07-12) — aggressive geometric-growth mandate.** Decision 2 Kelly fraction becomes a registered swept hyperparameter {0.5, 0.75, 1.0, 1.25} (no a-priori below-1 cap; winner data-selected by geometric growth) and the binding lower-tail-terminal-wealth-quantile clause is demoted to a monitored non-binding guardrail; the pyramiding gate and pre-registration discipline are retained. Decisions are NOT rewritten here; the authoritative amendment record is the ADR-0013 amendment map. Enacted on ADR-0013 acceptance (2026-07-12); overfitting-detection/integrity clauses are retained non-waivable.

## Context

The program's growth objective (compounding, pyramiding, position
multiplication relative to account size) is a *capital policy*, not evidence
about edges. Conflating the two is the classic self-deception: leverage
amplifies whatever the edge estimate is, including its error, and pyramiding
reshapes payoff skew in ways that can manufacture attractive equity curves
from zero-edge signals over finite samples. Separation makes each claim
testable at its own layer.

## Decision

1. **Signal layer** (`arsenal` subpackage). Experts emit direction and a
   calibrated confidence score only. No sizing, no leverage, no fill logic.
   Signal-layer evidence: conditional-edge scans on unit exposure (ADR-0002).
2. **Position-policy layer** (`position` subpackage). Owns sizing, leverage,
   pyramiding, and drawdown control:
   - Growth-optimal sizing follows the Kelly framework
     ([Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x)) at a
     **fractional** multiplier under a hard drawdown constraint
     ([MacLean, Thorp & Ziemba 2011](https://doi.org/10.1142/7598)). The
     fraction is selected by bootstrap simulation of the drawdown/ruin
     distribution on the shadow ledger — the standard half-Kelly heuristic is
     the *prior*, not the selected value; estimated (not true) edges overbet
     systematically, which is the empirical justification for fractions
     strictly below 1.
   - **Pyramiding is a gated component.** Any add-to-winner/add-to-loser
     schedule is pre-registered and evaluated as its own position-policy
     hypothesis with the skew and registered lower-tail-quantile
     consequences reported. On
     mean-reversion experts, pyramiding concentrates size at the breakout
     tail; this interaction must be exhibited, never assumed benign.
   - **Binding risk metric: a lower-tail terminal-wealth quantile**
     (bootstrap), never the median or mean. The quantile *level* is not a
     constant: it is derived from a registered risk-tolerance declaration —
     an acceptable ruin/drawdown probability under the constrained-growth
     formulation of MacLean-Thorp-Ziemba — frozen in a methodology memo
     before the first sizing study, with a sweep across deeper and
     shallower levels reported as sensitivity. Rationale: the mean of
     terminal wealth rises monotonically in the leverage fraction and the
     median peaks only at full Kelly, while a lower-tail quantile peaks at a
     strictly more conservative fraction — it is therefore the first of the
     three to signal overbetting, before growth-rate collapse. The
     quantile-optimal fraction is horizon-dependent (under the lognormal
     approximation an interior peak exists only when the full-Kelly fraction
     exceeds |z_q|/(σ√T)), so the registered risk-tolerance declaration
     freezes the terminal-wealth horizon T alongside the quantile level.
   - Every base expert retains its own hard stop inside its position policy;
     stop-loss authority is never delegated upward to the allocator.
3. **Execution layer** (`execution` subpackage). Owns fill models, latency,
   queue position, and transaction-cost application at the fidelity tiers of
   ADR-0006.
4. **Cross-layer tuning is prohibited.** No layer's parameters may be
   adjusted to repair another layer's measured weakness (e.g., raising Kelly
   fraction to rescue a fading signal; loosening fill assumptions to rescue a
   cost-bound expert). Each layer's parameters are selected against its own
   layer's objective on the shadow ledger.
5. The allocator (ADR-0001) composes the three layers but modifies only
   expert *weights*; it owns no stops and no leverage decisions outside the
   registered position policy.

## Consequences

- Positive: "exponential growth" claims become auditable — they must survive
  registered lower-tail-quantile accounting at the position layer rather
  than riding a backtest median.
- Positive: a cost-bound expert (ADR-0002 mode) can be rescued by execution
  work without touching the signal, and the rescue is attributable.
- Negative: three interfaces to maintain; sizing experiments need their own
  design.md documents.
- Obligation: ADR-0009 Expert Cards report signal-layer evidence on unit
  exposure; position-policy exhibits are separate sections and never blended
  into edge claims.

## Alternatives considered

- **Monolithic strategies owning their sizing and fills (1.0 style).**
  Rejected: makes the growth policy untestable and lets sizing artifacts
  masquerade as edge.
- **Allocator-owned global stop-loss.** Rejected: the allocator observes at
  weight-update cadence and cannot react intrabar; delegating stops upward
  recreates the range→breakout tail exposure at the portfolio level.
- **Full Kelly.** Rejected: with estimated edges, full Kelly is
  systematically over-leveraged (MacLean-Thorp-Ziemba); ruin risk under
  estimation error dominates the growth-rate gain.

## References

- [Kelly 1956, Bell Syst. Tech. J. 35:917-926](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x)
- [MacLean, Thorp & Ziemba 2011, *The Kelly Capital Growth Investment Criterion*, World Scientific](https://doi.org/10.1142/7598)
- [ADR-0001](ADR-0001-allocator-unit-of-inference.md), [ADR-0002](ADR-0002-arsenal-admission-standard.md), [ADR-0006](ADR-0006-execution-fidelity-tiers.md), [ADR-0009](ADR-0009-expert-card-terminal-deliverable.md)
