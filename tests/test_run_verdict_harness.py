"""Tests for the VERDICT-1 adjudication harness's pure machinery.

Pins the protocol §10 commitments that are testable without ledger
evidence: the exact blend identity (§1), the per-origin benchmark fitting's
NO-FUTURE-DEPENDENCE (perturbing eval-span data must not move any
train-fitted weight or any other window's benchmark stream), the eval-span
session filter, and the member alignment join. No verdict statistic is
computed here (the protocol freeze gates that).
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]


def _load_harness():
    if "run_verdict_harness" in sys.modules:
        return sys.modules["run_verdict_harness"]
    spec = importlib.util.spec_from_file_location(
        "run_verdict_harness", _ROOT / "scripts" / "run_verdict.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_verdict_harness"] = mod
    spec.loader.exec_module(mod)
    return mod


from skie_universe2.eval.windows import h900_windows  # noqa: E402

_H = _load_harness()


def _weekday_dates(start: date, n: int) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


class TestBlendMath:
    def test_ew_blend_exact_identity(self) -> None:
        # Two members with session log-returns r1, r2: the session-rebalanced
        # EW blend log-return must equal log(1 + (e^r1 - 1)/2 + (e^r2 - 1)/2).
        rng = np.random.default_rng(20260721)
        mat = rng.normal(0.0, 0.01, size=(50, 2))
        blend = _H._ew(mat)
        expected = np.log1p(0.5 * np.expm1(mat[:, 0]) + 0.5 * np.expm1(mat[:, 1]))
        assert np.allclose(blend, expected, rtol=1e-14)

    def test_single_member_blend_is_identity(self) -> None:
        rng = np.random.default_rng(20260721)
        mat = rng.normal(0.0, 0.01, size=(30, 1))
        assert np.allclose(_H._ew(mat), mat[:, 0], rtol=1e-14)


class TestPerOriginBenchmarks:
    def _fixture(self) -> tuple[list[date], np.ndarray]:
        w0 = h900_windows()[0]
        # Enough weekdays to fully cover windows 0 and 1 (train + eval).
        dates = _weekday_dates(w0.train_start, 1000)
        rng = np.random.default_rng(20260721)
        mat = rng.normal(0.0, 0.01, size=(len(dates), 3))
        mat[:, 1] += 0.002  # member 1 dominates in-sample
        return dates, mat

    def test_b1_selects_train_dominant_member(self) -> None:
        dates, mat = self._fixture()
        b1, _, fitted = _H._per_origin_benchmark_streams(dates, mat)
        w0 = h900_windows()[0]
        ev0 = np.array([(w0.origin <= d < w0.eval_end) for d in dates])
        assert fitted[ev0].all()
        assert np.allclose(b1[ev0], mat[ev0][:, 1], rtol=1e-14)

    def test_rolling_train_excludes_pre_train_start(self) -> None:
        """Audit QUANT-2-1: the 24-month train span is ROLLING, both bounds
        binding. Perturbing sessions BEFORE a window's train_start must not
        move that window's B1 selection or B3 weights (an expanding-train
        implementation would let them leak in)."""
        dates, mat = self._fixture()
        w1 = h900_windows()[1]
        b1_a, b3_a, _ = _H._per_origin_benchmark_streams(dates, mat)
        ev1 = np.array([(w1.origin <= d < w1.eval_end) for d in dates])
        pre_train = np.array([d < w1.train_start for d in dates])
        assert pre_train.any() and ev1.any()
        mat2 = mat.copy()
        mat2[pre_train] += 100.0  # violent perturbation strictly before w1's train
        b1_b, b3_b, _ = _H._per_origin_benchmark_streams(dates, mat2)
        # w1's benchmarks depend only on [train_start, origin): bit-identical.
        assert np.allclose(b1_a[ev1], b1_b[ev1], rtol=0, atol=0)
        assert np.allclose(b3_a[ev1], b3_b[ev1], rtol=0, atol=0)

    def test_no_future_dependence(self) -> None:
        """Protocol §10: perturbing a LATER window's EVAL span must not move
        an EARLIER window's train-fitted B1 selection OR B3 weights (audit
        QUANT-2-7 — the prior test's pre-origin assertion was vacuous because
        those rows are all-NaN)."""
        dates, mat = self._fixture()
        w0, w1 = h900_windows()[0], h900_windows()[1]
        ev0 = np.array([(w0.origin <= d < w0.eval_end) for d in dates])
        ev1 = np.array([(w1.origin <= d < w1.eval_end) for d in dates])
        assert ev0.any() and ev1.any()
        b1_a, b3_a, _ = _H._per_origin_benchmark_streams(dates, mat)
        mat2 = mat.copy()
        mat2[ev1] += 100.0  # violent perturbation of w1's eval span (after w0's train)
        b1_b, b3_b, _ = _H._per_origin_benchmark_streams(dates, mat2)
        # w0's train span [w0.train_start, w0.origin) is disjoint from w1's
        # eval span, so BOTH benchmarks over w0's eval must be bit-identical.
        assert np.allclose(b1_a[ev0], b1_b[ev0], rtol=0, atol=0)
        assert np.allclose(b3_a[ev0], b3_b[ev0], rtol=0, atol=0)


class TestSeedContract:
    def test_seed_verdict_matches_protocol_value(self) -> None:
        """Protocol §10 registers SEED_VERDICT = 20260721 (date-derived,
        distinct from every screen seed); the harness constant is the
        machine-readable source of that commitment (audit
        REPRODUCIBILITY-1-2)."""
        assert _H.SEED_VERDICT == 20260721  # noqa: PLR2004 — the registered protocol constant itself


class TestEvalFilterAndAlign:
    def test_eval_filter_matches_windows(self) -> None:
        w0 = h900_windows()[0]
        inside = w0.origin
        before = w0.train_start
        mask = _H._eval_session_filter([before, inside])
        assert mask.tolist() == [False, True]

    def test_align_inner_join_order(self) -> None:
        d1 = _weekday_dates(date(2020, 1, 1), 5)
        d2 = d1[1:]  # member 2 missing the first session
        m1 = _H.MemberStreams(
            name="a",
            by_instrument={"ES": {1.0: (d1, np.arange(5, dtype=float), np.arange(5, dtype=float))}},
        )
        m2 = _H.MemberStreams(
            name="b",
            by_instrument={
                "ES": {1.0: (d2, np.arange(4, dtype=float) * 10, np.arange(4, dtype=float))}
            },
        )
        dates, mat = _H._align([m1, m2], "ES", 1.0)
        assert dates == d2
        assert mat.shape == (4, 2)
        assert np.allclose(mat[:, 0], [1, 2, 3, 4])
        assert np.allclose(mat[:, 1], [0, 10, 20, 30])
