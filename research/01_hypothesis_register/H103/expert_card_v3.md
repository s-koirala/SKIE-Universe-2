---
# Expert Card - machine-readable frontmatter (schema per ADR-0009 §3)
hid: H103
card_version: 3
predecessor_card: research/01_hypothesis_register/H103/expert_card_v2.md
design_md_sha256: "84d01a6b4ad0971fd518ffa3d325d7ec93d7e44ce28d5e97066ca974baa345aa"
screen_addendum_sha256: "532047a3753e8d84acb5c5114bdda8796f1663fb245feb6cc2c9a57c90d12a20"
repro_log_run_ids: []          # correction of record; NO new computation ran
data_span: { start: 2015-01-05, end: 2025-12-05 }
instruments: [ES, NQ]
execution_tier: 0              # per ADR-0006
trial_register_increment: 0    # no scan runs; no family increment
disposition: pool-hold-reconsider   # UNCHANGED from v2
---

# Expert Card - H103 v3: standing-statement correction — the ES stress record is UNRESOLVED

**Card class: correction of record (append-only, ADR-0009 Decision 4).** This
version runs no new computation, changes no disposition, and increments no
register family. It exists to fix the *standing interpretation* of the H103
ES stress-cell record: the two measurements on file were taken under two
different stress-cell constructions, and neither settles the Lundström
high-vol-concentration prior
([Holmberg, Lönnbark & Lundström 2013, Finance Research Letters 10(1):27-33](https://doi.org/10.1016/j.frl.2012.09.001)).
Predecessor: [expert_card_v2.md](expert_card_v2.md) (2026-07-18 screen card),
which remains the numeric screen record; every v2 section not restated below
is carried unchanged by cross-link.

## 1. Provenance header

Unchanged from [v2 §1](expert_card_v2.md) (same frozen design SHA
`84d01a6b4ad0…`, same screen-addendum SHA `532047a3753e…`, same k1.0 ledger
partitions). This card cites only the two committed primary artifacts:

- RC-H103-1 scan artifact: `reports/H103/rc_h103_1_scan.json`
- RC-H103-2 screen artifact: `reports/H103/rc_h103_2_screen.json`

## 2. Failure-mode decomposition — the construction-dependence record, stated in full

The two ES stress-cell measurements on file, each with its construction and
sample size (both stand; append-only; neither is deleted or amended):

| Record | Stress-cell construction | Mean gross (per-session log-return) | n (sessions) | Bootstrap stat | RW-adj p |
|---|---|---|---|---|---|
| RC-H103-1 (2026-07-16) | **Leaked**: full-sample realized-vol percentile cutoff (quantile 0.8097 computed over the whole sample; look-ahead in the cell boundary) | −5.0922e-04 | 437 | −0.8404277792603854 | 0.7942 |
| RC-H103-2 (2026-07-17 frozen protocol; run 2026-07-18) | **Leakage-clean**: per-rolling-origin training-window empirical CDF cutoff (certified construction; p̂ ≈ 0.18) | +1.0295e-04 | 313 | +0.1544010591430268 | 0.6164 |

**Correct standing statement: UNRESOLVED.** A sign flip under a leakage
repair, measured on 28% less data (313 vs 437 sessions; the clean per-origin
cell is smaller by construction), is **not corroboration** of the Lundström
prior and is **not powered to resolve it**: at the design-registered effect
size the clean cell clears the registered n ≥ 174 per-instrument power floor
(n = 313) and returns a null there, but at the far smaller observed effect
neither record is powered — neither statistic is distinguishable from zero
(|stat| ≤ 0.85 on both constructions) — so direction and magnitude below the
design effect size remain open. The RC-1 §8 precision-gate failure (mean
indistinguishable from zero at the 25% half-width bar) has no clean-
construction counterpart on record. What the pair of measurements DOES
establish — and what must not be flattened into a single "unresolved" line —
is the **construction-dependence exhibit itself**: the ES stress-cell mean's
sign differs between the two constructions on record, which differ in BOTH
boundary estimation (leaked full-sample cutoff vs per-origin training-window
CDF) and classified session coverage (RC-2 classifies only per-origin
eval-window sessions — ES stress+non_stress = 1549 of 2276; ~700 early
sessions never classified — with per-window stress fractions ranging
0.00–0.65), so the flip is **not attributable to boundary leakage alone**;
a matched-sample decomposition has not been run. Any statement conditioned
on `realized_vol_percentile` must therefore name its construction (see the
covariate-registry note added 2026-07-18).

Consequences for prior statements of record:

- RC-H103-1's "Lundström prior contradicted" was rendered on the **leaked**
  cell; it is construction-dependent, not a settled adjudication. The dated
  RC-1 disposition memo is append-only and stands as written; THIS card is
  its successor correction (ADR-0009 append-only versioning).
- v2 §2's exhibit correctly flagged the reversal but framed the clean
  construction as the operative measurement; v3 sharpens the standing status
  to UNRESOLVED — the clean measurement is a screen-tier queue statistic, not
  evidence the prior holds.
- The 1.0-era "stress-subset consistency" argument (retro register, H103
  digest) was built on the leaked-construction reading and is **withdrawn**
  in the register addendum (2026-07-18); the underlying 1.0 evidence remains
  frozen as recorded.

**Mandatory disclosure (ADR-0013/0014 evidential framing).** Where v2 reports
the ES stress cell as a screen pass: that pass is at the enacted
`screening_error_rate_target` = 0.7400550140326007 (Romano-Wolf within scan;
config value governs), a deliberately loose budget under which a passing cell
may carry up to ~74% probability of being backtest-overfit. Margins are thin:
DSR 0.3038 vs bound 0.2599 (margin +0.0439), PBO 0.7296 vs bound 0.7401
(margin 0.0105), RW-adj p 0.6164 vs level (margin 0.1237). The S-d bounds are
PROVISIONAL OPERATIONAL PROXIES of a posterior-null budget (discovery-alpha
memo §A.6.2). A screen pass is an unadjudicated queue entry; the VERDICT has
not run; **nothing is certified**, and the arsenal remains EMPTY.

## 3. Conditional-edge panel

Unchanged from [v2 §3](expert_card_v2.md) (no new numbers; the v2 panel is
the current screen record).

## 4. Ensemble block

Unchanged from [v2 §4](expert_card_v2.md) (arsenal EMPTY; null-valued by
construction).

## 5. Stability profile

Unchanged from [v2 §5](expert_card_v2.md).

## 6. Disposition

```yaml
disposition: pool-hold-reconsider   # UNCHANGED by this correction
binding_criterion: "v2 screen record stands; v3 corrects the STANDING INTERPRETATION of the ES stress cell to UNRESOLVED (construction-dependent); no re-adjudication ran"
```

## 7. Burned-data entry

No new span consumed (no computation ran). The v2 §7 entry stands.

## 8. Priors update

1. **Lundström high-vol-concentration prior: UNRESOLVED as of 2026-07-18.**
   Not contradicted (that reading was leaked-construction-dependent), not
   corroborated (a +1.03e-04 mean at |stat| = 0.15 on 313 sessions is not
   evidence of concentration), and not powered to resolve it below the design
   effect size (powered null at the registered n ≥ 174 floor; unpowered for
   the observed effect magnitude). Re-adjudication requires a powered,
   pre-registered test on the certified per-origin construction — a
   verdict-tier or successor-scan object, not a reinterpretation of these
   records. Attribution provenance note: the cited 2013 FRL paper establishes
   large-move-day / intraday-momentum concentration for ORB; the **ex-ante
   volatility-state** form of the prior tested here derives from Lundström,
   "Day trading returns across volatility states" (working-paper tier, cited
   in the frozen design §3) — the frozen surfaces' compound label is carried
   verbatim, with this clarifier.
2. The construction-dependence exhibit is itself the finding: the thin ES
   stress-cell conditional mean changes sign between the leaked and the
   certified constructions (boundary estimation AND session coverage differ;
   not attributable to leakage alone without a matched-sample decomposition).
   It is recorded in the covariate registry (`realized_vol_percentile`
   `construction_dependence_note`, 2026-07-18) as a standing caution for
   every future consumer of this covariate.
