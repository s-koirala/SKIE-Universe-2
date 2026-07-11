"""H900 HMM emission features — versioned feature registry.

Implements research/01_hypothesis_register/H900/design.md §3:

- ``ret_5m@1.0.0`` — 5-minute adjusted close-to-close log return on the
  roll-adjusted continuous contract (design §2 roll-handling note).
- ``rvol_5m_24h@1.0.0`` — realized volatility: square root of the
  rolling sum of squared 5-minute log returns over the trailing 288
  five-minute bars (24 hours). The 24h/288-bar convention is the 1.0
  H052a emission-feature convention (design §3 justification), carried
  unchanged for comparability with the 1.0 regime evidence.

The emission vector is ``(ret_5m, log(rvol_5m_24h))``, standardized per
training window using training-window moments only (design §3).

Point-in-time property: every feature at bar t is a function of bars
<= t only (trailing windows; no centering, no future shift). The
ADR-0008 leakage canary for this unsupervised pipeline is
:func:`pit_canary_future_mutation` — filtered states (and features) at
bar t must be invariant to arbitrary mutation of bars > t.

Aggregation rule (registered here per design §2): 5-minute bars are
built from the 1-minute substrate with polars ``group_by_dynamic``
(every=5m, closed='left', label='left'): open=first, high=max, low=min,
close=last, volume=sum. A bar labelled t covers [t, t+5m) and is
observable at t+5m; downstream indexing is in bar counts, so the label
convention carries no look-ahead (asserted by the canary).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import polars as pl

from skie_universe2.utils.sessions import cme_session_date_expr

# Feature registry (design.md §3 registered names/versions).
FEATURE_VERSIONS: dict[str, str] = {
    "ret_5m": "1.0.0",
    "rvol_5m_24h": "1.0.0",
}

BAR_MINUTES = 5  # justify: H900 design.md §2 registered evidence frequency
# justify: H900 design.md §3 — trailing 288 five-minute bars = 24 hours,
# the 1.0 H052a emission-feature convention carried unchanged.
RVOL_WINDOW_BARS = 288
# Emission vector dimension: (ret_5m, log rvol_5m_24h), design §3.
EMISSION_DIM = 2  # justify: H900 design.md §3 registered emission vector

# Maximum feature lookback == the design §6 purge width ("purge = 288
# bars (maximum feature lookback, §3)").
MAX_FEATURE_LOOKBACK_BARS = RVOL_WINDOW_BARS  # justify: H900 design.md §4/§6


@dataclass(frozen=True)
class ExclusionWindow:
    """One registered a-priori exclusion span (design.md §2 item (b)).

    ``start``/``end`` are inclusive CME-session-date bounds of a
    December-roll late-commit window from the substrate-defect register
    (data/processed/_provenance coverage_gaps entries, defect
    DEC_ROLL_LATE_COMMIT).
    """

    symbol: str
    start: date
    end: date


def exclusion_windows_from_provenance(coverage_gaps: list[dict]) -> tuple[ExclusionWindow, ...]:
    """Parse the provenance JSON ``coverage_gaps`` list into exclusion windows.

    Each entry carries ``expected_crossover_window`` = "YYYY-MM-DD ..
    YYYY-MM-DD"; the window is excluded inclusively on CME session dates.
    The register's ``terminal_window`` entries (December 2025 roll whose
    successor takeover falls beyond the sample) carry a prose upper
    bound — those windows are open-ended, excluded through end of data
    (``date.max``).
    """
    out = []
    for gap in coverage_gaps:
        lo, hi = (s.strip() for s in gap["expected_crossover_window"].split("..", maxsplit=1))
        try:
            end = date.fromisoformat(hi)
        except ValueError:
            end = date.max  # terminal window: open-ended through end of sample
        out.append(
            ExclusionWindow(
                symbol=gap["symbol"],
                start=date.fromisoformat(lo),
                end=end,
            )
        )
    return tuple(out)


def apply_registered_exclusions(
    bars_1min: pl.LazyFrame,
    *,
    symbol: str,
    exclusions: tuple[ExclusionWindow, ...],
    exclude_pit_provisional: bool,
    exclude_coverage_gaps: bool,
) -> pl.LazyFrame:
    """Apply the design §2 registered a-priori exclusions to 1-minute bars.

    Primary analysis: both flags True. Sensitivity (inclusion variant):
    both False. Exclusion (b) removes bars whose CME session date falls
    inside a registered December-roll late-commit window for this
    symbol; session-date attribution uses the shared
    ``cme_session_date_expr`` rule so it cannot drift from the ingest.
    """
    lf = bars_1min
    if exclude_pit_provisional:
        lf = lf.filter(~pl.col("pit_provisional"))
    if exclude_coverage_gaps:
        spans = [e for e in exclusions if e.symbol == symbol]
        if spans:
            session = cme_session_date_expr("ts_event")
            cond = pl.lit(False)
            for e in spans:
                cond = cond | (session.is_between(pl.lit(e.start), pl.lit(e.end)))
            lf = lf.filter(~cond)
    return lf


def aggregate_5min(bars_1min: pl.LazyFrame) -> pl.DataFrame:
    """Aggregate 1-minute bars to 5-minute bars (rule in module docstring)."""
    return (
        bars_1min.sort("ts_event")
        .group_by_dynamic("ts_event", every=f"{BAR_MINUTES}m", closed="left", label="left")
        .agg(
            open=pl.col("open").first(),
            high=pl.col("high").max(),
            low=pl.col("low").min(),
            close=pl.col("close").last(),
            volume=pl.col("volume").sum(),
        )
        .collect()
    )


def compute_emissions(bars_5m: pl.DataFrame) -> pl.DataFrame:
    """Compute the H900 emission features on a 5-minute bar frame.

    Adds columns ``ret_5m``, ``rvol_5m_24h``, ``log_rvol_5m_24h``,
    ``session_date`` and ``emission_valid``. Returns the full frame
    (invalid warm-up rows retained with ``emission_valid = False`` so
    callers can align bar indices).

    Passthrough contract (round-2 audit CODE-2-1): any extra columns on
    the input frame (e.g. the §7 ``unadjusted_close`` reference price)
    ride through the internal ``sort("ts_event")`` row-aligned with the
    computed features — callers must thread auxiliary per-bar columns
    THROUGH this function rather than re-attaching them positionally to
    the (re-sorted) output. Pinned by
    tests/test_h900_features_windows.py::TestComputeEmissions::
    test_passthrough_column_alignment_under_row_perturbation.

    Return convention (design §2): log return on the roll-adjusted
    close, close-to-close between CONSECUTIVE RETAINED bars. Where a
    registered exclusion removed the natural predecessor bars (gap to
    the previous retained bar exceeds one calendar week — only the
    December-roll exclusion windows produce such gaps on this
    substrate; ordinary weekend/holiday closures are <= 3 days), the
    return would span the excluded defective span, so it is set null
    and the rvol window restarts. Weekend/maintenance-break gaps keep
    their close-to-close return (a sojourn continues across the break,
    design §2 session rule).
    """
    # Gap classifier: exclusion-induced gaps are ~3.5 weeks (Dec-roll
    # windows); the longest natural market closure (weekend + adjacent
    # holiday) is <= 4 calendar days. 7 days separates the two regimes
    # with a wide margin on both sides — a classification boundary from
    # the substrate's structure, not a tunable analysis parameter.
    max_natural_gap = timedelta(days=7)  # justify: see gap-classifier note above
    df = bars_5m.sort("ts_event").with_columns(
        ret_5m=pl.col("close").log().diff(),
        _gap=pl.col("ts_event").diff(),
        session_date=cme_session_date_expr("ts_event"),
    )
    df = df.with_columns(
        ret_5m=pl.when(pl.col("_gap") > max_natural_gap).then(None).otherwise(pl.col("ret_5m"))
    )
    # rvol over trailing RVOL_WINDOW_BARS returns; requires a full,
    # null-free window (min_samples = window) so post-gap warm-up rows
    # are null rather than contaminated.
    df = df.with_columns(
        rvol_5m_24h=(
            pl.col("ret_5m")
            .pow(2)
            .rolling_sum(window_size=RVOL_WINDOW_BARS, min_samples=RVOL_WINDOW_BARS)
            .sqrt()
        )
    )
    # A zero rvol window (flat prices for 24h) would make log(rvol)
    # -inf; treat as invalid rather than feeding -inf to the HMM.
    df = df.with_columns(
        log_rvol_5m_24h=pl.when(pl.col("rvol_5m_24h") > 0)
        .then(pl.col("rvol_5m_24h").log())
        .otherwise(None)
    )
    df = df.with_columns(
        emission_valid=pl.col("ret_5m").is_not_null() & pl.col("log_rvol_5m_24h").is_not_null()
    ).drop("_gap")
    return df


@dataclass(frozen=True)
class StandardizationMoments:
    """Training-window feature moments (design §3: train moments only)."""

    mean: np.ndarray  # (2,)
    std: np.ndarray  # (2,)


def fit_moments(train_emissions: np.ndarray) -> StandardizationMoments:
    """Fit per-feature mean/std on the TRAINING emission matrix only."""
    x = np.asarray(train_emissions, dtype=np.float64)
    # noqa comment below: the ndim check is an array-RANK check that is 2
    # only coincidentally with EMISSION_DIM (round-2 audit CODE-2-2).
    if x.ndim != 2 or x.shape[1] != EMISSION_DIM:  # noqa: PLR2004 — rank check
        raise ValueError(f"emission matrix must be (T, {EMISSION_DIM}); got {x.shape!r}.")
    if not np.all(np.isfinite(x)):
        raise ValueError("emission matrix contains non-finite values.")
    mean = x.mean(axis=0)
    std = x.std(axis=0, ddof=0)
    if np.any(std <= 0):
        raise ValueError("degenerate training feature (zero variance); cannot standardize.")
    return StandardizationMoments(mean=mean, std=std)


def standardize(x: np.ndarray, moments: StandardizationMoments) -> np.ndarray:
    """Apply training-window moments to any emission matrix (train or eval)."""
    return (np.asarray(x, dtype=np.float64) - moments.mean) / moments.std


def emission_matrix(df: pl.DataFrame) -> np.ndarray:
    """Extract the (T, 2) emission matrix from valid rows of a feature frame."""
    valid = df.filter(pl.col("emission_valid"))
    return np.column_stack(
        [
            valid.get_column("ret_5m").to_numpy(),
            valid.get_column("log_rvol_5m_24h").to_numpy(),
        ]
    )


def pit_canary_future_mutation(
    bars_5m: pl.DataFrame,
    *,
    cut_index: int,
    rng: np.random.Generator,
) -> None:
    """ADR-0008 leakage canary for the unsupervised H900 pipeline.

    A supervised pipeline's canary injects a future-knowing feature and
    checks it dominates. H900 has no labels, so the canary asserts the
    equivalent point-in-time property directly: every feature value at
    bar index < ``cut_index`` must be bit-identical after arbitrary
    mutation of all bars >= ``cut_index``. Combined with the ported
    filter-prefix causality gate (filter_states(y[:t]) ==
    filter_states(y)[:t], tests/test_regime_hmm_fit.py), this proves
    filtered states at t are invariant to bars > t through the whole
    feature -> standardize -> filter chain.

    Raises AssertionError on any violation.
    """
    if not 0 < cut_index < bars_5m.height:
        raise ValueError(f"cut_index must be inside the frame; got {cut_index}.")
    base = compute_emissions(bars_5m)
    mutated_tail = bars_5m.slice(cut_index).with_columns(
        close=pl.col("close") * pl.lit(rng.uniform(1.5, 2.5)),
        high=pl.col("high") * pl.lit(rng.uniform(1.5, 2.5)),
        low=pl.col("low") * pl.lit(rng.uniform(0.4, 0.7)),
    )
    mutated = pl.concat([bars_5m.slice(0, cut_index), mutated_tail])
    got = compute_emissions(mutated)
    for col in ("ret_5m", "rvol_5m_24h", "log_rvol_5m_24h", "emission_valid"):
        a = base.get_column(col).head(cut_index)
        b = got.get_column(col).head(cut_index)
        if not a.equals(b):
            raise AssertionError(
                f"PIT canary FAILED: feature '{col}' changed before the "
                f"mutation cut (bar < {cut_index}) — look-ahead leak."
            )
