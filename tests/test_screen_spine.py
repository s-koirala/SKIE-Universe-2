"""Tests for the packaged ADR-0014 screen spine (screening/screen_spine.py).

Pins the leakage-clean per-origin percentile construction (no future
dependence — the property whose absence the H103 record convicted), the
matched-surface dispersion reader, and the pure helpers extracted from the
RC-*-2 harness.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import polars as pl
import pytest

from skie_universe2.eval.windows import h900_windows
from skie_universe2.screening import screen_spine as spine
from skie_universe2.utils.paths import ProjectPaths


def _covs(values: dict[date, float]) -> pl.DataFrame:
    return pl.DataFrame(
        {"session_date": list(values.keys()), "rvol_entry": list(values.values())}
    ).sort("session_date")


def _weekday_dates(start: date, n: int) -> list[date]:
    out, d = [], start
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


class TestPerOriginPercentile:
    def _base(self) -> dict[date, float]:
        w0 = h900_windows()[0]
        train_dates = _weekday_dates(w0.train_start, 40)
        eval_dates = _weekday_dates(w0.origin, 10)
        vals = {d: float(i) for i, d in enumerate(train_dates)}  # 0..39, sorted
        vals.update({d: 20.0 for d in eval_dates})  # eval value = train median area
        return vals

    def test_percentile_is_train_window_rank(self) -> None:
        vals = self._base()
        out = spine.per_origin_percentile(_covs(vals), "rvol_entry")
        w0 = h900_windows()[0]
        ev = out.filter(pl.col("session_date") >= w0.origin)
        # value 20.0 against train values 0..39: searchsorted right -> 21/40.
        assert ev.height > 0
        assert np.allclose(ev.get_column("rvol_entry_pct").to_numpy(), 21.0 / 40.0)

    def test_no_future_dependence(self) -> None:
        """Changing LATER sessions' values must not move earlier labels."""
        vals = self._base()
        out1 = spine.per_origin_percentile(_covs(vals), "rvol_entry")
        w1 = h900_windows()[1]
        vals2 = dict(vals)
        for d in _weekday_dates(w1.origin, 30):  # perturb a later window's span
            vals2[d] = 1e9
        out2 = spine.per_origin_percentile(_covs(vals2), "rvol_entry")
        w0 = h900_windows()[0]
        a = out1.filter(pl.col("session_date") < w0.eval_end)
        b = out2.filter(pl.col("session_date") < w0.eval_end)
        assert a.equals(b)

    def test_pre_origin_sessions_unlabeled(self) -> None:
        vals = self._base()
        out = spine.per_origin_percentile(_covs(vals), "rvol_entry")
        first_origin = h900_windows()[0].origin
        assert out.get_column("session_date").min() >= first_origin

    def test_all_null_raises(self) -> None:
        frame = pl.DataFrame(
            {"session_date": [date(2017, 1, 3)], "rvol_entry": [None]},
            schema={"session_date": pl.Date, "rvol_entry": pl.Float64},
        )
        with pytest.raises(RuntimeError, match="all-null"):
            spine.per_origin_percentile(frame, "rvol_entry")


class TestRegisterTrialSharpes:
    def test_reads_recorded_families_excluding_unconditional(self) -> None:
        # Real project config: rc-h101-2 and rc-h103-2 carry 10 trials each,
        # of which 2 per family are :unconditional.
        paths = ProjectPaths.discover()
        vals = spine.register_trial_sharpes(paths, ("rc-h101-2", "rc-h103-2"))
        assert len(vals) == 16
        assert all(isinstance(v, float) for v in vals)

    def test_unknown_family_raises(self) -> None:
        # FAIL-CLOSED: a named family absent from the register raises
        # (round-2 audit CR-2-1); silent skip would be indistinguishable
        # from the present-but-empty case.
        paths = ProjectPaths.discover()
        with pytest.raises(RuntimeError, match="not found"):
            spine.register_trial_sharpes(paths, ("no-such-family",))

    def test_named_empty_family_raises(self, tmp_path) -> None:
        # FAIL-CLOSED on zero recorded trials (round-2 audit QUANT-2-3),
        # pinned on a SYNTHETIC config so the contract holds regardless of
        # the live register's state (round-3 audit CODE-3-1/QUANT-3-1: the
        # live rc-h105-1 family stops being empty once its disposition
        # emitter runs, which must not break this test).
        cfg = tmp_path / "config"
        cfg.mkdir()
        (cfg / "multipletest_family.yaml").write_text(
            "schema_version: 1\n"
            "screening_error_rate_target: 0.5\n"
            "families:\n"
            "  - family_id: populated-fam\n"
            "    correction: romano-wolf\n"
            "    trials:\n"
            "      - hid: HX:ES:cell_a\n"
            "        sharpe_estimate: 0.01\n"
            "  - family_id: empty-fam\n"
            "    correction: romano-wolf\n"
            "    trials: []\n",
            encoding="utf-8",
        )
        paths = ProjectPaths(root=tmp_path)
        assert spine.register_trial_sharpes(paths, ("populated-fam",)) == [0.01]
        with pytest.raises(RuntimeError, match="no recorded trial Sharpes"):
            spine.register_trial_sharpes(paths, ("populated-fam", "empty-fam"))


