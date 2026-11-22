# NinjaTrader execution costs — ES / NQ / MES / MNQ (2026-11-22)

Principal direction 2026-11-22: NinjaTrader is the trading platform. This note
records the cost research behind the registered schedule
[config/cost_schedules/ninjatrader_v1.yaml](../../config/cost_schedules/ninjatrader_v1.yaml)
(consumed by the H107 screen, design §7). Gathered by two research subagents
on 2026-11-22; every number below carries its source. Items marked
UNVERIFIED have not been cross-checked against a primary source.

## 1. Per-contract fees (US site)

Source: https://ninjatrader.com/pricing/commissions/ — per-symbol data
embedded in the page; the page states the table is "as of August 14, 2026".
Exchange and NFA fees are reported combined. Per side, USD.

| Contract | Plan | Commission | Exch + NFA | Clearing | All-in / side | All-in round turn |
|---|---|---|---|---|---|---|
| ES / NQ | Free | 1.29 | 1.39 | 0.19 | 2.87 | 5.74 |
| ES / NQ | Monthly | 0.99 | 1.39 | 0.19 | 2.57 | 5.14 |
| ES / NQ | Lifetime | 0.59 | 1.39 | 0.19 | 2.17 | 4.34 |
| MES / MNQ | Free | 0.39 | 0.36 | 0.19 | 0.94 | 1.88 |
| MES / MNQ | Monthly | 0.29 | 0.36 | 0.19 | 0.84 | 1.68 |
| MES / MNQ | Lifetime | 0.09 | 0.36 | 0.19 | 0.64 | 1.28 |

- NFA assessment: $0.01/side from 2026-07-01, $0.02 from 2027-07-01
  (https://www.nfa.futures.org/faqs/members/nfa-assessment-fees.html). The
  implied CME exchange fee ($1.38 E-mini / $0.35 micro) is UNVERIFIED against
  CME's fee schedule (cmegroup.com blocked the automated fetch). Note the
  registered `futures_rt_v1` uses $1.38 + $0.02 NFA + $0.85 commission and no
  clearing fee — $2.25/side vs $2.17 (lifetime) here.
- Rithmic order routing adds $0.25/contract only if routed via Rithmic
  (https://ninjatrader.com/pricing/account-fees/); excluded.
- Fixed costs: Monthly plan $99/mo, Lifetime $1,499 once
  (https://ninjatrader.com/pricing/); CME Level-I data $12/mo bundle (free
  when funded), Level-II $48/mo; Free-plan inactivity $35 after 30 days with
  no live trade (account-fees page).
- Margins (context, same commissions page): day margin ES $500, NQ $1,000,
  MES $50, MNQ $100; initial ES $26,758, NQ $40,205, MES $2,657, MNQ $4,021.

## 2. Spread and slippage

| Contract | Tick value | Evidence | Status |
|---|---|---|---|
| ES | $12.50 | quoted spread ≈ 1 tick in RTH (mean 0.251 pt, 2008–11) and ≈1.03–1.06 ticks overnight; top-of-book depth 984 (US hours) / 265 (Europe) / 54 (Asia) contracts — Andersen, Bondarenko, Kyle & Obizhaeva, AEA 2017 preliminary paper, Table 1; spread near the minimum tick at all hours by 2020 — NY Fed Staff Report 917 | literature (citation check pending) |
| NQ | $5.00 | 1–2 ticks, thinner than ES | practitioner, UNVERIFIED |
| MES | $1.25 | "often 1 tick", thinner book | practitioner, UNVERIFIED |
| MNQ | $0.50 | "1 tick", thinner book | practitioner, UNVERIFIED |

No quantitative source was found for widening at the 09:30 open, 16:00 close
or 18:00 ET reopen; CME reports ES depth fell 68% on 2025-04-07 and 90% in
March 2020 (stress).

**Registered scenarios (ticks per side, session-agnostic):** central ES/MES
0.5, NQ/MNQ 1.0; pessimistic ES/MES 1.5, NQ/MNQ 2.0. Per ADR-0016's
swept-assumption rule, a net claim must survive the pessimistic endpoint.

## 3. Implication for a 5-min crossover

Per unit of notional, a micro costs ~3× an E-mini (lifetime: $0.64 on $5/pt
vs $2.17 on $50/pt). At an ES price of 5,000, one lifetime round trip is
≈ 1.7 bp of notional for ES and ≈ 5.1 bp for MES, before slippage. A rule
that reverses several times a session needs a gross edge of several basis
points per session just to break even on micros.

## 4. Open items

- Verify the CME exchange fee against the current CME fee schedule (manual
  download).
- Replace the UNVERIFIED NQ/MES/MNQ spread figures with session-split spread
  and depth computed from Databento GLBX MBP-1 (the project's vendor).
- Re-check the NinjaTrader table quarterly (stated update cadence).
