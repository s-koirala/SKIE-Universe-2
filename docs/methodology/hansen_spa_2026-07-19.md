# Hansen (2005) SPA — frozen reference estimator

*Method freeze date: 2026-07-19. Estimator:
[src/skie_universe2/inference/hansen_spa.py](../../src/skie_universe2/inference/hansen_spa.py)
(13 tests, [tests/test_hansen_spa.py](../../tests/test_hansen_spa.py)).
Purpose: the ADR-0007 Decision 3 confirmation-ladder existence test ("does
ANY candidate in a registered family outperform a benchmark"), required by
the first-admission VERDICT protocol (VERDICT-1) and reusable at Phase 4.
No SPA statistic was computed on project evidence before this freeze.*

## 1. The test

[Hansen 2005, J. Bus. Econ. Stat. 23(4):365-380](https://doi.org/10.1198/073500105000000063)
tests the null that no candidate in the family outperforms the benchmark —
`E[d_k] ≤ 0` for all k, `d_k` the per-period performance differential
candidate-minus-benchmark (paraphrase, not a quotation) — against the
union alternative that at least one does. It repairs the two documented defects of White's Reality Check
([White 2000](https://doi.org/10.1111/1468-0262.00152)): (i) the RC's
least-favorable null (every candidate exactly at the boundary) makes its
p-value inflatable by adding poor/irrelevant candidates; (ii) the
unstudentized RC statistic is dominated by high-variance candidates.
Hansen's fixes — studentization and a sample-dependent recentering that
excludes candidates rejected by a law-of-iterated-logarithm band — are both
implemented.

## 2. Implementation choices (each verifiable in the source)

1. **Statistic (primary):** the studentized
   `T = max_k √t · d̄_k / ω̂_k` (Hansen's T^SPA form). `studentize=False`
   gives the unstudentized max-mean variant, retained for the
   cross-validation benchmark (arch's `SPA` supports both; its own
   `studentize` default is True — audit LITERATURE-1-1 correction).
   **Disclosed deviation (audit QUANT-1-1):** Hansen's T^SPA carries an
   outer floor at zero (`max{·, 0}`); this implementation and the arch
   reference both use the UNFLOORED max. Both sides of the bootstrap
   comparison share the transform, so p-values coincide whenever any
   candidate mean is positive; with all means negative the unfloored
   p-value is weakly larger — conservative, cannot manufacture an
   admission.
2. **Long-run variance `ω̂²_k`:** the stationary-bootstrap kernel closed
   form `γ̂_0 + 2Σᵢ κ(i)γ̂_i`, `κ(i) = (1−i/t)(1−p)^i + (i/t)(1−p)^{t−i}`,
   `p = 1/block_length` — term-for-term the reference implementation's
   non-nested `_compute_variance`, asserted equal at 1e-12 in
   `test_kernel_variance_matches_arch`. Floored at 0 (finite-sample kernel
   estimates can dip negative).
3. **Null distribution:** stationary bootstrap
   ([Politis & Romano 1994](https://doi.org/10.1080/01621459.1994.10476870))
   with JOINT row resampling (one index draw per replicate applied to all
   columns — cross-candidate dependence preserved), reusing the frozen
   project `stationary_bootstrap_indices`; block length supplied by the
   caller via the frozen Politis-White selector
   ([2004](https://doi.org/10.1081/ETC-120028836), as corrected by
   [Patton, Politis & White 2009](https://doi.org/10.1080/07474930802459016)
   — the constants the in-repo `bootstrap.py` implements).
4. **Three recenterings, three p-values** (`lower ≤ consistent ≤ upper`,
   pinned by test): `g_l = max(d̄,0)`;
   `g_c = d̄·1{d̄ ≥ −√((ω̂²/t)·2 log log t)}` (the LIL validity band;
   mask asserted equal to the reference's `_check_column_validity`);
   `g_u = d̄` (the RC analog). **`consistent` is the PRIMARY p-value**
   (Hansen's recommendation); `upper`/`lower` are reported bounds.
5. **p-value:** `(1/B)·#{T*_b > T}` (strict inequality, matching the
   reference). The bootstrap statistic uses the SAME `ω̂_k` as the observed
   statistic (per Hansen 2005 and the arch reference; the paywalled
   original's internal section numbers are not independently verified and
   are not pinpoint-cited — audit LITERATURE-1-3).
6. **Degeneracy fail-closed:** non-finite inputs, `t < 4` (LIL undefined),
   `block_length < 1`, and near-constant columns raise — a constant
   differential has no sampling distribution, and silently dropping a
   column would alter the family the register recorded.

## 3. Verification record

- **Deterministic components vs the vetted reference implementation**
  (`arch` 8.0.0, declared in `pyproject.toml` SOLELY as this benchmark):
  kernel variances equal at 1e-12; LIL validity masks equal; recentering
  vectors equal by construction (same means/masks).
- **Stochastic components:** unstudentized p-values within 0.05 of
  `arch.SPA` on a fixed separated case at B = 2000 (independent RNG
  streams; MC SE ≈ 0.011).
- **Paper properties pinned by test:** p-value ordering; power on a
  dominant candidate (p ≤ 0.01); null non-rejection; the headline
  poor-alternative insensitivity (adding a μ = −2 candidate leaves
  `consistent` unchanged within MC noise while the RC-style `upper` cannot
  decrease; the added candidate is LIL-invalid); studentization
  scale-invariance; seed determinism.
- The verdict machinery calls ONLY this frozen estimator; `arch` is never
  imported outside the test.

## 4. Scope and non-scope

Used by VERDICT-1 (one SPA per ladder benchmark over a candidate's
registered Kelly-arm family, intersection-union across benchmarks — the
protocol, not this memo, fixes that structure) and reusable at Phase 4 over
(allocator-config × Kelly) families. This memo freezes the ESTIMATOR only:
no level (read from `config/multipletest_family.yaml` at runtime), no
family definition, no admission rule lives here.
