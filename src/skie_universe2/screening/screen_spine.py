"""ADR-0014 screen spine — the shared, packaged screen machinery.

Single source of truth for the S-a..S-e screen sequence executed by the
fresh-forward-candidate harnesses (``scripts/run_screen_h105.py``,
``scripts/run_screen_h106.py``), extracted per the H105/H106 pre-freeze
audit round-1 findings CODE-1-1/CODE-1-2 (spine duplication + private-name
reach-through across file-path script imports). The statistical stages are
lifted stage-for-stage from the certified RC-*-2 screen harness
(``scripts/run_screen_h101_h103.py``); two pure helpers
(:func:`hac_variance_inflation`, :func:`kpss_stationarity`) carry the
frozen RC-H101-1 harness's computation (``scripts/run_rc_h101_1_scan.py`` —
left untouched as a historical scan artifact; THIS module is the living
copy new code imports; each function's docstring states its exact relation
to the frozen body).

Stages (per :class:`ScreenSpec`):

- **S-c** Romano-Wolf StepM over the declared cell family per instrument,
  stationary block bootstrap (Politis-Romano 1994) with the Politis-White
  2004 automatic block length; PASS iff mean gross > 0 AND adjusted p <
  the ENACTED ``screening_error_rate_target`` (read from
  ``config/multipletest_family.yaml`` at runtime — never transcribed).
- **S-d** DSR >= 1 - level (Bailey & Lopez de Prado 2014; HAC-adjusted
  n_eff; the gate trial count AND the cross-trial dispersion estimated on
  MATCHED surfaces — the dispersion pools the register's recorded
  non-``unconditional`` trial Sharpes with the current scan's sigma cells,
  H105 audit QUANT-1-4) and PBO <= level (Bailey et al. 2017 CSCV, S=16
  contiguous row-blocks on the NaN-masked T x n_cells member-only-Sharpe
  matrix over the full joined session panel).
- **S-e** amended rule: rule-based causal cells carry their structural
  observation lag; latent-state latency is UNATTAINABLE (the reproducible
  1c emission is required input; no placeholder).
- **Section-8 exhibits** (registered a-priori diagnostics; H105/H106 audit
  QUANT-1-5/QUANT-1-3): KPSS ('c' + 'ct'), the primary-cell stationary-
  bootstrap CI with the 25% half-width report-eligibility ratio, the
  Lo-2002 HAC-effective-n Sharpe SE, and an optional Ledoit-Wolf 2008
  pairwise cell contrast.

Leakage-clean covariate labeling: :func:`per_origin_percentile` scores each
eval-span session against the TRAIN-window empirical CDF of a per-session
covariate over the registered h900 rolling windows — the certified
RC-H103-2 construction (H105 audit QUANT-1-1: full-sample cutoffs are the
convicted construction class and are not used anywhere in this module).
"""

from __future__ import annotations

import hashlib
import json
import warnings
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import polars as pl
import yaml
from statsmodels.tools.sm_exceptions import InterpolationWarning
from statsmodels.tsa.stattools import kpss

from skie_universe2.eval.windows import h900_windows
from skie_universe2.inference.bootstrap import (
    politis_white_block_length,
    stationary_bootstrap_indices,
)
from skie_universe2.inference.deflated_sharpe import deflated_sharpe_ratio
from skie_universe2.inference.ledoit_wolf_sharpe import sharpe_ratio_difference_test
from skie_universe2.inference.pbo import probability_of_backtest_overfitting
from skie_universe2.inference.romano_wolf import romano_wolf_stepm
from skie_universe2.utils import reproducibility
from skie_universe2.utils.paths import ProjectPaths

# justify: scan convention (RC-H101-1/RC-*-2 lineage).
N_BOOTSTRAP = 1000
# justify: frozen pbo.py CSCV default (Bailey et al. 2017 S=16).
PBO_SPLITS = 16
# justify: RC-H101-1 convention — high/low cells = top/bottom tercile bands
# (re-expressed per-origin by per_origin_percentile; never full-sample).
VOL_TERCILE_HI = 2.0 / 3.0
VOL_TERCILE_LO = 1.0 / 3.0
MIN_CELL_N = 2  # justify: ddof=1 minimum; structural
EPS = 1e-12  # justify: structural div-by-zero guard
# justify: design §8 precision report-eligibility fraction (H900/H001/H101
# CONSORT-style convention, inherited verbatim).
PRECISION_FRACTION = 0.25
# justify: descriptive-CI level (design §8; binding level is the config's).
ALPHA_CI = 0.05


