---
schema_version: "WI-3-§2-v1"
conforms_to: "skills/audit-remediate-loop/SKILL.md §Audit-trail field spec (WI-3 §2)"
title: "Audit trail — RC-H107-1 screen (session-VWAP × EMA(N) crossover grid), disposition + Expert Card"
type: audit_trail
date: 2026-11-22
started_at: "2026-11-22T10:15:00-0600"
ended_at: "2026-11-22T11:27:03-0600"
artifacts:
  - path: reports/H107/rc_h107_1_screen.json
    git_head: a4cf00454e8c97dbf45cd492f4fd3d4bcae8a1a4
    sha256: ee950594fd1279e580732e83a0f8487a23c8a406d6adc4c867ac3d449a14acc7
  - path: research/01_hypothesis_register/H107/expert_card_v1.md
    git_head: a4cf00454e8c97dbf45cd492f4fd3d4bcae8a1a4
    sha256: 3e96d86607d62776efcea7c46e3b2821bf0921f470610ee4a61b1d1fc583547c
  - path: scripts/run_shadow_ledger_backfill.py
    git_head: a4cf00454e8c97dbf45cd492f4fd3d4bcae8a1a4
    sha256: 7fa5a77b170ac73545d841d5f9e6395e195ade7039cb262ee94adc09c9a0cdd6
    note: "defer-manifest patch — modified in the working tree this session; committed in this trail's commit"
repo_head: a4cf00454e8c97dbf45cd492f4fd3d4bcae8a1a4
worktree_clean: false
audit_criteria:
  task_spec: >
    Execute the frozen H107 (RC-H107-1) ADR-0014 SCREEN on the canonical shadow
    ledger and gate the resulting pool-hold-reconsider/archive-null disposition
    + Expert Card through audit-remediate-loop, stopping before any set-level
    verdict, Kelly-fraction selection, or EMA-span selection.
  consulted:
    - path: CLAUDE.md
      sha256: 031aa589ee45a83117253f39aacb262a00bf48354c0a658febce09b8982f41d9
    - path: ~/.claude/CLAUDE.md
      sha256: 5bdabead8ae5be6265623f857580c26c95479f5192ba9db1662f2ba23ee6f328
    - path: ~/.claude/rules/quant-project.md
      sha256: 0c71a7f95c9d6c325bce42bb78a3ed88b1434efeb736b8c2fce0859dc695e181
    - path: research/01_hypothesis_register/H107/design.md
      sha256: 912198045de4bee2dbffebf9efaa2998c8553431c2898f1367cebf8fd24b1397
mechanism: "audit-remediate-loop — parallel-Agent fallback (NOT the Workflow engine); 4 specialist branches, each carrying its own adversarial refute step; 3-round cap, converged in round 1. WI-38 Workflow run_id/transcript_dir not applicable (no Workflow run)."
agents:
  - branch: literature-check
    agent_def_path: ~/.claude/agents/literature-check.md
    model_id: claude-opus-4-8
    effort: default
    role: "verify the single support citation (Gao et al. 2018) and judge over-claim"
  - branch: code-reviewer
    agent_def_path: ~/.claude/agents/code-reviewer.md
    model_id: claude-opus-4-8
    effort: default
    role: "review the defer-manifest driver change for the ADR-0011 D4 completeness guarantee"
  - branch: quant-auditor
    agent_def_path: ~/.claude/agents/quant-auditor.md
    model_id: claude-opus-4-8
    effort: default
    role: "screen statistical-method fidelity to design §5/§8"
  - branch: reproducibility-verifier
    agent_def_path: ~/.claude/agents/reproducibility-verifier.md
    model_id: claude-opus-4-8
    effort: default
    role: "reproducibility envelope — ReproLogs, substrate/design-SHA binding, seed determinism"
operator: "SKIE (principal)"
acted_on_behalf_of: "SKIE (principal); orchestration + defer-manifest fix + resume authorized in chat 2026-11-22"
routing: "quant-project cwd → quant-auditor (epi-auditor excluded by the co-run rule); code change → code-reviewer; citations → literature-check; reproducibility → reproducibility-verifier. Branches scoped by the /orchestrate delegation spec (deliverable_spec_h107-screen_469c1ea1-c77_2026-11-22.md)."
rounds_completed: 1
rounds_cap: 3
cap_reached: false
verdict: accept
counts:
  critical: 0
  major: 2
  minor: 6
  remediated: 3
  refuted_dropped: 5
  logged_no_change: 6
  deferred: 0
sidecar:
  path: docs/audits/audit_trail_h107-screen_2026-11-22.sidecar.json
  sha256: 95d580b4c77d4fb67a9d4478ac81357e9f2adda8a440c6eda8b24a5ac7f77e51
---

# Audit trail — RC-H107-1 screen (H107 session-VWAP × EMA(N) crossover grid)

