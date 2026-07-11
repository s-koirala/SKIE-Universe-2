"""H900 production run — dwell-time feasibility gate (ADR-0004 Decision 6).

Executes the frozen pre-registered design at
research/01_hypothesis_register/H900/design.md (SHA-256 recorded in the
emitted ReproLog as ``config_resolved_sha256``) over the Phase C
roll-adjusted evidence bars:

1. ADR-0008 leakage canary on the feature pipeline (future-mutation
   invariance; the causal-filter prefix gate is enforced by the ported
   unit tests).
2. Per instrument (ES, NQ) x 15 rolling-origin windows (design §2):
   24m train / 6m step, purge 288 bars, embargo = Politis-White block
   length on the training 5-minute returns.
3. Grid n_states {2,3,4} x cov {diag,full}, 5 EM restarts with the
   registered seed rule (restart i uses seed + i; design §5/§11), BIC
   selection per window per instrument; all cells kept as sensitivity;
   non-converged cells reported, never re-run (design §9).
4. Dwell spells from the CAUSAL filtered state sequence (warm-started
   at the purge+embargo boundary per the 1.0 fold-continuity rule);
   session-continuous spells primary, session-truncated sensitivity.
5. KM median + Greenwood CI per window; pooled median via stationary
   bootstrap over the chronological spell sequence (design §8).
6. CUSUM (Page 1954) detection latency against filtered change-points
   for the BIC-selected cell (design §7).
7. Break-even frontier D_be(mu) = L_detect + c_switch/mu over the
   registered mu grid; §10 verdict.

Deterministic: single registered seed (20260710); RNG only via
numpy Generator seeded explicitly; no wall-clock dependence in any
numeric path.

Usage:
    uv run python scripts/run_h900_dwell_study.py [--variant both]
        [--out reports/H900] [--skip-canary] [--max-windows N (dev only)]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import polars as pl

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.costs.futures_rt_v1 import (  # noqa: E402
    MU_CENTRAL,
    MU_GRID,
    FuturesRtV1CostModel,
    break_even_dwell_bars,
)
from skie_universe2.eval.windows import h900_windows  # noqa: E402
from skie_universe2.features.regime_emissions import (  # noqa: E402
    MAX_FEATURE_LOOKBACK_BARS,
    aggregate_5min,
    apply_registered_exclusions,
    compute_emissions,
    exclusion_windows_from_provenance,
    fit_moments,
    pit_canary_future_mutation,
    standardize,
)
from skie_universe2.inference.bootstrap import politis_white_block_length  # noqa: E402
from skie_universe2.inference.cusum import cusum_detection_delays  # noqa: E402
from skie_universe2.inference.survival import (  # noqa: E402
    km_fit,
    km_median,
    km_median_greenwood_ci,
    pooled_km_median_stationary_bootstrap,
)
from skie_universe2.models.regime._core import (  # noqa: E402
    bic as bic_score,
)
from skie_universe2.models.regime._core import (  # noqa: E402
    log_emission_matrix,
)
from skie_universe2.models.regime.dwell import extract_spells, filtered_state_path  # noqa: E402
from skie_universe2.models.regime.hmm import GaussianHMM  # noqa: E402
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.hashing import file_sha256  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

# ---------------------------------------------------------------------------
# Registered run parameters (every value traceable to the frozen design)
# ---------------------------------------------------------------------------

SEED = 20260710  # justify: H900 design.md §11 pre-registered RNG seed
N_RESTARTS = 5  # justify: H900 design.md §5 (5 EM restarts per cell)
RESTART_SEEDS = [SEED + i for i in range(N_RESTARTS)]  # justify: design §11 seed+i rule
N_STATES_GRID = (2, 3, 4)  # justify: H900 design.md §5 registered grid
COVARIANCE_GRID = ("diag", "full")  # justify: H900 design.md §5 registered grid
ALPHA = 0.05  # justify: H900 design.md §8 registered alpha
PURGE_BARS = MAX_FEATURE_LOOKBACK_BARS  # justify: design §6 purge = max feature lookback (288)
INSTRUMENTS = ("ES", "NQ")  # justify: H900 design.md §2 registered universe
SAMPLE_START = date(2015, 1, 2)  # justify: design §2 sample period start
SAMPLE_END = date(2025, 12, 31)  # justify: design §2 sample period end
# Bootstrap replication count for the pooled-median CI: the 1.0
# LW2008/H052a studentised-bootstrap convention (n=2000, see
# docs/reports/expert_card_H052a_retro §2) carried unchanged; MC error
# of the 2.5/97.5 percentile at B=2000 is well inside reporting
# precision.
N_BOOTSTRAP = 2000  # justify: 1.0 bootstrap replication convention (H052a LW2008 n=2000)
# Precision requirement (design §8): pooled D_med 95% CI half-width
# must be < 25% of the point estimate, else indeterminate.
PRECISION_HALF_WIDTH_FRAC = 0.25  # justify: H900 design.md §8 registered precision gate
DATASET = "vendor_legacy_1min_roll_adjusted"
PROVENANCE_FILE = "vendor_legacy_1min_roll_adjusted_20260711.json"


@dataclass
class CellResult:
    """One (window, grid-cell) fit + dwell record."""

    instrument: str
    variant: str
    window_id: int
    n_states: int
    covariance_type: str
    log_likelihood: float
    bic: float
    converged: bool
    n_restarts_used: int
    dead_state_events: int
    pd_ridge_events: int
    selected: bool
    n_train_bars: int
    n_eval_bars: int
    embargo_bars: int
    train_block_length: float
    # Continuous-session (primary) dwell summary on usable spells:
    n_spells: int
    n_events: int
    km_median_bars: float
    km_ci_low_bars: float
    km_ci_high_bars: float
    fit_error: str = ""


def _load_bars_1min(paths: ProjectPaths, symbol: str) -> pl.LazyFrame:
    glob = str(paths.data_processed / DATASET / f"symbol={symbol}" / "**" / "*.parquet")
    return pl.scan_parquet(glob).select(
        "ts_event",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "unadjusted_close",
        "pit_provisional",
    )


def _coverage_gaps(paths: ProjectPaths) -> list[dict]:
    payload = json.loads(
        (paths.data_processed / "_provenance" / PROVENANCE_FILE).read_text(encoding="utf-8")
    )
    return payload["coverage_gaps"]


def _dataset_checksums(paths: ProjectPaths) -> dict[str, str]:
    """Frozen per-file SHA-256 entries from data/_manifest.json (design §11)."""
    manifest = json.loads((paths.data / "_manifest.json").read_text(encoding="utf-8"))
    out = {}
    for key, entry in manifest["files"].items():
        if DATASET in key or key.endswith("_provenance/" + PROVENANCE_FILE):
            out[key] = entry["sha256"]
    if not out:
        raise RuntimeError("no dataset checksums found in data/_manifest.json")
    return out


def _utc(d: date) -> datetime:
    return datetime(d.year, d.month, d.day, tzinfo=None)


def _segment_ids(ts: np.ndarray, max_gap_days: float = 7.0) -> np.ndarray:
    """Contiguity segments of a valid-bar timestamp sequence.

    Split where consecutive valid bars are more than ``max_gap_days``
    apart — only the registered December-roll exclusion windows (plus
    their rvol warm-up shadow) produce such gaps; natural closures are
    <= 4 days (same classifier as compute_emissions).
    """
    if ts.size == 0:
        return np.empty(0, dtype=np.int64)
    gaps = np.diff(ts.astype("datetime64[s]").astype(np.int64))
    breaks = gaps > max_gap_days * 86400.0
    return np.concatenate([[0], np.cumsum(breaks)]).astype(np.int64)


def _spells_over_segments(
    states: np.ndarray,
    session_ord: np.ndarray,
    seg_ids: np.ndarray,
    *,
    truncate_at_session: bool,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Extract usable spells segment-by-segment.

    Returns (durations, events, states, chronological start positions).
    First spell of every segment is left-censored (dropped via
    ``usable()``); last spell of every segment is right-censored.
    """
    durations, events, st, starts = [], [], [], []
    for seg in np.unique(seg_ids):
        mask = seg_ids == seg
        sub = extract_spells(
            states[mask],
            session_ids=session_ord[mask] if truncate_at_session else None,
            truncate_at_session=truncate_at_session,
        ).usable()
        offset = int(np.flatnonzero(mask)[0])
        durations.append(sub.duration_bars)
        events.append(sub.event)
        st.append(sub.state)
        starts.append(sub.start_index + offset)
    return (
        np.concatenate(durations) if durations else np.empty(0, dtype=np.int64),
        np.concatenate(events) if events else np.empty(0, dtype=bool),
        np.concatenate(st) if st else np.empty(0, dtype=np.int64),
        np.concatenate(starts) if starts else np.empty(0, dtype=np.int64),
    )


