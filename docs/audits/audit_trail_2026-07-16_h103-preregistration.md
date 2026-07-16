# Audit trail — H103 pre-registration (stress-state ORB, ES+NQ)

**Date:** 2026-07-16
**Deliverable:** [research/01_hypothesis_register/H103/design.md](../../research/01_hypothesis_register/H103/design.md)
— pre-registration design for H103 (anti-gate / stress-state-only first-hour ORB,
2.0 re-specification of 1.0 H054), ES+NQ.
**Frozen SHA-256:** `84d01a6b4ad0971fd518ffa3d325d7ec93d7e44ce28d5e97066ca974baa345aa`
(frozen_sha256=`84d01a6b4ad0`).
**Pre-registration ReproLog:** run `2e0e5464f86f4a32a72bcebf214433d1`.
**Loop:** audit-remediate-loop, 3 rounds (cap 3), parallel-specialist-ensemble.
**Terminal verdict:** ACCEPT (round-2 format ACCEPT; round-3 quant ACCEPT; no surviving
critical/major).
**Operator input:** instrument scope ES+NQ (operator decision 2026-07-16); the draft was
authored ES-only and promoted to ES+NQ before this loop.

## Round 1 — 3 parallel auditors (quant/method, literature, format)

### quant-auditor (1 critical, 3 major, 5 minor)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F-1-1 | critical | §5/§9 still ES-only while §1/§2/§6/§8/§10 adjudicate ES+NQ — estimator produces no NQ scan yet §10 declares an NQ disposition | **FIXED** — §5A backfills expert × {ES, NQ}; §5B scans each instrument's stress cell; §9 consumes the {ES,NQ} backfill; NQ ledger source = the shared RC-H101-1 canonical backfill |
| F-1-2 | major | `realized_vol_percentile` reference-window unspecified → possible purge leakage | **FIXED** — §3 registers the per-session input (rvol_5m_24h, 288-bar causal, ≤ purge) and the percentile reference = training-window empirical CDF (PIT-clean by construction) |
| F-1-3 | major | Forking paths: H103 primary stress cell ≈ RC-H101-1's already-null `high_vol` cell on the SAME ledger; not registered as a prior correlated trial | **FIXED** — §5B registers the RC-H101-1 scan as a prior correlated trial (band vs tercile stated); §8 DSR N_trials folds in the full RC-H101-1 same-ledger surface (round-2 F-2-3) |
| F-1-4 | major | Joint ES+NQ FWER asserted but not operationalized; diverged from RC-H101-1's per-instrument RW | **FIXED** (superseded by round-2 F-2-1) — resolved to per-instrument RW + Šidák cross-instrument union |
| F-1-5 | minor | §7 cost basis ES-only | **FIXED** — NQ ≈4.15e-5 notional drag added; NQ account-dollar basis resolved by scan |
| F-1-6 | minor | §11 `(ES)` checksum tag | **FIXED** — `(ES, NQ)` |
| F-1-7 | minor | n≥174 power floor ES-anchored, transported to NQ | **FIXED** — per-instrument (n_ES, n_NQ) re-derived from each instrument's own effect/variance; ES effect not transported |
| F-1-8 | minor | §8 promised PBO but RC-H101-1 established it is structurally deferred on this surface | **FIXED** — §8 defers PBO with the same rigor as the screening-level deferral |
| F-1-9 | minor | Anti-gate vs §4 position-gate / ADR-0001 D5 tension | **FIXED** — §3/§4 clarify a rule-based conditional expert (ADR-0002); the HMM sets only the scalar train-window cutoff, never per-session membership |

### literature-check (6 minor; all 11+ DOIs verified against Crossref)

Lundström companion paper cited for the high-vs-low decomposition (F-1-1); "S&P 500
(and crude oil) futures" (F-1-2); BTZ gloss sharpened to variance-risk-premium/stress
states, not realized-vol (F-1-3); Hoenig-Heisey (10.1198/000313001300339897) and Grinold
1989 (10.3905/jpm.1989.409211, Crossref-verified) registered in frontmatter (F-1-4/5);
Tsai corrected to open-access (F-1-6). All fixed.

### format-auditor (3 major, 3 minor)

The incomplete ES→ES+NQ propagation in §5A/§5B/§9 (F-1-1/2/3, same as quant F-1-1) and
§11 (F-1-4) — all **FIXED**. Splitter 24/6 anchor labeled (F-1-5). §1 bare-DOI list
accepted as convention (F-1-6). Frontmatter/template/identity-hygiene clean.

## Round 2 — quant + format re-audit

### format-auditor — verdict **ACCEPT**

ES→ES+NQ conversion complete and consistent; frontmatter valid; cross-refs resolve;
sibling RC-H101-1 numbers match bit-for-bit. Two cosmetic minors: stale DRAFT-banner text
(resolved at freeze) and §5B→§5(B) notation (normalized at freeze).

### quant-auditor — verdict proceed-with-remediation (1 major, 4 minor)

| ID | Sev | Issue | Disposition |
|---|---|---|---|
| F-2-1 | major | The "pooled ES×NQ RW" fix asserted a joint cross-instrument resampling scheme neither specified nor implemented (RC-H101-1 resamples one per-instrument series) | **FIXED** — §5B revised to per-instrument RW (validated estimator) + a Šidák cross-instrument union bound at the deferred screening level; §2 reconciled; conservative, buildable, no joint-panel resampler required |
| F-2-2 | minor | Cutoff "set to occupancy probability" operationally ambiguous | **FIXED** — stress cell = sessions with train-window rvol percentile ≥ (1 − p̂), p̂ = HMM stress occupancy |
| F-2-3 | minor | Only the single RC-H101-1 high_vol cell folded into N_trials; RC-H101-1 ran 10 same-ledger trials | **FIXED** — full RC-H101-1 same-ledger surface folded in (conservative) |
| F-2-4 | minor | RC-XCORR-1 non-redundancy did not state per-instrument vs pooled | **FIXED** — §10 RC-XCORR-1 is per-instrument (ES, NQ), pair admitted per instrument |
| F-2-5 | minor | PBO DOI (10.21314/JCF.2016.322) absent from frontmatter | **FIXED** — added (with the Grinold DOI) |

## Round 3 — focused quant verification of the F-2-1 multiplicity fix — verdict **ACCEPT**

Verified: (1) the Šidák union 1−(1−α)^(1/2) across 2 families is the correct FWER control
for the "reject-if-either" decision, conservative under positive ES–NQ dependence
(direction confirmed; Bonferroni fallback ≈ α without any dependence assumption);
(2) buildable with the existing per-instrument `romano_wolf_stepm` (no joint-panel
resampler); (3) §2/§5B/§8/§10 mutually consistent; (4) no new inconsistency or bare
constant. Minor F-3-1 (note the assumption-free Bonferroni fallback so validity does not
hinge on positive-orthant dependence) **FIXED** in §5B.

## Residual risk (accepted, pre-registered)

- The stress-cell result is likely another descriptive null (H103 re-tests essentially the
  vol-conditioning RC-H101-1 already found null on the shared ledger); the multiplicity
  accounting now registers that lineage honestly.
- Purge/percentile-CDF leakage and the joint-FWER scheme are verified at the DESIGN level;
  final verification is against the actual covariate + per-instrument RW implementation at
  scan time (RC-H103-1), including the registered Šidák-union screening rule.
- PBO and the screening/FWER level remain DEFERRED; no admission is certified while
  outstanding. Kelly-fraction selection remains BLOCKED. The n_ES/n_NQ power floors and the
  RC-XCORR-1 bounds are re-derived per instrument at freeze-time/scan-time.
