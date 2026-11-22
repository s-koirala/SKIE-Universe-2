---
schema_version: "WI-3-§2-v1"
conforms_to: "skills/audit-remediate-loop/SKILL.md §Audit-trail field spec (WI-3 §2)"
title: "Audit trail — canonical performance-tearsheet tooling + H107 instance"
type: audit_trail
date: 2026-11-22
started_at: "2026-11-22T11:40:00-0600"
ended_at: "2026-11-22T12:10:00-0600"
artifacts:
  - path: src/skie_universe2/reporting/tearsheet.py
    git_head: 2c24fe0c1942fb3fb52ef65b82814d18887e2934
    sha256: ac9a8b10d63d77ba7158e24bd01cfe60f604408c1bf171b2c6bca3963c94704d
  - path: scripts/build_tearsheet.py
    git_head: 2c24fe0c1942fb3fb52ef65b82814d18887e2934
    sha256: cb097db4d34b81f86ab01e2f9553790c94b35e345335f6db220b61e5cbd38dae
  - path: docs/templates/tearsheet_template.html
    git_head: 2c24fe0c1942fb3fb52ef65b82814d18887e2934
    sha256: 01eb9cf8484e81bf7f1be0fd1da56e51ab770eba7dda514a20c5fd302edd256f
  - path: tests/test_tearsheet.py
    git_head: 2c24fe0c1942fb3fb52ef65b82814d18887e2934
    sha256: 71d21e6fb6085c32e90c2ba50dfe39a6bdbe34eb6b85f5bf0c33004976124780
  - path: reports/H107/H107_tearsheet.html
    git_head: 2c24fe0c1942fb3fb52ef65b82814d18887e2934
    sha256: 3d696b8a3214cf3655ffa24c4510815fc960afc32661366c18a0c059d0461cd3
repo_head: 2c24fe0c1942fb3fb52ef65b82814d18887e2934
worktree_clean: false
audit_criteria:
  task_spec: >
    Save the H107 tearsheet as a reusable, canonical report generator for other
    hypotheses; render the H107 instance into the repo; and commit + push all of
    this session's work. The reporting module is a diagnostic exhibit renderer
    (equity, drawdown, Monte Carlo, monthly, metrics) over audited shadow-ledger
    per-session series; it certifies nothing.
  consulted:
    - path: CLAUDE.md
      sha256: 2d195b936f4140c6fa9d36ee50874b48736e904c494543c0016067f995e70687
    - path: ~/.claude/CLAUDE.md
      sha256: 5bdabead8ae5be6265623f857580c26c95479f5192ba9db1662f2ba23ee6f328
    - path: ~/.claude/rules/quant-project.md
      sha256: 0c71a7f95c9d6c325bce42bb78a3ed88b1434efeb736b8c2fce0859dc695e181
mechanism: "audit-remediate-loop — parallel-Agent fallback (NOT the Workflow engine); 2 specialist branches, each with its own adversarial refute step; converged round 1, all 13 findings remediated. WI-38 Workflow run_id/transcript_dir not applicable."
agents:
  - branch: code-reviewer
    agent_def_path: ~/.claude/agents/code-reviewer.md
    model_id: claude-opus-4-8
    effort: default
    role: "code quality, ledger-load/cost cross-check, artifact-page contract (CSP/DOCTYPE/theme)"
  - branch: quant-auditor
    agent_def_path: ~/.claude/agents/quant-auditor.md
    model_id: claude-opus-4-8
    effort: default
    role: "statistical correctness of the metric + Monte-Carlo formulas (log/simple conventions)"
operator: "SKIE (principal)"
acted_on_behalf_of: "SKIE (principal); 'save this tearsheet template … make canonical. commit and push all findings and work from this session' (chat 2026-11-22)"
routing: "quant-project cwd → quant-auditor (epi-auditor excluded); new reporting module + template → code-reviewer. Branches scoped to the reporting tooling; the metric formulas to quant-auditor, the IO/template/style to code-reviewer."
rounds_completed: 1
rounds_cap: 3
cap_reached: false
verdict: accept
counts:
  critical: 0
  major: 2
  minor: 11
  remediated: 13
  refuted_dropped: 2
  logged_no_change: 0
  deferred: 0
sidecar:
  path: docs/audits/audit_trail_tearsheet-tooling_2026-11-22.sidecar.json
  sha256: dce85ac6475a32d9c962db09a6dfaa69c8261abbbe8868eff44679d7a6a43c02
---

# Audit trail — canonical performance-tearsheet tooling

**Deliverable.** A hypothesis-agnostic reporting module — pure-analytics library
[tearsheet.py](../../src/skie_universe2/reporting/tearsheet.py), data-driven
[tearsheet_template.html](../templates/tearsheet_template.html), CLI
[build_tearsheet.py](../../scripts/build_tearsheet.py), and
[test_tearsheet.py](../../tests/test_tearsheet.py) (10 tests) — that renders any
shadow-ledger `expert_id`'s per-session gross/net log-return series into a
MultiCharts/TradingView-style report (equity, drawdown, iid-bootstrap Monte
Carlo, monthly-return grid, per-session histogram, metrics table, optional
screen-verdict panel). First rendered instance:
[reports/H107/H107_tearsheet.html](../../reports/H107/H107_tearsheet.html)
(EMA_9, Kelly 1.0, ES/NQ). **The output is a diagnostic exhibit; it certifies
nothing and is not a deployable strategy.**

## Round 1 — findings (converged; all 13 remediated, 2 refuted-and-dropped)