@dataclass(frozen=True)
class InstrumentData:
    """Per-instrument inputs the candidate harness supplies to the spine."""

    instrument: str
    dates: list
    gross: np.ndarray
    entered: np.ndarray
    cells: dict[str, np.ndarray]
    canary: dict
    extras: dict = field(default_factory=dict)


@dataclass(frozen=True)
class ScreenSpec:
    """One candidate's frozen screen parameterization (design-derived)."""

    scan_id: str
    hid: str
    seed: int
    n_trials_gate: int
    dwell_bars_per_session: float
    cell_order: tuple[str, ...]
    sigma_cells: tuple[str, ...]
    primary_cell: str
    ledger_expert_id: str
    observation_lag_bars: Mapping[str, float]
    dispersion_register_families: tuple[str, ...]
    prepare_instrument: Callable[[ProjectPaths, str], InstrumentData]
    design_relpath: str
    pairwise_contrast: tuple[str, str] | None = None
    instruments: tuple[str, ...] = ("ES", "NQ")


def screen_level(paths: ProjectPaths) -> float:
    """Read the enacted screening_error_rate_target (single source of truth)."""
    cfg = yaml.safe_load((paths.config / "multipletest_family.yaml").read_text(encoding="utf-8"))
    level = cfg.get("screening_error_rate_target")
    if not isinstance(level, int | float) or not (0.0 < level < 1.0):
        raise RuntimeError(
            "screening_error_rate_target is not enacted in config/multipletest_family.yaml"
        )
    return float(level)


def s_e_latency(paths: ProjectPaths) -> dict:
    """Read the S-e emission (P1-2.0-H900-BOCPD-WHITENED reproducible output).

    STOPS if absent — the supervised-CUSUM latency is FORBIDDEN and no
    placeholder is substituted (ADR-0014 S-e).
    """
    p = paths.root / "reports" / "H900_whitened_roc" / "h900_whitened_roc.json"
    if not p.is_file():
        raise RuntimeError(
            "S-e latency input missing: reports/H900_whitened_roc/h900_whitened_roc.json "
            "(run scripts/run_h900_whitened_roc.py first; no placeholder is substituted)"
        )
    emission = json.loads(p.read_text(encoding="utf-8")).get("s_e_unsupervised_detection_latency")
    if not emission:
        raise RuntimeError("S-e emission block empty in the whitened-ROC artifact")
    return emission


def hac_variance_inflation(x: np.ndarray) -> float:
    """HAC variance-inflation factor for the mean, Newey-West 1994 Bartlett bandwidth.

    Body lifted from the frozen RC-H101-1 harness `_hac_variance_inflation`
    (its docstring records the Lo-2002 leading-order-approximation
    rationale) — including the load-bearing bandwidth cap ``m <= n - 1``
    (without it, m > n crashes the autocovariance slices on small strongly
    autocorrelated cells; round-2 audit REPRODUCIBILITY-2-1/QUANT-2-1) and
    the pilot-lag floor. Floored at 1.0 (never deflates below the IID SE).
    """
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]
    n = x.size
    if n < MIN_CELL_N:
        return 1.0
    xc = x - x.mean()
    g0 = float(xc @ xc / n)
    if g0 <= EPS:
        return 1.0

    def gamma(j: int) -> float:
        return float(xc[: n - j] @ xc[j:] / n)

    # Newey-West 1994 plug-in: pilot lag then optimal Bartlett bandwidth.
    pilot = max(int(4.0 * (n / 100.0) ** (2.0 / 9.0)), 1)
    s0 = g0 + 2.0 * sum(gamma(j) for j in range(1, pilot + 1))
    s1 = 2.0 * sum(j * gamma(j) for j in range(1, pilot + 1))
    if abs(s0) <= EPS:
        return 1.0
    gamma_hat = 1.1447 * (((s1 / s0) ** 2) ** (1.0 / 3.0))  # Bartlett-kernel constant
    m = min(max(int(gamma_hat * n ** (1.0 / 3.0)), 0), n - 1)
    lrv = g0 + 2.0 * sum((1.0 - j / (m + 1.0)) * gamma(j) for j in range(1, m + 1))
    return float(max(lrv / g0, 1.0))


