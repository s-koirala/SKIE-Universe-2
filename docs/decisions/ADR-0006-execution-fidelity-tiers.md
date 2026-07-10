---
name: ADR-0006 — Execution fidelity tiers
description: Three graded execution-simulation tiers (bar-close, intrabar OHLC-path, tick/queue/latency); tier promotion is a stage gate; limit-order and interbar claims are unreportable below Tier 2
type: process
status: accepted
date: 2026-07-10
supersedes: ""
superseded_by: ""
---

# ADR-0006 — Execution fidelity tiers

## Context

The program targets minutes-scale scalping with interbar execution. Backtest
fill assumptions dominate reported performance at this frequency: assuming a
limit fill whenever price touches the level ignores queue position and
adverse selection, and flatters mean-reversion strategies specifically —
the fills most likely granted are the ones where the market blew through the
level ([Harris 2003](https://global.oup.com/academic/product/trading-and-exchanges-9780195144703),
*practitioner*). Paper-vs-reality divergence is the canonical implementation
shortfall ([Perold 1988](https://doi.org/10.3905/jpm.1988.409150)). At the
same time, forcing tick-level simulation on every screening run would make
exploration unaffordable. Graded fidelity resolves the tension.

## Decision

1. Three execution-simulation tiers, implemented in the `execution`
   subpackage:
   - **Tier 0 — bar-close.** Market-order fills at bar close, bar-level cost
     model applied. Default for all exploration-tier work (ADR-0007) and
     shadow-ledger backfill.
   - **Tier 1 — intrabar OHLC-path.** Fills evaluated against the
     high/low/close path with conservative tie-breaking (adverse ordering
     when OHLC path is ambiguous). Minimum tier for any pyramiding or
     stop-placement exhibit (position layer, ADR-0005), since stops and adds
     trigger intrabar.
   - **Tier 2 — tick/queue/latency.** Tick (or finest available) data, queue
     position model for limit orders, explicit latency assumption,
     order-flow-aware slippage
     ([Cont, Kukanov & Stoikov 2014](https://doi.org/10.1093/jjfinec/nbt003)).
     Required tier for any limit-order, interbar-entry, or scalping-hold-time
     claim.
2. **Reportability rule.** A performance claim is unreportable above its
   simulated tier's ceiling: limit-order/interbar/scalping claims below
   Tier 2, and pyramiding/stop exhibits below Tier 1, may appear only in
   exploration-tier material explicitly labeled with their tier.
3. **Tier promotion is a stage gate**: an expert or allocator configuration
   promotes to a higher tier only with a design.md amendment recording the
   added execution assumptions, and the higher-tier result supersedes the
   lower-tier one in all downstream evidence.
4. The bar-level cost model (lifted from 1.0 `backtest/costs/`, per-side,
   applied as log-return drag) applies at **every** tier; tiers add fill
   realism on top of, never instead of, the cost model. Empirical cost
   calibration from live fills feeds back per ADR-0010.
5. Tier is a recorded column in the shadow ledger (ADR-0003); mixed-tier
   comparisons are prohibited within a single evidence table.

## Consequences

- Positive: exploration stays cheap (Tier 0); realism is purchased only where
  a claim depends on it.
- Positive: fill-assumption sensitivity becomes an explicit, auditable delta
  (Tier 0 vs 1 vs 2 on the same expert).
- Negative: Tier 2 requires tick-data acquisition and a queue model — a
  substantial infrastructure hypothesis of its own; until it lands, the
  program's scalping claims remain formally exploratory.
- Obligation: the Tier-2 fill model itself must be validated against live
  fills (ADR-0010 tracking data) before its outputs are confirmation-grade.

## Alternatives considered

- **Single high-fidelity tier for everything.** Rejected: exploration
  throughput is the 2.0 objective; tick-level simulation on every screen
  reprices iteration back to 1.0 economics.
- **Optimistic intrabar fills (touch = fill).** Rejected: known upward bias
  for limit-order mean-reversion; conservative tie-breaking is the only
  defensible Tier-1 default.
- **Deferring all execution realism to live paper-trading.** Rejected: burns
  calendar time (the scarcest resource) and confounds execution error with
  signal decay.

## References

- [Perold 1988, J. Portfolio Manage. 14(3):4-9](https://doi.org/10.3905/jpm.1988.409150)
- [Cont, Kukanov & Stoikov 2014, J. Financ. Econom. 12:47-88](https://doi.org/10.1093/jjfinec/nbt003)
- [Harris 2003, *Trading and Exchanges*, Oxford UP](https://global.oup.com/academic/product/trading-and-exchanges-9780195144703) (*practitioner*)
- SKIE-Universe 1.0 cost-model modules (sibling repo, `src/skie_ninja/backtest/costs/`)
- [ADR-0003](ADR-0003-shadow-ledger-canonical-object.md), [ADR-0005](ADR-0005-three-layer-separation.md), [ADR-0007](ADR-0007-two-tier-discovery-pipeline.md), [ADR-0010](ADR-0010-live-capital-escalation.md)
