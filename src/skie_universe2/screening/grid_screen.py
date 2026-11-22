"""ADR-0014 SCREEN over a registered PARAMETER GRID (H107 design §5).

The packaged :mod:`skie_universe2.screening.screen_spine` screens one ledger
stream against masked conditioning CELLS. A parameter grid is a different
family shape: K distinct per-session return series (one expert id per grid
point) on a common session axis. This module runs the identical gate
conjunction on that shape, reusing the spine's public helpers verbatim:

- **S-c** Romano-Wolf StepM over the K grid columns per instrument via the
  frozen PANEL estimator (:func:`romano_wolf_stepm_panel`, VERDICT-1;
  rows resampled jointly so cross-span dependence is preserved), stationary
  bootstrap with the Politis-White block length of the PRIMARY column; PASS
  iff mean gross > 0 AND adjusted p < the ENACTED level (runtime read).
- **S-d** DSR >= 1 - level (n_trials_gate frozen in the design; dispersion
  pooled over the register's recorded trial Sharpes + this scan's grid
  Sharpes — the spine's matched-surface rule) AND PBO <= level, where PBO is
  the Bailey et al. 2017 CSCV on the T x K grid matrix — the canonical
  "probability the in-sample-best grid point underperforms out of sample".
- **S-e** every grid point is a rule-based causal expert (lag 0): reported,
  definitionally satisfied (H105 §3 statement).

Net-of-cost columns are DESCRIPTIVE (the screen is on gross edge; net binds
at the VERDICT): per instrument variant (e.g. ES and MES on the ES price
path) and broker plan, mean per-session net = gross - turnover x per-unit
notional drag of that variant/plan.

Output JSON mirrors the spine's ``run_screen`` shape (``instruments[*].cells``
with ``cell`` = grid-point label) so the v1 disposition emitter consumes it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from skie_universe2.inference.bootstrap import politis_white_block_length
from skie_universe2.inference.deflated_sharpe import deflated_sharpe_ratio
from skie_universe2.inference.pbo import probability_of_backtest_overfitting
from skie_universe2.inference.romano_wolf import romano_wolf_stepm_panel
from skie_universe2.screening.screen_spine import (
    EPS,
    MIN_CELL_N,
    N_BOOTSTRAP,
    PBO_SPLITS,
    cell_sharpe,
    hac_variance_inflation,
    kpss_stationarity,
    member_only_sharpe,
    rolling_growth,
)

_PANEL_NDIM = 2  # justify: structural — (sessions, grid points)


@dataclass(frozen=True)
class CostVariant:
    """One (contract, plan) per-side cost on a parent instrument's price path."""

    label: str  # e.g. "MES/lifetime"
    per_unit_drag: float  # one-way log-return drag per unit |Δposition|


@dataclass(frozen=True)
class GridPanel:
    """Per-instrument grid inputs (all arrays T x K, common session axis)."""

    instrument: str
    dates: list
    labels: tuple[str, ...]
    gross: np.ndarray
    turnover: np.ndarray
    canary: dict
    cost_variants: tuple[CostVariant, ...] = ()
    extras: dict = field(default_factory=dict)


def per_unit_drag(per_side_usd: float, *, reference_price: float, multiplier: float) -> float:
    """One-way notional log drag of one contract side: -log(1 - cost/notional)."""
    notional = reference_price * multiplier
    ratio = per_side_usd / notional
    if not (0.0 <= ratio < 1.0):
        raise ValueError(f"per-side cost/notional {ratio} outside [0, 1)")
    return float(-np.log1p(-ratio))


