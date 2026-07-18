# Audit trail — Phase-1 numeric calibrations + Phase-2a screen protocol (2026-07-17)

Deliverable package: the three BLOCKING numeric instantiations
(`P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE`,
`P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`, `P1-2.0-H900-BOCPD-WHITENED`
on-ledger) + the ADR-0014 screen-protocol freeze (RC-H101-2 / RC-H103-2
addenda, harness, register/ledger repairs). Audit mechanism: the
audit-remediate Workflow (5 specialist branches — quant-auditor,
code-reviewer, literature-check, reproducibility-verifier, format-auditor —
with the adversarial refute gate), 3-round cap.

Workflow runs: round 1 `wf_ff39d792-1d9`, round 2 `wf_7e19cf06-f59`, round 3
recorded below.

## Round 1 (scope: 1a/1b runners, memo addenda, config enactment, artifacts)

Refute gate: 7 major findings across branches — 6 distinct defects — all
survived refutation (none refuted). Disposition REMEDIATED for all:

| ID | Sev | Finding (condensed) | Disposition |
|---|---|---|---|
| QUANT-1-1 (+LITERATURE-1-1) | major | Enacted t\* (lfdr-scale MPRR cutoff) transplanted onto RW-adjusted-p / DSR / PBO scales with no bridge | REMEDIATED: documented as a GOVERNANCE scale-transfer deviation (memo §A.6.2); p/DSR/PBO applications marked provisional operational proxies (§A.7); re-derivation registered (§A.8.4) |
| QUANT-1-2 (+REPRODUCIBILITY-1-1) | major | A.5/A.6 misstated the empirical-bridge degeneracy direction (claimed admit-nothing; artifact shows 14/14 admitted, bridge = Efron pi0 = 0.0885) | REMEDIATED: A.5/A.6.1 + script docstring corrected to the admit-everything account grounded in the RD3 red flag |
| QUANT-1-3 | major | H_dem "structural one-window upper bound" assumed certain demotion (ADR-0012 dethroning non-operational); conservatism inverted | REMEDIATED: H_dem re-cast as a banded assumption axis {1,2,4} windows inside the enactment band |
| QUANT-1-4 | major | r_backstop treated the mechanically-censored 2/2 gate record as an empirical rate | REMEDIATED: re-classified as a censored-record PRIOR, banded {0, 0.3332}; live-outcome replacement registered (§A.8.2) |
| FORMAT-1-1 | major | Stale "(null)/DEFERRED" level comments contradicting the enactment inside multipletest_family.yaml | REMEDIATED: comment sweep |
| — net effect | | | enacted level moved 0.8693 → **0.7401** (median of the expanded 24-point band) |

Minors (18) triaged: fixed — `norm.sf` idiom, CI_ALPHA-derived quantiles,
JSON non-finite sentinels, kelly notes-override + three-state grid-top
verdict, PRDS sufficient-condition wording, Jeffreys 2.5th-percentile label,
RD5 N>20 conditional flags, bootstrap partial/drop counters, B.2
zero-imputation note, harness-import spec guard, quadrature/clamp justify
comments. Accepted-not-fixed (logged): CODE-1-1 (checksum-helper duplication
across the two calibration runners — dedup deferred; recorded residual).

## Round 2 (scope extended: + whitened-ROC runner/artifact/memo §C, screen addenda + harness, register/ledger repairs)

Refute gate: 9 major findings across branches — 6 distinct defects (the
stale-level comment was reported by four branches) — all survived refutation
(none refuted). Disposition REMEDIATED for all:

| ID | Sev | Finding (condensed) | Disposition |
|---|---|---|---|
| CODE-2-1 (+FORMAT-2-1, LITERATURE-2-1, REPRODUCIBILITY-2-1) | major | rc-h101-2 pre-registration comment restated the superseded 0.8693 level | REMEDIATED: comment now cites 0.7401-at-registration with the full-precision config value governing |
| QUANT-2-1 | major | Hazard grid never reached the declared 0.5 ceiling (top 0.316) while best-net sat at the boundary — the UNATTAINABLE verdict rested on an unexplored region | REMEDIATED: grid extended with 10^-0.375 and the 0.5 ceiling; full re-run and re-emission |
| QUANT-2-2 | major | The net "95% box" (Bonferroni Wilson difference, coverage ≥90%) was verdict-determining: under the calibrated Newcombe interval the NQ noise-ceiling point qualifies (L=1) | REMEDIATED: calibrated Newcombe (1998) MOVER interval + the MAJORITY-COHERENCE floor (fp < alarm_prob, the registered Bayes 0-1-loss majority standard) as emission rule v2 — excludes the degenerate always-alarm corner on principle |
| QUANT-2-3 | major | H103 label join relied on unguaranteed polars row order (silent misalignment risk at a leakage-critical boundary) | REMEDIATED: `maintain_order="left"` + row-count guard + all arrays re-extracted from the joined frame |
| QUANT-2-4 | major | The masked-matrix PBO "rank-preservation" claim is false when member densities differ (√density Sharpe shrinkage) | REMEDIATED: NaN-masked matrix + member-only Sharpe `score_fn`; the addendum claim retracted and replaced |
| REPRODUCIBILITY-2-2 | major | Screen ReproLog bound only the addendum + ROC artifact, not the evaluation substrate or the level-supplying config | REMEDIATED: substrate manifest checksums + multipletest_family.yaml SHA merged into the screen ReproLog |