def run_variant(  # noqa: PLR0912, PLR0915 — single-pass orchestrator mandated linear by design §9 (fixed grid, no re-runs); splitting would scatter the registered protocol
    *,
    paths: ProjectPaths,
    variant: str,
    instruments: tuple[str, ...],
    max_windows: int | None,
    out_dir: Path,
) -> tuple[dict, list[Path]]:
    """Run one exclusion variant end-to-end.

    Returns (verdict blob, explicit list of files written by this call —
    consumed by the CODE-1-4 model_hash).
    """
    exclude = variant == "primary"
    gaps = _coverage_gaps(paths)
    exclusions = exclusion_windows_from_provenance(gaps)
    windows = h900_windows()
    if max_windows is not None:
        windows = windows[:max_windows]  # dev-only truncation; never for production

    cost_model = FuturesRtV1CostModel.from_config(paths.config / "instruments.yaml")

    cell_rows: list[CellResult] = []
    spell_rows: list[dict] = []
    latency_rows: list[dict] = []
    per_instrument: dict[str, dict] = {}

    for symbol in instruments:
        t0 = time.perf_counter()
        lf = _load_bars_1min(paths, symbol).filter(
            pl.col("ts_event").is_between(
                pl.lit(_utc(SAMPLE_START)).dt.replace_time_zone("UTC"),
                pl.lit(_utc(SAMPLE_END) + timedelta(days=1)).dt.replace_time_zone("UTC"),
                closed="left",
            )
        )
        lf = apply_registered_exclusions(
            lf,
            symbol=symbol,
            exclusions=exclusions,
            exclude_pit_provisional=exclude,
            exclude_coverage_gaps=exclude,
        )
        bars_1m = lf.collect()
        # 5-minute aggregation needs OHLCV; carry unadjusted_close for
        # the §7 notional reference via a parallel last() aggregation.
        bars_5m = (
            bars_1m.lazy()
            .sort("ts_event")
            .group_by_dynamic("ts_event", every="5m", closed="left", label="left")
            .agg(
                open=pl.col("open").first(),
                high=pl.col("high").max(),
                low=pl.col("low").min(),
                close=pl.col("close").last(),
                volume=pl.col("volume").sum(),
                unadjusted_close=pl.col("unadjusted_close").last(),
            )
            .collect()
        )
        # Round-2 audit CODE-2-1: unadjusted_close is threaded THROUGH
        # compute_emissions as a passthrough column (row-aligned across
        # its internal ts_event sort) — never re-attached positionally.
        feats = compute_emissions(bars_5m)
        valid = feats.filter(pl.col("emission_valid")).sort("ts_event")
        ts_all = valid.get_column("ts_event").to_numpy()
        x_all = np.column_stack(
            [
                valid.get_column("ret_5m").to_numpy(),
                valid.get_column("log_rvol_5m_24h").to_numpy(),
            ]
        )
        session_ord = valid.get_column("session_date").cast(pl.Int32).to_numpy()
        unadj_close = valid.get_column("unadjusted_close").to_numpy()
        print(
            f"[{variant}/{symbol}] {bars_1m.height} 1-min bars -> "
            f"{valid.height} valid 5-min emission bars "
            f"({time.perf_counter() - t0:.1f}s)",
            flush=True,
        )

        pooled_durations: list[np.ndarray] = []
        pooled_durations_trunc: list[np.ndarray] = []
        pooled_events_trunc: list[np.ndarray] = []
        pooled_events: list[np.ndarray] = []
        pooled_delay: list[np.ndarray] = []
        pooled_delay_event: list[np.ndarray] = []
        eval_prices: list[np.ndarray] = []

        for w in windows:
            train_lo = np.searchsorted(ts_all, np.datetime64(_utc(w.train_start)))
            train_hi = np.searchsorted(ts_all, np.datetime64(_utc(w.origin)))
            eval_hi = np.searchsorted(ts_all, np.datetime64(_utc(w.eval_end)))
            fit_hi = train_hi - PURGE_BARS  # design §6 purge at the boundary
            x_train = x_all[train_lo:fit_hi]
            if x_train.shape[0] < PURGE_BARS:
                raise RuntimeError(f"window {w.window_id}: empty training span")
            moments = fit_moments(x_train)
            z_train = standardize(x_train, moments)

            # Embargo: PW 2004/PPW 2009 automatic block length on the
            # training 5-minute return series (design §6).
            sel = politis_white_block_length(x_train[:, 0], bootstrap_type="stationary")
            embargo_bars = int(np.ceil(sel.block_length))
            eval_lo = train_hi + embargo_bars
            x_eval = x_all[eval_lo:eval_hi]
            z_eval = standardize(x_eval, moments)
            ts_eval = ts_all[eval_lo:eval_hi]
            sess_eval = session_ord[eval_lo:eval_hi]
            seg_eval = _segment_ids(ts_eval)
            eval_prices.append(unadj_close[eval_lo:eval_hi])

            # ---- registered 6-cell grid, 5 restarts each ----
            fits: dict[tuple[int, str], GaussianHMM | None] = {}
            errors: dict[tuple[int, str], str] = {}
            bics: dict[tuple[int, str], float] = {}
            for n in N_STATES_GRID:
                for cov in COVARIANCE_GRID:
                    model = GaussianHMM(n_states=n, covariance_type=cov)
                    try:
                        model.fit(z_train, seed=SEED, restart_seeds=RESTART_SEEDS)
                        assert model.fit_result_ is not None
                        fits[(n, cov)] = model
                        bics[(n, cov)] = bic_score(
                            log_likelihood=model.fit_result_.best_log_likelihood,
                            n_states=n,
                            dim=z_train.shape[1],
                            covariance_type=cov,  # type: ignore[arg-type]
                            t_len=z_train.shape[0],
                        )
                    except Exception as exc:  # noqa: BLE001 — design §9: report, never re-run
                        fits[(n, cov)] = None
                        errors[(n, cov)] = f"{type(exc).__name__}: {exc}"

            # BIC argmin over successfully fitted cells (selection.py
            # convention: strict <, registered grid order breaks ties).
            selected_key: tuple[int, str] | None = None
            best = np.inf
            for n in N_STATES_GRID:
                for cov in COVARIANCE_GRID:
                    if (n, cov) in bics and bics[(n, cov)] < best:
                        best = bics[(n, cov)]
                        selected_key = (n, cov)

            for n in N_STATES_GRID:
                for cov in COVARIANCE_GRID:
                    key = (n, cov)
                    model = fits[key]
                    is_sel = key == selected_key
                    if model is None:
                        cell_rows.append(
                            CellResult(
                                instrument=symbol,
                                variant=variant,
                                window_id=w.window_id,
                                n_states=n,
                                covariance_type=cov,
                                log_likelihood=float("nan"),
                                bic=float("nan"),
                                converged=False,
                                n_restarts_used=0,
                                dead_state_events=0,
                                pd_ridge_events=0,
                                selected=False,
                                n_train_bars=int(z_train.shape[0]),
                                n_eval_bars=int(z_eval.shape[0]),
                                embargo_bars=embargo_bars,
                                train_block_length=float(sel.block_length),
                                n_spells=0,
                                n_events=0,
                                km_median_bars=float("nan"),
                                km_ci_low_bars=float("nan"),
                                km_ci_high_bars=float("nan"),
                                fit_error=errors[key],
                            )
                        )
                        continue
                    assert model.fit_result_ is not None and model.params_ is not None

                    # Causal filter over the eval span, warm-started from
                    # the train-fold terminal log-alpha propagated across
                    # the purge+embargo gap (1.0 fold-continuity rule).
                    prior = model.terminal_log_alpha(z_train)
                    n_prop = int(eval_lo - fit_hi)
                    post = model.filter_states_from_prior(z_eval, prior, n_propagation_steps=n_prop)
                    states = filtered_state_path(post)

                    # Round-1 audit CODE-1-3: the primary-rule spells are
                    # consumed after this loop, so bind them explicitly
                    # up front instead of leaking a loop variable.
                    dur_c, ev_c, st_c, starts_c = _spells_over_segments(
                        states, sess_eval, seg_eval, truncate_at_session=False
                    )
                    dur_t, ev_t, st_t, starts_t = _spells_over_segments(
                        states, sess_eval, seg_eval, truncate_at_session=True
                    )
                    for rule_name, (dur, ev, st, starts) in (
                        ("continuous", (dur_c, ev_c, st_c, starts_c)),
                        ("truncated", (dur_t, ev_t, st_t, starts_t)),
                    ):
                        for k in range(dur.size):
                            spell_rows.append(
                                {
                                    "instrument": symbol,
                                    "variant": variant,
                                    "window_id": w.window_id,
                                    "n_states": n,
                                    "covariance_type": cov,
                                    "selected": is_sel,
                                    "session_rule": rule_name,
                                    "state": int(st[k]),
                                    "start_ts": ts_eval[
                                        starts[k]
                                    ].item(),  # np.datetime64 -> datetime
                                    "duration_bars": int(dur[k]),
                                    "event": bool(ev[k]),
                                }
                            )
                    # Per-window KM on the continuous (primary) rule.
                    if dur_c.size and ev_c.any():
                        est = km_median_greenwood_ci(dur_c.astype(float), ev_c, alpha=ALPHA)
                        med, lo, hi = est.median, est.ci_low, est.ci_high
                    else:
                        med = lo = hi = float("nan")
                    cell_rows.append(
                        CellResult(
                            instrument=symbol,
                            variant=variant,
                            window_id=w.window_id,
                            n_states=n,
                            covariance_type=cov,
                            log_likelihood=float(model.fit_result_.best_log_likelihood),
                            bic=float(bics[key]),
                            converged=bool(
                                model.fit_result_.per_restart_converged[
                                    int(np.argmax(model.fit_result_.per_restart_log_likelihood))
                                ]
                            ),
                            n_restarts_used=int(model.fit_result_.n_restarts_used),
                            dead_state_events=int(model.fit_result_.best_dead_state_events),
                            pd_ridge_events=int(model.fit_result_.best_pd_ridge_events),
                            selected=is_sel,
                            n_train_bars=int(z_train.shape[0]),
                            n_eval_bars=int(z_eval.shape[0]),
                            embargo_bars=embargo_bars,
                            train_block_length=float(sel.block_length),
                            n_spells=int(dur_c.size),
                            n_events=int(ev_c.sum()),
                            km_median_bars=float(med),
                            km_ci_low_bars=float(lo),
                            km_ci_high_bars=float(hi),
                        )
                    )

                    if is_sel:
                        pooled_durations.append(dur_c.astype(float))
                        pooled_events.append(ev_c)
                        # Round-2 audit QUANT-2-1: the session-truncated
                        # sensitivity must get the SAME registered §8
                        # pooled-bootstrap treatment as the primary rule.
                        pooled_durations_trunc.append(dur_t.astype(float))
                        pooled_events_trunc.append(ev_t)
                        # CUSUM latency vs filtered change-points (§7).
                        log_b_eval = log_emission_matrix(
                            z_eval,
                            model.params_.means,
                            model.params_.covars,
                            model.params_.covariance_type,
                        )
                        for seg in np.unique(seg_eval):
                            m = seg_eval == seg
                            dd = cusum_detection_delays(
                                log_b_eval[m], states[m], model.params_.log_transmat
                            )
                            pooled_delay.append(dd.delay_bars.astype(float))
                            pooled_delay_event.append(dd.event)
                            for k in range(dd.delay_bars.size):
                                latency_rows.append(
                                    {
                                        "instrument": symbol,
                                        "variant": variant,
                                        "window_id": w.window_id,
                                        "n_states": n,
                                        "covariance_type": cov,
                                        "from_state": int(dd.from_state[k]),
                                        "to_state": int(dd.to_state[k]),
                                        "delay_bars": int(dd.delay_bars[k]),
                                        "event": bool(dd.event[k]),
                                        "threshold": float(dd.threshold[k]),
                                    }
                                )
            sel_txt = f"{selected_key[0]}-{selected_key[1]}" if selected_key else "none"
            print(
                f"[{variant}/{symbol}] window {w.window_id} "
                f"({w.origin} -> {w.eval_end}): selected {sel_txt}, "
                f"embargo {embargo_bars} bars ({time.perf_counter() - t0:.0f}s cum)",
                flush=True,
            )

        # ---- pooled per-instrument estimates (BIC-selected cells) ----
        d_pool = np.concatenate(pooled_durations)
        e_pool = np.concatenate(pooled_events)
        rng = np.random.default_rng(SEED)  # justify: design §11 registered seed
        pooled = pooled_km_median_stationary_bootstrap(
            d_pool, e_pool, alpha=ALPHA, n_bootstrap=N_BOOTSTRAP, rng=rng
        )
        delay_pool = np.concatenate(pooled_delay) if pooled_delay else np.empty(0)
        delay_ev_pool = (
            np.concatenate(pooled_delay_event) if pooled_delay_event else np.empty(0, dtype=bool)
        )
        l_detect = km_median(km_fit(delay_pool, delay_ev_pool)) if delay_pool.size else float("nan")
        ref_price = float(np.median(np.concatenate(eval_prices)))
        c_switch = cost_model.switch_drag_notional(symbol, reference_price=ref_price)
        c_switch_acct = cost_model.switch_drag_account_dollar(symbol)

        half_width = (pooled.ci_high - pooled.ci_low) / 2.0
        precision_ok = bool(half_width < PRECISION_HALF_WIDTH_FRAC * pooled.median)
        d_be_central = break_even_dwell_bars(
            detection_latency_bars=l_detect, c_switch=c_switch, mu_per_bar=MU_CENTRAL
        )
        # Session-truncated sensitivity, registered §8 bootstrap method
        # (round-2 audit QUANT-2-1). Fresh seeded Generator so the result
        # is identical whether computed inline or regenerated from the
        # archived spells parquet (--regen-sensitivity).
        pooled_t = pooled_km_median_stationary_bootstrap(
            np.concatenate(pooled_durations_trunc),
            np.concatenate(pooled_events_trunc),
            alpha=ALPHA,
            n_bootstrap=N_BOOTSTRAP,
            rng=np.random.default_rng(SEED),  # justify: design §11 registered seed
        )
        per_instrument[symbol] = {
            "session_truncated_sensitivity": _truncated_block(pooled_t),
            "pooled_median_dwell_bars": pooled.median,
            "pooled_ci_low_bars": pooled.ci_low,
            "pooled_ci_high_bars": pooled.ci_high,
            "pooled_ci_half_width_bars": half_width,
            "precision_ok": precision_ok,
            "n_spells_pooled": int(pooled.n_observations),
            "n_events_pooled": int(pooled.n_uncensored),
            "n_bootstrap_undefined": int(pooled.n_undefined_replicates),
            "spell_block_length": float(pooled.block_selection.block_length),
            "detection_latency_median_bars": l_detect,
            "n_transitions_pooled": int(delay_pool.size),
            "n_alarms_pooled": int(delay_ev_pool.sum()),
            "reference_price_unadjusted_median": ref_price,
            "switch_cost_usd": cost_model.switch_cost_usd(symbol),
            "c_switch_notional": c_switch,
            "c_switch_account_dollar_sensitivity": c_switch_acct,
            "break_even_frontier_bars": {
                f"{mu:g}": break_even_dwell_bars(
                    detection_latency_bars=l_detect, c_switch=c_switch, mu_per_bar=mu
                )
                for mu in MU_GRID
            },
            "d_be_central_bars": d_be_central,
            "h1_met": bool(precision_ok and pooled.ci_low > d_be_central),
        }

    # ---- §10 verdict ----
    any_h1 = any(v["h1_met"] for v in per_instrument.values())
    all_precise = all(v["precision_ok"] for v in per_instrument.values())
    if any_h1:
        verdict = "GO"
    elif not all_precise:
        verdict = "indeterminate — insufficient spells"
    else:
        verdict = "NO-GO"

    blob = {
        "hypothesis_id": "H900",
        "variant": variant,
        "verdict": verdict,
        "decision_rule": (
            "GO iff 95% CI lower bound of pooled D_med > D_be(mu=1.2e-4) for the "
            "BIC-selected model on >=1 instrument (design.md §10); precision gate "
            "per §8 (CI half-width < 25% of point estimate)."
        ),
        "mu_central": MU_CENTRAL,
        "alpha": ALPHA,
        "seed": SEED,
        "n_bootstrap": N_BOOTSTRAP,
        "instruments": per_instrument,
    }

    # ---- outputs ----
    out_dir.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(spell_rows).write_parquet(out_dir / f"h900_spells_{variant}.parquet")
    pl.DataFrame(latency_rows).write_parquet(out_dir / f"h900_latency_{variant}.parquet")
    pl.DataFrame([asdict(c) for c in cell_rows]).write_csv(
        out_dir / f"h900_window_summary_{variant}.csv"
    )
    (out_dir / f"h900_verdict_{variant}.json").write_text(
        json.dumps(blob, indent=2, sort_keys=True), encoding="utf-8"
    )
    written = [
        out_dir / f"h900_spells_{variant}.parquet",
        out_dir / f"h900_latency_{variant}.parquet",
        out_dir / f"h900_window_summary_{variant}.csv",
        out_dir / f"h900_verdict_{variant}.json",
    ]
    return blob, written


