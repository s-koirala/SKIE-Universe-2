# H105 Expert Card v2 — VERDICT-1 adjudication A1

*Appended 2026-07-19 (ADR-0009/ADR-0014 D3 append-only card version; prior
version expert_card_v1.md stands unedited). Rendered by
`scripts/emit_verdict_disposition.py` from
`reports/VERDICT-1/verdict_h105.json` — never hand-copied.*

## Adjudication record

| Field | Value |
|---|---|
| Protocol | research/02_verdict/VERDICT-1_protocol.md (SHA `ac611bc4a786...`) |
| Candidate (queue) | H105 (stem H105) |
| Adjudication index | A1 |
| Incumbent set at adjudication | EMPTY (degenerate first case, |S| = 0) |
| Level (runtime-read) | 0.7400550140326007 (config/multipletest_family.yaml governs) |
| Trial surface (this adjudication) | 16 (§6 branch enumeration) |
| Cumulative register N (DSR) | 72 |
| Seed / bootstrap / rotors | 20260721 / 1000 / 2000 |
| ReproLog | logs/reproducibility/repro_log_1b56058f868e46c19f7bed86e6cbd062.json |

## §2.2 conjunction

| Clause | Outcome |
|---|---|
| 1. Marginal SPA (consistent p) | 0.010000 — PASS |
| 2. Ladder IU (max SPA p, non-degenerate rungs) | 0.010000; rotor min Šidák p 0.272459 — PASS |
| 3. Qualifying columns (StepM ∧ rotor) | ['ES:k0.5', 'NQ:k0.5', 'NQ:k0.75', 'NQ:k1.0', 'NQ:k1.25'] |
| 4. Persistence (best-qualifying column DSR/PBO) | DSR bound 0.259945; PBO 0.006294 (bound 0.740055) — FAIL |
| **Admitted** | **False** |

## Per-column report — 8 (instrument × Kelly arm) columns; NO fraction selected (ADR-0013 D9)

| Column | Δ Sharpe (marginal) | StepM adj-p | Identified | Rotor Šidák p | DSR |
|---|---|---|---|---|---|
| ES:k0.5 | 0.026443 | 0.097902 | yes | 0.692134 | 0.000000 |
| ES:k0.75 | 0.025519 | 0.105894 | yes | 0.762363 | 0.000000 |
| ES:k1.0 | 0.024594 | 0.112887 | yes | 0.791383 | 0.000000 |
| ES:k1.25 | 0.023668 | 0.121878 | yes | 0.778893 | 0.000000 |
| NQ:k0.5 | 0.044421 | 0.023976 | yes | 0.272459 | 0.000000 |
| NQ:k0.75 | 0.043340 | 0.027972 | yes | 0.290422 | 0.000000 |
| NQ:k1.0 | 0.042256 | 0.027972 | yes | 0.275480 | 0.000000 |
| NQ:k1.25 | 0.041170 | 0.028971 | yes | 0.385070 | 0.000000 |

Best qualifying column (REPORTED (instrument, arm) pair, not a selection):
NQ:k0.5.

## Disposition

**pool-hold-reconsider (re-affirmed)** — held in the provisional pool (ADR-0014 D3); reconsideration-eligible on the next incumbent-set change.

Degenerate rungs this adjudication: ['b1', 'b3'];
B2 identity anchor: EW(U) is the §1 set functional (recorded, not tested).
Trial identifiers: `VERDICT:H105:A1:{instrument}:k{arm}:{object}`
in the `first-admission-verdict` family.

## §7 substrate grade & labeling (binding)

- Tier-0, constant-1-tick-slippage (ADR-0006 D2; not live-capital eligibility).
- CONDITIONAL-GRADE (§7): December/Globex blind spot inside the competence window (91 ES / 101 NQ excluded sessions; 69.0%/67.8% overnight-ETH). A confirmation-grade re-adjudication on the DR-1/DR-2-repaired ledger is a REGISTERED future-session event (fresh trial-register increment + appended card), never an automatic step.
