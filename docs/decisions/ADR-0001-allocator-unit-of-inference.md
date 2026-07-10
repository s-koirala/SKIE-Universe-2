---
name: ADR-0001 — Allocator as the unit of statistical inference
description: Statistical hypotheses in 2.0 are statements about the allocator's rolling net performance; individual strategies are experts (inputs), never conclusions
type: architecture
status: accepted
date: 2026-07-10
supersedes: "SKIE-Universe 1.0 per-strategy deployment-gate paradigm (sibling repo; not amended in place)"
superseded_by: ""
---

# ADR-0001 — Allocator as the unit of statistical inference

## Context

SKIE-Universe 1.0 evaluated each hypothesis as a standalone strategy: a single
walk-forward fold (train 2015–2022, OOS 2024–2025), a primary inference
`T = SR_arm − SR_bench` with a Ledoit-Wolf 2008 CI, and a terminal pass/fail
disposition. The realized dispositions — H050 (HMM regime-gating actively
harmful, CI excludes zero on the negative side, both symbols), H053 (null),
H052a/H054 (no unconditional deployable edge) — constitute the program's
empirical finding: no standalone, unconditional, all-regime strategy in the
tested family survives its own deployment gate. The 2026-07-10 user directive
founds 2.0 on the alternative premise: edges are conditional and transient, and
the tradable object is the *rotation among them*, not any single member.

A meta-layer allocation claim cannot be adjudicated by per-component gates.
Requiring each expert to independently beat a benchmark (1.0's gate) filters
out exactly the components a rotor needs — strategies with positive
*conditional* edge and useful decorrelation but no standalone alpha. The
component's worth in an ensemble is its marginal contribution
([Grinold 1989](https://doi.org/10.3905/jpm.1989.409211)), not its solo record.

## Decision

1. The unit of statistical inference in this project is the **allocator**: an
   online strategy-selection layer over an arsenal of expert strategies.
   Every deployment-grade hypothesis (SPA family membership, CI on net edge,
   capital decision) attaches to allocator output series only.
2. **No individual strategy is ever required to beat a benchmark to remain in
   the arsenal.** The 1.0 strategy-level deployment gate is abolished in this
   repository. Strategy-level evaluation exists solely to produce admission
   evidence (ADR-0002) and Expert Cards (ADR-0009).
3. The allocator family is the **full-information online-experts class**:
   multiplicative-weights / Hedge
   ([Freund & Schapire 1997](https://doi.org/10.1006/jcss.1997.1504)) with
   non-stationarity handling via fixed-share
   ([Herbster & Warmuth 1998](https://doi.org/10.1023/A:1007424614876)),
   discounted cumulative losses
   ([Cesa-Bianchi & Lugosi 2006 §2.11](https://doi.org/10.1017/CBO9780511546921)),
   or adaptive-regret methods
   ([Hazan & Seshadhri 2009](https://doi.org/10.1145/1553374.1553425)). Regret
   against a switching oracle is the theoretical object the program tests.
   (Discounted/sliding-window UCB per
   [Garivier & Moulines 2011, ALT, LNCS 6925:174-188](https://doi.org/10.1007/978-3-642-24412-4_16)
   is the *bandit-side* analogue and is out of scope per the Alternatives
   section.)
4. Allocator hyperparameters (learning rate, share/discount rate, window) are
   **never hand-set**: selection is by nested walk-forward CV on the shadow
   ledger (ADR-0003) under the rolling-evaluation regime (ADR-0004), per the
   user-global zero-magic-numbers directive.
5. Generative regime *classification as a gate* is prohibited as an allocator
   mechanism. H050 is the controlling precedent: a wrong latent-state model is
   worse than none. Latent regime estimates may enter only as covariates that
   tilt allocator priors, never as binary position gates.

## Consequences

- Positive: nulls under 1.0's gate become admissible experts; the arsenal can
  legally contain every archived 1.0 hypothesis plus untested simple rules.
- Positive: statistical power concentrates where the capital decision is made.
- Negative/obligation: selection bias moves up a level, multiplied by arsenal
  size — ADR-0007's confirmation gates and ADR-0008's trial register are the
  compensating controls and are non-waivable.
- Obligation: allocator regret accounting requires counterfactual expert
  returns on every bar — forces ADR-0003 (shadow ledger) as a precondition.

## Alternatives considered

- **Retain 1.0 per-strategy gates and add a combiner on survivors.** Rejected:
  the survivor set is empty by construction; the gate destroys the rotor's
  input space.
- **Bandit formulation (learn only from the traded strategy).** Rejected:
  full-information regret is O(√(T ln N)) vs bandit O(√(T·N ln N))
  ([Auer et al. 2002](https://doi.org/10.1137/S0097539701398375);
  [Cesa-Bianchi & Lugosi 2006](https://doi.org/10.1017/CBO9780511546921));
  shadow execution makes full information available at data cost only.
- **State-conditional generative allocation (classify regime → allocate).**
  Rejected on 1.0's own evidence (H050 negative result); retained only as
  covariate tilting per Decision 5.

## References

- [Freund & Schapire 1997, J. Comput. Syst. Sci. 55:119-139](https://doi.org/10.1006/jcss.1997.1504)
- [Herbster & Warmuth 1998, Mach. Learn. 32:151-178](https://doi.org/10.1023/A:1007424614876)
- [Auer, Cesa-Bianchi, Freund & Schapire 2002, SIAM J. Comput. 32:48-77](https://doi.org/10.1137/S0097539701398375)
- [Hazan & Seshadhri 2009, ICML 2009:393-400](https://doi.org/10.1145/1553374.1553425)
- [Cesa-Bianchi & Lugosi 2006, *Prediction, Learning, and Games*, Cambridge UP](https://doi.org/10.1017/CBO9780511546921)
- [Grinold 1989, J. Portfolio Manage. 15(3):30-37](https://doi.org/10.3905/jpm.1989.409211)
- SKIE-Universe 1.0 H050 KPI report v1 (sibling repo,
  `research/01_hypothesis_register/H050/H050_kpi_report_v1.md`) — controlling
  negative precedent for regime-gating.
