---
name: ADR-0010 — Live-capital escalation schedule
description: Leverage and position multiplication scale only with demonstrated live-vs-shadow tracking fidelity on a pre-declared escalation schedule; backtest evidence alone caps at minimum size
type: governance
status: accepted
date: 2026-07-10
supersedes: ""
superseded_by: ""
---

# ADR-0010 — Live-capital escalation schedule

## Context

The program's stated objective is exponential account growth via leverage,
pyramiding, and position multiplication. Every prior ADR relaxes or
re-targets a 1.0 constraint; this one is the single point where the growth
objective meets the failure mode that funds it. Backtest and shadow evidence
overstate live performance through fill optimism, cost mis-calibration, and
selection residue — the paper-vs-reality gap is implementation shortfall
([Perold 1988](https://doi.org/10.3905/jpm.1988.409150)). Under leverage, an
overstated edge is not underperformance but ruin (ADR-0005 Kelly framing).
Therefore size is *earned by measurement*, never granted by simulation.

## Decision

1. **Minimum-size cap on simulation evidence.** An allocator configuration
   that clears the confirmation ladder (ADR-0007) is eligible only for the
   minimum viable live size (micro contracts, one unit). No simulation
   result, however strong, authorizes more.
2. **Pre-declared escalation schedule.** Before the first live trade, a
   schedule is frozen in a design.md specifying: evaluation-window length
   per step, the tracking-fidelity criterion for promotion, the size
   increment per promotion, and the maximum leverage ceiling implied by the
   position-policy registered lower-tail-quantile constraint (ADR-0005).
   Mid-flight schedule edits are
   prohibited; a new schedule is a new pre-registration.
3. **Tracking-fidelity criterion (equivalence test).** Promotion is granted
   only on *affirmative* evidence of tracking, never on failure to detect a
   difference. For each step, an equivalence margin δ on the
   live-minus-shadow return residual (both arms recorded per ADR-0003
   Decision 7) is pre-registered, derived from the cost-model tolerance —
   not hand-set. Promotion requires the two-one-sided-tests procedure at
   level α ([Schuirmann 1987](https://doi.org/10.1007/BF01068419)) —
   equivalently, the 100(1−2α)% residual CI lying entirely inside ±δ. The
   step's evaluation-window
   length is selected to achieve the registered power against a divergence
   of size δ, so short or noisy windows cannot promote through low power.
   The test level α and the power target are themselves selected by the
   same registered error-rate-cost analysis framework as ADR-0002 (c) —
   cost of false promotion under leverage against cost of delayed
   escalation — documented in the escalation-schedule design.md.
4. **Demotion is automatic and asymmetric.** A CUSUM
   ([Page 1954](https://doi.org/10.1093/biomet/41.1-2.100)) monitor on the
   live-minus-shadow residual triggers immediate demotion one step (or to
   flat, per the frozen schedule) on detection; re-promotion requires
   re-satisfying the criterion from the demoted level. Demotion thresholds
   come from the same detection-delay vs false-alarm calibration as
   ADR-0004's change-point machinery.
5. **Cost-model feedback.** Live fills continuously calibrate the cost and
   fill models (ADR-0006); a recalibration that materially degrades shadow
   performance retro-flags affected confirmation evidence for re-run.
6. **Prohibited accelerants.** Doubling-down/martingale sizing, discretionary
   overrides of the schedule, and intra-step size increases are prohibited
   categorically; they are the classic exponential-growth failure modes.

## Consequences

- Positive: the growth objective gets a concrete, auditable ramp instead of
  a leap of faith; every increment is backed by live evidence.
- Positive: the live-vs-shadow residual doubles as the program's ongoing
  execution-model validation (ADR-0006 Consequence).
- Negative: the ramp is slow by construction — weeks-to-months per step;
  calendar time becomes the binding resource, which is the honest price of
  leverage.
- Obligation: broker/platform telemetry (fills, latency) must be ingested to
  compute the residual; this is an infrastructure prerequisite to the first
  live step.

## Alternatives considered

- **Size proportional to backtest Kelly estimate from day one.** Rejected:
  maximizes exposure at the moment of maximum estimation error; ruin-first
  under the overbetting asymmetry.
- **Discretionary escalation ("scale up when it feels validated").**
  Rejected: unauditable, and the discretion will be exercised at
  euphoria-correlated moments — the schedule exists to bind future
  decisions.
- **Fixed calendar ramp regardless of tracking.** Rejected: promotes on time
  served rather than evidence; decouples size from the only measurement that
  justifies it.

## References

- [Perold 1988, J. Portfolio Manage. 14(3):4-9](https://doi.org/10.3905/jpm.1988.409150)
- [Page 1954, Biometrika 41:100-115](https://doi.org/10.1093/biomet/41.1-2.100)
- [Schuirmann 1987, J. Pharmacokinet. Biopharm. 15:657-680](https://doi.org/10.1007/BF01068419)
- [Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x); [MacLean, Thorp & Ziemba 2011](https://doi.org/10.1142/7598) (via [ADR-0005](ADR-0005-three-layer-separation.md))
- [ADR-0003](ADR-0003-shadow-ledger-canonical-object.md), [ADR-0004](ADR-0004-rolling-evaluation-regime.md), [ADR-0006](ADR-0006-execution-fidelity-tiers.md), [ADR-0007](ADR-0007-two-tier-discovery-pipeline.md)
