"""Render a canonical performance tearsheet for any shadow-ledger expert.

Loads the per-session gross/net log-return streams for one ``expert_id`` (any
member of the ADR-0003 shadow ledger) across one or more instruments, builds the
platform-style report via :mod:`skie_universe2.reporting.tearsheet`, and injects
it into ``docs/templates/tearsheet_template.html`` to produce a single
self-contained HTML file (data embedded inline).

The report is a DIAGNOSTIC EXHIBIT of ledger evidence; it certifies nothing and
is not a deployable strategy.

Net basis (``--net``):
- ``ledger``                  : one net series from the ledger ``ret_net`` (futures_rt_v1).
- ``ninjatrader:<plan>``      : two series (central + pessimistic slippage) from
                                config/cost_schedules/ninjatrader_v1.yaml for <plan>
                                in {free, monthly, lifetime}.

Optional ``--screen <rc_*_screen.json> --screen-cell <cell>`` adds the per-cell
ADR-0014 screen-verdict panel (RW p / DSR / PBO) for each instrument.

Example (H107 primary cell, as committed):
    uv run python scripts/build_tearsheet.py --hid H107 \
        --ledger-id vwap_ema9_cross_k1.0@1.0.0 --instruments ES,NQ \
        --title "H107 · VWAP × EMA(9)" \
        --subtitle "Session-anchored VWAP crossover · 5-min · Kelly 1.0 · 2015-2025" \
        --net ninjatrader:lifetime --screen reports/H107/rc_h107_1_screen.json \
        --screen-cell ema9 --disposition-from-screen --out reports/H107 --name H107_tearsheet
"""

from __future__ import annotations

import argparse
import html as _html
import json
import sys
from datetime import UTC, date, datetime
from pathlib import Path

import numpy as np
import polars as pl
import yaml

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

import run_shadow_ledger_backfill as backfill  # noqa: E402

from skie_universe2.costs.futures_rt_v1 import FuturesRtV1CostModel  # noqa: E402
from skie_universe2.reporting import tearsheet as ts  # noqa: E402
from skie_universe2.screening.grid_screen import per_unit_drag  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

TEMPLATE_RELPATH = "docs/templates/tearsheet_template.html"
NINJA_SCHEDULE_RELPATH = "config/cost_schedules/ninjatrader_v1.yaml"


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
        .agg(gross=pl.col("ret_gross").sum(), cost=(pl.col("ret_gross") - pl.col("ret_net")).sum())
        .sort("session_date")
        .collect()
    )


def _ninjatrader_variants(symbol: str, ref_price: float, plan: str):
    """(scenario -> per_unit_drag) for the E-mini parent, <plan>, central+pessimistic."""
    sched = yaml.safe_load((_ROOT / NINJA_SCHEDULE_RELPATH).read_text(encoding="utf-8"))
    out = {}
    for contract, spec in sched["contracts"].items():
        if spec["parent"] != symbol or contract != symbol:  # E-mini parent only
            continue
        comm = sched["commission"][plan][contract]
        for scen, slip in sched["slippage_ticks_per_side"].items():
            per_side = (
                float(comm)
                + float(spec["exch_nfa"])
                + float(spec["clearing"])
                + float(slip[contract]) * float(spec["tick_value"])
            )
            out[scen] = per_unit_drag(
                per_side, reference_price=ref_price, multiplier=float(spec["multiplier"])
            )
    return out


