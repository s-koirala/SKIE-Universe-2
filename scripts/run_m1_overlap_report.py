"""M1 realized-coverage overlap report (setup plan §2.3; ADR-0015 companion).

Computes, for every pair of distinct `expert_hash` coverage sets in scope,
the REALIZED overlap at both registered granularities:

- **bar-level Jaccard** over (instrument, bar_ts) tuples on which each
  expert held non-zero exposure WITHIN its passing competence-window
  sessions (T_X of the setup plan §2.3 M1 formula, from the shadow ledger —
  the sole evidence source, ADR-0003), and
- **session-level Jaccard** over (instrument, session_date) member
  sessions — "same days?" vs "same minutes?" (both reported; a candidate
  disjoint at bar level but identical at session level is still limited
  diversification at session cadence).

The label-based ADR-0015 verdict precondition GOVERNS (a living statistic
cannot rewrite the accepted rule); M1 is the mandatory REPORTED companion
that informs the operator-gated lift action and gates nothing mechanically
(ADR-0015 Decision 3; setup plan §2.3 M1/M2).

Coverage sets in scope (recomputed from the recorded constructions):

- ``orb_first_hour_k1.0@1.0.0`` — union of the H101 + H103 pool records'
  passing cells. Session membership recomputed exactly as recorded:
  RC-H101-2 cells via the RC-H101-1 harness (full-sample terciles + fh
  sign — the recorded construction of those pool entries) and the H103
  stress/non_stress cells via the certified per-origin construction
  (`run_screen_h101_h103._h103_stress_labels`, 15 HMM refits/instrument).
- ``overnight_session_drift_k1.0@1.0.0`` — passing cells from the
  RC-H105-1 screen artifact; session membership via the frozen harness's
  `_prepare_instrument`.
- ``vr_range_reversal_k1.0@1.0.0`` — likewise from RC-H106-1 (skipped
  with a notice when the artifact does not exist yet).

Pre-scan predictions quoted for comparison (frozen design §12(c)):
H105 vs ORB — bar-level EXACTLY 0 (identity; a nonzero measured value
falsifies the implementation), session-level ≈ 0.75-0.95. H106 vs ORB —
bar-level ≈ 0.05-0.25 (structural guess, declared), session-level
≈ 0.85-1.0. H105 vs H106 — reported (H106's design §12(c) names the
pairwise as a required report; no numeric band was frozen for it).

Usage:
    uv run python scripts/run_m1_overlap_report.py [--skip H106]
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import polars as pl

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT / "scripts"))

from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

SEED = 20260719  # justify: registered H105 scan seed; this report is deterministic (no RNG)

_PREDICTIONS = {
    ("orb_first_hour_k1.0@1.0.0", "overnight_session_drift_k1.0@1.0.0"): {
        "bar_level": (
            "EXACTLY 0 (H105 design §12(c) identity; nonzero falsifies the implementation)"
        ),
        "session_level": "≈ 0.75-0.95 (H105 design §12(c))",
    },
    ("orb_first_hour_k1.0@1.0.0", "vr_range_reversal_k1.0@1.0.0"): {
        "bar_level": "≈ 0.05-0.25 (H106 design §12(c); structural guess, declared)",
        "session_level": "≈ 0.85-1.0 (H106 design §12(c))",
    },
    ("overnight_session_drift_k1.0@1.0.0", "vr_range_reversal_k1.0@1.0.0"): {
        "bar_level": "no frozen numeric band (required report per H106 design §12(c))",
        "session_level": "no frozen numeric band (required report)",
    },
}


def _load_script(name: str, fname: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _ROOT / "scripts" / fname)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _active_bars(paths: ProjectPaths, expert_id: str, symbol: str) -> pl.DataFrame:
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
        .filter(pl.col("ret_gross") != 0)
        .select("session_date", "bar_ts")
        .collect()
    )


def _coverage(
    paths: ProjectPaths, expert_id: str, member_sessions: dict[str, set]
) -> tuple[set, set]:
    """(bar tuples, session tuples) within each instrument's member sessions."""
    bars: set = set()
    sessions: set = set()
    for symbol, mem in member_sessions.items():
        if not mem:
            continue
        frame = _active_bars(paths, expert_id, symbol)
        frame = frame.filter(pl.col("session_date").is_in(sorted(mem)))
        for sd, ts in zip(
            frame.get_column("session_date").to_list(),
            frame.get_column("bar_ts").to_list(),
            strict=True,
        ):
            bars.add((symbol, ts))
            sessions.add((symbol, sd))
    return bars, sessions