Minors (12) triaged: fixed — JSON sanitizers in both new runners, orphaned
justify comment, Expr-only train-boundary filter, sys.modules registration
in the harness loader, unconsumed SEED_SD removed (S-d/S-e are
deterministic; addenda corrected), growth-series buckets moved to the
registered h900 evaluation windows, S-e structural-vacuity acknowledgement
(the gate cannot bind for the registered rule-based cells; its
discriminating power is reserved for latent-state cells), noise-ceiling
qualifier propagation, dirty-tree provenance note (see residuals).
Accepted-not-fixed (logged): CODE-2-5 residue (private-API coupling of the
screen harness to the RC-H101-1 harness — single-source-of-truth trade-off
recorded; promotion to a shared src/ module deferred).

## Round 3 (wf_d7e582ad-27b; FINAL under the cap)

Branch verdicts: literature-check ACCEPT, format-auditor ACCEPT;
code-reviewer / quant-auditor / reproducibility-verifier
proceed-with-remediation. Refute gate: 5 major findings across branches — 2
distinct defects, both LATENT in the not-yet-run screen runner — survived
refutation (none refuted). REMEDIATED post-round and verified by direct
behavioral checks (no artifact regeneration required; the screens had not
executed):

| ID | Sev | Finding (condensed) | Disposition |
|---|---|---|---|
| CODE-3-1 (+QUANT-3-1, REPRODUCIBILITY-3-1) | major | The screen runner's round-2 JSON sanitizer was dead code (defined, never called at the write site; no allow_nan=False) | REMEDIATED: `_json_sanitize(result)` + `allow_nan=False` wired at the artifact write; verified by AST/content check |
| CODE-3-2 (+QUANT-3-2) | major | The REGISTERED correlation-adjusted N_eff diagnostic NaN'd out (np.corrcoef on the NaN-masked matrix; disjoint cells void every pair) | REMEDIATED: pairwise-COMPLETE member-overlap correlations (>= 2-session overlap per pair; explicit null + reason when no pair is estimable), emitted per instrument |

Minors: fixed — the round-2 Expr-only train-filter replacement had silently
missed (exposed as F821 when the stale Series was removed; now truly
Expr-only), Newcombe DOI + MOVER-label anachronism note added to memo §C.1
(the hybrid-score construction is Newcombe 1998; "MOVER" is Zou & Donner
2008's later generalization — the artifact field name `net_mover95` keeps
the later label, noted), the runner docstring's amendment-trigger record
bracketed as historical (the final sweep's NQ shoulder has a calibrated-
positive CI but fails floor (ii)), artifact-key predicate clarified in §C.1
(`hazards_with_net_ci_including_zero` = the no-significant-positive set,
lower bound <= 0), and this trail's round-1/2 counting reconciled.
Accepted-not-fixed (recorded): the `net_mover95`/`hazards_with_net_ci_
including_zero` key names retained in the emitted artifact (renaming would
force a ~2 h deterministic re-run for cosmetics; predicates documented),
run_screen main() length + closure hoist (CODE-3-3/CODE-3-4 style points;
ruff-clean), S-e vacuity-acknowledgement wording variants
(QUANT-3-5/REPRODUCIBILITY-3-2 — the substantive acknowledgement is in both
addenda).

**Exit state: no unresolved critical/major findings. The 3-round cap is
reached; the accepted residuals above and the §Standing residual risks are
surfaced to the operator rather than iterated further.**

## Standing residual risks

1. The enacted level's scale transfer (posterior-null t\* applied to
   RW-p/DSR/PBO gates) is a governance proxy, re-derived at the §A.8
   re-instantiation — not a statistical identity.
2. The r_backstop/H_dem axes are priors/assumptions banded into the level,
   not measurements; live-vs-shadow outcomes replace them when they exist.
3. All Phase-1 runs executed on a dirty working tree (recorded
   `working_tree_hash` binds content; the provenance commits landing this
   session close the loop) — bit-identical reproduction from HEAD alone is
   possible only after those commits.
4. The kelly grid-bracketing verdict is inconclusive-on-null-ledger; both
   calibrations re-instantiate at the first admission.
5. CODE-1-1 / CODE-2-5 helper-duplication and private-API coupling residues
   (deferred refactors, recorded).