def _truncated_block(pooled_t) -> dict:
    """Verdict-JSON sensitivity block for the session-truncated rule."""
    return {
        "method": (
            "stationary bootstrap over the chronological truncated-rule "
            "spell sequence, PW automatic block length, B=2000, "
            "percentile CI (design §8 registered method)"
        ),
        "pooled_median_dwell_bars": pooled_t.median,
        "pooled_ci_low_bars": pooled_t.ci_low,
        "pooled_ci_high_bars": pooled_t.ci_high,
        "n_spells_pooled": int(pooled_t.n_observations),
        "n_events_pooled": int(pooled_t.n_uncensored),
        "spell_block_length": float(pooled_t.block_selection.block_length),
        "n_bootstrap_undefined": int(pooled_t.n_undefined_replicates),
    }


def _pooled_from_spells(spells: pl.DataFrame, *, instrument: str, rule: str):
    """Registered §8 pooled bootstrap from an archived spells frame."""
    g = spells.filter(
        (pl.col("instrument") == instrument) & pl.col("selected") & (pl.col("session_rule") == rule)
    ).sort("window_id", "start_ts")
    return pooled_km_median_stationary_bootstrap(
        g.get_column("duration_bars").to_numpy().astype(float),
        g.get_column("event").to_numpy(),
        alpha=ALPHA,
        n_bootstrap=N_BOOTSTRAP,
        rng=np.random.default_rng(SEED),  # justify: design §11 registered seed
    )