def _screen_cell(screen_path: Path, instrument: str, cell: str) -> dict | None:
    blob = json.loads(screen_path.read_text(encoding="utf-8"))
    level = blob.get("screen_level")
    for inst in blob["instruments"]:
        if inst["instrument"] != instrument:
            continue
        for c in inst["cells"]:
            if c["cell"] == cell:
                sd = c["s_d"]
                # Construction-dependent s_d fields may be absent on a degenerate
                # cell (grid_screen._dsr_block omits dsr_bound); read defensively
                # so a degenerate cell renders instead of crashing (code-reviewer CR-1-1).
                dsr = sd.get("dsr")
                dsr_b, pbo, pbo_b = sd.get("dsr_bound"), sd.get("pbo"), sd.get("pbo_bound")
                pbo_pass = pbo is not None and pbo_b is not None and pbo <= pbo_b
                gates = [
                    {
                        "lab": "RW adj. p-value",
                        "val": f"{c['rw_adj_pvalue']:.3f}",
                        "sub": f"vs level {level:.3f}",
                        "pass": bool(c["s_c_pass"]),
                        "tag": "S-c pass" if c["s_c_pass"] else "S-c fail",
                    },
                    {
                        "lab": "Deflated Sharpe",
                        "val": f"{dsr:.1e}" if dsr is not None else "—",
                        "sub": f"needs ≥ {dsr_b:.3f}"
                        if dsr_b is not None
                        else "degenerate (no bound)",
                        "pass": bool(sd.get("dsr_pass", False)),
                        "tag": "S-d pass" if sd.get("dsr_pass") else "S-d fail",
                    },
                    {
                        "lab": "PBO (overfit prob.)",
                        "val": f"{pbo:.3f}" if pbo is not None else "—",
                        "sub": f"needs ≤ {pbo_b:.3f}" if pbo_b is not None else "—",
                        "pass": pbo_pass,
                        "tag": "pass" if pbo_pass else "fail",
                    },
                    {
                        "lab": "Screen result",
                        "val": "✓" if c["screen_pass"] else "✗",
                        "sub": "admitted to pool" if c["screen_pass"] else "not admitted",
                        "pass": bool(c["screen_pass"]),
                        "tag": "pool" if c["screen_pass"] else "archive",
                    },
                ]
                dsr_txt = f"{dsr:.1e}" if dsr is not None else "degenerate"
                callout = (
                    f'Gross Sharpe ≈ <b class="mono">{c["sharpe"]:.4f}</b>/session; '
                    f"<b>Deflated Sharpe ≈ {dsr_txt}</b> — the edge sits below the "
                    f"selection-corrected benchmark, so it does not survive multiplicity."
                )
                return {
                    "gates": gates,
                    "note": f"ADR-0014 singleton screen, cell {cell}, enacted level {level:.4f}.",
                    "callout": callout,
                }
    return None


def _instrument_inputs(
    paths: ProjectPaths,
    *,
    expert_id: str,
    symbol: str,
    net: str,
    screen_path: Path | None,
    screen_cell: str | None,
) -> ts.InstrumentInputs:
    df = _ledger_session_sums(paths, expert_id, symbol)
    dates = [str(d) for d in df.get_column("session_date").to_list()]
    gross = df.get_column("gross").to_numpy()
    cost = df.get_column("cost").to_numpy()
    # Match grid_screen's finite contract: a ruin (-inf) row must hard-fail, not
    # become a silent null in the exhibit (code-reviewer CR-1-6).
    if not (np.isfinite(gross).all() and np.isfinite(cost).all()):
        bad = [
            d
            for d, g, c in zip(dates, gross, cost, strict=True)
            if not (np.isfinite(g) and np.isfinite(c))
        ]
        raise SystemExit(
            f"non-finite ledger returns for {expert_id}/{symbol} at "
            f"{bad[:5]} ({len(bad)} session(s)) — refusing to emit a corrupt tearsheet"
        )

    valid = backfill._load_valid_bars(paths, symbol, None)
    ref_price = float(np.median(valid.get_column("unadjusted_close").to_numpy()))
    model = FuturesRtV1CostModel.from_config(paths.config / "instruments.yaml")
    per_unit_ledger = model.switch_drag_notional(symbol, reference_price=ref_price) / 2.0
    turnover = cost / per_unit_ledger

    series = [ts.SeriesSpec("gross", "Gross", gross)]
    if net == "ledger":
        series.append(
            ts.SeriesSpec("net_ledger", "Net (futures_rt_v1)", gross - cost, is_primary_net=True)
        )
    elif net.startswith("ninjatrader:"):
        plan = net.split(":", 1)[1]
        v = _ninjatrader_variants(symbol, ref_price, plan)
        series.append(
            ts.SeriesSpec(
                "net_central", "Net · central", gross - turnover * v["central"], is_primary_net=True
            )
        )
        series.append(
            ts.SeriesSpec(
                "net_pess", "Net · pessimistic", gross - turnover * v["pessimistic"], dash=True
            )
        )
    else:
        raise SystemExit(f"--net must be 'ledger' or 'ninjatrader:<plan>', got {net!r}")

    screen = _screen_cell(screen_path, symbol, screen_cell) if screen_path and screen_cell else None
    return ts.InstrumentInputs(
        symbol=symbol, dates=dates, series=series, turnover=turnover, screen=screen
    )


