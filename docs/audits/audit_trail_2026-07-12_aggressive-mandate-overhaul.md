# Audit Trail — Aggressive geometric-growth governance overhaul

**Deliverable:** Reframe SKIE-Universe 2.0 from risk-averse to optimism +
exponential (compounded/geometric) growth via a high-risk methodology
(principal-directed + approved 2026-07-12). Keystone **ADR-0013** installs
geometric growth (Kelly log-wealth) as the primary objective, sweeps the Kelly
fraction as a registered hyperparameter, demotes the lower-tail terminal-wealth
quantile to a monitored non-binding guardrail, cost-tunes discovery α looser,
loosens ADR-0002 admission, steepens the ADR-0010 ramp — and reaffirms the
overfitting/integrity core as **non-waivable and *more* binding under leverage**.
**Date:** 2026-07-12 · **Status:** all artifacts `proposed` (nothing enacted in
place; downstream ADRs carry non-invasive `amended_by: ADR-0013` banners, and
ADR-0013's amendment map is the authoritative change record).
**Mechanism:** `audit-remediate` Workflow, 3-round cap.

## Artifacts

New: `docs/decisions/ADR-0013-aggressive-geometric-growth-mandate.md`,
`docs/decisions/ADR-0012-standing-incumbent-allocator.md` (champion-challenger).
Reframed: `docs/methodology/allocator_metric_family_report_objects.md`, `README.md`,
`CLAUDE.md`, `config/multipletest_family.yaml`, `config/conditioning_covariates.yaml`,
both `reports/H900/*.md` (rationale-only), and `amended_by` banners on
ADR-0002/0004/0005/0007/0010.

## Central integrity finding (the load-bearing check — PASSED all three rounds)

Every round confirmed the reframe **preserved the overfitting/integrity core**:
DSR/PBO overfitting detection, the ADR-0007 matched-turnover random rotor, PIT
canaries, the ADR-0008 family-wise trial register, ReproLog, and the ADR-0003
shadow ledger remain **non-waivable**; SPA/StepM correction machinery is retained
(only the discovery-α *level* and the *objective* change); ADR-0001 Decision 5
(regime = conditioning covariate/prior-tilt, never a gate) is preserved verbatim.
The reframe is aggressive on sizing + discovery, unchanged on not deploying fake
edges. H900 report numbers/verdicts are unchanged (rationale-only).

## Round 1 (2026-07-12)

Routing: quant-auditor, literature-check, format-auditor. Verdicts:
literature-check **accept** (19 references Crossref/arXiv-verified — Kelly 1956,
MacLean-Thorp-Ziemba 2011, Hansen 2005, Romano-Wolf 2005, BH 1995, DSR, PBO,
White 2000, Politis-Romano/White/PPW, etc., no fabrication); quant + format
**proceed-with-remediation**. 3 majors (0 refuted) + 7 minors — all remediated.

| ID | Issue | Disposition |
|---|---|---|
| QUANT-1-1 | Kelly grid `{0.75,1.0,1.25}` floored **above** the estimation-error-adjusted growth optimum (MTZ + ADR-0005's own half-Kelly logic put it near 0.5); the sweep couldn't select the fastest-growing fraction → systematic over-betting. | **Fixed** — grid extended to **`{0.5,0.75,1.0,1.25}`** (brackets half-Kelly → leveraged); endpoints registered as an **output** of the calibration follow-up, not asserted. |
| QUANT-1-6 | The "self-penalizing / concave interior maximum, no cap needed" safety claim asserted without derivation; fails at 1.25× where `1+f·R≤0` is undefined-log ruin; no estimator exists yet. | **Fixed** — softened to "concave under standard single-period assumptions"; interior-max/grid-bracketing/ruin handling **to be derived** via new **BLOCKING** follow-up `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` (no swept fraction selected on geometric growth before it is frozen). |
| QUANT-1-2 / LITERATURE-1-1 / FORMAT-1-1 | ADR-0012 dead link `ADR-0013-geometric-growth-objective.md`. | **Fixed** → `ADR-0013-aggressive-geometric-growth-mandate.md`. |
| Minors QUANT-1-3/1-4/1-5, FORMAT-1-2/1-3 | grid open-inequality pin; Politis-Romano caption → geometric-growth-differential; "only α level" → acknowledge FWER→FDR criterion change + keep BH-PRDS/BY obligation; MTZ title standardized; CLAUDE ADR-0012 row added. | **All fixed.** |

## Round 2 (2026-07-12)

Routing: quant, literature, format. Verdicts: format **accept**; quant +
literature **proceed-with-remediation**. 2 majors (0 refuted) — **same root
cause** — + 2 minors. All remediated.

| ID | Issue | Disposition |
|---|---|---|
| QUANT-2-1 / LITERATURE-2-1 | The round-1 concavity/ruin softening + blocking-follow-up gate was applied to ADR-0013 but **not propagated to ADR-0012**, which still asserted "self-penalizes over-betting" categorically (contradicting the keystone) and left champion selection ungated. | **Fixed** — ADR-0012 Context, Decision 2, References caption, and Consequences now mirror ADR-0013's hedged wording ("penalized in expectation"; interior-max/ruin **to be derived**) and add the explicit gate: no swept fraction selected on geometric growth, no >1× dethroning certifiable, before `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` is frozen. |
| FORMAT-2-1 / FORMAT-2-2 | Kelly 1956 issue-number inconsistency (`35(4)` vs `35`); same propagation flagged for format. | **Fixed** — standardized to `35:917-926`; propagation resolved above. |

## Round 3 (2026-07-12) — ACCEPT

Routing: quant-auditor, literature-check, format-auditor. **All three branches
accept** → loop-level verdict **accept**. 0 majors, 0 refuted, 4 minors (fixed).

- **QUANT-3-1 / FORMAT-3-1** — ADR-0013 Consequences said the family expands "×3 grid points" but the grid has 4 `{0.5,0.75,1.0,1.25}`. **Fixed** → "×4 grid points".
- **QUANT-3-2** — CLAUDE.md's Kelly-fraction summary omitted the blocking-gate clause. **Fixed** — added the `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` selection block.
- **LITERATURE-3-1** — MTZ 2011 described as "collecting Thorp's applied work" (it's a multi-author edited volume). **Fixed** — "edited volume collecting the Kelly capital-growth literature (incl. Thorp's applied work)."

Round-3 verification confirmed: ADR-0012 ↔ ADR-0013 mutually consistent on the
concavity/ruin epistemic status (categorical claim grep = 0; blocking gate linked
in both); grid `{0.5,0.75,1.0,1.25}` consistent across both ADRs + config + CLAUDE;
Kelly citation standardized; and the **integrity core stated non-waivable in all
artifacts** (DSR/PBO, random rotor, PIT canaries, trial register, ReproLog,
shadow ledger; SPA/StepM retained).

### Final disposition

**Accepted** (round 3, all branches accept; no major survived any round). The
reframe is governance-faithful, internally consistent, integrity-core-preserving,
citation-valid, and zero-magic-number. All artifacts remain `proposed`; the two
BLOCKING calibration follow-ups gate enactment (see Residual risk).

## Residual risk (carried)

- **Governance prose constrains nothing numerically until implementation.** The
  geometric-growth estimator (metric G) does not yet exist; the mandate is a
  standing objective/parameterization contract. Two **blocking** follow-ups gate
  enactment: `P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE` (loosened α/δ/power,
  size increment, and confirmation of the grid endpoints) and
  `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` (interior maximum, grid bracketing,
  ruin handling on the shadow-ledger fat-tailed distribution). No swept Kelly
  fraction is selected on geometric growth, and no loosened target is enacted,
  before both memos are frozen with ReproLogs.
- **All artifacts are `proposed`;** downstream ADRs are not edited in place.
  Enactment of the amendment map awaits acceptance.
