"""Tests for the frozen Hansen (2005) SPA estimator.

Verification strategy (CLAUDE.md: confirm numerical results against a
reference implementation): the DETERMINISTIC components (stationary-bootstrap
kernel variance, LIL validity mask, the three recentering vectors) are
asserted EQUAL to ``arch.bootstrap.SPA`` (Sheppard) on shared inputs at
1e-12; the stochastic p-values are asserted CLOSE on a well-separated fixed
case (independent RNG streams; tolerance >> Monte-Carlo SE). Paper
properties pinned: p-value ordering lower <= consistent <= upper; power on a
dominant candidate; the headline poor-alternative insensitivity of the
consistent p-value vs the Reality-Check-style upper p-value (Hansen 2005:
the RC p-value is sensitive to — and can be inflated by — the inclusion of
poor and irrelevant alternatives; paraphrase, no verbatim quotation or
section pinpoint per audit LITERATURE-1-3/2-1).
"""

from __future__ import annotations

import numpy as np
import pytest
from arch.bootstrap import SPA as ArchSPA  # noqa: N811 — arch's class is named SPA

from skie_universe2.inference.hansen_spa import hansen_spa, sb_kernel_variance

_SEED = 20260719  # registered scan-family seed lineage (deterministic tests)
_B = 500
_BLOCK = 5.0


def _null_panel(t: int = 300, k: int = 4, seed: int = _SEED) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.normal(0.0, 1.0, size=(t, k))


class TestAgainstReference:
    """Deterministic-part equality + stochastic proximity vs arch.SPA.

    PRIVATE-API COUPLING (audit CODE-1-2): ``_loss_diff_var`` and
    ``_check_column_validity`` are arch internals with no public accessor —
    the exact reason ``arch==8.0.0`` is PINNED in pyproject.toml. If a
    deliberate arch upgrade renames them, update the pin and these two
    accessors together; a failure here after an upgrade is the pin doing
    its job, not an estimator regression.
    """

    def _arch(self, d: np.ndarray, reps: int = 1000) -> ArchSPA:
        # arch loss_diff = benchmark - models; benchmark 0, models -d -> d.
        spa = ArchSPA(
            np.zeros(d.shape[0]),
            -d,
            block_size=int(_BLOCK),
            reps=reps,
            bootstrap="stationary",
            studentize=False,
            seed=12345,
        )
        spa.compute()
        return spa

    def test_kernel_variance_matches_arch(self) -> None:
        d = _null_panel()
        spa = self._arch(d, reps=10)
        mine = sb_kernel_variance(d, _BLOCK)
        assert np.allclose(mine, spa._loss_diff_var, rtol=1e-12, atol=1e-12)

    def test_consistent_validity_mask_matches_arch(self) -> None:
        rng = np.random.default_rng(_SEED)
        d = rng.normal(0.0, 1.0, size=(300, 4))
        d[:, 2] -= 1.0  # one deeply poor candidate -> invalid for recentering
        spa = self._arch(d, reps=10)
        res = hansen_spa(d, block_length=_BLOCK, rng=np.random.default_rng(_SEED), n_bootstrap=5)
        assert np.array_equal(res.consistent_valid, spa._check_column_validity())
        assert not res.consistent_valid[2]

    def test_unstudentized_pvalues_close_to_arch(self) -> None:
        rng = np.random.default_rng(_SEED)
        d = rng.normal(0.0, 1.0, size=(400, 3))
        d[:, 0] += 0.08  # moderately superior candidate
        reps = 2000
        spa = self._arch(d, reps=reps)
        res = hansen_spa(
            d,
            block_length=_BLOCK,
            rng=np.random.default_rng(_SEED),
            n_bootstrap=reps,
            studentize=False,
        )
        ref = spa.pvalues  # index: lower, consistent, upper
        # Independent RNG streams: tolerance well above the MC standard error
        # (~sqrt(p(1-p)/B) ~ 0.011 at p=0.5, B=2000).
        assert abs(res.p_value_lower - ref["lower"]) < 0.05
        assert abs(res.p_value_consistent - ref["consistent"]) < 0.05
        assert abs(res.p_value_upper - ref["upper"]) < 0.05


