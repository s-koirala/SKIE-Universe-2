# Audit trail — OD-G deliverables argument-validity audit (findings-only)

- **Date:** 2026-07-19
- **Deliverables (audited as one argument set):**
  [docs/decisions/ADR-0016-tier2-execution-fidelity-scoping.md](../decisions/ADR-0016-tier2-execution-fidelity-scoping.md) (proposed),
  [docs/research_notes/od_g_spread_liquidity_setup_plan_2026-07-18.md](../research_notes/od_g_spread_liquidity_setup_plan_2026-07-18.md),
  [docs/research_notes/databento_pull_spec_cost_sheet_2026-07-18.md](../research_notes/databento_pull_spec_cost_sheet_2026-07-18.md)
- **Task framing:** operator reported controversy and opposing viewpoints
  regarding OD-G and directed a critical inspection of the validity of the
  arguments as described in the deliverables. **Findings-only round:** the
  deliverable of this audit is the assessment; no artifact was edited.
  Remediation of the confirmed findings is an operator decision (several fixes
  touch a proposed principal-only ADR and the semantics of an accepted ADR).
  **Superseded later the same day:** the principal authorized remediation and
  governance updates (2026-07-19 direction); rounds 2–3 below record the
  remediation and its verification, and ADR-0016 was **accepted by that
  direction** after the round-1 ADR-body fixes were applied.
