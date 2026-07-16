"""Tests for the reference smoke expert (contract conformance + causality)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import numpy as np
import pytest

from skie_universe2.experts.base import BarWindow, Expert, assert_prefix_invariant
from skie_universe2.experts.reference import CausalMomentumExpert


def _bars(n: int, seed: int) -> BarWindow:
    rng = np.random.default_rng(seed)
    close = 100.0 + np.cumsum(rng.normal(0, 1, n))
    base = datetime(2025, 1, 6, 9, 30, tzinfo=UTC)
    return BarWindow(
        ts=[base + timedelta(minutes=5 * i) for i in range(n)],
        open=close,
        high=close + 0.5,
        low=close - 0.5,
        close=close,
        volume=np.full(n, 1000.0),
    )


def test_conforms_to_protocol() -> None:
    assert isinstance(CausalMomentumExpert(), Expert)


def test_expert_id_versioned() -> None:
    assert CausalMomentumExpert(lookback=3).expert_id == "ref_causal_mom_l3@1.0.0"


def test_signal_is_causal() -> None:
    assert_prefix_invariant(CausalMomentumExpert(lookback=3), _bars(60, 1))


def test_warmup_flat_then_signed() -> None:
    sig = CausalMomentumExpert(lookback=3).signal(_bars(40, 2))
    assert np.all(sig.direction[:3] == 0)  # warm-up flat
    assert set(np.unique(sig.direction)).issubset({-1, 0, 1})


def test_invalid_lookback_raises() -> None:
    with pytest.raises(ValueError, match="lookback must be >= 1"):
        CausalMomentumExpert(lookback=0)
