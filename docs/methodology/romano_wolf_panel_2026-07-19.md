# Panel Romano-Wolf StepM — frozen reference estimator

*Method freeze date: 2026-07-19. Estimator:
`romano_wolf_stepm_panel` in
[src/skie_universe2/inference/romano_wolf.py](../../src/skie_universe2/inference/romano_wolf.py)
(append-only addition; the masked variant is untouched). Tests:
[tests/test_romano_wolf_panel.py](../../tests/test_romano_wolf_panel.py)
(7). Purpose: the VERDICT-1 per-benchmark IDENTIFICATION step over a
candidate's registered Kelly-arm family. No panel-StepM statistic was
computed on project evidence before this freeze.*

## 1. Why a panel variant

The frozen `romano_wolf_stepm` tests masked SUBSETS of one per-session
series (the screen-tier conditioning-cell family). The verdict-tier family
is different in kind: the four registered Kelly-arm marginal-growth-delta
streams of one candidate are four DISTINCT series over the same session
axis (the levered log-return map is nonlinear in the fraction, so arms are
not scalar multiples). Concatenation tricks would destroy the cross-arm
dependence structure the joint bootstrap must preserve; hence a panel
variant.

## 2. Construction (mirrors the masked variant stage-for-stage)

- H0_k: `E[panel[:,k]] ≤ 0`; one-sided studentized
  `t_k = mean_k/(sd_k/√t)` with the masked variant's exact
  degenerate-column conventions (constant-positive → +inf, etc.).
- Joint null: stationary bootstrap
  ([Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870))
  resampling ROWS — one index draw per replicate applied to every column,
  cross-arm dependence preserved; block length caller-supplied via the
  frozen Politis-White selector.
- Adjusted p-values: the identical Romano-Wolf efficient step-down
  algorithm and consonant rejection walk, verbatim from the masked variant
  ([Romano & Wolf 2005](https://doi.org/10.1111/j.1468-0262.2005.00615.x);
  the module's recorded 2016 algorithmic form).
- Fail-closed: non-finite panels raise (a partially-observed family is a
  different estimand); columns below `min_n` are never rejected.

## 3. Verification record

Pinned by test: **exact k=1 equivalence with the frozen masked variant**
(same series, all-true mask, same seeded Generator → identical statistic,
adjusted p, rejection at 1e-12 — the two implementations share the
bootstrap draw sequence by construction); dominant-column identification;
null non-rejection; step-down monotonicity of adjusted p-values along the
statistic order; degenerate-column conventions; seed determinism.

## 4. Scope

VERDICT-1 per-benchmark identification (which Kelly arms of a candidate
outperform benchmark j, FWER-controlled over the 4-arm family) and
reusable at Phase 4 over (allocator-config × Kelly) panels. Levels are
passed by the caller from `config/multipletest_family.yaml` at runtime.