def regen_sensitivity(paths: ProjectPaths, out_dir: Path) -> list[Path]:
    """Insert the QUANT-2-1 truncated-rule sensitivity into existing
    verdict JSONs from the ARCHIVED spells parquet — no refit.

    Justification for skipping the refit (documented per QUANT-2-1): the
    sensitivity consumes only (a) the archived spell sequences, which
    are byte-identical to the production run's (the addition changes no
    fit, filter, or spell-extraction path), and (b) the registered seed;
    the §8 bootstrap is a pure function of those. As a guard, the
    continuous-rule pooled estimate is recomputed from the same parquet
    and asserted equal to the archived verdict values before anything is
    rewritten.
    """
    written: list[Path] = []
    for variant in ("primary", "inclusive"):
        spells = pl.read_parquet(out_dir / f"h900_spells_{variant}.parquet")
        verdict_path = out_dir / f"h900_verdict_{variant}.json"
        blob = json.loads(verdict_path.read_text(encoding="utf-8"))
        for instrument, entry in blob["instruments"].items():
            check = _pooled_from_spells(spells, instrument=instrument, rule="continuous")
            if (
                check.median != entry["pooled_median_dwell_bars"]
                or check.ci_low != entry["pooled_ci_low_bars"]
                or check.ci_high != entry["pooled_ci_high_bars"]
            ):
                raise RuntimeError(
                    f"regen guard failed for {variant}/{instrument}: archived "
                    f"continuous pooled estimate not reproduced from the spells "
                    f"parquet (got {check.median} [{check.ci_low}, {check.ci_high}])."
                )
            pooled_t = _pooled_from_spells(spells, instrument=instrument, rule="truncated")
            entry["session_truncated_sensitivity"] = _truncated_block(pooled_t)
            print(
                f"[regen/{variant}/{instrument}] truncated pooled: "
                f"{pooled_t.median:.0f} bars CI [{pooled_t.ci_low}, {pooled_t.ci_high}] "
                f"(block {pooled_t.block_selection.block_length:.1f}); "
                "continuous guard: reproduced",
                flush=True,
            )
        verdict_path.write_text(json.dumps(blob, indent=2, sort_keys=True), encoding="utf-8")
        written.append(verdict_path)
    return written


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--variant", choices=["primary", "inclusive", "both"], default="both")
    parser.add_argument("--out", default="reports/H900")
    parser.add_argument("--skip-canary", action="store_true")
    parser.add_argument(
        "--regen-sensitivity",
        action="store_true",
        help=(
            "QUANT-2-1 artifact-completion mode: insert the session-truncated "
            "pooled-bootstrap sensitivity into existing verdict JSONs from the "
            "archived spells parquet (no refit; guarded by a continuous-rule "
            "reproduction check). Emits its own ReproLog."
        ),
    )
    parser.add_argument(
        "--max-windows",
        type=int,
        default=None,
        help="DEV ONLY: truncate the window list; production runs use all 15.",
    )
    args = parser.parse_args()

    paths = ProjectPaths.discover()
    out_dir = paths.root / args.out

    if args.regen_sensitivity:
        design_path = paths.root / "research/01_hypothesis_register/H900/design.md"
        design_sha = hashlib.sha256(design_path.read_bytes()).hexdigest()
        input_checksums = {
            f"reports/H900/h900_spells_{v}.parquet": file_sha256(
                out_dir / f"h900_spells_{v}.parquet"
            )
            for v in ("primary", "inclusive")
        }
        log = reproducibility.capture(
            phase="h900-dwell-feasibility-sensitivity-regen",
            hypothesis_id="H900",
            rng_seed=SEED,
            dataset_checksums=input_checksums,
            config_resolved_sha256=design_sha,
            paths=paths,
        )
        log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
        log.write(log_path)
        written = regen_sensitivity(paths, out_dir)
        hasher = hashlib.sha256()
        for f in written:
            hasher.update(f.name.encode("utf-8"))
            hasher.update(f.read_bytes())
        reproducibility.with_model_hash(log, hasher.hexdigest()).write(log_path)
        print(f"ReproLog (regen): {log_path.name}", flush=True)
        return 0

    # ---- ReproLog FIRST (ADR-0008 Decision 3: before artifact writes) ----
    design_path = paths.root / "research/01_hypothesis_register/H900/design.md"
    design_sha = hashlib.sha256(design_path.read_bytes()).hexdigest()
    log = reproducibility.capture(
        phase="h900-dwell-feasibility-production",
        hypothesis_id="H900",
        rng_seed=SEED,
        dataset_checksums=_dataset_checksums(paths),
        config_resolved_sha256=design_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (design SHA {design_sha[:12]}...)", flush=True)

    # ---- ADR-0008 leakage canary on the real feature pipeline ----
    if not args.skip_canary:
        lf = _load_bars_1min(paths, "ES").filter(
            pl.col("ts_event") < pl.lit(datetime(2015, 3, 1)).dt.replace_time_zone("UTC")
        )
        bars = aggregate_5min(lf.collect().lazy().drop("unadjusted_close"))
        pit_canary_future_mutation(
            bars, cut_index=bars.height // 2, rng=np.random.default_rng(SEED)
        )
        print("PIT canary: PASS (features before cut invariant to future mutation)", flush=True)

    variants = ["primary", "inclusive"] if args.variant == "both" else [args.variant]
    written_this_run: list[Path] = []
    for variant in variants:
        blob, written = run_variant(
            paths=paths,
            variant=variant,
            instruments=INSTRUMENTS,
            max_windows=args.max_windows,
            out_dir=out_dir,
        )
        written_this_run.extend(written)
        print(f"[{variant}] VERDICT: {blob['verdict']}", flush=True)

    # Attach a model hash over the EXPLICIT list of files written by this
    # run (round-1 audit CODE-1-4: a directory glob could sweep in stale
    # artifacts from other runs/variants) for the ReproLog model_hash
    # field (design §11). Path order is deterministic (variant order).
    hasher = hashlib.sha256()
    for f in written_this_run:
        hasher.update(f.name.encode("utf-8"))
        hasher.update(f.read_bytes())
    reproducibility.with_model_hash(log, hasher.hexdigest()).write(log_path)
    print(f"ReproLog updated with model_hash: {log_path.name}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
