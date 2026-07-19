# Audit trail — VERDICT-1 first-admission protocol freeze (B bundle)

*2026-07-19. Deliverable: the pre-registered first-admission VERDICT
protocol ([VERDICT-1_protocol.md](../../research/02_verdict/VERDICT-1_protocol.md),
frozen SHA-256 `ac611bc4a786717a249c93b58b61ed5b400f686a18e4735b911e3db7137e10ef`,
freeze ReproLog `repro_log_f975dcef3c0545779c06ac7dcc41a1a6.json`) plus its
prerequisite frozen estimators (Hansen 2005 SPA, panel Romano-Wolf StepM),
the registered `first-admission-verdict` multiplicity family, the
adjudication harness [run_verdict.py](../../scripts/run_verdict.py), and the
disposition emitter [emit_verdict_disposition.py](../../scripts/emit_verdict_disposition.py).
Method: audit-remediate loop (Workflow engine, 5-branch specialist +
adversarial refute gate, 3-round cap). Verdict: **ACCEPT at round 3 (cap
reached).***

## Frozen artifacts

| Artifact | Freeze basis |
|---|---|
| [VERDICT-1_protocol.md](../../research/02_verdict/VERDICT-1_protocol.md) | SHA in freeze ReproLog `config_resolved_sha256`; append-only after this SHA |
| [hansen_spa.py](../../src/skie_universe2/inference/hansen_spa.py) + [memo](../methodology/hansen_spa_2026-07-19.md) + 13 tests | arch==8.0.0 cross-validation (1e-12 on deterministic parts) |
| `romano_wolf_stepm_panel` in [romano_wolf.py](../../src/skie_universe2/inference/romano_wolf.py) + [memo](../methodology/romano_wolf_panel_2026-07-19.md) + 7 tests | k=1 masked-variant equivalence; shared `_stepdown_adjust` behavior-pinned |
| `first-admission-verdict` family, [multipletest_family.yaml](../../config/multipletest_family.yaml) | surface rule registered BEFORE any statistic |

## Round 1 (VERDICT-1 protocol + estimators + family + harness scaffold)

Verdict proceed-with-remediation. **1 major confirmed by refuter:**

- **QUANT-1-4** (major, confirmed) — §3(ii) conflated joint-bootstrap
  within-panel dependence modeling with screen→verdict selection
  conditioning. FIX: §3(ii) now attributes selection accounting solely to
  the register + clause-4 cumulative-trial DSR deflation (naming its
  provisional-proxy status); §2.2 gained a declarative error-rate-semantics
  paragraph (nominal p-values unconditional on the screen event).

Minors remediated (freeze-relevant): CODE-1-1 (shared `_stepdown_adjust`
extraction), CODE-1-2/QUANT-1-2/REPRODUCIBILITY-1-1 (`arch==8.0.0` pin +
private-API-coupling justification), CODE-1-3/QUANT-1-7 (panel docstring),
CODE-1-4 (`sb_kernel_variance` guards), QUANT-1-1/LITERATURE-1-2 (unfloored-max
deviation disclosed + conservative-direction argument), QUANT-1-3 (B2
identity-anchor Phase-4 scope note), QUANT-1-5 (S=16 CSCV justification),
QUANT-1-6 (adjudication-index in trial id), REPRODUCIBILITY-1-2 (SEED_VERDICT
harness-constant test), LITERATURE-1-1/1-3 (arch-default + pinpoint wording),
LITERATURE-1-4/1-5 (Berger 1982 + Šidák 1967 DOIs).

## Round 2 (after remediation)

Verdict proceed-with-remediation. **4 majors confirmed by refuter, 1 refuted:**

- **QUANT-2-1** (confirmed) — B1/B3 per-origin fit used an EXPANDING train
  window, not the registered 24-month ROLLING span. FIX: harness masks
  `[w.train_start ≤ d < w.origin]` (both bounds); protocol §10 states both
  bounds binding; new test `test_rolling_train_excludes_pre_train_start`.
- **QUANT-2-2** (confirmed) — the ES-then-NQ row concatenation put
  contemporaneous cross-instrument dependence at lag T, invisible to a
  block bootstrap (anti-conservative on the binding clauses). FIX: the joint
  panel is rebuilt SESSION-ALIGNED with 8 columns (instrument × arm); one
  bootstrap index sequence spans all 8 columns → serial + cross-arm +
  cross-instrument dependence in columns. Propagated to protocol §1/§2/§3/§6,
  surface 16/40, the harness, emitter, and tests.
- **QUANT-2-3** (confirmed) — DSR trial COUNT (40) vs dispersion pool (from
  4 marginal Sharpes) diverged at |U|≥2. FIX: dispersion pools ALL
  current-surface Sharpe-bearing column trials (8 marginal + 24 rung);
  rotor trials declaredly Sharpe-less; protocol §6 declares the difference.
- **QUANT-2-4** (REFUTED) — the alleged missing §8 side-effect emitter: the
  refuter reproduced that `emit_verdict_disposition.py` already exists.
  Dropped; the emitter was subsequently hardened + tested.
- **REPRODUCIBILITY-2-1** (confirmed) — incumbent ledger partitions omitted
  from the ReproLog checksums. FIX: `main()` loops candidate + every
  incumbent family.

Minors remediated: REPRODUCIBILITY-2-2 (cp1252 `--help` crash → stdout/stderr
reconfigure + ASCII argparse description), QUANT-2-5/2-6/REPRODUCIBILITY-2-3
(block-length + rotor-seed wording → protocol §10 matches the harness),
QUANT-2-7 (vacuous PIT test → perturb a LATER window, assert earlier-window
B1 AND B3 bit-identical), LITERATURE-2-1 (Hansen §2 pinpoint quote →
unquoted paraphrase), CODE-2-1/2-2/2-3 (dead var removed, `ArmStreams` alias,
de-obfuscated boolean).

## Round 3 (FINAL, cap reached)

Verdict **ACCEPT** (0 to remediate; 4 minors logged and then applied as
freeze-relevant polish on the permanent append-only artifact):

- **CODE-3-1** — duplicated `_REGISTRY`/`KELLY_GRID` across harness + emitter.
  APPLIED: extracted to [src/skie_universe2/verdict/registry.py](../../src/skie_universe2/verdict/registry.py),
  imported by both (they cannot drift).
- **CODE-3-2** — `_fmt_sr` missing param annotation. APPLIED.
- **QUANT-3-1** — dispersion pool hardcoded a 4-family tuple while the count
  enumerated rc-* dynamically (agree now = 40; structurally asymmetric under
  a mid-queue register change). APPLIED: dispersion families discovered from
  the same non-empty rc-* enumeration (`_nonempty_rc_families`), so count and
  dispersion provably share one surface.
- **REPRODUCIBILITY-3-1** — protocol §6 said count/dispersion "differ ONLY by
  the rotor exception", but the cumulative screen base also excludes
  `:unconditional` cells from the dispersion pool. APPLIED: §6 now discloses
  the divergence is the rotor exception PLUS the inherited `:unconditional`
  exclusion (no computed number changes).

## Residual risk (declared)

The harness computes NO verdict statistic on real data pre-freeze (freeze +
ADR-0015 operator gate). First-run data-shape edge cases (e.g. < 4 aligned
OOS sessions after the fitted-mask selection, a near-constant differential
column tripping `hansen_spa`'s degeneracy guard) are unexercised until the
gated first adjudication. All literature citations verified EXACT against
Crossref; environment reproduces (arch==8.0.0 + polars==1.40.0 pinned in
uv.lock). No Kelly fraction selected; append-only discipline enforced with
layout-drift refusal.
