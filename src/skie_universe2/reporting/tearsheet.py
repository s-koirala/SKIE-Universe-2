"""Canonical performance-tearsheet builder (hypothesis-agnostic).

Turns per-session **log-return** streams into the JSON a platform-style
backtest report renders: equity, drawdown, Monte Carlo cone + terminal
distribution, monthly-return grid, per-session histogram and a metrics table,
for one or more named return series (e.g. ``gross`` and net-of-cost variants)
across one or more instruments.

The module is pure analytics: it does NOT touch the ledger or the filesystem
(``scripts/build_tearsheet.py`` loads the shadow ledger and injects the output
into ``docs/templates/tearsheet_template.html``). All returns are per-session
log-returns at a fixed Kelly fraction, so equity compounds as
``exp(cumsum(r))`` — matching the project's geometric (log-wealth) objective.
The output is a DIAGNOSTIC exhibit; it certifies nothing.

Metric conventions (annualized by the realized sessions-per-year, not a
hard-coded 252):

- Sharpe   = mean(r) / std(r, ddof=1) * sqrt(S/yr)
- Sortino  = mean(r) / sqrt(mean(min(r,0)^2)) * sqrt(S/yr)   [Sortino & Price 1994]
- CAGR     = equity[-1] ** (1/years) - 1
- Drawdown = equity / cummax([1.0] + equity) - 1   (peak references 1.0 inception)
- Calmar   = CAGR / |MaxDD|
- Profit factor = sum(positive simple returns) / |sum(negative simple returns)|
  on simple per-session P&L ``expm1(r)``, the platform (gross-profit/gross-loss)
  convention — not a sum of logs.

Monte Carlo is an iid bootstrap (resample-with-replacement) of the per-session
returns — the classic trade-shuffle MC of MultiCharts/TradingView — giving a
percentile cone of compounded wealth, the terminal-wealth distribution, and the
distribution of worst drawdown. It is a path-reshuffle exhibit, not a
forward-return forecast: **iid resampling discards serial dependence, so under
positive autocorrelation or volatility clustering the cone and the max-drawdown
distribution understate realized risk.**
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np

__all__ = ["SeriesSpec", "InstrumentInputs", "build_report", "round_floats"]

# justify: Monte-Carlo and chart-resolution parameters for a DIAGNOSTIC exhibit
# (certifies nothing; no inference threshold). 10k resamples stabilize the
# percentile cone; 160/500 are chart downsample point-counts; 60/40 are display
# histogram bin-counts. Seed mirrors run_screen_h107.SEED_SC (freeze-date form).
_N_MC = 10000
_CONE_POINTS = 160
_HIST_BINS = 60
_MC_HIST_BINS = 40
_DOWNSAMPLE_POINTS = 500
_DEFAULT_SEED = 20261122

# Fixed, theme-tokened colour slots the template defines (--s0 … --s4).
_COLOR_SLOTS = ("s0", "s1", "s2", "s3", "s4")


@dataclass
class SeriesSpec:
    """Display + data for one named per-session log-return stream."""

    key: str  # machine key, e.g. "gross", "net_central"
    label: str  # display label
    values: np.ndarray  # per-session log-returns (1-D)
    dash: bool = False  # dashed line in the equity chart
    is_primary_net: bool = False  # the net series the hero tiles / MC cone use


@dataclass
class InstrumentInputs:
    """Everything the report needs for one instrument."""

    symbol: str
    dates: list[str]  # ISO session dates, aligned with every series
    series: list[SeriesSpec]
    turnover: np.ndarray  # per-session turnover (contracts/side), for metrics
    screen: dict | None = None  # optional screen-verdict block (gates)
    extras: dict = field(default_factory=dict)


# ----------------------------------------------------------------------------- analytics


def equity(r: np.ndarray) -> np.ndarray:
    """Compounded log-wealth path (inception 1.0 is the implicit prior point)."""
    return np.exp(np.cumsum(r))


def drawdown(eq: np.ndarray) -> np.ndarray:
    """Fractional drawdown (<= 0) from the running peak, with the peak measured
    from the 1.0 inception reference so a first-session loss is a real drawdown
    (quant-auditor F-1-1)."""
    peak = np.maximum.accumulate(np.concatenate([[1.0], eq]))[1:]
    return eq / peak - 1.0


def downsample(arr: np.ndarray, n: int = _DOWNSAMPLE_POINTS) -> np.ndarray:
    """Even stride down to <= ``n`` points (keeps first and last)."""
    a = np.asarray(arr, dtype=float)
    if a.size <= n:
        return a
    idx = np.unique(np.linspace(0, a.size - 1, n).astype(int))
    return a[idx]


def _sessions_per_year(dates: list[str]) -> tuple[float, float]:
    """Return (sessions_per_year, elapsed_years) from the first/last ISO date."""
    d0, d1 = date.fromisoformat(dates[0]), date.fromisoformat(dates[-1])
    years = max((d1 - d0).days / 365.25, 1e-9)
    return len(dates) / years, years


def metrics(r: np.ndarray, turn: np.ndarray, dates: list[str]) -> dict:
    """Platform-style performance metrics for one per-session log-return series."""
    n = len(r)
    eq = equity(r)
    dd = drawdown(eq)
    spy, years = _sessions_per_year(dates)
    mean = float(r.mean())
    sd = float(r.std(ddof=1)) if n > 1 else 0.0
    dsd = float(np.sqrt((np.minimum(r, 0.0) ** 2).mean()))
    wins, losses = r[r > 0], r[r < 0]
    simple = np.expm1(r)  # simple per-session P&L for the gross-profit/loss profit factor
    gp_s, gl_s = float(simple[simple > 0].sum()), float(simple[simple < 0].sum())
    final = float(eq[-1])
    maxdd = float(dd.min())
    cagr = (final ** (1 / years) - 1.0) if final > 0 else float("nan")
    return {
        "n_sessions": n,
        "date_start": dates[0],
        "date_end": dates[-1],
        "years": years,
        "sessions_per_year": spy,
        "total_return_pct": (final - 1.0) * 100,
        "final_equity": final,
        "cagr_pct": cagr * 100,
        "sharpe_ann": mean / sd * np.sqrt(spy) if sd > 0 else 0.0,
        "sortino_ann": (mean / dsd * np.sqrt(spy))
        if dsd > 0
        else (float("inf") if mean > 0 else 0.0),
        "max_drawdown_pct": maxdd * 100,
        "calmar": (cagr / abs(maxdd)) if maxdd < 0 and np.isfinite(cagr) else float("nan"),
        "mean_bps": mean * 1e4,
        "std_bps": sd * 1e4,
        "win_rate_pct": float((r > 0).mean()) * 100,
        "profit_factor": gp_s / abs(gl_s) if gl_s != 0 else float("inf"),
        "avg_win_bps": float(wins.mean()) * 1e4 if wins.size else 0.0,
        "avg_loss_bps": float(losses.mean()) * 1e4 if losses.size else 0.0,
        "expectancy_bps": mean * 1e4,
        "best_bps": float(r.max()) * 1e4,
        "worst_bps": float(r.min()) * 1e4,
        "avg_turnover": float(turn.mean()),
        "total_turnover": float(turn.sum()),
    }


def monthly(r: np.ndarray, dates: list[str]) -> list[dict]:
    """Compounded return per calendar month (%), one row per year + YTD."""
    acc: dict[tuple[int, int], float] = {}
    for ri, ds in zip(r, dates, strict=True):
        y, m, _ = ds.split("-")
        acc[(int(y), int(m))] = acc.get((int(y), int(m)), 0.0) + float(ri)
    rows = []
    for y in sorted({yy for yy, _ in acc}):
        months = [
            (np.exp(acc[(y, m)]) - 1.0) * 100 if (y, m) in acc else None for m in range(1, 13)
        ]
        ytd_log = sum(acc[(y, m)] for m in range(1, 13) if (y, m) in acc)
        rows.append({"year": y, "months": months, "ytd_pct": (np.exp(ytd_log) - 1.0) * 100})
    return rows


def return_hist(r: np.ndarray, bins: int = _HIST_BINS) -> dict:
    """Per-session return histogram in bps (counts + bin edges)."""
    counts, edges = np.histogram(r * 1e4, bins=bins)
    return {"counts": counts.tolist(), "edges": edges.tolist()}


def mc_cone(
    r: np.ndarray, rng: np.random.Generator, n_mc: int = _N_MC, cone_points: int = _CONE_POINTS
) -> dict:
    """Iid bootstrap equity-path cone + terminal / max-drawdown distributions.

    Resamples per-session returns with replacement; this discards serial
    dependence, so under positive autocorrelation the cone and the max-drawdown
    tail understate realized risk (see module docstring).
    """
    n = len(r)
    idx = rng.integers(0, n, size=(n_mc, n))
    paths = np.exp(np.cumsum(r[idx], axis=1))
    tsel = np.unique(np.linspace(0, n - 1, cone_points).astype(int))
    pct = np.percentile(paths[:, tsel], [5, 25, 50, 75, 95], axis=0)
    term = paths[:, -1]
    paths0 = np.concatenate([np.ones((paths.shape[0], 1)), paths], axis=1)  # 1.0 inception (F-1-1)
    dd = (paths0 / np.maximum.accumulate(paths0, axis=1) - 1.0).min(axis=1)
    hi = float(np.percentile(term, 99.5))
    counts, edges = np.histogram(np.clip(term, 0, hi if hi > 0 else 1.0), bins=_MC_HIST_BINS)
    return {
        "t_index": tsel.tolist(),
        "p05": pct[0].tolist(),
        "p25": pct[1].tolist(),
        "p50": pct[2].tolist(),
        "p75": pct[3].tolist(),
        "p95": pct[4].tolist(),
        "terminal": {
            "p05": float(np.percentile(term, 5)),
            "p50": float(np.percentile(term, 50)),
            "p95": float(np.percentile(term, 95)),
            "mean": float(term.mean()),
            "prob_loss_pct": float((term < 1.0).mean()) * 100,
            "hist_counts": counts.tolist(),
            "hist_edges": edges.tolist(),
        },
        "maxdd": {
            "p50_pct": float(np.percentile(dd, 50)) * 100,
            "p05_pct": float(np.percentile(dd, 5)) * 100,  # worst 5% tail
            "worst_pct": float(dd.min()) * 100,
        },
    }


# ----------------------------------------------------------------------------- assembly


def _instrument_block(
    inp: InstrumentInputs, *, rng: np.random.Generator, mc_keys: list[str], n_mc: int
) -> dict:
    dates = inp.dates
    sm = {s.key: np.asarray(s.values, dtype=float) for s in inp.series}
    dates_ds = [
        dates[j] for j in np.unique(np.linspace(0, len(dates) - 1, _DOWNSAMPLE_POINTS).astype(int))
    ]
    return {
        "symbol": inp.symbol,
        "dates_ds": dates_ds,
        "n_sessions": len(dates),
        "equity": {k: downsample(equity(v)).tolist() for k, v in sm.items()},
        "drawdown": {k: downsample(drawdown(equity(v)) * 100).tolist() for k, v in sm.items()},
        "metrics": {k: metrics(v, inp.turnover, dates) for k, v in sm.items()},
        "monthly": {k: monthly(v, dates) for k, v in sm.items()},
        "ret_hist": {k: return_hist(v) for k, v in sm.items()},
        "mc": {k: mc_cone(sm[k], rng, n_mc=n_mc) for k in mc_keys if k in sm},
        "screen": inp.screen,
        "extras": inp.extras,
    }


def build_report(
    *,
    hid: str,
    title: str,
    subtitle: str,
    cost_note: str,
    instruments: list[InstrumentInputs],
    disposition: str | None = None,
    enacted_level: float | None = None,
    generated: str,
    note: str = "",
    seed: int = _DEFAULT_SEED,
    n_mc: int = _N_MC,
) -> dict:
    """Assemble the full report dict for the template.

    The series DISPLAY spec (keys, labels, colours, dashes) is taken from the
    FIRST instrument and must match across instruments. Exactly one series must
    be flagged ``is_primary_net`` — the hero tiles, Monte Carlo cone and the
    monthly-heatmap default use it.
    """
    if not instruments:
        raise ValueError("build_report requires at least one instrument")
    ref = instruments[0].series
    keys0 = [s.key for s in ref]
    for ins in instruments[1:]:
        if [s.key for s in ins.series] != keys0:
            raise ValueError(
                f"series keys differ for {ins.symbol}: {[s.key for s in ins.series]} != {keys0}"
            )
    primaries = [s.key for s in ref if s.is_primary_net]
    if len(primaries) != 1:
        raise ValueError(f"exactly one series must be is_primary_net; got {primaries}")
    primary_net = primaries[0]
    gross_key = keys0[0]
    mc_keys = [gross_key, primary_net] if gross_key != primary_net else [gross_key]

    series_display = [
        {
            "key": s.key,
            "label": s.label,
            "color": f"var(--{_COLOR_SLOTS[i % len(_COLOR_SLOTS)]})",
            "dash": s.dash,
            "is_primary_net": s.is_primary_net,
        }
        for i, s in enumerate(ref)
    ]
    rng = np.random.default_rng(seed)
    blocks = {
        ins.symbol: _instrument_block(ins, rng=rng, mc_keys=mc_keys, n_mc=n_mc)
        for ins in instruments
    }
    return {
        "hid": hid,
        "title": title,
        "subtitle": subtitle,
        "cost_note": cost_note,
        "disposition": disposition,
        "enacted_level": enacted_level,
        "generated": generated,
        "seed": seed,
        "n_mc": n_mc,
        "note": note,
        "series": series_display,
        "gross_key": gross_key,
        "primary_net_key": primary_net,
        "mc_cone_key": primary_net,
        "instrument_order": [ins.symbol for ins in instruments],
        "has_verdict": any(ins.screen for ins in instruments),
        "instruments": blocks,
    }


def round_floats(o, sig: int = 6):
    """Recursively round floats (and drop non-finite -> None) to shrink JSON."""
    if isinstance(o, bool):
        return o
    if isinstance(o, float):
        return None if not np.isfinite(o) else float(f"{o:.{sig}g}")
    if isinstance(o, dict):
        return {k: round_floats(v, sig) for k, v in o.items()}
    if isinstance(o, list | tuple):
        return [round_floats(v, sig) for v in o]
    return o