def _orb_member_sessions(paths: ProjectPaths) -> dict[str, set]:
    """Union of the ORB hash's recorded passing cells (H101 + H103)."""
    rc1 = _load_script("rc_h101_harness", "run_rc_h101_1_scan.py")
    rc2 = _load_script("rc_h101_h103_screen", "run_screen_h101_h103.py")
    out: dict[str, set] = {}
    # Recorded passing cells per instrument (pool ledger competence_window_cells).
    h101_cells = {"ES": ("first_hour_up",), "NQ": ("high_vol", "first_hour_up")}
    h103_cells = {"ES": ("stress", "first_hour_up"), "NQ": ("non_stress", "first_hour_up")}
    for symbol in ("ES", "NQ"):
        ledger = rc1._kelly1_gross_ledger(paths, symbol)
        covs = rc1._session_covariates(paths, symbol)
        df = ledger.join(covs, on="session_date", how="inner").sort("session_date")
        dates = df.get_column("session_date").to_list()
        gross = df.get_column("gross").to_numpy()
        entered = (df.get_column("n_active").to_numpy() > 0) & np.isfinite(gross)
        rvol = df.get_column("rvol").to_numpy()
        fh = df.get_column("fh_sign").to_numpy()
        cells = rc1._cells(entered, rvol, fh)
        mem: set = set()
        for c in h101_cells[symbol]:
            mem |= {d for d, m in zip(dates, cells[c], strict=True) if m}
        # H103 stress/non_stress: certified per-origin labels.
        labels, _ = rc2._h103_stress_labels(paths, rc1, symbol)
        lab = df.join(labels, on="session_date", how="left", maintain_order="left")
        stress_col = lab.get_column("stress").to_list()
        labeled = [s is not None for s in stress_col]
        for c in h103_cells[symbol]:
            if c == "stress":
                sel = [
                    d
                    for d, e, s, has in zip(dates, entered, stress_col, labeled, strict=True)
                    if e and has and bool(s)
                ]
            elif c == "non_stress":
                sel = [
                    d
                    for d, e, s, has in zip(dates, entered, stress_col, labeled, strict=True)
                    if e and has and not bool(s)
                ]
            else:  # first_hour_up already unioned via the H101 cells
                continue
            mem |= set(sel)
        out[symbol] = mem
    return out


def _candidate_member_sessions(paths: ProjectPaths, hid: str) -> dict[str, set] | None:
    """Passing-cell member sessions for a fresh candidate from its screen artifact."""
    artifact = paths.root / "reports" / hid / f"rc_{hid.lower()}_1_screen.json"
    if not artifact.is_file():
        return None
    blob = json.loads(artifact.read_text(encoding="utf-8"))
    passing = {
        inst["instrument"]: [c["cell"] for c in inst["cells"] if c.get("screen_pass")]
        for inst in blob["instruments"]
    }
    if not any(passing.values()):
        return {}
    harness = _load_script(f"rc_{hid.lower()}_harness_m1", f"run_screen_{hid.lower()}.py")
    out: dict[str, set] = {}
    for symbol, cell_names in passing.items():
        if not cell_names:
            out[symbol] = set()
            continue
        data = harness._prepare_instrument(paths, symbol)
        mem: set = set()
        for c in cell_names:
            mask = data.cells[c]
            mem |= {d for d, m in zip(data.dates, mask, strict=True) if m}
        out[symbol] = mem
    return out


def _jaccard(a: set, b: set) -> float | None:
    union = a | b
    if not union:
        return None
    return len(a & b) / len(union)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip", nargs="*", default=[], choices=["H105", "H106"])
    args = parser.parse_args()
    paths = ProjectPaths.discover()

    log = reproducibility.capture(
        phase="m1-realized-overlap-report",
        hypothesis_id="n/a",  # cross-candidate companion statistic, not a scan
        rng_seed=SEED,
        dataset_checksums={},
        config_resolved_sha256=None,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name}", flush=True)

    coverages: dict[str, tuple[set, set]] = {}
    print("[orb] recomputing recorded cell membership (incl. per-origin stress)...", flush=True)
    coverages["orb_first_hour_k1.0@1.0.0"] = _coverage(
        paths, "orb_first_hour_k1.0@1.0.0", _orb_member_sessions(paths)
    )
    for hid, expert_id in (
        ("H105", "overnight_session_drift_k1.0@1.0.0"),
        ("H106", "vr_range_reversal_k1.0@1.0.0"),
    ):
        if hid in args.skip:
            print(f"[{hid}] skipped by flag", flush=True)
            continue
        mem = _candidate_member_sessions(paths, hid)
        if mem is None:
            print(f"[{hid}] screen artifact absent; skipped", flush=True)
            continue
        if not mem:
            print(f"[{hid}] screen FAIL (no passing cells); coverage empty", flush=True)
            coverages[expert_id] = (set(), set())
            continue
        coverages[expert_id] = _coverage(paths, expert_id, mem)

    result: dict = {
        "repro_log": log_path.name,
        "governing_rule": (
            "ADR-0015 label-based verdict precondition GOVERNS; M1 is the "
            "mandatory REPORTED companion (setup plan §2.3); meeting any "
            "threshold is reported, never acted on autonomously"
        ),
        "coverage_sizes": {
            k: {"n_bars": len(b), "n_sessions": len(s)} for k, (b, s) in coverages.items()
        },
        "pairs": [],
    }
    names = list(coverages)
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            (ba, sa), (bb, sb) = coverages[a], coverages[b]
            pred = _PREDICTIONS.get((a, b)) or _PREDICTIONS.get((b, a)) or {}
            pair = {
                "experts": [a, b],
                "bar_level_jaccard": _jaccard(ba, bb),
                "session_level_jaccard": _jaccard(sa, sb),
                "n_shared_bars": len(ba & bb),
                "n_shared_sessions": len(sa & sb),
                "pre_scan_prediction": pred,
            }
            result["pairs"].append(pair)
            print(
                f"  {a} vs {b}: J_bar={pair['bar_level_jaccard']} "
                f"J_session={pair['session_level_jaccard']}",
                flush=True,
            )

    out_dir = paths.root / "reports" / "M1_overlap"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "m1_realized_overlap.json"
    out_path.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(f"Wrote {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
