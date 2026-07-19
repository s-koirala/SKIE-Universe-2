# Audit trail — A-package: 2026-07-19 authorization records + ADR-0017

*Date: 2026-07-19. Deliverables: the ADR-0015 LIFT AUTHORIZATION RECORD +
schema `lift_record`; ADR-0017 (realized-bar verdict-precondition input,
accepted) + `amended_by` banner + schema `realized_bar_input` addendum;
checker dual-basis extension + tests; DR-1/DR-2 governance-authorization
addendum + OD-D mirror. Loop: audit-remediate (Workflow engine, 5-branch +
adversarial refute gate), 3 rounds (cap), final verdict **ACCEPT (all five
branches)**.*

## Round 1

| ID | Sev | Finding (abbrev.) | Disposition |
|---|---|---|---|
| CR-1-1 | major | Realized-bar reporting call sat outside main()'s try/except: a corrupt M1 artifact raised an unhandled JSONDecodeError AFTER the MET print → OS exit 1 overriding the label-keyed contract (refuter reproduced end-to-end) | REMEDIATED — `realized_bar_report_lines` made total (schema-unreadable / addendum-absent / artifact-absent with tried paths named / artifact-corrupt / malformed-pair all degrade to plain lines) + a belt-and-braces `except Exception` guard in main() |
| CR-1-2..5 | minor | Dual-root artifact resolution; robust experts unpack; stderr reconfigure; robustness tests incl. exit-code immunity | REMEDIATED |
| CR-1-6 | minor | Schema parsed twice (TOCTOU seam) | ACCEPTED residual (harmless at scale) |

Governance documents (ADR-0015 banner, ADR-0017, schema blocks, DR
addendum + OD-D mirror): accepted by all branches in round 1 on content,
grounds citation, not-self-acceptance rationale, and no-decision-body-
rewrite discipline.

## Round 2

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| QUANT-2-1 | major | LABEL-path input errors escaped the except tuple (yaml.YAMLError is not a ValueError; non-mapping schema/record/provenance raise AttributeError) → exit 1 masquerading as BLOCKED; four probes refuter-reproduced | REMEDIATED — `except Exception` contract guard (justified) + shape validation (schema mapping; record object; provenance object) + four main()-level tests |
| QUANT-2-2 | major | String-valued `competence_window_cells` character-decomposed under `set.update` → a demonstrably flippable FALSE MET (refuter reproduced) | REMEDIATED — list-of-str refusal (S6), test-pinned |
| CR-2-1 | minor | Non-str `artifact` value / non-dict `pre_scan_prediction` could raise inside the (guarded) reporter; docstring totality claim | REMEDIATED |

## Round 3 — ACCEPT (cap)

`remediate: []`; all branches accept. Two trail minors applied immediately
post-verdict (free, contract-adjacent): CR-3-1 `expert_hash` must be a
non-empty str (type-strictness at the trust boundary); QUANT-3-1 a fifth
main()-level exit-2 test for the string-cells probe. Suite: 22/22.

## Residual risks (at cap)

- CR-1-6 double schema parse (accepted TOCTOU-at-this-scale residual).
- cp1252 consoles degrade non-ASCII prediction glyphs to replacement
  characters by design (both channels reconfigured).
- The ADR-0017 realized-bar basis carries no numeric bound BY DESIGN
  (operator-weighed, reporting-only; ADR-0017 D3).
- Exotic filesystem/M1 pathologies are absorbed by the belt-and-braces
  guard into degraded report lines rather than tested branch-by-branch.

**Verdict: ACCEPT (3 rounds, cap).** The authorization records are durable;
the checker reports both bases with the exit code keyed on the label rule.
