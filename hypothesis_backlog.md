# Hypothesis backlog

Append-only register of research hypotheses for this project. Per
SKIE-Universe convention (verified via `gh api` 2026-05-15). New entries added
via [/hypothesis-new](https://github.com/s-koirala/dotfiles/tree/main/claude/commands/hypothesis-new.md)
(R3-1 — pending). Append-only: archived hypotheses retain their row with
`status: archived`.

## Status legend

| Status | Meaning |
|---|---|
| `designed` | Pre-registration frozen via /preregister (R3-2a); design.md SHA recorded |
| `validated` | validate-data PASS on input dataset |
| `powered` | power-analysis run; n meets registered effect-of-interest |
| `running` | walk-forward / fit in progress |
| `kpi-reported` | KPI report card emitted to reports/{HID}/ |
| `promoted` | passed multipletest-gate; deployed to production |
| `archived` | null result kept (no deletion per non-loss policy); see failure_log.md |
| `retro-card-emitted` | Expert Card (ADR-0009) emitted from 1.0 evidence; ADR-0002 admission scan not yet run — added 2026-07-10 for the Reanalysis block (`P1-2.0-RETRO-CARD-1.0-REGISTER`) |

## Backlog

| HID | Tier | Title | Status | Mechanism citation | Notes |
|---|---|---|---|---|---|
| H001 | 1 | (reserved — no hypothesis registered) | (reserved) | (reserved — no hypothesis registered) | seed row from bootstrap template; content reserved for the first /hypothesis-new registration (placeholder markers removed 2026-07-10, Round-2 finding FORMAT-2-1; row preserved per append-only policy) |
| H100 | 5 | Retro of 1.0 H050 — HMM regime-gated LightGBM intraday directional signal (ES/NQ 1-min) | retro-card-emitted | [Hamilton 1989](https://doi.org/10.2307/1912559) | Disposition `re-specify-cost-bound`; card: [docs/reports/expert_card_H050_retro_2026-07-10.md](docs/reports/expert_card_H050_retro_2026-07-10.md); scans RC-H100-1..3 |
| H101 | 5 | Retro of 1.0 H052a — first-hour ORB, ES/NQ session cadence (HMM gate rejected; unconditional form is the candidate) | retro-card-emitted | [Holmberg, Lönnbark & Lundström 2013](https://doi.org/10.1016/j.frl.2012.09.001) | Disposition `arsenal-admit-conditional`; card: [docs/reports/expert_card_H052a_retro_2026-07-10.md](docs/reports/expert_card_H052a_retro_2026-07-10.md); scan RC-H101-1 |
| H102 | 5 | Retro of 1.0 H053 — 09:45→10:30 ET multi-timeframe regression with opening-bar mediator (ES/NQ) | retro-card-emitted | [Lou, Polk & Skouras 2019](https://doi.org/10.1016/j.jfineco.2019.03.011) | Disposition `re-specify-cost-bound`; card: [docs/reports/expert_card_H053_retro_2026-07-10.md](docs/reports/expert_card_H053_retro_2026-07-10.md); scans RC-H102-1..2 |
| H103 | 5 | Retro of 1.0 H054 — anti-gate (stress-state-only) first-hour ORB, ES session cadence | retro-card-emitted | [Bollerslev, Tauchen & Zhou 2009](https://doi.org/10.1093/rfs/hhp008) | Disposition `arsenal-admit-conditional`; card: [docs/reports/expert_card_H054_retro_2026-07-10.md](docs/reports/expert_card_H054_retro_2026-07-10.md); scan RC-H103-1; n_anti=7 power floor |
| H104 | 5 | Retro of 1.0 H055 — wick-rejection mean-reversion scalp, 4-symbol swept basket (ES/NQ/MGC/SIL; MGC+SIL post-hoc vs frozen design §2 universe {ES,NQ,MES,MNQ}) | retro-card-emitted | [Moskowitz, Ooi & Pedersen 2012](https://doi.org/10.1016/j.jfineco.2011.11.003) | Disposition `arsenal-admit-conditional` (post-hoc basis); card: [docs/reports/expert_card_H055_retro_2026-07-10.md](docs/reports/expert_card_H055_retro_2026-07-10.md); scans RC-H104-1..3; integrity + registration debt blocks admission |
| H900 | 4 | Dwell-time feasibility gate — regime sojourn-time distribution vs cost break-even dwell (ADR-0004 Decision 6 founding go/no-go) | kpi-reported | [Hamilton 1989](https://doi.org/10.2307/1912559); [Page 1954](https://doi.org/10.1093/biomet/41.1-2.100); [Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870) | First registered analysis of the program; go/no-go for all allocator work; design: research/01_hypothesis_register/H900/design.md (frozen 2026-07-10, SHA-256 `548f009ae505816a1b2aeb8693681224e080449b458013e87d6f3df3c8f4c43c`, ReproLog run 905a280415cf). **Executed 2026-07-11: verdict GO — archive(positive) pending audit** (§10 H1 met on BOTH instruments at μ=1.2e-4: ES pooled D_med 12 bars CI [10,14] vs D_be 4.45; NQ 9 bars CI [8,10] vs 2.54; precision gates pass; inclusive sensitivity also GO; round-1 audit remediated incl. PW-selector + exchange-fee corrections, verdict unchanged); report: [reports/H900/H900_dwell_feasibility_report_2026-07-11.md](reports/H900/H900_dwell_feasibility_report_2026-07-11.md); production ReproLog run efd8dcb1bf67 (supersedes round-1 run 3264085ca65e); winning family 4-state diag Gaussian HMM (30/30 windows) registered as ADR-0002 conditioning-set candidate; follow-up P1-2.0-H900-BOCPD-SENSITIVITY |

## Tiers

- **Tier 1:** Mechanism well-cited in peer-reviewed lit; high prior probability.
- **Tier 2:** Mechanism plausible from theory; weaker empirical support.
- **Tier 3:** Exploratory; structural hypothesis testing the substrate.
- **Tier 4:** Methodology/gate hypotheses (e.g., multiple-testing family scope).
- **Tier 5:** Replication / reanalysis of prior work.

## Reserved ID blocks

To avoid HID collision across parallel exploration:

| Block | Range | Reserved for |
|---|---|---|
| Main | H001–H099 | core hypotheses |
| Reanalysis | H100–H199 | replication of prior work |
| Methodology | H900–H999 | gate / framework hypotheses |