class TestPaperProperties:
    def test_pvalue_ordering(self) -> None:
        d = _null_panel(t=250, k=5)
        d[:, 1] -= 0.5  # include a poor alternative so the bounds separate
        res = hansen_spa(d, block_length=_BLOCK, rng=np.random.default_rng(_SEED), n_bootstrap=_B)
        assert res.p_value_lower <= res.p_value_consistent <= res.p_value_upper

    def test_power_on_dominant_candidate(self) -> None:
        rng = np.random.default_rng(_SEED)
        d = rng.normal(0.0, 1.0, size=(400, 3))
        d[:, 0] += 0.5  # strongly superior
        res = hansen_spa(d, block_length=_BLOCK, rng=np.random.default_rng(_SEED), n_bootstrap=_B)
        assert res.p_value_consistent <= 0.01

    def test_null_not_rejected(self) -> None:
        res = hansen_spa(
            _null_panel(),
            block_length=_BLOCK,
            rng=np.random.default_rng(_SEED),
            n_bootstrap=_B,
        )
        assert res.p_value_consistent > 0.05

    def test_poor_alternative_insensitivity(self) -> None:
        """Hansen's headline: a terrible added candidate inflates the RC-style
        upper p-value but leaves the consistent p-value (nearly) unchanged."""
        rng = np.random.default_rng(_SEED)
        base = rng.normal(0.0, 1.0, size=(400, 2))
        base[:, 0] += 0.12
        awful = rng.normal(-2.0, 1.0, size=(400, 1))
        with_awful = np.hstack([base, awful])

        res_base = hansen_spa(
            base, block_length=_BLOCK, rng=np.random.default_rng(_SEED), n_bootstrap=_B
        )
        res_awful = hansen_spa(
            with_awful,
            block_length=_BLOCK,
            rng=np.random.default_rng(_SEED),
            n_bootstrap=_B,
        )
        mc_tol = 0.03  # justify: ~3x the MC SE at B=500; not a decision threshold
        assert res_awful.p_value_consistent <= res_base.p_value_consistent + mc_tol
        assert res_awful.p_value_upper >= res_base.p_value_upper - mc_tol
        assert not res_awful.consistent_valid[2]

    def test_deterministic_given_seed(self) -> None:
        d = _null_panel(t=150, k=3)
        a = hansen_spa(d, block_length=_BLOCK, rng=np.random.default_rng(7), n_bootstrap=200)
        b = hansen_spa(d, block_length=_BLOCK, rng=np.random.default_rng(7), n_bootstrap=200)
        assert a.statistic == b.statistic
        assert a.p_value_consistent == b.p_value_consistent

    def test_studentized_scale_invariance(self) -> None:
        """Studentization makes the statistic invariant to per-column scale."""
        rng = np.random.default_rng(_SEED)
        d = rng.normal(0.02, 1.0, size=(300, 2))
        scaled = d * np.array([1.0, 50.0])
        a = hansen_spa(d, block_length=_BLOCK, rng=np.random.default_rng(9), n_bootstrap=300)
        b = hansen_spa(scaled, block_length=_BLOCK, rng=np.random.default_rng(9), n_bootstrap=300)
        assert a.statistic == pytest.approx(b.statistic, rel=1e-9)
        assert a.p_value_consistent == b.p_value_consistent


class TestValidation:
    def test_rejects_nonfinite(self) -> None:
        d = _null_panel(t=50, k=2)
        d[3, 1] = np.nan
        with pytest.raises(ValueError, match="non-finite"):
            hansen_spa(d, block_length=_BLOCK, rng=np.random.default_rng(1), n_bootstrap=10)

    def test_rejects_degenerate_column(self) -> None:
        d = _null_panel(t=50, k=2)
        d[:, 1] = 0.0
        with pytest.raises(ValueError, match="degenerate"):
            hansen_spa(d, block_length=_BLOCK, rng=np.random.default_rng(1), n_bootstrap=10)

    def test_rejects_short_sample(self) -> None:
        with pytest.raises(ValueError, match="at least"):
            hansen_spa(
                np.zeros((2, 2)), block_length=1.0, rng=np.random.default_rng(1), n_bootstrap=10
            )

    def test_rejects_bad_block_length(self) -> None:
        with pytest.raises(ValueError, match="block_length"):
            hansen_spa(
                _null_panel(t=50, k=2),
                block_length=0.5,
                rng=np.random.default_rng(1),
                n_bootstrap=10,
            )
