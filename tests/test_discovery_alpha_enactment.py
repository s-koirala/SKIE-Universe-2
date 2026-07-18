"""Enactment-coupling tests for the discovery-alpha numeric instantiation.

Step-2 closure of the reproduction gap around the ENACTED
``screening_error_rate_target`` (config/multipletest_family.yaml; artifact
``reports/discovery_alpha_calibration/discovery_alpha_calibration.json``;
ReproLog ``repro_log_ba92c200ec074f6e961d2a6632bb45ff.json``; generator
``scripts/run_discovery_alpha_calibration.py``, commit 65e1dc8 lineage).

Coverage (execution brief step 2.2):

- (i)   MPRR cutoff t* = lambda/(1+lambda): exact over a lambda grid,
        strictly monotone, boundary behaviour (0, +inf, negative, nan).
- (ii)  Enactment-band median: computed over enactment members ONLY,
        cardinality 24, band extrema match the artifact.
- (iii) Bootstrap CI: seed-reproducibility of the resampling primitive,
        CI brackets the enacted estimate, nan replicates dropped (not
        zero-filled) — pinned at source level, the semantics live inline
        in the frozen generator whose numerics must not be modified.
- (iv)  Config coupling: the YAML value equals the artifact's
        t_star_enacted at FULL float precision (== on the parsed floats),
        and the screen artifacts' S-d bounds are COMPUTED (1 - level,
        level), not independent literals.

These tests read committed artifacts; they do NOT re-run the calibration
(that is scripts/audits/check_discovery_alpha_reproduction.py).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
import yaml
from scripts.run_discovery_alpha_calibration import SEED as GENERATOR_SEED

from skie_universe2.inference.bootstrap import stationary_bootstrap_indices
from skie_universe2.inference.discovery_alpha import optimal_threshold

_ROOT = Path(__file__).resolve().parents[1]
_ARTIFACT = _ROOT / "reports" / "discovery_alpha_calibration" / "discovery_alpha_calibration.json"
_CONFIG = _ROOT / "config" / "multipletest_family.yaml"
_REPRO_LOG = _ROOT / "logs" / "reproducibility" / "repro_log_ba92c200ec074f6e961d2a6632bb45ff.json"
_GENERATOR = _ROOT / "scripts" / "run_discovery_alpha_calibration.py"
_SCREEN_ARTIFACTS = (
    _ROOT / "reports" / "H101" / "rc_h101_2_screen.json",
    _ROOT / "reports" / "H103" / "rc_h103_2_screen.json",
)
# justify: the registered enactment-band design is 2 instruments x 2 same-
# instrument mu-anchors x 3 H_dem multiples x 2 r variants = 24 points
# (generator module docstring; memo addendum section A.2). A cardinality
# drift means the enactment rule changed.
_ENACTMENT_BAND_CARDINALITY = 24


@pytest.fixture(scope="module")
def artifact() -> dict[str, Any]:
    return json.loads(_ARTIFACT.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def config() -> dict[str, Any]:
    return yaml.safe_load(_CONFIG.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# (i) MPRR cutoff t* = lambda / (1 + lambda)
# ---------------------------------------------------------------------------


def test_mprr_cutoff_exact_over_lambda_grid() -> None:
    """t* equals lambda/(1+lambda) EXACTLY (same float expression) on a grid."""
    # justify: grid spans the artifact's observed lambda range (1.04-31.3)
    # plus margins; 0 and large-lambda endpoints exercise the limits.
    grid = np.concatenate([np.array([0.0]), np.geomspace(1e-6, 1e6, 49)])
    for lam in grid:
        assert optimal_threshold(float(lam)) == float(lam) / (1.0 + float(lam))


def test_mprr_cutoff_strictly_monotone() -> None:
    grid = np.geomspace(1e-6, 1e6, 200)
    values = np.array([optimal_threshold(float(g)) for g in grid])
    assert np.all(np.diff(values) > 0.0)


def test_mprr_cutoff_boundaries() -> None:
    assert optimal_threshold(0.0) == 0.0
    at_inf = optimal_threshold(float("inf"))
    assert at_inf < 1.0
    # justify: the open-interval clamp is the generator's structural _EPS
    # guard; the cutoff must approach but never reach 1.
    assert 1.0 - at_inf <= 1e-9
    with pytest.raises(ValueError, match="non-negative"):
        optimal_threshold(-0.1)
    with pytest.raises(ValueError, match="non-negative"):
        optimal_threshold(float("nan"))


def test_enacted_level_consistent_with_mprr_identity(artifact: dict) -> None:
    """The enacted t* respects the odds identity t*/(1-t*) = lambda on the band.

    Every enactment-member band point must satisfy t* = lambda/(1+lambda)
    exactly as recorded (the artifact stores both).
    """
    members = [p for p in artifact["rd1_rd2_rd4_band"] if p["enactment_member"]]
    for point in members:
        lam = point["lambda"]
        assert point["t_star"] == optimal_threshold(lam)


# ---------------------------------------------------------------------------
# (ii) Enactment-band median over enactment members only
# ---------------------------------------------------------------------------


def test_enactment_band_median_members_only(artifact: dict) -> None:
    band = artifact["rd1_rd2_rd4_band"]
    members = [p["t_star"] for p in band if p["enactment_member"]]
    non_members = [p["t_star"] for p in band if not p["enactment_member"]]
    assert len(members) == _ENACTMENT_BAND_CARDINALITY
    assert non_members, "dwell-sensitivity (non-member) points must be recorded"

    enacted = artifact["enactment"]["screening_error_rate_target"]
    assert enacted == float(np.median(members))
    # Including the sensitivity points would CHANGE the median — the rule is
    # members-only, and this artifact must witness that distinction.
    assert enacted != float(np.median(members + non_members))


def test_enactment_band_extrema(artifact: dict) -> None:
    band = artifact["rd1_rd2_rd4_band"]
    members = [p["t_star"] for p in band if p["enactment_member"]]
    lo, hi = artifact["enactment"]["enactment_subset_band"]
    assert lo == min(members)
    assert hi == max(members)
    assert artifact["enactment"]["full_band_max_with_dwell_sensitivity"] == max(
        p["t_star"] for p in band
    )


# ---------------------------------------------------------------------------
# (iii) Bootstrap CI: seed reproducibility, bracketing, nan handling
# ---------------------------------------------------------------------------


def test_bootstrap_indices_seed_reproducible() -> None:
    """The resampling primitive is deterministic under the recorded seed."""
    # justify: n/block mirror the generator's per-session series scale (~2276
    # sessions, PW block length ~2.6); values only shape the fixture.
    n, block = 2276, 2.6
    idx_a = stationary_bootstrap_indices(
        n, block_length=block, rng=np.random.default_rng(GENERATOR_SEED)
    )
    idx_b = stationary_bootstrap_indices(
        n, block_length=block, rng=np.random.default_rng(GENERATOR_SEED)
    )
    assert np.array_equal(idx_a, idx_b)
    idx_c = stationary_bootstrap_indices(
        n, block_length=block, rng=np.random.default_rng(GENERATOR_SEED + 1)
    )
    assert not np.array_equal(idx_a, idx_c)


def test_generator_seed_matches_repro_log() -> None:
    log = json.loads(_REPRO_LOG.read_text(encoding="utf-8"))
    assert log["rng_seed"] == GENERATOR_SEED


def test_bootstrap_ci_brackets_enacted_level(artifact: dict) -> None:
    enacted = artifact["enactment"]["screening_error_rate_target"]
    ci_lo, ci_hi = artifact["enactment"]["bootstrap_ci95"]
    assert ci_lo <= enacted <= ci_hi
    assert 0.0 < ci_lo < ci_hi <= 1.0


def test_bootstrap_effective_count_consistent(artifact: dict) -> None:
    """Effective replicate count reflects drop-not-fill semantics."""
    en = artifact["enactment"]
    assert 0 < en["n_bootstrap_effective"] <= artifact["n_bootstrap"]
    assert en["n_partial_replicates"] >= 0
    assert en["n_dropped_evaluations"] >= 0


def test_nan_replicates_dropped_not_zero_filled_source_pin() -> None:
    """Source-level pin of the drop-not-fill semantics (2.2.iii).

    The semantics live inline in the frozen generator (whose numerics must
    not be modified, brief step 2.1), so the regression pin is on the source:
    the finite-filter idiom must be present and no zero-fill of the replicate
    vector may be introduced.
    """
    source = _GENERATOR.read_text(encoding="utf-8")
    assert "reps = reps[np.isfinite(reps)]" in source
    # Reject the known zero-fill idioms (audit QUANT-1-1: a source pin cannot
    # prove behaviour, so it at least enumerates the fill patterns that would
    # silently change the CI; the drop path itself is unexercised on this
    # ledger — n_dropped_evaluations == 0 — and a behavioural test would
    # require modifying the frozen generator).
    assert "nan_to_num" not in source
    assert "reps[~np.isfinite(reps)]" not in source
    assert "np.where(np.isfinite(reps)" not in source


# ---------------------------------------------------------------------------
# (iv) Config coupling at FULL float precision
# ---------------------------------------------------------------------------


def test_yaml_level_equals_artifact_t_star_exactly(artifact: dict, config: dict) -> None:
    level = config["screening_error_rate_target"]
    assert isinstance(level, float)
    assert level == artifact["enactment"]["screening_error_rate_target"]


def test_registered_family_block_matches_artifact(artifact: dict, config: dict) -> None:
    family = next(
        f for f in config["families"] if f["family_id"] == "allocator-confirmation-kelly-sweep"
    )
    reg = family["discovery_alpha_calibration"]
    assert reg["t_star_enacted"] == artifact["enactment"]["screening_error_rate_target"]
    assert reg["t_star_enacted"] == config["screening_error_rate_target"]
    assert reg["repro_log_run"] in artifact["repro_log"]
    assert (
        reg["criterion_decision"]
        == (artifact["rd5_criterion"]["screen_family_decision"]["criterion"])
    )


def test_screen_s_d_bounds_are_computed_from_level(config: dict) -> None:
    """Every screen-cell S-d bound equals (1 - level, level) EXACTLY.

    The bounds are runtime derivations from the registered level — a literal
    that drifts from the config value is the defect this test exists to catch.
    """
    level = config["screening_error_rate_target"]
    for path in _SCREEN_ARTIFACTS:
        screen = json.loads(path.read_text(encoding="utf-8"))
        cells_checked = 0
        for inst in screen["instruments"]:
            for cell in inst["cells"]:
                sd = cell["s_d"]
                assert sd["dsr_bound"] == 1.0 - level, f"{path.name}:{cell['cell']}"
                assert sd["pbo_bound"] == level, f"{path.name}:{cell['cell']}"
                cells_checked += 1
        assert cells_checked > 0
