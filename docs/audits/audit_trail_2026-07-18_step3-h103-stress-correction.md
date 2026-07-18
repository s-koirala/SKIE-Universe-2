# Audit trail — Step 3: H103 stress-record correction (2026-07-18)

**Deliverable:**
[expert_card_v3.md](../../research/01_hypothesis_register/H103/expert_card_v3.md)
(append-only correction of record; no new computation; register increment 0),
the H103 correction addendum in
[retro_card_register_2026-07-10.md](../research_notes/retro_card_register_2026-07-10.md),
the `construction_dependence_note` under `realized_vol_percentile` in
[conditioning_covariates.yaml](../../config/conditioning_covariates.yaml),
an annotation comment (record unchanged) in the `rc-h103-1` family of
[multipletest_family.yaml](../../config/multipletest_family.yaml), and the
UNRESOLVED qualifier on the H103 row of
[hypothesis_backlog.md](../../hypothesis_backlog.md). (The matching qualifiers
in CLAUDE.md and the backfill plan ride with the step-4 living-note commit.)

**Standing statement corrected to:** UNRESOLVED — a sign flip under a leakage
repair (RC-1 leaked full-sample cutoff: −5.0922e-04/session, n=437, stat
−0.8404277792603854 vs RC-2 leakage-clean per-origin: +1.0295e-04/session,
n=313, stat +0.1544010591430268; both re-verified against the primary JSONs
this session), on 28% less data; not corroboration; not powered to resolve
the prior. Both records stand append-only.

**Mechanism:** audit-remediate workflow, round 1 of max 3 (run
`wf_71dd472f-bb8`; routed branches: quant-auditor, literature-check,
format-auditor).

**Round-1 verdicts:** quant-auditor proceed-with-remediation (minors only);
literature-check accept; format-auditor accept. Zero critical, zero major —
loop exits at round 1; all minors below were nonetheless applied PRE-COMMIT
(the card was still uncommitted, avoiding an immediate v4).

## Findings and dispositions (all minor)

| ID | Location | Issue (abbrev.) | Disposition |
|---|---|---|---|
| QUANT-1-1 | v3 §2/§8; covariate note | Causal attribution overstated: the sign flip is confounded with session coverage (RC-2 classifies 1549 of 2276 ES sessions; ~700 early sessions never classified), not attributable to boundary leakage alone | **applied pre-commit** — v3 now states both difference axes (boundary estimation AND session coverage), "not attributable to boundary leakage alone; a matched-sample decomposition has not been run"; register addendum matched |
| QUANT-1-2 | v3 §2/§8; register addendum | Blanket "not powered" unreconciled with the design-registered n ≥ 174 floor (both records clear it at the design effect size) | **applied pre-commit** — "not powered to resolve it": powered null at the design effect size, unpowered for the far smaller observed effect |
| QUANT-1-3 | working tree | Step-3 change set not isolated (roadmap/CLAUDE.md/plan carry step-4 edits) | **applied by process** — step-3 commit stages exactly the five step-3 surfaces; step-4 edits committed separately |
| LITERATURE-1-1 | v3, addendum, covariate note | "Lundström high-vol-concentration prior" label: the 2013 FRL abstract shows large-move-day/intraday-momentum concentration, not the ex-ante volatility-state form (that derives from Lundström's separate working paper); unpinned-paraphrase flag (full text unretrievable, 403) | **applied pre-commit** — provenance clarifier added to v3 §8.1; frozen surfaces untouched |
| FORMAT-1-1 | register addendum | Withdrawal clause quoted the frozen digest non-verbatim (silent elision) | **applied pre-commit** — verbatim quotation restored with an explicit note that the quoted verb is the withdrawn 1.0-era claim |

## Post-remediation verification

- Both YAMLs parse; the `rc-h103-1` register RECORD lines are byte-unchanged
  (only a comment block added); `expert_card_v2.md`, the RC-H103-1
  disposition memo, frozen design.md, and the frozen screen addendum are
  untouched (git diff clean on all four).
- Every quoted figure re-verified against
  `reports/H103/rc_h103_1_scan.json` / `rc_h103_2_screen.json` (exact).
- No pool disposition changed; no enacted numeric changed; no register
  increment (no scan ran); nothing certified.

## Residual risk

The RC-H103-2 screen pipeline itself was not re-executed this round — the
correction card inherits any latent upstream error in those artifacts (they
carry their own 2-round audit accept). The leakage-vs-coverage decomposition
of the sign flip is explicitly left OPEN (matched-sample diagnostic not run);
any future claim attributing the flip to leakage alone requires that
pre-registered diagnostic first.
