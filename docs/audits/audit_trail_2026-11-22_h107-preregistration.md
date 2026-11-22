# Audit trail — H107 pre-registration (2026-11-22)

**Object:** H107 session-VWAP × EMA(N) crossover grid — design
`research/01_hypothesis_register/H107/design.md`, expert
`src/skie_universe2/experts/vwap_ema_cross.py`, grid screen
`src/skie_universe2/screening/grid_screen.py`, harness
`scripts/run_screen_h107.py`, backfill driver changes, emitter H107 entry,
`config/cost_schedules/ninjatrader_v1.yaml`, `rc-h107-1` register family.

**Protocol:** one independent adversarial round (fresh-context reviewer
handed the code, not the author's conclusions), then author remediation and
re-verification. Fewer rounds than the H105/H106 3-round precedent; recorded
as such.

## Round 1 — verdict: no critical findings; 2 major, 7 minor

Verified by execution (reviewer): 20 H107 tests; `cme_session_of` ≡
`cme_session_date_expr` on 200k random 2015-2026 UTC stamps (0 mismatches,
DST incl.); 263 held decision labels/session; signal speed 3.6 s / 750k
bars; synthetic early-close gap accrual; register counts on main; full
emitter simulation (card, pool, 14 register trials, burned spans) in a temp
root, repo untouched.

| # | Sev. | Finding | Disposition |
|---|---|---|---|
| 1 | major | Emitter pooled under the max-DSR passing span's hash → de-facto span selection at the screen, card/pool hash mismatch | **Fixed**: one pool-record set per passing grid point, own ledger id, `ledger_slice` suffix `:grid=emaN`; re-simulated (16 records = 4 passing ledgers × 4 fractions) |
| 2 | major | 14 append-only writes not resumable after a crash | **Fixed**: `_already_backfilled` skips complete (expert, asset) sets, aborts on partial; test added |
| 3 | minor | Holiday early-close gap accrual worse than stated (inside-window last bar; whole-weekend cases) | **Documented** design §4.7; calendar flatten = new-HID follow-up |
| 4 | minor | VWAP from valid bars only (warm-up after exclusions, pit_provisional holes) | **Documented** design §4.8 |
| 5 | minor | 264 vs measured 263 held labels | **Fixed** (`SESSION_BARS = 263`, design §4.5) |
| 6 | minor | DSR count (87) and dispersion surface not identical; `n_eff_corr_adjusted_reported` missing | **Documented** (conservative direction) + **added** the reported field |
| 7 | minor | Emitter wrote cell-partition wording into the append-only register/card for a grid | **Fixed**: per-HID `cluster_notes` / `family_note` |
| 8 | minor | Grid labels look label-disjoint to the precondition checker | **Documented** design §12 (realized-bar report governs) |
| 9 | minor | Turnover recovery depends on screen-time reference price | **Documented** design §8 (ReproLog-detectable) |
| — | note | Pre-origin 2015-2016 sessions consumed by S-c/S-d but not in burned mirror (inherited) | **Disclosed** design §6 |

Categories with no defect: look-ahead/PIT, Romano-Wolf panel usage, PBO
construction (weak gate at 7 correlated columns — observation), fail-closed
dispersion families, cost arithmetic and micro→parent mapping, emitter field
compatibility, runtime feasibility (~42M ledger rows, slow but feasible),
ADR-0014 dispositions.

## Acceptance

Author remediation applied and re-verified (H107 tests 21/21; full suite
re-run before freeze; emitter re-simulated). Design frozen — SHA-256
recorded in `hypothesis_backlog.md` (H107 row) and the freeze ReproLog.
