# Audit trail — Phase B retro Expert Cards (H100–H104)

- **Deliverable:** five retro Expert Cards (ADR-0009) for 1.0 hypotheses
  H050/H052a/H053/H054/H055, registered as H100–H104; register digest;
  hypothesis_backlog.md rows; burned-data ledger mirror rows. Closes
  registered follow-up `P1-2.0-RETRO-CARD-1.0-REGISTER`.
- **Pattern:** audit-remediate loop (Workflow engine `audit-remediate`),
  3 rounds (cap reached), branches routed: quant-auditor, literature-check,
  format-auditor. Every critical/major passed an adversarial refute gate;
  0 findings refuted across all rounds.
- **Source of record:** SKIE-Universe@`ce018515a667`
  research/01_hypothesis_register/{H050,H052a,H053,H054,H055}/.

## Round 1 — verdict: block (8 confirmed, 0 refuted, 12 minors logged)

| ID | Sev | Finding (abbrev.) | Remediation |
|---|---|---|---|
| QUANT-1-1 | critical | H104 card misquoted the frozen 1.0 design (window "2026-06-30" vs registered 2025-12-03/19; MGC/SIL outside frozen universe {ES,NQ,MES,MNQ}; "PF > 1.1" misattributed as registered H_1 vs LW2008 strict dominance) | Registration-conformance note quoting design verbatim; MGC/SIL evidence relabeled post-hoc universe extension; window+universe extensions added to RC-H104-1 trial surface; KPI vector noted as post-freeze ADR-0017/0018/0024 substitution |
| QUANT-1-2 | major | v2 report misquotes v1 C5 basket (−10.0% vs v1's −6.6%) while card claimed "small numerical drift" | §2 footnote documents the reconciliation failure; substrate SHA tags [v1/b93e544]/[v2/317429e4] on every number; reconciliation added to RC-H104-3 |
| QUANT-1-3 | major | Burned-data mirror rows absent despite ready ledger schema | 11 spans appended to config/burned_data_ledger.yaml; §7 cells flipped to recorded |
| QUANT-1-4 | major | H104 §5 "never-worked on ES" contradicted card's own ES-C3 evidence | §5 restated: ES indeterminate; never-worked supported only NQ/SIL |
| LIT-1-1 | major | Dead Tsai 2019 DOI (…2899852) | Corrected to 10.1109/ACCESS.2019.2899177 both occurrences + 1.0 errata note |
| LIT-1-2 | major | 30.33% gate-flip rate presented symbol-generic (ES-only; NQ = 11.77%) | Per-symbol figures everywhere incl. binding_criterion + register digest |
| LIT-1-3 | major | H100 card claimed flip counts/decomposition "not reported" though cited memo reports both (§6.3/§6.4) | Memo evidence added; classification upgraded to cost-bound (memo-supported) with explicit RC-H100-1 rationale |
| FORMAT-1-1 | major | Absolute OS-username paths in Source-of-record links | All converted to SKIE-Universe@ce018515 repo-relative form; C:/Users grep = 0 |

## Round 2 — verdict: proceed-with-remediation (2 confirmed; lit + format accept)

| ID | Sev | Finding (abbrev.) | Remediation |
|---|---|---|---|
| QUANT-2-1 | major | H104 omitted material 1.0 artifact INVESTIGATE-FAILURE-MODE-H055-V2-MGC-CATASTROPHE-VS-SUCCESS.md (cell-level sub-window decomposition, decay-onset assessment, hindsight-bias caveat, two BLOCKING 1.0 follow-ups, third unregistered-window statement) | Memo added to sources-of-record; §5 restated (worked-then-decay-onset on MGC, onset ≈2026-Q2); Phase O.7.5 hindsight caveat in §2 + §6; RC-H104-2/3 cite 1.0 lineage; conformance note extended |
| QUANT-2-2 | major | Cost-share points (52%/87%/37%) rested on an unreconciled unit basis; 1.0 source's own ≈3e-4 drag is internally inconsistent with its formula | Points withdrawn → basis-labeled ranges (NQ ≈13–83%, ES ≈74–99%, H103 ≈2–37%); source inconsistency flagged; priors restated basis-indeterminate |

Folded minors: QUANT-2-3 (full v1↔v2 discrepancy set footnoted), FORMAT-2-1
(H001 backlog placeholders → reserved wording).

## Round 3 — verdict: ACCEPT (all branches; cap reached)

- quant-auditor: all round-2 remediations verified against primary sources
  (design SHAs recomputed, memo/KPI figures matched line-by-line, cost-share
  ranges independently recomputed). One new minor QUANT-3-1 (win-rate range
  42–48% → 36–48% per v1 Table 5) — fixed post-verdict by the lead session.
- literature-check: 19 external citations re-verified; zero new findings;
  Tsai substantive claim verified against the paper abstract.
- format-auditor: no placeholders, no identity leakage, ledger mirrors §7
  spans exactly.

## Documented residuals (logged, not remediated)

QUANT-1-5/6/7, QUANT-2-4 (H104 burned-span end-date basis),
LITERATURE-1-4/5/6/7, LITERATURE-2-1 (MacLean-Thorp-Ziemba 2010-vs-2011
volume dating, inherited from frozen 1.0 design), LITERATURE-2-2 (Zarattini
grouping label), FORMAT-1-3/4. Structural residual: cards transcribe but do
not re-derive 1.0 statistics; unflagged 1.0-internal errors propagate until
the RC-H10x admission scans re-materialize the series from the shadow ledger.

## Disposition summary (ADR-0009 vocabulary; "fail" not used)

| Card | 1.0 HID | Disposition |
|---|---|---|
| H100 | H050 | re-specify-cost-bound (memo-supported) |
| H101 | H052a | arsenal-admit-conditional |
| H102 | H053 | re-specify-cost-bound |
| H103 | H054 | arsenal-admit-conditional (structurally unpowered; shadow-ledger accumulation required) |
| H104 | H055 | arsenal-admit-conditional (explicitly post-hoc basis; fresh admission cycle required) |

Follow-up scans RC-H100-1 … RC-XCORR-1 enumerated in
[retro_card_register_2026-07-10.md](../research_notes/retro_card_register_2026-07-10.md).