Both branches confirmed the two cross-checks that validate the committed H107
numbers are clean: `build_tearsheet` loads the ledger and recovers turnover and
net variants byte-equivalently to `run_screen_h107`/`grid_screen`, and the
NinjaTrader variant selection isolates the E-mini parent (no MES/ES swap).

| id | branch | sev | target | disposition | summary |
|---|---|---|---|---|---|
| CR-1-1 | code-reviewer | major | subject | remediated | `sd['dsr_bound']` KeyError on a degenerate cell crashed the whole build → all `s_d` fields read via `.get()`, degenerate renders gracefully |
| CR-1-2 | code-reviewer | major | subject | remediated | template had no CSP → now a complete HTML doc with a meta CSP (default-src/connect-src 'none'; script cdnjs+inline; fonts allowed) |
| CR-1-3 | code-reviewer | minor | subject | remediated | dead `spy_sqrt` local removed |
| CR-1-4 | code-reviewer | minor | subject | remediated | `<!DOCTYPE html>` + head/body added (standards mode) |
| CR-1-5 | code-reviewer | minor | subject | remediated | `args.title` now `html.escape`d; `__DATA__` substituted before `__TITLE__` |
| CR-1-6 | code-reviewer | minor | subject | remediated | finite-guard added — a ruin (-inf) row hard-fails instead of becoming a silent null |
| CR-1-7 | code-reviewer | minor | subject | remediated | function-local `yaml`/`per_unit_drag` imports hoisted to module top |
| CR-1-8 | code-reviewer | minor | apparatus | remediated | exhibit constants (n_mc/cone/bins/downsample/seed) → named constants with a `# justify:` block |
| CR-1-9 | code-reviewer | minor | apparatus | remediated | `return_hist` docstring added |
| F-1-1 | quant-auditor | minor | subject | remediated | drawdown/MaxDD now reference the 1.0 inception (first-session loss is a real drawdown); applied in `drawdown()` and the MC maxdd |
| F-1-2 | quant-auditor | minor | subject | remediated | profit factor now simple-return gross-profit/gross-loss (`expm1`), the platform convention, not a sum of logs |
| F-1-3 | quant-auditor | minor | subject | remediated | zero-downside Sortino → `+inf` (renders "—"), not a misleading 0.0 |
| F-1-4 | quant-auditor | apparatus | apparatus | remediated | module/MC docstrings now state iid resampling understates risk under serial dependence |

## Refute-gate dispositions

| candidate | gate outcome | basis |
|---|---|---|
| CR-R1 "MES/ES contract-selection bug" | REFUTED, dropped | `contract != symbol` provably excludes micros; E-mini parent isolated |
| CR-R2 "turnover reconstruction diverges from the screen" | REFUTED, dropped | `/2.0` half-notional drag + median-reference-price construction byte-identical to `grid_screen` |
| CR-1-1 … CR-1-9, F-1-1 … F-1-4 | CONFIRMED | remediated (see table) |

## Verification of remediations

- `uv run ruff check` on the reporting module, CLI and tests → **clean** (23
  pre-remediation lint issues, incl. line-length and `timezone.utc`→`UTC`, fixed
  via ruff format + autofix + one manual f-string split).
- `uv run pytest tests/test_tearsheet.py` → **10 passed** (incl. the new
  inception-drawdown test and the updated simple-PF / inf-Sortino assertions).
- CLI re-run regenerated the H107 instance: **ES −77.2% / Sharpe −0.855 / MaxDD
  −77.7%; NQ −23.9% / −0.126 / −45.4%** (unchanged by the inception fix — the
  first session is not the worst drawdown), confirming the generalization
  reproduces the scratchpad numbers.
- Generated HTML: has `<!DOCTYPE html>` + CSP, the inline JSON parses, the
  document closes `</body></html>`, and the app script passes `node --check`.

## Deferred / logged minors

None. All findings were remediated this round; nothing deferred.

## Residual risk

- **MC iid assumption** — the Monte Carlo cone is a path-reshuffle that discards
  serial dependence; under positive autocorrelation it understates cone width
  and drawdown risk (now documented in the module/function docstrings). A
  stationary-block variant (Politis-Romano 1994) is a possible future option,
  not implemented.
- **CSP `'unsafe-inline'` for script** — the page's own inline bootstrap runs
  under `script-src … 'unsafe-inline'` (no hash/nonce), acceptable for a trusted
  self-generated file with the title escaped and the JSON non-executable;
  `default-src`/`connect-src 'none'` still block all network egress.
- **Sampling caveat** — two branches (code quality, formula fidelity) at effort
  default via the parallel-Agent fallback; critical-reviewer, scope-auditor and
  reproducibility branches were not run (the tooling is a diagnostic renderer and
  emits no ReproLog — there is no artifact-producing inference run to reproduce).
  Where no empirical check applied (the HTML contract, magic-number style), the
  refute gate ran without an empirical backstop.

## AI-assistance statement (ICMJE §V.A)

- **Model:** Claude Opus 4.8 (`claude-opus-4-8`) — author and both audit branches
  (branch models inherited the session default).
- **Roles:** *idea* = user (make the tearsheet canonical for other hypotheses);
  *code* = Claude (library, template, CLI, tests, remediations); *audit* = Claude
  (2 branches + refute gates).
- **Reproducibility logs:** n/a — the tooling is a diagnostic renderer over the
  already-audited RC-H107-1 ledger series, not an artifact-producing inference
  run. The underlying H107 evidence's ReproLogs are under `logs/reproducibility/`.

## Immutability and retention

Append-only (21 CFR 11.10(e)): corrections are appended as a dated addendum. The
tearsheet tooling is reusable infrastructure (no ledger writes); the rendered
H107 instance is a derived exhibit of the archived `archive-no-persistent-window`
screen and asserts no new disposition.
