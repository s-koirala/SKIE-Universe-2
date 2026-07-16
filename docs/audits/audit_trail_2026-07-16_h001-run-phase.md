# Audit trail — H001 run-phase estimators + harness

**Deliverable:** the H001 run-phase code executing the frozen design §4/§5/§8 —
[covariate_information.py](../../src/skie_universe2/inference/covariate_information.py)
(forward-VR target, Miller-Madow CMI, conditional restricted permutation, pooled
stationary-bootstrap CI, nested predictive delta, redundancy),
[variance_ratio_state.py](../../src/skie_universe2/features/variance_ratio_state.py)
(S_vr), the harness
[run_h001_covariate_study.py](../../scripts/run_h001_covariate_study.py), the public
scalar wrappers in
[regime_covariate.py](../../src/skie_universe2/signals/regime_covariate.py), and
the tests [test_covariate_information.py](../../tests/test_covariate_information.py) /
[test_variance_ratio_state.py](../../tests/test_variance_ratio_state.py).

**Mechanism:** [audit-remediate-loop](../../../.claude/skills/audit-remediate-loop)
via the Workflow engine, `.py` routing → **code-reviewer**, **quant-auditor**,
**reproducibility-verifier**, adversarial refute gate. Runs: round 1
`wf_9942f56a-9e1`, round 2 `wf_ad7c3da6-0c4`.

**Outcome:** ACCEPT at round 2 (all three branches accept; zero surviving
findings). Round 1 raised 3 majors + 9 minors; all remediated.

## Round 1 — verdict: proceed-with-remediation (3 majors, 0 refuted, 9 minors); code-reviewer ACCEPT

| ID | Branch | Issue | Disposition |
|---|---|---|---|
| QUANT-1-1 | quant | **Binding H1 gate used the plug-in CMI** (positively biased ~`(K_xyz+K_z−K_xz−K_yz)/2N` ≈ 4e-4 nats at N≈58k, the same order as the signal); MM correction computed but discarded. Counter-test under true conditional independence: plug-in fired CI>0 in 100% of reps, MM in ~60%. | **Fixed** — gate now uses the **n-weighted average of per-window Miller-Madow CMI** (labels stay within-window, also resolving QUANT-1-3); bootstrap CI shifted onto the MM scale by the deterministic bias offset; `cmi_plugin` retained for transparency |
| QUANT-1-2 | quant | **Permutation null anti-conservative** on the overlapping-window forward target (empirical Type-I 0.30 at h=6, 0.51 at h=12 vs 0.05) — the within-cell iid shuffle ignores the h−1-bar overlap. | **Fixed** — demoted to **illustrative-only** with a docstring exchangeability caveat; removed from the H1 decision (binding = MM-CI lower bound > 0 AND OOS delta > 0); run for the top-6 arms by CMI only |
| REPRODUCIBILITY-1-1 | repro | `uv sync` installed **no runtime deps** (numpy/polars/scipy under `data`, sklearn/numba under `models`) → entrypoint/tests fail out-of-box. | **Fixed** — `tool.uv.default-extras = ["data","models","dev"]`; documented `uv venv && uv sync` now reproduces |
| CODE-1-1 | code | broad `except ValueError: pass` around the nested delta could mask unrelated errors | **Fixed** — replaced with an explicit both-classes precondition guard |
| CODE-1-4 | code | `main()` exceeds the 50-line threshold untagged | **Fixed** — scoped `noqa: PLR0915` with justification |
| QUANT-1-3 | quant | pooled permutation/CMI pooled non-comparable across-window HMM labels into one table | **Fixed** — binding estimate is per-window (labels within-window); permutation illustrative-only |
| QUANT-1-4 | quant | S_vt not independently segment-masked | **Fixed (doc)** — the S_vr 288+q−2-bar segment mask strictly dominates the ≤8-bar S_vt lookback, so S_vt cross-break bars are already excluded; documented |
| QUANT-1-5 | quant | bootstrap circular blocks may wrap disjoint eval spans | **Dispositioned** — documented negligible edge effect (block ≪ window length) |
| REPRODUCIBILITY-1-3 | repro | ReproLog `model_hash` ingested parquet (byte-encoding varies by version) | **Fixed** — hash restricted to text artifacts (csv + json) |
| CODE-1-2/1-3, REPRO-1-2 | code/repro | internal type annotations, positional tuple, no `reproduce` target | Logged (below-threshold polish; not remediated) |

## Round 2 — verdict: accept (0 findings; all three branches accept)

All three majors verified correctly remediated. New remediation code confirmed
sound: the vectorized `_stationary_block_indices` is a distributionally-equivalent
stationary bootstrap; the precompute refactor routes train+eval through the same
`states_from_scalars` with a train-only fitted median (leakage-safe, S_vt-identical
to the emitter path, independently verified bit-identical to the pre-refactor run);
the CI-shift-by-MM-correction is a defensible location bias correction.

## Residual risk (recorded, non-blocking)

- The CI shift treats the MM correction as a deterministic offset and does not
  propagate its own second-order (`O(K/2N)`) sampling variability into the CI
  width — negligible at N≈1e5+.
- The pooled block bootstrap resamples plug-in contributions concatenated across
  non-contiguous eval spans; circular blocks may wrap span boundaries (QUANT-1-5)
  — negligible at block ≪ window length.
- The vectorized bootstrap is distributionally, not bit-, identical to the
  per-element reference — adequate for mean CIs.
- **Large-N interpretation caveat (material):** at ~1e5+ pooled bars a negligible
  CMI trivially clears the CI>0 bar, so nearly all arms register "H1". The binding
  screening/FWER level (which weighs effect size against the 400-arm multiplicity)
  is the DEFERRED project-wide `screening_error_rate_target`, so no arm is
  certified. **Effect magnitudes (CMI nats, OOS log-loss reduction, ARI-vs-HMM),
  not the H1 count, are the material read** — foregrounded in the disposition
  report.

Estimator + emitter tests: 49 passing. Lint clean (ruff + format).
