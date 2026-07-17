"""RC-H103-1 — H103 stress-state ORB admission scan (ADR-0002(c)).

Executes the H103 frozen design (SHA 84d01a6b4ad0…) §5(B) admission scan on the SHARED
H101 {ES, NQ} shadow ledger: does the first-hour ORB carry conditional GROSS (pre-cost)
per-session edge in the pre-registered STRESS cell? H103 is the anti-gate (stress-only)
conditioning of the same ORB rule H101 trades unconditionally — it shares H101's single
backfilled ledger, it is NOT a second expert (design §4).

Primary cell (design §3): the STRESS cell = sessions whose realized-vol percentile is
≥ (1 − p̂), where p̂ is the stationary (unconditional) occupancy probability of the H900
4-state diagonal-Gaussian HMM's stress state (highest log-rvol emission-mean state),
computed PER INSTRUMENT. This descriptive scan fits the registered HMM on the FULL sample
for p̂ and cuts the stress cell on the FULL-sample rvol quantile. Because the stress
indicator DEFINES H103's positions (multiplicative, §4) — not merely slicing an
unconditional strategy for reporting as RC-H101-1's tercile did — this full-sample cutoff
is genuine look-ahead relative to the registered per-rolling-origin train-window cutoff
(design §3/§6; config/conditioning_covariates.yaml reference_distribution =
training_window_empirical_cdf). It is retained here ONLY because the leakage is
ANTI-CONSERVATIVE for H0 — it can only INFLATE apparent stress edge — so a null/negative
stress result is robust to it a fortiori. The leakage-clean per-origin cutoff is the
CERTIFIED-run version, deferred with the screening level and PBO. The realized-vol
percentile input is `rvol_5m_24h` (288-bar causal), design §3.

Multiplicity (design §5(B)): Romano-Wolf StepM runs PER INSTRUMENT over the §3 cells;
the cross-instrument (2-family) multiplicity is controlled by a Šidák union bound at the
DEFERRED `screening_error_rate_target` (reported descriptively — nothing certified). DSR
N_trials folds in the FULL RC-H101-1 same-ledger surface (design §8). PBO is DEFERRED, not
waived (design §3.5/§8). Matched-turnover rotor is restricted to STRESS sessions
(design §7). RC-XCORR-1 non-redundancy vs H101 is computed PER INSTRUMENT (design §10).

Reads the CANONICAL ledger written by run_shadow_ledger_backfill.py --expert h101.

Usage:
    uv run python scripts/run_rc_h103_1_scan.py [--instruments ES,NQ] [--out reports/H103]
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
    emission_matrix,
    exclusion_windows_from_provenance,
    fit_moments,
    standardize,
)
from skie_universe2.inference.bootstrap import (  # noqa: E402
    politis_white_block_length,
    stationary_bootstrap_indices,
)
from skie_universe2.inference.deflated_sharpe import deflated_sharpe_ratio  # noqa: E402
from skie_universe2.inference.ledoit_wolf_sharpe import sharpe_ratio_difference_test  # noqa: E402
from skie_universe2.inference.matched_turnover_rotor import matched_turnover_rotor  # noqa: E402
from skie_universe2.inference.romano_wolf import romano_wolf_stepm  # noqa: E402
from skie_universe2.models.regime.hmm import GaussianHMM  # noqa: E402
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

SEED = 20260716  # justify: RC-H101/H103 scan seed lineage (project register)
HMM_SEED = 20260710  # justify: H900 design.md §11 pre-registered HMM seed (reused for p̂)
HMM_N_RESTARTS = 5  # justify: H900 design.md §5 (5 EM restarts)
HMM_RESTART_SEEDS = [HMM_SEED + i for i in range(HMM_N_RESTARTS)]  # justify: seed+i rule
DATASET = "vendor_legacy_1min_roll_adjusted"
PROVENANCE_FILE = "vendor_legacy_1min_roll_adjusted_20260711.json"
# justify: bootstrap p-value MC SE ≈ sqrt(p(1-p)/B); at B=1000 SE ≤ 0.0158, 0.0069 at 0.05.
N_BOOTSTRAP = 1000
# justify: rotor-percentile MC SE ≈ sqrt(p(1-p)/B); at B=2000 SE ≤ 0.0112, 0.0049 at 0.05.
N_ROTORS = 2000
ALPHA = 0.05  # justify: descriptive CI level; binding FWER = deferred screening target
_N_INSTRUMENTS_FAMILY = 2  # justify: ES+NQ → Šidák union exponent = family count (design §5B)
# justify: full RC-H101-1 same-ledger surface folded into DSR N_trials (design §8, its N_trials).
_RC_H101_1_PRIOR_TRIALS = 10
# justify: 1.0 H054 §9.2 ES-anchor power floor (design §8). This is the ES anchor ONLY; the
# per-instrument n_ES/n_NQ re-derivation from each instrument's own effect/variance is a
# certified-run step, DEFERRED (retrospective power forbidden). Used here as a lower-bound
# sample-size check, not the certified per-instrument floor.
_POWER_FLOOR_ES_ANCHOR = 174
_NY = ZoneInfo("America/New_York")
_RTH_OPEN = time(9, 30)
_MIN_CELL_N = 2  # justify: ddof=1 sample-variance minimum; structural, not a threshold
_EPS = 1e-12  # justify: structural div-by-zero guard, not a tunable threshold
_HMM_N_STATES = 4  # justify: H900 winning model = 4-state diagonal-Gaussian HMM
_HMM_COV = "diag"  # justify: H900 winning model covariance type
# justify: emission vector = (ret_5m, log_rvol); stress state = max log-rvol emission mean.
_STRESS_EMISSION_DIM = 1
_PRIMARY_CELL = "stress"  # justify: pre-registered primary cell (design §3)
_CELL_ORDER = ("unconditional", "stress", "non_stress", "first_hour_up", "first_hour_down")
# non-nested conditioning cells for the DSR cross-trial dispersion (excludes unconditional).
_SIGMA_CELLS = ("stress", "non_stress", "first_hour_up", "first_hour_down")


def _dataset_checksums(paths: ProjectPaths) -> dict[str, str]:
    """Per-file SHA-256 for the scan substrate from data/_manifest.json (ReproLog R1-E)."""
    manifest = json.loads((paths.data / "_manifest.json").read_text(encoding="utf-8"))
    out = {k: e["sha256"] for k, e in manifest["files"].items() if DATASET in k}
    if not out:
        raise RuntimeError("no dataset checksums found in data/_manifest.json")
    return out


def _five_min_bars(paths: ProjectPaths, symbol: str) -> pl.DataFrame:
    """Load → registered exclusions → 5-minute aggregation (shared by covariates + HMM)."""
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
    return (
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


def _stress_occupancy(feats: pl.DataFrame) -> dict:
    """Fit the H900 4-state diag HMM on the full sample; return the stationary stress occupancy p̂.

    Descriptive full-sample fit (the leakage-clean per-rolling-origin train-window cutoff is
    the CERTIFIED-run version, deferred with the screening level — design §3/§6).
    """
    x = emission_matrix(feats)  # (T, 2) = [ret_5m, log_rvol_5m_24h]
    z = standardize(x, fit_moments(x))
    model = GaussianHMM(n_states=_HMM_N_STATES, covariance_type=_HMM_COV)
    # When restart_seeds is supplied, RNG determinism comes ENTIRELY from restart_seeds;
    # seed= is recorded on the FitResult but not consumed on this path (GaussianHMM.fit).
    model.fit(z, seed=HMM_SEED, restart_seeds=HMM_RESTART_SEEDS)
    means = model.params_.means  # (n_states, 2)
    stress = int(np.argmax(means[:, _STRESS_EMISSION_DIM]))
    trans = np.exp(model.params_.log_transmat)
    evals, evecs = np.linalg.eig(trans.T)
    # Perron-Frobenius stationary vector for eigenvalue 1. The eigenvector's sign is
    # arbitrary and (for a positive-recurrent chain) its entries share one sign, so take
    # |Re(·)| and normalize with an _EPS-guarded denominator; clip p̂ to [0,1] so eigen
    # numerics can never abort the downstream np.quantile(rvol, 1 − p̂).
    stat = np.abs(np.real(evecs[:, int(np.argmin(np.abs(evals - 1.0)))]))
    denom = float(stat.sum())
    # filter_states returns the (T, n_states) causal filtered posterior; the MAP label
    # is its per-bar argmax. Empirical MAP occupancy is a cross-check on the stationary p̂.
    emp = float((model.filter_states(z).argmax(axis=1) == stress).mean())
    p_hat = float(np.clip(stat[stress] / denom, 0.0, 1.0)) if denom > _EPS else emp
    return {
        "p_hat": p_hat,
        "stress_state": stress,
        "empirical_occupancy": emp,
        "stress_logrvol_mean_z": float(means[stress, _STRESS_EMISSION_DIM]),
        "n_bars": int(x.shape[0]),
    }


def _kelly1_gross_ledger(paths: ProjectPaths, symbol: str) -> pl.DataFrame:
    """Per-session pre-cost (gross) AND net-of-cost ORB return from the shared H101 k1.0 ledger.

    ``gross`` = sum of ledger ``ret_gross`` (the admission-scan primary, ADR-0002 pre-cost);
    ``net`` = sum of ledger ``ret_net`` (Tier-0 `futures_rt_v1` cost already applied, design
    §7) — used for the RC-XCORR-1 non-redundancy comparison (design §5(C)/§10 net-of-cost).
    """
    glob = str(
        paths.data_processed
        / "shadow_ledger"
        / "expert_id=orb_first_hour_k1.0@1.0.0"
        / f"asset={symbol}"
        / "**"
        / "part-0000.parquet"
    )
    lf = pl.scan_parquet(glob).select("session_date", "ret_gross", "ret_net")
    return (
        lf.group_by("session_date")
        .agg(
            gross=pl.col("ret_gross").sum(),
            net=pl.col("ret_net").sum(),
            n_active=(pl.col("ret_gross") != 0).sum(),
        )
        .sort("session_date")
        .collect()
    )


def _session_covariates(feats: pl.DataFrame) -> pl.DataFrame:
    """Per-session realized-vol proxy (rvol at RTH open) + first-hour RTH return sign."""
    feats = feats.filter(pl.col("emission_valid")).sort("ts_event")
    ts = feats.get_column("ts_event").to_list()
    close = feats.get_column("close").to_numpy()
    rvol = feats.get_column("rvol_5m_24h").to_numpy()
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
        if k == _DEFAULT_N_OR:
            rows[sd]["fh_sign"] = int(np.sign(close[i] - rows[sd]["or_open"]))
        n_rth[sd] = k + 1
    recs = [r for r in rows.values() if "fh_sign" in r and np.isfinite(r["rvol"])]
    return pl.DataFrame(recs).select("session_date", "rvol", "fh_sign")


def _cells(entered: np.ndarray, rvol: np.ndarray, fh: np.ndarray, p_hat: float) -> dict:
    """Pre-registered conditioning cells; STRESS = rvol percentile ≥ (1 − p̂) (design §3)."""
    cutoff = np.quantile(rvol, 1.0 - p_hat)  # top-p̂ band by realized-vol
    return {
        "unconditional": entered,
        "stress": entered & (rvol >= cutoff),  # PRIMARY (design §3)
        "non_stress": entered & (rvol < cutoff),
        "first_hour_up": entered & (fh > 0),
        "first_hour_down": entered & (fh < 0),
    }


def _hac_variance_inflation(x: np.ndarray) -> float:
    """HAC variance-inflation for the mean, Newey-West 1994 Bartlett bandwidth (≥ 1.0).

    Effective n = n / VIF implements the design §8 autocorrelation-adjusted (Lo-2002)
    Sharpe SE as a leading-order HAC approximation (same helper as RC-H101-1).
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

    pilot = max(int(4.0 * (n / 100.0) ** (2.0 / 9.0)), 1)
    s0 = g0 + 2.0 * sum(gamma(j) for j in range(1, pilot + 1))
    s1 = 2.0 * sum(j * gamma(j) for j in range(1, pilot + 1))
    if abs(s0) <= _EPS:
        return 1.0
    gamma_hat = 1.1447 * (((s1 / s0) ** 2) ** (1.0 / 3.0))
    m = min(max(int(gamma_hat * n ** (1.0 / 3.0)), 0), n - 1)
    lrv = g0 + 2.0 * sum((1.0 - j / (m + 1.0)) * gamma(j) for j in range(1, m + 1))
    return float(max(lrv / g0, 1.0))


