# Audit trail — DR-1/DR-2 agent-side prep + Phase-4 proposed draft (E+F bundle)

*2026-07-19. Deliverables: (E) the DR-1/DR-2 December-roll repair agent-side
preparation — the `vendor_databento_dec_roll_repair_1min` registry entry
([config/data_sources.yaml](../../config/data_sources.yaml)), the operator
runbook ([dr1_dr2_operator_runbook_2026-07-19.md](../research_notes/dr1_dr2_operator_runbook_2026-07-19.md)),
and the cost-sheet/plan authorization addenda; (F) the Phase-4 confirmation
protocol draft ([PHASE4_confirmation_protocol_PROPOSED.md](../../research/02_verdict/PHASE4_confirmation_protocol_PROPOSED.md),
status `proposed`). Method: audit-remediate loop (Workflow engine, 3-round
cap). Verdict: **ACCEPT at round 3 (cap reached).***

## Scope constraints verified every round

No dollar figures (all prices `TBD — operator to quote`); no agent-executable
spend path (execution operator-only per config `spend_authorization`, runbook
preamble, cost sheet §5(d)); 11 pull windows (10 DR-1 + 1 DR-2), 46-day
Dec 01→Jan 15 spans; correct Databento parameter names (GLBX.MDP3, ohlcv-1m,
mbp-10/mbo, `metadata.get_billable_size`/`get_cost`, `stype_in='parent'`);
append-only discipline on the DEC_ROLL_LATE_COMMIT defect record; F
authorizes/runs/registers nothing.

## Round 1

Verdict proceed-with-remediation. **3 majors confirmed by refuter:**

- **QUANT-1-1 + REPRODUCIBILITY-1-1** (confirmed) — runbook §5.1 presented the
  post-pull ingest as ready-to-run, but NO code path consumes
  `vendor_databento_dec_roll_repair_1min` (the ingest is hard-wired to the
  single legacy registry key + legacy CSV file pattern), so §5 verbatim would
  re-ingest the defective substrate and re-emit unchanged `coverage_gaps`.
  FIX: added an explicit **§5.0 "BUILD PREREQUISITE, NOT YET BUILT"** block —
  the merge stage (resolve BOTH registry keys, parse the repair
  `{REQUEST_ID}_{SYMBOL_SET}` files incl. `dbn.zst`, repair-precedence in the
  11 windows) is a future-session deliverable with its own commit/tests/audit;
  §5.1–5.4 relabeled the intended pipeline SHAPE, not a runnable command.
- **LITERATURE-1-1** (confirmed) — the pinned CME citation said the December
  roll Monday falls "~Dec 08-14", a misderivation (third Friday is Dec 15-21,
  so the roll Monday is Dec 11-17). FIX: corrected to Dec 11-17 with the
  2015-2025 recomputation {14,12,11,17,16,14,13,12,11,16,15}; retracted the
  "~Dec 08-14" claim; restated that the ~Dec 08 crossover-window starts
  PRE-DATE the convention-implied roll Monday (no pull-window change).

## Round 2

Verdict proceed-with-remediation. **2 majors confirmed by refuter:**

- **QUANT-2-1** (confirmed) — the round-1 LITERATURE-1-1 fix had (via an
  earlier commit 375c787) edited the append-only DEC_ROLL_LATE_COMMIT
  `description` field IN PLACE, replacing the original "(CME guidance: volume
  migrates ~8 calendar days before last-trade)." clause while the entry's
  `repair` field still claimed "retained unedited per ADR-0011". FIX: the
  `description` field is RESTORED byte-identical to the 2026-07-10 d1e4eaa5
  original (verified at raw-byte level); ALL 2026-07-19 attribution content
  moved into the additive `roll_convention_citation` field per ADR-0011 D4.
- **LITERATURE-2-1** (confirmed) — the "~8 calendar days before last-trade"
  EARLY-migration figure is unpinned (the CME source fixes the roll DATE, not
  an ~8-day early migration), AND config claimed LITERATURE-1-4 "closed"
  while cost sheet §2.1.1 said "open". FIX: the additive field now labels the
  ~8-day figure an INTERNAL EMPIRICAL ESTIMATE and marks LITERATURE-1-4
  **partially closed** (roll-date convention pinned; early-migration
  magnitude an internal estimate); cost sheet §2.1.1 reconciled to the same
  status. Minor QUANT-2-2 (runbook §1 "91/101 sessions" vs cost sheet §2.1.4
  "110/110 bar-dates") — runbook §1 now states the two are different
  denominators (blind-spot sessions vs calendar bar-dates), not in conflict.

## Round 3 (FINAL, cap reached)

Verdict **ACCEPT** — all three branches accept, 0 findings. Verified: the
`description` field is byte-identical to d1e4eaa5 (an apparent YAML-parse
mismatch was a cp1252/utf-8 em-dash artifact, not a real edit); LITERATURE-1-4
status AGREES between config and cost sheet §2.1.1 ("partially closed"); the
CME roll-date convention and both URLs confirmed; the FRL 2013 DOI
(10.1016/j.frl.2012.09.001, Holmberg-Lönnbark-Lundström) verified;
Databento method names and `parent` symbology confirmed; F is `proposed` and
authorizes/runs/registers nothing.

## Residual risk (declared, non-blocking)

The ~8-day early-migration magnitude remains an unpinned internal estimate
pending a primary OI-migration source, to be recorded at repair
registration; disclosed as partially-closed in both artifacts, and the
Dec 01 pull-window starts conservatively bracket the pinned roll Monday
(Dec 11-17) regardless of its eventual value. The
[backfill_admission_plan](../research_notes/backfill_admission_plan_2026-07-17.md)
"Lundström working paper" reference is an unpinned secondary source, but the
operative empirical claim (large-move-day concentration) is anchored to the
verified 2013 FRL paper — low-stakes, transparently hedged.