class TestPureHelpers:
    def test_member_only_sharpe_degenerate_columns(self) -> None:
        mat = np.column_stack(
            [
                np.array([1.0, 2.0, 3.0, 4.0]),
                np.array([np.nan, np.nan, np.nan, 1.0]),  # < MIN_CELL_N members
            ]
        )
        out = spine.member_only_sharpe(mat)
        assert np.isfinite(out[0])
        assert out[1] == -np.inf

    def test_consecutive_run_median(self) -> None:
        m = np.array([True, True, False, True, True, True, False])
        assert spine.consecutive_run_median(m) == 2.5
        assert spine.consecutive_run_median(np.array([], dtype=bool)) == 0.0

    def test_hac_vif_floor(self) -> None:
        rng = np.random.default_rng(20260719)
        x = rng.normal(size=500)
        assert spine.hac_variance_inflation(x) >= 1.0

    def test_hac_vif_bandwidth_cap_small_negatively_autocorrelated(self) -> None:
        # Round-2 audit REPRODUCIBILITY-2-1/QUANT-2-1 regression: without
        # the frozen m <= n-1 bandwidth cap, small strongly autocorrelated
        # cells drive m > n and crash the autocovariance slices. Both the
        # alternating-sign and the MA(2)-style |s1/s0|-large constructions
        # must return a finite VIF >= 1.
        for n in (4, 10, 17, 20):
            alt = np.array([1.0 if i % 2 == 0 else -1.0 for i in range(n)])
            v = spine.hac_variance_inflation(alt)
            assert np.isfinite(v) and v >= 1.0
        rng = np.random.default_rng(20260720)
        e = rng.normal(size=19)
        ma2 = e[2:] - 0.5 * e[1:-1] - 0.49 * e[:-2]  # 1+2r1+2r2 near 0
        v = spine.hac_variance_inflation(ma2)
        assert np.isfinite(v) and v >= 1.0

    def test_hac_vif_matches_frozen_rc1_helper(self) -> None:
        # The spine body must agree with the frozen RC-H101-1 helper on
        # ordinary inputs (the living-copy contract).
        root = Path(__file__).resolve().parents[1]
        if "rc_h101_harness" in sys.modules:
            mod = sys.modules["rc_h101_harness"]
        else:
            fspec = importlib.util.spec_from_file_location(
                "rc_h101_harness", root / "scripts" / "run_rc_h101_1_scan.py"
            )
            mod = importlib.util.module_from_spec(fspec)
            sys.modules["rc_h101_harness"] = mod
            fspec.loader.exec_module(mod)
        rng = np.random.default_rng(20260719)
        for _ in range(5):
            x = rng.normal(size=300) + 0.3 * np.sin(np.arange(300) / 7.0)
            assert spine.hac_variance_inflation(x) == pytest.approx(
                mod._hac_variance_inflation(x), rel=1e-12
            )

    def test_kpss_reports_both_variants(self) -> None:
        rng = np.random.default_rng(20260719)
        x = rng.normal(size=400)
        out = spine.kpss_stationarity(x)
        assert set(out) == {"stat", "reject_stationarity_5pct", "level_c", "trend_ct"}
        assert not out["reject_stationarity_5pct"]  # white noise is level-stationary

    def test_json_sanitize(self) -> None:
        blob = {"a": float("nan"), "b": float("inf"), "c": [1.0, float("-inf")]}
        out = spine.json_sanitize(blob)
        assert out == {"a": None, "b": "inf", "c": [1.0, "-inf"]}
