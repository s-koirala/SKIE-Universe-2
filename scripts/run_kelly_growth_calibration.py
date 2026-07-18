"""P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE — on-ledger NUMERIC instantiation.

Instantiates the frozen Kelly-growth concavity/ruin method
(docs/methodology/kelly_growth_concavity_ruin_2026-07-12.md; reference
estimator src/skie_universe2/inference/kelly_growth.py) on the populated
ADR-0003 shadow ledger, producing the deferred numeric outputs per instrument:

  - the full-Kelly bet ``b*`` and the D1 grid growth curve g(f) over the
    registered sweep {0.5, 0.75, 1.0, 1.25} (absorbing barrier primary,
    capping sensitivity),
  - the D3 ruin barrier ``f_max``, per-grid-point distance-to-barrier and
    single-bar ``P(ruin)`` with stationary-bootstrap CI,
  - the D4 over-betting zero-growth crossing ``f_0`` (grid-top verdict:
    is 1.25 < f_0?),
  - the D2 estimation-error-adjusted OOS optimum ``f**`` via the frozen
    purged/embargoed nested rolling origin, with a stationary-bootstrap CI on
    the per-fraction OOS growth,
  - the D5 Busseti-Ryu-Boyd drawdown bound per grid point,
  - the GRID-BRACKETING VERDICT: does {0.5, 0.75, 1.0, 1.25} bracket the
    estimation-adjusted optimum (f** interior) and does the grid top stay
    inside the positive-growth region?

RECORD ONLY: this run selects NO Kelly fraction (fraction selection is a
Phase-4 champion action under ADR-0012/0013 and additionally requires the
discovery-alpha level for the swept family). The numbers below are the memo's
deferred on-ledger instantiation, nothing more.

Substrate (ADR-0003 sole-evidence rule): the per-SESSION return stream of the
ledger's expert at unit fraction (``orb_first_hour_k1.0@1.0.0``), per
instrument — sessions are the expert's natural compounding atoms (one
round-trip per session, flat overnight; the per-bar stream is ~0-inflated by
construction outside the holding window). NET returns are the primary
currency (the position layer sizes realizable, post-cost streams; ADR-0008
bar-level cost drag), GROSS reported as sensitivity. The honest expected
regime on the current ledger: the RC-H101-1/RC-H103-1 nulls mean the
favourable-bet premise (E[R] > 0) may FAIL — ``full_kelly_leverage`` then
returns b* = 0 and the report records a degenerate (no-positive-bet) verdict,
which is itself the on-ledger answer while the arsenal is empty.

Usage:
    uv run python scripts/run_kelly_growth_calibration.py
        [--out reports/kelly_growth_calibration]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

import polars as pl  # noqa: E402

from skie_universe2.inference.bootstrap import (  # noqa: E402
    stationary_bootstrap_indices,
)
from skie_universe2.inference.kelly_growth import (  # noqa: E402
    KELLY_FRACTION_GRID,
    KellyGrowthReport,
    full_kelly_leverage,
    growth_rate,
    growth_second_derivative,
    kelly_growth_report,
    nested_rolling_origin_growth,
)
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

# justify: pre-registered date-seed, project scan convention (RC-H101-1 used 20260716;
# the discovery-alpha calibration uses the same 20260717 date-seed this session).
SEED = 20260717
# justify: k1.0 = unit position -> the estimator applies its own leverage f*b*.
LEDGER_EXPERT = "orb_first_hour_k1.0@1.0.0"
INSTRUMENTS = ("ES", "NQ")  # justify: the populated ledger universe
# justify: memo appendix registered defaults — H900 §8 / 1.0 H052a stationary-
# bootstrap replication convention; two-sided 95% reporting convention.
N_BOOTSTRAP = 2000
CI_ALPHA = 0.05
_MIN_CELL_N = 2  # justify: ddof=1 minimum; structural
_EPS = 1e-12  # justify: structural div-by-zero guard


def _dataset_checksums(paths: ProjectPaths) -> dict[str, str]:
    """Shadow-ledger k1.0 partition roll-up digest (same rule as the alpha run)."""
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
    return {f"shadow_ledger[{LEDGER_EXPERT}]({n} partitions)": digest.hexdigest()}


def _per_session(paths: ProjectPaths, symbol: str) -> dict[str, np.ndarray]:
    """Per-session net and gross return streams (entered sessions, finite)."""
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
        .select("session_date", "ret_gross", "ret_net")
        .group_by("session_date")
        .agg(
            gross=pl.col("ret_gross").sum(),
            net=pl.col("ret_net").sum(),
            n_active=(pl.col("ret_gross") != 0).sum(),
        )
        .sort("session_date")
        .collect()
    )
    entered = df.get_column("n_active").to_numpy() > 0
    out = {}
    for col in ("net", "gross"):
        x = df.get_column(col).to_numpy().astype(np.float64)[entered]
        out[col] = x[np.isfinite(x)]
        if out[col].size < _MIN_CELL_N:
            raise RuntimeError(f"[{symbol}] degenerate {col} series (n={out[col].size})")
    return out


def _report_to_dict(rep: KellyGrowthReport) -> dict:
    """Serialize a KellyGrowthReport (dataclasses -> plain JSON).

    The frozen estimator stamps every report with its default deferred-
    instantiation note; THIS run IS the deferred on-ledger instantiation, so
    the note is superseded at serialization (frozen module untouched; the
    original string is kept for traceability).
    """
    return {
        "b_star": rep.b_star,
        "f_max": rep.f_max,
        "f_zero": rep.f_zero,
        "block_length": rep.block_length.to_dict(),
        "grid": [
            {
                "fraction": g.fraction,
                "leverage": g.leverage,
                "growth_absorbing": g.growth_absorbing,
                "growth_cap_sensitivity": g.growth_cap_sensitivity,
                "distance_to_barrier": g.distance_to_barrier,
                "single_bar_ruin_prob": g.single_bar_ruin_prob,
                "ruin_ci_low": g.ruin_ci_low,
                "ruin_ci_high": g.ruin_ci_high,
                "drawdown_bound": {
                    "drawdown_level": g.drawdown_bound.drawdown_level,
                    "exponent": g.drawdown_bound.exponent,
                    "prob_bound": g.drawdown_bound.prob_bound,
                    "valid": g.drawdown_bound.valid,
                },
            }
            for g in rep.grid
        ],
        "notes_frozen_estimator_default": rep.notes,
        "notes": (
            "ON-LEDGER NUMERIC INSTANTIATION 2026-07-17 (this artifact IS the "
            "deferred step-4 instantiation; the frozen estimator's default "
            "deferred note above is superseded — see top-level status)"
        ),
    }


def _growth_curve_ci(x: np.ndarray, *, rng: np.random.Generator, block_length: float) -> dict:
    """Stationary-bootstrap CI on g(f) per grid fraction (absorbing barrier).

    Each resample re-solves b* on the resampled measure and evaluates the grid
    growth curve there — the CI covers BOTH the bet-estimation and the
    growth-evaluation uncertainty (the memo's "with CIs" obligation on the
    concavity/bracketing exhibit). Resamples with no favourable bet (b* = 0)
    contribute g = 0 at every fraction (no bet, no growth) and are counted.
    """
    reps = np.empty((N_BOOTSTRAP, len(KELLY_FRACTION_GRID)), dtype=np.float64)
    n_no_bet = 0
    for b in range(N_BOOTSTRAP):
        idx = stationary_bootstrap_indices(x.size, block_length=block_length, rng=rng)
        xb = x[idx]
        b_star_b = full_kelly_leverage(xb)
        if not np.isfinite(b_star_b) or b_star_b <= 0.0:
            reps[b, :] = 0.0
            n_no_bet += 1
            continue
        for j, f in enumerate(KELLY_FRACTION_GRID):
            reps[b, j] = growth_rate(xb, float(f) * b_star_b, barrier="absorbing")
    lo = np.quantile(reps, CI_ALPHA / 2.0, axis=0)
    hi = np.quantile(reps, 1.0 - CI_ALPHA / 2.0, axis=0)
    return {
        "fractions": list(KELLY_FRACTION_GRID),
        "ci_low": lo.tolist(),
        "ci_high": hi.tolist(),
        "n_no_favourable_bet_resamples": int(n_no_bet),
    }


def run_instrument(symbol: str, streams: dict[str, np.ndarray]) -> dict:
    """Full D1-D5 instantiation for one instrument (net primary, gross sensitivity)."""
    out: dict = {"instrument": symbol}
    for currency in ("net", "gross"):
        x = streams[currency]
        rng = np.random.default_rng(SEED)  # justify: same seed per currency -> comparable CIs
        b_star = full_kelly_leverage(x)
        block: dict = {"currency": currency, "n_sessions": int(x.size)}
        if not np.isfinite(b_star) or b_star <= 0.0:
            block["degenerate"] = (
                "no favourable bet (E[R] <= 0 or no interior optimum): b* = "
                f"{b_star}; the D1-D5 report is undefined on this stream — the "
                "on-ledger answer while the expert stream carries no positive "
                "edge (RC-H101-1/RC-H103-1 nulls)"
            )
            block["b_star"] = float(b_star)
            block["mean_per_session"] = float(x.mean())
            out[currency] = block
            continue
        rep = kelly_growth_report(x, rng=rng, n_bootstrap=N_BOOTSTRAP, ci_alpha=CI_ALPHA)
        block["report"] = _report_to_dict(rep)
        # D1 concavity exhibit at the grid points (analytic second derivative).
        block["g2_at_grid"] = {
            str(f): float(growth_second_derivative(x, rep.b_star, float(f)))
            for f in KELLY_FRACTION_GRID
        }
        block["growth_curve_ci"] = _growth_curve_ci(
            x, rng=rng, block_length=max(rep.block_length.block_length, 1.0)
        )
        # D2 estimation-error-adjusted OOS optimum (frozen walk-forward; memo
        # appendix registered defaults: 5 splits, 1% embargo, purge 0 for the
        # one-session return label, warm-up 50%).
        ro = nested_rolling_origin_growth(x)
        block["rolling_origin"] = {
            "fractions": ro.fractions.tolist(),
            "oos_growth": ro.oos_growth.tolist(),
            "f_star_oos": ro.f_star_oos,
            "n_folds": ro.n_folds,
            "b_star_folds": ro.b_star_folds.tolist(),
            "notes": ro.notes,
        }
        # Grid verdicts (memo D2/D4: OUTPUTS, not assertions).
        finite_oos = np.where(np.isfinite(ro.oos_growth), ro.oos_growth, -np.inf)
        interior = bool(
            np.isfinite(ro.f_star_oos)
            and min(KELLY_FRACTION_GRID) < ro.f_star_oos < max(KELLY_FRACTION_GRID)
        )
        block["verdicts"] = {
            "f_star_oos_interior": interior,
            "f_star_oos_at_grid_edge": (
                None
                if not np.isfinite(ro.f_star_oos)
                else (
                    "floor"
                    if ro.f_star_oos == min(KELLY_FRACTION_GRID)
                    else ("top" if ro.f_star_oos == max(KELLY_FRACTION_GRID) else None)
                )
            ),
            # Three-state verdict (audit CODE-1-4): True/False on a finite
            # crossing; True with branch "no-crossing" when f_zero = +inf (no
            # zero-growth crossing exists); None when f_zero is NaN (crossing
            # undefined -- never reported as a pass).
            "grid_top_inside_positive_growth": (
                bool(max(KELLY_FRACTION_GRID) < rep.f_zero)
                if np.isfinite(rep.f_zero)
                else (True if np.isposinf(rep.f_zero) else None)
            ),
            "grid_top_verdict_branch": (
                "finite-crossing"
                if np.isfinite(rep.f_zero)
                else ("no-crossing-inf" if np.isposinf(rep.f_zero) else "undefined-nan")
            ),
            "any_grid_point_ruinous": bool(
                any(not np.isfinite(g.growth_absorbing) for g in rep.grid)
            ),
            "oos_curve_finite": bool(np.all(np.isfinite(finite_oos))),
        }
        out[currency] = block
    return out


def _json_sanitize(obj):
    """RFC 8259-safe serialization: non-finite floats -> string sentinels."""
    if isinstance(obj, dict):
        return {k: _json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_json_sanitize(v) for v in obj]
    if isinstance(obj, float) and not np.isfinite(obj):
        # covers +inf, -inf, and nan (nan compares False on both > and <)
        return "inf" if obj > 0 else ("-inf" if obj < 0 else "nan")
    return obj


def main() -> int:
    """ReproLog -> per-instrument D1-D5 -> JSON artifact -> console summary."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default="reports/kelly_growth_calibration")
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    out_dir = paths.root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    memo = paths.root / "docs/methodology/kelly_growth_concavity_ruin_2026-07-12.md"
    memo_sha = hashlib.sha256(memo.read_bytes()).hexdigest()
    log = reproducibility.capture(
        phase="kelly-growth-numeric-calibration",
        hypothesis_id="P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE",
        rng_seed=SEED,
        dataset_checksums=_dataset_checksums(paths),
        config_resolved_sha256=memo_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (memo SHA {memo_sha[:12]}...)", flush=True)

    results = []
    for symbol in INSTRUMENTS:
        streams = _per_session(paths, symbol)
        results.append(run_instrument(symbol, streams))

    blob = {
        "calibration": "P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE",
        "status": (
            "NUMERIC-INSTANTIATED (method frozen 2026-07-12; this run supplies "
            "the deferred on-ledger numbers); RECORD ONLY — no Kelly fraction "
            "is selected (Phase-4 champion action)"
        ),
        "seed": SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "substrate": {
            "ledger_expert": LEDGER_EXPERT,
            "instruments": list(INSTRUMENTS),
            "unit": "per-session (expert compounding atom; flat overnight)",
            "primary_currency": "net (Tier-0 cost drag applied)",
        },
        "repro_log": log_path.name,
        "instruments": results,
    }
    (out_dir / "kelly_growth_calibration.json").write_text(
        json.dumps(_json_sanitize(blob), indent=2, sort_keys=True, default=str, allow_nan=False),
        encoding="utf-8",
    )

    for r in results:
        for currency in ("net", "gross"):
            blk = r[currency]
            if "degenerate" in blk:
                msg = blk["degenerate"][:80]
                print(f"  {r['instrument']}/{currency}: DEGENERATE — {msg}...", flush=True)
                continue
            rep = blk["report"]
            ro = blk["rolling_origin"]
            print(
                f"  {r['instrument']}/{currency}: b*={rep['b_star']:.3f} f_max={rep['f_max']:.3f} "
                f"f_0={rep['f_zero']:.3f} f**_oos={ro['f_star_oos']} "
                f"grid_top_ok={blk['verdicts']['grid_top_inside_positive_growth']}",
                flush=True,
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
