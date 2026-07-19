# DR-1/DR-2 December-roll repair — operator runbook

*Dated 2026-07-19. Spend authorized at the GOVERNANCE level 2026-07-19
(cost-sheet authorization addendum); EXECUTION is operator-only under the
standing rule (cost sheet §5(d)): no agent places the order, runs the
metered download, or touches payment. This runbook ends at quotable
parameters + the post-pull pipeline the operator triggers; every price is
`TBD — operator to quote`. Upstream registration:
`vendor_databento_dec_roll_repair_1min` in
[config/data_sources.yaml](../../config/data_sources.yaml) (ADR-0011 D3 —
registration precedes ingest; already committed).*

## 1. What this purchase repairs

`DEC_ROLL_LATE_COMMIT` (critical): per-year raw sharding hid the next
year's H contract, so every ES/NQ Z→H roll 2016–2025 committed ~3 weeks
late; the mitigation is EXCLUSION (91 ES / 101 NQ sessions, the same
mid-December band yearly; ~68–69% of excluded bars are overnight-ETH).
Post-repair, the registered **confirmation-grade H105 re-adjudication**
becomes runnable (§5). Official roll convention (pinned):
CME equity roll date = the **Monday prior to the third Friday** of the
expiration month
([cmegroup.com/trading/equity-index/rolldates.html](https://www.cmegroup.com/trading/equity-index/rolldates.html);
[Understanding Futures Expiration & Contract Roll](https://www.cmegroup.com/education/courses/introduction-to-futures/understanding-futures-expiration-contract-roll)).

## 2. Exact request parameters (cost sheet §2.1.2 / §4 rows DR-1, DR-2)

- **Dataset:** `GLBX.MDP3`  ·  **Schema:** `ohlcv-1m`  ·  **Encoding:**
  `dbn.zst` preferred (≈0.16× CSV bytes, MGC precedent), CSV acceptable.
- **Symbology:** `parent` (`stype_in="parent"`, symbols `ES.FUT`,
  `NQ.FUT`) — returns ALL active expiries incl. the Z–H calendar spreads in
  each window (requesting raw per-year symbols is what CAUSED the defect;
  the MGC/SIL continuous-pull precedent avoids it). Per boundary Y/Y+1 the
  window must resolve `ESZ{Y}`, `ESH{Y+1}`, `NQZ{Y}`, `NQH{Y+1}` and the
  `ESZ{Y}-ESH{Y+1}` / `NQZ{Y}-NQH{Y+1}` spreads — verify presence in the
  delivered file before accepting the pull.
- **DR-1 windows (10, each `start` inclusive → `end` exclusive):**
  `2015-12-01→2016-01-16`, `2016-12-01→2017-01-16`,
  `2017-12-01→2018-01-16`, `2018-12-01→2019-01-16`,
  `2019-12-01→2020-01-16`, `2020-12-01→2021-01-16`,
  `2021-12-01→2022-01-16`, `2022-12-01→2023-01-16`,
  `2023-12-01→2024-01-16`, `2024-12-01→2025-01-16`.
- **DR-2 window (1):** `2025-12-01→2026-01-16` (covers the ES tail from
  2025-12-04; ES raw ends 2025-12-03 vs NQ 2025-12-19).
- **Order form:** DR-1 + DR-2 as ONE order (§5(a)); one request per window
  (11 total) or the vendor's multi-range batch equivalent — NOT per-year
  full-span requests.

## 3. Quote first (no download)

For each window, with the official Python client:

```python
from databento import Historical
client = Historical()  # operator's own API key from the account env
for start, end in WINDOWS:  # the 11 (start, end) pairs of §2
    size = client.metadata.get_billable_size(
        dataset="GLBX.MDP3", schema="ohlcv-1m",
        symbols=["ES.FUT", "NQ.FUT"], stype_in="parent",
        start=start, end=end,
    )
    cost = client.metadata.get_cost(
        dataset="GLBX.MDP3", schema="ohlcv-1m",
        symbols=["ES.FUT", "NQ.FUT"], stype_in="parent",
        start=start, end=end,
    )
    print(start, end, size, cost)
```

Record the 11 quotes in this note's addendum before ordering. Sanity
anchor (repo-derived, not a price): the whole DR-1+DR-2 request is
≈1.9–2.9 M `ohlcv-1m` rows ≈ 145–220 MB CSV / ≈ 23–35 MB dbn.zst (cost
sheet §2.1.3 × 1.1 for the 11th window) — a quote wildly above that scale
indicates a symbology mistake (e.g. accidental full-span request).

## 4. Pull, checksum, store (machine level — never the repo)

1. `client.timeseries.get_range(...)` per window with the §2 parameters →
   files under `~/datasets/vendor_databento_dec_roll_repair/raw_1min/`
   named per the registered `file_pattern`.
2. **Retrieval-time sidecars (ADR-0011 D4):** for each delivered file,
   write `{file}.sha256` (`sha256sum` output) plus a `retrieval.json`
   (request params verbatim, UTC retrieval timestamp, Databento job id).
3. Verify per §2 that each window's file contains BOTH outrights and the
   Z–H spread for its boundary; refuse/re-request otherwise.
4. Nothing under the repo's `data/` is touched in this step.

## 5. Post-pull pipeline (operator reports "pull complete" → agent-run)

Executed only AFTER the operator confirms §4, in order:

1. **Ingest:** `uv run python scripts/ingest.py --dataset vendor_legacy_1min --start 2015-01-01 --end 2026-01-16 --symbols ES NQ`
   with the repair source merged per the ingest module's registry rules
   (the ingest refuses unregistered sources; the repair entry is already
   registered). Then the roll-adjusted re-materialization:
   `uv run python scripts/ingest.py --dataset vendor_legacy_1min_roll_adjusted --start 2015-01-01 --end 2026-01-16 --symbols ES NQ`.
   **OD-F append-only:** new partitions; old ones deprecated, never
   edited. The re-ingest EMITS a NEW dated provenance JSON
   (`data/processed/_provenance/vendor_legacy_1min_roll_adjusted_{YYYYMMDD}.json`,
   atomic write) whose regenerated `coverage_gaps` reflect the repaired
   substrate; the `_20260711` record is retained UNEDITED as the
   pre-repair record.
2. **Manifest:** `uv run python scripts/build_data_manifest.py` then
   `--check` green.
3. **Derivatives re-run:** shadow-ledger re-backfills for affected experts
   into NEW `expert_id@version`-bumped partitions (ADR-0003 D3), PIT
   canaries re-run; screens whose statistics touched excluded windows are
   re-screened per their designs' registered re-run rules.
4. **H105 re-adjudication at CONFIRMATION grade — a FUTURE-SESSION
   adjudication event:** it runs only under the frozen VERDICT-1 protocol
   (or a registered addendum), with a fresh trial-register increment and
   an appended Expert Card version (ADR-0014 D3). It is NEVER an automatic
   pipeline tail step; the operator schedules it explicitly.

## 6. What remains NOT authorized (unchanged)

ADR-0016 stage B (T2-B `mbo`+`mbp-10` validation pull) — UNDECIDED; MX-1
micro siblings; T2-D*; CAL-1. None of §2–§5 touches any of them.
