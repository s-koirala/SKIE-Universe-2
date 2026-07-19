# H106 Expert Card v2 — VERDICT-1 adjudication A1

*Appended 2026-07-19 (ADR-0009/ADR-0014 D3 append-only card version; prior
version expert_card_v1.md stands unedited). Rendered by
`scripts/emit_verdict_disposition.py` from
`reports/VERDICT-1/verdict_h106.json` — never hand-copied.*

## Adjudication record

| Field | Value |
|---|---|
| Protocol | research/02_verdict/VERDICT-1_protocol.md (SHA `ac611bc4a786...`) |
| Candidate (queue) | H106 (stem H106) |
| Adjudication index | A1 |
| Incumbent set at adjudication | EMPTY (degenerate first case, |S| = 0) |
| Level (runtime-read) | 0.7400550140326007 (config/multipletest_family.yaml governs) |
| Trial surface (this adjudication) | 16 (§6 branch enumeration) |
| Cumulative register N (DSR) | 56 |
| Seed / bootstrap / rotors | 20260721 / 1000 / 2000 |
| ReproLog | logs/reproducibility/repro_log_b2f7cd83d20144b68e01928e93855e0d.json |

## §2.2 conjunction

| Clause | Outcome |
|---|---|
| 1. Marginal SPA (consistent p) | 0.487000 — PASS |
| 2. Ladder IU (max SPA p, non-degenerate rungs) | 0.487000; rotor min Šidák p 1.000000 — FAIL |
| 3. Qualifying columns (StepM ∧ rotor) | none |
| 4. Persistence (best-qualifying column DSR/PBO) | DSR bound 0.259945; PBO 0.000000 (bound 0.740055) — FAIL |
| **Admitted** | **False** |

## Per-column report — 8 (instrument × Kelly arm) columns; NO fraction selected (ADR-0013 D9)

| Column | Δ Sharpe (marginal) | StepM adj-p | Identified | Rotor Šidák p | DSR |
|---|---|---|---|---|---|
| ES:k0.5 | -1.295241 | 1.000000 | no | 1.000000 | 0.000000 |
| ES:k0.75 | -1.296063 | 1.000000 | no | 1.000000 | 0.000000 |
| ES:k1.0 | -1.296871 | 1.000000 | no | 1.000000 | 0.000000 |
| ES:k1.25 | -1.297665 | 1.000000 | no | 1.000000 | 0.000000 |
| NQ:k0.5 | -0.473677 | 1.000000 | no | 1.000000 | 0.000000 |
| NQ:k0.75 | -0.475199 | 1.000000 | no | 1.000000 | 0.000000 |
| NQ:k1.0 | -0.476715 | 1.000000 | no | 1.000000 | 0.000000 |
| NQ:k1.25 | -0.478225 | 1.000000 | no | 1.000000 | 0.000000 |

Best qualifying column (REPORTED (instrument, arm) pair, not a selection):
none.

## Disposition

**pool-hold-reconsider (re-affirmed)** — held in the provisional pool (ADR-0014 D3); reconsideration-eligible on the next incumbent-set change.

Degenerate rungs this adjudication: ['b1', 'b3'];
B2 identity anchor: EW(U) is the §1 set functional (recorded, not tested).
Trial identifiers: `VERDICT:H106:A1:{instrument}:k{arm}:{object}`
in the `first-admission-verdict` family.

## §7 substrate grade & labeling (binding)

- Tier-0, constant-1-tick-slippage (ADR-0006 D2; not live-capital eligibility).
- net-not-monetizable caveat (§7): the screened edge is pre-cost; at the Tier-0 constant-1-tick-per-side floor the 1-bar-hold net is deeply negative. Any admission is an allocator-unit marginal-contribution judgment (ADR-0001), not a tradable-standalone claim.
