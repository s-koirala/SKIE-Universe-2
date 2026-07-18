# Audit trail — Step 1: ADR-0015 pool-HOLD ratification (2026-07-18)

**Deliverable:** [ADR-0015](../decisions/ADR-0015-ratified-pool-hold-verdict-precondition.md)
(status: proposed), `verdict_precondition` block in
[config/pool_ledger_schema.yaml](../../config/pool_ledger_schema.yaml),
[scripts/audits/check_verdict_precondition.py](../../scripts/audits/check_verdict_precondition.py)
(reporting check), [tests/test_check_verdict_precondition.py](../../tests/test_check_verdict_precondition.py).

**Mechanism:** audit-remediate workflow, round 1 of max 3
(run `wf_a3103c83-693`; 5 parallel branches: code-reviewer, quant-auditor,
reproducibility-verifier, literature-check, format-auditor).

**Round-1 verdicts:** all five branches **accept**. Zero critical, zero major.
Loop exits at round 1 (no critical/major to refute or remediate).

## Findings and dispositions (all minor)

| ID | Location | Issue (abbrev.) | Disposition |
|---|---|---|---|
| CODE-1-1 | check_verdict_precondition.py | EXIT_ERROR diagnostics printed to stdout, conflating report stream with error stream | **applied** — error path now prints to stderr |
| CODE-1-2 | check_verdict_precondition.py | `ProjectPaths.discover()` called unconditionally outside try; fully path-specified invocation could traceback instead of exit 2 | **applied** — discovery lazy + inside try; RuntimeError mapped to EXIT_ERROR |
| QUANT-1-1 | ADR-0015 ground (c) | Heading generalized a cell-specific rotor result (only the RC-H101-1 primary high_vol cell has a rotor comparison on record) | **applied** — heading and body re-scoped to "the sole null-allocator comparison on record"; RC-2 competence cells explicitly noted as rotor-untested (verdict-tier object) |
| QUANT-1-2 | check_verdict_precondition.py | Missing `competence_structure.competence_window_cells` silently became empty coverage (schema-drift degradation) | **applied** — absent field now raises (exit 2); explicitly-empty list stays valid/excluded; test added (10 tests total, green) |
| REPRODUCIBILITY-1-1 | check_verdict_precondition.py | Checker report not self-provenancing (no ledger SHA / date echoed) | **logged, not applied** — explicitly non-blocking per the finding; the check is reporting-only by ADR-0015 design; revisit if the report is ever cited as evidence |
| LITERATURE-1-1 | ADR-0015 Context | Operator-ratification claim not pinned to a durable committed artifact | **logged, not applied** — the session trail (`docs/audits/session_trail_2026-07-18.md`) is deliberately untracked (never-stage rule), so citing it would dangle for a clone; the ADR's `status: proposed` design makes operator acceptance itself the durable ratification record (mitigation noted by the auditor) |

## Post-remediation verification

- `pytest tests/test_check_verdict_precondition.py`: **10 passed**.
- Live checker: `BLOCKED: distinct_expert_hash_count = 1`, exit code 1
  (acceptance criterion met).
- `config/pool_ledger_schema.yaml` parses (yaml.safe_load).
- `data/processed/pool_ledger/pool_ledger.jsonl` untouched (no disposition
  change); no pre-commit/CI wiring added.

## Residual risk

Low. The ADR is `status: proposed` and enacts nothing until operator
acceptance; the precondition is reporting-only; the checker refuses malformed
input rather than degrading. Nothing is certified; the arsenal remains EMPTY;
no register increment occurred (no scan ran).
