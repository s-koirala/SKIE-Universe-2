"""H900 BOCPD-sensitivity reproduction gate (P1-2.0-H900-BOCPD-SENSITIVITY).

Closes audit finding QUANT-1-6 / ADR-0008: the claim that wiring the BOCPD
sensitivity detector into ``scripts/run_h900_dwell_study.py`` leaves the frozen
CUSUM decision object bit-identical was asserted but not codified. This script
diffs the committed frozen artifacts (``reports/H900``) against a fresh
BOCPD-run output directory (default ``reports/H900_bocpd_run``) and fails
loudly on any regression of the registered decision object.

Gate (per variant, both ``primary`` and ``inclusive``):
- ``h900_spells_{variant}.parquet``       : sorted-equal on all columns.
- ``h900_latency_{variant}.parquet``      : ``delay_bars`` + ``event`` sorted-
  equal; ``|delta threshold| <= THRESHOLD_TOL`` (pre-existing numba/BLAS
  float-noise in ``log(1/(1-a_ii))``, immaterial to every integer delay).
- ``h900_verdict_{variant}.json``         : the registered decision object
  (verdict + all instrument fields EXCEPT the additive BOCPD keys) is equal.

Usage:
    uv run python scripts/audits/check_h900_bocpd_reproduction.py \
        [--frozen reports/H900] [--regen reports/H900_bocpd_run]

Exit code 0 = reproduction holds; 1 = regression (details printed).
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

import polars as pl

# RELATIVE tolerance on the CUSUM threshold column. threshold = log(1/(1-a_ii))
# (~5.4) inherits ~1e-8 RELATIVE (~1e-7 absolute) BLAS/numba reduction-order
# noise from the EM fit across independent runs; delays (integers), spells, and
# the verdict are invariant. 1e-6 relative bounds the observed ~2e-8 with ~50x
# headroom while still catching any real logic change (which shifts the anchor
# by >> 1e-6).
THRESHOLD_REL_TOL = 1.0e-6

VARIANTS = ("primary", "inclusive")
# Total order (QUANT-2-5): include every column that distinguishes spell rows
# (grid cell + session rule + selected flag + event) so DataFrame.equals does
# not depend on polars stable-sort preserving construction order.
SPELL_SORT = [
    "instrument",
    "variant",
    "window_id",
    "n_states",
    "covariance_type",
    "session_rule",
    "selected",
    "state",
    "start_ts",
    "duration_bars",
    "event",
]
# 'event' (and 'threshold'/'hazard') appended so the ordering is total before
# the column comparisons — not reliant on stable-sort + construction order
# (REPRODUCIBILITY-3-3).
LAT_SORT = [
    "instrument",
    "variant",
    "window_id",
    "n_states",
    "covariance_type",
    "from_state",
    "to_state",
    "delay_bars",
    "event",
    "threshold",
]
# REPRO-2-1: the BOCPD deliverable is under the same bit-identity gate as the
# CUSUM object it is a sensitivity to.
BOCPD_SORT = [
    "instrument",
    "variant",
    "window_id",
    "n_states",
    "covariance_type",
    "from_state",
    "to_state",
    "delay_bars",
    "event",
    "hazard",
]


def _strip_bocpd(blob: dict) -> dict:
    """Registered decision object: drop the additive BOCPD-sensitivity keys."""
    out = copy.deepcopy(blob)
    out.pop("bocpd_sensitivity_verdict", None)
    for inst in out.get("instruments", {}).values():
        inst.pop("bocpd_sensitivity", None)
    return out


def _check_variant(frozen: Path, regen: Path, variant: str) -> list[str]:
    fails: list[str] = []

    a = pl.read_parquet(frozen / f"h900_spells_{variant}.parquet").sort(SPELL_SORT)
    b = pl.read_parquet(regen / f"h900_spells_{variant}.parquet").select(a.columns).sort(SPELL_SORT)
    if not a.equals(b):
        fails.append(f"[{variant}] spells differ (rows {a.height} vs {b.height})")

    a = pl.read_parquet(frozen / f"h900_latency_{variant}.parquet").sort(LAT_SORT)
    b = pl.read_parquet(regen / f"h900_latency_{variant}.parquet").select(a.columns).sort(LAT_SORT)
    if not (a["delay_bars"].equals(b["delay_bars"]) and a["event"].equals(b["event"])):
        fails.append(f"[{variant}] CUSUM delay_bars/event differ")
    rel = ((a["threshold"] - b["threshold"]).abs() / a["threshold"].abs().clip(1e-300)).max()
    if rel is not None and rel > THRESHOLD_REL_TOL:
        fails.append(f"[{variant}] threshold rel-drift {rel:.2e} > tol {THRESHOLD_REL_TOL:.0e}")

    # BOCPD sensitivity artifact (REPRO-2-1): same bit-identity gate.
    a = pl.read_parquet(frozen / f"h900_bocpd_latency_{variant}.parquet").sort(BOCPD_SORT)
    b = (
        pl.read_parquet(regen / f"h900_bocpd_latency_{variant}.parquet")
        .select(a.columns)
        .sort(BOCPD_SORT)
    )
    if not (a["delay_bars"].equals(b["delay_bars"]) and a["event"].equals(b["event"])):
        fails.append(f"[{variant}] BOCPD delay_bars/event differ")
    hrel = ((a["hazard"] - b["hazard"]).abs() / a["hazard"].abs().clip(1e-300)).max()
    if hrel is not None and hrel > THRESHOLD_REL_TOL:
        fails.append(f"[{variant}] BOCPD hazard rel-drift {hrel:.2e} > tol {THRESHOLD_REL_TOL:.0e}")

    va = _strip_bocpd(
        json.loads((frozen / f"h900_verdict_{variant}.json").read_text(encoding="utf-8"))
    )
    vb = _strip_bocpd(
        json.loads((regen / f"h900_verdict_{variant}.json").read_text(encoding="utf-8"))
    )
    if va != vb:
        fails.append(
            f"[{variant}] registered verdict object differs "
            f"(frozen={va.get('verdict')}, regen={vb.get('verdict')})"
        )

    if not fails:
        rel_str = "n/a" if rel is None else f"{rel:.2e}"
        print(
            f"[{variant}] OK  spells+CUSUM-delays+BOCPD-delays+event bit-identical; "
            f"threshold rel-drift {rel_str} <= {THRESHOLD_REL_TOL:.0e}; "
            f"verdict object identical."
        )
    return fails


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--frozen", default="reports/H900")
    p.add_argument("--regen", default="reports/H900_bocpd_run")
    args = p.parse_args()
    frozen, regen = Path(args.frozen), Path(args.regen)

    all_fails: list[str] = []
    for v in VARIANTS:
        all_fails.extend(_check_variant(frozen, regen, v))

    if all_fails:
        print("\nREPRODUCTION GATE FAILED:")
        for f in all_fails:
            print("  -", f)
        return 1
    print(
        "\nREPRODUCTION GATE PASSED: BOCPD wiring preserves the frozen "
        "H900 CUSUM decision object."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
