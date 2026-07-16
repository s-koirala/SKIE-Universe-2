"""RC-H101-1 — H101 first-hour-ORB admission scan (ADR-0002(c)).

Executes the H101 frozen design §5 admission scan on the backfilled shadow ledger:
does the unconditional first-hour ORB carry conditional GROSS (pre-cost) per-session
edge in a pre-declared conditioning cell? Primary pre-registered cell family =
high-realized-volatility sessions (Lundström prior:
[Holmberg, Lönnbark & Lundström 2013](https://doi.org/10.1016/j.frl.2012.09.001),
design §3).

Pipeline:
  1. Aggregate the H101 ledger (Kelly fraction 1.0 = unit position → the pre-cost
     ORB gross return) to per-SESSION gross returns per instrument; entered mask =
     sessions the ORB traded.
  2. Per-session conditioning covariates from the substrate: session realized-vol
     tercile (the high-vol primary cell), first-hour RTH return sign, unconditional.
  3. Confirmation ladder (descriptive — screening/FWER level DEFERRED):
     - Romano-Wolf StepM over the cells (FWER-adjusted p-values, every cell).
     - Stationarity: KPSS level+trend test (design §8(a), Kwiatkowski et al. 1992)
       PLUS the rolling-origin sub-window dispersion exhibit (§8(b), aligned to the
       §6 6-month walk-forward step).
     - Deflated Sharpe Ratio on the primary cell, with an autocorrelation-adjusted
       (HAC, Newey-West 1994 bandwidth) effective sample size (design §8 TS-Sharpe
       mandate) and N_trials over the full instrument×cell selection surface.
     - Matched-turnover random rotor (ADR-0007 non-waivable) on the PRIMARY cell
       (the adjudicated substrate) plus an unconditional exhibit.
  4. §10 disposition: admit-conditional / re-specify-cost / archive — DESCRIPTIVE
     (no cell certified; the binding screening level is deferred).

PBO (design §8 / ADR-0008) is DEFERRED, not computed here: standard CSCV
(Bailey et al. 2017) requires a common-length (T×N) performance matrix over
alternative full-period strategy configurations, but the RC-H101-1 selection
surface is (a) conditioning-cell subsets on DIFFERENT session memberships (not a
common T) and (b) the Kelly-fraction × cell grid whose fraction axis is BLOCKED on
the two Decision-9 memos. PBO over that surface is materialized at the shadow-ledger
backfill once Kelly selection unblocks; until then it is deferred with the same
rigor as the screening-level deferral (it is NOT waived — no admission is certified
while it is outstanding).

Reads the CANONICAL ledger written by run_shadow_ledger_backfill.py --expert h101.

Usage:
    uv run python scripts/run_rc_h101_1_scan.py [--instruments ES,NQ] [--out reports/H101]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import warnings
from datetime import time
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import polars as pl
from statsmodels.tools.sm_exceptions import InterpolationWarning
from statsmodels.tsa.stattools import kpss

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) → skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.experts.orb_first_hour import _DEFAULT_N_OR  # noqa: E402
from skie_universe2.features.regime_emissions import (  # noqa: E402
    apply_registered_exclusions,
    compute_emissions,
    exclusion_windows_from_provenance,
)
from skie_universe2.inference.bootstrap import politis_white_block_length  # noqa: E402
from skie_universe2.inference.deflated_sharpe import deflated_sharpe_ratio  # noqa: E402
from skie_universe2.inference.matched_turnover_rotor import matched_turnover_rotor  # noqa: E402
from skie_universe2.inference.romano_wolf import romano_wolf_stepm  # noqa: E402
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

SEED = 20260716  # justify: H101 design.md §11 pre-registered seed
DATASET = "vendor_legacy_1min_roll_adjusted"
PROVENANCE_FILE = "vendor_legacy_1min_roll_adjusted_20260711.json"
# justify: bootstrap p-value MC standard error ≈ sqrt(p(1-p)/B); at B=1000 the SE is
# ≤ 0.0158 (worst case p=0.5) and 0.0069 at p=ALPHA=0.05 — sub-alpha resolution.
N_BOOTSTRAP = 1000
# justify: rotor-percentile MC SE ≈ sqrt(p(1-p)/B); at B=2000 the SE is ≤ 0.0112
# (p=0.5), 0.0049 at p=0.05 — decision-grade resolution at the ALPHA boundary.
N_ROTORS = 2000
ALPHA = 0.05  # justify: descriptive CI level; binding FWER = deferred screening target
_NY = ZoneInfo("America/New_York")
_RTH_OPEN = time(9, 30)
_VOL_TERCILE_HI = 2.0 / 3.0  # justify: high-vol primary cell = top realized-vol tercile
_VOL_TERCILE_LO = 1.0 / 3.0  # justify: low-vol contrast cell = bottom tercile
_MIN_CELL_N = 2  # justify: ddof=1 sample-variance minimum; structural, not a threshold
_EPS = 1e-12  # justify: structural div-by-zero guard, not a tunable threshold
_ROLLING_STEP_MONTHS = 6  # justify: H101 design §6 walk-forward step (rolling-origin exhibit §8(b))
_PRIMARY_CELL = "high_vol"  # justify: pre-registered primary cell (design §3, Lundström prior)
_CELL_ORDER = ("unconditional", "high_vol", "low_vol", "first_hour_up", "first_hour_down")
# Non-nested conditioning cells for the DSR cross-trial dispersion (exclude the
# 'unconditional' superset that contains every other cell → nested, poor sigma).
_SIGMA_CELLS = ("high_vol", "low_vol", "first_hour_up", "first_hour_down")


def _dataset_checksums(paths: ProjectPaths) -> dict[str, str]:
    """Per-file SHA-256 for the scan substrate from data/_manifest.json (ReproLog R1-E)."""
    manifest = json.loads((paths.data / "_manifest.json").read_text(encoding="utf-8"))
    out = {k: e["sha256"] for k, e in manifest["files"].items() if DATASET in k}
    if not out:
        raise RuntimeError("no dataset checksums found in data/_manifest.json")
    return out


def _hac_variance_inflation(x: np.ndarray) -> float:
    """HAC variance-inflation factor for the mean, Newey-West 1994 Bartlett bandwidth.

    Returns ``LRV / gamma0`` where ``LRV`` is the Bartlett-kernel long-run variance
    with the Newey & West 1994 data-dependent bandwidth (rules/quant-project.md HAC
    rule). Feeding the Sharpe SE an effective sample size ``T / VIF`` is a leading-order
    HAC APPROXIMATION to the Lo-2002 time-series Sharpe SE (design §8): it inflates the
    SE by the return-MEAN long-run-variance ratio, not the exact Lo-2002 estimator
    (which also involves the squared-return moment dynamics). Adequate here — VIF≈1.08
    (ES) / 1.375 (NQ), both DSR conclusions robust. Floored at 1.0 (never deflate below
    the IID SE; the design's concern is that IID UNDERSTATES the SE under positive
    serial dependence).
    """
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]
    n = x.size
    if n < _MIN_CELL_N:
        return 1.0
    xc = x - x.mean()
    g0 = float(xc @ xc / n)
    if g0 <= _EPS:
        return 1.0

    def gamma(j: int) -> float:
        return float(xc[: n - j] @ xc[j:] / n)

    # Newey-West 1994 plug-in: pilot lag then optimal Bartlett bandwidth.
    pilot = max(int(4.0 * (n / 100.0) ** (2.0 / 9.0)), 1)
    s0 = g0 + 2.0 * sum(gamma(j) for j in range(1, pilot + 1))
    s1 = 2.0 * sum(j * gamma(j) for j in range(1, pilot + 1))
    if abs(s0) <= _EPS:
        return 1.0
    gamma_hat = 1.1447 * (((s1 / s0) ** 2) ** (1.0 / 3.0))  # Bartlett-kernel constant
    m = min(max(int(gamma_hat * n ** (1.0 / 3.0)), 0), n - 1)
    lrv = g0 + 2.0 * sum((1.0 - j / (m + 1.0)) * gamma(j) for j in range(1, m + 1))
    return float(max(lrv / g0, 1.0))


def _kpss_stationarity(x: np.ndarray) -> dict:
    """KPSS stationarity test, both variants (design §8(a), Kwiatkowski et al. 1992).

    Runs BOTH the level ``regression='c'`` (the variant matching the constant-mean
    premise of the block bootstrap / Romano-Wolf / DSR stack) and the level+trend
    ``regression='ct'`` variant. The top-level ``stat``/``reject_stationarity_5pct``
    mirror the level ('c') test as the primary read; both are reported in full.
    """
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]

    def _one(reg: str) -> dict:
        with warnings.catch_warnings():
            # kpss emits InterpolationWarning when the statistic falls outside the
            # p-value lookup table (p is then clipped to the nearest tabulated bound);
            # the crit values are the primary read, so ONLY that category is suppressed.
            warnings.simplefilter("ignore", category=InterpolationWarning)
            stat, pval, nlags, crit = kpss(x, regression=reg, nlags="auto")
        return {
            "stat": float(stat),
            "pvalue_clipped": float(pval),
            "nlags": int(nlags),
            "crit": {k: float(v) for k, v in crit.items()},
            "reject_stationarity_5pct": bool(stat > crit["5%"]),
        }

    level = _one("c")
    trend = _one("ct")
    return {
        "level": level,  # regression='c' — matches the constant-mean bootstrap premise
        "trend": trend,  # regression='ct' — level+trend
        "stat": level["stat"],  # primary read = level variant
        "reject_stationarity_5pct": level["reject_stationarity_5pct"],
    }


def _kelly1_gross_ledger(paths: ProjectPaths, symbol: str) -> pl.DataFrame:
    """Per-session pre-cost ORB gross return from the k1.0 ledger partitions.

    Kelly fraction 1.0 = unit position → the ledger ``ret_gross`` is the pre-cost ORB
    gross return; the per-bar rows sum to the per-session gross. ``n_active`` counts
    non-zero-return bars (the entry proxy — the Tier-0 ledger schema stores no
    explicit position/turnover column).
    """
    glob = str(
        paths.data_processed
        / "shadow_ledger"
        / "expert_id=orb_first_hour_k1.0@1.0.0"
        / f"asset={symbol}"
        / "**"
        / "part-0000.parquet"
    )
    lf = pl.scan_parquet(glob).select("session_date", "ret_gross")
    return (
        lf.group_by("session_date")
        .agg(
            gross=pl.col("ret_gross").sum(),
            n_active=(pl.col("ret_gross") != 0).sum(),
        )
        .sort("session_date")
        .collect()
    )


def _session_covariates(paths: ProjectPaths, symbol: str) -> pl.DataFrame:
    """Per-session conditioning covariates: realized-vol proxy + first-hour sign.

    The realized-vol proxy is ``rvol_5m_24h`` at the RTH open; the tercile split that
    defines the high/low-vol cells (in ``_cells``) is computed over the FULL sample.
    That is a DESCRIPTIVE conditioning partition (ADR-0001 Decision 5 covariate, NOT a
    gate), so the full-sample cutoff is admissible; design §6's train-window-only
    moment rule binds only covariates used as GATES, which these are not. Promoting a
    cell to a gate would require recomputing the tercile train-window-only per origin.
    """
    glob = str(paths.data_processed / DATASET / f"symbol={symbol}" / "**" / "*.parquet")
    lf = pl.scan_parquet(glob).select(
        "ts_event", "open", "high", "low", "close", "volume", "unadjusted_close", "pit_provisional"
    )
    gaps = json.loads(
        (paths.data_processed / "_provenance" / PROVENANCE_FILE).read_text(encoding="utf-8")
    )["coverage_gaps"]
    lf = apply_registered_exclusions(
        lf,
        symbol=symbol,
        exclusions=exclusion_windows_from_provenance(gaps),
        exclude_pit_provisional=True,
        exclude_coverage_gaps=True,
    )
    bars_5m = (
        lf.sort("ts_event")
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
    feats = compute_emissions(bars_5m).filter(pl.col("emission_valid")).sort("ts_event")
    ts = feats.get_column("ts_event").to_list()
    close = feats.get_column("close").to_numpy()
    rvol = feats.get_column("rvol_5m_24h").to_numpy()

    # First RTH bar per session -> session realized-vol proxy (rvol at RTH open) and
    # first-hour return sign (close after n_or RTH bars vs the RTH-open close).
    rows: dict[object, dict] = {}
    n_rth: dict[object, int] = {}
    for i, t in enumerate(ts):
        local = t.astimezone(_NY)
        if local.time() < _RTH_OPEN or local.time() >= time(16, 0):
            continue
        sd = local.date()
        k = n_rth.get(sd, 0)
        if k == 0:
            rows[sd] = {"session_date": sd, "rvol": float(rvol[i]), "or_open": float(close[i])}
        if k == _DEFAULT_N_OR:  # close at end of the first hour
            rows[sd]["fh_sign"] = int(np.sign(close[i] - rows[sd]["or_open"]))
        n_rth[sd] = k + 1
    recs = [r for r in rows.values() if "fh_sign" in r and np.isfinite(r["rvol"])]
    return pl.DataFrame(recs).select("session_date", "rvol", "fh_sign")


def _cells(entered: np.ndarray, rvol: np.ndarray, fh: np.ndarray) -> dict:
    """Pre-registered conditioning cells (boolean masks over ENTERED sessions).

    The vol terciles are full-sample descriptive cutoffs (see ``_session_covariates``);
    cells may overlap (``unconditional`` ⊇ every other cell; vol and sign cells cross),
    which the Romano-Wolf joint bootstrap accounts for.
    """
    hi = np.quantile(rvol, _VOL_TERCILE_HI)
    lo = np.quantile(rvol, _VOL_TERCILE_LO)
    return {
        "unconditional": entered,
        "high_vol": entered & (rvol >= hi),  # PRIMARY (Lundström prior)
        "low_vol": entered & (rvol <= lo),
        "first_hour_up": entered & (fh > 0),
        "first_hour_down": entered & (fh < 0),
    }


def _rolling_window_dispersion(gross: np.ndarray, session_dates: list, entered: np.ndarray) -> dict:
    """Per-window mean/variance dispersion over 6-month rolling-origin blocks (§8(b))."""
    ent_gross = gross[entered]
    ent_dates = [d for d, e in zip(session_dates, entered, strict=True) if e]
    if not ent_dates:
        return {"rolling_means": [], "rolling_vars": [], "mean_dispersion_cv": float("nan")}
    base = ent_dates[0].year * 12 + (ent_dates[0].month - 1)
    win_idx = np.array(
        [((d.year * 12 + (d.month - 1)) - base) // _ROLLING_STEP_MONTHS for d in ent_dates]
    )
    roll_means, roll_vars = [], []
    for w in range(int(win_idx.max()) + 1):
        chunk = ent_gross[win_idx == w]
        chunk = chunk[np.isfinite(chunk)]
        if chunk.size:
            roll_means.append(float(chunk.mean()))
        if chunk.size > 1:
            roll_vars.append(float(chunk.var(ddof=1)))
    cv = (
        float(np.std(roll_means) / (abs(np.mean(roll_means)) + _EPS))
        if roll_means
        else float("nan")
    )
    return {"rolling_means": roll_means, "rolling_vars": roll_vars, "mean_dispersion_cv": cv}


def run_scan(paths: ProjectPaths, symbol: str) -> dict:
    """Run the RC-H101-1 admission scan for one instrument.

    Returns
    -------
    dict
        ``instrument``, ``n_sessions``; ``cells`` (per-cell n / mean_gross / sharpe /
        RW stat / RW adj-p / descriptive rejection); ``primary`` (the high_vol cell's
        sr / n / n_eff / VIF / skew / kurtosis for the scan-level DSR); ``rotor_primary``
        and ``rotor_unconditional`` (matched-turnover rotor); ``kpss`` and
        ``stationarity`` (rolling-origin dispersion).
    """
    ledger = _kelly1_gross_ledger(paths, symbol)
    covs = _session_covariates(paths, symbol)
    df = ledger.join(covs, on="session_date", how="inner").sort("session_date")
    # Null/dtype safety at the polars→numpy boundary (a null-poisoned column would
    # silently NaN the downstream float math); fail loudly instead.
    nulls = df.select(pl.col("gross", "rvol", "fh_sign").null_count()).row(0)
    if any(nulls):
        raise RuntimeError(f"[{symbol}] unexpected nulls post-join: gross/rvol/fh_sign = {nulls}")
    session_dates = df.get_column("session_date").to_list()
    gross = df.get_column("gross").to_numpy().astype(np.float64)
    entered = df.get_column("n_active").to_numpy() > 0
    rvol = df.get_column("rvol").to_numpy().astype(np.float64)
    fh = df.get_column("fh_sign").to_numpy().astype(np.float64)
    # Non-finite guard: a Tier-0 ruin bar writes -inf, which the session sum would
    # propagate; count and exclude such sessions from the entered set (report the count).
    n_nonfinite = int((~np.isfinite(gross) & entered).sum())
    entered = entered & np.isfinite(gross)

    cells = _cells(entered, rvol, fh)
    cell_names = list(_CELL_ORDER)
    masks = np.vstack([cells[c] for c in cell_names])

    rng = np.random.default_rng(SEED)
    # Block length on the SAME chronological series the RW bootstrap resamples (the
    # full joined `gross` vector), not a different subset.
    bl = max(politis_white_block_length(gross, bootstrap_type="stationary").block_length, 1.0)
    rw = romano_wolf_stepm(
        gross,
        masks,
        block_length=bl,
        rng=rng,
        n_bootstrap=N_BOOTSTRAP,
        alpha=ALPHA,
        min_n=_MIN_CELL_N,
    )

    # Per-cell Sharpe (per-session units) for the scan-level DSR cross-trial dispersion.
    def _cell_sharpe(mask: np.ndarray) -> float:
        v = gross[mask]
        v = v[np.isfinite(v)]
        if v.size < _MIN_CELL_N:
            return float("nan")
        sd = v.std(ddof=1)
        # Degenerate (sd==0) cell -> nan (not 0.0): a constant cell has no Sharpe, and
        # nan is dropped cleanly from the DSR sigma pool (np.isfinite filter) rather
        # than mis-scoring a constant-negative cell as neutral (mirrors the romano_wolf
        # _cell_stats degenerate convention).
        return float(v.mean() / sd) if sd > _EPS else float("nan")

    per_cell = []
    for i, c in enumerate(cell_names):
        v = gross[cells[c]]
        v = v[np.isfinite(v)]
        per_cell.append(
            {
                "cell": c,
                "n": int(cells[c].sum()),
                "mean_gross": float(v.mean()) if v.size else float("nan"),
                "sharpe": _cell_sharpe(cells[c]),
                "stat": float(rw.stat[i]),
                "rw_adj_pvalue": float(rw.adjusted_pvalue[i]),
                "rejected_descriptive": bool(rw.rejected[i]),
            }
        )

    # Primary-cell inputs for the scan-level DSR: HAC-adjusted effective n (design §8
    # time-series Sharpe SE mandate).
    prim = gross[cells[_PRIMARY_CELL]]
    prim = prim[np.isfinite(prim)]
    vif = _hac_variance_inflation(prim)
    n_eff = max(int(round(prim.size / vif)), _MIN_CELL_N) if prim.size >= _MIN_CELL_N else prim.size
    prim_sd = prim.std() if prim.size else 0.0
    skew = float(((prim - prim.mean()) ** 3).mean() / (prim_sd**3 + _EPS)) if prim.size else 0.0
    kurt = float(((prim - prim.mean()) ** 4).mean() / (prim_sd**4 + _EPS)) if prim.size else 3.0
    primary = {
        "cell": _PRIMARY_CELL,
        "n": int(prim.size),
        "sharpe": _cell_sharpe(cells[_PRIMARY_CELL]),
        "hac_vif": float(vif),
        "n_eff": int(n_eff),
        "skew": skew,
        "kurtosis": kurt,
    }

    # Matched-turnover rotor: PRIMARY cell (the adjudicated substrate, design §10) plus
    # an unconditional exhibit. Independent RNG substreams derived from the pre-registered
    # SEED per design §11 ("bootstrap/rotor seeds derived as seed + replicate_index").
    def _rotor(series: np.ndarray, offset: int) -> dict:
        s = series[np.isfinite(series)]
        nan = float("nan")
        if s.size < _MIN_CELL_N:
            return {"expert_mean": nan, "expert_percentile": nan, "p_value": nan}
        r = matched_turnover_rotor(
            s,
            np.ones(s.size, dtype=bool),
            n_rotors=N_ROTORS,
            rng=np.random.default_rng(SEED + offset),
        )
        return {
            "expert_mean": r.expert_mean,
            "expert_percentile": r.expert_percentile,
            "p_value": r.p_value,
        }

    rotor_primary = _rotor(gross[cells[_PRIMARY_CELL]], 1)
    rotor_uncond = _rotor(gross[entered], 2)

    return {
        "instrument": symbol,
        "n_sessions": int(entered.sum()),
        "n_nonfinite_excluded": n_nonfinite,
        "block_length": float(bl),
        "cells": per_cell,
        "primary": primary,
        "rotor_primary": rotor_primary,
        "rotor_unconditional": rotor_uncond,
        "kpss": _kpss_stationarity(gross[entered]),
        "stationarity": _rolling_window_dispersion(gross, session_dates, entered),
    }


def _scan_dsr(results: list[dict]) -> None:
    """Attach the Deflated Sharpe Ratio per instrument (mutates each result in place).

    N_trials = the full instrument×cell selection surface (ADR-0013 more-binding
    multiplicity under leverage; a LOWER bound on the true historical trial count,
    so the reported DSR is an upper bound). sigma_SR = ddof=1 dispersion of the
    NON-NESTED conditioning-cell Sharpes pooled across instruments (excludes the
    'unconditional' superset). The primary-cell SE uses the HAC effective n.
    """
    n_trials = len(results) * len(_CELL_ORDER)
    pooled = []
    for r in results:
        by_cell = {c["cell"]: c["sharpe"] for c in r["cells"]}
        pooled.extend(by_cell[c] for c in _SIGMA_CELLS if np.isfinite(by_cell.get(c, np.nan)))
    sr_std = float(np.std(pooled, ddof=1)) if len(pooled) > 1 else float("nan")
    for r in results:
        p = r["primary"]
        if p["n"] >= _MIN_CELL_N and np.isfinite(sr_std) and sr_std > _EPS:
            sr = p["sharpe"]
            dsr = deflated_sharpe_ratio(
                sr, p["n_eff"], n_trials, sr_std, skew=p["skew"], kurtosis=p["kurtosis"]
            )
            r["deflated_sharpe"] = {
                "dsr": dsr.dsr,
                "sr_observed": dsr.sr_observed,
                "sr_benchmark": dsr.sr_benchmark,
                "n_trials": n_trials,
                "sr_std_pooled": sr_std,
                "n_eff_hac": p["n_eff"],
                "hac_vif": p["hac_vif"],
            }
        else:
            r["deflated_sharpe"] = None


def _disposition(results: list[dict]) -> str:
    """Descriptive §10 disposition keyed on the PRIMARY (high_vol) cell.

    A descriptive positive requires: primary-cell mean gross > 0 AND Romano-Wolf
    descriptive rejection AND the primary cell beats its OWN matched-turnover rotor
    (p < ALPHA). Binding certification awaits the deferred screening level.
    """
    for r in results:
        prim = next(c for c in r["cells"] if c["cell"] == _PRIMARY_CELL)
        rotor_p = r["rotor_primary"]["p_value"]
        beats_rotor = np.isfinite(rotor_p) and rotor_p < ALPHA
        if prim["mean_gross"] > 0 and prim["rejected_descriptive"] and beats_rotor:
            return "admit-conditional (DESCRIPTIVE; screening level deferred, not certified)"
    return "no descriptive positive primary-cell edge (screening level deferred; not archived)"


def main() -> int:
    """ReproLog → per-instrument scan → scan-level DSR → disposition → JSON artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instruments", default="ES,NQ")
    parser.add_argument("--out", default="reports/H101")
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    out_dir = paths.root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    instruments = tuple(s.strip() for s in args.instruments.split(","))

    # ReproLog first (ADR-0008 / CLAUDE.md reproducibility contract): git HEAD,
    # pip-freeze SHA, dataset checksums, seed, frozen-design SHA.
    design_path = paths.root / "research/01_hypothesis_register/H101/design.md"
    design_sha = hashlib.sha256(design_path.read_bytes()).hexdigest()
    log = reproducibility.capture(
        phase="rc-h101-1-admission-scan",
        hypothesis_id="H101",
        rng_seed=SEED,
        dataset_checksums=_dataset_checksums(paths),
        config_resolved_sha256=design_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (design SHA {design_sha[:12]}...)", flush=True)

    results = [run_scan(paths, s) for s in instruments]
    _scan_dsr(results)
    disposition = _disposition(results)
    blob = {
        "scan": "RC-H101-1",
        "hypothesis_id": "H101",
        "disposition": disposition,
        "decision_rule": (
            "DESCRIPTIVE ADR-0002(c) scan: primary cell = high_vol; a cell is a "
            "descriptive positive iff mean gross > 0 AND Romano-Wolf-adjusted "
            "rejection AND beats its OWN matched-turnover rotor (p<0.05). The binding "
            "FWER/screening level is the DEFERRED screening_error_rate_target — no "
            "cell is CERTIFIED until it is set (design §5/§8/§10). PBO is DEFERRED "
            "(see module docstring), NOT waived."
        ),
        "seed": SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "n_rotors": N_ROTORS,
        "repro_log": log_path.name,
        "instruments": results,
    }
    (out_dir / "rc_h101_1_scan.json").write_text(
        json.dumps(blob, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    print(f"[RC-H101-1] disposition: {disposition}", flush=True)
    for r in results:
        prim = next(c for c in r["cells"] if c["cell"] == _PRIMARY_CELL)
        rp = r["rotor_primary"]["p_value"]
        kp = r["kpss"]
        dsr = r["deflated_sharpe"]
        dsr_str = f"{dsr['dsr']:.3f}" if dsr else "n/a"
        print(
            f"  {r['instrument']}: high_vol n={prim['n']} mean_gross={prim['mean_gross']:.2e} "
            f"rw_adj_p={prim['rw_adj_pvalue']:.3f} rotor_p={rp:.3f} "
            f"DSR={dsr_str} KPSS_c={kp['stat']:.3f}(rej5%={kp['reject_stationarity_5pct']})",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