def _dsr_block(v: np.ndarray, sharpe: float, n_trials: int, sr_std: float, level: float) -> dict:
    if v.size < MIN_CELL_N or not np.isfinite(sr_std) or sr_std <= EPS or not np.isfinite(sharpe):
        return {"dsr": float("nan"), "dsr_pass": False, "reason": "degenerate"}
    vif = hac_variance_inflation(v)
    n_eff = max(int(round(v.size / vif)), MIN_CELL_N)
    sd = v.std()
    skew = float(((v - v.mean()) ** 3).mean() / (sd**3 + EPS))
    kurt = float(((v - v.mean()) ** 4).mean() / (sd**4 + EPS))
    res = deflated_sharpe_ratio(sharpe, n_eff, n_trials, sr_std, skew=skew, kurtosis=kurt)
    return {
        "dsr": float(res.dsr),
        "dsr_bound": 1.0 - level,
        "dsr_pass": bool(res.dsr >= 1.0 - level),
        "n_eff_hac": n_eff,
        "hac_vif": float(vif),
        "n_trials_gate": n_trials,
    }


def run_grid_screen(  # noqa: PLR0915 — one linear, auditable gate sequence (spine precedent)
    panels: list[GridPanel],
    *,
    level: float,
    seed: int,
    n_trials_gate: int,
    register_sharpes: list[float],
    primary_label: str,
    dwell_bars_per_session: float,
    n_bootstrap: int = N_BOOTSTRAP,
    pbo_splits: int = PBO_SPLITS,
) -> dict:
    """Run S-c / S-d / S-e over every instrument's grid panel; spine-shaped dict."""
    if not (0.0 < level < 1.0):
        raise ValueError(f"level must be in (0, 1), got {level}")
    out_inst: list[dict] = []
    for p in panels:
        g = np.asarray(p.gross, dtype=np.float64)
        if g.ndim != _PANEL_NDIM or g.shape[1] != len(p.labels) or g.shape != p.turnover.shape:
            raise ValueError(f"{p.instrument}: panel/labels/turnover shape mismatch")
        if not np.isfinite(g).all():
            raise ValueError(f"{p.instrument}: gross panel must be fully finite (inner join)")
        k_primary = p.labels.index(primary_label)
        bl = max(
            politis_white_block_length(g[:, k_primary], bootstrap_type="stationary").block_length,
            1.0,
        )
        rw = romano_wolf_stepm_panel(
            g,
            block_length=bl,
            rng=np.random.default_rng(seed),
            n_bootstrap=n_bootstrap,
            alpha=level,
            min_n=MIN_CELL_N,
        )
        cells = []
        for k, lab in enumerate(p.labels):
            v = g[:, k]
            mean = float(v.mean())
            cells.append(
                {
                    "cell": lab,
                    "n": int(v.size),
                    "mean_gross": mean,
                    "sharpe": cell_sharpe(v),
                    "stat": float(rw.stat[k]),
                    "rw_adj_pvalue": float(rw.adjusted_pvalue[k]),
                    "s_c_pass": bool(mean > 0.0 and float(rw.adjusted_pvalue[k]) < level),
                    "mean_turnover_per_session": float(p.turnover[:, k].mean()),
                    "net_descriptive": {
                        cv.label: float((v - p.turnover[:, k] * cv.per_unit_drag).mean())
                        for cv in p.cost_variants
                    },
                }
            )
        pbo_res = probability_of_backtest_overfitting(
            g, s_splits=pbo_splits, score_fn=member_only_sharpe
        )
        rhos = [
            float(np.corrcoef(g[:, a], g[:, b])[0, 1])
            for a in range(g.shape[1])
            for b in range(a + 1, g.shape[1])
            if g[:, a].std() > EPS and g[:, b].std() > EPS
        ]
        out_inst.append(
            {
                "instrument": p.instrument,
                "canary": p.canary,
                "block_length": float(bl),
                "block_length_source": f"politis-white on primary column {primary_label}",
                "cells": cells,
                "pbo": {
                    "pbo": float(pbo_res.pbo),
                    "s_splits": pbo_splits,
                    "n_combinations": int(pbo_res.n_combinations),
                    "construction": "CSCV on the T x K grid matrix (member-only Sharpe)",
                },
                "cell_dependence": {
                    "rho_bar_pairwise": float(np.mean(rhos)) if rhos else None,
                    "n_estimable_pairs": len(rhos),
                    # reported, never substituted for n_trials_gate (spine rule)
                    "n_eff_corr_adjusted_reported": (
                        float(n_trials_gate / (1.0 + (n_trials_gate - 1) * max(np.mean(rhos), 0.0)))
                        if rhos
                        else None
                    ),
                },
                "section8": {"kpss_primary": kpss_stationarity(g[:, k_primary])},
                **({"extras": p.extras} if p.extras else {}),
            }
        )

    sigma_pool = list(register_sharpes) + [
        c["sharpe"] for inst in out_inst for c in inst["cells"] if np.isfinite(c["sharpe"])
    ]
    sr_std = float(np.std(sigma_pool, ddof=1)) if len(sigma_pool) > 1 else float("nan")
    for inst, p in zip(out_inst, panels, strict=True):
        pbo = inst["pbo"]["pbo"]
        inst["sr_std_surface"] = {
            "sr_std": sr_std,
            "n_register_trials": len(register_sharpes),
            "n_current_sigma_cells": len(sigma_pool) - len(register_sharpes),
        }
        mask_all = np.ones(len(p.dates), dtype=bool)
        for k, c in enumerate(inst["cells"]):
            v = np.asarray(p.gross, dtype=np.float64)[:, k]
            sd = _dsr_block(v, c["sharpe"], n_trials_gate, sr_std, level)
            growth = rolling_growth(v, p.dates, mask_all)
            finite = [x for x in growth if np.isfinite(x)]
            sd.update(
                {
                    "pbo": pbo,
                    "pbo_bound": level,
                    "pbo_pass": bool(pbo <= level),
                    "per_window_growth": growth,
                    "positive_window_fraction": (
                        float(np.mean([x > 0 for x in finite])) if finite else float("nan")
                    ),
                }
            )
            sd["pass"] = bool(sd["dsr_pass"] and sd["pbo_pass"])
            c["s_d"] = sd
            c["s_e"] = {
                "cell_mechanism": "rule-based-causal-expert (grid point)",
                "observation_lag_bars": 0.0,
                "cell_dwell_bars": dwell_bars_per_session,
                "pass": True,
                "note": "lag-0 rule: S-e definitionally satisfied (reported, not discriminating)",
            }
            c["screen_pass"] = bool(
                inst["canary"].get("pass", False) and c["s_c_pass"] and sd["pass"] and True
            )

    any_pass = any(c["screen_pass"] for i in out_inst for c in i["cells"])
    any_sc = any(c["s_c_pass"] for i in out_inst for c in i["cells"])
    if any_pass:
        disposition = (
            "screen-pass -> provisional pool (pool-hold-reconsider eligible; "
            "VERDICT is a separate operator-authorized event)"
        )
    elif any_sc:
        disposition = (
            "archive-no-persistent-window (gross edge present in >= 1 grid point but "
            "persistence gates fail)"
        )
    else:
        disposition = (
            "archive-no-persistent-window (sub-reason: archive-no-gross-edge — "
            "no S-c pass at any grid point)"
        )
    return {
        "screen_level": level,
        "seed_s_c": seed,
        "n_bootstrap": n_bootstrap,
        "primary_cell": primary_label,
        "family_shape": "parameter-grid panel (K expert ids x common session axis)",
        "dwell_bars_per_session": dwell_bars_per_session,
        "disposition": disposition,
        "decision_rule": (
            "ADR-0014 SCREEN over the registered grid: a grid point passes iff S-a "
            f"canary AND mean gross > 0 AND panel-RW-adjusted p < {level} (S-c) AND "
            f"DSR >= {1 - level:.4f} AND grid PBO <= {level} (S-d) AND S-e (lag 0). "
            "NOTHING certified; net columns descriptive."
        ),
        "instruments": out_inst,
    }
