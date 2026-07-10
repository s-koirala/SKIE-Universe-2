---
name: ADR-0009 — Expert Card as the mandatory terminal deliverable
description: Every hypothesis test terminates in an eight-section machine-readable Expert Card; the word "fail" is not a disposition
type: process
status: accepted
date: 2026-07-10
supersedes: "SKIE-Universe 1.0 pass/fail KPI disposition convention (sibling repo; not amended in place)"
superseded_by: ""
---

# ADR-0009 — Expert Card as the mandatory terminal deliverable

## Context

1.0's terminal deliverable (KPI report card, ADR-0013/0014 lineage) served a
binary deployment question and collapsed nulls to one bit, discarding the
structure that 2.0 consumes: *why* the strategy failed, *where* it had
conditional edge, and *what* it contributes to an ensemble. The user
directive (2026-07-10) mandates a templated deliverable replacing "fail" as
an agent report. The Expert Card is that deliverable; its consumer is the
allocator layer and future hypothesis design, not only the operator.

## Decision

1. Every hypothesis test — expert, position-policy, or allocator
   configuration — terminates in an **Expert Card** rendered from
   [docs/templates/expert_card_TEMPLATE.md](../templates/expert_card_TEMPLATE.md),
   stored at
   `research/01_hypothesis_register/{HID}/expert_card_v{N}.md`.
2. **Eight mandatory sections**, in order:
   1. **Provenance header** — HID, design.md SHA-256, ReproLog run_id(s),
      data span, instruments, execution tier (ADR-0006), trial-register
      increment.
   2. **Failure-mode decomposition** — pre-cost edge with CI; net edge; cost
      share of gross; classification among: no-gross-edge / cost-bound /
      fold-unstable / conditional-only / execution-bound, with the binding
      numbers for each determination.
   3. **Conditional-edge panel** — edge per pre-declared conditioning cell
      (ADR-0002 (b)), multiplicity-corrected CIs, correction method and
      family reference.
   4. **Ensemble block** — net-of-cost residual correlation vs each current
      arsenal member; marginal-IR estimate vs the spanned arsenal.
   5. **Stability profile** — rolling-window edge series; CUSUM/BOCPD
      change-point dates; estimated edge half-life where decay is detected.
      This section is what distinguishes *decayed* from *never-worked*.
   6. **Disposition** — exactly one of: `deploy-candidate` /
      `arsenal-admit-conditional` / `arsenal-admit-diversifier` /
      `re-specify-cost-bound` / `re-specify-execution-bound` /
      `archive-no-gross-edge`, with the numeric criterion that bound it.
      The strings "pass" and "fail" are prohibited as dispositions.
   7. **Burned-data entry** — OOS spans consumed, mirrored to
      `config/burned_data_ledger.yaml` (ADR-0008).
   8. **Priors update** — at most five structured lines stating what this
      result constrains for queued hypotheses.
3. **Machine-readability.** Sections 1, 3, 4, 6, 7 carry YAML frontmatter or
   fenced YAML blocks with a stable schema; the allocator admission file is
   *generated* from sections 3–5 by script, never hand-copied.
4. Cards are **append-only** (ADR-0008): re-evaluation of the same expert
   emits `expert_card_v{N+1}` cross-linking its predecessor.
5. **Retro-carding.** 1.0's H050, H052a, H053, H054, H055 receive
   retroactive Expert Cards generated from their existing KPI report cards,
   as the first admission candidates and the dry run of the template.
   Registered as follow-up `P1-2.0-RETRO-CARD-1.0-REGISTER`.
6. Numeric values in a card must agree with the underlying run sidecars;
   cross-cell agreement is checked at every audit round (lifting 1.0's
   ADR-0014 cross-cell discipline).

## Consequences

- Positive: every outcome including archive produces reusable, queryable
  evidence; the "priors update" section compounds across hypotheses.
- Positive: agent sessions report a disposition taxonomy, never a bare
  verdict.
- Negative: heavier terminal deliverable than a verdict; mitigated by the
  template and by script-generated sections.
- Obligation: template schema changes are ADR-level decisions (they break
  the generated admission files).

## Alternatives considered

- **Extend the 1.0 KPI report card with extra sections.** Rejected: its
  9-table core answers a standalone-deployment question 2.0 no longer asks;
  carrying it forward would re-center evidence on the abolished gate.
- **Database rows instead of markdown cards.** Rejected for now: markdown +
  YAML keeps cards reviewable in audit loops and diffable in git; a derived
  database view can be added without changing the canonical artifact.
- **Free-form findings memos.** Rejected: non-machine-readable, and the
  allocator admission path would reintroduce hand-copying errors.

## References

- SKIE-Universe 1.0 ADR-0013 / ADR-0014 (report-card lineage; sibling repo).
- [ADR-0002](ADR-0002-arsenal-admission-standard.md), [ADR-0004](ADR-0004-rolling-evaluation-regime.md), [ADR-0005](ADR-0005-three-layer-separation.md), [ADR-0008](ADR-0008-integrity-non-negotiables.md)
- Template: [docs/templates/expert_card_TEMPLATE.md](../templates/expert_card_TEMPLATE.md)