def _kpss_stationarity(x: np.ndarray) -> dict:
    """KPSS stationarity, both variants (design §8(a)); level 'c' is the primary read."""
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]

    def _one(reg: str) -> dict:
        with warnings.catch_warnings():
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
    return {
        "level": level,
        "trend": _one("ct"),
        "stat": level["stat"],
        "reject_stationarity_5pct": level["reject_stationarity_5pct"],
    }


def _cell_sharpe(v: np.ndarray) -> float:
    """Per-session-unit Sharpe; nan for a degenerate constant cell (drops from sigma pool)."""
    v = v[np.isfinite(v)]
    if v.size < _MIN_CELL_N:
        return float("nan")
    sd = v.std(ddof=1)
    return float(v.mean() / sd) if sd > _EPS else float("nan")


def _sharpe(x: np.ndarray) -> float:
    """Per-period Sharpe (mean/std, ddof=1); 0.0 for a degenerate zero-variance series."""
    s = x.std(ddof=1)
    return float(x.mean() / s) if s > _EPS else 0.0


def _rc_xcorr1(h103: np.ndarray, h101: np.ndarray) -> dict:
    """RC-XCORR-1 per-instrument non-redundancy vs H101 on NET-OF-COST series (design §5(C)/§10).

    H103 net series = the ORB net-of-cost masked to stress sessions (flat/0 on non-stress —
    the realizable H103 strategy); H101 net series = the unconditional ORB net-of-cost. Both
    are per-session over the common entered-session index. Reports:
    - the per-session net return correlation;
    - the **marginal contribution to ensemble Sharpe** as the mean-variance / Grinold result:
      adding H103 to a portfolio already holding H101 improves the maximum attainable Sharpe
      iff SR_103 > corr · SR_101 (the covariance-DERIVED non-redundancy bound, §10(iii), never
      a fixed constant); the residual (appraisal) ratio is the marginal magnitude
      (Grinold 1989 marginal IR).

    Only the design §10(iii) "marginal IR positive" branch is exercised; the alternative "OR
    residual correlation below the ensemble-variance-budget bound" branch is NOT separately
    computed — this makes the gate strictly STRICTER than the pre-registered rule
    (conservative), so it cannot flip a null; the full branch is a certified-run refinement.
    """
    m = np.isfinite(h103) & np.isfinite(h101)
    a, b = h103[m], h101[m]
    ok = a.size >= _MIN_CELL_N and a.std() > _EPS and b.std() > _EPS
    corr = float(np.corrcoef(a, b)[0, 1]) if ok else float("nan")
    sr_h103 = _sharpe(a)
    sr_h101 = _sharpe(b)
    # Grinold marginal IR = the residual (appraisal) ratio of H103 after projecting out
    # H101: (SR_103 − corr·SR_101) / sqrt(1 − corr^2). This is the long-only-relevant
    # marginal contribution to the ensemble IR given H101 is held — positive iff
    # SR_103 > corr·SR_101 (the covariance-DERIVED non-redundancy bound, §10(iii), never a
    # fixed constant). (SR_opt − SR_101 was rejected as the metric: the unconstrained
    # tangency can short a negative-Sharpe leg, giving a misleading "improvement".)
    bound = float(corr * sr_h101) if np.isfinite(corr) else float("nan")
    if np.isfinite(corr) and abs(corr) < 1.0 - _EPS:
        residual_ir = float((sr_h103 - corr * sr_h101) / np.sqrt(1.0 - corr**2))
    else:
        residual_ir = float("nan")
    # The marginal-IR-add premise is only well-posed when H101 is rationally held
    # (SR_101 > 0); with a net-negative base leg a less-negative SR_103 can clear the
    # (negative) bound and give a spurious "adds". Gate on both.
    base_held = sr_h101 > 0.0
    return {
        "basis": "net_of_cost",
        "return_correlation": corr,
        "sharpe_h101": sr_h101,
        "sharpe_h103": sr_h103,
        "base_net_positive": bool(base_held),
        "nonredundancy_bound_corr_x_sr101": bound,  # SR_103 must exceed this to add
        "residual_information_ratio": residual_ir,  # Grinold marginal IR (appraisal ratio)
        "adds_marginal_ir": bool(np.isfinite(residual_ir) and residual_ir > 0.0 and base_held),
        "n_aligned_sessions": int(a.size),
    }


