# Audit trail — ADR-0014 provisional candidate pool + pool-ledger schema

- **Date:** 2026-07-17
- **Deliverables:**
  [docs/decisions/ADR-0014-provisional-candidate-pool-screen-verdict.md](../decisions/ADR-0014-provisional-candidate-pool-screen-verdict.md),
  [config/pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml)
- **Mechanism:** audit-remediate-loop → Workflow engine
  ([workflows/audit-remediate.js](https://github.com/s-koirala/dotfiles)), 5-branch
  specialist routing, adversarial refute gate on every critical/major finding.
- **Rounds:** 2 of 3 cap (exit on zero critical/major surviving the gate).
- **Routing (both rounds):** quant-auditor, literature-check, format-auditor
  (`.md`/`.yaml`, flags: citations, identity, statistical; no `.py` → no
  code-reviewer; repro flag off).

## Round 1

Branch verdicts: quant-auditor `proceed-with-remediation`; literature-check
`accept`; format-auditor `accept`.

| ID | Sev | Category | Refute gate | Disposition | Fix |
|---|---|---|---|---|---|
| QUANT-1-1 | major | parameter | `refuted: false` (reproduced-check + logical-proof: DSR is a [0,1] probability per deflated_sharpe.py; ">0" vacuous; threshold unregistered repo-wide) | remediated | Added schema `dsr_bound_ref` tied to DSR ≥ 1 − screen α (discovery-alpha OUTPUT); ADR S-d rewritten to disavow "positive DSR". |
| QUANT-1-2 | major | reproducibility | `refuted: false` (source-quote: conditioning_covariates.yaml:114-116 "unquantified pending P1-2.0-H900-BOCPD-WHITENED"; on-ledger ROC re-run DEFERRED per CLAUDE.md) | remediated | ADR S-e + Obligation + schema `detection_latency_bars` marked BLOCKED/DEFERRED; screen not end-to-end executable / no pass certifiable until reproducible on-ledger unsupervised latency emitted. |
| QUANT-1-3 | minor | method | n/a (minor) | remediated | "pool size enters DSR effective-trials count" → effective-trials *estimator* (correlation-adjusted, not raw count) in Decision 4 + amendment map. |
| QUANT-1-4 | minor | method | n/a (minor) | remediated | Cold-start `covers_uncovered_cell` non-discriminating at \|arsenal\|=0 → ADR + schema state the primary is inert at \|arsenal\|=0; ordering falls to the persistence-margin tie-breaker. |
| QUANT-1-5 | minor | reporting | n/a (minor) | remediated | Pool disposition enum documented as the intentional pool-relevant subset of ADR-0009; cost/execution-bound → non-positive marginal_growth_delta → pool-hold-reconsider. |
| LITERATURE-1-1 | minor | misattribution | n/a (minor) | remediated | "Grinold-Kahn" label on sole-author Grinold 1989 → "Fundamental Law / marginal-IR" (compound points to the distinct 1995/2000 textbook). |
| FORMAT-1-1 | minor | citations | n/a (minor) | remediated | "Lopez de Prado" → "López de Prado" diacritic normalized in schema. |

Refuted: none. All 7 remediated (2 majors + 5 minors; minors carried despite
`invitesPolish:false` as cheap correctness gains).

## Round 2

Branch verdicts: **all three `accept`**; `remediate: []` — **exit condition met**
(zero critical/major). Three fresh minors logged (loop drops them; carried here
as cheap parity/consistency fixes).

| ID | Sev | Category | Disposition | Fix |
|---|---|---|---|---|
| QUANT-2-1 | minor | parameter | remediated | `pbo_bound_ref` pointed at no named producer (unlike anchored `dsr_bound_ref`) → anchored to PBO ≤ screen α (screening_error_rate_target); ADR S-d updated. |
| QUANT-2-2 | minor | reporting | remediated | `ruin_prob_contribution` tagged `role: gate` but is a verdict-level float exclusion → new `role: verdict-gate` + role-taxonomy comment in the schema. |
| LITERATURE-2-1 | minor | citation consistency | remediated | Round-1 Grinold relabel left a "matching ADR-0002(d) usage" pointer to still-mislabeled ADR-0002(d) → added an ADR-0002(d) label-harmonization row to the amendment map; reference note clarified (harmonized on acceptance). |

## Post-round-2 remediation defect (self-caught)

The round-1 QUANT-1-1 and round-2 edits introduced `[0,1]`, embedded quotes, and
`map<str,float>` into YAML **flow-mapping** values in the schema — illegal in flow
context. The whole schema failed `yaml.safe_load` (latent from the initial draft;
the format-auditor's comment-style check did not parse it). **Fix:** converted every
field spec from flow (`{dtype:…, role:…, desc:…}`) to **block** style, where prose
descriptions with commas/brackets are legal. Verified: `yaml.safe_load` OK, all
seven remediations present post-rewrite (a diacritic regression during the rewrite
was caught and restored). No third multi-agent round was spent on this verified
syntactic reformatting, the exit condition having been met at round 2.

## Residual risk (carried to the ADR / project state)

- **quant-auditor:** After remediation the ADR is a correct governance *proposal*.
  Its two persistence/selectability numeric inputs — the (S-d) PBO/DSR bounds (via
  the discovery-alpha calibration) and the (S-e) unsupervised detection latency
  (via `P1-2.0-H900-BOCPD-WHITENED`) — plus the pool-priority weights (via the
  standing `P1-2.0-POOL-PRIORITY-CALIBRATE`) are all **deferred OUTPUTs**. The
  screen therefore **cannot be executed end-to-end, and its false-discovery control
  cannot be empirically validated, until those upstream calibrations emit
  reproducible values.** This is disclosed in the artifacts, not a defect.
- **literature-check:** All 9 external DOIs resolve and Crossref-match; Herbster &
  Warmuth confined to a reported switching-oracle-regret diagnostic (no
  re-promotion over the ADR-0013 geometric-growth primary). No citation defect
  remains.
- **format-auditor:** Identity hygiene clean (SKIE pseudonym; no real-name/OS
  strings); no template stubs; zero-magic-number posture holds (weights null/OUTPUT
  pending, bounds are registered pointers, path-maxima role:descriptive and barred
  from ranking).

## Status

**Update 2026-07-17 (post-audit): ADR-0014 accepted by principal direction and
enacted.** Status flipped to `accepted`; amendment-map banners + `amended_by`
added to ADR-0002/0004/0007/0009 (decision bodies not rewritten in place);
pool-schema status `accepted`; `P1-2.0-POOL-PRIORITY-CALIBRATE` opened (standing,
monitored); H101/H103 screen re-runs queued (blocked on the Phase-1 numeric
calibrations). Enactment is governance-only — no Kelly fraction selected, no
discovery level set, no admission certified. At audit time (rounds 1–2 above) the
ADR was `status: proposed`; the acceptance is recorded here for provenance.
