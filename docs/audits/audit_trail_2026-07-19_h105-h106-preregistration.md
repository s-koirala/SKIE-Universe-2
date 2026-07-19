# Audit trail — H105 + H106 pre-registration bundles (Step-5 forward batch)

*Date: 2026-07-19. Deliverables: the H105 (overnight/Globex session-drift)
and H106 (VR range-state reversal) pre-registration bundles — designs,
experts + tests, screen harnesses, registrations, disposition emitter — plus
the packaged screen spine the loop forced into existence. Loop:
audit-remediate (Workflow engine, 5-branch specialist ensemble + adversarial
refute gate), 3 rounds (cap), final verdict **ACCEPT (all four branches)**.
The designs froze immediately after round 3.*

Branches routed per round: code-reviewer, quant-auditor,
reproducibility-verifier, literature-check.

## Round 1 (two parallel bundle audits: H105 wf_ee743c46; H106 wf_a15267e8)

14 confirmed majors (none survived the refute gate as false), 2 findings
REFUTED at the gate, ~30 minors. Highlights:

| ID | Sev | Finding (abbrev.) | Disposition |
|---|---|---|---|
| H105 QUANT-1-1 / H106 QUANT-1-1 | major | Vol cells used FULL-SAMPLE tercile cutoffs while claiming lag-0 ex-ante selectability — the construction class the H103 `expert_card_v3` record convicted; pass-eligible cells gated a decision | REMEDIATED — certified leakage-clean per-origin train-window-CDF terciles (`screen_spine.per_origin_percentile`, no-future-dependence test); designs restated incl. the labeled-span property |
| H106 CODE-1-1 / CODE-1-2 | major | Screen spine copy-pasted across harnesses; private-name reach-through over chained file-path script imports | REMEDIATED — spine EXTRACTED to packaged [screening/screen_spine.py](../../src/skie_universe2/screening/screen_spine.py) (ScreenSpec/InstrumentData; public names); harnesses reduced to spec + covariate providers |
| H105 QUANT-1-2 | major | Design §5 described PBO as "CSCV over the 15 rolling windows"; the executed statistic is CSCV S=16 on the full session panel | REMEDIATED — design reworded to the executed construction |
| H105 QUANT-1-3 | major | No implementing path for register-trials / burned-spans / card / pool | REMEDIATED — [emit_screen_expert_card_v1.py](../../scripts/emit_screen_expert_card_v1.py) (card, pool records with the candidate's OWN `expert_hash`, `rc-*-1` trials, 30 burned windows/HID) |
| H105 QUANT-1-4 | major | DSR fed N=30 trial count but dispersion from 8 local cells (mismatched surfaces) | REMEDIATED — `register_trial_sharpes` pools the register's recorded non-unconditional trial Sharpes with the scan's sigma cells |
| H105 QUANT-1-5 / H106 QUANT-1-3 | major | §8 registered diagnostics (KPSS, primary CI + 25% precision, Lo-2002 SE, LW contrast) unimplemented | REMEDIATED — spine §8 exhibits block incl. the H106-registered LW `vr_range` vs `vr_trend` contrast (RC-H103-1 paired construction) |
| H105 QUANT-1-6 | major | `prior_rth_ret` = shift(1) took a weeks-stale value across exclusion gaps | REMEDIATED — 4-calendar-day gap nulling (derived bound) + design §3(ii) |
| H106 LITERATURE-1-1 | major | LM90 characterization inverted (paper's emphasis is lead-lag dominance for portfolios) | REMEDIATED — restated: single-instrument own-autocovariance channel; portfolio finding does not transfer as support |
| H105 REPRO-1-1/LIT-1-1/1-2 | major | Design transcriptions vs the P3-A record (3.67→3.66; NQ p05=185) | REMEDIATED |
| H106 QUANT-1-2 / REPRO-1-1 | major | Claimed missing tooling paths | **REFUTED at the gate** (refuters located the v1 emitter; concrete file evidence) |

Also remediated from the minors: LM88 "VR<1 prevalence" misattribution
dropped; zero-mean-AR(1) and population-vs-sample VR hedges added; LPS 2019
attribution scoped to firm-level stocks; PW 2004 + Hoenig-Heisey DOIs;
S-e structural vacuity declared; state-sequence coincidence note; ledger-
partition checksum binding (`build_checksums`, fail-closed); test hygiene.

## Round 2 (combined, wf_f2efea54)

6 findings to remediate (1 critical), none refuted:

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| REPRODUCIBILITY-2-1 / QUANT-2-1 | **critical** | The spine's `hac_variance_inflation`, documented as a verbatim lift, DROPPED the frozen `m ≤ n−1` bandwidth cap — the refuter reproduced a ValueError crash on a small MA(2)-style cell | REMEDIATED — frozen body restored line-for-line (pilot floor, s0 early-return, cap); 2 regression tests incl. equality vs the frozen helper at 1e-12 |
| QUANT-2-2 | major | H105 §3 cell-family bullet still said "full-sample upper tercile" (incomplete round-1 propagation into the about-to-freeze text) | REMEDIATED |
| QUANT-2-3 / REPRODUCIBILITY-2-2 | major | H106's matched-dispersion surface silently under-pooled if run before the H105 emitter (rc-h105-1 empty) | REMEDIATED — `register_trial_sharpes` FAILS CLOSED on absent or zero-trial named families; run-order PRECONDITION registered in H106 §5 |
| REPRODUCIBILITY-2-3 / QUANT-2-5 | major | Both §11 RNG statements ("one sequential stream") were false vs the three per-stage same-seed Generators | REMEDIATED — §11 restated to the actual per-stage dedicated-Generator construction |
| minors | — | emitter `n_gate` bare `next()`; LW guard ddof; kpss "verbatim" wording; register-comment emitter naming (marker preserved byte-exact); NW94 DOI; dead sentinel | REMEDIATED |

## Round 3 (final, wf_92f94813) — ACCEPT

`remediate: []`, all branches accept. Six minors logged; three fixed
immediately post-verdict because they would bite within the session:
- CODE-3-1/QUANT-3-1 — the empty-family test read the LIVE register and
  would fail the moment the H105 emitter populates `rc-h105-1` → rebuilt on
  a synthetic tmp-path config fixture.
- CODE-3-3 — fail-closed dispersion probe hoisted to `run_screen` entry
  (fail-fast; no result change).
- LITERATURE-3-1 — Patton-Politis-White 2009 correction DOI added to both
  frontmatters + §8 (the in-repo `bootstrap.py` already implements the
  PPW-2009-corrected constants, so this aligns citation with
  implementation).
- CODE-3-2 — comment corrected (the H106 harness's reuse of the H105
  script's `_valid_5m_features` is deliberate module-internal reuse of the
  substrate loader; promotion to a packaged public name is a residual).

## Residual risks (logged at cap)

1. `register-trials` idempotent append keys on a byte-exact marker line in
   `config/multipletest_family.yaml`; a future YAML-formatter pass would
   silently convert the append into a skip (REPRODUCIBILITY-3-1). Hardening
   (YAML-node parse) deferred.
2. The substrate loader `_valid_5m_features` remains a script-level private
   name consumed by two scripts (CODE-3-2); packaging it is deferred.
3. `test_reads_recorded_families_excluding_unconditional` pins len==16
   against the live rc-h101-2/rc-h103-2 families (stable: frozen scan
   families are append-only and complete).
4. Canary-block duplication across the two harnesses (CR-2-5, cosmetic).
5. The kpss output keys are renamed vs the frozen RC-1 helper
   (`level_c`/`trend_ct`; documented — artifact schemas differ from RC-1's).

**Verdict: ACCEPT (3 rounds, cap).** Designs frozen immediately after; the
freeze SHAs and ReproLogs are recorded in
[hypothesis_backlog.md](../../hypothesis_backlog.md) and the freeze commit.