def _bootstrap_ci(x: np.ndarray, *, block_length: float, rng: np.random.Generator) -> dict:
    """Stationary block-bootstrap percentile CI on the mean of a per-session series (design §8)."""
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]
    if x.size < _MIN_CELL_N:
        return {"lo": float("nan"), "hi": float("nan")}
    boot = np.empty(N_BOOTSTRAP, dtype=np.float64)
    for b in range(N_BOOTSTRAP):
        idx = stationary_bootstrap_indices(x.size, block_length=block_length, rng=rng)
        boot[b] = x[idx].mean()
    lo, hi = np.quantile(boot, [ALPHA / 2.0, 1.0 - ALPHA / 2.0])
    return {"lo": float(lo), "hi": float(hi)}


def _ledoit_wolf_pairwise(net: np.ndarray, entered: np.ndarray, cells: dict) -> dict:
    """Ledoit-Wolf studentized paired Sharpe comparison — the anti-gate differential (design §8).

    Compares the STRESS cell's per-session net Sharpe against the complement (non_stress) and
    the unconditional cell, on the realizable H103 series (net masked to each cell, 0 elsewhere,
    over the common entered-session index) so the legs are paired and algebraically dependent.
    """

    def _masked(cell: str) -> np.ndarray:
        return np.where(entered & np.isfinite(net), np.where(cells[cell], net, 0.0), np.nan)

    stress = _masked("stress")
    out = {}
    for other in ("non_stress", "unconditional"):
        a = stress[np.isfinite(stress) & np.isfinite(_masked(other))]
        b = _masked(other)[np.isfinite(stress) & np.isfinite(_masked(other))]
        if a.size < _MIN_CELL_N:
            out[f"stress_vs_{other}"] = None
            continue
        # block_length=None → the estimator PW-auto-selects on ITS OWN paired influence
        # series u_t (design §8), rather than borrowing the unconditional-gross block length.
        res = sharpe_ratio_difference_test(
            a,
            b,
            block_length=None,
            rng=np.random.default_rng(SEED + 3),
            n_bootstrap=N_BOOTSTRAP,
        )
        out[f"stress_vs_{other}"] = {
            "sharpe_diff": res.sharpe_diff,
            "studentized_stat": res.studentized_stat,
            "p_value": res.p_value,
            "ci_low": res.ci_low,
            "ci_high": res.ci_high,
        }
    return out


