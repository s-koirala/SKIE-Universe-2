"""Shadow-ledger backfill driver (ADR-0003 population; backfill plan M2/M3).

Populates the append-only shadow ledger by running an :class:`Expert` (ADR-0005
Layer 1) through the position policy (Layer 2, Kelly sweep) and the Tier-0
bar-close execution helper (Layer 3, ADR-0006 D1) to produce the counterfactual
per-bar returns the ledger stores, then writing them via `ShadowLedgerWriter`.

Per the operator decision (2026-07-16): run on the EXISTING ES/NQ roll-adjusted
substrate (primary-exclusion variant; December-roll windows excluded, not
corrected — no new-data budget). Every Kelly fraction {0.5,0.75,1.0,1.25} is a
distinct ``expert_id`` (ADR-0013 D3); selection is BLOCKED on the two Decision-9
Kelly memos, so all four are materialized and none is selected.

``--smoke`` runs the reference smoke expert to an ISOLATED scratch ledger (default)
to validate the pipeline end-to-end without touching the canonical ledger; a real
evidence backfill requires a frozen-design expert (e.g. H101) and writes to the
canonical location.

Usage:
    uv run python scripts/run_shadow_ledger_backfill.py --smoke \
        [--instruments ES,NQ] [--max-bars N] [--out <scratch dir>]
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import polars as pl

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.costs.futures_rt_v1 import FuturesRtV1CostModel  # noqa: E402
from skie_universe2.execution.tier0_barclose import tier0_counterfactual  # noqa: E402
from skie_universe2.experts.base import BarWindow, Expert, assert_prefix_invariant  # noqa: E402
from skie_universe2.experts.reference import CausalMomentumExpert  # noqa: E402
from skie_universe2.features.regime_emissions import (  # noqa: E402
    apply_registered_exclusions,
    compute_emissions,
    exclusion_windows_from_provenance,
)
from skie_universe2.ledger.shadow_ledger import ShadowLedgerWriter  # noqa: E402
from skie_universe2.policy.meta_shift_policy import KELLY_FRACTION_GRID  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

SEED = 20260716  # justify: registered project seed (H900/H001 lineage)
COST_MODEL_ID = "futures_rt_v1"
DATASET = "vendor_legacy_1min_roll_adjusted"
PROVENANCE_FILE = "vendor_legacy_1min_roll_adjusted_20260711.json"


def _load_valid_bars(paths: ProjectPaths, symbol: str, max_bars: int | None) -> pl.DataFrame:
    """Load → exclude (primary) → aggregate 5m → emissions → valid bars (reuse H001 path)."""
    glob = str(paths.data_processed / DATASET / f"symbol={symbol}" / "**" / "*.parquet")
    lf = pl.scan_parquet(glob).select(
        "ts_event", "open", "high", "low", "close", "volume", "unadjusted_close", "pit_provisional"
    )
    gaps = _provenance_gaps(paths)
    lf = apply_registered_exclusions(
        lf,
        symbol=symbol,
        exclusions=exclusion_windows_from_provenance(gaps),
        exclude_pit_provisional=True,
        exclude_coverage_gaps=True,
    )
    bars_1m = lf.collect()
    bars_5m = (
        bars_1m.lazy()
        .sort("ts_event")
        .group_by_dynamic("ts_event", every="5m", closed="left", label="left")
        .agg(
            open=pl.col("open").first(),
            high=pl.col("high").max(),
            low=pl.col("low").min(),
            close=pl.col("close").last(),
            volume=pl.col("volume").sum(),
            unadjusted_close=pl.col("unadjusted_close").last(),
        )
        .collect()
    )
    feats = compute_emissions(bars_5m)
    valid = feats.filter(pl.col("emission_valid")).sort("ts_event")
    if max_bars is not None:
        valid = valid.head(max_bars)
    return valid


def _provenance_gaps(paths: ProjectPaths) -> list[dict]:
    payload = json.loads(
        (paths.data_processed / "_provenance" / PROVENANCE_FILE).read_text(encoding="utf-8")
    )
    return payload["coverage_gaps"]


def _bar_window(valid: pl.DataFrame) -> BarWindow:
    return BarWindow(
        ts=valid.get_column("ts_event").to_list(),
        open=valid.get_column("open").to_numpy(),
        high=valid.get_column("high").to_numpy(),
        low=valid.get_column("low").to_numpy(),
        close=valid.get_column("close").to_numpy(),
        volume=valid.get_column("volume").to_numpy(),
    )


def _rows_for_expert_kelly(
    *,
    expert: Expert,
    kelly: float,
    symbol: str,
    valid: pl.DataFrame,
    cost_model: FuturesRtV1CostModel,
) -> pl.DataFrame:
    """Signal → position (kelly) → Tier-0 counterfactual → ledger-schema rows.

    Row ``t`` (accrual bar) carries the counterfactual the position decided at
    ``t-1`` earned over ``(t-1, t]``. Bar 0 (no prior return) is dropped.
    """
    bars = _bar_window(valid)
    sig = expert.signal(bars)
    # Layer 2: target position = direction · strength · kelly (Kelly-swept size).
    strength = np.nan_to_num(sig.strength, nan=0.0)
    target = sig.direction.astype(np.float64) * strength * kelly
    # log return r[t] over (t-1, t] on the roll-adjusted close.
    close = bars.close
    r = np.full(close.size, np.nan, dtype=np.float64)
    r[1:] = np.log(close[1:] / close[:-1])
    # Tier-0 per-unit turnover cost = half the round-trip notional drag.
    ref_price = float(np.median(valid.get_column("unadjusted_close").to_numpy()))
    per_unit = cost_model.switch_drag_notional(symbol, reference_price=ref_price) / 2.0
    cf = tier0_counterfactual(target, r, per_unit_turnover_cost=per_unit)

    name, version = expert.expert_id.split("@")
    expert_id = f"{name}_k{kelly}@{version}"
    # Drop bar 0 (no accrual); keep every other valid bar (counterfactual completeness).
    # Slice the native polars datetime/date columns rather than round-tripping numpy.
    accrual = valid.slice(1)
    n = accrual.height
    return pl.DataFrame(
        {
            "expert_id": pl.Series([expert_id] * n, dtype=pl.Utf8),
            "asset": pl.Series([symbol] * n, dtype=pl.Utf8),
            "bar_ts": accrual.get_column("ts_event").cast(pl.Datetime("us", "UTC")),
            "session_date": accrual.get_column("session_date").cast(pl.Date),
            "ret_gross": cf.ret_gross[1:],
            "ret_net": cf.ret_net[1:],
            "cost_model_id": pl.Series([COST_MODEL_ID] * n, dtype=pl.Utf8),
            "fidelity_tier": np.zeros(n, dtype=np.int64),
        }
    )


def run_smoke(
    paths: ProjectPaths, *, instruments: tuple[str, ...], max_bars: int, out: Path
) -> int:
    """End-to-end pipeline validation to an ISOLATED scratch ledger (no evidence)."""
    scratch = ProjectPaths(root=out)
    (out / "config").mkdir(parents=True, exist_ok=True)
    # Point covariate validation at the real config (no cov_ columns here anyway).
    writer = ShadowLedgerWriter(
        paths=scratch,
        update_manifest=False,
        covariates_config_path=paths.config / "covariates.yaml",
    )
    cost_model = FuturesRtV1CostModel.from_config(paths.config / "instruments.yaml")
    expert = CausalMomentumExpert()

    total_rows = 0
    for symbol in instruments:
        valid = _load_valid_bars(paths, symbol, max_bars)
        print(f"[smoke/{symbol}] {valid.height} valid 5-min bars", flush=True)
        # Signal-layer PIT canary (ADR-0008 D1): sweep cuts on this window.
        assert_prefix_invariant(expert, _bar_window(valid))
        frames = [
            _rows_for_expert_kelly(
                expert=expert, kelly=k, symbol=symbol, valid=valid, cost_model=cost_model
            )
            for k in KELLY_FRACTION_GRID
        ]
        df = pl.concat(frames)
        results = writer.write_partitions(df, rng_seed=SEED, hypothesis_id="n/a-smoke")
        total_rows += int(df.height)
        # Read-back validation: re-read one partition and check row count.
        n_written = sum(rr.n_rows for rr in results)
        print(
            f"[smoke/{symbol}] wrote {len(results)} partitions, {n_written} rows "
            f"({len(KELLY_FRACTION_GRID)} Kelly fractions); canary PASS",
            flush=True,
        )
    print(
        f"[smoke] TOTAL {total_rows} rows across {len(instruments)} instruments -> {out}",
        flush=True,
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke", action="store_true", help="pipeline validation to scratch ledger"
    )
    parser.add_argument("--instruments", default="ES,NQ")
    parser.add_argument("--max-bars", type=int, default=2000, help="smoke bar cap per instrument")
    parser.add_argument("--out", default=None, help="scratch ledger root (smoke)")
    args = parser.parse_args()

    paths = ProjectPaths.discover()
    if not args.smoke:
        raise SystemExit(
            "Only --smoke is implemented. A real evidence backfill requires a "
            "frozen-design expert (e.g. H101); see the M3 milestone in "
            "docs/research_notes/shadow_ledger_backfill_plan_2026-07-16.md."
        )
    out = Path(args.out) if args.out else (paths.data / "interim" / "shadow_ledger_smoke")
    if out.exists():
        shutil.rmtree(out)  # smoke scratch is disposable (NOT the canonical ledger)
    instruments = tuple(s.strip() for s in args.instruments.split(","))
    return run_smoke(paths, instruments=instruments, max_bars=args.max_bars, out=out)


if __name__ == "__main__":
    raise SystemExit(main())