**Deliverable.** The ADR-0014 SCREEN of H107 on the canonical k1.0 shadow
ledger (7 EMA spans × ES/NQ): [rc_h107_1_screen.json](../../reports/H107/rc_h107_1_screen.json),
the ADR-0009 [expert_card_v1.md](../../research/01_hypothesis_register/H107/expert_card_v1.md),
and the supporting defer-manifest fix to the backfill driver. **Disposition of
record: `archive-no-persistent-window`** — no grid point clears S-a…S-e; H107 is
NOT admitted, the provisional pool is unchanged, the arsenal stays EMPTY, and no
set-level verdict, Kelly fraction, or EMA span was selected.

**Result in one line.** Gross edge is present-but-tiny on 13/14 cells (S-c
passes), net is negative at every registered cost variant, and the Deflated
Sharpe is ~1e-24…1e-15 on every cell — far below the S-d bound 0.2599 — so no
grid point's edge survives the 87-trial deflation. This is the design's modal
a-priori outcome (cost-dominated / net-not-monetizable whipsaw; §1).

## Round 1 — findings (converged: zero subject-stream critical/major survive)

The screen itself (quant-auditor) and the citation (literature-check) returned
**accept with zero defects**. The two majors are both reproducibility findings
about the *run state*, remediated by committing the executed tree; the code
change carried one remediated minor.

| id | branch | sev | target | category | disposition | summary | failure scenario |
|---|---|---|---|---|---|---|---|
| F-1 | reproducibility-verifier | major | subject | reproducibility | remediated (this commit) | design §11 won't reproduce from clean HEAD a4cf004 — needs the uncommitted defer-manifest driver patch | `git checkout a4cf004 && <§11>` times out at the ema9 ES backfill write on a clean machine |
| F-2 | reproducibility-verifier | major | subject | reproducibility | remediated (this commit) | whole run executed on a dirty tree; HEAD pins env (uv.lock) but not code/manifest — only `working_tree_hash` does | one-command reconstruction from HEAD yields a different driver than the one that ran |
| CR-Minor-1 | code-reviewer | minor | subject | correctness | remediated | builder-missing was a soft-skip → exit 0 with a stale manifest (silent ADR-0011 D4 waiver) | if `build_data_manifest.py` were absent, the backfill exits success with an incomplete manifest |
| F-3 | reproducibility-verifier | minor | subject | reproducibility | logged + follow-up | screen binds substrate via `data/_manifest.json`, not by re-hashing scanned parquet bytes; no `--check` gate | a manifest stale vs on-disk ledger would bind manifest state rather than the evidence read |
| L-1 | literature-check | minor | subject | citation | logged (accept) | Gao et al. 2018 exists, attributed correctly, used within scope with explicit hedging; Crossref PENDING discharged | n/a — informational pass |
| CR-Minor-2 | code-reviewer | minor | apparatus | robustness | logged (no change) | `check=True` is the intended loud-fail — confirmed correct | n/a |
| CR-Minor-3 | code-reviewer | minor | subject | robustness | logged (no change) | single deferred pass runs unbounded (no timeout) — acceptable vs a magic-number timeout | a genuinely hung subprocess blocks the one-shot driver with no diagnostic |
| CR-Minor-4 | code-reviewer | minor | apparatus | style | logged (no change) | `capture_output` omitted vs the per-write path (builder output streams to console) | n/a — benign, no manifest-content effect |

## Refute-gate dispositions

Every candidate defect the quant-auditor raised against the screen statistics
was put through an adversarial refutation and **dropped** (the method is
faithful); the two confirmed reproducibility majors and CR-Minor-1 survived
their gates and were remediated.

| candidate | gate outcome | basis |
|---|---|---|
| QA-R1 "DSR floored/degenerate" | REFUTED, dropped | no clip/guard; DSR varies smoothly 2.98e-24→1.30e-15 tracking Sharpe; independent z-recompute (SR~0.02 vs 87-trial benchmark 0.1909 → z≈−8…−10) matches to leading order; `0.000` is `:.3f` console rounding, JSON has full precision |
| QA-R2 "masked estimator / wrong block column" | REFUTED, dropped | explicit `romano_wolf_stepm_panel` on T×7; block length from `g[:, ema9]`; monotone adjusted-p matches panel step-down |
| QA-R3 "level transcribed not read" | REFUTED, dropped | `screen_level(paths)` reads YAML at runtime; `dsr_bound = 1 − 0.7400550140326007` exactly complementary |
| QA-R4 "PBO matrix mis-constructed" | REFUTED, dropped | inner-join panel finite; `member_only_sharpe` = per-column Sharpe; S=16 → C(16,8)=12870 as reported |
| QA-R5 "routing wrong (should be pass / no-gross-edge)" | REFUTED, dropped | no cell clears all gates (DSR fails all); S-c passes somewhere → no-gross-edge sub-reason correctly not taken |
| F-1, F-2 (repro majors) | CONFIRMED (refute gate FALSE: HEAD blob has `ShadowLedgerWriter(paths=paths)` manifest-on; ReproLogs `git_dirty=true`) | remediated by committing the executed tree |
| CR-Minor-1 | CONFIRMED | remediated (helper now raises on missing builder) |

