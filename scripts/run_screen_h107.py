"""RC-H107-1 — ADR-0014 SCREEN of the session-VWAP x EMA(N) crossover grid.

Executes the FROZEN H107 protocol
(research/01_hypothesis_register/H107/design.md §5) on the canonical k1.0
shadow ledger for EVERY registered EMA-span grid point
(``expert_id=vwap_ema{N}_cross_k1.0@1.0.0``, N in EMA_SPAN_GRID). The
statistical stages are :mod:`skie_universe2.screening.grid_screen` (the
parameter-grid counterpart of the packaged spine; same gate conjunction).
This script supplies only the H107-specific pieces:

- the per-session gross panel (T sessions x K spans, inner-joined) and the
  per-session turnover panel recovered exactly from the ledger
  (turnover = (gross - net) / per-unit futures_rt_v1 drag, the backfill's
  own reference-price construction),
- the descriptive NinjaTrader net columns (config/cost_schedules/
  ninjatrader_v1.yaml: E-mini + micro x plan x slippage scenario),
- the S-a prefix-invariance canary for every grid point on the substrate,
- the frozen constants (seed, n_trials_gate, dispersion families).

Prerequisite: ``uv run python scripts/run_shadow_ledger_backfill.py --expert h107``.

Usage:
    uv run python scripts/run_screen_h107.py [--out reports/H107]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from pathlib import Path

import numpy as np
import polars as pl
import yaml

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

import run_shadow_ledger_backfill as backfill  # noqa: E402

from skie_universe2.costs.futures_rt_v1 import FuturesRtV1CostModel  # noqa: E402
from skie_universe2.experts.base import assert_prefix_invariant  # noqa: E402
from skie_universe2.experts.vwap_ema_cross import (  # noqa: E402
    EMA_SPAN_GRID,
    PRIMARY_EMA_SPAN,
    VwapEmaCrossExpert,
)
from skie_universe2.screening import screen_spine as spine  # noqa: E402
from skie_universe2.screening.grid_screen import (  # noqa: E402
    CostVariant,
    GridPanel,
    per_unit_drag,
    run_grid_screen,
)
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

SCAN_ID = "RC-H107-1"
HID = "H107"
SEED_SC = 20261122  # justify: registered scan seed (design §5; freeze date)
# justify: design §8 — cumulative register trial count at freeze (73) + this
# scan's 7 spans x 2 instruments (14) = 87; frozen, never recomputed at run.
N_TRIALS_GATE = 87
# justify: design §4 — held decision labels per session inside the window
# (18:00 ET .. 15:50 ET labels = 21 h 55 min of 5-min bars; audit-measured).
SESSION_BARS = 263
DISPERSION_FAMILIES = ("rc-h101-2", "rc-h103-2", "rc-h105-1", "rc-h106-1")
DESIGN_RELPATH = "research/01_hypothesis_register/H107/design.md"
COST_SCHEDULE_RELPATH = "config/cost_schedules/ninjatrader_v1.yaml"
DATASET = backfill.DATASET
_CANARY_TAIL_BARS = 5_000  # justify: bounded multi-session causality sample (backfill rule)
LABELS = tuple(f"ema{n}" for n in EMA_SPAN_GRID)
PRIMARY_LABEL = f"ema{PRIMARY_EMA_SPAN}"


def ledger_id(span: int) -> str:
    return f"vwap_ema{span}_cross_k1.0@1.0.0"


def _ledger_session_sums(paths: ProjectPaths, expert_id: str, symbol: str) -> pl.DataFrame:
    glob = str(
        paths.data_processed
        / "shadow_ledger"
        / f"expert_id={expert_id}"
        / f"asset={symbol}"
        / "**"
        / "part-0000.parquet"
    )
    return (
        pl.scan_parquet(glob)
        .select("session_date", "ret_gross", "ret_net")
        .group_by("session_date")
        .agg(
            gross=pl.col("ret_gross").sum(),
            cost=(pl.col("ret_gross") - pl.col("ret_net")).sum(),
        )
        .sort("session_date")
        .collect()
    )


def _cost_variants(symbol: str, ref_price: float) -> tuple[CostVariant, ...]:
    sched = yaml.safe_load((_ROOT / COST_SCHEDULE_RELPATH).read_text(encoding="utf-8"))
    out: list[CostVariant] = []
    for contract, spec in sched["contracts"].items():
        if spec["parent"] != symbol:
            continue
        for plan, comm in sched["commission"].items():
            for scen, slip in sched["slippage_ticks_per_side"].items():
                per_side = (
                    float(comm[contract])
                    + float(spec["exch_nfa"])
                    + float(spec["clearing"])
                    + float(slip[contract]) * float(spec["tick_value"])
                )
                out.append(
                    CostVariant(
                        label=f"{contract}/{plan}/{scen}",
                        per_unit_drag=per_unit_drag(
                            per_side,
                            reference_price=ref_price,
                            multiplier=float(spec["multiplier"]),
                        ),
                    )
                )
    return tuple(out)


def prepare_panel(paths: ProjectPaths, symbol: str) -> GridPanel:
    valid = backfill._load_valid_bars(paths, symbol, None)
    ref_price = float(np.median(valid.get_column("unadjusted_close").to_numpy()))
    model = FuturesRtV1CostModel.from_config(paths.config / "instruments.yaml")
    per_unit_ledger = model.switch_drag_notional(symbol, reference_price=ref_price) / 2.0

    # S-a: prefix-invariance canary for every grid point on the evaluation substrate.
    window = backfill._bar_window(valid.tail(_CANARY_TAIL_BARS))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for span in EMA_SPAN_GRID:
            assert_prefix_invariant(VwapEmaCrossExpert(span), window)
    canary = {"instrument": symbol, "n_bars": window.close.size, "spans": list(EMA_SPAN_GRID)}
    canary["pass"] = True

    joined: pl.DataFrame | None = None
    for span, lab in zip(EMA_SPAN_GRID, LABELS, strict=True):
        df = _ledger_session_sums(paths, ledger_id(span), symbol).rename(
            {"gross": f"g_{lab}", "cost": f"c_{lab}"}
        )
        joined = df if joined is None else joined.join(df, on="session_date", how="inner")
    assert joined is not None
    joined = joined.sort("session_date")
    gross = np.column_stack([joined.get_column(f"g_{lab}").to_numpy() for lab in LABELS])
    cost = np.column_stack([joined.get_column(f"c_{lab}").to_numpy() for lab in LABELS])
    finite = np.isfinite(gross).all(axis=1)  # ruin (-inf) rows would surface here
    return GridPanel(
        instrument=symbol,
        dates=joined.get_column("session_date").to_list(),
        labels=LABELS,
        gross=gross,
        turnover=cost / per_unit_ledger,
        canary=canary,
        cost_variants=_cost_variants(symbol, ref_price),
        extras={
            "reference_price_median_unadjusted": ref_price,
            "per_unit_drag_futures_rt_v1": per_unit_ledger,
            "n_sessions_non_finite_gross": int((~finite).sum()),
        },
    )


def _checksums(paths: ProjectPaths) -> dict[str, str]:
    manifest = json.loads((paths.data / "_manifest.json").read_text(encoding="utf-8"))
    files = manifest["files"]
    out = {k: e["sha256"] for k, e in files.items() if DATASET in k}
    if not out:
        raise RuntimeError("no substrate checksums found in data/_manifest.json")
    for span in EMA_SPAN_GRID:
        eid = ledger_id(span)
        parts = {k: e["sha256"] for k, e in files.items() if f"expert_id={eid}" in k}
        if not parts:
            raise RuntimeError(f"no ledger partitions for {eid} in data/_manifest.json")
        out[f"shadow_ledger:expert_id={eid} ({len(parts)} parts)"] = hashlib.sha256(
            "".join(f"{k}:{v}\n" for k, v in sorted(parts.items())).encode()
        ).hexdigest()
    for rel in (DESIGN_RELPATH, "config/multipletest_family.yaml", COST_SCHEDULE_RELPATH):
        out[rel] = hashlib.sha256((paths.root / rel).read_bytes()).hexdigest()
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/H107")
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    out_dir = paths.root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    level = spine.screen_level(paths)
    reg_sharpes = spine.register_trial_sharpes(paths, DISPERSION_FAMILIES)  # fail-fast
    checksums = _checksums(paths)
    design_sha = checksums[DESIGN_RELPATH]
    log = reproducibility.capture(
        phase=f"{SCAN_ID.lower()}-screen",
        hypothesis_id=HID,
        rng_seed=SEED_SC,
        dataset_checksums=checksums,
        config_resolved_sha256=design_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (design SHA {design_sha[:12]}...)", flush=True)

    panels = [prepare_panel(paths, s) for s in ("ES", "NQ")]
    result = run_grid_screen(
        panels,
        level=level,
        seed=SEED_SC,
        n_trials_gate=N_TRIALS_GATE,
        register_sharpes=reg_sharpes,
        primary_label=PRIMARY_LABEL,
        dwell_bars_per_session=float(SESSION_BARS),
    )
    result.update(
        {
            "scan": SCAN_ID,
            "hypothesis_id": HID,
            "s_e_emission": spine.s_e_latency(paths),
            "ledger_expert_ids": [ledger_id(n) for n in EMA_SPAN_GRID],
            "cost_schedule": COST_SCHEDULE_RELPATH,
            "repro_log": log_path.name,
            "design_md_sha256": design_sha,
        }
    )
    out_path = out_dir / "rc_h107_1_screen.json"
    out_path.write_text(
        json.dumps(
            spine.json_sanitize(result), indent=2, sort_keys=True, default=str, allow_nan=False
        ),
        encoding="utf-8",
    )
    print(f"[{SCAN_ID}] disposition: {result['disposition']}", flush=True)
    for inst in result["instruments"]:
        for c in inst["cells"]:
            sd = c["s_d"]
            net = c["net_descriptive"]
            nt = net.get(f"{inst['instrument']}/lifetime/central", float("nan"))
            print(
                f"  {inst['instrument']}/{c['cell']}: mean={c['mean_gross']:.3e} "
                f"turnover/sess={c['mean_turnover_per_session']:.2f} "
                f"net(lifetime,central)={nt:.3e} S-c p={c['rw_adj_pvalue']:.3f} "
                f"DSR={sd.get('dsr', float('nan')):.3f} PBO={sd['pbo']:.3f} "
                f"PASS={c['screen_pass']}",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
