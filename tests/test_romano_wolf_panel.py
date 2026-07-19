"""Tests for the panel Romano-Wolf StepM variant (VERDICT-1 freeze, 2026-07-19).

The panel variant must mirror the frozen masked variant exactly where the two
constructions coincide: a k=1 panel equals the masked variant with a single
all-true mask on the same series and the same seeded Generator (identical
bootstrap draw sequence → identical statistics, adjusted p-values, and
rejection). Panel-specific properties pinned on top.
"""

from __future__ import annotations

import numpy as np
import pytest

from skie_universe2.inference.romano_wolf import (
    romano_wolf_stepm,
    romano_wolf_stepm_panel,
)

_SEED = 20260719
_B = 400
_BLOCK = 5.0


def test_k1_panel_equals_masked_full_mask() -> None:
    rng = np.random.default_rng(_SEED)
    x = rng.normal(0.02, 1.0, size=300)
    masked = romano_wolf_stepm(
        x,
        np.ones((1, x.size), dtype=bool),
        block_length=_BLOCK,
        rng=np.random.default_rng(7),
        n_bootstrap=_B,
        alpha=0.5,
    )
    panel = romano_wolf_stepm_panel(
        x[:, None],
        block_length=_BLOCK,
        rng=np.random.default_rng(7),
        n_bootstrap=_B,
        alpha=0.5,
    )
    assert panel.stat[0] == pytest.approx(masked.stat[0], rel=1e-12)
    assert panel.adjusted_pvalue[0] == pytest.approx(masked.adjusted_pvalue[0], rel=1e-12)
    assert bool(panel.rejected[0]) == bool(masked.rejected[0])


def test_dominant_column_identified() -> None:
    rng = np.random.default_rng(_SEED)
    panel = rng.normal(0.0, 1.0, size=(400, 4))
    panel[:, 2] += 0.4
    res = romano_wolf_stepm_panel(
        panel,
        block_length=_BLOCK,
        rng=np.random.default_rng(11),
        n_bootstrap=_B,
        alpha=0.1,
    )
    assert res.rejected[2]
    assert res.adjusted_pvalue[2] < 0.05


def test_null_mostly_unrejected() -> None:
    rng = np.random.default_rng(_SEED)
    panel = rng.normal(0.0, 1.0, size=(400, 4))
    res = romano_wolf_stepm_panel(
        panel,
        block_length=_BLOCK,
        rng=np.random.default_rng(11),
        n_bootstrap=_B,
        alpha=0.05,
    )
    assert not res.rejected.any()


def test_adjusted_p_monotone_in_stat_order() -> None:
    rng = np.random.default_rng(_SEED)
    panel = rng.normal(0.0, 1.0, size=(300, 5))
    panel += np.array([0.3, 0.15, 0.0, -0.15, -0.3])
    res = romano_wolf_stepm_panel(
        panel,
        block_length=_BLOCK,
        rng=np.random.default_rng(3),
        n_bootstrap=_B,
        alpha=0.1,
    )
    order = np.argsort(-res.stat)
    assert np.all(np.diff(res.adjusted_pvalue[order]) >= -1e-15)


def test_degenerate_constant_column_conventions() -> None:
    rng = np.random.default_rng(_SEED)
    panel = rng.normal(0.0, 1.0, size=(100, 3))
    panel[:, 1] = 0.5  # constant positive -> +inf stat convention
    res = romano_wolf_stepm_panel(
        panel,
        block_length=_BLOCK,
        rng=np.random.default_rng(5),
        n_bootstrap=50,
        alpha=0.5,
    )
    assert np.isinf(res.stat[1]) and res.stat[1] > 0


def test_rejects_nonfinite_panel() -> None:
    panel = np.zeros((50, 2))
    panel[3, 1] = np.nan
    with pytest.raises(ValueError, match="non-finite"):
        romano_wolf_stepm_panel(
            panel, block_length=1.0, rng=np.random.default_rng(1), n_bootstrap=10
        )


def test_deterministic_given_seed() -> None:
    rng = np.random.default_rng(_SEED)
    panel = rng.normal(0.01, 1.0, size=(200, 3))
    a = romano_wolf_stepm_panel(
        panel, block_length=_BLOCK, rng=np.random.default_rng(2), n_bootstrap=100
    )
    b = romano_wolf_stepm_panel(
        panel, block_length=_BLOCK, rng=np.random.default_rng(2), n_bootstrap=100
    )
    assert np.array_equal(a.adjusted_pvalue, b.adjusted_pvalue)