def run_scan(paths: ProjectPaths, symbol: str) -> dict:
    """RC-H103-1 scan for one instrument: p̂ → stress cell → confirmation ladder.

    Returns
    -------
    dict
        ``instrument``, ``n_sessions``, ``n_nonfinite_excluded``; ``hmm_stress_occupancy``
        (p̂ / stress_state / empirical occupancy); ``stress_cutoff_rvol_quantile``;
        ``block_length``; ``cells`` (per-cell n / mean_gross / sharpe / RW stat+adj-p+reject);
        ``primary`` (stress-cell sr / n / n_eff / VIF / skew / kurtosis for the scan-level DSR);
        ``rotor_stress`` (stress-restricted matched-turnover rotor); ``kpss``; ``precision_gate``
        (§8 25% report-eligibility CI); ``ledoit_wolf_anti_gate`` (stress-vs-complement /
        -unconditional paired Sharpe comparison); ``rc_xcorr1`` (net-of-cost non-redundancy vs
        H101); ``power_floor``. ``deflated_sharpe`` is attached out-of-band by ``_scan_dsr``.
    """
    feats = compute_emissions(_five_min_bars(paths, symbol))
    occ = _stress_occupancy(feats)
    p_hat = occ["p_hat"]

    ledger = _kelly1_gross_ledger(paths, symbol)
    covs = _session_covariates(feats)
    df = ledger.join(covs, on="session_date", how="inner").sort("session_date")
    nulls = df.select(pl.col("gross", "net", "rvol", "fh_sign").null_count()).row(0)
    if any(nulls):
        raise RuntimeError(
            f"[{symbol}] unexpected nulls post-join: gross/net/rvol/fh_sign = {nulls}"
        )
    gross = df.get_column("gross").to_numpy().astype(np.float64)
    net = df.get_column("net").to_numpy().astype(np.float64)
    entered = df.get_column("n_active").to_numpy() > 0
    rvol = df.get_column("rvol").to_numpy().astype(np.float64)
    fh = df.get_column("fh_sign").to_numpy().astype(np.float64)
    n_nonfinite = int((~np.isfinite(gross) & entered).sum())  # Tier-0 ruin (-inf) diagnostic
    entered = entered & np.isfinite(gross) & np.isfinite(net)

    cells = _cells(entered, rvol, fh, p_hat)
    cell_names = list(_CELL_ORDER)
    masks = np.vstack([cells[c] for c in cell_names])

    rng = np.random.default_rng(SEED)
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

    per_cell = []
    for i, c in enumerate(cell_names):
        v = gross[cells[c]]
        vf = v[np.isfinite(v)]
        per_cell.append(
            {
                "cell": c,
                "n": int(cells[c].sum()),
                "mean_gross": float(vf.mean()) if vf.size else float("nan"),
                "sharpe": _cell_sharpe(v),
                "stat": float(rw.stat[i]),
                "rw_adj_pvalue": float(rw.adjusted_pvalue[i]),
                "rejected_descriptive": bool(rw.rejected[i]),
            }
        )

    # Primary (stress) cell DSR inputs: HAC effective n.
    prim = gross[cells[_PRIMARY_CELL]]
    prim = prim[np.isfinite(prim)]
    vif = _hac_variance_inflation(prim)
    n_eff = max(int(round(prim.size / vif)), _MIN_CELL_N) if prim.size >= _MIN_CELL_N else prim.size
    sd = prim.std() if prim.size else 0.0
    skew = float(((prim - prim.mean()) ** 3).mean() / (sd**3 + _EPS)) if prim.size else 0.0
    kurt = float(((prim - prim.mean()) ** 4).mean() / (sd**4 + _EPS)) if prim.size else 3.0

    # Matched-turnover rotor restricted to STRESS sessions (design §7).
    stress_gross = gross[cells[_PRIMARY_CELL]]
    stress_gross = stress_gross[np.isfinite(stress_gross)]
    if stress_gross.size >= _MIN_CELL_N:
        r = matched_turnover_rotor(
            stress_gross,
            np.ones(stress_gross.size, dtype=bool),
            n_rotors=N_ROTORS,
            rng=np.random.default_rng(SEED + 1),
        )
        rotor = {
            "expert_mean": r.expert_mean,
            "expert_percentile": r.expert_percentile,
            "p_value": r.p_value,
        }
    else:
        _nan = float("nan")
        rotor = {"expert_mean": _nan, "expert_percentile": _nan, "p_value": _nan}

    # RC-XCORR-1 (NET-OF-COST, design §5(C)/§10): H103 = ORB net masked to stress sessions
    # (flat/0 elsewhere — the realizable H103 strategy); H101 = unconditional ORB net.
    h103_series = np.where(entered, np.where(cells[_PRIMARY_CELL], net, 0.0), np.nan)
    h101_series = np.where(entered, net, np.nan)
    xcorr = _rc_xcorr1(h103_series, h101_series)

    # §8 precision gate + stress-cell gross-edge stationary-bootstrap CI. The gate is
    # report-eligibility: CI half-width < 25% of |point estimate| (design §8; the 25%
    # fraction is the inherited H900/H001 CONSORT-style reporting convention, not tuned).
    ci = _bootstrap_ci(prim, block_length=bl, rng=np.random.default_rng(SEED + 2))
    point = float(prim.mean()) if prim.size else float("nan")
    half_width = (ci["hi"] - ci["lo"]) / 2.0 if np.isfinite(ci["lo"]) else float("nan")
    precision = {
        "point_estimate_mean_gross": point,
        "ci_low": ci["lo"],
        "ci_high": ci["hi"],
        "half_width": half_width,
        "half_width_over_point": (
            float(half_width / (abs(point) + _EPS)) if np.isfinite(half_width) else float("nan")
        ),
        "meets_25pct_precision_gate": bool(
            np.isfinite(half_width) and half_width < 0.25 * abs(point)
        ),
    }

    # Ledoit-Wolf studentized pairwise Sharpe comparison — the anti-gate differential
    # (stress vs complement), design §8. Algebraically-dependent legs → paired studentized
    # bootstrap over the aligned per-session series (net-of-cost, the realizable strategy).
    lw = _ledoit_wolf_pairwise(net, entered, cells)

    return {
        "instrument": symbol,
        "n_sessions": int(entered.sum()),
        "n_nonfinite_excluded": n_nonfinite,
        "hmm_stress_occupancy": occ,
        "stress_cutoff_rvol_quantile": float(1.0 - p_hat),
        "block_length": float(bl),
        "cells": per_cell,
        "primary": {
            "cell": _PRIMARY_CELL,
            "n": int(prim.size),
            "sharpe": _cell_sharpe(gross[cells[_PRIMARY_CELL]]),
            "hac_vif": float(vif),
            "n_eff": int(n_eff),
            "skew": skew,
            "kurtosis": kurt,
        },
        "rotor_stress": rotor,
        "kpss": _kpss_stationarity(gross[cells[_PRIMARY_CELL]]),
        "precision_gate": precision,
        "ledoit_wolf_anti_gate": lw,
        "rc_xcorr1": xcorr,
        "power_floor": {
            "stress_trade_count": int(prim.size),
            "es_anchor_floor": _POWER_FLOOR_ES_ANCHOR,
            # design §8: n≥174 is the ES anchor (1.0 H054 §9.2); the per-instrument
            # freeze-time power-analysis re-derivation of n_ES/n_NQ from each instrument's
            # OWN stress-cell effect/variance is DEFERRED (retrospective power forbidden,
            # Hoenig & Heisey 2001). exceeds_es_anchor is a LOWER-BOUND sample-size check
            # only — NOT the per-instrument certified floor.
            "exceeds_es_anchor": bool(prim.size >= _POWER_FLOOR_ES_ANCHOR),
            "per_instrument_floor_derivation": "deferred (certified-run; not ES-transported)",
        },
    }


