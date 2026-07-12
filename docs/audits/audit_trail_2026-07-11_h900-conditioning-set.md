# Audit Trail — H900 conditioning-set + report-object registration (step 3)

**Deliverable:** Register the H900 winning regime family as the ADR-0002
candidate conditioning covariate, and the dwell/detection-latency metrics as
standing ADR-0004 report objects — the frozen §10 GO consequence of the H900
dwell-time feasibility gate.
**Date:** 2026-07-11 · **Governance:** ADR-0001 D5, ADR-0002(b)/(c), ADR-0004 D4/D5/D6.
**Artifacts:** `config/conditioning_covariates.yaml` (new),
`docs/methodology/allocator_metric_family_report_objects.md` (new),
`config/covariates.yaml` (pointer comment).
**Branch:** `claude/h900-conditioning-set`, stacked on `claude/h900-bocpd-sensitivity`
(step 2 / PR #4) — this deliverable references the BOCPD sensitivity result.

## Round 1 (2026-07-11)

Routing: `quant-auditor`, `literature-check`. Verdicts: literature-check
**accept**; quant-auditor **proceed-with-remediation**. Triage: 1 major (confirmed,
0 refuted) + 6 minors.

### Confirmed major — remediated

| ID | Issue | Disposition |
|---|---|---|
| QUANT-1-1 | The docs cited BOCPD results (ES 66 / NQ 52; ~46–48%) and `inference/bocpd.py` as established facts, but the branch was cut from `main` (9c7c64b), which does not contain the BOCPD work (only PR #4's branch does) — an undeclared cross-branch merge dependency; on that branch the citations pointed at non-existent artifacts. | **Fixed (structural)** — rebased the step-3 branch onto `claude/h900-bocpd-sensitivity` (HEAD 9a9e269). The BOCPD report, `bocpd.py`, and the `bocpd_sensitivity` verdict block are now committed on-branch; the figures are backed by committed artifacts. Step 3 is a stacked PR (merge PR #4 first). |

### Minors — all remediated

- **LITERATURE-1-1** — config header folded "define conditional-edge scan cells" into an ADR-0001 D5 paraphrase. **Fixed** — prior-tilt attributed to ADR-0001 D5, scan-cell use to ADR-0002(c), separately; the gating prohibition (the core D5 protection) preserved.
- **QUANT-1-3** — CUSUM L_detect caveat cited "report §4"; the 2–3 bar figure is in §3.2. **Fixed** → §3.2.
- **feature-id** (literature residual) — config listed emission id `log_rvol_5m_24h@1.0.0`; the registered feature is `rvol_5m_24h@1.0.0` with log as an emission transform. **Fixed** — `features: [ret_5m@1.0.0, rvol_5m_24h@1.0.0]` + `emission_vector: (ret_5m, log rvol_5m_24h)`.
- **QUANT-1-2 / LITERATURE-1-3** — methodology member 3 gave "detector alarm" as the verbatim ADR-0004 D4 definition (D4 endpoint is "allocator weight response"). **Fixed** — states the D4 endpoint and flags detector-alarm as the standing pre-allocator proxy.
- **QUANT-1-4** — B=2000 lacked a provenance annotation. **Fixed** → "(H900 §8; 1.0 H052a convention)".
- **LITERATURE-1-2** — member 5 block-length cite omitted the PPW-2009 correction mandated by ADR-0004 D4. **Fixed** — added Patton, Politis & White 2009 (10.1080/07474930802459016) to member 5 and the references.

### Round-1 residual (auditor statements)

- **literature-check (accept):** all 8 external citations resolved to primary sources; H900 numbers (CUSUM ES 3/NQ 2, dwell ES 12/NQ 9, BOCPD ES 66/NQ 52, corroboration 45.7%/48.1%) and design SHA `548f009ae505…` reconcile against the committed report/verdict/audit trail.
- **quant-auditor:** after remediation the registration is ADR-faithful, D5-compliant, citation-valid; residual was the merge-ordering dependency — resolved by the rebase.

## Round 2 (2026-07-11) — ACCEPT

Routing: `quant-auditor`, `literature-check`. Verdicts: **both accept** →
loop-level verdict **accept**. 0 majors, 0 refuted, 2 minors (remediated).

- **QUANT-2-1** — the `regime_hmm_h900` references block carried an orphaned Grinold 1989 citation (marginal-contribution is an ADR-0002(d) concept absent from this covariate-definition entry). **Fixed** — dropped; Rabiner 1989 (HMM) is the load-bearing citation.
- **LITERATURE-2-1** — the post-hoc-covariate obligation was cited to `ADR-0002(e)` (the archive disposition); the obligation lives in ADR-0002 Consequences. **Fixed** → "(ADR-0002 Consequences/obligation; ADR-0008 Decision 4)".

Verification confirmed: rebase resolved QUANT-1-1 (BOCPD artifacts committed
on-branch; ES 66/NQ 52, 45.7%/48.1% corroboration, CUSUM 3/2, design SHA
`548f009ae505…` all reconcile); all round-1 remediations correctly applied;
ADR-0001-D5 compliance intact (covariate/scan-cell, explicit no-gate language);
all 9 external citations resolve to primary sources.

### Final disposition

**Accepted** (round 2, both branches accept; no major ever survived the refute
gate). Step 3 registration is governance-faithful, ADR-0001-D5-compliant, and
citation-valid.

## Residual risk (carried)

- **Stacked-PR merge order:** step 3 must merge after PR #4 (step 2 / BOCPD).
  Its BOCPD citations are backed only once PR #4 lands. Declared here and in the
  step-3 PR.
- **KM-median semantics of BOCPD L_detect** (carried from step 2): with a
  sub-50% alarm fraction the KM median 66/52 is a censoring-bounded statistic,
  not a clean central estimate — the artifacts caveat it as a corroboration-rate
  result with true live latency "unquantified" (`P1-2.0-H900-BOCPD-WHITENED`).
