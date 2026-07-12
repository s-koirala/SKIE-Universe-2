# Audit Trail — P1-2.0-H900-BOCPD-SENSITIVITY

**Deliverable:** BOCPD sensitivity detector for the H900 dwell-feasibility gate
(closes [report](../../reports/H900/H900_dwell_feasibility_report_2026-07-11.md)
§6 deviation 1; ADR-0004 Decision 6, ADR-0008).
**Date:** 2026-07-11
**Mechanism:** `audit-remediate-loop` skill → Workflow engine
[audit-remediate.js](../../../.claude/workflows/audit-remediate.js), 5-branch
specialist ensemble + adversarial refute gate, 3-round cap.
**Artifacts audited:** `src/skie_universe2/inference/bocpd.py`,
`tests/test_bocpd_latency.py`, `scripts/run_h900_dwell_study.py` (modifications),
`reports/H900_bocpd_run/h900_verdict_{primary,inclusive}.json`.

## Result summary

| Detector | Verdict (primary) | Verdict (inclusive) | ES L_detect | NQ L_detect |
|---|---|---|---|---|
| CUSUM (primary, registered) | **GO** (reproduced) | **GO** (reproduced) | 3 | 2 |
| BOCPD (sensitivity) | **NO-GO** | **NO-GO** | 66 | 52 (primary) |

Headline: the H900 GO holds on the supervised CUSUM detector (bit-identical
reproduction of the frozen decision object) but is **not confirmed** by the
unsupervised BOCPD sensitivity detector — pooled KM L_detect 47–66 bars vs
regime dwell 8–12. **The GO is supervised-detection-dependent.** This is the
caveat the registered sensitivity detector exists to surface (report §6
pre-flagged "BOCPD may report longer").

Refined mechanism (synced to the round-2/3 remediations — this supersedes the
round-1 QUANT-1-3 framing): the NO-GO is driven by BOCPD's **detection rate,
not slow detection.** Only ~46–48% of the HMM's filtered transitions trigger a
BOCPD alarm within their sojourn; among those that do, the **uncensored** median
delay is low (ES 10 / NQ 5 bars, at/below the dwell). The remaining ~52–54% of
transitions never alarm and are treated as censored, inflating the KM median to
47–66. **This run cannot attribute that censored fraction** (QUANT-2-4): each
non-alarming transition is either (a) a signal-free "soft" filtered-MAP flip or
(b) a genuine change the model-light detector is underpowered to see — not
separated here. Consequently the KM median's bias direction is *conditional*
(QUANT-3-1): an upper bound only under (a); under (b) non-detection is effectively
non-detection and KM does not bound the truth. The clean statement: BOCPD
confirms fast detection of ~half of the filtered transitions and does not
corroborate the other half; the **true live-unsupervised latency is unquantified**
by this run pending the whitened variant (`P1-2.0-H900-BOCPD-WHITENED`).

## Round 1 (2026-07-11)

Routing: `code-reviewer`, `quant-auditor`, `reproducibility-verifier`,
`literature-check` (format-auditor not routed; identity flag false).
Branch verdicts: code-reviewer **accept**; quant-auditor, reproducibility-verifier,
literature-check **proceed-with-remediation**.
Triage: 8 majors → refute gate → 7 confirmed + 1 refuted; 11 minors logged.

### Confirmed majors (survived adversarial refutation) — all remediated

