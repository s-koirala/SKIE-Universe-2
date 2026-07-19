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
from skie_universe2.experts.orb_first_hour import OrbFirstHourExpert  # noqa: E402
from skie_universe2.experts.overnight_drift import OvernightSessionDriftExpert  # noqa: E402
from skie_universe2.experts.reference import CausalMomentumExpert  # noqa: E402
from skie_universe2.experts.vr_range_reversal import VrRangeReversalExpert  # noqa: E402
from skie_universe2.features.regime_emissions import (  # noqa: E402
    apply_registered_exclusions,
    compute_emissions,
    exclusion_windows_from_provenance,
)
from skie_universe2.ledger.shadow_ledger import ShadowLedgerWriter  # noqa: E402
from skie_universe2.policy.kelly_sweep import KELLY_FRACTION_GRID  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

SEED = 20260716  # justify: registered project seed (H900/H001 lineage)
COST_MODEL_ID = "futures_rt_v1"
DATASET = "vendor_legacy_1min_roll_adjusted"
PROVENANCE_FILE = "vendor_legacy_1min_roll_adjusted_20260711.json"
# Bounded canary sample: enough bars to span several RTH sessions (the causality
# unit), not the full series (the cut-sweep would re-signal it ~16x).
_CANARY_SAMPLE_BARS = 5000  # justify: multi-session causality sample, not an analysis parameter


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


def _make_expert(name: str) -> Expert:
    if name == "reference":
        return CausalMomentumExpert()
    if name == "h101":
        return OrbFirstHourExpert()
    if name == "h105":
        return OvernightSessionDriftExpert()
    if name == "h106":
        return VrRangeReversalExpert()
    raise ValueError(f"unknown expert {name!r}; choose reference|h101|h105|h106")


def run_backfill(
    paths: ProjectPaths,
    *,
    expert: Expert,
    hypothesis_id: str,
    instruments: tuple[str, ...],
    max_bars: int | None,
    writer: ShadowLedgerWriter,
    label: str,
) -> int:
    """Population run: expert × {instruments} × 4 Kelly fractions → ledger partitions."""
    cost_model = FuturesRtV1CostModel.from_config(paths.config / "instruments.yaml")
    total_rows = 0
    for symbol in instruments:
        valid = _load_valid_bars(paths, symbol, max_bars)
        print(f"[{label}/{symbol}] {valid.height} valid 5-min bars", flush=True)
        # Signal-layer PIT canary (ADR-0008 D1): cut-sweep before any write. Causality
        # is a property of the rule, so a bounded multi-session sample suffices (the
        # full-span cut-sweep would re-signal the whole series ~16x).
        canary_bars = _bar_window(valid.head(_CANARY_SAMPLE_BARS))
        assert_prefix_invariant(expert, canary_bars)
        df = pl.concat(
            [
                _rows_for_expert_kelly(
                    expert=expert, kelly=k, symbol=symbol, valid=valid, cost_model=cost_model
                )
                for k in KELLY_FRACTION_GRID
            ]
        )
        results = writer.write_partitions(df, rng_seed=SEED, hypothesis_id=hypothesis_id)
        total_rows += int(df.height)
        print(
            f"[{label}/{symbol}] wrote {len(results)} partitions, "
            f"{sum(rr.n_rows for rr in results)} rows "
            f"({len(KELLY_FRACTION_GRID)} Kelly fractions); canary PASS",
            flush=True,
        )
    print(f"[{label}] TOTAL {total_rows} rows across {len(instruments)} instruments", flush=True)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke", action="store_true", help="validate to a scratch ledger (no evidence)"
    )
    parser.add_argument("--expert", default="h101", choices=["reference", "h101", "h105", "h106"])
    parser.add_argument("--hypothesis-id", default=None, help="ledger hypothesis_id")
    parser.add_argument("--instruments", default="ES,NQ")
    parser.add_argument("--max-bars", type=int, default=None, help="bar cap (dev/smoke)")
    parser.add_argument("--out", default=None, help="scratch ledger root (smoke)")
    args = parser.parse_args()

    paths = ProjectPaths.discover()
    expert = _make_expert(args.expert)
    instruments = tuple(s.strip() for s in args.instruments.split(","))

    if args.smoke:
        out = Path(args.out) if args.out else (paths.data / "interim" / "shadow_ledger_smoke")
        if out.exists():
            shutil.rmtree(out)  # scratch is disposable (NOT the canonical ledger)
        (out / "config").mkdir(parents=True, exist_ok=True)
        writer = ShadowLedgerWriter(
            paths=ProjectPaths(root=out),
            update_manifest=False,
            covariates_config_path=paths.config / "covariates.yaml",
        )
        return run_backfill(
            paths,
            expert=expert,
            hypothesis_id="n/a-smoke",
            instruments=instruments,
            max_bars=args.max_bars if args.max_bars is not None else 2000,
            writer=writer,
            label="smoke",
        )

    # Production: write to the CANONICAL append-only ledger — requires a
    # frozen-design (evidence-eligible) expert; the reference expert is smoke-only.
    if args.expert == "reference":
        raise SystemExit(
            "The reference expert produces no evidence; use --smoke, or --expert h101 "
            "for a canonical evidence backfill (frozen design H101)."
        )
    hyp = args.hypothesis_id or args.expert.upper()
    writer = ShadowLedgerWriter(paths=paths)  # canonical data/processed/shadow_ledger/
    return run_backfill(
        paths,
        expert=expert,
        hypothesis_id=hyp,
        instruments=instruments,
        max_bars=args.max_bars,
        writer=writer,
        label=hyp,
    )


if __name__ == "__main__":
    raise SystemExit(main())
