# Audit trail — H101 ORB pre-registration (2.0 re-specification of 1.0 H052a)

**Deliverable:** [research/01_hypothesis_register/H101/design.md](../../research/01_hypothesis_register/H101/design.md)
— the frozen 2.0 pre-registration for hypothesis H101, the unconditional first-hour
opening-range-breakout expert on ES/NQ, the **first forward arsenal-admission
candidate** on the shadow ledger (promoted from the retro Expert Card of 1.0
H052a, disposition `arsenal-admit-conditional`). Pre-registers the H101 ORB expert
(backfilled to the ADR-0003 ledger) and the RC-H101-1 ADR-0002(c) admission scan.

**Mechanism:** [audit-remediate-loop](../../../.claude/skills/audit-remediate-loop)
via the Workflow engine, `.md` routing → **quant-auditor**, **literature-check**,
**format-auditor**, adversarial refute gate. Runs: round 1 `wf_3355f620-54f`,
round 2 `wf_189203d0-778`.

**Outcome:** ACCEPT at round 2 (all three branches accept; all round-1 findings
verified resolved). Round 1 raised 3 remediate-level findings (1 critical, 2 major)
+ 2 minors; all remediated.

## Round 1 — verdict: proceed-with-remediation (3 majors/critical, 0 refuted, 2 minors); format-auditor ACCEPT

| ID | Branch | Issue | Disposition |
|---|---|---|---|
| LITERATURE-1-1 / QUANT-1-1 | lit / quant | **Ledoit-Wolf 2008 DOI `10.1198/073500105000000063` actually resolves to Hansen 2005 SPA** — a real misattribution; the project's own `rules/quant-project.md` has the correct DOI. | **Fixed** — → `10.1016/j.jempfin.2008.03.002` in frontmatter + §8; the wrong DOI fully removed |
| QUANT-1-2 | quant | **No stationarity diagnostic** on the per-session ORB gross-return series, which the block bootstrap / Romano-Wolf / Lo-2002 stack presumes (the user's Verification directive requires it) | **Fixed** — §8 registers a KPSS level+trend test (Kwiatkowski et al. 1992) + a rolling-origin sub-window mean/variance stability exhibit, with a documented action-if-rejected (report the break, ADR-0009 re-specify path, per-window dispersion as the primary stability read) |
| LITERATURE-1-2 | lit | **Zarattini 2024 misquoted** as authority for the 60-minute OR window — the paper studies a 5-minute opening range | **Fixed** — `n_or=12` re-justified VERBATIM on the 1.0 H052a first-hour definition; Zarattini re-scoped (ORB class supported, 60-min window from H052a not Zarattini) |
| QUANT-1-3 | quant | Lo-2002 Sharpe CI variant unspecified | **Fixed** — the autocorrelation-adjusted (time-series) variant specified |
| QUANT-1-4 | quant | 25% precision gate provenance | **Fixed** — tagged as H900/H001-inherited CONSORT-style convention, not H101-tuned |

## Round 2 — verdict: accept (0 remediate, 1 minor)

All round-1 findings verified resolved; every cited DOI (incl. the corrected
Ledoit-Wolf and the new KPSS DOI) resolves to its claimed source. One minor
(QUANT-2-1): the specific Tsai-2019 figures (>8% annual, p<0.03) could not be
verified against the paywalled full text. **Remediated before freeze** — the §1
mechanism reworded to the Crossref-verifiable claim ("reports positive,
statistically-significant timely-ORB profitability on index-futures markets"),
specific magnitudes not reproduced, per the no-paraphrasing-without-verification
directive.

## Residual risk (recorded)

- **First real ledger evidence.** H101 is the first evidence-eligible expert; its
  admission scan RC-H101-1 (registered family `rc-h101-1` in
  [config/multipletest_family.yaml](../../config/multipletest_family.yaml)) runs on
  the backfilled ledger. The screening/FWER level is the DEFERRED project-wide
  `screening_error_rate_target`, so the scan is descriptive and no cell certified
  until it is set.
- **ORB expert early-close limitation.** [orb_first_hour.py](../../src/skie_universe2/experts/orb_first_hour.py)
  flats at the 15:55 RTH-close label; holiday half-days (~9/yr, 13:00 ET close) are
  not specially handled (documented) — a follow-up needing the exchange half-day
  calendar.
- **ADR-0002(d) non-redundancy** is trivial at the empty arsenal (H001 archived
  null), so H101's admission **defines** the arsenal-covariance bound memo; the
  known H103 structural dependence (same ORB on the complementary session subset)
  is deferred to RC-XCORR-1.
- **December-roll windows** remain excluded, not corrected (no Databento repull —
  operator decision, no new-data budget).

Design frozen 2026-07-16, SHA-256 `a7c5c9178f66…`; expert code 9 tests, lint clean.
