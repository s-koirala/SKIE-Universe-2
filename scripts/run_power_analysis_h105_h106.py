"""Pre-data power / precision analysis for H105 and H106 (design §9 power gate).

Runs AFTER the design freeze and BEFORE the backfill (mission step P3-B.5 /
P3-C; od_g setup plan §5.2 precedent). PROSPECTIVE only: no signal mean, no
edge statistic, and no screen outcome is computed — effect sizes come from
the registered literature/project anchors, and only DESIGN-STAGE variance
quantities are estimated from the substrate (second moments and state
prevalences; Hoenig & Heisey 2001 forbids retrospective power, not
historical variance estimation).

Registered effect anchors (per-session gross log-return):

- ``mu_h900_anchor`` = 1.2e-4 — the registered H900 §10 break-even
  per-session edge anchor (the project's standing minimum-economically-
  meaningful effect constant; H900 design/report of record).
- ``mu_boyarchenko_lower`` (H105 only) = 0.037 / 252 ≈ 1.468e-4 — the
  Boyarchenko-Larsen-Whelan 2023 headline (~3.7%/yr accruing in the
  02:00-03:00 ET window alone, RFS 36(9):3502-3547) spread over ~252
  sessions: a LOWER anchor for the full-overnight mean under the paper's
  mechanism (one hour of a 15.5-hour window).

Computed per instrument × binding cell:

1. **S-c power (approximate)** at the ENACTED screening level (read from
   config/multipletest_family.yaml at runtime): one-sided z-approximation
   ``power = Phi(mu/(sigma/sqrt(n)) + z_level)`` where ``z_level`` is the
   (1 - level) normal quantile. The Romano-Wolf family adjustment and
   serial dependence make the realized gate somewhat stricter; this is the
   standard design-stage approximation and is labeled as such.
2. **§8 precision-gate feasibility**: n required for the 95% CI half-width
   to be < 25% of the effect anchor (``n_req = (z_0.975 * sigma /
   (0.25 * mu))^2``) vs the n available; the H103 precedent (both cells
   failed this REPORT-ELIGIBILITY gate at n = 437/313) makes the expected
   verdict "not met at literature effect sizes" — that constrains the
   card's report-eligibility, NOT the screen (the STOP rule binds on the
   S-c/S-d gates being unreachable, which this analysis evaluates).

Design-stage inputs estimated from the substrate (no signal evaluation):
per-session competence-window return volatility (H105: std of the summed
overnight-segment 5-min log-returns; H106: sqrt(E[#active bars]) × per-bar
return std, with #active approximated by the range-state prevalence — the
signal's second moment under a symmetric-sign position, no signed edge
used), cell prevalences (tercile ≈ 1/3 by construction; sign/state
prevalences measured), and session counts.

Writes ``reports/{HID}/power_analysis.json`` + a ReproLog per HID.

Usage:
    uv run python scripts/run_power_analysis_h105_h106.py --hid H105
    uv run python scripts/run_power_analysis_h105_h106.py --hid H106
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl
from scipy.stats import norm

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.features.variance_ratio_state import (  # noqa: E402
    VR_LAG_Q,
    VR_WINDOW_BARS,
    VarianceRatioState,
    variance_ratio_state,
)
from skie_universe2.screening import screen_spine as spine  # noqa: E402
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402
from skie_universe2.utils.sessions import SEGMENT_OVERNIGHT_ETH  # noqa: E402

# justify: registered H900 §10 break-even per-session edge anchor (project
# effect-size constant of record; H900_dwell_feasibility_report_2026-07-11).
MU_H900_ANCHOR = 1.2e-4
# justify: derived — Boyarchenko-Larsen-Whelan 2023 (10.1093/rfs/hhad020)
# ~3.7%/yr in the 02:00-03:00 ET window / ~252 CME sessions per year; a
# LOWER anchor for the full-overnight per-session mean (H105 design §1).
MU_BOYARCHENKO_LOWER = 0.037 / 252.0
# justify: H105/H106 design §8 — descriptive CI level (H900/H101 lineage).
ALPHA_CI = 0.05
# justify: H105/H106 design §8 — the §8 precision report-eligibility
# fraction, inherited VERBATIM from the H900/H001 CONSORT-style convention.
PRECISION_FRACTION = 0.25
SEED = 20260719  # justify: H105 design §11 seed; analysis is deterministic (no RNG consumed)
_MIN_N = 2  # justify: ddof=1 minimum; structural


def _load_h105_harness():
    if "rc_h105_harness" in sys.modules:
        return sys.modules["rc_h105_harness"]
    spec = importlib.util.spec_from_file_location(
        "rc_h105_harness", _ROOT / "scripts" / "run_screen_h105.py"
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules["rc_h105_harness"] = mod
    spec.loader.exec_module(mod)
    return mod


def _screen_level(paths: ProjectPaths) -> float:
    return spine.screen_level(paths)


def _h105_design_inputs(paths: ProjectPaths, symbol: str) -> dict:
    """Per-session overnight-return sigma + sign-cell prevalence (no means)."""
    h = _load_h105_harness()
    feats = h._valid_5m_features(paths, symbol)
    on = feats.filter(pl.col("segment") == SEGMENT_OVERNIGHT_ETH).sort("ts_event")
    per = (
        on.with_columns(pl.col("close").log().diff().over("cme_session_date").alias("r5"))
        .group_by("cme_session_date")
        .agg(overnight_ret=pl.col("r5").sum())
        .drop_nulls()
    )
    sigma = float(per.get_column("overnight_ret").std(ddof=1))
    n_sessions = int(per.height)
    covs = h._session_covariates(paths, symbol)
    prior = covs.get_column("prior_rth_ret").to_numpy()
    finite = np.isfinite(prior.astype(np.float64))
    p_up = float((prior[finite] > 0).mean()) if finite.any() else float("nan")
    return {
        "sigma_session": sigma,
        "n_sessions": n_sessions,
        "cell_prevalence": {
            "unconditional": 1.0,
            "high_vol": 1.0 / 3.0,
            "low_vol": 1.0 / 3.0,
            "prior_rth_up": p_up * float(finite.mean()),
            "prior_rth_down": (1.0 - p_up) * float(finite.mean()),
        },
        "sigma_note": (
            "std of summed overnight-segment 5-min log-returns per session "
            "(second moment only; the H105 signal is deterministic long, so "
            "this is the design-stage sigma of its per-session gross)"
        ),
    }


def _h106_design_inputs(paths: ProjectPaths, symbol: str) -> dict:
    """Per-session reversal-gross sigma approximation + state prevalences."""
    h = _load_h105_harness()
    feats = h._valid_5m_features(paths, symbol).sort("ts_event")
    close = feats.get_column("close").to_numpy().astype(np.float64)
    r = np.log(close[1:] / close[:-1])
    sigma_bar = float(np.nanstd(r, ddof=1))
    state_r = variance_ratio_state(r, window=VR_WINDOW_BARS, q=VR_LAG_Q)
    defined = state_r != VarianceRatioState.UNDETERMINED
    p_range = float((state_r[defined] == VarianceRatioState.RANGE).mean())
    n_sessions = int(feats.get_column("cme_session_date").n_unique())
    bars_per_session = float(feats.height / max(n_sessions, 1))
    # Under a ±1 position on range-state bars, the per-session gross second
    # moment ≈ (#active bars) × sigma_bar² (symmetric signs; no signed edge
    # information consumed). Design-stage approximation, labeled.
    exp_active = p_range * bars_per_session
    sigma_session = float(np.sqrt(exp_active) * sigma_bar)
    # State-at-open prevalence for the vr cells (state, not outcome, data).
    covs_state = state_r[defined]
    return {
        "sigma_session": sigma_session,
        "sigma_bar": sigma_bar,
        "n_sessions": n_sessions,
        "bars_per_session_mean": bars_per_session,
        "range_state_bar_prevalence": p_range,
        "cell_prevalence": {
            "unconditional": 1.0,
            "vr_range_at_open": p_range,  # bar prevalence ≈ at-open prevalence (stationary)
            "vr_trend_at_open": float((covs_state == VarianceRatioState.TREND).mean()),
            "high_vol": 1.0 / 3.0,
            "low_vol": 1.0 / 3.0,
        },
        "sigma_note": (
            "sqrt(E[#range-state bars/session]) x per-bar return std — the "
            "signal's per-session second moment under symmetric signs; no "
            "signed edge used (prospective-only rule)"
        ),
    }


def _power_row(mu: float, sigma: float, n: float, level: float) -> dict:
    """One-sided z-approximation of S-c power + §8 precision feasibility."""
    if not (np.isfinite(mu) and np.isfinite(sigma) and sigma > 0 and n >= _MIN_N):
        return {"power_s_c_approx": None, "n_required_precision": None, "precision_met": None}
    se = sigma / np.sqrt(n)
    z_level = norm.ppf(1.0 - level)  # critical z at the enacted one-sided level
    power = float(norm.cdf(mu / se - z_level))
    z975 = norm.ppf(1.0 - ALPHA_CI / 2.0)
    n_req = float((z975 * sigma / (PRECISION_FRACTION * mu)) ** 2)
    return {
        "power_s_c_approx": power,
        "n_required_precision": n_req,
        "precision_met": bool(n >= n_req),
        "n_available": float(n),
        "se_at_n": float(se),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hid", required=True, choices=("H105", "H106"))
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    level = _screen_level(paths)

    design = paths.root / "research/01_hypothesis_register" / args.hid / "design.md"
    design_sha = hashlib.sha256(design.read_bytes()).hexdigest()
    log = reproducibility.capture(
        phase=f"{args.hid.lower()}-power-analysis",
        hypothesis_id=args.hid,
        rng_seed=SEED,
        dataset_checksums={"design.md": design_sha},
        config_resolved_sha256=design_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name}", flush=True)

    anchors = {"mu_h900_anchor": MU_H900_ANCHOR}
    if args.hid == "H105":
        anchors["mu_boyarchenko_lower"] = MU_BOYARCHENKO_LOWER

    out: dict = {
        "hid": args.hid,
        "repro_log": log_path.name,
        "design_md_sha256": design_sha,
        "screen_level_runtime": level,
        "effect_anchors": anchors,
        "prospective_only_note": (
            "no signal mean or edge statistic computed (Hoenig & Heisey 2001); "
            "sigma/prevalence are design-stage substrate quantities"
        ),
        "instruments": {},
    }
    for symbol in ("ES", "NQ"):
        d = (
            _h105_design_inputs(paths, symbol)
            if args.hid == "H105"
            else _h106_design_inputs(paths, symbol)
        )
        rows = {}
        for cell, prev in d["cell_prevalence"].items():
            n_cell = prev * d["n_sessions"] if np.isfinite(prev) else float("nan")
            rows[cell] = {
                anchor: _power_row(mu, d["sigma_session"], n_cell, level)
                for anchor, mu in anchors.items()
            }
        out["instruments"][symbol] = {**d, "cells": rows}
        print(f"[{symbol}] sigma_session={d['sigma_session']:.3e} n={d['n_sessions']}")

    out_dir = paths.root / "reports" / args.hid
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "power_analysis.json"
    out_path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}", flush=True)

    # Console verdict for the design §9 power gate.
    for symbol in ("ES", "NQ"):
        cells = out["instruments"][symbol]["cells"]
        for cell, per_anchor in cells.items():
            for anchor, row in per_anchor.items():
                if row["power_s_c_approx"] is not None:
                    print(
                        f"  {symbol}/{cell} @ {anchor}: "
                        f"power(S-c)~{row['power_s_c_approx']:.3f}, "
                        f"precision n_req={row['n_required_precision']:.0f} "
                        f"vs n={row['n_available']:.0f} "
                        f"({'MET' if row['precision_met'] else 'not met'})",
                        flush=True,
                    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
