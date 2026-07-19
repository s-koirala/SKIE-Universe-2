# Verdict-readiness memo — first-admission VERDICT (operator gate)

*Date: 2026-07-19. One-page operator decision brief; nothing here is
self-executing. The set-level VERDICT (ADR-0014 D2), its authorization, the
ADR-0015 lift, and every vendor spend remain named, dated operator actions.*

## 1. Pool state (after the Step-5 forward batch)

| Quantity | Value |
|---|---|
| Pool records | **16** (4 HIDs × 4 Kelly fractions) |
| Distinct `expert_hash` | **3** — `orb_first_hour_k1.0@1.0.0` (H101+H103), `overnight_session_drift_k1.0@1.0.0` (H105), `vr_range_reversal_k1.0@1.0.0` (H106) |
| Arsenal | EMPTY (nothing certified; no Kelly fraction selected) |
| New screens | RC-H105-1 **PASS** (6 cells: ES+NQ high_vol/low_vol/prior_rth_up; unconditional fails S-d on both; prior_rth_down fails S-d on both) — [card](../../research/01_hypothesis_register/H105/expert_card_v1.md). RC-H106-1 **PASS** (4 ES cells: unconditional, vr_range_at_open, high_vol, low_vol; ALL NQ cells fail S-d) — [card](../../research/01_hypothesis_register/H106/expert_card_v1.md) |
| Trial register | +20 records (`rc-h105-1`, `rc-h106-1`); families pre-registered before their scans; burned-data ledger +60 window-spans (30/HID, scripted mirror) |
| Pre-data power gates | S-c well-powered at the enacted level for every binding cell (0.83–0.95); the §8 25% precision report-eligibility is unreachable at literature effect sizes (n_req ≈ 10⁵ vs n ≈ 10³) — declared, constrains card claims only ([H105](../../reports/H105/power_analysis.json), [H106](../../reports/H106/power_analysis.json)) |

## 2. ADR-0015 verdict precondition: **MET (label-based; reporting-only)**

[check_verdict_precondition.py](../../scripts/audits/check_verdict_precondition.py)
→ exit 0: ≥ 2 pairwise-disjoint coverage vectors across 3 distinct hashes.
The disjoint pair is **(ORB, H106)** at the LABEL level.

**The operator should read the M1 companion before acting on this**
([m1_realized_overlap.json](../../reports/M1_overlap/m1_realized_overlap.json);
setup plan §2.3: the label rule GOVERNS, M1 informs):

| Pair | Label verdict | Realized-BAR Jaccard | Realized-SESSION Jaccard | Frozen §12(c) prediction (bar / session) |
|---|---|---|---|---|
| ORB ↔ H105 | **collides** (the name `NQ:high_vol` appears in both vectors — different constructions, zero shared bars) | **0.0 exactly** | 0.585 | EXACTLY 0 ✓ / 0.75–0.95 (below band) |
| ORB ↔ H106 | **disjoint** | 0.089 | 0.301 | 0.05–0.25 ✓ / 0.85–1.0 (below band) |
| H105 ↔ H106 | — | 0.212 | 0.413 | no frozen band (required report) |

The label statistic and the realized statistic **invert**: the pair the
checker certifies as disjoint (ORB↔H106) shares ~9% of realized bars, while
the pair it blocks-on-collision (ORB↔H105) is **bar-disjoint to the exact
zero the frozen design predicted** — the strongest disjointness in the
pool, invisible to the label rule because two different constructions share
the string `high_vol`. This is the setup plan §2.2 label-gameability
critique realized in both directions at once. Session-level values fall
below their predicted bands for a declared reason: the predictions were
written for whole-expert activity; realized coverage is
passing-cell-restricted, and H106 passed on ES only.

**Standing note:** the setup plan §2.3 M1 already proposes an ADR-0015
amendment making realized-bar disjointness a first-class
`verdict_precondition` input (operator acceptance required). Today's
exhibit is the empirical case for it. Until accepted, the label rule
governs and this memo only reports.

## 3. Cold-start pool-priority ordering (ADR-0014 D6; queue, not certification)

At |arsenal| = 0 the coverage-novelty primary is inert; ordering falls to
the persistence-margin tie-breaker (headline S-d DSR / 1−PBO):

1. **H106** (DSR 1.000 @ ES:low_vol; PBO 0.047) — but see §5 risk (i)
2. **H105** (DSR 0.788 @ NQ:low_vol; PBO 0.217)
3. **H101** (DSR 0.573; PBO 0.216)
4. **H103** (DSR 0.571; PBO 0.442)

## 4. The exact operator gates now open

| Gate | Recordable object |
|---|---|
| ADR-0015 HOLD lift + first-admission VERDICT authorization | **`lift_action`** — named, dated operator authorization (ADR-0015 D3). Precondition reports MET; the M1 exhibit above is the material context |
| DR-1/DR-2 December-roll repair | **spend authorization** (quote-ready; cost sheet §4). **Now BINDING for confirmation-grade adjudication of H105** — the verdict tier is confirmation-tier, and overnight/Globex evidence is conditional-grade until the repair (rule of record 2026-07-19; the blind spot is structurally concentrated in H105's own competence window: ~68–69% of every excluded bar is overnight-ETH). A verdict rendered pre-repair carries the declared blind spot into the admission record |
| ADR-0016 stage B | **authorized / declined / undecided** (currently undecided; unchanged by this session; parallel track, lifts nothing here) |

If the lift is authorized: the VERDICT runs the ADR-0007 ladder on marginal
geometric growth (incl. the non-waivable matched-turnover rotor), authors
the arsenal-covariance anchor, and triggers the registered first-admission
re-instantiations (Kelly concavity/ruin bracketing on the admitted ledger;
discovery-alpha §A.8). All of that is post-lift work; none of it ran.

## 5. Residual risks the operator should weigh

- **(i) H106's gross is not monetizable at Tier-0 cost.** The 1-bar-hold
  reversal's per-session gross (ES ≈ 22 bps) rides ~10² bar-level switches;
  at the constant 1-tick-per-side floor the net is deeply negative (declared
  at freeze, design §7). Its screen pass is a pre-cost persistent-window
  fact, not a tradable edge; its priority-1 queue slot (persistence margin)
  should be read against that. The empirical slippage calibration
  (`P1-H052A-COST-CALIBRATION-EMPIRICAL`) and/or ADR-0016 Tier-2 work is
  where that question resolves.
- **(ii) The screen level is deliberately loose** (0.7401 retain-fwer):
  pool entry certifies nothing; the verdict ladder is where selection is
  paid for.
- **(iii) December/Globex blind spot** (91 ES / 101 NQ sessions/instrument,
  same calendar band every year) binds hardest on H105 (§4 above);
  DR-1/DR-2 repairs it for ~130–200 MB of vendor data plus an append-only
  re-materialization and re-screen (OD-F path).
- **(iv) Label-namespace collisions** in `competence_window_cells` are now
  a demonstrated failure mode of the precondition's letter (both
  directions); the proposed ADR-0015 amendment (§2) is the structural fix.
- **(v) NQ asymmetry:** H106 has no passing NQ cell; H105's NQ
  `unconditional` fails S-d. Cross-instrument robustness at the verdict
  tier is not pre-established for either candidate.
