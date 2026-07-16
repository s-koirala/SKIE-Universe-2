# Audit trail — H001 covariate emitter (reference implementation)

**Deliverable:** the H001 frozen design §5 pure conditioning-covariate emitter —
[src/skie_universe2/signals/indicators.py](../../src/skie_universe2/signals/indicators.py)
(six new causal indicators: `ema`, `kama`, `linreg_slope`, `atr`, `parkinson`,
`realized_vol`) and
[src/skie_universe2/signals/regime_covariate.py](../../src/skie_universe2/signals/regime_covariate.py)
(`RegimeCovariateEmitter`, leakage-safe fit/transform), with tests
[tests/test_indicators.py](../../tests/test_indicators.py) and
[tests/test_regime_covariate.py](../../tests/test_regime_covariate.py).

**Mechanism:** [audit-remediate-loop](../../../.claude/skills/audit-remediate-loop)
via the Workflow engine, `.py` routing → **code-reviewer**, **quant-auditor**,
**reproducibility-verifier**, adversarial refute gate. Run `wf_db5ee578-7a8`.

**Outcome:** ACCEPT at round 1 — all three branches accept; **0 critical/major**;
7 minors logged and all remediated (accuracy/robustness, not deferred as polish).
Core verified: no look-ahead in any indicator, leakage-safe median split (fit on
train, applied verbatim to test), correct indicator formulas, correct state
mapping.

## Round 1 — verdict: accept (0 remediate, 7 minors, all fixed)

| ID | Branch | Issue | Disposition |
|---|---|---|---|
| CODE-1-1 | code-reviewer | 6 new indicators used prose docstrings vs the module's NumPy Parameters/Returns style | **Fixed** — NumPy-style sections added to all six |
| CODE-1-2 | code-reviewer | `UNDETERMINED` duplicated (const + enum); `vol_bit*2+trend_bit` encoding not tied to `RegimeState` → silent drift risk | **Fixed** — sentinel derived from enum; `test_state_index_encoding_is_locked` pins 0/1/2/3 |
| CODE-1-3 | code-reviewer | `OHLCArrays` didn't coerce list/Series inputs → `AttributeError` not `ValueError` | **Fixed** — `np.asarray(...,float64)` coercion in `__post_init__` |
| QUANT-1-1 / REPRODUCIBILITY-1-1 | quant / repro | actual warm-up is family-dependent (`max(n_v,n_t)`, not `-1`) for `sma_slope`/`atr`/log-return vol families | **Fixed** — family-dependent conservative warm-up documented; `test_extra_warmup_bar_for_first_difference_family` added. No code change (behaviour is conservative, no leakage) |
| QUANT-1-2 / REPRODUCIBILITY-1-2 | quant / repro | KAMA docstring "0..period-1 NaN" off by one (index `period-1` is the finite seed) | **Fixed** — docstring corrected; `test_seed_is_finite_at_period_minus_one` added |

## Residual risk (recorded)

- The emitter is the §5 state constructor only. The **full H001 run** — the
  conditional-MI / nested-prediction estimators, the rolling-origin harness with
  horizon-aware purge, the 400-arm scan, and the forward variance-ratio target —
  is the next (run-phase) build, not covered here.
- A **PIT canary** (ADR-0008) over the full feature→label pipeline is due at the
  run build; the leakage-safe fit/transform contract and the `transform(prefix)
  == transform(full)[:k]` causality test cover the emitter in isolation, but the
  end-to-end pipeline canary is still owed once the estimator/label layer exists.

Tests: 44 passing (leakage-safety, causality, encoding lock, per-family warm-up,
all 16 family combinations, known indicator values). Lint clean (ruff + format).