def kpss_stationarity(x: np.ndarray) -> dict:
    """KPSS stationarity test, both variants (Kwiatkowski et al. 1992).

    Statistically identical to the frozen RC-H101-1 harness
    `_kpss_stationarity` (same tests, same primary read); the output keys
    are renamed ``level``/``trend`` -> ``level_c``/``trend_ct`` for
    self-describing artifacts. Level ('c') is the primary read (matching
    the constant-mean premise of the bootstrap/RW/DSR stack); 'ct'
    reported in full alongside.
    """
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]

    def _one(reg: str) -> dict:
        with warnings.catch_warnings():
            # kpss emits InterpolationWarning when the statistic falls
            # outside the p-value lookup table; crit values are the primary
            # read, so ONLY that category is suppressed.
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
        "stat": level["stat"],
        "reject_stationarity_5pct": level["reject_stationarity_5pct"],
        "level_c": level,
        "trend_ct": trend,
    }


def member_only_sharpe(sub: np.ndarray) -> np.ndarray:
    """Per-column Sharpe over MEMBER (non-NaN) sessions (RC-*-2 CSCV rule)."""
    n_cols = sub.shape[1]
    out = np.full(n_cols, -np.inf, dtype=np.float64)
    for j in range(n_cols):
        v = sub[:, j]
        v = v[np.isfinite(v)]
        if v.size < MIN_CELL_N:
            continue
        sd = v.std(ddof=1)
        if sd > EPS:
            out[j] = float(v.mean() / sd)
    return out


def cell_sharpe(v: np.ndarray) -> float:
    """ddof=1 per-session Sharpe of a cell's member values (nan if degenerate)."""
    v = v[np.isfinite(v)]
    if v.size < MIN_CELL_N:
        return float("nan")
    sd = v.std(ddof=1)
    return float(v.mean() / sd) if sd > EPS else float("nan")


def consecutive_run_median(members: np.ndarray) -> float:
    """Median run length (sessions) of consecutive TRUE membership."""
    if members.size == 0 or not members.any():
        return 0.0
    padded = np.concatenate(([False], members, [False]))
    starts = np.flatnonzero(padded[1:].astype(int) - padded[:-1].astype(int) == 1)
    ends = np.flatnonzero(padded[1:].astype(int) - padded[:-1].astype(int) == -1)
    return float(np.median(ends - starts))


def rolling_growth(gross: np.ndarray, dates: list, mask: np.ndarray) -> list[float]:
    """Mean gross over the cell's member sessions per REGISTERED eval window."""
    if not dates:
        return []
    out = []
    for w in h900_windows():
        sel = mask & np.array([(w.origin <= d < w.eval_end) for d in dates])
        vals = gross[sel]
        vals = vals[np.isfinite(vals)]
        out.append(float(vals.mean()) if vals.size else float("nan"))
    return out


