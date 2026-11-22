"""End-to-end synthetic test of the H107 backfill rows -> screen-panel path.

Exercises, on a synthetic 5-min substrate (no vendor data needed):
``run_shadow_ledger_backfill._rows_for_expert_kelly`` for every registered
EMA span -> ledger-layout parquet -> ``run_screen_h107.prepare_panel`` ->
``run_grid_screen``. Asserts the ledger-recovered turnover equals the
signal's true per-session turnover (the exactness claim of design §7).
"""

from __future__ import annotations

import shutil
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import run_screen_h107 as h107  # noqa: E402
import run_shadow_ledger_backfill as backfill  # noqa: E402

from skie_universe2.costs.futures_rt_v1 import FuturesRtV1CostModel  # noqa: E402
from skie_universe2.experts.vwap_ema_cross import (  # noqa: E402
    EMA_SPAN_GRID,
    VwapEmaCrossExpert,
    cme_session_of,
)
from skie_universe2.ledger.shadow_ledger import ShadowLedgerWriter  # noqa: E402
from skie_universe2.screening.grid_screen import run_grid_screen  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

_NY = ZoneInfo("America/New_York")


def _synthetic_valid(seed: int, n_sessions: int = 12) -> pl.DataFrame:
    rng = np.random.default_rng(seed)
    ts: list[datetime] = []
    day = datetime(2024, 3, 11, 18, 0, tzinfo=_NY)  # Monday-session start (Sun eve skipped)
    for _ in range(n_sessions):
        t = day
        while t < day + timedelta(hours=23):  # 18:00 -> 17:00 next day
            ts.append(t.astimezone(UTC))
            t += timedelta(minutes=5)
        day += timedelta(days=1)
    n = len(ts)
    close = 5000.0 * np.exp(np.cumsum(rng.normal(0, 6e-4, n)))
    return pl.DataFrame(
        {
            "ts_event": pl.Series(ts, dtype=pl.Datetime("us", "UTC")),
            "open": close,
            "high": close + 1.0,
            "low": close - 1.0,
            "close": close,
            "volume": rng.integers(10, 5000, n).astype(float),
            "unadjusted_close": close,
            "session_date": pl.Series([cme_session_of(t) for t in ts], dtype=pl.Date),
        }
    )


@pytest.fixture
def fake_root(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> ProjectPaths:
    paths = ProjectPaths(root=tmp_path)
    (tmp_path / "config").mkdir()
    shutil.copy(_ROOT / "config" / "instruments.yaml", tmp_path / "config" / "instruments.yaml")
    cost = FuturesRtV1CostModel.from_config(paths.config / "instruments.yaml")
    frames = {"ES": _synthetic_valid(1), "NQ": _synthetic_valid(2)}
    for sym, valid in frames.items():
        for span in EMA_SPAN_GRID:
            rows = backfill._rows_for_expert_kelly(
                expert=VwapEmaCrossExpert(span),
                kelly=1.0,
                symbol=sym,
                valid=valid,
                cost_model=cost,
            )
            out = (
                paths.data_processed
                / "shadow_ledger"
                / f"expert_id={h107.ledger_id(span)}"
                / f"asset={sym}"
                / "year=2024"
            )
            out.mkdir(parents=True)
            rows.write_parquet(out / "part-0000.parquet")
    monkeypatch.setattr(backfill, "_load_valid_bars", lambda _p, sym, _m: frames[sym])
    return paths


def test_prepare_panel_recovers_true_turnover(fake_root: ProjectPaths) -> None:
    panel = h107.prepare_panel(fake_root, "ES")
    assert panel.labels == h107.LABELS
    assert panel.canary["pass"]
    assert panel.gross.shape == (len(panel.dates), len(EMA_SPAN_GRID))
    # true turnover of the k1.0 primary signal, summed per session (accrual-bar keyed)
    valid = backfill._load_valid_bars(fake_root, "ES", None)
    sig = VwapEmaCrossExpert(9).signal(backfill._bar_window(valid))
    pos = sig.direction.astype(float)
    turn = np.abs(np.diff(np.concatenate([[0.0], pos])))[:-1]  # charged on the next bar
    sess = valid.get_column("session_date").to_list()[1:]
    truth = pl.DataFrame({"s": sess, "t": turn}).group_by("s").agg(pl.col("t").sum()).sort("s")
    k = h107.LABELS.index("ema9")
    got = dict(zip(panel.dates, panel.turnover[:, k], strict=True))
    for s, t in truth.iter_rows():
        assert got[s] == pytest.approx(t, abs=1e-6)
    # always-in 22h window: every session enters and exits at least once
    assert np.all(panel.turnover[:, k] >= 2.0 - 1e-9)


def test_grid_screen_runs_on_synthetic_ledger(fake_root: ProjectPaths) -> None:
    panels = [h107.prepare_panel(fake_root, s) for s in ("ES", "NQ")]
    res = run_grid_screen(
        panels,
        level=0.7400550140326007,
        seed=h107.SEED_SC,
        n_trials_gate=h107.N_TRIALS_GATE,
        register_sharpes=[0.1, -0.05, 0.02, 0.2],
        primary_label=h107.PRIMARY_LABEL,
        dwell_bars_per_session=float(h107.SESSION_BARS),
        n_bootstrap=100,
        pbo_splits=4,
    )
    assert [i["instrument"] for i in res["instruments"]] == ["ES", "NQ"]
    labels = {c["cell"] for c in res["instruments"][0]["cells"]}
    assert labels == set(h107.LABELS)
    nets = res["instruments"][0]["cells"][0]["net_descriptive"]
    assert {"ES/lifetime/central", "MES/free/pessimistic"} <= set(nets)
    assert not any(k.startswith("NQ") for k in nets)


def test_backfill_resume_guard(tmp_path: Path) -> None:
    writer = ShadowLedgerWriter(paths=ProjectPaths(root=tmp_path), update_manifest=False)
    exp = VwapEmaCrossExpert(9)
    assert backfill._already_backfilled(writer, exp, "ES") is False
    for k in backfill.KELLY_FRACTION_GRID[:2]:
        (writer.base_dir / f"expert_id=vwap_ema9_cross_k{k}@1.0.0" / "asset=ES").mkdir(parents=True)
    with pytest.raises(SystemExit):
        backfill._already_backfilled(writer, exp, "ES")
    for k in backfill.KELLY_FRACTION_GRID:
        (writer.base_dir / f"expert_id=vwap_ema9_cross_k{k}@1.0.0" / "asset=ES").mkdir(
            parents=True, exist_ok=True
        )
    assert backfill._already_backfilled(writer, exp, "ES") is True
    assert backfill._already_backfilled(writer, exp, "NQ") is False
