# Audit trail — Step 2: discovery-alpha reproduction-gap closure (2026-07-18)

**Deliverable:**
[tests/test_discovery_alpha_enactment.py](../../tests/test_discovery_alpha_enactment.py)
(14 enactment-coupling tests),
[tests/test_check_discovery_alpha_reproduction.py](../../tests/test_check_discovery_alpha_reproduction.py)
(2 exit-code-contract tests),
[scripts/audits/check_discovery_alpha_reproduction.py](../../scripts/audits/check_discovery_alpha_reproduction.py)
(reproduction check), memo §A.9 in
[discovery_alpha_cost_calibration_2026-07-12.md](../methodology/discovery_alpha_cost_calibration_2026-07-12.md).
The frozen generator `scripts/run_discovery_alpha_calibration.py` and estimator
`src/skie_universe2/inference/discovery_alpha.py` are UNTOUCHED (numerics not
modified per brief step 2.1).

**Executed reproduction record (S7 evidence):** two executed runs, both
REPRODUCED — frozen `0.7400550140326007` == fresh `0.7400550140326007` (exact
float `==`), 0 field mismatches over the entire artifact, exit code 0.
ReproLogs: `repro_log_de9a810dbeeb4664b9c405e1f6d798cf.json` (pre-remediation
run), `repro_log_53c25c7a11594dcc920d7d65f9b89de4.json` (post-remediation
re-run). The enacted value was not changed, rounded, or re-derived anywhere.

**Mechanism:** audit-remediate workflow, 2 rounds of max 3
(runs `wf_28401379-e9a`, `wf_23daa14b-520`; 5 branches each).

## Round 1 (verdicts: code-reviewer proceed-with-remediation; other four accept)

| ID | Severity | Issue (abbrev.) | Refute gate | Disposition |
|---|---|---|---|---|
| CODE-1-1 | major | Crash inside the check exits 1 — indistinguishable from EXIT_MISMATCH (FINDING) | **CONFIRMED** (refuter reproduced the collision) | **remediated** — body moved to `_run()`; `main()` maps any crash to EXIT_ERROR=2 with traceback to stderr; crash-mapping test added; check RE-EXECUTED post-remediation (exit 0) |
| CODE-1-2 | major | Long `main()` lacks the generator's noqa-justification convention | **REFUTED** (counter-test: PLR0915 inactive — 46 statements vs default 50; convention is enforcement-driven) | dropped with counter-evidence |
| CODE-1-3 | minor | ERROR/FINDING diagnostics on stdout | — | **applied** (stderr) |
| CODE-1-4 | minor | Partial type annotations (`_diff` params, fixtures) | — | **applied** |
| QUANT-1-1 | minor | nan-drop guard is a source pin, not behavioral; drop path unexercised (n_dropped = 0 on this ledger) | — | **partially applied** — pin extended with negative assertions for alternative zero-fill idioms; behavioral test would require modifying the frozen generator (documented in-test); accepted limitation |

## Round 2 (verdicts: all five branches accept; zero critical/major)

| ID | Severity | Issue (abbrev.) | Disposition |
|---|---|---|---|
| CODE-2-1 | minor | Import-time failure still exits 1 (outside `main()`'s handler); traceback disambiguates | **logged, not applied** — benign in the pinned uv env; deferred-import refactor noted for a future edit |
| CODE-2-2 | minor | `list[dict]` unparameterized vs `_diff`'s `list[dict[str, object]]` | **applied** |
| QUANT-2-1 | minor | Memo A.9 diff-record citation ambiguous after the re-run overwrote the scratch file | **applied** — A.9 now states the scratch path holds the LATEST run's record with embedded `check_run_id` |
| LITERATURE-2-1 | minor | Frozen memo body Reference 9 truncates the MPRR title (subtitle ": The Case of Gene Expression Microarrays") | **logged, not applied** — the reference list sits in the FROZEN memo body (pre-§A); correction queued for the next non-frozen edit; attribution/numerics unaffected |

## Post-loop verification

- 16 tests green (14 enactment + 2 exit-code).
- `git diff` clean on the generator and estimator (numerics untouched).
- Substrate pre-flight: recorded dataset checksums (two RC-1 scan JSONs +
  shadow-ledger roll-up, 4811 partitions) match current files exactly.
- Provenance nuance documented (memo §A.9): the original ReproLog's
  `config_resolved_sha256` (`c7788707…`) snapshots the memo pre-remediation;
  the committed memo hashes `b7edc598…`.

## Residual risk

The exact-float reproduction gate is demonstrated on this machine/env only;
BLAS/NumPy version drift could produce a spurious exit-1 FINDING with
unchanged code (the check's ERROR-vs-FINDING separation and the ReproLog env
capture make that diagnosable). The bootstrap nan-drop path remains
behaviorally unexercised on this ledger (0 dropped evaluations); pinned at
source level only.