| ID | Issue | Disposition |
|---|---|---|
| QUANT-1-1 | Verdict-JSON detector string + docstring misdescribe the run (said "anchored hazard / MAP-reset / parameter-free"; actual = 1/median-dwell hazard, P≥0.5 posterior-majority alarm). | **Fixed** — rewrote the `bocpd_sensitivity["detector"]` string and the `bocpd.py` module docstring to the operative config. |
| QUANT-1-2 | Production hazard is outcome-derived (1/median-dwell); `anchored_hazard` never reached in the run; conservative-bias claim untested. | **Fixed** — added `test_smaller_hazard_never_detects_sooner` (conservative-bias witness); documented `anchored_hazard` as the default + registered robustness alternative; NO-GO holds under both (archived-data cross-check: generative-hazard L=94/76). |
| QUANT-1-3 | KM L_detect assumes non-informative censoring, but censoring = successor sojourn length (linked to the event across pooled transition types). | **Fixed** — documented the assumption as a caveat; added `event_delay_median_bars_uncensored` to the verdict blob as a censoring-free robustness witness (the uncensored-event median also sits far above the dwell). |
| QUANT-1-5 | NIG predictive assumes iid-within-run, but `log_rvol` is autocorrelated by construction (288-bar overlapping rolling window). | **Fixed (documented)** — flagged as a registered limitation that biases L_detect upward; whitened/AR-robustness variant registered as future work. |
| QUANT-1-6 | Bit-identical CUSUM reproduction claim had no committed test/diff. | **Fixed** — added `scripts/audits/check_h900_bocpd_reproduction.py` (sorted-equality of spells + CUSUM delay_bars/event; |Δthreshold|≤3e-8; registered-verdict-object equality); recorded PASS below. |
| REPRODUCIBILITY-1-1 | Same detector-string provenance defect in the verdict archive (18–19 distinct per-window hazards, not one anchored value). | **Fixed** — see QUANT-1-1; per-window hazards remain archived in `h900_bocpd_latency_*.parquet`. |
| REPRODUCIBILITY-1-2 | Module/dataclass docstrings describe a detector not the one that produced results. | **Fixed** — docstrings aligned to the operative per-window 1/median-dwell hazard + `alarm_prob=0.5` rule. |
| LITERATURE-1-1 | `1/(1-a_ii)` hazard anchor misattributed to Lorden 1971 (Markov sojourn arithmetic; Lorden's e^h bound is not used by BOCPD). | **Fixed** — re-attributed to Markov sojourn arithmetic; Lorden citation removed from `bocpd.py` (retained only in `cusum.py` where the e^h bound is invoked). |

### Refuted (dropped with concrete counter-evidence)

| ID | Issue | Refutation |
|---|---|---|
| QUANT-1-4 | L_detect lacks a CI while the verdict compares CI'd dwell vs point D_be embedding L_detect. | **Refuted (counter-test).** Bootstrapped + Greenwood CI on CUSUM L_detect: ES [2,3], NQ [2,2]; propagating the upper bound into D_be leaves ES GO with 5.55-bar margin, NQ with 5.46-bar margin. The GO is invariant to L_detect uncertainty; the "could make GO marginal" claim is quantitatively false. |

### Minors (logged; selectively remediated where cheap + integrity-relevant)

- **LITERATURE-1-3** — N_BOOTSTRAP=2000 misattributed to Ledoit & Wolf 2008. **Fixed** (re-attributed to the internal 1.0 convention + Politis & Romano 1994 stationary bootstrap).
- **LITERATURE-1-4** — dangling `ADR-0018` reference. **Fixed** (qualified as SKIE-Universe 1.0 ADR).
- **LITERATURE-1-2** — Adams & MacKay figure-number loci unverifiable. **Fixed** (cite §2/Algorithm 1, not a figure number).
- **QUANT-1-7** — `MAX_RUN_LENGTH=200` lacked a justify tag / fold-mass note. **Fixed** (justify tag + fold-mass test cross-reference).
- **REPRODUCIBILITY-1-3** — committed artifacts under `reports/H900_bocpd_run/` but default `--out` is `reports/H900`. **Fixed** (documented the exact reproduction command in the script docstring).
- **CODE-1-1/1-2/1-3, REPRODUCIBILITY-1-4/1-5/1-6** — annotation completeness, `sys.path` shim/E402, gitignored filtered-sequence archive not clone-visible, seed literal not sourced from design.md, BLAS/thread pinning for the bit-identical claim. **Logged as residual** (see below); not blocking.

### Round-1 residual risks (auditor statements)

- **quant-auditor:** "NO-GO robustly established (detector numerically verified, tests pass, citations valid, KM recovers latent delay in simulation)"; residual on informative censoring + outcome-derived hazard, both now remediated by documentation + robustness witnesses.
- **reproducibility-verifier:** "The NO-GO headline reproduces from the committed parquet … the conservative-bias direction of the hazard holds … the NO-GO cannot be a hazard-circularity artifact." Residual was the provenance-string mismatch (now fixed).
- **literature-check:** "No fabricated or nonexistent sources"; the single major misattribution (Lorden) now fixed.
- **code-reviewer:** **accept** — "Code-quality risk is low."

### Reproduction gate (QUANT-1-6) — recorded result

`scripts/audits/check_h900_bocpd_reproduction.py` (run 2026-07-11):
spells + CUSUM `delay_bars` + `event` **bit-identical** (sorted) for both
variants; `threshold` column relative drift 1.76e-08 (primary) / 1.88e-08
(inclusive) — pre-existing numba/BLAS reduction-order noise in `log(1/(1-a_ii))`
(~1e-7 absolute), immaterial to every integer delay; registered verdict object
identical (GO both variants). **PASS** (gate tolerance 1e-6 relative).

## Round 2 (2026-07-11)

Routing: `code-reviewer`, `quant-auditor`, `reproducibility-verifier`,
`literature-check`. Branch verdicts: code-reviewer **accept**,
reproducibility-verifier **accept**, literature-check **accept**, quant-auditor
**proceed-with-remediation**. Triage: 1 major → refute gate → confirmed
(0 refuted); 9 minors logged. **No new numeric or logic change** — every fix was
documentary/test/gate; the result is unchanged across all rounds.

### Confirmed major — remediated

| ID | Issue | Disposition |
|---|---|---|
| QUANT-2-1 | The round-1 QUANT-1-3 fix over-claimed: it called the uncensored median a "censoring-free witness" that "mitigates" informative censoring, but the data (uncensored ES 10 / NQ 5 ≤ dwell 8–12) contradicts "sits far above," and it contradicts the correct §4. The uncensored subset is the alarm-selected complement of the censored soft flips, so it cannot witness independence from the censoring model. | **Fixed** — rewrote the script comment and report §5.1: uncensored median = fast-detection subsample (biased low), KM median = censoring-inflated (biased high), the two **bracket** the truth, neither distribution-free, and the NO-GO magnitude *does* depend on scoring non-detection as censoring. |

### Minors — remediated (all except one pre-existing, out-of-diff)

- **QUANT-2-2** — iid "biases upward" asserted without derivation (a variance-under-estimate counter-effect exists). **Fixed** — reframed as "expected-but-unverified; sign settled only by the whitened variant"; dropped the proven-upper-bound claim.
- **QUANT-2-4** — §4 attributed the ~54% non-alarming fraction to "soft flips" (HMM over-segmentation) while §5.2 gives a competing "detector underpowering" reading. **Fixed** — §4 now states the missed fraction is confounded between the two and not separated by this run.
- **QUANT-2-3** — "median-exact (0-min error)" localization not archived as a metric. **Fixed** — restated as an archived per-row diagnostic (median 0-min on this run), not gated by the verdict.
- **QUANT-2-5** — reproduction-gate `SPELL_SORT` not a total order. **Fixed** — added covariance_type/session_rule/selected/event so ordering is total before `equals()`.
- **REPRODUCIBILITY-2-1** — gate did not diff the BOCPD latency parquets. **Fixed** — gate now asserts BOCPD `delay_bars`/`event` sorted-equal + hazard within rel-tol; PASSES bit-identical both variants.
- **LITERATURE-2-1** — `anchored_hazard` docstring called `1/sum_i pi_i(1-a_ii)` the "expected sojourn averaged over occupancy" (that is `sum_i pi_i/(1-a_ii)`; they coincide only for equal diagonals). **Fixed** — reworded to "mean pooled inter-switch interval = reciprocal of the stationary switch rate."
- **CODE-2-1** — the conservative-bias / alarm-prob monotonicity tests guarded their only assertion behind `if <both>.event`, risking a vacuous pass. **Fixed** — assert both alarms fire (strengthened the +3.5σ shift where needed), then compare unconditionally.
- **CODE-2-3** — variant literal hardcoded in three places. **Fixed** — hoisted a module-level `VARIANTS` constant.
- **CODE-2-2** — `_truncated_block` / `_pooled_from_spells` annotation gaps. **Logged (out of diff)** — pre-existing helpers in the frozen study, not introduced by this deliverable.

### Round-2 residual (auditor statements)

- reproducibility-verifier / literature-check / code-reviewer: **accept**.
- quant-auditor: residual confined to the (now-remediated) documentary
  over-claims; NO-GO and reproduction unaffected.

Post round-2 remediation: lint clean, full suite **275 pass**, reproduction gate
**PASS** both variants (BOCPD parquets now gated too).

## Round 3 (2026-07-11) — final (3-round cap reached)

Routing: `code-reviewer`, `quant-auditor`, `reproducibility-verifier`,
`literature-check`. Branch verdicts: code-reviewer **accept**, literature-check
**accept**, quant-auditor / reproducibility-verifier **proceed-with-remediation**.
Triage: 3 majors → refute gate → confirmed (0 refuted); 4 minors. All majors were
the **same axis** — residual over-claim / attribution inconsistency the round-2
prose fixes did not fully propagate — and are documentary (no numeric/logic
change). **All remediated.**

### Confirmed majors — remediated

| ID | Issue | Disposition |
|---|---|---|
| QUANT-3-1 | Report §5.1 still asserted "the two bracket the truth" and "soft flips" — pre-committing to attribution (a); the bracket/upper-bound claim fails under (b) (non-detection is effectively infinite latency, so KM does not upper-bound). | **Fixed** — §5.1 now attribution-neutral and *conditional*: bracket/high-bias hold only under (a); under (b) KM does not bound the truth; the run does not separate them. |
| REPRODUCIBILITY-3-2 | §5.1 and the script comment labeled the censored fraction "soft flips" (presumes (a)), contradicting §4's confounded reading. | **Fixed** — replaced "soft flips" with "censored non-alarming transitions" in §5.1 and the script comment. |
| REPRODUCIBILITY-3-1 | The audit-trail **Result summary** (this doc) was never synced to the round-2 remediations — still carried "soft flips", "upper bound", "far exceeds". | **Fixed** — Result summary rewritten to the confounded/conditional framing; marked as superseding the round-1 QUANT-1-3 framing. |

### Minors — remediated

- **QUANT-3-2** — `bocpd.py` docstring called the uncensored median a "robustness cross-check". **Fixed** → "biased-low companion, not a robustness guarantee."
- **LITERATURE-3-1** — `bocpd.py` docstring line 37 / function summary line 277 still said "mean sojourn" (repudiated by the LITERATURE-2-1 body for unequal `a_ii`). **Fixed** → "stationary switch rate / mean pooled inter-switch interval"; test renamed `test_anchored_hazard_matches_switch_rate`.
- **REPRODUCIBILITY-3-3** — `LAT_SORT`/`BOCPD_SORT` lacked a total-order tiebreaker. **Fixed** → appended `event` (+ `threshold`/`hazard`).
- **CODE-3-1** — deep-copy via `json.loads(json.dumps(...))`. **Fixed** → `copy.deepcopy`.

### Final disposition

Cap reached (round 3). After round-3 remediation: **lint clean, full suite 275
pass, reproduction gate PASS both variants** (bit-identical spells + CUSUM &
BOCPD delays + event; threshold rel-drift ≤1.9e-8; verdict object identical).
All majors across three rounds are remediated; no critical ever surfaced; the
numeric result was invariant throughout (CUSUM GO reproduced bit-identical;
BOCPD sensitivity NO-GO both variants). **Accepted with the standing residual
below.** No round 4 (per cap; residual surfaced to the lead session).

## Residual risk (carried)

- **Unquantified live-unsupervised latency (the standing scientific residual):**
  ~52–54% of filtered transitions never alarm; this run **cannot** attribute
  that fraction between (a) signal-free soft filtered-MAP flips and (b) genuine
  changes the model-light detector is underpowered to see. Consequently the KM
  L_detect (47–66) is neither a clean upper nor lower bound on the true
  live-rotor latency — only that BOCPD corroborates ~half the filtered
  transitions (at dwell-comparable latency) and declines the other half. The
  registered whitened/AR-robust variant `P1-2.0-H900-BOCPD-WHITENED` is required
  to separate HMM over-segmentation from detector underpowering and to quantify
  the achievable latency. **The founding gate stays GO on the registered CUSUM
  object; this residual is a caveat carried to the allocator confirmation tier.**
- **Clone-visibility of the refit-free archive (REPRODUCIBILITY-1-4):** the
  filtered-sequence archive is gitignored (ADR-0011 bulk-data policy); a fresh
  clone reconstructs it only by re-running the study. Fit params (means/covars/
  log_transmat) and per-window hazards are committed; the standardization
  moments are not yet serialized. Follow-up candidate.
- **iid-within-run misspecification (QUANT-1-5):** L_detect is biased upward on
  the autocorrelated `log_rvol` dimension; a whitened/AR-robust BOCPD variant is
  registered future work. The NO-GO is robust in direction but its magnitude is
  an upper bound on achievable unsupervised latency.
- **BLAS/thread pinning (REPRODUCIBILITY-1-6):** the bit-identical CUSUM
  reproduction is asserted under the local BLAS build; cross-platform
  bit-identity is not pinned (`OMP/MKL/OPENBLAS_NUM_THREADS`).
