# Audit trail — handoff-resolution changeset (2026-07-14)

Audit-remediate loop over the 2026-07-13 handoff-review resolution changeset:
the `P1-2.0-H900-BOCPD-WHITENED` finalization plus the findings/handoff/retro
reconciliations under ADR-0012/0013. Mechanism: the Workflow engine
[audit-remediate.js](../../../.claude/workflows/audit-remediate.js) — deterministic
routing → 5 parallel specialist branches → adversarial refute gate. 2 rounds
(cap 3); loop exited on round 2 with no critical/major surviving.

Artifacts audited: [whitening.py](../../src/skie_universe2/inference/whitening.py),
[test_whitening.py](../../tests/test_whitening.py),
[whitening_ar_robust_bocpd_2026-07-13.md](../methodology/whitening_ar_robust_bocpd_2026-07-13.md),
[handoff_review_findings_2026-07-13.md](../research_notes/handoff_review_findings_2026-07-13.md),
[session_handoff_2026-07-12.md](../research_notes/session_handoff_2026-07-12.md),
[retro_card_register_2026-07-10.md](../research_notes/retro_card_register_2026-07-10.md),
and (round 2) the emitted ReproLog.

## Round 1 — 21 findings, 0 refuted, all remediated

Branch verdicts: code-reviewer accept; quant-auditor / reproducibility-verifier /
format-auditor proceed-with-remediation; literature-check accept. Every
critical/major finding survived the adversarial refute gate (0 refuted).

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| QUANT-1-1 | major | Memo §4 "~0.76–0.81 corroboration rate" not reproduced by any frozen test; contradicts step-2 ~0.47 | Fixed — figure withdrawn; ROC-wide claim reattributed to the prior on-ledger probe (session_handoff §2) |
| QUANT-1-2 | major | "No ROC point accurate & timely" is ROC-wide but tests exercise only alarm_prob=0.5 | Fixed — narrowed to the single Bayes operating point; ROC-wide result attributed to prior probe; on-ledger sweep marked DEFERRED |
| QUANT-1-6 | major | Correction banner claims deliverable "committed"/"audit-remediated" prematurely | Fixed — reworded to actions taken + resolution commit trail |
| REPRODUCIBILITY-1-1 | major | No 13-field ReproLog for the freeze | Fixed — emitted `repro_log_56b6293a…json` (config_resolved_sha256 = memo SHA) |
| REPRODUCIBILITY-1-2 | major | §4 crux figure not reproduced; contradicts "each section names its test" | Fixed — see QUANT-1-1; added `test_whitened_true_change_detection_rate` |
| FORMAT-1-1 | major | Finding-5 blockquote re-embeds the absolute OS-username path | Fixed — quote sanitized to `<user>`; session_handoff path stripped |
| FORMAT-1-2 | major | Headline constants (0.42, 0.76–0.81) not test-backed | Fixed — 0.42 test-backed; 0.76–0.81 withdrawn |
| QUANT-1-3 / REPRO-1-3 / FORMAT-1-3 | minor | §3 mislabel: "21.3× vs residual innovation" (true ratio = 1/(1−φ)=100) | Fixed — spike 21.27 (stable-sd units), ratio 100, amplification 7.089 stated distinctly |
| QUANT-1-4 | minor | Memo median 20.8 ≠ reproduced 20.15 | Fixed — 20.15 |
| QUANT-1-5 / REPRO-1-4 / FORMAT-1-4 | minor | Constants (rtol, n_seg, n_seed) unjustified; φ=0.99 vs ρ=0.997 unexplained | Fixed — MC-band comments on every constant; φ-monotonicity note |
| QUANT-1-7 / LITERATURE-1-1 | minor | 0.05 mislabeled a "control-chart" reference (Shewhart is 0.0027) | Fixed — reattributed to the significance convention; 0.0027 noted |
| CODE-1-1/2/3/4 | minor | Missing Returns docstrings; uncommented 1e-300; zip strict=False; test annotations | Fixed — all four |
| REPRODUCIBILITY-1-5 | minor | "byte-identical (modulo line endings)" self-contradictory | Fixed — "content-identical after newline normalization" (both docs) |

## Round 2 — 3 minor findings, 0 refuted, all remediated

Branch verdicts: code-reviewer / quant-auditor / literature-check / format-auditor
**accept**; reproducibility-verifier errored on a harness StructuredOutput retry
cap (not a finding; its round-1 concern was already closed by the emitted
ReproLog). No critical/major → **loop exit**.

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| QUANT-2-1 / FORMAT-2-1 | minor | §4 "TP stays 0.82–0.95 down to δ=0.5" not frozen (only δ=3 tested) | Fixed — added `test_whitened_detection_rate_across_shift_sizes` (δ∈{0.5,1.0,3.0}); §4 cites it |
| LITERATURE-2-1 | minor | Withdrawal note's guess that 0.76–0.81 "was the step-2 alarm fraction" is wrong (that is ~0.47) | Fixed — dropped the incorrect provenance guess; state origin undetermined |

## Residual risk (carried, disclosed)

The load-bearing on-ledger ROC (net ≈ 26 pp @ `L_detect ≈ 45` vs ≈ 4 bars) rests
on a secondary source ([session_handoff §2](../research_notes/session_handoff_2026-07-12.md))
with no preserved reproducible artifact — the prior whitened on-ledger run was
never committed and `reports/H900_bocpd_run/` is a content-identical reproduction
of the step-2 non-whitened outputs. The memo discloses this (§4/§5) and marks a
reproducible on-ledger prewhitened ROC/latency re-run as the **deferred**
confirmation. NO-GO robustness currently rests jointly on the frozen synthetic
operating-point evidence and the documented prior probe, not on a reproducible
on-ledger number. Final state: 346 tests pass, ruff clean.
