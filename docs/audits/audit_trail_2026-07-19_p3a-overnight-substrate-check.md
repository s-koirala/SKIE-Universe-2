# Audit trail — P3-A overnight/Globex substrate feasibility check

*Date: 2026-07-19. Deliverable: the Phase-3 P3-A feasibility gate
([overnight_globex_substrate_feasibility_2026-07-19.md](../research_notes/overnight_globex_substrate_feasibility_2026-07-19.md)
+ harness [run_overnight_substrate_check.py](../../scripts/run_overnight_substrate_check.py)
+ artifact `reports/P3A_overnight_substrate/overnight_substrate_check.json`).
Loop: audit-remediate (Workflow engine, 5-branch specialist ensemble +
adversarial refute gate), 2 rounds, clean exit (round-2 `remediate: []`).*

Branches routed: code-reviewer, quant-auditor, reproducibility-verifier,
literature-check (format flags off; no epi routing). Verdicts round 1:
accept / accept / proceed-with-remediation / proceed-with-remediation;
round 2: no surviving critical/major.

## Round 1 — findings and dispositions

| ID | Sev | Finding (abbrev.) | Refute gate | Disposition |
|---|---|---|---|---|
| LITERATURE-1-1 | major | Report's 1-minute-substrate sentence quoted the 5-min-grid halt totals (562/526) as 1-min counts; "~230 sessions" misstated NQ (196); "~0.01% of rows" understated the 0.076% share | **CONFIRMED** (refuter reproduced every element from the JSON; no counter-evidence) | REMEDIATED — sentence rewritten with 1-min counts 2,521 ES / 2,286 NQ, 228/196 sessions, <0.1%, 5-min figures labeled |
| LITERATURE-1-2 / REPRODUCIBILITY-1-1 / QUANT-1-2 | minor | "~69–70%" overnight-ETH share excludes NQ's 67.85%; text designated for verbatim design.md propagation | n/a (minor) | REMEDIATED (design-propagating): per-instrument 69.0% ES / 67.8% NQ in report + H105 design.md |
| REPRODUCIBILITY-1-2 | minor | Same hour-17 sentence, share + session-count figures | n/a | REMEDIATED with LITERATURE-1-1 |
| CODE-1-1 | minor | Two E501 line-length violations | n/a | REMEDIATED (justify comments wrapped) |
| CODE-1-2 | minor | `str(None)` serialized as `"None"` for empty terminal windows | n/a | REMEDIATED (JSON null) |
| CODE-1-3 | minor | Obscure singleton-list comprehension for gap/window pairing | n/a | REMEDIATED (filter + zip strict) |
| CODE-1-4 | minor | Bare `dict` annotations | n/a | LOGGED, not remediated (auditor: do not block) |
| CODE-1-5 | minor | Session-segment classifier script-local; the H105 expert needs the same boundaries (drift risk) | n/a | REMEDIATED — extracted to [utils/sessions.py](../../src/skie_universe2/utils/sessions.py) `session_segment_expr` + constants, 9 boundary/DST unit tests ([test_session_segments.py](../../tests/test_session_segments.py)) |
| QUANT-1-3 | minor | 0.05/0.95 summary quantiles lacked a justify comment | n/a | REMEDIATED |

Post-remediation the harness was re-run: **bit-identical statistics**, new
ReproLog run `5e370d881cbe` (supersedes `45ce4594e92b` as the run of record).

## Round 2 — verification sweep

`remediate: []` — no critical/major. Six minors, all applied:

| ID | Finding (abbrev.) | Disposition |
|---|---|---|
| CODE-2-1 / REPRODUCIBILITY-2-1 / LITERATURE-2-1(a) | NQ excluded-session share 3.67% → 3.66% (double-rounding of 0.036647) | REMEDIATED |
| QUANT-2-1 / LITERATURE-2-1(b) | NQ overnight-ETH share 67.9% → 67.8% (double-rounding of 67.848%; propagated to H105 design.md) | REMEDIATED (both files) |
| LITERATURE-2-2 | Exchange-schedule constants lacked a CME primary citation (values verified CORRECT against cmegroup.com trading hours) | REMEDIATED (citation added in sessions.py) |
| LITERATURE-2-3 | ES end-date convention ambiguity (UTC bar-date 2025-12-03 vs CME session-date 2025-12-04) | REMEDIATED (convention parenthetical added) |

## Residual risk

- Bare `dict` annotations in the one-shot harness (dispositioned
  non-blocking).
- Segment tests do not cover the 16:59/17:59 sub-edges (implied by the
  tested 17:00/18:00 half-open edges) or the fall-back ambiguous local hour
  (outside every segment boundary).
- CME primary documentation verified via the public trading-hours page; the
  contract-spec PDF was not fetched (tier-2 web source; values corroborated
  by the substrate's own hour histograms).
- The report's §4 explicitly bars quoting coverage numbers as edge evidence;
  no evidence claim is present (verified by two branches).

**Verdict: ACCEPT (2 rounds).** Run of record: ReproLog `5e370d881cbe`.