## Deferred / logged minors

- **L-1 (logged, accept).** Citation is clean and correctly hedged. The design's
  "Crossref verification: PENDING" flag is empirically discharged by this run,
  but **design.md is frozen (SHA 912198045de4) and is NOT edited**; the discharge
  is recorded here and in the sidecar only.
- **CR-Minor-2/3/4 (logged, no change).** Confirmed-correct / acceptable-tradeoff
  / benign respectively; see table.
- **F-3 (logged + follow-up).** Registered as a non-blocking follow-up
  **`P1-2.0-SCREEN-MANIFEST-DISK-CHECK`**: add a `build_data_manifest.py --check`
  (manifest == disk) assertion as the screen's first step. Empirically clean this
  run (digest recomputed → exact match; append-only ledger + immediate single
  rebuild).
- **quant-auditor observational note (logged).** DSR count surface (87) and
  dispersion surface (32) differ; design-acknowledged (§8 audit finding 6);
  immaterial — DSR ~1e-15 is orders of magnitude below the 0.2599 bound, so no
  dispersion-pool change flips the outcome.

## Verification of remediations

- **CR-Minor-1.** `_rebuild_full_manifest` now raises `FileNotFoundError` on a
  missing builder (loud fail). `uv run python -m py_compile scripts/run_shadow_ledger_backfill.py`
  → OK. Behaviorally inert for this run (builder present), so the in-flight
  backfill was unaffected.
- **F-1 / F-2.** Remediated by committing the executed tree (driver patch +
  rebuilt `data/_manifest.json` + run artifacts) in this trail's commit, which
  pins `repo_head` to the code that ran. The frozen §11 commands are unchanged
  and reproduce against the committed patched driver (the driver is referenced
  infrastructure, not part of the frozen design; design SHA 912198045de4
  unchanged). The 56 ledger streams were canary-PASS at write and the manifest
  single-rebuild end-state was verified byte-equivalent (ema9 k1.0 digest match).
- **Screen integrity (no remediation needed).** quant-auditor confirmed S-c
  (panel RW, seed 20261122, PW block length on ema9), S-d (DSR + CSCV PBO S=16,
  n_trials_gate 87), exact-from-ledger turnover (verified to the penny), and §10
  routing all faithful to the frozen design.

## Residual risk

- **F-3** — screen substrate binding is manifest-mediated, not re-hashed from the
  bytes actually scanned (empirically clean this run; follow-up registered).
- **Upstream ledger generation** (gross/turnover) and the register-trial Sharpes
  feeding `sr_std` are outside the screen's code and the quant-auditor's stated
  scope; ledger provenance is separately bound by the backfill ReproLogs.
- **CR-Minor-3** — the single deferred manifest pass runs unbounded by design.
- **Sampling caveat.** Four specialist branches (citation, code, statistical
  fidelity, reproducibility) ran at effort **default** via the parallel-Agent
  fallback, scoped by the orchestrate delegation spec. `critical-reviewer` and
  `scope-auditor` of the full orchestrate contract were NOT run as separate
  branches this round; the frozen H107 design carries a prior 1-round upstream
  audit ([audit_trail_2026-11-22_h107-preregistration.md](audit_trail_2026-11-22_h107-preregistration.md),
  design SHA 912198045de4). A different branch set, seed, or effort could surface
  findings not seen here. No empirical backstop beyond the on-ledger screen itself
  was available for the prose findings.

## AI-assistance statement (ICMJE §V.A)

- **Model:** Claude Opus 4.8 (`claude-opus-4-8`) — orchestrator and all four
  specialist audit branches (branch models inherited the session default; the
  agent definitions specify no model override).
- **Roles:** *idea* = operator (principal-proposed VWAP×EMA rule, 2026-11-22);
  *code* = Claude (defer-manifest driver fix + Minor-1 hardening); *execution* =
  Claude (frozen backfill → screen → Expert-Card harness, unmodified);
  *audit* = Claude (4 branches + refute gates).
- **Reproducibility logs:** `logs/reproducibility/` (15 ReproLogs: 14
  `shadow_ledger_write` + 1 `rc-h107-1-screen`).

## Immutability and retention

Append-only (21 CFR 11.10(e)): corrections are added as a dated addendum, never
overwritten; a second round would append a new round section to this file. The
shadow ledger (ADR-0003) and the `rc-h107-1` trial register, burned-data ledger,
and Expert Card are append-only; this run added 56 ledger streams, 14 `rc-h107-1`
trial records, 30 burned spans, and 0 pool records (null disposition). The
disposition of record is `archive-no-persistent-window`; it is reconsideration-
eligible only under the ADR-0014 rules, not editable in place.
