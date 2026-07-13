---
name: ADR-0012 — Standing incumbent allocator (champion-challenger governance)
description: A human-legible standing champion allocator configuration is the live default and live-capital anchor; the champion is selected over the joint (allocator-config x Kelly-fraction) space on geometric (compounded, Kelly log-wealth) growth as the primary dethroning statistic; a challenger dethrones it only through the ADR-0007 confirmation ladder by a pre-registered geometric-growth-improvement margin after a minimum incumbency dwell, with every challenge and every Kelly-fraction trial logged in the ADR-0008 trial register
type: governance
status: accepted
date: 2026-07-12
supersedes: ""
superseded_by: ""
---

# ADR-0012 — Standing incumbent allocator (champion-challenger governance)

## Context

ADR-0001 makes the allocator the unit of inference; ADR-0007 certifies allocator
configurations against the confirmation ladder; ADR-0010 escalates live size for a
configuration that clears it. Nothing yet designates *which* certified
configuration is the standing default that carries live capital between
confirmation cycles. Rolling evaluation (ADR-0004) yields a metric time series,
not a single durable winner, so ops, external communication, and the ADR-0010
escalation schedule have no one named configuration to anchor on. The two failure
modes without a designation are symmetric: paralysis (no live default) and
thrashing (reallocating to the momentary best and churning on noise).

The allocator already performs champion-challenger *internally* — Hedge /
fixed-share upweights currently-best experts per regime and is scored against the
best-in-hindsight switching oracle (ADR-0001 Decision 3; ADR-0004 Decision 4).
This ADR adds no estimator and no selection mechanism. It adds a human-legible
*standing designation* one level up, over allocator configurations, for
operational default, communication, and live-capital anchoring. The risk it must
manage is meta-overfitting: a standing incumbent invites repeated challenges,
which form a new multiple-testing family above the expert-level family already
controlled by ADR-0007/0008.