def _scan_dsr(results: list[dict]) -> None:
    """Attach the DSR per instrument; N_trials includes the full RC-H101-1 prior surface (§8)."""
    n_trials = len(results) * len(_CELL_ORDER) + _RC_H101_1_PRIOR_TRIALS
    pooled = []
    for r in results:
        by_cell = {c["cell"]: c["sharpe"] for c in r["cells"]}
        pooled.extend(by_cell[c] for c in _SIGMA_CELLS if np.isfinite(by_cell.get(c, np.nan)))
    sr_std = float(np.std(pooled, ddof=1)) if len(pooled) > 1 else float("nan")
    for r in results:
        p = r["primary"]
        if p["n"] >= _MIN_CELL_N and np.isfinite(sr_std) and sr_std > _EPS:
            dsr = deflated_sharpe_ratio(
                p["sharpe"], p["n_eff"], n_trials, sr_std, skew=p["skew"], kurtosis=p["kurtosis"]
            )
            r["deflated_sharpe"] = {
                "dsr": dsr.dsr,
                "sr_observed": dsr.sr_observed,
                "sr_benchmark": dsr.sr_benchmark,
                "n_trials": n_trials,
                "sr_std_pooled": sr_std,
                "n_eff_hac": p["n_eff"],
            }
        else:
            r["deflated_sharpe"] = None


