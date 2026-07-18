"""P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE — on-ledger NUMERIC instantiation.

Instantiates the frozen discovery-alpha cost calibration
(docs/methodology/discovery_alpha_cost_calibration_2026-07-12.md; reference
estimator src/skie_universe2/inference/discovery_alpha.py) on the populated
ADR-0003 shadow ledger, producing the deferred numeric outputs:

  - the RD1/RD2 loss ratio ``lambda`` per band point (with a
    stationary-bootstrap CI on the enacted level),
  - the RD3 base-rate band ``pi1`` (exploration hit rate primary; Storey /
    Efron reported with the memo's mis-specified-null red flag),
  - the RD4 Bayes cutoff ``t*`` — THE ENACTED LEVEL — plus the two FDR
    reporting bridges (empirical and model-side implied screening FDR),
  - the RD5 FWER-vs-FDR criterion decision over the registered family sizes,
  - the RD6 TOST diagnostic triple (recorded; consumed by the ADR-0010 ramp
    only at Phase 5).

The METHOD is frozen (2026-07-12) and is not re-derived here; this script only
supplies the on-ledger inputs the memo declared as deferred OUTPUTs (RD6 table)
and records the enacted values. Per the memo every input is data-derived:

  - **false-edge substrate** = the DEMEANED realized per-session NET return
    stream of the ledger's null expert (``orb_first_hour_k1.0@1.0.0``;
    RC-H101-1/RC-H103-1 dispositioned provisional-archive-null) — a genuinely
    ZERO-edge, fat-tailed allocator-arm with the realized higher moments (the
    memo's "zero/neg-edge" canonical case; its sizing damage is the variance
    drag, keeping L_FD > 0 and lambda finite). The RAW (un-demeaned) streams
    are reported as sensitivity: the ES raw mean is negative (larger L_FD,
    tighter level) and the NQ raw mean is weakly positive (L_FD -> 0,
    lambda -> inf — a costless false discovery), bracketing the primary.
  - **true-edge substrate** = the same stream mean-shifted to the DSR deflation
    benchmark Sharpe (the selection-adjusted null expectation from the
    register's own trial records) — the MINIMUM edge the program can
    distinguish from selection luck; preserves the realized higher moments.
    ``mu`` (two-groups z-shift) is the same anchor:
    ``mu = sr_benchmark * sqrt(n_eff)``.
  - **H_dwell** (champion-dwell horizon) = entered sessions per ADR-0004
    6-month rolling-origin evaluation window (median over the ledger windows);
    the enacted point is the structural 1-window floor (ADR-0012 dwell floor is
    not yet calibrated; 1 window is the minimum a champion can hold by
    construction and is CONSERVATIVE for lambda — it under-states L_MD).
    {1, 2, 4} windows are reported as a sensitivity doubling band.
  - **H_dem** (demotion latency) = an ASSUMPTION AXIS, banded {1, 2, 4}
    evaluation windows. One window is the re-adjudication cadence FLOOR, but
    demotion of a false champion at the next cycle is NOT certain — the
    ADR-0012 dethroning rule is non-operational (its margin/dwell memo is
    unfrozen) and a zero-edge champion is only demoted when the cycle's
    evidence resolves it — so the exposure horizon is uncertain and is priced
    into the ENACTMENT band rather than fixed at its floor (audit round 1,
    QUANT-1-3: fixing H_dem at 1 window UNDER-states L_FD and is
    anti-conservative for lambda). The Schuirmann-TOST powered window is
    reported as the RD6 diagnostic only.
  - **r_backstop** = a PRIOR/ASSUMPTION AXIS, banded {0, 0.3332}. The
    project's realized record (2/2 nulls caught by the DSR / rotor /
    Romano-Wolf stack) is structurally CENSORED — a null that slipped the
    gates would be recorded as an admission, not a miss, so k = n is
    mechanical and the record carries almost no information about
    P(reject | null) (audit round 1, QUANT-1-4). The band spans r = 0 (the
    no-information anchor: no backstop credit, lambda = H_dwell x g /
    (H_dem x drag)) to r = 0.3332 (the lower endpoint of the Jeffreys
    central 95% interval on the censored record — Beta(k+1/2, n-k+1/2)
    2.5th percentile; an optimistic-but-recorded reading). Non-circular
    either way (no dependence on the level being derived; the earlier
    fixed-point construction coupling r_backstop to the output level is
    REMOVED — at the pi1 -> 0 boundary its implied-FDR translation is
    provably discontinuous, so no fixed point exists there). The
    re-instantiation condition (memo addendum §A.8) replaces this prior with
    live-vs-shadow outcome data once an admitted expert accrues it — the
    only design that can observe a gate miss.
  - **dependence_inflation** (RD5) = ``1 + (N-1) * rho_bar`` with ``rho_bar``
    the mean pairwise correlation of the per-session conditioning-cell return
    series on the ledger (the effective-tests shrinkage under equicorrelation).
  - **prds_defensible** (RD5) = an EMPIRICAL check: non-negative pairwise
    correlations are a SUFFICIENT condition for PRDS of one-sided tests on
    jointly-Gaussian-approximated cell statistics (Benjamini-Yekutieli 2001
    §3.1, multivariate-normal example); decided from the measured cell
    correlation matrix, not asserted.

Enactment rule (stated ex ante). The ENACTED ``screening_error_rate_target``
is the RD4 Bayes cutoff ``t*`` (Muller-Parmigiani-Robert-Rousseau
posterior-null cutoff; the memo's primary RD4 decision object, and pi1-FREE
per the memo), aggregated as the MEDIAN over the ENACTMENT BAND = instrument
x same-instrument mu-anchor x H_dem in {1, 2, 4} windows x r_backstop in
{0, 0.3332}, all at the 1-window CHAMPION-DWELL floor (the H_dwell 2x/4x
multiples remain reported sensitivity: dwell above the floor only raises
L_MD and loosens the level, and the floor is the only structurally
guaranteed dwell while the ADR-0012 dwell memo is unfrozen). The band's two
assumption axes price the round-1 audit findings QUANT-1-3 (uncertain
demotion latency) and QUANT-1-4 (censored backstop record) into the level
rather than fixing either at a point. SCALE TRANSFER (documented deviation,
memo addendum §A.6): t* lives on the posterior-null / local-fdr scale; its
enactment as the Romano-Wolf adjusted-p threshold and as the DSR/PBO bounds
is a GOVERNANCE choice under the ADR-0013 cost-tuned-looser mandate — an
operational proxy, NOT a claimed statistical identity between scales — and
is re-derived on a non-degenerate lfdr estimator at the §A.8
re-instantiation. The memo's RD6 implied-FDR arrow is reported as a bridge,
not enacted: the empirical bridge on the current 14-trial population admits
ALL 14 trials (every Efron lfdr from the degenerate n=14 Lindsey fit is
0.016-0.196 < t*, so the bridge returns their mean = the Efron pi0 = 0.0885)
and is untrustworthy because that same fit implies pi1 ~ 0.91 against the
RD3 factor-zoo red flag; the model bridge is separately discontinuous at
pi1 -> 0. Analytic cross-check: for small near-Gaussian per-session returns,
``lambda ~ (H_dwell/H_dem) x 4/(1 - r)`` (operating-Kelly growth SR^2/2 over
half-Kelly variance drag SR^2/8); at H_dwell = H_dem, r = 0.3332 this gives
lambda ~ 6.0, t* ~ 0.857 — the estimator's on-ledger values are validated
against this benchmark. The RD5 criterion is evaluated at the enacted level.
Nothing in this run certifies any admission and no Kelly fraction is
selected.

Usage:
    uv run python scripts/run_discovery_alpha_calibration.py
        [--out reports/discovery_alpha_calibration]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
from scipy.stats import beta as beta_dist
from scipy.stats import norm

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

import polars as pl  # noqa: E402

from skie_universe2.inference.bootstrap import (  # noqa: E402
    politis_white_block_length,
    stationary_bootstrap_indices,
)
from skie_universe2.inference.discovery_alpha import (  # noqa: E402
    LossModel,
    TwoGroupsModel,
    build_loss_model,
    efron_local_fdr,
    fwer_vs_fdr_decision,
    implied_screening_fdr,
    optimal_threshold,
    storey_pi0,
    two_groups_lfdr_gaussian,
)
from skie_universe2.inference.kelly_growth import full_kelly_leverage, growth_rate  # noqa: E402
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

# justify: pre-registered date-seed, project scan convention (RC-H101-1 used 20260716).
SEED = 20260717
# justify: k1.0 = unit position -> gross/net in per-unit currency.
LEDGER_EXPERT = "orb_first_hour_k1.0@1.0.0"
INSTRUMENTS = ("ES", "NQ")  # justify: the populated ledger universe (backfill_admission_plan §3)
# justify: bootstrap CI replication count — matches the RC-H101-1/RC-H103-1 scan
# convention (N=1000; MC SE of a percentile bound <= 0.0158 at p=0.5).
N_BOOTSTRAP = 1000
# justify: two-sided nominal 95% coverage (reporting convention, kelly_growth default).
CI_ALPHA = 0.05
# justify: ADR-0004/H101-design §6 registered rolling-origin step — 6 calendar months.
EVAL_WINDOW_MONTHS = 6
# justify: sensitivity doubling band around the structural 1-window champion-dwell
# floor (ADR-0012 dwell floor uncalibrated; enacted point = the 1-window floor —
# the only structurally guaranteed dwell; 2x/4x reported as sensitivity only,
# since larger dwell only raises L_MD and loosens the level).
DWELL_WINDOW_MULTIPLES = (1, 2, 4)
# justify: ENACTMENT-band demotion-latency axis (audit QUANT-1-3): demotion at
# the next evaluation cycle is not certain (ADR-0012 dethroning non-operational),
# so the exposure horizon is banded over 1/2/4 re-adjudication cycles rather
# than fixed at the 1-cycle floor.
H_DEM_WINDOW_MULTIPLES = (1, 2, 4)
# justify: ADR-0013 Decision 3 registered Kelly grid; f_min = grid minimum (the
# RD2/RD6 "minimum live fraction"), operating fractions = the full grid.
KELLY_GRID = (0.5, 0.75, 1.0, 1.25)
F_MIN = min(KELLY_GRID)
# justify: the project's realized record of the non-waivable gates on null
# candidates: RC-H101-1 and RC-H103-1 (both nulls, both caught) -> k = n = 2.
BACKSTOP_RECORD = {"n_null_candidates": 2, "n_rejected_by_gates": 2}
_EPS = 1e-12  # justify: structural div-by-zero guard
# justify: shared-cell stat identity tolerance across the two scan artifacts
# (float-repr round-trip only; the cells are computed from the same ledger).
_STAT_IDENTITY_TOL = 1e-9
# justify: registered family sizes for the RD5 criterion sweep: 5 = per-instrument
# within-scan cell family (RC-H101-1/RC-H103-1 design); 10 = per-scan (2 instruments);
# 20 = the register's current DSR trial surface (RC-H103-1); 40 = pool-augmented
# projection (ADR-0014 Decision 4, one re-adjudication cycle); 100/400/2000 = the
# projected confirmation-tier (config x Kelly-fraction) family growth, reported so
# the crossover N* is visible before that family exists.
FAMILY_SIZES = (5, 10, 20, 40, 100, 400, 2000)
_MIN_CELL_N = 2  # justify: ddof=1 sample-variance minimum; structural


# ---------------------------------------------------------------------------
# Ledger + register inputs
# ---------------------------------------------------------------------------


def _dataset_checksums(paths: ProjectPaths) -> dict[str, str]:
    """Shadow-ledger partition SHA-256s for the calibration substrate (ReproLog).

    The full per-partition checksum map (~4.8k partitions per instrument for
    the k1.0 expert) is collapsed to a single SHA-256 over the sorted
    (path, frame_sha256) roll-up records of the k1.0 partitions, plus the
    scan-artifact hashes.
    """
    rollups = paths.data_processed / "shadow_ledger" / "_rollups" / "rollups.jsonl"
    digest = hashlib.sha256()
    n = 0
    with rollups.open(encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec["partition"]["expert_id"] == LEDGER_EXPERT:
                digest.update(rec["path"].encode())
                digest.update(rec["frame_sha256"].encode())
                n += 1
    if n == 0:
        raise RuntimeError(f"no roll-up records found for {LEDGER_EXPERT}")
    out = {f"shadow_ledger[{LEDGER_EXPERT}]({n} partitions)": digest.hexdigest()}
    for scan in ("H101/rc_h101_1_scan.json", "H103/rc_h103_1_scan.json"):
        p = paths.root / "reports" / scan
        out[f"reports/{scan}"] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def _per_session_net(paths: ProjectPaths, symbol: str) -> np.ndarray:
    """Per-session NET return of the realized null expert (entered sessions).

    The k1.0 ledger's ``ret_net`` summed per session over entered sessions
    (non-zero-return bars, the RC-H101-1 entry proxy); non-finite (ruin)
    sessions excluded with the same rule as the scans.
    """
    glob = str(
        paths.data_processed
        / "shadow_ledger"
        / f"expert_id={LEDGER_EXPERT}"
        / f"asset={symbol}"
        / "**"
        / "part-0000.parquet"
    )
    df = (
        pl.scan_parquet(glob)
        .select("session_date", "ret_net", "ret_gross")
        .group_by("session_date")
        .agg(
            net=pl.col("ret_net").sum(),
            n_active=(pl.col("ret_gross") != 0).sum(),
        )
        .sort("session_date")
        .collect()
    )
    x = df.filter(pl.col("n_active") > 0).get_column("net").to_numpy().astype(np.float64)
    x = x[np.isfinite(x)]
    if x.size < _MIN_CELL_N:
        raise RuntimeError(f"[{symbol}] degenerate entered-session net series (n={x.size})")
    return x


def _sessions_per_eval_window(paths: ProjectPaths, symbol: str) -> float:
    """Median entered sessions per 6-month rolling window on the ledger."""
    glob = str(
        paths.data_processed
        / "shadow_ledger"
        / f"expert_id={LEDGER_EXPERT}"
        / f"asset={symbol}"
        / "**"
        / "part-0000.parquet"
    )
    df = (
        pl.scan_parquet(glob)
        .select("session_date", "ret_gross")
        .group_by("session_date")
        .agg(n_active=(pl.col("ret_gross") != 0).sum())
        .filter(pl.col("n_active") > 0)
        .sort("session_date")
        .collect()
    )
    dates = df.get_column("session_date").to_list()
    base = dates[0].year * 12 + (dates[0].month - 1)
    idx = np.array([((d.year * 12 + (d.month - 1)) - base) // EVAL_WINDOW_MONTHS for d in dates])
    counts = np.bincount(idx)
    counts = counts[counts > 0]
    return float(np.median(counts))


def _trial_population(paths: ProjectPaths) -> dict:
    """Confirmation-tier trial population from the two executed scan artifacts.

    Collects every per-cell studentized statistic from RC-H101-1 + RC-H103-1
    and de-duplicates the cells shared between the scans (identical (instrument,
    cell) with identical stat — the two scans share the same underlying ledger,
    so ``unconditional``/``first_hour_up``/``first_hour_down`` appear twice).
    One-sided p-values from the standard normal approximation to the
    studentized statistics (the memo's RD3 z-population convention).
    """
    stats: dict[tuple[str, str], float] = {}
    n_raw = 0
    benchmarks = []
    for scan in ("H101/rc_h101_1_scan.json", "H103/rc_h103_1_scan.json"):
        blob = json.loads((paths.root / "reports" / scan).read_text(encoding="utf-8"))
        for inst in blob["instruments"]:
            for cell in inst["cells"]:
                n_raw += 1
                key = (inst["instrument"], cell["cell"])
                if key in stats and abs(stats[key] - cell["stat"]) > _STAT_IDENTITY_TOL:
                    raise RuntimeError(f"shared cell {key} has divergent stats across scans")
                stats[key] = float(cell["stat"])
            ds = inst.get("deflated_sharpe")
            if ds:
                benchmarks.append(
                    {
                        "instrument": inst["instrument"],
                        "scan": blob["scan"],
                        "sr_benchmark": float(ds["sr_benchmark"]),
                        "n_eff": int(ds["n_eff_hac"]),
                        "n_trials": int(ds["n_trials"]),
                    }
                )
    z = np.array(sorted(stats.values()), dtype=np.float64)
    p = norm.sf(z)  # survival function (exact tail; avoids 1 - cdf cancellation)
    return {
        "z": z,
        "p": p,
        "n_raw": n_raw,
        "n_distinct": int(z.size),
        "keys": sorted(f"{k[0]}:{k[1]}" for k in stats),
        "benchmarks": benchmarks,
    }


# ---------------------------------------------------------------------------
# RD3 — pi1 band (reporting; the enacted t* is pi1-free per the memo)
# ---------------------------------------------------------------------------


def _pi1_band(trials: dict) -> dict:
    """Three-estimator pi1 band (RD3) with the small-N red flags recorded.

    - exploration hit rate: executed edge-bearing scans to date (H001, H101,
      H103) -> 0/3 admitted; Jeffreys (Beta(1/2,1/2)) central 95% interval.
      PRIMARY (the project's own record; consistent with the factor-zoo prior).
    - Storey-Tibshirani spline pi0 and Efron two-groups local fdr on the n=14
      correlated trial population: both blow past the factor-zoo prior — the
      memo's RD3 red flag for a mis-specified null at this tiny dependent N;
      REPORTED, excluded from any decision use.
    """
    n_admit, n_scans = 0, 3
    # justify: central 1 - CI_ALPHA credible interval endpoints + median of the
    # Jeffreys posterior (quantiles derived from CI_ALPHA, not restated).
    jeff_lo = float(beta_dist.ppf(CI_ALPHA / 2.0, n_admit + 0.5, n_scans - n_admit + 0.5))
    jeff_med = float(beta_dist.ppf(0.5, n_admit + 0.5, n_scans - n_admit + 0.5))
    jeff_hi = float(beta_dist.ppf(1.0 - CI_ALPHA / 2.0, n_admit + 0.5, n_scans - n_admit + 0.5))
    hit_rate = {
        "estimator": "exploration-hit-rate",
        "pi1": n_admit / n_scans,
        "jeffreys_95ci": [jeff_lo, jeff_hi],
        "jeffreys_median": jeff_med,
        "n_admitted": n_admit,
        "n_scans": n_scans,
        "enactment_band_member": True,
    }
    p = trials["p"]
    pi0_storey = storey_pi0(p)
    storey = {
        "estimator": "storey-tibshirani-spline",
        "pi0": float(pi0_storey),
        "pi1": float(1.0 - pi0_storey),
        "caveat": (
            f"n={p.size} correlated p-values; the spline pi0 clamps at 1/m -> "
            "pi1 ~ 0.93, far above the factor-zoo prior — the memo's RD3 "
            "mis-specified-null red flag; EXCLUDED from decision use"
        ),
        "enactment_band_member": False,
    }
    lfdr = efron_local_fdr(trials["z"])
    efron = {
        "estimator": "efron-lindsey-lfdr-mean",
        "pi0": float(np.mean(lfdr)),
        "pi1": float(1.0 - np.mean(lfdr)),
        "caveat": (
            f"n={trials['z'].size} correlated z-values; the Lindsey density is "
            "degenerate at this N and pi1 ~ 0.91 fails the factor-zoo "
            "cross-check (RD3 red flag); EXCLUDED from decision use"
        ),
        "enactment_band_member": False,
    }
    return {
        "estimators": [hit_rate, storey, efron],
        "factor_zoo_crosscheck": (
            "Harvey-Liu-Zhu 2016 (doi:10.1093/rfs/hhv059) and Harvey-Liu 2020 "
            "(doi:10.1111/jofi.12951) document a large null proportion among "
            "published factors; the hit-rate band (pi1 ~ 0 with a wide small-N "
            "upper bound) is CONSISTENT with that prior; Storey/Efron are not."
        ),
        "empirical_lfdr": lfdr.tolist(),
    }


# ---------------------------------------------------------------------------
# RD1/RD2 loss model -> RD4 t* (direct; no iteration)
# ---------------------------------------------------------------------------


def _jeffreys_backstop_lower() -> float:
    """Lower endpoint of the Jeffreys central 95% interval on the gate record.

    Beta(k + 1/2, n - k + 1/2) at its CI_ALPHA/2 (2.5th) percentile
    (Brown-Cai-DasGupta 2001 Jeffreys interval), at the project's record
    (k = n = 2: RC-H101-1, RC-H103-1 both null, both caught by the DSR /
    rotor / Romano-Wolf stack). The record is structurally CENSORED (a null
    that slipped the gates would surface as an admission, not a miss — audit
    QUANT-1-4), so this endpoint is a PRIOR-style optimistic reading, banded
    against the r = 0 no-information anchor in the enactment band; it is
    non-circular (no dependence on the level being derived).
    """
    k = BACKSTOP_RECORD["n_rejected_by_gates"]
    n = BACKSTOP_RECORD["n_null_candidates"]
    return float(beta_dist.ppf(CI_ALPHA / 2.0, k + 0.5, n - k + 0.5))


def _tost_powered_window(delta: float, sigma_te: float, alpha: float, beta: float) -> float:
    """Schuirmann-TOST powered window (sessions) for margin ``delta`` (RD6 DIAGNOSTIC).

    One-sided sample-size at level ``alpha``, power ``1-beta``:
    ``n = ((z_alpha + z_beta) * sigma_te / delta)^2`` (Schuirmann 1987).
    Degenerate at ``alpha`` (or ``beta``) >= 0.5 (the z-quantiles vanish);
    returns ``nan`` there — a reported diagnostic for the ADR-0010 ramp,
    never the loss model's ``H_dem`` input.
    """
    z_a = float(norm.isf(alpha))
    z_b = float(norm.isf(beta))
    if z_a + z_b <= 0.0:
        return float("nan")
    return float(((z_a + z_b) * sigma_te / max(delta, _EPS)) ** 2)


def _band_point(
    false_net: np.ndarray,
    *,
    sr_bench: float,
    h_dwell_sessions: float,
    h_window_sessions: float,
    r_backstop: float,
    operating_fraction: float,
    h_dem_multiple: float = 1.0,
    controls_in_force: bool = True,
) -> tuple[LossModel, dict]:
    """RD1/RD2 loss model and RD4 cutoff at one band point (direct, no iteration).

    True-edge stream = false-edge stream mean-shifted to the DSR benchmark
    Sharpe (preserves realized higher moments). ``H_dem`` =
    ``h_dem_multiple`` re-adjudication cycles (the enactment-band assumption
    axis; module docstring); under ``controls_in_force=False`` the RD2 bound
    is withheld AND the demotion latency reverts to the full dwell horizon
    (no demotion machinery), the memo's tighter-alpha fallback.
    """
    sd = float(false_net.std(ddof=1))
    sr_false = float(false_net.mean() / sd) if sd > _EPS else 0.0
    true_net = false_net + (sr_bench - sr_false) * sd
    b_star = full_kelly_leverage(true_net)
    g_bench = growth_rate(true_net, F_MIN * b_star, barrier="absorbing")
    # justify: H_dem = h_dem_multiple x one ADR-0004 evaluation window (the
    # re-adjudication cadence), floor 1 session; the multiple is the banded
    # assumption axis (QUANT-1-3). Controls-off: no demotion machinery -> full
    # dwell exposure.
    h_dem = (
        max(h_dem_multiple * h_window_sessions, 1.0)
        if controls_in_force
        else max(h_dwell_sessions, 1.0)
    )
    model = build_loss_model(
        true_net,
        false_net,
        operating_fraction=operating_fraction,
        min_live_fraction=F_MIN,
        champion_dwell_bars=h_dwell_sessions,
        demotion_latency_bars=h_dem,
        backstop_rejection_rate=r_backstop,
        controls_in_force=controls_in_force,
        b_star_true=b_star,
    )
    diag = {
        "sr_false": sr_false,
        "sr_bench_anchor": sr_bench,
        "b_star_true": float(b_star),
        "g_bench_per_session": float(g_bench),
        "sigma_te": sd,
        "h_dem_sessions": float(h_dem),
        "r_backstop": r_backstop,
        "t_star": optimal_threshold(model.loss_ratio),
    }
    return model, diag


def _implied_model_fdr(t_star: float, *, pi0: float, mu: float) -> float:
    """Model-side implied screening FDR at cutoff ``t*`` (REPORTING BRIDGE).

    Deterministic quadrature: E[lfdr | lfdr < t*] under the two-groups
    marginal density on a dense z grid (no RNG). Returns 0.0 when the
    admitted set is empty. Discontinuous at the pi1 -> 0 boundary (the
    admitted set flips between empty and everything), which is why this is a
    reported bridge and not the enacted level.
    """
    # justify: +/-10 SD covers both mixture components to < 1e-20 tail mass at
    # the largest anchor mu (~1.15); 20001 points -> 1e-3 z-step, quadrature
    # error far below the reported 1e-4 precision. Numerical grid, not tuned.
    z = np.linspace(-10.0, 10.0, 20001)
    lfdr = two_groups_lfdr_gaussian(z, pi0=pi0, mu=mu)
    f = pi0 * norm.pdf(z) + (1.0 - pi0) * norm.pdf(z, loc=mu)
    admitted = lfdr < t_star
    mass = float(np.trapezoid(f * admitted, z))
    if mass <= _EPS:
        return 0.0
    return float(np.trapezoid(f * admitted * lfdr, z) / mass)


# ---------------------------------------------------------------------------
# Dependence structure of the cell family (RD5 inputs)
# ---------------------------------------------------------------------------


def _load_scan_harness():
    """Import the RC-H101-1 harness module (single source of truth for cells).

    scripts/ is not a package (pyproject ``package = false``); the harness is
    loaded by file path so the EXACT registered cell construction
    (``_session_covariates`` + ``_cells``) is reused rather than re-implemented.
    """
    import importlib.util  # noqa: PLC0415 — deferred: only used to reuse the harness cells

    harness_path = _ROOT / "scripts" / "run_rc_h101_1_scan.py"
    spec = importlib.util.spec_from_file_location("rc_h101_harness", harness_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load the RC-H101-1 harness at {harness_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _cell_dependence(paths: ProjectPaths) -> dict:
    """Mean pairwise correlation of the per-session cell contribution series.

    Rebuilds the RC-H101-1 five-cell masks EXACTLY (reusing the harness's
    ``_session_covariates`` / ``_cells`` by module import) and measures the
    pairwise correlation matrix of the masked contribution series (a cell's
    sessions carry their gross return, non-members 0 — the view the joint RW
    bootstrap resamples). ``rho_bar`` (mean off-diagonal) feeds the RD5
    ``dependence_inflation = 1 + (N-1) rho_bar``; the minimum off-diagonal
    decides ``prds_defensible`` (non-negative correlations are SUFFICIENT
    for PRDS of one-sided tests on a multivariate normal —
    Benjamini-Yekutieli 2001 §3.1 multivariate-normal example; a materially
    negative pair forfeits the argument -> BY fallback).
    """
    harness = _load_scan_harness()
    rhos: list[float] = []
    min_rho = np.inf
    per_instrument = {}
    for symbol in INSTRUMENTS:
        ledger = harness._kelly1_gross_ledger(paths, symbol)
        covs = harness._session_covariates(paths, symbol)
        df = ledger.join(covs, on="session_date", how="inner").sort("session_date")
        gross = df.get_column("gross").to_numpy().astype(np.float64)
        entered = (df.get_column("n_active").to_numpy() > 0) & np.isfinite(gross)
        rvol = df.get_column("rvol").to_numpy().astype(np.float64)
        fh = df.get_column("fh_sign").to_numpy().astype(np.float64)
        cells = harness._cells(entered, rvol, fh)
        names = list(harness._CELL_ORDER)
        mat = np.vstack([np.where(cells[c], gross, 0.0) for c in names])
        corr = np.corrcoef(mat)
        iu = np.triu_indices_from(corr, k=1)
        off = corr[iu]
        rhos.extend(off.tolist())
        min_rho = min(min_rho, float(off.min()))
        per_instrument[symbol] = {
            "cells": names,
            "rho_offdiag": off.tolist(),
            "n_sessions": int(entered.sum()),
        }
    rho_bar = float(np.mean(rhos))
    # justify: PRDS tolerance = sampling-noise floor on a ~2k-session correlation
    # (SE ~ 1/sqrt(n) ~ 0.02, 2.5 SE); a pair below -0.05 is materially negative
    # and forfeits the PRDS case (BY fallback).
    prds_tol = -0.05
    return {
        "rho_bar": rho_bar,
        "rho_min": float(min_rho),
        "prds_defensible": bool(min_rho >= prds_tol),
        "prds_tolerance": prds_tol,
        "per_instrument": per_instrument,
        "note": (
            "exact RC-H101-1 cell masks (harness _session_covariates/_cells "
            "reused by module import); masked contribution-series correlations"
        ),
    }


# ---------------------------------------------------------------------------
# Main calibration
# ---------------------------------------------------------------------------


def run_calibration(paths: ProjectPaths) -> dict:  # noqa: PLR0912, PLR0915 — one linear, auditable calibration sequence (band -> enactment -> CI -> bridges -> RD5 -> RD6); splitting would scatter the enactment-rule invariants
    """Full RD1-RD6 numeric instantiation; returns the machine artifact dict."""
    rng = np.random.default_rng(SEED)
    trials = _trial_population(paths)
    pi1_band = _pi1_band(trials)
    dependence = _cell_dependence(paths)
    r_backstop = _jeffreys_backstop_lower()

    # Benchmark anchors (mu band): sr_benchmark x n_eff from the register's DSR
    # blocks — RC-H103-1 (N_trials=20, the current full surface) is the primary
    # anchor; RC-H101-1 (N_trials=10) enters the band as sensitivity.
    anchors = [
        {
            "instrument": b["instrument"],
            "scan": b["scan"],
            "sr_benchmark": b["sr_benchmark"],
            "n_eff": b["n_eff"],
            "mu": b["sr_benchmark"] * float(np.sqrt(b["n_eff"])),
        }
        for b in trials["benchmarks"]
    ]

    raw_nets = {s: _per_session_net(paths, s) for s in INSTRUMENTS}
    false_nets = {s: raw_nets[s] - raw_nets[s].mean() for s in INSTRUMENTS}
    windows = {s: _sessions_per_eval_window(paths, s) for s in INSTRUMENTS}

    # ENACTMENT BAND: instrument x same-instrument mu-anchor x H_dem multiple
    # x r_backstop variant, all at the 1-window dwell floor (module docstring).
    r_variants = (
        {"label": "r0-no-information", "r": 0.0},
        {"label": "r-jeffreys-censored-record", "r": r_backstop},
    )
    band_points = []
    for symbol in INSTRUMENTS:
        false_net = false_nets[symbol]
        for anchor in [a for a in anchors if a["instrument"] == symbol]:
            for hd_mult in H_DEM_WINDOW_MULTIPLES:
                for rv in r_variants:
                    model, diag = _band_point(
                        false_net,
                        sr_bench=anchor["sr_benchmark"],
                        h_dwell_sessions=windows[symbol],
                        h_window_sessions=windows[symbol],
                        r_backstop=rv["r"],
                        operating_fraction=1.0,  # justify: unit fraction = the
                        # k1.0 ledger currency; the operating-fraction sweep is
                        # reported below as the lambda sensitivity
                        h_dem_multiple=float(hd_mult),
                    )
                    band_points.append(
                        {
                            "instrument": symbol,
                            "enactment_member": True,
                            "dwell_multiple": 1,
                            "h_dem_multiple": hd_mult,
                            "r_variant": rv["label"],
                            "r_backstop": rv["r"],
                            "h_dwell_sessions": windows[symbol],
                            "mu_anchor": f"{anchor['scan']}:{anchor['instrument']}",
                            "mu": anchor["mu"],
                            "lambda": float(model.loss_ratio),
                            "t_star": diag["t_star"],
                            "l_md": float(model.l_md),
                            "l_fd": float(model.l_fd),
                            "l_fd_unbounded": float(model.l_fd_unbounded),
                            "loss_diag": diag,
                        }
                    )
    # H_dwell 2x/4x sensitivity (reported only; at H_dem = 1 window, Jeffreys r).
    for symbol in INSTRUMENTS:
        false_net = false_nets[symbol]
        for mult in DWELL_WINDOW_MULTIPLES[1:]:
            for anchor in [a for a in anchors if a["instrument"] == symbol]:
                model, diag = _band_point(
                    false_net,
                    sr_bench=anchor["sr_benchmark"],
                    h_dwell_sessions=mult * windows[symbol],
                    h_window_sessions=windows[symbol],
                    r_backstop=r_backstop,
                    operating_fraction=1.0,
                )
                band_points.append(
                    {
                        "instrument": symbol,
                        "enactment_member": False,
                        "dwell_multiple": mult,
                        "h_dem_multiple": 1,
                        "r_variant": "r-jeffreys-censored-record",
                        "r_backstop": r_backstop,
                        "h_dwell_sessions": mult * windows[symbol],
                        "mu_anchor": f"{anchor['scan']}:{anchor['instrument']}",
                        "mu": anchor["mu"],
                        "lambda": float(model.loss_ratio),
                        "t_star": diag["t_star"],
                        "l_md": float(model.l_md),
                        "l_fd": float(model.l_fd),
                        "l_fd_unbounded": float(model.l_fd_unbounded),
                        "loss_diag": diag,
                    }
                )

    # Enactment (ex ante rule, module docstring): median t* over the
    # enactment band (24 points: 2 instruments x 2 anchors x 3 H_dem x 2 r).
    enact_pool = [p["t_star"] for p in band_points if p["enactment_member"]]
    enacted_alpha = float(np.median(enact_pool))
    band_min = float(np.min(enact_pool))
    band_max = float(np.max(enact_pool))
    full_band_max = float(np.max([p["t_star"] for p in band_points]))

    # Closed-form benchmark cross-check (module docstring): lambda ~ 4/(1-r).
    lambda_benchmark = 4.0 / (1.0 - r_backstop)
    t_star_benchmark = lambda_benchmark / (1.0 + lambda_benchmark)

    # Controls-off exhibit (RD2 conditional): the tighter fallback the memo
    # mandates when Memo-1 sizing / ADR-0010 ramp are not in force.
    controls_off = []
    for symbol in INSTRUMENTS:
        anchor = max((a for a in anchors if a["instrument"] == symbol), key=lambda a: a["n_eff"])
        model_off, diag_off = _band_point(
            false_nets[symbol],
            sr_bench=anchor["sr_benchmark"],
            h_dwell_sessions=windows[symbol],
            h_window_sessions=windows[symbol],
            r_backstop=r_backstop,
            operating_fraction=1.0,
            controls_in_force=False,
        )
        controls_off.append(
            {
                "instrument": symbol,
                "lambda": float(model_off.loss_ratio),
                "t_star": diag_off["t_star"],
            }
        )

    # Bootstrap CI on the enacted level: stationary-bootstrap resample the
    # false-edge session series (per instrument, PW block length), recompute
    # the enactment-subset median t* per replicate (fast: no quadrature).
    bls = {
        s: max(
            politis_white_block_length(false_nets[s], bootstrap_type="stationary").block_length,
            1.0,
        )
        for s in INSTRUMENTS
    }
    reps = np.empty(N_BOOTSTRAP, dtype=np.float64)
    n_expected_evals = len(anchors) * len(H_DEM_WINDOW_MULTIPLES) * len(r_variants)
    n_partial_replicates = 0
    n_dropped_evaluations = 0
    for b in range(N_BOOTSTRAP):
        vals = []
        for symbol in INSTRUMENTS:
            x = false_nets[symbol]
            idx = stationary_bootstrap_indices(x.size, block_length=bls[symbol], rng=rng)
            xb = x[idx]
            for anchor in [a for a in anchors if a["instrument"] == symbol]:
                for hd_mult in H_DEM_WINDOW_MULTIPLES:
                    for rv in r_variants:
                        try:
                            _, diag_b = _band_point(
                                xb,
                                sr_bench=anchor["sr_benchmark"],
                                h_dwell_sessions=windows[symbol],
                                h_window_sessions=windows[symbol],
                                r_backstop=rv["r"],
                                operating_fraction=1.0,
                                h_dem_multiple=float(hd_mult),
                            )
                            vals.append(diag_b["t_star"])
                        except (ValueError, RuntimeError):
                            n_dropped_evaluations += 1
                            continue  # degenerate resample; counted (CODE-1-3)
        if vals and len(vals) < n_expected_evals:
            n_partial_replicates += 1
        reps[b] = np.median(vals) if vals else np.nan
    reps = reps[np.isfinite(reps)]
    ci_lo = float(np.quantile(reps, CI_ALPHA / 2.0))
    ci_hi = float(np.quantile(reps, 1.0 - CI_ALPHA / 2.0))

    # Raw-stream sensitivity (un-demeaned false-edge substrate).
    raw_sensitivity = {}
    for symbol in INSTRUMENTS:
        anchor = max((a for a in anchors if a["instrument"] == symbol), key=lambda a: a["n_eff"])
        try:
            model_raw, diag_raw = _band_point(
                raw_nets[symbol],
                sr_bench=anchor["sr_benchmark"],
                h_dwell_sessions=windows[symbol],
                h_window_sessions=windows[symbol],
                r_backstop=r_backstop,
                operating_fraction=1.0,
            )
            raw_sensitivity[symbol] = {
                "raw_mean_per_session": float(raw_nets[symbol].mean()),
                "lambda": float(model_raw.loss_ratio),
                "t_star": diag_raw["t_star"],
            }
        except (ValueError, RuntimeError) as exc:
            raw_sensitivity[symbol] = {
                "raw_mean_per_session": float(raw_nets[symbol].mean()),
                "error": str(exc),
            }

    # Lambda sensitivity across the registered Kelly operating fractions.
    lambda_by_fraction = {}
    for symbol in INSTRUMENTS:
        anchor = max((a for a in anchors if a["instrument"] == symbol), key=lambda a: a["n_eff"])
        rows = {}
        for f in KELLY_GRID:
            model_f, _ = _band_point(
                false_nets[symbol],
                sr_bench=anchor["sr_benchmark"],
                h_dwell_sessions=windows[symbol],
                h_window_sessions=windows[symbol],
                r_backstop=r_backstop,
                operating_fraction=f,
            )
            rows[str(f)] = float(model_f.loss_ratio)
        lambda_by_fraction[symbol] = rows

    # Reporting bridges at the enacted cutoff. implied_screening_fdr takes the
    # LOSS RATIO; feed the enacted t* back through the odds identity
    # t*/(1 - t*) = lambda so the cutoff matches.
    empirical_lfdr = np.asarray(pi1_band["empirical_lfdr"], dtype=np.float64)
    bridge_empirical = float(
        implied_screening_fdr(empirical_lfdr, enacted_alpha / (1.0 - enacted_alpha))
    )
    pi1_hit = next(e for e in pi1_band["estimators"] if e["estimator"] == "exploration-hit-rate")
    mu_med = float(np.median([a["mu"] for a in anchors]))
    bridge_model = {}
    # justify: 1e-6 = structural open-interval clamp keeping pi0 in (0, 1)
    # for the two-groups density (domain guard, not a tuned parameter).
    for label, pi1_v in (
        ("jeffreys-lo", max(pi1_hit["jeffreys_95ci"][0], 1e-6)),
        ("jeffreys-median", pi1_hit["jeffreys_median"]),
        ("jeffreys-hi", min(pi1_hit["jeffreys_95ci"][1], 1.0 - 1e-6)),
    ):
        bridge_model[label] = _implied_model_fdr(enacted_alpha, pi0=1.0 - pi1_v, mu=mu_med)

    # RD5 criterion sweep at the enacted level over the registered family sizes.
    central = [p for p in band_points if p["enactment_member"]]
    lambda_central = float(np.median([p["lambda"] for p in central]))
    l_md_central = float(np.median([p["l_md"] for p in central]))
    l_fd_central = float(np.median([p["l_fd"] for p in central]))
    pi1_central = pi1_hit["jeffreys_median"]
    central_model = LossModel(
        l_fd=l_fd_central,
        l_md=l_md_central,
        loss_ratio=lambda_central,
        controls_in_force=True,
        l_fd_unbounded=l_fd_central / max(1.0 - r_backstop, _EPS),
        backstop_rejection_rate=r_backstop,
        min_live_fraction=F_MIN,
        demotion_latency_bars=float(np.median([p["loss_diag"]["h_dem_sessions"] for p in central])),
        champion_dwell_bars=float(np.median([p["h_dwell_sessions"] for p in central])),
        notes="central (median) band point for the RD5 sweep",
    )
    two_groups = TwoGroupsModel(pi0=1.0 - pi1_central, mu=mu_med)
    criterion_sweep = []
    for n_fam in FAMILY_SIZES:
        dep_infl = 1.0 + (n_fam - 1) * max(dependence["rho_bar"], 0.0)
        dec = fwer_vs_fdr_decision(
            two_groups,
            n_fam,
            central_model,
            family_alpha=enacted_alpha,
            fdr_level=enacted_alpha,
            dependence_inflation=dep_infl,
            prds_defensible=dependence["prds_defensible"],
        )
        criterion_sweep.append(
            {
                "family_size": n_fam,
                "dependence_inflation": dep_infl,
                "criterion": dec.criterion,
                "prds_obligation": dec.prds_obligation,
                "loss_fwer": dec.loss_fwer,
                "loss_fdr": dec.loss_fdr,
                "power_fwer": dec.power_fwer,
                "power_fdr": dec.power_fdr,
                # beyond the register's realized surface (N = 20): flagged
                # conditional on the dependence transferring (QUANT-1-5).
                "conditional_on_dependence_transfer": bool(n_fam > max(FAMILY_SIZES[:3])),
            }
        )
    screen_decision = criterion_sweep[0]
    rd5_note = (
        "rows with family_size > 20 extrapolate the NESTED-cell equicorrelation "
        "(rho_bar = measured on the RC-H101-1 mask structure) to future "
        "(config x Kelly-fraction) families whose dependence does not exist yet "
        "(QUANT-1-5); the criterion for the confirmation family is RE-DECIDED on "
        "that family's own measured dependence at its first swept scan (§A.8 "
        "standing condition)."
    )

    # RD6 TOST diagnostic at the enacted level (consumed at Phase 5).
    tost = {}
    for symbol in INSTRUMENTS:
        anchor = max((a for a in anchors if a["instrument"] == symbol), key=lambda a: a["n_eff"])
        _, diag = _band_point(
            false_nets[symbol],
            sr_bench=anchor["sr_benchmark"],
            h_dwell_sessions=windows[symbol],
            h_window_sessions=windows[symbol],
            r_backstop=r_backstop,
            operating_fraction=1.0,
        )
        powered = _tost_powered_window(
            diag["g_bench_per_session"], diag["sigma_te"], enacted_alpha, enacted_alpha
        )
        tost[symbol] = {
            "alpha_tost": enacted_alpha,
            "beta_tost": enacted_alpha,
            "delta_per_session": diag["g_bench_per_session"],
            "sigma_te": diag["sigma_te"],
            "powered_window_sessions": powered,
            "structural_h_dem_sessions": diag["h_dem_sessions"],
            "note": (
                "symmetric (alpha=beta) DIAGNOSTIC at the enacted level "
                "(nan when the level >= 0.5: the TOST z-quantiles vanish); "
                "the loss model's H_dem is the structural one-evaluation-"
                "window bound; the lambda-weighted asymmetric re-split is an "
                "ADR-0010 Phase-5 action, deferred until a champion exists"
            ),
        }

    return {
        "calibration": "P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE",
        "status": (
            "NUMERIC-INSTANTIATED (method frozen 2026-07-12; this run supplies "
            "the deferred on-ledger numbers)"
        ),
        "seed": SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "substrate": {
            "ledger_expert": LEDGER_EXPERT,
            "instruments": list(INSTRUMENTS),
            "per_session_currency": "net, demeaned (zero-edge primary; raw as sensitivity)",
            "n_entered_sessions": {s: int(false_nets[s].size) for s in INSTRUMENTS},
            "sessions_per_eval_window_median": windows,
        },
        "trial_population": {
            "n_raw": trials["n_raw"],
            "n_distinct": trials["n_distinct"],
            "keys": trials["keys"],
            "z": trials["z"].tolist(),
            "benchmark_anchors": anchors,
        },
        "rd2_backstop": {
            "record": BACKSTOP_RECORD,
            "jeffreys_lower_95": r_backstop,
        },
        "rd3_pi1": pi1_band,
        "rd1_rd2_rd4_band": band_points,
        "enactment": {
            "rule": (
                "screening_error_rate_target = the RD4 Bayes posterior-null "
                "cutoff t* (pi1-free), median over the 1-window dwell-floor "
                "enactment subset (instrument x same-instrument mu-anchor); "
                "2x/4x dwell multiples sensitivity only; the memo's "
                "implied-FDR translation is degenerate on the all-null ledger "
                "and is reported as a bridge, not enacted (see memo addendum)"
            ),
            "screening_error_rate_target": enacted_alpha,
            "enactment_subset_band": [band_min, band_max],
            "full_band_max_with_dwell_sensitivity": full_band_max,
            "bootstrap_ci95": [ci_lo, ci_hi],
            "n_bootstrap_effective": int(reps.size),
            "n_partial_replicates": n_partial_replicates,
            "n_dropped_evaluations": n_dropped_evaluations,
            "closed_form_benchmark": {
                "lambda": lambda_benchmark,
                "t_star": t_star_benchmark,
                "formula": (
                    "lambda ~ (H_dwell/H_dem) x 4/(1 - r); SR^2/2 over SR^2/8; "
                    "quoted at H_dwell = H_dem, r = jeffreys endpoint"
                ),
            },
        },
        "controls_off_exhibit": controls_off,
        "raw_stream_sensitivity": raw_sensitivity,
        "lambda_by_operating_fraction": lambda_by_fraction,
        "reporting_bridges": {
            "empirical_implied_fdr_at_enacted": bridge_empirical,
            "model_implied_fdr_at_enacted": bridge_model,
            "note": (
                "on this run the empirical bridge admits ALL 14 trials (every "
                "Efron lfdr from the degenerate n=14 Lindsey fit is below the "
                "cutoff), so it returns their mean = the Efron pi0 — "
                "untrustworthy because the same fit implies pi1 ~ 0.91 against "
                "the RD3 red flag; the model bridge is separately "
                "discontinuous at pi1 -> 0. Bridges are REPORTED operating "
                "points, not the enacted level."
            ),
        },
        "rd5_criterion": {
            "sweep": criterion_sweep,
            "note": rd5_note,
            "screen_family_decision": screen_decision,
            "dependence": {k: v for k, v in dependence.items() if k != "per_instrument"},
            "dependence_per_instrument": dependence["per_instrument"],
        },
        "rd6_tost": tost,
        "certifies": "nothing (no admission certified, no Kelly fraction selected)",
    }


def _json_sanitize(obj):
    """RFC 8259-safe serialization: non-finite floats -> string sentinels.

    Bare Infinity/NaN tokens are invalid JSON (FORMAT-1-2); machine consumers
    get "inf"/"-inf"/"nan" strings instead.
    """
    if isinstance(obj, dict):
        return {k: _json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_json_sanitize(v) for v in obj]
    if isinstance(obj, float) and not np.isfinite(obj):
        # covers +inf, -inf, and nan (nan compares False on both > and <)
        return "inf" if obj > 0 else ("-inf" if obj < 0 else "nan")
    return obj


def main() -> int:
    """ReproLog -> calibration -> JSON artifact -> console summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/discovery_alpha_calibration")
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    out_dir = paths.root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    memo = paths.root / "docs/methodology/discovery_alpha_cost_calibration_2026-07-12.md"
    memo_sha = hashlib.sha256(memo.read_bytes()).hexdigest()
    log = reproducibility.capture(
        phase="discovery-alpha-numeric-calibration",
        hypothesis_id="P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE",
        rng_seed=SEED,
        dataset_checksums=_dataset_checksums(paths),
        config_resolved_sha256=memo_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (memo SHA {memo_sha[:12]}...)", flush=True)

    result = run_calibration(paths)
    result["repro_log"] = log_path.name
    (out_dir / "discovery_alpha_calibration.json").write_text(
        json.dumps(_json_sanitize(result), indent=2, sort_keys=True, default=str, allow_nan=False),
        encoding="utf-8",
    )

    en = result["enactment"]
    sd = result["rd5_criterion"]["screen_family_decision"]
    tgt = en["screening_error_rate_target"]
    esb = en["enactment_subset_band"]
    ci = en["bootstrap_ci95"]
    bench = en["closed_form_benchmark"]
    print(f"[discovery-alpha] screening_error_rate_target (t*) = {tgt:.4f}", flush=True)
    print(f"  enactment-subset band = [{esb[0]:.4f}, {esb[1]:.4f}]", flush=True)
    print(f"  bootstrap 95% CI      = [{ci[0]:.4f}, {ci[1]:.4f}]", flush=True)
    print(
        f"  closed-form benchmark: lambda={bench['lambda']:.2f} t*={bench['t_star']:.4f}",
        flush=True,
    )
    print(
        f"  screen-family (N=5) criterion = {sd['criterion']} "
        f"(prds_obligation={sd['prds_obligation']})",
        flush=True,
    )
    for row in result["rd5_criterion"]["sweep"]:
        print(
            f"    N={row['family_size']:>5}: {row['criterion']:<20} "
            f"loss_fwer={row['loss_fwer']:.3f} loss_fdr={row['loss_fdr']:.3f}",
            flush=True,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