Under the 2.0 aggressive geometric-growth mandate, the champion is ranked and
dethroned on **geometric (compounded) growth** — Kelly-optimal log-wealth growth
rate ([Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x);
[MacLean, Thorp & Ziemba 2011](https://doi.org/10.1142/7598)) — not on
switching-oracle regret, which is demoted to a reported secondary. The Kelly
fraction is a registered swept hyperparameter over the grid {0.5, 0.75, 1.0,
1.25}, and the champion is selected over the *joint*
(allocator-config x Kelly-fraction) space. The joint space enlarges the
meta-overfitting family this ADR must control: every (config x fraction) pair is
a distinct challenge carried in the ADR-0008 family-wise trial register, so the
Kelly-fraction dimension is a multiplicity source, not a free parameter. The
geometric-growth objective penalizes over-betting **in expectation** — under
standard (thin-tailed, single-period) assumptions expected log-wealth is concave
in the fraction with an interior maximum ([MacLean, Thorp & Ziemba 2011](https://doi.org/10.1142/7598)).
Whether that concavity, the interior maximum, and the swept grid's bracketing of
it hold on the shadow-ledger multi-period, fat-tailed return distribution — and
the ruin handling at a leveraged fraction (a realized `1 + f·R ≤ 0` yields −∞
geometric growth, correctly rejecting that fraction) — are **to be derived** via
the ADR-0013 BLOCKING follow-up `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`; **no
swept Kelly fraction is selected on geometric growth, and no dethroning on a >1×
fraction is certifiable, before that memo is frozen and its ReproLog emitted**.
This does not weaken the overfitting core: at leverage an overfit champion does not
merely underperform, it *ruins* (negative geometric growth on a fake edge), so
the DSR/PBO confirmation ladder and matched-turnover random rotor (Decision 3)
bind *more* tightly here, not less.

## Decision

1. **Standing incumbent at the allocator level, never the strategy level.** The
   champion is the current best *allocator configuration* — arsenal membership
   plus the Hedge / fixed-share weighting rule and its CV-selected hyperparameters
   (ADR-0001 Decisions 1, 3–4) — held as the standing default irrespective of
   short-term performance until a challenger dethrones it under Decision 3.
   Consistency with ADR-0001 is binding and explicit: a single expert is never the
   champion; the champion is the meta-allocator over the arsenal, and this
   designation does **not** resurrect the abolished 1.0 strategy-level deployment
   gate (ADR-0001 Decision 2). The internal champion-challenger among experts is
   unchanged; this is an ops/comms/capital overlay, not a new mechanism.

2. **"Best" is geometric (compounded) growth over the joint config x Kelly-fraction
   space, not return and no longer regret.** Ranking is on **geometric growth** —
   the Kelly-optimal compounded log-wealth growth rate ([Kelly 1956](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x);
   [MacLean, Thorp & Ziemba 2011](https://doi.org/10.1142/7598)) — as the primary
   dethroning statistic, computed over the *joint* (allocator-config x
   Kelly-fraction) space with the Kelly fraction swept over the registered grid
   {0.5, 0.75, 1.0, 1.25}. These fraction values are the
   registered sweep grid (a hyperparameter search per the zero-magic-number rule,
   not hand-picked constants); the winning fraction is data-selected on geometric
   growth, which penalizes over-betting in expectation — but only after the
   ADR-0013 BLOCKING follow-up `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`
   establishes the interior maximum, grid bracketing, and ruin handling on the
   shadow-ledger fat-tailed distribution (until then no swept fraction is
   selected on geometric growth). Switching-oracle regret and
   the lower-tail terminal-wealth quantile (ADR-0004 Decision 4) are retained as
   **reported secondaries**: regret remains the primary *internal* expert-selection
   object (ADR-0001 Decision 3) and is reported here for diagnosis; the lower-tail
   quantile is a **monitored, non-binding guardrail** (demoted from the ADR-0004 /
   ADR-0005 binding role under the 2.0 mandate), still reported, never decisive.
   All three are reported per the standing report-object contract
   [docs/methodology/allocator_metric_family_report_objects.md](../methodology/allocator_metric_family_report_objects.md);
   raw or nominal return is never a ranking object.

3. **Pre-registered replacement rule (the anti-data-dredging crux).** A challenger
   dethrones the incumbent only by beating it on the Decision-2 geometric-growth
   metric under the full ADR-0007 confirmation ladder — Hansen SPA existence across
   all five benchmarks including the non-waivable matched-turnover random rotor
   (ADR-0007 Decision 4), Romano-Wolf StepM identification, Deflated Sharpe, and the
   PBO exhibit — by a pre-declared **geometric-growth-improvement margin** over the
   incumbent, with the challenge registered as a new entry in the ADR-0008
   family-wise trial register *before* it runs. Because the champion is selected
   over the joint (config x Kelly-fraction) space, **every (config x fraction) pair
   is a separate trial in the family**: the SPA/StepM correction covers the
   Kelly-fraction-expanded family, and the swept fractions pay their multiplicity
   exactly as the config challenges do — the fraction dimension buys no free look.
   The margin, the winning fraction's registration, and the comparison horizon are
   frozen prior to the challenge (ADR-0008 Decision 4 pre-registration). These
   overfitting-detection gates (DSR + PBO + random rotor) are non-waivable and bind
   *more* tightly at leverage: an overfit champion levered at or above full Kelly
   ruins the compounded capital it is levering into, so the gates protect the
   geometric growth they certify. Dethroning on unadjusted or nominal
   outperformance is prohibited; challenge multiplicity is carried in the same
   register as the expert-level scans, so each challenge — and each fraction —
   pays its correction.

4. **Incumbency / survivorship-bias control.** The incumbent receives no tenure
   exemption: at each challenge it is re-qualified on the *same* fresh
   purge-and-embargo out-of-sample windows the challenger faces (rolling-origin,
   ADR-0004 Decision 2), head-to-head on one identical fold set. The comparison is
   never challenger-on-fresh-data against an incumbent record inherited from older
   or longer windows — that would let accumulated tenure masquerade as edge.
   Windows consumed are burned for both arms in the ADR-0008 burned-data ledger.

5. **Champion dwell (meta-overfitting guard).** A challenge may succeed no faster
   than the meta-evidence supports: a minimum incumbency dwell / evidence-
   accumulation requirement must elapse before a dethroning is certifiable. This
   mirrors the ADR-0004 Decision 6 dwell-vs-break-even logic one level up — as a
   regime is worth switching to only if it persists past break-even dwell
   (detection latency + cost payback), a champion is worth replacing only if the
   challenger's geometric-growth advantage persists past the meta-evidence
   half-life; replacement faster than that is thrashing on noise, the dominant
   meta-overfitting failure mode — and the mode most ruinous under leverage, where a
   noise-driven handover to an over-bet challenger compounds losses. The dwell floor
   is a **to-be-calibrated parameter**, set empirically (never a magic number) from
   the rate at which the geometric-growth-differential CI stabilizes under the
   ADR-0004 stationary-bootstrap stack; see the calibration follow-up in
   Consequences.

6. **Live-capital anchoring and controlled handover.** The champion is the
   configuration that carries live size on the ADR-0010 escalation schedule;
   challengers accrue live-vs-shadow tracking in shadow (ADR-0003 Decision 7
   dual-arm recording) until they win. A dethroning triggers a **pre-registered
   handover schedule**, not an abrupt full reallocation: the incumbent steps down
   and the challenger steps up through the ADR-0010 tracking-fidelity criterion, a
   scheduled crossfade frozen before the handover (ADR-0010 Decisions 2–3). The new
   champion earns its live size by its own live-vs-shadow evidence — it never
   inherits the incumbent's earned size, which would grant size by simulation and
   violate ADR-0010 Decision 1.

## Consequences

- Positive: a live default always exists — the program neither paralyzes for want
  of a single ranked winner nor thrashes chasing the momentary best.
- Positive: replacement is disciplined by the same confirmation ladder and trial
  register that govern admission, so dethroning cannot be bought with noise.
- Positive: live capital gets one named, stable, human-legible anchor for ops,
  comms, and the ADR-0010 ramp.
- Negative: adds a standing governance object (the incumbent designation with its
  margin, dwell, and handover schedule) that must be maintained and re-registered
  on change.
- Negative: meta-overfitting remains possible if the dwell is set too short or the
  ladder is weakened; both are non-waivable, and the matched-turnover random-rotor
  benchmark (ADR-0007 Decision 4) still binds every challenger.
- Obligation: every challenge — successful or not — and every swept Kelly-fraction
  trial increments the ADR-0008 family-wise trial register; challenge and
  fraction multiplicity is corrected in the same family as the expert-level scans.
- Obligation: the geometric-growth-improvement margin (Decision 3) and the
  champion-dwell floor (Decision 5) are empirically calibrated by explicit
  error-rate-cost analysis (cost of a false dethroning under leverage vs cost of
  an over-tenured incumbent) analogous to ADR-0002 (c) / ADR-0010 Decision 3;
  registered as BLOCKING follow-up `P1-2.0-CHAMPION-MARGIN-DWELL-CALIBRATE`. This
  ADR is **accepted (2026-07-12)** — the champion-challenger framework is in
  force — but the dethroning rule is **non-operational until that memo is frozen
  with its ReproLog emitted**: until calibrated, no dethroning is certifiable.
- Obligation: no swept Kelly fraction is selected on geometric growth, and no
  dethroning on a >1× fraction is certifiable, before the ADR-0013 BLOCKING
  follow-up `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE` (interior maximum, grid
  bracketing, and ruin handling on the shadow-ledger fat-tailed distribution) is
  frozen and its ReproLog emitted.

## Alternatives considered

- **Best single hypothesis / expert as the champion.** Rejected: violates ADR-0001
  Decisions 1–2 — the unit of inference is the allocator, and a single-strategy
  champion resurrects the abolished 1.0 deployment gate and its empty survivor set.
- **Continuous reallocation to the momentary best (no standing champion).**
  Rejected: thrashes on noise, provides no stable live-capital anchor, and is
  incompatible with the ADR-0010 escalation discipline (size earned by measurement
  over frozen windows, not re-chosen every bar).
- **Replace on nominal outperformance.** Rejected: data-dredging across a growing
  family of challenges; bypasses the ADR-0007 confirmation ladder and the ADR-0008
  trial register, manufacturing false dethronings at precisely the leverage where
  they are ruinous (ADR-0010).
- **Keep switching-oracle regret as the primary dethroning statistic.** Rejected
  under the 2.0 aggressive geometric-growth mandate: regret measures distance to a
  hindsight benchmark, not the compounded capital growth the program now optimizes.
  Geometric (Kelly log-wealth) growth is the primary ranking object; regret is
  retained as a reported secondary (Decision 2).
- **Fix the Kelly fraction at full (1.0) rather than sweep it.** Rejected: the
  optimal fraction is data-dependent (estimation error and fat tails favor
  fractional Kelly; MacLean-Thorp-Ziemba 2011), so it is a registered swept
  hyperparameter {0.5, 0.75, 1.0, 1.25} with the winner selected on geometric growth
  over the joint space and its multiplicity carried in the trial register — not a
  hand-fixed constant.
- **Incumbent scored on its legacy record, challenger on fresh windows.** Rejected:
  survivorship bias — tenure on more/older data flatters the incumbent; Decision 4
  forces one shared fresh fold set for both arms.

## References

- [Freund & Schapire 1997, J. Comput. Syst. Sci. 55:119-139](https://doi.org/10.1006/jcss.1997.1504) — Hedge / multiplicative weights (the allocator's internal champion-challenger).
- [Herbster & Warmuth 1998, Mach. Learn. 32:151-178](https://doi.org/10.1023/A:1007424614876) — fixed-share; switching-oracle regret, the Decision-2 reported-secondary object.
- [Kelly 1956, Bell Syst. Tech. J. 35:917-926](https://doi.org/10.1002/j.1538-7305.1956.tb03809.x) — log-optimal (geometric) growth criterion; the Decision-2 primary ranking object.
- [MacLean, Thorp & Ziemba 2011, *The Kelly Capital Growth Investment Criterion: Theory and Practice*, World Scientific](https://doi.org/10.1142/7598) — fractional-Kelly theory and practice; motivates the swept fraction grid {0.5, 0.75, 1.0, 1.25}; over-betting is penalized in expectation, with the interior maximum / ruin behaviour to be derived (Decisions 2–3; ADR-0013 blocking follow-up `P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`).
- [Hansen 2005, J. Bus. Econ. Stat. 23:365-380](https://doi.org/10.1198/073500105000000063) — SPA existence test (ladder step, Decision 3).
- [Romano & Wolf 2005, Econometrica 73:1237-1282](https://doi.org/10.1111/j.1468-0262.2005.00615.x) — StepM identification under FWER control.
- [Bailey & López de Prado 2014, J. Portfolio Manage. 40(5):94-107](https://doi.org/10.3905/jpm.2014.40.5.094) — Deflated Sharpe.
- [Bailey, Borwein, López de Prado & Zhu 2017, J. Comput. Finance 20(4):39-69](https://doi.org/10.21314/JCF.2016.322) — PBO.
- [Politis & Romano 1994, J. Am. Stat. Assoc. 89:1303-1313](https://doi.org/10.1080/01621459.1994.10476870) — stationary bootstrap for the geometric-growth-differential CI (Decisions 3, 5).
- [Nosek, Ebersole, DeHaven & Mellor 2018, PNAS 115:2600-2606](https://doi.org/10.1073/pnas.1708274114) — pre-registration of the replacement rule.
- [Perold 1988, J. Portfolio Manage. 14(3):4-9](https://doi.org/10.3905/jpm.1988.409150) — implementation shortfall; motivates the earned-not-inherited handover (Decision 6).
- [ADR-0001](ADR-0001-allocator-unit-of-inference.md), [ADR-0004](ADR-0004-rolling-evaluation-regime.md), [ADR-0007](ADR-0007-two-tier-discovery-pipeline.md), [ADR-0008](ADR-0008-integrity-non-negotiables.md), [ADR-0010](ADR-0010-live-capital-escalation.md) — governing decisions this ADR sits atop.
- **Dependency:** this ADR sits atop [ADR-0013](ADR-0013-aggressive-geometric-growth-mandate.md), which establishes geometric (Kelly log-wealth) growth as the program's primary objective and the Kelly fraction as the registered swept hyperparameter; the champion-selection statistic here inherits that objective.
