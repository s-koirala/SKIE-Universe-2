"""Gaussian HMM regime toolkit — numerical-fidelity port of SKIE-Universe 1.0.

Ported from ``SKIE-Universe@ce018515:src/skie_ninja/models/regime/`` per the
ADR-0008 audit-and-lift obligation for the H900 dwell-time feasibility gate
(research/01_hypothesis_register/H900/design.md §5). Deploy-time state
inference is the causal forward filter (``GaussianHMM.filter_states`` /
``filter_states_from_prior``) — never smoothed states, never Viterbi.
"""

from __future__ import annotations

from skie_universe2.models.regime._core import (
    BaumWelchResult,
    CovarianceType,
    HMMParams,
    baum_welch_em,
    bic,
    count_free_parameters,
)
from skie_universe2.models.regime.hmm import FitResult, GaussianHMM
from skie_universe2.models.regime.selection import (
    SelectionCandidate,
    SelectionResult,
    select_gaussian_hmm,
)

__all__ = [
    "BaumWelchResult",
    "CovarianceType",
    "FitResult",
    "GaussianHMM",
    "HMMParams",
    "SelectionCandidate",
    "SelectionResult",
    "baum_welch_em",
    "bic",
    "count_free_parameters",
    "select_gaussian_hmm",
]