def main() -> int:
    p = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    p.add_argument("--hid", required=True)
    p.add_argument(
        "--ledger-id",
        required=True,
        help="shadow-ledger expert_id, e.g. vwap_ema9_cross_k1.0@1.0.0",
    )
    p.add_argument("--instruments", default="ES,NQ")
    p.add_argument("--title", required=True)
    p.add_argument("--subtitle", default="")
    p.add_argument("--net", default="ledger", help="ledger | ninjatrader:<free|monthly|lifetime>")
    p.add_argument("--screen", default=None, help="path to rc_*_screen.json")
    p.add_argument("--screen-cell", default=None)
    p.add_argument("--disposition-from-screen", action="store_true")
    p.add_argument("--seed", type=int, default=20261122)
    p.add_argument("--n-mc", type=int, default=10000)
    p.add_argument("--out", default="reports")
    p.add_argument("--name", default=None, help="output stem (default: <hid>_tearsheet)")
    args = p.parse_args()

    paths = ProjectPaths.discover()
    instruments = tuple(s.strip() for s in args.instruments.split(","))
    screen_path = (paths.root / args.screen) if args.screen else None

    cost_note = {"ledger": "net of futures_rt_v1 costs"}.get(
        args.net, f"net of NinjaTrader costs ({args.net.split(':')[-1]} plan, central slippage)"
    )
    disposition, level = None, None
    if args.screen and screen_path.is_file():
        blob = json.loads(screen_path.read_text(encoding="utf-8"))
        level = blob.get("screen_level")
        if args.disposition_from_screen:
            disposition = blob.get("disposition")

    inst_inputs = [
        _instrument_inputs(
            paths,
            expert_id=args.ledger_id,
            symbol=s,
            net=args.net,
            screen_path=screen_path,
            screen_cell=args.screen_cell,
        )
        for s in instruments
    ]
    report = ts.build_report(
        hid=args.hid,
        title=args.title,
        subtitle=args.subtitle,
        cost_note=cost_note,
        instruments=inst_inputs,
        disposition=disposition,
        enacted_level=level,
        generated=date.today().isoformat(),
        note="Per-session compounded log-wealth from the audited shadow ledger.",
        seed=args.seed,
        n_mc=args.n_mc,
    )
    data = json.dumps(ts.round_floats(report))

    template = (paths.root / TEMPLATE_RELPATH).read_text(encoding="utf-8")
    if "__DATA__" not in template or "__TITLE__" not in template:
        raise SystemExit(f"template {TEMPLATE_RELPATH} missing __TITLE__/__DATA__ placeholders")
    if "</script>" in data:
        raise SystemExit("report JSON contains '</script>' — refusing to inline")
    # Substitute data first, then the HTML-escaped title, so neither a markup
    # title nor a literal sentinel in the title can break out (code-reviewer CR-1-5).
    html_doc = template.replace("__DATA__", data).replace("__TITLE__", _html.escape(args.title))

    out_dir = paths.root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.name or f"{args.hid}_tearsheet"
    out_html = out_dir / f"{stem}.html"
    out_json = out_dir / f"{stem}.json"
    out_html.write_text(html_doc, encoding="utf-8")
    out_json.write_text(json.dumps(ts.round_floats(report), indent=0), encoding="utf-8")
    print(
        f"[{args.hid}] wrote {out_html.relative_to(paths.root).as_posix()} "
        f"({out_html.stat().st_size} bytes) + {out_json.name} "
        f"@ {datetime.now(tz=UTC).isoformat(timespec='seconds')}"
    )
    for s in instruments:
        m = report["instruments"][s]["metrics"]
        pk = report["primary_net_key"]
        print(
            f"  {s}: net totRet={m[pk]['total_return_pct']:.1f}%  "
            f"Sharpe={m[pk]['sharpe_ann']:.3f}  MaxDD={m[pk]['max_drawdown_pct']:.1f}%"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