def _sidak_threshold(alpha: float, m_families: int) -> float:
    """Per-family Šidák level for the cross-instrument union (design §5(B))."""
    return 1.0 - (1.0 - alpha) ** (1.0 / m_families)


def _disposition(results: list[dict]) -> str:
    """§10 disposition — provisional (edge side descriptive; RC-XCORR-1 gate reported).

    admit-conditional requires, on some instrument: stress mean gross > 0 AND per-instrument
    Romano-Wolf-adjusted p ≤ the Šidák per-family level AND the stress cell beats its rotor AND
    RC-XCORR-1 clears (positive marginal Sharpe over H101). Absent a positive stress edge the
    disposition is provisional-archive-null (held descriptive — screening level deferred, per
    the RC-H101-1 precedent). When RC-XCORR-1 additionally fails on ALL instruments
    (H103 spanned by H101), the redundant-with-H101 leg is flagged.
    """
    sidak = _sidak_threshold(ALPHA, _N_INSTRUMENTS_FAMILY)
    for r in results:
        prim = next(c for c in r["cells"] if c["cell"] == _PRIMARY_CELL)
        rotor_p = r["rotor_stress"]["p_value"]
        beats_rotor = np.isfinite(rotor_p) and rotor_p < ALPHA
        adds = bool(r["rc_xcorr1"].get("adds_marginal_ir"))
        if prim["mean_gross"] > 0 and prim["rw_adj_pvalue"] <= sidak and beats_rotor and adds:
            return "admit-conditional (DESCRIPTIVE; screening level deferred, not certified)"
    redundant = all(not r["rc_xcorr1"].get("adds_marginal_ir") for r in results)
    tail = (
        " + redundant-with-H101 (RC-XCORR-1: non-positive residual IR over H101)"
        if redundant
        else ""
    )
    return (
        "provisional-archive-null (no descriptive positive stress-cell edge; held descriptive, "
        f"screening level deferred, not archived){tail}"
    )


