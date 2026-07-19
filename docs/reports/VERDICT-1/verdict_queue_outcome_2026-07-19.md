# VERDICT-1 first-admission queue — outcome report

*2026-07-19. Protocol: [VERDICT-1_protocol.md](../../../research/02_verdict/VERDICT-1_protocol.md)
(frozen SHA-256 `ac611bc4a786717a249c93b58b61ed5b400f686a18e4735b911e3db7137e10ef`).
Enacted level `screening_error_rate_target` = 0.7400550140326007 (read at
runtime; DSR bound 1−level = 0.2599, PBO bound = level). Seed 20260721;
1000 SPA/StepM bootstraps; 2000 rotor draws; PBO CSCV S=16.*

## Verdict: NO ADMISSION. Arsenal remains EMPTY.

Both queued candidates were adjudicated against the empty incumbent set
(|S| = 0, the degenerate first case) and **neither is admitted**. No
incumbent-set change occurred, so the ADR-0014 D3 re-adjudication of the
held ORB hash (queue item 3) was **not triggered**, and the Work-Plan D
first-admission triggers (Kelly concavity/ruin re-instantiation,
discovery-alpha §A.8(1) re-derivation, arsenal-covariance anchor,
pool-priority first data points) **did not fire**. No Kelly fraction is
selected; no Phase-4 entry; ADR-0010 untouched. This is the pre-registered
"no-admission is valid and terminal" outcome (protocol §2.2, §9).

## C1 — H106 (`vr_range_reversal_k*@1.0.0`), |S| = 0

**NOT admitted** ([verdict_h106.json](../../../reports/VERDICT-1/verdict_h106.json);
ReproLog `repro_log_b2f7cd83d201…`). 8 columns (ES/NQ × 4 Kelly arms), 1636
OOS sessions, current surface 16, cumulative register N = 56.

| §2.2 clause | Result |
|---|---|
| 1. Marginal SPA (consistent p) | 0.487 < 0.740 → PASS |
| 2. Ladder IU + rotor | IU max p 0.487 (PASS); rotor min Šidák p **1.000** (FAIL) → **iu_pass FALSE** |
| 3. Qualifying columns | **none** (rotor Šidák = 1.000 in every column) |
| 4. Persistence | not reached (no qualifying column) |

**Binding failure: the matched-turnover rotor rung.** Every marginal-delta
column Sharpe is NEGATIVE (ES ≈ −1.30, NQ ≈ −0.47 per session) — at |S| = 0
the marginal delta is H106's own net stream, which at the Tier-0
constant-1-tick floor is net-negative and loses to a matched-turnover random
rotor in all 8 columns. This is the pre-registered **net-not-monetizable
caveat** (§7) realized on-ledger. Disposition: `pool-hold-reconsider`
(re-affirmed); Expert Card [v2](../../../research/01_hypothesis_register/H106/expert_card_v2.md).

## C2 — H105 (`overnight_session_drift_k*@1.0.0`), |S| = 0 — CONDITIONAL-GRADE

**NOT admitted** ([verdict_h105.json](../../../reports/VERDICT-1/verdict_h105.json);
ReproLog `repro_log_1b56058f868e…`). 1636 OOS sessions, current surface 16,
cumulative register N = **72** (40 screen + 16 H106 verdict + 16 H105).

| §2.2 clause | Result |
|---|---|
| 1. Marginal SPA (consistent p) | 0.010 < 0.740 → PASS |
| 2. Ladder IU + rotor | IU max p 0.010 (PASS); rotor min Šidák p 0.273 (PASS) → **iu_pass TRUE** |
| 3. Qualifying columns | **5**: ES:k0.5, NQ:k0.5, NQ:k0.75, NQ:k1.0, NQ:k1.25 |
| 4. Persistence | PBO 0.006 ≤ 0.740 (PASS); **DSR ≈ 0.000 < 0.2599 (FAIL)** → **persistence FALSE** |

H105 clears every gate EXCEPT the non-waivable DSR persistence bound. The
marginal-delta column Sharpes are POSITIVE but modest (best NQ:k0.5 ≈ 0.044
per session, t ≈ 1.3 over ~800 NQ sessions), and the Deflated-Sharpe
deflation over the cumulative 72-trial register — whose dispersion pool
includes H106's net-negative verdict trials and the screen families — pushes
DSR below the 0.2599 bound in every column. This is the ADR-0013 mandate
made concrete: **aggression on sizing/discovery is bought with strictly more
conservative multiplicity accounting** — a modest overnight-drift edge does
not survive the leverage-binding deflation. Disposition:
`pool-hold-reconsider` (re-affirmed, CONDITIONAL-GRADE §7); Expert Card
[v2](../../../research/01_hypothesis_register/H105/expert_card_v2.md).

**Order-dependence, disclosed:** the cumulative-surface rule (protocol §6)
makes H105's DSR bound harder because H106 was adjudicated first (its 16
trials are in H105's cumulative N and its 8 net-negative marginal Sharpes
widen the dispersion pool). This is the pre-registered behavior — every
trial on the shared substrate adds to the multiplicity burden — and is
conservative, never anti-conservative.

## C3 — held ORB (H101+H103) — NOT TRIGGERED

The ORB re-adjudication (queue item 3) is conditioned on an incumbent-set
change (ADR-0014 D3). No admission occurred, the set is unchanged, so ORB was
not re-adjudicated; it retains its screen disposition (`pool-hold-reconsider`).

## Ledger effects (append-only)

- `first-admission-verdict` register: +32 trials (H106 A1: 16; H105 A1: 16;
  8 rotor trials per candidate declaredly Sharpe-less, protocol §6).
- Pool ledger: +8 copy-forward records (H105, H106 × 4 arms) carrying the
  verdict disposition + §7 substrate grade + Tier-0 cost label.
- Burned-data ledger: +60 `admission-verdict` spans (2 candidates × 15
  windows × 2 instruments).
- No `config/arsenal.yaml` (created only at first admission).

## Next (operator-gated)

The H105 edge exists gross and clears identification (SPA/StepM/rotor/PBO);
it fails only the leverage-binding DSR persistence at this multiplicity. The
**DR-1/DR-2 December-roll repair** (governance-authorized, execution
operator-only) enables the registered **confirmation-grade H105
re-adjudication** on the repaired ledger — a future-session event under this
frozen protocol. No agent action is authorized beyond the quotable pull
parameters + runbook.
