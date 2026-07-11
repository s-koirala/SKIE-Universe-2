# Audit trail — Phase A: H900 dwell-time feasibility gate execution

- **Deliverable:** execution of frozen hypothesis H900 (ADR-0004 Decision 6
  founding go/no-go): 1.0 HMM toolkit + stationary-bootstrap ports, emission
  features, dwell/KM/CUSUM/cost modules, production runner, and the terminal
  report [reports/H900/H900_dwell_feasibility_report_2026-07-11.md](../../reports/H900/H900_dwell_feasibility_report_2026-07-11.md).
- **Design conformance:** frozen design SHA
  `548f009ae505816a1b2aeb8693681224e080449b458013e87d6f3df3c8f4c43c` verified
  at runtime and recorded as `config_resolved_sha256` in the production
  ReproLogs. 14 documented deviations, each justified in report §6; none
  outcome-motivated (adjudicated by the audit).
- **Pattern:** audit-remediate loop (Workflow engine), 3 rounds (cap),
  branches: code-reviewer, quant-auditor, reproducibility-verifier,
  literature-check. Adversarial refute gate on every major; 0 refuted.

## Verdict

**GO** — primary registered analysis and inclusive sensitivity both meet the
§10 H1 criterion on BOTH instruments (design requires ≥1):

| Instrument | Pooled KM median dwell | 95% bootstrap CI | D_be(μ=1.2e-4) | L_detect | Precision gate |
|---|---|---|---|---|---|
| ES (primary) | 12 bars (60 min) | [10.0, 14.0] | 4.45 bars | 3 bars | 2.0 < 3.0 pass |
| NQ (primary) | 9 bars (45 min) | [8.0, 10.0] | 2.54 bars | 2 bars | 1.0 < 2.25 pass |

Frontier fails only at μ=1e-5 (both instruments); passes at 4e-5/1.2e-4/2.7e-4.
BIC selected 4-state diagonal in 30/30 window fits (grid ceiling — in-grid
dwell lengthens with state count, so the ceiling is conservative in-grid;
extrapolation beyond the frozen grid is untested). 360/360 EM fits converged.
Worst-case latency bound (all censored transitions = +∞) and doubled-latency
stress leave GO standing. Account-dollar cost basis would fail both
instruments — standing caveat carried from the Phase B QUANT-2-2
basis-indeterminacy finding.

## Round 1 — proceed-with-remediation (8 confirmed majors, 0 refuted)

Fee erratum ($1.18→$1.38 exchange fee, D_be +0.02), PW block-length selector
sign guard removed (Ĝ enters PW 2004 eq. 9 squared; b=1 fallback had masked
legitimate estimates — production re-run executed, block lengths ES 1.73 /
NQ 2.97, embargoes 1–67 bars), informative-censoring latency bound added
(§5.5), grid-ceiling direction corrected, fail-closed fee-config loader,
5-tuple annotation, explicit continuous-spell binding, `git_dirty` +
`working_tree_hash` added to the ReproLog schema. Fold-ins: per-window count
corrected to 13/15 ES + 15/15 NQ; report re-dated to the actual run date;
Lorden/Politis citation fixes; model_hash over the explicit file list.

## Round 2 — repro + literature accept; 2 confirmed majors

- CODE-2-1: positional Series alignment of the reference-price column
  replaced by a passthrough through `compute_emissions` with an
  order-perturbation contract test (refuter had demonstrated silent
  misalignment on perturbed input; production numbers unchanged).
- QUANT-2-1: session-truncated sensitivity pooled CIs had been computed with
  undisclosed Greenwood instead of the registered §8 stationary bootstrap.
  Recomputed and persisted (`session_truncated_sensitivity` verdict blocks):
  primary ES 49 [35, 69] (auto block ≈99.9 bars), NQ 32 [24, 41] (≈86.1);
  regen mode first reproduced all archived continuous-rule pooled estimates
  from the untouched spells parquet (4/4 cells matched) and emitted ReproLog
  `bc5b16aef8ae`. Greenwood retained only as a labeled method comparison.

## Round 3 — verdict: ACCEPT (all four branches; cap reached)

6 minors logged; three applied post-verdict by the lead session (censoring
"fourfold" → actual ~0.9%→29% / ~0.8%→26% figures; resolvable Politis 2003
DOI 10.1080/10485250310001604659 restored; Hansen 2005 quotation demoted to
paraphrase with unverified-pin note). Remaining documented residuals:
CODE-3-1 (duplicated 7-day gap constant), CODE-3-2 (two annotations),
LITERATURE-3-3 (Klein & Moeschberger §3.4 sub-section pin unverifiable
against the paywalled text), plus the logged rounds-1/2 minors in the
workflow journals.

## Reproducibility chain

- Production ReproLog `repro_log_efd8dcb1bf674382988b89db97a0776c.json`
  (seed 20260710, design SHA as config_resolved_sha256, dataset checksums,
  model_hash over the 8 written outputs, `git_dirty` honest).
- Sensitivity-regen ReproLog `repro_log_bc5b16aef8ae4ed487868879632ccc9f.json`.
- Burned-data ledger: 30 H900 rows (per evaluation window per instrument,
  spans tiling 2017-01-01 → 2024-07-01; 2024-07 → 2025-12 remains unburned).
- PIT canary: PASS on the real ES substrate + negative control proving the
  canary fires on injected look-ahead.

## Registered follow-ups

| ID | Action |
|---|---|
| P1-2.0-H900-BOCPD-SENSITIVITY | BOCPD sensitivity detector (the one registered sensitivity not computed; explicit design deviation) |
| — | Winning family (4-state diag Gaussian HMM) registered as the ADR-0002 conditioning-set candidate for admission scans RC-H100-1 … RC-H104-1 |
