---
name: ADR-0003 — Shadow ledger as the canonical data object
description: Every expert runs counterfactually on every asset and bar, net-of-cost, into an append-only checksummed ledger; all admission, training, and evaluation reads come from it
type: architecture
status: accepted
date: 2026-07-10
supersedes: ""
superseded_by: ""
---

# ADR-0003 — Shadow ledger as the canonical data object

## Context

Online allocation is a bandit problem if expert performance is observed only
when traded, and a full-information experts problem if every expert's
counterfactual return is observed every period. The regret separation is
material: O(√(T ln N)) full-information vs O(√(T·N ln N)) bandit
([Cesa-Bianchi & Lugosi 2006](https://doi.org/10.1017/CBO9780511546921);
[Auer et al. 2002](https://doi.org/10.1137/S0097539701398375)). Because expert
strategies are deterministic functions of market data, their counterfactual
returns are computable offline — full information is available at compute
cost only. The ledger also solves the observability failure of 1.0: a
one-shot fold cannot distinguish *decayed* from *never-worked*; a continuous
counterfactual record can.

## Decision

1. The **shadow ledger** is the single canonical data object of the project:
   an append-only record of counterfactual net-of-cost returns for **every
   arsenal expert × every universe asset × every bar**, traded or not.
2. Storage: partitioned parquet under `data/processed/shadow_ledger/`
   (partition keys: expert_id, asset, session_date), Int64/typed schema
   validated on write, SHA-256 roll-up per partition recorded in
   `data/_manifest.json` — lifting the 1.0 `WalkForwardEngine` ledger
   conventions verbatim.
3. **Append-only.** Rows are never mutated. An expert version bump is a new
   `expert_id@version`; corrections are new partitions plus a deprecation
   record. Ledger writes emit a ReproLog (ADR-0008).
4. **Sole read path.** Admission scans (ADR-0002), allocator
   training/selection (ADR-0001), rolling evaluation (ADR-0004), and Expert
   Card generation (ADR-0009) may read expert performance *only* from the
   ledger. No side-channel backtests enter evidence.
5. Each admitted expert **backfills** the ledger over the project's shared
   historical span at its assigned execution-fidelity tier (ADR-0006) with
   the bar-level cost model applied (ADR-0008) before it is eligible for
   allocator weight.
6. Per-expert ledger rows carry the conditioning covariates (ADR-0002 (b))
   as columns, so conditional-edge scans and allocator covariate tilts are
   reproducible joins, not recomputations.
7. The live system writes both arms — realized fills and shadow
   counterfactuals — enabling the live-vs-shadow tracking measurement that
   ADR-0010 escalation is conditioned on.

## Consequences

- Positive: allocator learning is full-information; decaying experts are
  de-weighted from shadow evidence *before* capital discovers the decay.
- Positive: decay vs never-worked becomes a measurable distinction
  (stability profile, ADR-0009 §5).
- Negative: compute and storage scale with arsenal × universe × bar
  frequency; Tier-0 fidelity (ADR-0006) keeps the default cheap.
- Obligation: ledger schema and cost-model version are part of every
  downstream result's provenance chain.

## Alternatives considered

- **Bandit allocation without shadow execution.** Rejected: strictly worse
  regret for no benefit given deterministic experts (references above).
- **Recompute-on-demand backtests instead of a persisted ledger.** Rejected:
  breaks provenance (results change silently with code drift), makes the
  burned-data ledger unenforceable, and repays compute per consumer.
- **Mutable ledger with in-place corrections.** Rejected: destroys audit
  reproducibility; contradicts ADR-0008.

## References

- [Cesa-Bianchi & Lugosi 2006, *Prediction, Learning, and Games*, Cambridge UP](https://doi.org/10.1017/CBO9780511546921)
- [Auer, Cesa-Bianchi, Freund & Schapire 2002, SIAM J. Comput. 32:48-77](https://doi.org/10.1137/S0097539701398375)
- SKIE-Universe 1.0 `WalkForwardEngine` parquet-ledger + SHA-256 roll-up
  conventions (sibling repo, `src/skie_ninja/backtest/`).
- [ADR-0001](ADR-0001-allocator-unit-of-inference.md), [ADR-0006](ADR-0006-execution-fidelity-tiers.md), [ADR-0008](ADR-0008-integrity-non-negotiables.md), [ADR-0010](ADR-0010-live-capital-escalation.md)