- **Mechanism:** audit-remediate-loop → Workflow engine
  ([workflows/audit-remediate.js](https://github.com/s-koirala/dotfiles)),
  run `wf_4e13a5bc-a6e`, 15 agents (2 specialist branches + 13 adversarial
  refuters, one per critical/major finding), 0 errors.
- **Rounds:** 3 of 3 (cap) — round 1 findings + refute gate (run
  `wf_4e13a5bc-a6e`); round 2 verification, 3 residual majors + 3 minors (run
  `wf_4a55c455-fdd`); round 3 **accept / accept, zero findings** (run
  `wf_32b8f9cd-bf1`) — clean exit at the cap.
- **Routing:** quant-auditor (high effort), literature-check (high effort).
  `.md`-only artifact set → no code-reviewer; flags: statistical + citations
  on, repro + identity off.

## Round 1 — confirmed findings (survived the adversarial refute gate)

12 findings survived; 0 critical, 12 major. Two defect pairs were found
independently by both branches (QUANT-1-11 ≡ LITERATURE-1-2; QUANT-1-12 ≡
LITERATURE-1-1), so the 12 findings describe **10 distinct defects**, 2 of
them double-confirmed. Disposition for all (updated later the same day,
post-authorization): **remediated in place** — every proposed fix below was
applied; three were applied incompletely at first and completed after round 2
(QUANT-2-1/-2/-3 below).

| ID | Sev | Category | Refute gate | Finding (condensed) | Proposed fix |
|---|---|---|---|---|---|
| QUANT-1-2 | major | method | not refuted (reproduced; grep over ADR-0016 for `go/no-go|no-go|declin` = 0 hits) | Plan §6 (and §4/§7) key the OD-G decision gate on "ADR-0016 stage A (the operator's go/no-go on acquiring a Tier-2 substrate)", but ADR-0016 D6 defines stage A as scoping-only ("scope + ADR (no spend). This document.") with the spend decision at stage B; the ADR defines no substrate go/no-go event and no dated NO-GO/decline object at any stage, so gate-table rows 3–5 (GO/NO-GO cells) bind on objects that do not exist. Only the "Undecided" rows currently resolve. | Re-key plan §4/§6/§7 to actual ADR-0016 objects (GO = named, dated stage-B authorization); add an explicit dated "stage-B declined / not scheduled" terminal object to ADR-0016 or key the NO-GO rows to a principal statement outside the ADR. |
| QUANT-1-3 | major | assumption | not refuted (quotes reproduce; no numbered decision resolves promotion-vs-successor; ADR-0016 D3 leans the *opposite* reading) | ADR-0016's load-bearing DATA-BURN ORDERING Obligation ("dead … including the Tier-2 evaluation of the same mechanism") extends ADR-0008 D5 ("successor hypotheses") to the same-mechanism case — i.e. presumes the successor-HID answer to the promotion-vs-successor question that plan §§1/7 flag as OPEN and say ADR-0016 should resolve. ADR-0016 resolves it nowhere. The cheapest-decision-timing argument survives; the span-death claim is presented as rule while it is one of two open readings. | Add a numbered decision resolving promotion-vs-successor (e.g. unchanged estimand = same HID + declared span-freshness rule; changed estimand = new HID under ADR-0008 D5) and derive the Obligation from it. Same fix covers E-d's extension of D5 to fill-model calibration spans (calibration is not an HID under the D5 text). |
| QUANT-1-4 | major | method | not refuted (all quotes reproduce; ADR-0016 contains no overnight/DR-1 reconciliation; 22 coverage_gaps verified) | Cross-document conflict on the immediate Step-5 action: plan §3 rank-1 overnight/Globex = "Cheap to check, no vendor spend"; sheet §5(c) = "DR-1/DR-2 are prerequisites of **any** overnight/Globex screen" (hardening its own §2.1.4 "plausible prerequisite" hedge). Neither extreme survives: an overnight screen can run today at conditional grade on the exclusion-filtered substrate, but carries a structurally non-random blind spot (every December roll window falls in Globex sessions + the whole post-2025-12-08 tail) that is materially worse for an overnight mechanism than for RTH ones. | One reconciled statement in both documents: screenable NOW at conditional grade with the December/Globex blind spot declared in the design; DR-1/DR-2 prerequisite for December-inclusive or confirmation-grade overnight evidence and any December-complete re-backfill. Fix plan §3 feasibility cell + §7; soften sheet §5(c) "any" to the §2.1.4 hedge. |
| QUANT-1-5 | major | reporting | not refuted (non-existence claim + stage-table divergence reproduced verbatim) | Ordering-of-record inconsistency plus divergent stage definitions under one name: the sheet asserts "ADR-0016 does not exist as of 2026-07-18" and gates T2-B on ratification, while ADR-0016 (dated 2026-07-18) exists in the same tree; the sheet's stage-C row includes "ADR-0006 obligation to validate against live fills" as a stage-C gate — unsatisfiable at \|arsenal\|=0, would deadlock stage D — whereas ADR-0016 V-c explicitly removes live reconciliation from gating (V-a/V-b gate); sheet stage-A wording also differs. | Update the sheet (it is the stale document): pointer to the drafted proposed ADR-0016 + drafting-order note; mirror the ADR's stage A–D definitions verbatim in §1.3 and §5(c) (stage-C gates = V-a/V-b; live fills = standing re-validation condition). |
| QUANT-1-6 | major | method | not refuted (V-a "OUTPUT" + D6 containment quotes verbatim; no external bound-generating rule anywhere in the ADR; V-b is an independent failure path → severity mitigation only) | Internal circularity in ADR-0016: D5(V-a) makes the stage-C acceptance bounds "an OUTPUT of this comparison" — the same MBO-vs-MBP-10 comparison those bounds gate. Bounds derived from the observed error distribution cannot fail the model, so D6's containment claim ("cannot reproduce MBO queue behaviour within the stage-C acceptance bounds … not remediated by loosening the acceptance bounds") is structurally empty — the forbidden loosening is built into the bound-generation rule. E-a's grid-endpoints-as-output is legitimate (sweep, no pass/fail); acceptance bounds are pass/fail objects and need an external criterion. | Derive stage-C acceptance bounds from a decision-relevance criterion external to the comparison (e.g. maximum queue/fill error under which the E-a pessimistic endpoint still brackets the true fill distribution conservatively for the D3 claim classes), with the bound-generating **rule** (not just its "form") pre-registered before the MBO sample is opened. |
| QUANT-1-7 | major | method | not refuted (schema + ADR-0015 quotes verbatim; no amendment proposed anywhere in the plan; plan M2 internally contradicts §6(i)) | The plan's cosmetic-novelty **diagnosis is VERIFIED** against ground truth ([pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml) `window_overlap_jaccard` and the `verdict_precondition` are label-based, hence gameable exactly as §2.2 claims; `min_distinct_disjoint_coverage: 2` operator-directed/provisional as claimed). But the remedy overreaches: M1 + §6 standing condition (i) declare the ADR-0015 precondition "is evaluated on realized-bar disjointness (M1), never on cell labels" — a living note rewriting the semantics of a rule recorded verbatim in an ACCEPTED ADR whose Consequences require supersession "through a new ADR, never by silent edit". | Recast M1 as a mandatory REPORTED companion statistic (bar-level + session-level Jaccard alongside the label-based precondition) and propose an ADR-0015 amendment / schema addendum before any document asserts the precondition "is evaluated" on realized bars. The operator can weigh M1 in the already-operator-gated lift action without rewriting the accepted rule. |
| QUANT-1-9 | major | parameter | not refuted (all quotes verbatim; §1.4 justifies ≥5 sessions and ≥2 blocks but contains no power computation for 10; "Proposed" labeling ≠ the "upper bound" fact-claim) | Stage-B sizing asserted, not derived, and contradicts the sizing rule of the ADR that will govern it: ADR-0016 D2/D6 require the MBO sample "sized by the validation power requirement of Decision 5, not by convenience", but Decision-5 bounds do not exist yet and the sheet fixes 10 sessions and claims "10 sessions is an upper bound on what the decision needs". The quoting instruction "price **any** 10 ES sessions" rests on a within-regime byte-insensitivity claim with zero in-repo basis (tick volume "NOT DERIVABLE") and contradicts the sheet's own premise that event intensity differs by regime — permits an all-calm quote despite the mandated 5-calm+5-stress mix. | Label the 10-session figure PROVISIONAL pending the Decision-5 validation-power spec; change the quoting instruction to price a rule-selected candidate calm block and stress block separately and report both; drop or caveat the within-regime insensitivity claim. |
| QUANT-1-10 | major | numerical | not refuted (git grep: `MES` in 9+ tracked files; retro register line 124 IS the pooling proposal; git ls-files confirms tracked) | The OD-B justification repair rests on a false repo-ground-truth claim: "MES and MNQ appear nowhere in the tracked repo (the only hits are in an untracked local brief)". False — [retro_card_register_2026-07-10.md](../research_notes/retro_card_register_2026-07-10.md):124 is precisely the RC-H103-1 pooled ES+NQ+MES+MNQ scan spec ("… to n ≥ 174 stress-cell trades"), plus H103/design.md:125 and backfill plan §5, all tracked. The substantive conclusion survives — the n≥174 floor was met on ES+NQ alone as executed (disposition §3.8 verified verbatim), so breadth-not-sample-size is the defensible MX-1 rationale — but the provenance claim misstates the record: OD-B traces to the registered retro-card scan spec, not to nothing. | Correct sheet §2.3: pooling proposal exists in the tracked retro-card register + H103 design.md; as-executed RC-H103-1 met the floor on ES+NQ alone, rendering the pooling rationale **obsolete rather than absent**. Keep the conclusion and MX-1 priority unchanged. |
| QUANT-1-11 | major | method | not refuted (full text obtained; paper's own Table I/Fig 6: CHL lowest bias at **larger** spreads (3–8%); ~30% upward bias at 1% spread) | Abdi & Ranaldo 2017 gloss direction-inverted: plan claims CHL "generally lower bias than Corwin-Schultz in **low-spread** regimes"; the paper claims best TAQ-benchmark correlations and most accurate estimates for **less liquid** (wide-spread) stocks. For tick-constrained ES/NQ the low-spread regime is exactly the one governing primary-proxy selection, so the gloss pre-steers the §7 pre-registration choice on a claim the source does not make. | Replace with the paper's stated claims or cite the specific simulation table; rest the proxy selection on a bias characterization verified for the tight-spread, tick-floor regime. |
| QUANT-1-12 | major | method | not refuted (Crossref metadata all three DOIs; no close-side consideration anywhere in the plan) | Intraday-pattern citation cluster misdescribes and misattributes: "U-shape in spreads — widest at the open, narrowing through midday" cites Wood-McInish-Ord 1985 (returns/volatility, not spreads), McInish & Wood 1992 (actual spread paper — **reverse-J**: elevated at open AND close), and CRS 2001 (daily aggregate liquidity, not intraday). §2.2's direction survives via MW1992's open-side, but the omitted close-side elevation matters for the overlap argument: close bars also populate a wide-spread cell and are NOT ORB bars — the M3(c) expected-overlap prediction should reflect it. | Restate as reverse-J per MW1992; re-scope WMO 1985 to returns/volatility; drop or re-scope CRS 2001; propagate close-side elevation into M3(c). |
| LITERATURE-1-1 | major | misattributed | not refuted (independent Crossref verification, all three counts) | Independent confirmation of QUANT-1-12 (same defect, literature branch): only MW1992 supports an intraday spread claim and its finding is a "crude reverse J-shaped pattern"; WMO 1985 is minute-by-minute RETURNS; CRS 2001 is DAILY aggregate. | As QUANT-1-12. |
| LITERATURE-1-2 | major | misattributed | not refuted (full-text search; Table III Panel E: Corwin-Schultz OUTPERFORMS CHL in the smallest effective-spread quintile — HL 0.450 vs CHL 0.381 cross-sectional) | Independent confirmation of QUANT-1-11 (same defect, literature branch), strengthened: in the paper's closest analogue of a low-spread regime, Corwin-Schultz is the *better* proxy; follow-on literature (e.g. Ardia-Guidotti-Kroencke 2024, doi:10.1016/j.jfineco.2024.103916) reports ALL low-frequency estimators materially biased when true spread is small relative to volatility — exactly the ES/NQ regime. The sentence is the only bias characterization on record and pre-steers §7. | As QUANT-1-11, plus an explicit caveat that the low-spread/high-vol index-futures regime is where every OHLC-based estimator is weakest; §7 selection needs its own empirical justification on this substrate. |

## Refuted at the gate (logged, dropped from remediation)

| ID | Sev | Claim | Refutation (evidence type: logical-proof) |
|---|---|---|---|
| QUANT-1-1 | critical | ADR-0016 D5(V-c) silently weakens the accepted ADR-0006 standing Obligation (live-fill validation before confirmation-grade) while claiming to amend no decision body; three documents mutually inconsistent on the reportability boundary. | **Refuted.** The finding conflates two predicates the documents keep separate: gating the BUILD vs gating output CONFIRMATION-GRADE. ADR-0006's Obligation withholds confirmation-grade from Tier-2 *outputs* until live-fill validation; it never conditions the build or claim assertion on live fills — "assertable/reportable but sub-confirmation-grade" is a state ADR-0006 itself defines. ADR-0016 D3 explicitly adds no reportability rule; the References carry the ADR-0006 Obligation as referenced-not-restated, so it remains fully binding after acceptance — the normative state on confirmation-grade is identical before and after. The V-c Expert-Card re-validation flag is strictly ADDITIVE (stricter, not weaker). Sheet §5(c) ("a FURTHER gate before … confirmation-grade") and plan §1 ("not confirmation-grade until after a champion is trading") both restate the still-in-force ADR-0006 Obligation. All three documents are consistent on this point. |

Adjudication note: this was the single `critical` of the round and the most
prominent of the operator-reported opposing viewpoints. It dissolves — the
apparent contradiction is a build-gate vs confirmation-grade-gate distinction,
and ADR-0016's V-c is *stricter* than the status quo, not weaker.

## Minors logged (not remediated; `invitesPolish: false`)

| ID | Sev | Finding (condensed) |
|---|---|---|
| QUANT-1-8 | minor | Plan §3 rank-1 "Disjointness is an identity" is valid at bar level but the plan never applies its own M1 session-level caveat to its own rank-1: an overnight expert is ~100% session-date-overlapping with the ORB pool ("disjoint at bar level but identical at session level is still poor diversification" — the plan's own words). Add a session-level column to §3. |
| QUANT-1-13 | minor | Lo & MacKinlay 1988 named in plan §3 without link/DOI; the DOI is already registered in-repo (conditioning_covariates.yaml → 10.1093/rfs/1.1.41). |
| QUANT-1-14 | minor | Sheet §0 verification labels honest; this audit **upgrades three rows by direct fetch** (GLBX.MDP3 history start 2010-06-06 VERIFIED; mbp-10 + ohlcv-1m schemas VERIFIED; MDP2-era caveat CONFIRMED in direction — page says "Since March 2017", vs the sheet's 2017-05-21: residual date discrepancy for the operator). New consequence: the stage-B block-selection rule carries no post-2017 constraint, so a rule-selected stress block landing pre-2017-03 would buy an MBO span with no order-level ground truth, voiding the validation purpose. Add "block start ≥ confirmed order-level-granularity date (~2017-03)" as a fifth mandatory exclusion. |
| QUANT-1-15 | minor | ADR-0016 E-a's precedent claim ("the ADR-0013 Kelly grid, whose endpoints are likewise a calibration output") misdescribes the repo record: the Kelly grid is a REGISTERED sweep fixed at ADR-0013 acceptance whose bracketing was checked afterwards (inconclusive-on-null-ledger, re-instantiation registered). E-a's own rule stands without the inaccurate analogy. |
| LITERATURE-1-3 | minor | ADR-0016 V-b over-attributes: monotone fill-rate-by-queue-position is a generic consequence of price-time priority, not a stated prediction of Huang-Lehalle-Rosenbaum 2015 (which models state-dependent order-flow intensities; the curve is derivable by simulation, not stated). Criterion sound; attribution overstated. |
| LITERATURE-1-4 | minor | "(CME guidance: volume migrates ~8 calendar days before last trade)" is an exchange attribution with no citation anywhere in the chain (sheet quotes the registry; the registry entry carries no source; CME rolldates page unreachable during audit; only tier-5 corroboration found). Pin to an official CME source in `config/data_sources.yaml` or reattribute as registry-derived convention. |
| LITERATURE-1-5 | minor | Same Lo & MacKinlay 1988 unlinked-citation observation as QUANT-1-13 (convention/verifiability breach; author-year technically satisfies the rule). |

## Ground truth verified CLEAN (checks that came back exact)

- Pool state as claimed in plan §2.1: 8 records, 1 distinct `expert_hash`, the
  exact competence-window cell union, against
  [pool_ledger.jsonl](../../data/processed/pool_ledger/pool_ledger.jsonl).
- Provenance register: exactly 22 `coverage_gaps` = 20 late-committed rolls +
  2 terminal windows, windows/dates as tabulated in sheet §2.1.2.
- `screening_error_rate_target` = 0.7400550140326007 and the S-d bound
  arithmetic (DSR ≥ 0.2599449859673993, PBO ≤ level).
- All sheet derived arithmetic spot-checked: 110/3293 = 3.34% and 110/3307 =
  3.33%; 770 × 1,115 ≈ 858.5k rows ≈ 67 MB at ~78 B/row; 69,103,919 /
  432,368,327 ≈ 0.16× compression; 4,270 × 85 KB ≈ 360 MB; dark-span day
  counts; store ≈ 1.7 GB.
- RC-H103-1 disposition §3.8 quote verbatim ("Both stress cells exceed the
  n≥174 ES-anchor sample-size floor (ES 437, NQ 481)").
- Plan §2.2 gameability diagnosis of the label-based `window_overlap_jaccard`
  / `verdict_precondition`: VERIFIED against
  [pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml) (the
  *diagnosis* is right; only the remedy's semantics-rewrite overreaches —
  QUANT-1-7).
- Citations verified correct: Corwin-Schultz 2012; Roll 1984 (undefined under
  positive autocovariance is canonical); Amihud 2002 (price-impact-not-spread
  gloss faithful); Glosten-Milgrom 1985 (adverse-selection gloss faithful);
  Huang-Lehalle-Rosenbaum 2015 metadata; Cont-Kukanov-Stoikov 2014 (gloss
  faithful; 2013-online/2014-print cited correctly); Bailey-LdP 2014; PBO
  JCF 20(4):39-69 (2016-DOI/2017-cite oddity already closed by
  `P1-2.0-CITE-DOI-VERIFY-PBO-2017`, not re-raised); Perold 1988; Harris 2003
  monograph handling transparent.
- Sheet §0 Databento verification labels HONEST (auditor fetches reproduced
  the reported truncations); nothing load-bearing rests on an UNVERIFIED row
  (2010-06-06 start irrelevant to every priced item; MDP2 caveat carried
  in-row on T2-D3).

## Residual risk (carried; verbatim-condensed from the branches)

- **quant-auditor:** paywalled full texts (Abdi-Ranaldo simulation section,
  McInish-Wood 1992 body) could partially rehabilitate the flagged glosses
  (note: the refuters subsequently obtained the Abdi-Ranaldo full text and
  the finding hardened, not softened); the DR-1 2–3× spread-row multiplier
  and the 26.44 bar-dates/month store derivation were not independently
  re-derived; the March-2017 vs 2017-05-21 MDP-era cutoff is unresolved;
  until QUANT-1-2/-3 are remediated, OD-G sequencing and any ADR-0016
  acceptance bind on a stage-A gate object and a span-death rule the three
  documents define inconsistently.
- **literature-check:** (1) MDP2-era MBO availability/fidelity for any
  2015–2017-05 span remains unverifiable by fetch — operator must confirm
  with Databento before pricing T2-D3, exactly as the sheet instructs;
  (2) the true bias behaviour of ALL OHLC-based spread estimators in the
  ultra-low-spread ES/NQ regime is genuinely unsettled — the §7
  proxy-selection step needs its own empirical justification regardless of
  how the Abdi-Ranaldo gloss is reworded; (3) the CME rolldates page was
  unreachable, so the eight-day roll convention rests on tier-5 sources
  pending an official pin.

## Round 2 — verification (run `wf_4a55c455-fdd`; 5 agents)

Branch verdicts: literature-check **accept** (all 13 DOIs Crossref-verified;
all internal quotes verbatim on the tracked record; every relative link in
the edited regions resolves; the two citation-content rewrites verified
against primary full text — Abdi-Ranaldo Table III Panel E smallest-quintile
HL 0.450 > CHL 0.381 and the 1%-spread-simulation upward bias confirmed;
McInish-Wood reverse-J confirmed; CRS 2001 fully removed). quant-auditor
`proceed-with-remediation`: 3 majors — each an incomplete round-1 fix (the
lead's fix-map overclaimed three sites), each confirmed by its refuter — plus
3 minors.

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| QUANT-2-1 | major | Plan §6 standing condition (i) still asserted the ADR-0015 precondition "is evaluated on realized-bar disjointness" — the QUANT-1-7 fix was applied at §2.3 but never at this second site, leaving an internal contradiction. | remediated — §6(i) now the companion-statistic form; the label-based rule governs until the proposed ADR-0015 amendment is accepted |
| QUANT-2-2 | major | Sheet §2.1.4(3) "cannot be screened", §4 DR-1 "makes overnight/Globex mechanisms screenable", and §5(b) — three residual unqualified sites contradicting the reconciled §5(c). | remediated — all three qualified December-inclusive / confirmation-grade, conditional-grade path stated |
| QUANT-2-3 | major | Sheet §1.4 item 5 still opened with the underived "10 sessions is an upper bound" fact-claim. | remediated — session count = power-specification OUTPUT; 10 = provisional planning figure |
| QUANT-2-4 | minor | Both T2-D3 sites still said UNVERIFIED for the MDP2-era caveat vs the upgraded §0 row. | remediated — confirmed-in-direction; exact cutoff OPEN (~2017-03 vs 2017-05-21) |
| QUANT-2-5 | minor | "Decision-5 validation-power specification" had no defined owner/timing object anywhere. | remediated — ADR-0016 D6 stage B: authored + pre-registered as part of the stage-B pre-registration, before pricing |
| LITERATURE-2-1 | minor | The vendor-page dated sentence ("Since March 2017") not independently re-fetchable in round 2 (JS-truncated pages); substance corroborated via search-surfaced Databento docs. | no text change — the operator pins the vendor's dated statement at stage-B pricing (already mandated in-artifact) |

## Round 3 — final verification (run `wf_32b8f9cd-bf1`)

**Both branches `accept`; zero findings; clean exit at the 3-round cap.**
Verified: all eight round-2 fix sites correct and mutually consistent, and the
three documents now issue ONE operator sequencing instruction at every site —
defer Form A; overnight/Globex first (conditional-grade screenable now with
the December/Globex blind spot declared); DR-1/DR-2 prerequisite only for
December-inclusive / confirmation-grade overnight evidence; T2-B gated on the
named, dated stage-B authorization. Post-round-3 cheap consistency fix applied
(a literature-branch observation outside the fix sites, not a finding): sheet
§5(a) step 2 re-keyed from "after the staged build is ratified as an ADR" to
the named stage-B authorization.

## Final residual risk (carried)

- The GLBX MDP2→MDP3 order-level-granularity cutoff (page: "Since March
  2017"; carried figure 2017-05-21) rests on the round-1 vendor-page fetch —
  OPEN; the operator pins it with the vendor before stage-B pricing (mandated
  in sheet §0/§1.4(4) and ADR-0016 D6 stage B).
- Abdi-Ranaldo Table III verified on the July-2016 working-paper copy;
  published-RFS table numbering presumed identical (label-only risk).
- The label-based ADR-0015 precondition remains gameable until the proposed
  realized-bar amendment is put to the operator; M1 companion reporting is
  mandatory in the interim.

## Loop state

CLOSED — 3 rounds, exit on clean round-3 accept. Governance outcomes recorded
the same day by principal direction: ADR-0016 **accepted** (stage A only — no
spend authorized); OD-G Form A **deferred**; forward-sourcing priority
**overnight/Globex → mean-reversion**; DR-1/DR-2 **elevated to quote-ready
top purchase priority** (operator-only spend, not authorized); ADR-0015 HOLD
unchanged. Downstream doc updates (roadmap, backfill plan, CLAUDE.md,
CHANGELOG, handoff banner, data_sources.yaml attribution note) land in the
same-day commits.