def main() -> int:
    """ReproLog → per-instrument scan → DSR → Šidák-union disposition → JSON artifact."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instruments", default="ES,NQ")
    parser.add_argument("--out", default="reports/H103")
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    out_dir = paths.root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    instruments = tuple(s.strip() for s in args.instruments.split(","))

    design_path = paths.root / "research/01_hypothesis_register/H103/design.md"
    design_sha = hashlib.sha256(design_path.read_bytes()).hexdigest()
    log = reproducibility.capture(
        phase="rc-h103-1-admission-scan",
        hypothesis_id="H103",
        rng_seed=SEED,
        dataset_checksums=_dataset_checksums(paths),
        config_resolved_sha256=design_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (H103 design SHA {design_sha[:12]}...)", flush=True)

    results = [run_scan(paths, s) for s in instruments]
    _scan_dsr(results)
    disposition = _disposition(results)
    sidak = _sidak_threshold(ALPHA, _N_INSTRUMENTS_FAMILY)
    blob = {
        "scan": "RC-H103-1",
        "hypothesis_id": "H103",
        "disposition": disposition,
        "decision_rule": (
            "DESCRIPTIVE ADR-0002(c) scan: primary = STRESS cell (rvol percentile ≥ 1−p̂, "
            "p̂ = H900 HMM stationary stress occupancy per instrument). Descriptive positive iff "
            "stress mean gross > 0 AND per-instrument Romano-Wolf-adjusted p ≤ the Šidák "
            f"cross-instrument per-family level ({sidak:.4f} at ALPHA={ALPHA}) AND the stress cell "
            "beats its stress-restricted matched-turnover rotor. The binding FWER/screening level "
            "is the DEFERRED screening_error_rate_target — no cell CERTIFIED until it is set "
            "(design §5(B)/§8/§10). PBO DEFERRED (design §3.5), not waived. RC-XCORR-1 "
            "non-redundancy vs H101 is a MANDATORY per-instrument admission gate (reported here)."
        ),
        "seed": SEED,
        "hmm_seed": HMM_SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "n_rotors": N_ROTORS,
        "sidak_per_family_level_at_alpha": sidak,
        "repro_log": log_path.name,
        "instruments": results,
    }
    (out_dir / "rc_h103_1_scan.json").write_text(
        json.dumps(blob, indent=2, sort_keys=True, default=str), encoding="utf-8"
    )
    print(f"[RC-H103-1] disposition: {disposition}", flush=True)
    for r in results:
        prim = next(c for c in r["cells"] if c["cell"] == _PRIMARY_CELL)
        rp = r["rotor_stress"]["p_value"]
        dsr = r["deflated_sharpe"]
        dsr_str = f"{dsr['dsr']:.3f}" if dsr else "n/a"
        occ = r["hmm_stress_occupancy"]
        xc = r["rc_xcorr1"]
        lw = r["ledoit_wolf_anti_gate"].get("stress_vs_non_stress") or {}
        lw_p = lw.get("p_value", float("nan"))
        prec = r["precision_gate"]["meets_25pct_precision_gate"]
        print(
            f"  {r['instrument']}: p_hat={occ['p_hat']:.3f} stress n={prim['n']} "
            f"mean_gross={prim['mean_gross']:.2e} rw_adj_p={prim['rw_adj_pvalue']:.3f} "
            f"rotor_p={rp:.3f} DSR={dsr_str} | xcorr={xc['return_correlation']:.3f} "
            f"resid_IR={xc['residual_information_ratio']:+.4f} adds={xc['adds_marginal_ir']} "
            f"| LW(stress-vs-calm)_p={lw_p:.3f} prec25={prec}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
