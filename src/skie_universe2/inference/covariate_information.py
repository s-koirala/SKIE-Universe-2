"""H001 covariate-information estimators (design §4/§5/§8).

Reference estimators for the H001 conditioning-covariate non-redundancy study
([research/01_hypothesis_register/H001/design.md]):

- :func:`forward_variance_ratio` — the §4 forward target ``Y(t)``: a
  self-normalizing within-window realized variance-ratio proxy
  ``VR_h(t) = (Σ r)^2 / (h · RV_h)`` over the forward window ``(t, t+h]``,
  bounded ``[0, h]``, ``E ≈ 1`` under a random walk; ``<1`` reversion, ``>1``
  continuation. Degenerate windows (forward ``RV_h = 0``) → NaN (§4 drop rule).
- :func:`conditional_mutual_information` — the §5 primary statistic
  ``I(Y ; S_vt | Z)`` with a Miller-Madow bias correction (plug-in entropies,
  nats).
- :func:`cmi_pointwise_contributions` — per-bar plug-in CMI contributions whose
  mean is the plug-in CMI; the series the §8 pooled bar-level stationary
  bootstrap resamples for the CI.
- :func:`stratified_permutation_pvalue` — the §5/§8 conditional
  (within-``Z``-cell) restricted-permutation null (Runge 2018): permute ``Y``
  only within strata of ``Z``, preserving ``p(Y | Z)``.
- :func:`nested_predictive_delta` — the §5 nested out-of-sample
  predictive-information delta (log-loss + McFadden pseudo-R²) of the augmented
  model ``{Z, S_vt}`` over the baseline ``{Z}``; the ADR-0002(d) marginal-
  information analogue (Grinold 1989).
- :func:`partition_redundancy` — descriptive adjusted Rand / adjusted mutual
  information (Hubert & Arabie 1985; Vinh, Epps & Bailey 2010) of ``S_vt`` vs
  each registered comparison covariate.

All entropies/CMI are in **nats**. Integer label arrays are categorical codes;
callers drop bars where any of ``Y``, ``S_hmm``, ``S_vr`` is invalid before
calling (the emitter's UNDETERMINED ``S_vt`` state is a valid category).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.lib.stride_tricks import sliding_window_view
from numpy.typing import NDArray
from sklearn.metrics import adjusted_mutual_info_score, adjusted_rand_score

# Default permutation-null replicate count — a Monte-Carlo precision choice for
# the p-value (resolution 1/(B+1)), not an analysis parameter. 999 gives a
# min p-value of 1e-3, adequate below any deferred screening level.
DEFAULT_N_PERMUTATIONS = 999  # justify: MC permutation resolution, not a tunable threshold

# Random-walk null of the self-normalizing variance-ratio proxy: E[VR_h] ≈ 1, so
# the sign split is at 1 (VR>1 continuation, VR<1 reversion). Derived from the
# estimator's construction (design §4), not a tuned threshold.
VR_RANDOM_WALK = 1.0  # justify: E[VR_h]=1 under a random walk (design §4 derivation)


# ── §4 forward variance-ratio target ──────────────────────────────────


def forward_variance_ratio(log_returns: NDArray[np.float64], h: int) -> NDArray[np.float64]:
    """Self-normalizing within-window realized variance-ratio proxy (design §4).

    ``VR_h(t) = (Σ_{i=1..h} r_{t+i})^2 / (Σ_{i=1..h} r_{t+i}^2)`` over the forward
    window ``(t, t+h]`` (note ``h · RV_h = Σ r^2``). Aligned to bar ``t``; the
    last ``h`` bars have no full forward window → NaN. Degenerate forward windows
    (``Σ r^2 = 0``, i.e. all forward returns zero) → NaN (§4 drop rule). Any NaN
    forward return propagates to NaN.

    Parameters
    ----------
    log_returns : 1-D float array
        Per-bar log returns (``r[t]`` realized at bar ``t``).
    h : int
        Forward horizon in bars (``>= 1``).

    Returns
    -------
    NDArray[np.float64]
        Same length as *log_returns*; ``VR_h(t)`` at bar ``t``, NaN where
        undefined.
    """
    if h < 1:
        raise ValueError(f"h must be >= 1, got {h}")
    r = np.asarray(log_returns, dtype=np.float64)
    if r.ndim != 1:
        raise ValueError(f"log_returns must be 1-D, got {r.ndim}-D")
    n = r.size
    out = np.full(n, np.nan, dtype=np.float64)
    if n <= h:
        return out
    windows = sliding_window_view(r, h)  # (n-h+1, h); windows[j] = r[j:j+h]
    fwd = windows[1:]  # forward window for bar t = r[t+1 : t+h+1]  (t = 0..n-h-1)
    s = fwd.sum(axis=1)
    ss = (fwd**2).sum(axis=1)
    with np.errstate(invalid="ignore", divide="ignore"):
        y = np.where(ss > 0.0, s * s / ss, np.nan)
    out[: y.size] = y
    return out


def vr_sign_label(vr: NDArray[np.float64]) -> NDArray[np.int64]:
    """Binary sign-of-``VR_h − 1`` label (design §5): 1 continuation, 0 reversion.

    Invalid (NaN) targets are encoded as ``-1`` so callers can mask them out.
    """
    vr = np.asarray(vr, dtype=np.float64)
    out = np.full(vr.shape, -1, dtype=np.int64)
    valid = np.isfinite(vr)
    out[valid] = (vr[valid] > VR_RANDOM_WALK).astype(np.int64)
    return out


# ── §5 conditional mutual information (Miller-Madow) ───────────────────


def _encode(*cols: NDArray[np.int64]) -> NDArray[np.int64]:
    """Encode joint tuples of small-cardinality integer columns into codes.

    Mixed-radix combination (no sort/unique): each column is shifted to a
    non-negative offset and folded in with a running multiplier. Codes are
    non-negative but not necessarily contiguous; entropy/count consumers use
    ``np.bincount`` so gaps are harmless. Fast for the low-cardinality label
    columns here (``y``≤2, ``S_vt``≤5, ``S_hmm``≤4, ``S_vr``≤3).
    """
    code = None
    mult = 1
    for c in cols:
        a = np.asarray(c, dtype=np.int64).ravel()
        a = a - a.min()
        k = int(a.max()) + 1 if a.size else 1
        code = a * mult if code is None else code + a * mult
        mult *= k
    return code if code is not None else np.zeros(0, dtype=np.int64)


def _z_codes(z: NDArray[np.int64]) -> NDArray[np.int64]:
    """Collapse a conditioning set ``z`` (shape ``(N,)`` or ``(N, k)``) to codes."""
    z = np.asarray(z, dtype=np.int64)
    if z.ndim == 1:
        return _encode(z)
    return _encode(*[z[:, j] for j in range(z.shape[1])])


def _entropy_mm_nats(codes: NDArray[np.int64]) -> float:
    """Miller-Madow-corrected plug-in entropy (nats): ``H_hat + (K-1)/(2N)``."""
    counts = np.bincount(codes)
    counts = counts[counts > 0]
    total = counts.sum()
    p = counts / total
    h_plugin = -np.sum(p * np.log(p))
    k = counts.size
    return float(h_plugin + (k - 1) / (2.0 * total))


def conditional_mutual_information(
    y: NDArray[np.int64],
    x: NDArray[np.int64],
    z: NDArray[np.int64],
) -> float:
    """Miller-Madow-corrected ``I(Y ; X | Z)`` in nats (design §5).

    Uses the entropy identity ``I(Y;X|Z) = H(Y,Z) + H(X,Z) − H(Z) − H(X,Y,Z)``
    with each term Miller-Madow bias-corrected. May be slightly negative from
    over-correction on sparse tables; that is expected and handled by the CI.
    """
    y = np.asarray(y, dtype=np.int64)
    x = np.asarray(x, dtype=np.int64)
    zc = _z_codes(z)
    return (
        _entropy_mm_nats(_encode(y, zc))
        + _entropy_mm_nats(_encode(x, zc))
        - _entropy_mm_nats(zc)
        - _entropy_mm_nats(_encode(x, y, zc))
    )


def cmi_pointwise_contributions(
    y: NDArray[np.int64],
    x: NDArray[np.int64],
    z: NDArray[np.int64],
) -> NDArray[np.float64]:
    """Per-bar plug-in CMI contributions (nats); their mean is the plug-in CMI.

    Contribution at bar ``t`` is
    ``log[ p(x,y,z) · p(z) / (p(x,z) · p(y,z)) ]`` from plug-in counts. This is
    the pooled bar-level series the §8 stationary bootstrap resamples for the CI.
    """
    y = np.asarray(y, dtype=np.int64)
    x = np.asarray(x, dtype=np.int64)
    zc = _z_codes(z)
    n = y.size

    def _logp(codes: NDArray[np.int64]) -> NDArray[np.float64]:
        counts = np.bincount(codes)
        return np.log(counts[codes].astype(np.float64)) - np.log(n)

    return _logp(_encode(x, y, zc)) + _logp(zc) - _logp(_encode(x, zc)) - _logp(_encode(y, zc))


def stratified_permutation_pvalue(
    y: NDArray[np.int64],
    x: NDArray[np.int64],
    z: NDArray[np.int64],
    *,
    rng: np.random.Generator,
    n_permutations: int = DEFAULT_N_PERMUTATIONS,
) -> float:
    """Conditional (within-``Z``-cell) restricted-permutation p-value (design §5/§8).

    Permutes ``Y`` only within strata of ``Z`` (preserving ``p(Y | Z)`` while
    breaking the ``Y``–``X`` link), recomputes the Miller-Madow CMI, and returns
    ``(1 + #{CMI_perm >= CMI_obs}) / (1 + n_permutations)`` (Runge 2018).

    **Exchangeability caveat (binding on interpretation).** The within-cell
    shuffle assumes ``Y`` is exchangeable within each ``Z``-cell (i.i.d. draws from
    ``p(Y | Z)``). When ``Y`` is a forward statistic over OVERLAPPING windows (e.g.
    the H001 forward variance-ratio target, whose consecutive labels share ``h-1``
    returns), the i.i.d. shuffle understates the null variance and the p-value is
    **anti-conservative** (empirically ~6–10× at ``h``∈{6,12}). Use this as an
    ILLUSTRATIVE diagnostic only for such targets; the dependence-aware block
    bootstrap CI is the binding inference (design §8). For genuinely i.i.d.-within-
    cell targets the p-value is calibrated.
    """
    y = np.asarray(y, dtype=np.int64)
    x = np.asarray(x, dtype=np.int64)
    zc = _z_codes(z)
    obs = conditional_mutual_information(y, x, zc)
    # Pre-group bar indices by Z-stratum for O(N) per-permutation shuffling.
    strata = [np.flatnonzero(zc == zv) for zv in np.unique(zc)]
    ge = 1  # +1 includes the observed statistic (Davison & Hinkley convention)
    for _ in range(n_permutations):
        yp = y.copy()
        for idx in strata:
            yp[idx] = rng.permutation(y[idx])
        if conditional_mutual_information(yp, x, zc) >= obs:
            ge += 1
    return ge / (n_permutations + 1)


# ── §8 pooled bar-level stationary-bootstrap CI ────────────────────────


def _stationary_block_indices(n: int, p: float, rng: np.random.Generator) -> NDArray[np.int64]:
    """One stationary-bootstrap resample of indices via block generation.

    Draws geometric(``p``) block lengths from uniform starts and concatenates the
    (circular) blocks until ``n`` indices are produced (Politis-Romano 1994).
    Fully vectorised (no per-element loop) for speed on long pooled series;
    equivalent in distribution to
    :func:`skie_universe2.inference.bootstrap.stationary_bootstrap_indices`.
    """
    expected = max(1.0, 1.0 / p)
    n_blocks = int(np.ceil(n / expected * 1.5)) + 8
    starts = rng.integers(0, n, size=n_blocks)
    lengths = rng.geometric(p, size=n_blocks)
    while int(lengths.sum()) < n:  # extremely rare top-up
        starts = np.concatenate([starts, rng.integers(0, n, size=n_blocks)])
        lengths = np.concatenate([lengths, rng.geometric(p, size=n_blocks)])
    total = int(lengths.sum())
    within = np.arange(total) - np.repeat(np.cumsum(lengths) - lengths, lengths)
    idx = (np.repeat(starts, lengths) + within) % n
    return idx[:n].astype(np.int64)


@dataclass(frozen=True)
class BootstrapCI:
    """Point estimate and percentile CI of a pooled mean."""

    point: float
    ci_low: float
    ci_high: float
    n_bootstrap: int
    block_length: float


def stationary_bootstrap_mean_ci(
    values: NDArray[np.float64],
    *,
    block_length: float,
    rng: np.random.Generator,
    n_bootstrap: int,
    alpha: float = 0.05,
) -> BootstrapCI:
    """Percentile CI of the mean of a serially-dependent series (design §8).

    Resamples *values* with the Politis-Romano 1994 stationary bootstrap at the
    supplied (PW-selected) block length and returns the ``alpha`` percentile CI
    of the resample means. The point estimate is the raw mean.
    """
    v = np.asarray(values, dtype=np.float64)
    n = v.size
    if n == 0:
        raise ValueError("values must be non-empty")
    p = 1.0 / float(block_length)
    means = np.empty(n_bootstrap, dtype=np.float64)
    for b in range(n_bootstrap):
        means[b] = v[_stationary_block_indices(n, p, rng)].mean()
    lo, hi = np.quantile(means, [alpha / 2.0, 1.0 - alpha / 2.0])
    return BootstrapCI(
        point=float(v.mean()),
        ci_low=float(lo),
        ci_high=float(hi),
        n_bootstrap=n_bootstrap,
        block_length=float(block_length),
    )


# ── §5 nested out-of-sample predictive-information delta ───────────────


@dataclass(frozen=True)
class NestedDelta:
    """Nested OOS predictive-information delta (augmented − baseline)."""

    logloss_base: float
    logloss_aug: float
    delta_logloss: float  # base − aug; positive ⇒ S_vt improves prediction
    mcfadden_base: float
    mcfadden_aug: float
    delta_mcfadden: float  # aug − base; positive ⇒ S_vt adds pseudo-R²
    n_train: int
    n_test: int


def nested_predictive_delta(
    y_train: NDArray[np.int64],
    z_train: NDArray[np.int64],
    x_train: NDArray[np.int64],
    y_test: NDArray[np.int64],
    z_test: NDArray[np.int64],
    x_test: NDArray[np.int64],
) -> NestedDelta:
    """Nested OOS predictive-information delta of ``{Z, S_vt}`` over ``{Z}`` (design §5).

    Compares a saturated conditional model on **``Z``-cells** (baseline) with one
    on **``Z×S_vt`` joint cells** (augmented). Each model's per-cell probability is
    the add-one-smoothed train frequency ``(Σy+1)/(n+2)`` — analytically the
    (near-)MLE of a saturated logistic regression on one-hot cells, so this is the
    fully-interacted logistic model of design §5 evaluated in closed form (the
    additive main-effects form cannot represent ``p(Y|Z,S_vt)`` interactions). Test
    cells unseen in train fall back to the train base rate (train-only stats → no
    leakage). Scores test-slice log-loss and McFadden pseudo-R² (vs a train
    base-rate null). Requires both target classes in TRAIN and TEST.

    Parameters
    ----------
    y_train, y_test : 1-D int array
        Binary target (``0``/``1``).
    z_train, z_test : int array, shape ``(N,)`` or ``(N, k)``
        Conditioning covariate columns (``S_hmm``, ``S_vr``).
    x_train, x_test : 1-D int array
        The candidate covariate ``S_vt`` (may include the ``-1`` state).
    """
    y_train = np.asarray(y_train, dtype=np.int64)
    y_test = np.asarray(y_test, dtype=np.int64)
    if set(np.unique(y_train)) != {0, 1} or len(np.unique(y_test)) < 2:
        raise ValueError("nested delta requires both target classes in train and test")

    ntr = y_train.size
    z_tr = np.asarray(z_train, dtype=np.int64).reshape(ntr, -1)
    z_te = np.asarray(z_test, dtype=np.int64).reshape(y_test.size, -1)
    x_tr = np.asarray(x_train, dtype=np.int64).ravel()
    x_te = np.asarray(x_test, dtype=np.int64).ravel()
    z_cols = [np.concatenate([z_tr[:, j], z_te[:, j]]) for j in range(z_tr.shape[1])]
    x_col = np.concatenate([x_tr, x_te])

    base_rate = min(max(float(np.mean(y_train)), 1e-12), 1 - 1e-12)

    def _logloss(codes_all: NDArray[np.int64]) -> float:
        k = int(codes_all.max()) + 1
        n = np.bincount(codes_all[:ntr], minlength=k).astype(np.float64)
        s = np.bincount(codes_all[:ntr], weights=y_train.astype(np.float64), minlength=k)
        p = np.where(n > 0, (s + 1.0) / (n + 2.0), base_rate)
        pt = np.clip(p[codes_all[ntr:]], 1e-12, 1 - 1e-12)
        yt = y_test.astype(np.float64)
        return float(-np.mean(yt * np.log(pt) + (1 - yt) * np.log(1 - pt)))

    ll_base = _logloss(_encode(*z_cols))
    ll_aug = _logloss(_encode(*z_cols, x_col))
    yt = y_test.astype(np.float64)
    ll_null = float(-np.mean(yt * np.log(base_rate) + (1 - yt) * np.log(1 - base_rate)))

    mcf_base = 1.0 - ll_base / ll_null
    mcf_aug = 1.0 - ll_aug / ll_null
    return NestedDelta(
        logloss_base=ll_base,
        logloss_aug=ll_aug,
        delta_logloss=ll_base - ll_aug,
        mcfadden_base=mcf_base,
        mcfadden_aug=mcf_aug,
        delta_mcfadden=mcf_aug - mcf_base,
        n_train=ntr,
        n_test=int(y_test.size),
    )


# ── §5 descriptive partition redundancy ────────────────────────────────


@dataclass(frozen=True)
class PartitionRedundancy:
    """Adjusted Rand / adjusted mutual information of ``S_vt`` vs a covariate."""

    adjusted_rand: float
    adjusted_mutual_info: float


def partition_redundancy(
    s_vt: NDArray[np.int64],
    other: NDArray[np.int64],
) -> PartitionRedundancy:
    """Descriptive overlap of ``S_vt`` with a comparison partition (design §5).

    Adjusted Rand index (Hubert & Arabie 1985) and adjusted mutual information
    (Vinh, Epps & Bailey 2010); both chance-corrected, ``~0`` when independent.
    """
    return PartitionRedundancy(
        adjusted_rand=float(adjusted_rand_score(other, s_vt)),
        adjusted_mutual_info=float(adjusted_mutual_info_score(other, s_vt)),
    )