def json_sanitize(obj):
    """RFC 8259-safe serialization: NaN -> null, +/-inf -> string sentinels."""
    if isinstance(obj, dict):
        return {k: json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [json_sanitize(v) for v in obj]
    if isinstance(obj, float) and not np.isfinite(obj):
        return "inf" if obj > 0 else ("-inf" if obj < 0 else None)
    return obj


def ledger_sessions(paths: ProjectPaths, expert_id: str, symbol: str) -> pl.DataFrame:
    """Per-session pre-cost gross return from a candidate's k1.0 ledger."""
    glob = str(
        paths.data_processed
        / "shadow_ledger"
        / f"expert_id={expert_id}"
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


def per_origin_percentile(covs: pl.DataFrame, value_col: str) -> pl.DataFrame:
    """Leakage-clean per-origin percentile of a per-session covariate.

    The certified RC-H103-2 construction (train-window empirical CDF per
    registered h900 rolling window; eval-span sessions scored against it).
    Sessions outside every eval span (pre-first-origin) receive no label.
    Returns columns ``session_date``, ``{value_col}_pct``.
    """
    if covs.get_column(value_col).is_null().all():
        raise RuntimeError(f"per_origin_percentile: {value_col} is all-null")
    rows: list[dict] = []
    for w in h900_windows():
        train = covs.filter(
            (pl.col("session_date") >= w.train_start) & (pl.col("session_date") < w.origin)
        )
        ev = covs.filter(
            (pl.col("session_date") >= w.origin) & (pl.col("session_date") < w.eval_end)
        )
        train_vals = train.get_column(value_col).drop_nulls().to_numpy()
        if train_vals.size < MIN_CELL_N or ev.height == 0:
            continue
        train_sorted = np.sort(train_vals)
        ev_vals = ev.get_column(value_col).to_numpy().astype(np.float64)
        pct = np.searchsorted(train_sorted, ev_vals, side="right") / train_sorted.size
        for d, p, v in zip(ev.get_column("session_date").to_list(), pct, ev_vals, strict=True):
            if np.isfinite(v):
                rows.append({"session_date": d, f"{value_col}_pct": float(p)})
    if not rows:
        raise RuntimeError(f"per_origin_percentile: no labelable session for {value_col}")
    return pl.DataFrame(rows)


def register_trial_sharpes(paths: ProjectPaths, families: tuple[str, ...]) -> list[float]:
    """Recorded non-`unconditional` trial Sharpes of the named register families.

    Feeds the DSR cross-trial dispersion so the sigma surface matches the
    gate trial count's surface (H105 audit QUANT-1-4); `unconditional`
    trials are excluded per the standing non-nested-cell convention.

    FAIL-CLOSED (round-2 audit QUANT-2-3/REPRODUCIBILITY-2-2/CR-2-1): a
    named family that is absent from the register, or present with zero
    recorded trials, raises — the matched-surface commitment is run-order-
    dependent (e.g. rc-h105-1 is empty until the RC-H105-1 disposition
    emitter appends its trials), and silently under-pooling the dispersion
    would bias every downstream DSR.
    """
    cfg = yaml.safe_load((paths.config / "multipletest_family.yaml").read_text(encoding="utf-8"))
    by_id = {fam.get("family_id"): fam for fam in cfg.get("families", [])}
    out: list[float] = []
    for name in families:
        fam = by_id.get(name)
        if fam is None:
            raise RuntimeError(
                f"dispersion family {name!r} not found in config/multipletest_family.yaml"
            )
        vals = [
            float(t["sharpe_estimate"])
            for t in fam.get("trials", []) or []
            if not str(t.get("hid", "")).endswith(":unconditional")
            and isinstance(t.get("sharpe_estimate"), int | float)
        ]
        if not vals:
            raise RuntimeError(
                f"dispersion family {name!r} carries no recorded trial Sharpes — "
                "run its screen + disposition emitter first (matched-surface "
                "precondition; the spine fails closed rather than under-pool)"
            )
        out.extend(vals)
    return out


def _primary_cell_exhibits(
    gross: np.ndarray,
    cells: dict[str, np.ndarray],
    spec: ScreenSpec,
    entered: np.ndarray,
    bl: float,
) -> dict:
    """Design §8 exhibits: KPSS, primary-cell bootstrap CI + precision, Lo SE."""
    prim = gross[cells[spec.primary_cell]]
    prim = prim[np.isfinite(prim)]
    out: dict = {"kpss_entered_series": kpss_stationarity(gross[entered])}
    if prim.size < MIN_CELL_N:
        out["primary_cell"] = {"reason": "degenerate"}
        return out
    # Descriptive stationary-bootstrap CI on the primary-cell mean (design
    # §8; deterministic given the registered seed — a dedicated Generator so
    # the exhibit cannot perturb the S-c stream).
    rng = np.random.default_rng(spec.seed)
    means = np.empty(N_BOOTSTRAP, dtype=np.float64)
    for b in range(N_BOOTSTRAP):
        idx = stationary_bootstrap_indices(prim.size, block_length=bl, rng=rng)
        means[b] = float(prim[idx].mean())
    lo_q, hi_q = ALPHA_CI / 2.0, 1.0 - ALPHA_CI / 2.0
    ci_lo, ci_hi = float(np.quantile(means, lo_q)), float(np.quantile(means, hi_q))
    point = float(prim.mean())
    half_width = (ci_hi - ci_lo) / 2.0
    precision_ratio = half_width / abs(point) if abs(point) > EPS else float("inf")
    # Lo-2002 HAC-effective-n Sharpe SE (the RC-H101-1 documented
    # leading-order approximation: SE ~ sqrt((1 + SR^2/2) / n_eff)).
    vif = hac_variance_inflation(prim)
    n_eff = max(int(round(prim.size / vif)), MIN_CELL_N)
    sr = cell_sharpe(prim)
    sharpe_se = float(np.sqrt((1.0 + 0.5 * sr**2) / n_eff)) if np.isfinite(sr) else float("nan")
    out["primary_cell"] = {
        "cell": spec.primary_cell,
        "n": int(prim.size),
        "mean_gross": point,
        "ci95_stationary_bootstrap": [ci_lo, ci_hi],
        "ci_half_width": half_width,
        "precision_ratio_half_width_over_mean": precision_ratio,
        "precision_report_eligible": bool(precision_ratio < PRECISION_FRACTION),
        "precision_fraction": PRECISION_FRACTION,
        "sharpe": sr,
        "sharpe_se_lo2002_hac": sharpe_se,
        "hac_vif": float(vif),
        "n_eff_hac": n_eff,
    }
    if spec.pairwise_contrast is not None:
        a_cell, b_cell = spec.pairwise_contrast
        # Paired construction (RC-H103-1 precedent): each cell's returns
        # masked to 0 outside the cell over the common entered index, so the
        # legs are equal-length, algebraically dependent per-session series.
        common = entered & np.isfinite(gross)
        va = np.where(cells[a_cell], gross, 0.0)[common]
        vb = np.where(cells[b_cell], gross, 0.0)[common]
        if va.size >= MIN_CELL_N and va.std(ddof=1) > EPS and vb.std(ddof=1) > EPS:
            lw = sharpe_ratio_difference_test(
                va,
                vb,
                block_length=None,  # PW-auto on the paired influence series
                rng=np.random.default_rng(spec.seed),
                n_bootstrap=N_BOOTSTRAP,
            )
            out["pairwise_contrast"] = {
                "cells": [a_cell, b_cell],
                "construction": "cell-masked-to-zero paired series (RC-H103-1 rule)",
                "sharpe_diff": lw.sharpe_diff,
                "studentized_stat": lw.studentized_stat,
                "p_value": lw.p_value,
                "ci_low": lw.ci_low,
                "ci_high": lw.ci_high,
                "method": "Ledoit-Wolf 2008 studentized time-series bootstrap",
            }
        else:
            out["pairwise_contrast"] = {"cells": [a_cell, b_cell], "reason": "degenerate"}
    return out


def run_screen(paths: ProjectPaths, spec: ScreenSpec) -> dict:  # noqa: PLR0912, PLR0915 — one linear, auditable screen sequence (S-a..S-e -> disposition); splitting scatters the gate conjunction
    """Execute the ADR-0014 screen for one candidate per its frozen spec."""
    level = screen_level(paths)
    latency = s_e_latency(paths)
    # Fail-fast precondition probe (round-3 audit CODE-3-3): validate the
    # matched-dispersion families BEFORE any bootstrap work; the same values
    # feed the S-d dispersion pool below.
    reg_sharpes = register_trial_sharpes(paths, spec.dispersion_register_families)

    instruments_out: list[dict] = []
    per_symbol: dict[str, InstrumentData] = {}
    for symbol in spec.instruments:
        data = spec.prepare_instrument(paths, symbol)
        per_symbol[symbol] = data
        gross, cells = data.gross, data.cells
        masks = np.vstack([cells[c] for c in spec.cell_order])
        rng = np.random.default_rng(spec.seed)
        bl = max(politis_white_block_length(gross, bootstrap_type="stationary").block_length, 1.0)
        rw = romano_wolf_stepm(
            gross,
            masks,
            block_length=bl,
            rng=rng,
            n_bootstrap=N_BOOTSTRAP,
            alpha=level,
            min_n=MIN_CELL_N,
        )
        per_cell = []
        for i, c in enumerate(spec.cell_order):
            v = gross[cells[c]]
            v = v[np.isfinite(v)]
            per_cell.append(
                {
                    "cell": c,
                    "n": int(cells[c].sum()),
                    "mean_gross": float(v.mean()) if v.size else float("nan"),
                    "sharpe": cell_sharpe(gross[cells[c]]),
                    "stat": float(rw.stat[i]),
                    "rw_adj_pvalue": float(rw.adjusted_pvalue[i]),
                    "s_c_pass": bool(
                        v.size >= MIN_CELL_N
                        and float(v.mean()) > 0.0
                        and float(rw.adjusted_pvalue[i]) < level
                    ),
                }
            )
        instruments_out.append(
            {
                "instrument": symbol,
                "canary": data.canary,
                "block_length": float(bl),
                "cells": per_cell,
                "section8": _primary_cell_exhibits(gross, cells, spec, data.entered, bl),
                **({"extras": data.extras} if data.extras else {}),
            }
        )

    # ---- S-d: DSR + PBO; dispersion surface matched to the gate count
    # (reg_sharpes validated fail-fast at entry) ----
    sigma_pool = list(reg_sharpes)
    for inst in instruments_out:
        for c in inst["cells"]:
            if c["cell"] in spec.sigma_cells and np.isfinite(c["sharpe"]):
                sigma_pool.append(c["sharpe"])
    sr_std = float(np.std(sigma_pool, ddof=1)) if len(sigma_pool) > 1 else float("nan")

    for inst in instruments_out:
        data = per_symbol[inst["instrument"]]
        gross, cells, dates = data.gross, data.cells, data.dates
        mat = np.column_stack([np.where(cells[c], gross, np.nan) for c in spec.cell_order])
        pbo_res = probability_of_backtest_overfitting(
            mat, s_splits=PBO_SPLITS, score_fn=member_only_sharpe
        )
        inst["pbo"] = {
            "pbo": float(pbo_res.pbo),
            "s_splits": PBO_SPLITS,
            "n_combinations": int(pbo_res.n_combinations),
            "construction": (
                "NaN-masked T x n_cells per-session matrix over the full "
                "joined session panel, member-only Sharpe score_fn "
                "(RC-*-2 screen rule)"
            ),
        }
        pair_rhos: list[float] = []
        n_cols = mat.shape[1]
        for a in range(n_cols):
            for b in range(a + 1, n_cols):
                both = np.isfinite(mat[:, a]) & np.isfinite(mat[:, b])
                if int(both.sum()) < MIN_CELL_N:
                    continue
                va, vb = mat[both, a], mat[both, b]
                if va.std(ddof=1) <= EPS or vb.std(ddof=1) <= EPS:
                    continue
                pair_rhos.append(float(np.corrcoef(va, vb)[0, 1]))
        rho_bar = float(np.mean(pair_rhos)) if pair_rhos else None
        n_eff_corr = (
            spec.n_trials_gate / (1.0 + (spec.n_trials_gate - 1) * max(rho_bar, 0.0))
            if rho_bar is not None
            else None
        )
        inst["cell_dependence"] = {
            "rho_bar_pairwise_complete": rho_bar,
            "n_estimable_pairs": len(pair_rhos),
            "note": (
                "pairwise-complete member-overlap correlations; disjoint cell "
                "pairs are not estimable and are skipped"
            ),
        }
        inst["sr_std_surface"] = {
            "sr_std": sr_std,
            "n_register_trials": len(reg_sharpes),
            "register_families": list(spec.dispersion_register_families),
            "n_current_sigma_cells": len(sigma_pool) - len(reg_sharpes),
            "note": (
                "cross-trial dispersion pooled over the register's recorded "
                "non-unconditional trial Sharpes plus the current scan's "
                "sigma cells — matched to the gate count's surface "
                "(H105 audit QUANT-1-4)"
            ),
        }
        for c in inst["cells"]:
            mask = cells[c["cell"]]
            v = gross[mask]
            v = v[np.isfinite(v)]
            if v.size < MIN_CELL_N or not np.isfinite(sr_std) or sr_std <= EPS:
                c["s_d"] = {"dsr": float("nan"), "pass": False, "reason": "degenerate"}
                continue
            vif = hac_variance_inflation(v)
            n_eff = max(int(round(v.size / vif)), MIN_CELL_N)
            sd = v.std()
            skew = float(((v - v.mean()) ** 3).mean() / (sd**3 + EPS))
            kurt = float(((v - v.mean()) ** 4).mean() / (sd**4 + EPS))
            dsr = deflated_sharpe_ratio(
                c["sharpe"], n_eff, spec.n_trials_gate, sr_std, skew=skew, kurtosis=kurt
            )
            growth_series = rolling_growth(gross, dates, mask)
            finite = [g for g in growth_series if np.isfinite(g)]
            c["s_d"] = {
                "dsr": float(dsr.dsr),
                "dsr_bound": 1.0 - level,
                "dsr_pass": bool(dsr.dsr >= 1.0 - level),
                "pbo": inst["pbo"]["pbo"],
                "pbo_bound": level,
                "pbo_pass": bool(inst["pbo"]["pbo"] <= level),
                "n_eff_hac": n_eff,
                "hac_vif": float(vif),
                "n_trials_gate": spec.n_trials_gate,
                "n_eff_corr_adjusted_reported": (
                    float(n_eff_corr) if n_eff_corr is not None else None
                ),
                "per_window_growth": growth_series,
                "positive_window_fraction": (
                    float(np.mean([g > 0 for g in finite])) if finite else float("nan")
                ),
                "pass": bool(dsr.dsr >= 1.0 - level and inst["pbo"]["pbo"] <= level),
            }
        latent_attainable = bool(latency.get("latent_state_latency_attainable", False))
        for c in inst["cells"]:
            mask = cells[c["cell"]]
            med_run = consecutive_run_median(mask[data.entered])
            dwell_bars = med_run * spec.dwell_bars_per_session
            obs_lag = spec.observation_lag_bars.get(c["cell"])
            c["s_e"] = {
                "median_membership_run_sessions": med_run,
                "cell_dwell_bars": dwell_bars,
                "cell_mechanism": "rule-based-causal-covariate",
                "observation_lag_bars": obs_lag,
                "latent_state_latency_attainable": latent_attainable,
                "latent_state_note": (
                    "latent-state unsupervised latency UNATTAINABLE on the "
                    "reproducible 1c emission; a latent-state cell would FAIL "
                    "this gate outright"
                ),
                "pass": bool(obs_lag is not None and dwell_bars >= obs_lag),
            }
        for c in inst["cells"]:
            c["screen_pass"] = bool(
                inst["canary"]["pass"]
                and c["s_c_pass"]
                and c.get("s_d", {}).get("pass", False)
                and c.get("s_e", {}).get("pass", False)
            )

    any_pass = any(c["screen_pass"] for inst in instruments_out for c in inst["cells"])
    any_sc = any(c["s_c_pass"] for inst in instruments_out for c in inst["cells"])
    if any_pass:
        disposition = (
            "screen-pass -> provisional pool (pool-hold-reconsider eligible; "
            "VERDICT deferred under the ADR-0015 ratified operator HOLD)"
        )
    elif any_sc:
        disposition = (
            "archive-no-persistent-window (gross edge present in >= 1 cell but "
            "persistence/selectability gates fail)"
        )
    else:
        disposition = (
            "archive-no-persistent-window (sub-reason: archive-no-gross-edge — "
            "no S-c pass in any cell)"
        )

    return {
        "scan": spec.scan_id,
        "hypothesis_id": spec.hid,
        "screen_level": level,
        "s_e_emission": latency,
        "seed_s_c": spec.seed,
        "s_d_s_e_stages": "deterministic (no RNG consumed)",
        "n_bootstrap": N_BOOTSTRAP,
        "primary_cell": spec.primary_cell,
        "dwell_bars_per_session": spec.dwell_bars_per_session,
        "ledger_expert_id": spec.ledger_expert_id,
        "disposition": disposition,
        "decision_rule": (
            "ADR-0014 SCREEN: a cell passes iff S-a canary AND mean gross > 0 AND "
            f"RW-adjusted p < {level} (S-c) AND DSR >= {1 - level:.4f} AND PBO <= "
            f"{level} (S-d) AND cell dwell >= the observation lag (S-e). >= 1 "
            "passing cell -> pool entry; else archive-no-persistent-window. "
            "NOTHING certified; VERDICT deferred (ADR-0015 HOLD)."
        ),
        "instruments": instruments_out,
    }


def build_checksums(paths: ProjectPaths, spec: ScreenSpec, dataset_name: str) -> dict[str, str]:
    """ReproLog checksum set: substrate + design + level config + S-e emission
    + the candidate's OWN ledger partitions (the primary evidence — H105
    audit REPRODUCIBILITY-1-4; fail-closed when absent)."""
    manifest = json.loads((paths.data / "_manifest.json").read_text(encoding="utf-8"))
    checksums = {k: e["sha256"] for k, e in manifest["files"].items() if dataset_name in k}
    if not checksums:
        raise RuntimeError("no substrate checksums found in data/_manifest.json")
    ledger_entries = {
        k: e["sha256"]
        for k, e in manifest["files"].items()
        if f"expert_id={spec.ledger_expert_id}" in k
    }
    if not ledger_entries:
        raise RuntimeError(
            f"no ledger-partition checksums for expert_id={spec.ledger_expert_id} in "
            "data/_manifest.json — run the backfill (and manifest update) first"
        )
    # Bind a digest over the sorted per-partition hashes (thousands of
    # partitions; the ReproLog stays readable, the binding stays exact).
    digest = hashlib.sha256(
        "".join(f"{k}:{v}\n" for k, v in sorted(ledger_entries.items())).encode()
    ).hexdigest()
    checksums[f"shadow_ledger:expert_id={spec.ledger_expert_id} ({len(ledger_entries)} parts)"] = (
        digest
    )
    design = paths.root / spec.design_relpath
    checksums[spec.design_relpath] = hashlib.sha256(design.read_bytes()).hexdigest()
    checksums["config/multipletest_family.yaml"] = hashlib.sha256(
        (paths.config / "multipletest_family.yaml").read_bytes()
    ).hexdigest()
    roc = paths.root / "reports/H900_whitened_roc/h900_whitened_roc.json"
    if roc.is_file():
        checksums["reports/H900_whitened_roc/h900_whitened_roc.json"] = hashlib.sha256(
            roc.read_bytes()
        ).hexdigest()
    return checksums


def run_main(paths: ProjectPaths, spec: ScreenSpec, dataset_name: str, out_dir: Path) -> int:
    """ReproLog -> screen -> JSON artifact -> console summary (shared scaffold)."""
    out_dir.mkdir(parents=True, exist_ok=True)
    checksums = build_checksums(paths, spec, dataset_name)
    design_sha = checksums[spec.design_relpath]
    log = reproducibility.capture(
        phase=f"{spec.scan_id.lower()}-screen",
        hypothesis_id=spec.hid,
        rng_seed=spec.seed,
        dataset_checksums=checksums,
        config_resolved_sha256=design_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (design SHA {design_sha[:12]}...)", flush=True)

    result = run_screen(paths, spec)
    result["repro_log"] = log_path.name
    result["design_md_sha256"] = design_sha
    out_path = out_dir / f"{spec.scan_id.lower().replace('-', '_')}_screen.json"
    out_path.write_text(
        json.dumps(json_sanitize(result), indent=2, sort_keys=True, default=str, allow_nan=False),
        encoding="utf-8",
    )
    print(f"[{result['scan']}] disposition: {result['disposition']}", flush=True)
    for inst in result["instruments"]:
        for c in inst["cells"]:
            sd = c.get("s_d", {})
            print(
                f"  {inst['instrument']}/{c['cell']}: n={c['n']} "
                f"mean={c['mean_gross']:.3e} S-c p={c['rw_adj_pvalue']:.3f} "
                f"DSR={sd.get('dsr', float('nan')):.3f} PBO={sd.get('pbo', float('nan')):.3f} "
                f"PASS={c['screen_pass']}",
                flush=True,
            )
    return 0
