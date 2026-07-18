"""Discovery-alpha enacted-level reproduction check (brief step 2.3).

Re-runs the frozen generator ``scripts/run_discovery_alpha_calibration.py``
(commit 65e1dc8 lineage; original ReproLog
``repro_log_ba92c200ec074f6e961d2a6632bb45ff.json``) into a scratch path and
compares the regenerated artifact FIELD-BY-FIELD against the enacted artifact
``reports/discovery_alpha_calibration/discovery_alpha_calibration.json``.

HARD GATE: ``enactment.screening_error_rate_target`` must be EXACTLY equal
(``==`` on the float, never isclose). Any other field mismatch is also a
reproduction failure, reported per JSON path.

IF REPRODUCTION FAILS this is a FINDING for operator adjudication, not a
tolerance question: ``screening_error_rate_target`` is ENACTED governance and
must NOT be changed, rounded, re-derived, or "corrected" by this script or by
anything downstream of it (brief step 2.4). This script only reports.

Pre-flight: the original ReproLog's recorded dataset checksums (the two RC-1
scan JSONs + the shadow-ledger roll-up) are recomputed and compared; on drift
the re-run would not be on the same substrate and the check aborts as ERROR
rather than reporting a spurious mismatch. Note: the original ReproLog's
``config_resolved_sha256`` snapshots the METHODOLOGY MEMO as of run time
(2026-07-17, pre-remediation working tree) and legitimately differs from the
committed memo (prose remediation between run and commit); it is informational
here, not a gate — the generator's numerics do not read the memo.

Emits its own 13-field ReproLog BEFORE the re-run (ReproLog-first, G2).

Usage:
    uv run python scripts/audits/check_discovery_alpha_reproduction.py \
        [--scratch runs/discovery_alpha_repro_check]

Exit codes: 0 = reproduced exactly; 1 = mismatch (FINDING); 2 = error.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import traceback
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))
sys.path.insert(0, str(_ROOT))  # scripts.* namespace import of the generator

from scripts.run_discovery_alpha_calibration import (  # noqa: E402
    SEED,
    _dataset_checksums,
    _json_sanitize,
    run_calibration,
)

from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

EXIT_REPRODUCED = 0  # justify: structural exit-code convention
EXIT_MISMATCH = 1  # justify: structural exit-code convention (FINDING)
EXIT_ERROR = 2  # justify: structural exit-code convention (unusable input)
_ORIGINAL_RUN_ID = "ba92c200ec074f6e961d2a6632bb45ff"
_ARTIFACT_REL = "reports/discovery_alpha_calibration/discovery_alpha_calibration.json"
# justify: readability cap on printed mismatch paths; the full diff is written
# to the scratch dir regardless.
_MAX_PRINTED = 20


def _diff(frozen: object, fresh: object, path: str, out: list[dict[str, object]]) -> None:
    """Recursive exact-equality diff; appends {path, frozen, fresh} rows."""
    if isinstance(frozen, dict) and isinstance(fresh, dict):
        for key in sorted(set(frozen) | set(fresh)):
            if key not in frozen or key not in fresh:
                out.append(
                    {
                        "path": f"{path}.{key}",
                        "frozen": frozen.get(key, "<absent>"),
                        "fresh": fresh.get(key, "<absent>"),
                    }
                )
                continue
            _diff(frozen[key], fresh[key], f"{path}.{key}", out)
        return
    if isinstance(frozen, list) and isinstance(fresh, list):
        if len(frozen) != len(fresh):
            out.append({"path": f"{path}.<len>", "frozen": len(frozen), "fresh": len(fresh)})
            return
        for i, (a, b) in enumerate(zip(frozen, fresh, strict=True)):
            _diff(a, b, f"{path}[{i}]", out)
        return
    if frozen != fresh:
        out.append({"path": path, "frozen": frozen, "fresh": fresh})


def _run(scratch_rel: str) -> int:
    paths = ProjectPaths.discover()
    artifact_path = paths.root / _ARTIFACT_REL
    original_log_path = paths.logs_reproducibility / f"repro_log_{_ORIGINAL_RUN_ID}.json"
    scratch = paths.root / scratch_rel
    scratch.mkdir(parents=True, exist_ok=True)

    try:
        frozen = json.loads(artifact_path.read_text(encoding="utf-8"))
        original_log = json.loads(original_log_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(
            f"[discovery-alpha-repro] ERROR: cannot load inputs: {exc}", file=sys.stderr, flush=True
        )
        return EXIT_ERROR

    if original_log["rng_seed"] != SEED:
        print(
            f"[discovery-alpha-repro] ERROR: generator SEED {SEED} != recorded "
            f"rng_seed {original_log['rng_seed']} — not the recorded protocol.",
            file=sys.stderr,
            flush=True,
        )
        return EXIT_ERROR

    # Substrate drift pre-flight: recompute the recorded dataset checksums.
    current_checksums = _dataset_checksums(paths)
    recorded_checksums = original_log["dataset_checksums"]
    drift = {
        key: {"recorded": recorded_checksums.get(key), "current": current_checksums.get(key)}
        for key in sorted(set(recorded_checksums) | set(current_checksums))
        if recorded_checksums.get(key) != current_checksums.get(key)
    }
    if drift:
        print(
            "[discovery-alpha-repro] ERROR: dataset checksum drift — the re-run "
            "would not be on the recorded substrate (S6: stop rather than "
            "substitute):",
            file=sys.stderr,
            flush=True,
        )
        for key, pair in drift.items():
            print(
                f"  {key}:\n    recorded {pair['recorded']}\n    current  {pair['current']}",
                file=sys.stderr,
                flush=True,
            )
        return EXIT_ERROR

    # ReproLog FIRST (G2), then the artifact-producing re-run.
    log = reproducibility.capture(
        phase="discovery-alpha-reproduction-check",
        hypothesis_id="P1-2.0-KELLY-SWEEP-DISCOVERY-ALPHA-CALIBRATE",
        rng_seed=SEED,
        dataset_checksums=current_checksums,
        config_resolved_sha256=hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"[discovery-alpha-repro] ReproLog: {log_path.name}", flush=True)

    fresh_raw = run_calibration(paths)
    # Round-trip through the generator's own serialization so both sides are
    # compared in identical JSON-normalized form.
    fresh = json.loads(
        json.dumps(_json_sanitize(fresh_raw), sort_keys=True, default=str, allow_nan=False)
    )
    (scratch / "discovery_alpha_calibration_regenerated.json").write_text(
        json.dumps(fresh, indent=2, sort_keys=True), encoding="utf-8"
    )

    frozen_cmp = {k: v for k, v in frozen.items() if k != "repro_log"}
    fresh_cmp = {k: v for k, v in fresh.items() if k != "repro_log"}
    mismatches: list[dict[str, object]] = []
    _diff(frozen_cmp, fresh_cmp, "$", mismatches)
    (scratch / "reproduction_diff.json").write_text(
        json.dumps(
            {
                "original_run_id": _ORIGINAL_RUN_ID,
                "check_run_id": log.run_id,
                "n_mismatches": len(mismatches),
                "mismatches": mismatches,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    frozen_t = frozen["enactment"]["screening_error_rate_target"]
    fresh_t = fresh["enactment"]["screening_error_rate_target"]
    t_exact = frozen_t == fresh_t  # HARD GATE: float ==, not isclose
    print(f"[discovery-alpha-repro] t_star_enacted (frozen) = {frozen_t!r}", flush=True)
    print(f"[discovery-alpha-repro] t_star_enacted (fresh)  = {fresh_t!r}", flush=True)
    print(f"[discovery-alpha-repro] exact float equality    = {t_exact}", flush=True)
    print(f"[discovery-alpha-repro] field mismatches        = {len(mismatches)}", flush=True)

    if t_exact and not mismatches:
        print(
            "[discovery-alpha-repro] REPRODUCED: the enacted level "
            f"{frozen_t!r} regenerates exactly; all artifact fields equal.",
            flush=True,
        )
        return EXIT_REPRODUCED

    for row in mismatches[:_MAX_PRINTED]:
        print(
            f"  MISMATCH {row['path']}: frozen={row['frozen']!r} fresh={row['fresh']!r}", flush=True
        )
    if len(mismatches) > _MAX_PRINTED:
        print(f"  ... {len(mismatches) - _MAX_PRINTED} more (see scratch diff)", flush=True)
    print(
        "[discovery-alpha-repro] FINDING: reproduction failed. The enacted "
        "config value MUST NOT be changed or 'corrected'; record the "
        "discrepancy and halt for operator adjudication (brief step 2.4).",
        file=sys.stderr,
        flush=True,
    )
    return EXIT_MISMATCH


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scratch", default="runs/discovery_alpha_repro_check")
    args = parser.parse_args()
    try:
        return _run(args.scratch)
    except Exception:  # noqa: BLE001 — crash-to-ERROR mapping (audit CODE-1-1):
        # an uncaught exception would exit 1, indistinguishable from
        # EXIT_MISMATCH; a crashed check must never read as a reproduction
        # FINDING.
        traceback.print_exc(file=sys.stderr)
        print(
            "[discovery-alpha-repro] ERROR: check crashed (traceback above); "
            "NOT a reproduction finding.",
            file=sys.stderr,
            flush=True,
        )
        return EXIT_ERROR


if __name__ == "__main__":
    raise SystemExit(main())
