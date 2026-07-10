# Audit trail — Founding governance (ADR-0001..0010, Expert Card template, CLAUDE.md)

- **Date:** 2026-07-10
- **Deliverable:** 10 founding ADRs under [docs/decisions/](../decisions/), [expert_card_TEMPLATE.md](../templates/expert_card_TEMPLATE.md), CLAUDE.md founding-governance section
- **Mechanism:** audit-remediate-loop, Workflow engine (`workflows/audit-remediate.js`), 3 rounds (cap reached by design, exit on accept)
- **Routing (deterministic):** quant-auditor + literature-check per round; refute gate on every critical/major
- **Workflow run IDs:** R1 `wf_2c3150b5-e49`, R2 `wf_902d0296-c7d`, R3 `wf_90757ffc-7ec`
- **Final verdict:** **accept** (both branches, round 3); 0 findings refuted across all rounds

## Round 1 — 8 majors confirmed (0 refuted), all remediated

| ID | Location | Defect | Disposition |
|---|---|---|---|
| QUANT-1-1 / LITERATURE-1-2 | ADR-0001 | Garivier-Moulines 2011 (bandit D-UCB/SW-UCB) cited inside the full-information experts class the ADR itself rejects | Remediated: replaced with Cesa-Bianchi & Lugosi 2006 §2.11 discounted regret + Hazan & Seshadhri 2009 adaptive regret; G&M retained only as explicitly-labeled out-of-scope bandit analogue |
| QUANT-1-2 / LITERATURE-1-1 | ADR-0002 | STW 1999 attribution inverted (best rule survives Reality Check in-sample 1897–1986; fails OOS 1987–1996) | Remediated: corrected to in-sample-survives/OOS-decays — strengthens the transient-edge premise |
| QUANT-1-3 / LITERATURE-1-5 | ADR-0007 | "SPA over the benchmark family" inverts Hansen 2005 roles (family = candidates, benchmark = single) | Remediated: one SPA per ladder benchmark, family = allocator configurations from trial register, intersection-union across 5 tests |
| QUANT-1-4 | ADR-0008/0007 | DSR/PBO specified on a raw trial count — neither computable from a count | Remediated: register schema extended to per-trial records (SR estimate, return-series pointer, clustering metadata for N_eff); DSR uses (N_eff, V[SR]), PBO uses trial matrix via CSCV |
| QUANT-1-5 | ADR-0005/0004/0010 | q05 level a hand-set constant binding the Kelly fraction and leverage ceiling | Remediated: registered lower-tail-quantile level derived from a risk-tolerance declaration (MacLean-Thorp-Ziemba constrained growth), quantile sweep as sensitivity |
| QUANT-1-6 | ADR-0002 (c) | BH offered without dependence conditions (PRDS not automatic for overlapping cells) | Remediated: Romano-Wolf default; BH only with documented PRDS argument; else Benjamini-Yekutieli 2001 (cited) |
| QUANT-1-7 | ADR-0010 | Promotion on failure-to-reject (inverted burden; noisy windows promote easiest) | Remediated: Schuirmann 1987 TOST equivalence test, pre-registered margin δ from cost-model tolerance, window length powered against δ |

Round-1 minors folded in (co-located with major edits): QUANT-1-8/LITERATURE-1-4 (Politis-Romano 1994 + Politis-White 2004 + Patton-Politis-White 2009 citations, ADR-0004); QUANT-1-13/LITERATURE-1-6 (Kelly median claim corrected); QUANT-1-14/LITERATURE-1-7 (PBO DOI 10.21314/JCF.2016.322 Crossref-verified; follow-up `P1-2.0-CITE-DOI-VERIFY-PBO-2017` closed).

## Round 2 — 3 majors confirmed (0 refuted), all remediated; 6 minors (all regressions/residues of round-1 fixes) also remediated

| ID | Location | Defect | Disposition |
|---|---|---|---|
| QUANT-2-1 | ADR-0007 | Per-benchmark SPA establishes existence of an outperformer, not identity of the eligible configuration | Remediated: Romano-Wolf StepM identification step per benchmark; nominated configuration must lie in the FWER-controlled outperformer set for all five benchmarks |
| QUANT-2-2 / LITERATURE-2-1 | ADR-0004/0005 | Three residual q05 literals survived the round-1 purge | Remediated: repo-wide grep for `q05` returns zero matches |

Round-2 minors remediated as regression completions: QUANT-2-3 (Kelly rationale: mean monotone, median peaks at full Kelly, lower-tail quantile peaks strictly earlier); QUANT-2-4 (TOST at level α ↔ 100(1−2α)% CI); QUANT-2-5/LITERATURE-2-2 (template correction enum three-way); QUANT-2-6 (RW bootstrap requires serial-dependence-preserving resampling); LITERATURE-2-3 (FDR-target → screening error-rate target).

## Round 3 — accept (0 critical/major); 6 minors logged

Applied post-accept as consistency completions (mechanical, grep-verifiable; **not re-audited** — flagged per cap rule):

- QUANT-3-2/LITERATURE-3-1: CLAUDE.md scope line updated to include Romano-Wolf StepM in the confirmation gate.
- LITERATURE-3-2: Garivier-Moulines mention pinned to proceedings DOI 10.1007/978-3-642-24412-4_16.
- QUANT-3-1: ADR-0005 rationale now states horizon dependence of the quantile-optimal fraction (interior peak iff full-Kelly > |z_q|/(σ√T)); risk-tolerance declaration freezes horizon T alongside the quantile level (auditor numerically verified the GBM algebra).
- QUANT-3-3: ADR-0010 α and power target selection bound to the ADR-0002 (c) error-rate-cost analysis framework.
- QUANT-3-4: stub schemas committed at [config/multipletest_family.yaml](../../config/multipletest_family.yaml) and [config/burned_data_ledger.yaml](../../config/burned_data_ledger.yaml); template link now resolves.

## Open (logged, not remediated — invitesPolish=false)

- QUANT-1-9/LITERATURE-1-8: template §5/§7 YAML machine-readability gaps vs ADR-0009 §3 (§5 free-form; §7 table-only).
- QUANT-1-10: `fold-unstable` failure mode lacks a disposition in the ADR-0009 taxonomy.
- QUANT-1-11: ADR-0003 full-information claim is exact at Tier 0, model-conditional at Tiers 1–2 — conditionality unstated.
- QUANT-1-12: CUSUM/BOCPD parameter-selection procedure (ARL0/detection-delay trade-off) undefined in ADR-0004; ADR-0010 cross-reference dangles until it lands.
- LITERATURE-1-3: marginal-contribution machinery should cite Grinold & Kahn (book) rather than Grinold 1989 (fundamental-law article).

## Residual risk (recorded per post-loop step)

Governance prose constrains nothing numerically until implementation: the SPA/StepM/DSR/PBO constructions, the registered quantile level + horizon, TOST α/power calibration, and the per-trial register schema exist as ADR text and stub YAML only. First implementations must be re-audited against these corrected specifications (auditor verdict, both branches). Citation risk is low: ~30 unique citations verified against Crossref/primary metadata across rounds; sole unresolved items are two practitioner-book page checks (ISBN-matched, tier-labeled) and the CBL 2006 §2.11 pointer (confirmed from table of contents, publisher page does not expose sections).
