# Session Handoff — 2026-07-12

Program: SKIE-Universe 2.0 meta-strategy allocation research.
Prepared for: a fresh session continuing this work-stream.
Framing: this session installed the **aggressive geometric-growth mandate**
([ADR-0013](../decisions/ADR-0013-aggressive-geometric-growth-mandate.md)) and its
standing-incumbent governance
([ADR-0012](../decisions/ADR-0012-standing-incumbent-allocator.md)). Both are
**STATUS: proposed** — in force only as governing intent, not yet enacted. Every
next step below is framed by the geometric (compounded, Kelly log-wealth) growth
objective.

---

## 1. Executive summary

The program's capital philosophy was reframed from risk-averse tail protection to
**optimism + exponential (compounded) growth via a high-risk methodology**. The
primary objective is now geometric (Kelly log-wealth) growth rate; the Kelly
fraction becomes a registered swept hyperparameter `{0.5, 0.75, 1.0, 1.25}` whose
winner is data-selected over the joint (allocator-config × Kelly-fraction) space;
the lower-tail terminal-wealth quantile is demoted from binding metric to a
monitored non-binding guardrail. The overfitting/integrity core (DSR/PBO,
matched-turnover random rotor, PIT canaries, trial register, ReproLog, shadow
ledger, SPA/StepM) is explicitly reaffirmed as **non-waivable and more binding
under leverage** — because at leverage an overfit champion does not merely
underperform, it **ruins** (negative geometric growth on a fake edge).

Three research/registration deliverables landed alongside the governance overhaul,
all on the H900 regime-detection line:

1. **H900 BOCPD detection-latency sensitivity** (PR #4 / `9a9e269`): CUSUM verdict
   GO reproduced bit-identically; unsupervised BOCPD is NO-GO on both variants —
   H900's GO is **supervised-detection-dependent**.
2. **H900 regime family registered** (PR #5 / `ac2d383`) as the ADR-0002 candidate
   conditioning covariate (covariate-not-gate, ADR-0001-D5 compliant) and
   dwell/detection-latency registered as standing ADR-0004 report objects.
3. **Aggressive-mandate governance overhaul** (PR #6 / `87641f6`): ADR-0013
   keystone + ADR-0012 champion-challenger + an 18-row amendment map + `amended_by`
   banners on the affected founding ADRs.

One investigation completed but its deliverable is **parked**:
**P1-2.0-H900-BOCPD-WHITENED** — AR/whitening prewhitening of the near-unit-root
`log_rvol` does **not** rescue the BOCPD NO-GO. The full net-detection-vs-hazard
ROC shows **no operating point is both accurate and timely**, so the
supervised-detection dependence is robust. The module and tests are drafted but
untracked; finalize + ROC report + audit + commit remains TO DO.

---

## 2. What was accomplished

All work committed on branch `claude/aggressive-mandate-overhaul`, which stacks
the four steps below.

### Step 1 — main reconciliation
Local `main` fast-forwarded to `origin/main`. No content change.

### Step 2 — H900 BOCPD detection-latency sensitivity — PR #4, commit `9a9e269`
- New module [src/skie_universe2/inference/bocpd.py](../../src/skie_universe2/inference/bocpd.py)
  — Adams-MacKay 2007 Bayesian Online Changepoint Detection port.
- Reproduction gate [scripts/audits/check_h900_bocpd_reproduction.py](../../scripts/audits/check_h900_bocpd_reproduction.py).
- Report [reports/H900/H900_bocpd_sensitivity_2026-07-11.md](../../reports/H900/H900_bocpd_sensitivity_2026-07-11.md);
  tests [tests/test_bocpd_latency.py](../../tests/test_bocpd_latency.py).
- **Findings:** CUSUM supervised-detection verdict **GO reproduced bit-identically**.
  Unsupervised **BOCPD is NO-GO on both variants**: detection latency
  `L_detect = 66` bars (ES) / `52` bars (NQ) against dwell times of `12` / `9`
  bars respectively — the detector fires long after the regime it is meant to
  catch has already ended. Conclusion: **H900's GO is supervised-detection-
  dependent**; it does not survive substitution of an unsupervised online
  detector. Closed report deviation-1. 3-round audit-remediate accept.

### Step 3 — H900 regime family registration — PR #5, commit `ac2d383`
- Registered the winning **4-state diagonal-covariance Gaussian HMM** (fit on
  standardized `ret_5m` and `log rvol_5m_24h`) as the ADR-0002 **candidate
  conditioning covariate** in [config/conditioning_covariates.yaml](../../config/conditioning_covariates.yaml).
  Registered as a **covariate, not a gate** — ADR-0001 Decision 5 compliant.
- Registered dwell-time and detection-latency as **standing ADR-0004 report
  objects** in
  [docs/methodology/allocator_metric_family_report_objects.md](../methodology/allocator_metric_family_report_objects.md).
- 2-round audit accept.

### Step 4 — Aggressive-mandate governance overhaul — PR #6, commit `87641f6`
- [ADR-0013](../decisions/ADR-0013-aggressive-geometric-growth-mandate.md) — the
  keystone reframe (see §4).
- [ADR-0012](../decisions/ADR-0012-standing-incumbent-allocator.md) —
  standing-incumbent / champion-challenger governance.
- 18-row **amendment map** in ADR-0013 (§ "Amendment map", from ADR-0013 line 238),
  with `amended_by` banners installed on the affected founding ADRs:
  [ADR-0002](../decisions/ADR-0002-arsenal-admission-standard.md),
  [ADR-0004](../decisions/ADR-0004-rolling-evaluation-regime.md),
  [ADR-0005](../decisions/ADR-0005-three-layer-separation.md),
  [ADR-0007](../decisions/ADR-0007-two-tier-discovery-pipeline.md),
  [ADR-0010](../decisions/ADR-0010-live-capital-escalation.md).
- Reframed methodology doc, README, CLAUDE.md, config, and rationale-only reframes
  of the H900 reports (no numeric result was altered — reframes are narrative only).
- 3-round audit accept; **integrity core preserved every round**.

### Parked investigation — P1-2.0-H900-BOCPD-WHITENED (COMPLETE; deliverable PARKED)
- **Method:** whitened / AR-robust BOCPD that prewhitens the near-unit-root
  `log_rvol` before online changepoint scoring, tested on the archived filtered
  sequences (**no refit**).
- **Finding — the whitened ROC:** the full net-detection-vs-hazard ROC shows **no
  operating point is simultaneously accurate and timely**. Best discrimination
  (net ≈ 26 pp) requires `L_detect ≈ 45` bars; pushing latency down to `≈ 4` bars
  collapses the detector to **pure noise**. There is no elbow that buys timely,
  accurate detection.
- **Conclusion:** whitening does **not** rescue the NO-GO. The
  supervised-detection dependence established in Step 2 is **robust** to
  AR-structure removal.
- **State:** module [src/skie_universe2/inference/whitening.py](../../src/skie_universe2/inference/whitening.py)
  and tests [tests/test_whitening.py](../../tests/test_whitening.py) are drafted
  but **untracked** (see §3). The deliverable — finalize module, write the ROC
  report, run the audit loop, commit — is **TO DO**.

---

## 3. Repository state

### Branch topology
- Working branch: **`claude/aggressive-mandate-overhaul`** (all Steps 1–4 above).
  Tip `87641f6`.
- The three research steps sit as **stacked PRs** on top of `main`, merge order
  **#4 → #5 → #6**:
  - **PR #4** `9a9e269` — H900 BOCPD sensitivity (base of the stack).
  - **PR #5** `ac2d383` — H900 conditioning-covariate registration (on #4).
  - **PR #6** `87641f6` — governance overhaul (on #5; tip of the stack).
  Merge in that order to preserve the linear history; #6 assumes #4 and #5.
- Feature branches present locally: `claude/h900-bocpd-sensitivity`,
  `claude/h900-conditioning-set`, `claude/h900-bocpd-whitened`,
  `claude/github-repo-validation-c829f1`.
- `origin/main` HEAD is at the pre-session `9c7c64b` (merge of PR #3). The stacked
  PRs are not yet merged to `main` from this session's perspective.

### On main vs on feature branches
- **On `main` already:** the H900 dwell-time feasibility gate (`c9e3e4f`, verdict
  GO) and its prereg freeze (`6ce8019`), plus CI/data-manifest fixes.
- **Not yet on `main`:** everything in Steps 2–4 (PRs #4/#5/#6), pending the
  merge-order above.

### Parked untracked files (survive checkout; not on any branch)
- [src/skie_universe2/inference/whitening.py](../../src/skie_universe2/inference/whitening.py) — `??` untracked.
- [tests/test_whitening.py](../../tests/test_whitening.py) — `??` untracked.
  These belong to the parked P1-2.0-H900-BOCPD-WHITENED deliverable and should be
  committed on `claude/h900-bocpd-whitened` when that deliverable is finalized.

### Untracked scratch (do not commit as-is)
- `reports/H900_bocpd_run/`, `reports/H900_smoke/`, `reports/H900_smoke2/` — smoke
  / scratch run outputs. Triage before any commit; not part of a deliverable.
- `docs/audits/session_trail_2026-07-10.md`, `docs/audits/session_trail_2026-07-12.md`,
  `.claude/` — session bookkeeping.

---

## 4. Governance framework now in force (as proposed)

Both ADRs are **STATUS: proposed**. They bind intent and frame all downstream work
but their amendment map is **not yet applied in place** — that application is an
explicit next step (§6.1) at principal discretion.

### ADR-0013 — aggressive geometric-growth mandate (keystone)
[docs/decisions/ADR-0013-aggressive-geometric-growth-mandate.md](../decisions/ADR-0013-aggressive-geometric-growth-mandate.md)
- **Primary objective:** geometric (compounded, Kelly log-wealth) growth rate.
  Rationale: growth-optimal betting is the Kelly criterion (Kelly 1956;
  MacLean-Thorp-Ziemba 2011). Under a compounded objective the loss function is
  asymmetric **opposite** to the founding assumption: a **missed** true edge
  forgoes unrecoverable compounding, whereas a **false** admission is caught
  downstream by DSR/PBO + the random rotor.
- **Kelly fraction:** registered swept hyperparameter `{0.5, 0.75, 1.0, 1.25}`;
  winner selected on best geometric growth over the joint
  (allocator-config × Kelly-fraction) space.
- **Lower-tail terminal-wealth quantile:** demoted binding → monitored non-binding
  guardrail.
- **Discovery alpha:** cost-tuned looser (FDR permitted where justified).
- **ADR-0002 admission** loosened; **ADR-0010 ramp** steepened.
- **Reaffirmed non-waivable and MORE binding at leverage:** DSR/PBO overfitting
  detection, matched-turnover random rotor, PIT canaries, trial register,
  ReproLog, shadow ledger, SPA/StepM.

### ADR-0012 — standing incumbent allocator (champion-challenger)
[docs/decisions/ADR-0012-standing-incumbent-allocator.md](../decisions/ADR-0012-standing-incumbent-allocator.md)
- A human-legible **standing champion** allocator config is the live default and
  live-capital anchor between confirmation cycles.
- Champion **ranked on geometric growth** as the primary dethroning statistic,
  selected over the joint (allocator-config × Kelly-fraction) space.
- A challenger **dethrones only through the ADR-0007 confirmation ladder**, by a
  pre-registered geometric-growth-improvement margin after a minimum incumbency
  dwell; every challenge and every Kelly-fraction trial logged in the ADR-0008
  trial register.

### Amendment-map scope
18 rows; touches ADRs **0002 / 0004 / 0005 / 0007 / 0010** (each amendment
STATUS: proposed until enacted). `amended_by` banners already installed on those
files; ADR-0008 references the trial-register obligation. Map lives in ADR-0013
§ "Amendment map".

### Two BLOCKING calibration follow-ups gate any Kelly-fraction selection
No swept scan may select a Kelly fraction until **both** clear:
1. **P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE** — derive/exhibit, on the
   shadow-ledger **multi-period, fat-tailed** distribution (with CIs), that
   expected log-wealth is concave in the leverage fraction with an interior
   maximum that the swept grid brackets, with explicit **ruin handling** (a
   realized `1 + f·R ≤ 0` yields **−∞** geometric growth, correctly rejecting
   that fraction). Concavity cannot be assumed: at `f = 1.25` a single fat-tailed
   bar with `1 + f·R ≤ 0` is ruin and log-wealth is undefined.
2. **P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE** — calibrate the loosened
   discovery alpha / FDR target that the Kelly sweep runs under, empirically
   (not by fiat), before the sweep adds to the multiple-testing family.

---

## 5. Open follow-ups register

### BLOCKING (gate Kelly-fraction selection)
- **P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE** — see §4; governs ADR-0013 D9.
- **P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE** — see §4; governs the
  loosened discovery alpha under the sweep.

### Deliverable to finalize
- **P1-2.0-H900-BOCPD-WHITENED** — investigation COMPLETE (NO-GO robust; ROC has
  no good operating point). Remaining: finalize
  [src/skie_universe2/inference/whitening.py](../../src/skie_universe2/inference/whitening.py)
  + [tests/test_whitening.py](../../tests/test_whitening.py), write the ROC
  report, run the audit-remediate loop, commit on
  `claude/h900-bocpd-whitened`.

### Governance enactment
- **Enact ADR-0012 / ADR-0013** — move proposed → accepted and apply the 18-row
  amendment map in place across ADRs 0002/0004/0005/0007/0010. At principal
  discretion.

### Carried from prior sessions (founding + H900 line)
- **P1-2.0-RETRO-CARD-1.0-REGISTER** — retro-card H050/H052a/H053/H054/H055 from
  1.0 KPI reports as first ADR-0002 admission candidates; register at
  [docs/research_notes/retro_card_register_2026-07-10.md](retro_card_register_2026-07-10.md).
- **P1-2.0-ROLL-SYMBOL-EXPAND** — expand the rolling-origin symbol set (see §6, step 7).
- **P1-2.0-DATABENTO-DEC-ROLL-REPULL** — operator-only vendor spend, **not
  agent-executable**.
- `P1-2.0-CITE-DOI-VERIFY-PBO-2017` — **closed** 2026-07-10 (Crossref verified).

---

## 6. Prioritized next-steps roadmap (geometric-growth mandate)

Each step lists governing ADRs and a one-line what/why. Ordering reflects
dependency: governance and the parked deliverable clear first, then the original
build chain, now all framed by the geometric-growth objective.

**6.1 — Enact ADR-0012 / ADR-0013.** *Gov: ADR-0012, ADR-0013.* Apply the 18-row
amendment map in place (0002/0004/0005/0007/0010); move both ADRs proposed →
accepted. **Why:** every step below inherits the geometric-growth objective and
champion-challenger frame; enacting first removes the "proposed" ambiguity from
all downstream registration.

**6.2 — Finalize the whitened deliverable.** *Gov: ADR-0004, ADR-0008.* Finalize
`whitening.py` + tests, write the ROC report, audit, commit on
`claude/h900-bocpd-whitened`. **Why:** closes P1-2.0-H900-BOCPD-WHITENED and
records the robust NO-GO so the supervised-detection dependence is not re-litigated.

**6.3 — (orig. Step 4) Expert producers + bar-level cost bridge + shadow-ledger
backfill.** *Gov: ADR-0003, ADR-0005, ADR-0006, ADR-0008.* Stand up expert
strategy producers, the bar-level cost bridge, and backfill the shadow ledger over
ES/NQ 2015–2025. **Why:** the shadow ledger (ADR-0003) is the sole evidence source;
geometric-growth selection and the Kelly-concavity derivation both require the
multi-period fat-tailed return record it holds.

**6.4 — (orig. Step 5) Lift the ADR-0008 PIT-canary suite.** *Gov: ADR-0008.* Wire
`pit_provisional` / December-roll exclusions and the PIT-canary leakage suite.
**Why:** non-waivable and more binding under leverage — a leaked feature that
survives to a levered champion ruins; canaries must gate before any sweep.

**6.5 — (orig. Step 6) ADR-0002 admission scans.** *Gov: ADR-0002, ADR-0007.* Run
the RC-H10x / RC-XCORR-1 admission scans under the (now-loosened) admission
standard, registered against the multiple-testing family. **Why:** admits the
retro-card and new candidates as conditioning covariates/experts; the
discovery-alpha calibration follow-up must be settled before the scan adds to the
family.

**6.6 — (orig. Step 7) Terminal-window generalization + symbol expansion.** *Gov:
ADR-0004, ADR-0007.* QUANT-3-2 terminal-window generalization and
P1-2.0-ROLL-SYMBOL-EXPAND. **Why:** rolling-origin robustness across windows and
symbols is the precondition for a durable ADR-0012 champion; DEC-roll repull is
operator-only vendor spend and stays out of the agent path.

**Gating reminder:** no Kelly-fraction sweep may select a winner until **both**
BLOCKING calibration follow-ups (§4/§5) clear. Steps 6.3–6.4 supply the
shadow-ledger record and leakage assurance those derivations depend on.

---

## Provenance / identity hygiene

Author: SKIE (pseudonym). No real-name identifiers, git author email, or OS
username in this file. Commit this handoff via `/commit-with-provenance`
(`--role=prose`) per the ICMJE 2026 AI-assistance disclosure and the project
ReproLog contract. All paths above are repo-relative to the project root.
