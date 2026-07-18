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


---

# Phase-2b/2c screen-results loop (separate deliverable; fresh audit budget)

Deliverables: RC-H101-2 / RC-H103-2 screen artifacts (both SCREEN PASS →
provisional pool, verdict deferred), Expert Cards v2 (script-generated), the
first pool-ledger materialization (8 records), per-cell register trials.
Workflow runs: round 1 `wf_551bba80-688`, round 2 `wf_b1be4d18-07d`.

## Round 1

Refute gate: 15 findings across branches — 6 distinct majors — all survived
refutation (none refuted). All REMEDIATED:

| Distinct defect | Disposition |
|---|---|
| Hardcoded §8.2 pass-prose contradicted the H103 passing set (calm cell described as high-vol) | prose now COMPOSED from the artifact's passing set via a declared cell→mechanism map |
| Missing growth windows encoded as the JSON string "nan" inside numeric arrays (screen artifacts + pool records) | sanitizer nan→null; both screens deterministically re-run (identical passing sets; new ReproLogs 7804ac45… / b257f65c…); pool records re-emitted with nulls |
| Pool append not idempotent (re-runs would duplicate the append-only ledger) | key-based duplicate guard + skip notices (verified by a live re-run: 0 appended) |
| Cards claimed +10 register records while rc-*-2 `trials` were empty (ADR-0008 D6 gap) | 10 per-cell trial records appended per family (sharpe, artifact ref, clustering metadata) |
| Pool records drifted from the pool_ledger_schema field names/roles | schema names emitted (screen_alpha_ref/dsr_bound_ref/pbo_bound_ref pointers, detection_latency_bars with structural-lag semantics, selectable; VERDICT-tier blocks null-marked) |
| H103 card silent on the leakage-clean construction REVERSING RC-1's ES-stress headline | Construction-dependence exhibit injected from both artifacts into §2 |

Minors fixed: estimable/total window coverage, significance/direction split
from the S-c conjunction, full freeze-verified design SHA-256 in frontmatter,
ReproLog-sourced screened_at (2026-07-18 UTC — the runs crossed UTC
midnight), RC-1 net notes injected from the rc_xcorr1 artifact block, derived
counts, and/or idiom removed, burned-data reference by recorded_at.
Accepted-not-fixed (recorded): the generator carries no unit tests
(CODE-1-10); the DSR gate binds at raw N = 20 with the correlation-adjusted
N_eff reported (the addendum-registered gate choice; QUANT-1-4); positional
instrument indexing (CODE-1-4).

## Round 2 (`wf_b1be4d18-07d`)

Verification of the round-1 remediation. 2 distinct majors found IN the
round-1 remediation itself; both survived the refute gate (none refuted) and
were REMEDIATED post-round:

| Distinct defect | Disposition |
|---|---|
| CODE-2-1/QUANT-2-2: `_net_note` read guessed rc_xcorr1 keys (`net_sr_h101`/`residual_ir`) absent from the RC-1 artifact (actual: `sharpe_h101`/`sharpe_h103`/`residual_information_ratio`), silently rendering "n/a" while the card claimed artifact-derived net values | fail-closed rewrite on the ACTUAL artifact keys (missing key → raise); H103 §2 now renders ES −0.0164/−0.0238/IR −0.0179, NQ 0.0144/0.0113/IR 0.0000 |
| QUANT-2-1: both cards hardcoded "reproduces RC-1 bit-identically" — FALSE for H103, where the certified leakage-clean per-origin construction changes 4/10 cells (ES:stress mean flips sign) | `_reproduction_claim()` DERIVES the claim per card by comparing (stat, n) tuples across RC-1/RC-2 artifacts at `_STAT_IDENTITY_TOL = 1e-9`; H101 renders 10/10 bit-identical, H103 renders 6/10 + the named 4-cell diff set attributed to the construction |

Minors fixed: n_gate fail-closed guard, `_fmt` bool exclusion, register
trials' `return_series_ref` dual-ref (ledger partition family + screen
artifact as cell-mask reference; the 20 appended records text-patched to
match), three-state register-family-missing error handling.
Accepted-not-fixed (recorded): hardcoded DATA_SPAN/ledger-slice constants as
registered record-shape choices (CODE-2-5); pool idempotency key without an
adjudication-event id — first-adjudication-only ledger by design;
re-adjudication events append with a changed `last_adjudicated_against`
(QUANT-2-3); dirty-tree screen runs with `working_tree_hash` recorded — the
provenance commit lands this session (REPRODUCIBILITY-2-2); card `screened_at`
2026-07-18 = ReproLog UTC date (runs crossed UTC midnight), derived-by-design.

## Round 3 (`wf_ab38cd03-84f`) — ACCEPT

Narrow verification of the round-2 remediation; all four routed branches
(code-reviewer, quant-auditor, reproducibility-verifier, literature-check)
returned ACCEPT with zero critical/major findings. Both round-2 majors were
verified against the primary artifacts by independent recomputation (not
prose): H101 10/10 (stat, n) tuples identical between RC-1/RC-2; H103 6/10
with diff set exactly {ES:stress, ES:non_stress, NQ:stress, NQ:non_stress}
(e.g. ES:stress n 437→313, stat −0.8404→+0.1544); H103 §2 net values
reconciled to `rc_h103_1_scan.json` `rc_xcorr1` at 4-dp (NQ residual IR
0.0000 = faithful rounding of +1.879e-05). Register dual-ref YAML validated;
all round-2 minors confirmed in place; no regression in round-1 properties
(idempotency, schema names, null growth encoding, composed §8.2, exhibit).

2 new minors logged, NOT remediated (dormant; unreachable on current
artifacts; post-accept churn declined): CODE-3-1 — `_reproduction_claim`
fail-open on zero RC-1/RC-2 key overlap (renders "0/0 cells" instead of
raising); QUANT-3-1 — the non-identical branch hardcodes the leakage-clean
construction attribution for ALL diff cells rather than restricting to a
declared construction-changed set. Both spun off to a follow-up task.

## Final disposition — Phase-2b/2c loop

Exit at round 3 on unanimous ACCEPT (0 critical/major; cap reached).
Cumulative: 8 distinct majors over rounds 1–2, all remediated and re-verified;
0 findings refuted at the gate in any round. Residual risks: the screen
passes are POOL entries only — verdict-tier objects (net/cost non-redundancy,
marginal geometric growth, Kelly-fraction selection) remain unadjudicated;
the enacted screening level's looseness is licensed by the non-waivable
verdict ladder that has not yet run; generator carries no unit tests; the
S-c "bit-identical" wording rests on the 1e-9 tolerance (for H101 the JSON
representations are in fact string-identical).
