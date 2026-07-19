"""VERDICT-1 adjudication harness (protocol: research/02_verdict/VERDICT-1_protocol.md).

Executes ONE queue adjudication of the frozen first-admission VERDICT
protocol (ADR-0014 D2; ADR-0015 lift record 2026-07-19) for a candidate
against the CURRENT incumbent set, using ONLY the frozen estimators:
`hansen_spa`, `romano_wolf_stepm_panel`, `matched_turnover_rotor`,
`deflated_sharpe_ratio`, `probability_of_backtest_overfitting`, and the
frozen Politis-White block-length selector. The protocol's SHA is bound
into the run ReproLog (`config_resolved_sha256`); the enacted level is read
from `config/multipletest_family.yaml` at runtime and every bound derives
from it.

Stages (protocol §§1-2): per-arm per-session NET streams from the ledger →
OOS sessions (the 15 registered eval spans) → marginal-delta panel
`Δ_f = g_f(S∪{C}) − g_f(S)` → per-rung differential panels (B1 best-single,
B3 inverse-vol — per-origin train-fitted; B2 identity anchor recorded, not
tested; B4 flat) → SPA (consistent p) + panel-StepM per panel → rotor rung
(frozen distributional rotor per arm, Šidák arm-union) → DSR (cumulative
register N; matched dispersion surface) + PBO (CSCV S=16, member-only
Sharpe, session × arm Δ matrix) → §2.2 conjunction → disposition +
append-only side effects (pool records, card bump, register trials, burned
spans, arsenal register on admission).

Incumbents are read from `config/arsenal.yaml` (absent = empty set — the
degenerate |S| = 0 first case). The candidate registry maps the queue names
to expert families; `ORB` adjudicates the held H101+H103 hash as one
expert implementation (ADR-0014 D3 re-adjudication; both cards bump).

Usage:
    uv run python scripts/run_verdict.py --candidate H106
    uv run python scripts/run_verdict.py --candidate H105
    uv run python scripts/run_verdict.py --candidate ORB
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import polars as pl
import yaml

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.eval.windows import h900_windows  # noqa: E402
from skie_universe2.inference.bootstrap import politis_white_block_length  # noqa: E402
from skie_universe2.inference.deflated_sharpe import deflated_sharpe_ratio  # noqa: E402
from skie_universe2.inference.hansen_spa import hansen_spa  # noqa: E402
from skie_universe2.inference.matched_turnover_rotor import matched_turnover_rotor  # noqa: E402
from skie_universe2.inference.pbo import probability_of_backtest_overfitting  # noqa: E402
from skie_universe2.inference.romano_wolf import romano_wolf_stepm_panel  # noqa: E402
from skie_universe2.screening import screen_spine as spine  # noqa: E402
from skie_universe2.utils import reproducibility  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402
from skie_universe2.verdict.registry import KELLY_GRID, VERDICT_REGISTRY  # noqa: E402

# justify: VERDICT-1 protocol §10 — pre-registered fresh verdict-family seed
# (date-derived; distinct from the screen seeds so draws are independent).
SEED_VERDICT = 20260721
# justify: scan convention (RC lineage; protocol §10 frozen-machinery list).
N_BOOTSTRAP = 1000
# justify: rotor convention (RC-H101-1 N_ROTORS).
N_ROTORS = 2000
# justify: frozen pbo.py CSCV default (Bailey et al. 2017 S=16).
PBO_SPLITS = 16
_MIN_N = 2  # justify: ddof=1 minimum; structural
_EPS = 1e-12  # justify: structural div-by-zero guard
INSTRUMENTS = ("ES", "NQ")  # justify: the registered §2 universe
PROTOCOL_RELPATH = "research/02_verdict/VERDICT-1_protocol.md"

# Candidate registry + Kelly grid — single source of truth shared with the
# disposition emitter (skie_universe2.verdict.registry; audit CODE-3-1).
_REGISTRY = VERDICT_REGISTRY


# Per-arm streams: {arm: (session dates, net log-returns, gross log-returns)}
# (audit CODE-2-2: the nested shape is part of the harness contract).
ArmStreams = dict[float, tuple[list, np.ndarray, np.ndarray]]

# Registered joint-panel column order (audit QUANT-2-2): instrument-major,
# arm-minor — 8 columns (instrument x Kelly arm) per tested panel, so the
# session-axis joint bootstrap carries cross-instrument dependence in COLUMNS.
COLUMNS = tuple((sym, f) for sym in INSTRUMENTS for f in KELLY_GRID)
COLUMN_KEYS = tuple(f"{sym}:k{f}" for sym, f in COLUMNS)


@dataclass(frozen=True)
class MemberStreams:
    """Per-instrument, per-arm OOS session log-return streams of one expert."""

    name: str
    by_instrument: dict[str, ArmStreams]


def _load_arsenal(paths: ProjectPaths) -> list[str]:
    p = paths.config / "arsenal.yaml"
    if not p.is_file():
        return []
    blob = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return [m["candidate"] for m in blob.get("members", [])]


def _eval_session_filter(dates: list) -> np.ndarray:
    """Mask of sessions inside the 15 registered eval spans (protocol §3)."""
    windows = h900_windows()
    return np.array([any(w.origin <= d < w.eval_end for w in windows) for d in dates], dtype=bool)


def _member_sessions(paths: ProjectPaths, family: str, version: str) -> MemberStreams:
    """Per-session net/gross log-returns per arm per instrument (full panel)."""
    out: dict = {}
    for symbol in INSTRUMENTS:
        per_arm: dict = {}
        for f in KELLY_GRID:
            expert_id = f"{family}_k{f}@{version}"
            glob = str(
                paths.data_processed
                / "shadow_ledger"
                / f"expert_id={expert_id}"
                / f"asset={symbol}"
                / "**"
                / "part-0000.parquet"
            )
            frame = (
                pl.scan_parquet(glob)
                .select("session_date", "ret_net", "ret_gross")
                .group_by("session_date")
                .agg(net=pl.col("ret_net").sum(), gross=pl.col("ret_gross").sum())
                .sort("session_date")
                .collect()
            )
            per_arm[f] = (
                frame.get_column("session_date").to_list(),
                frame.get_column("net").to_numpy().astype(np.float64),
                frame.get_column("gross").to_numpy().astype(np.float64),
            )
        out[symbol] = per_arm
    return MemberStreams(name=family, by_instrument=out)


def _align(members: list[MemberStreams], symbol: str, arm: float) -> tuple[list, np.ndarray]:
    """Inner-join member session nets on session_date; returns (dates, matrix).

    Matrix shape (n_sessions, n_members), column order = `members` order.
    """
    date_sets = [set(m.by_instrument[symbol][arm][0]) for m in members]
    common = sorted(set.intersection(*date_sets))
    idx_maps = [{d: i for i, d in enumerate(m.by_instrument[symbol][arm][0])} for m in members]
    mat = np.column_stack(
        [
            m.by_instrument[symbol][arm][1][[idx_maps[j][d] for d in common]]
            for j, m in enumerate(members)
        ]
    )
    return common, mat


def _blend(mat: np.ndarray, weights: np.ndarray) -> np.ndarray:
    """Session-rebalanced weighted blend of member session log-returns (§1)."""
    return np.log1p(np.expm1(mat) @ weights)


def _ew(mat: np.ndarray) -> np.ndarray:
    n = mat.shape[1]
    return _blend(mat, np.full(n, 1.0 / n))


def _per_origin_benchmark_streams(
    dates: list, mat: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """B1 (best-single) and B3 (inverse-vol) OOS streams, per-origin fitted (§2/§3).

    For each registered window: fit on train sessions strictly < origin
    (B1: argmax member by summed session log-return; B3: weights ∝ 1/std of
    member session nets, renormalized); emit the fitted benchmark's blend
    over that window's eval sessions. Returns (b1, b3, fitted_mask) over the
    full `dates` axis; sessions outside every eval span carry NaN and are
    excluded by the caller's OOS mask.
    """
    n = len(dates)
    b1 = np.full(n, np.nan)
    b3 = np.full(n, np.nan)
    fitted = np.zeros(n, dtype=bool)
    for w in h900_windows():
        # Registered 24-month ROLLING train span (audit QUANT-2-1): both
        # bounds bind, matching the RollingWindow contract and the screen
        # precedent — an expanding train would be a different estimator.
        train = np.array([(w.train_start <= d < w.origin) for d in dates])
        ev = np.array([(w.origin <= d < w.eval_end) for d in dates])
        if int(train.sum()) < _MIN_N or not ev.any():
            continue
        train_mat = mat[train]
        best = int(np.argmax(train_mat.sum(axis=0)))
        sds = train_mat.std(axis=0, ddof=1)
        inv = 1.0 / np.maximum(sds, _EPS)
        w3 = inv / inv.sum()
        b1[ev] = mat[ev][:, best]
        b3[ev] = _blend(mat[ev], w3)
        fitted[ev] = True
    return b1, b3, fitted


def _sharpe(v: np.ndarray) -> float:
    v = v[np.isfinite(v)]
    if v.size < _MIN_N:
        return float("nan")
    sd = v.std(ddof=1)
    return float(v.mean() / sd) if sd > _EPS else float("nan")


def _nonempty_rc_families(cfg: dict) -> tuple[str, ...]:
    """The rc-* screen families that carry >=1 trial, in register order.

    ONE enumeration feeds both the DSR count and the dispersion pool (audit
    QUANT-3-1): empty rc-*-1 families contribute 0 to the count and are
    correctly excluded from the dispersion families (register_trial_sharpes
    fails closed on an empty family), so the two surfaces provably track the
    same family set by construction — not by a hardcoded coincidence.
    """
    return tuple(
        fam["family_id"]
        for fam in cfg.get("families", [])
        if str(fam.get("family_id", "")).startswith("rc-") and (fam.get("trials") or [])
    )


def _cumulative_register_surface(paths: ProjectPaths, current_surface: int) -> int:
    """Protocol §6: DSR trial count = cumulative register surface (raw binds)."""
    cfg = yaml.safe_load((paths.config / "multipletest_family.yaml").read_text(encoding="utf-8"))
    screen_trials = 0
    verdict_trials = 0
    for fam in cfg.get("families", []):
        fid = fam.get("family_id", "")
        n = len(fam.get("trials") or [])
        if fid.startswith("rc-"):
            screen_trials += n
        elif fid == "first-admission-verdict":
            verdict_trials += n
    return screen_trials + verdict_trials + current_surface


def _dispersion_pool(paths: ProjectPaths, current_sharpes: list[float]) -> float:
    """Matched-surface dispersion (§6): screen-family recorded non-unconditional
    Sharpes + verdict-family recorded Sharpes + the current surface's Sharpes.

    The screen families are DISCOVERED from the same non-empty rc-*
    enumeration the count uses (audit QUANT-3-1), so a new screen family
    registered mid-queue lands in BOTH surfaces rather than only the count.
    The `:unconditional` exclusion inside register_trial_sharpes is the
    standing nested-cell convention (protocol §6, disclosed).
    """
    cfg = yaml.safe_load((paths.config / "multipletest_family.yaml").read_text(encoding="utf-8"))
    vals = spine.register_trial_sharpes(paths, _nonempty_rc_families(cfg))
    for fam in cfg.get("families", []):
        if fam.get("family_id") == "first-admission-verdict":
            for t in fam.get("trials") or []:
                s = t.get("sharpe_estimate")
                if isinstance(s, int | float):
                    vals.append(float(s))
    vals.extend([s for s in current_sharpes if np.isfinite(s)])
    return float(np.std(vals, ddof=1)) if len(vals) > 1 else float("nan")


def run_adjudication(paths: ProjectPaths, candidate: str) -> dict:  # noqa: PLR0912, PLR0915 — one linear, auditable protocol sequence (§1..§8); splitting would scatter the frozen conjunction
    """Execute the frozen VERDICT-1 protocol for one queue candidate."""
    level = spine.screen_level(paths)
    incumbents = _load_arsenal(paths)
    if candidate in incumbents:
        raise RuntimeError(f"{candidate} is already an arsenal member")
    meta = _REGISTRY[candidate]

    cand = _member_sessions(paths, meta["family"], meta["version"])
    inc_streams = [
        _member_sessions(paths, _REGISTRY[m]["family"], _REGISTRY[m]["version"]) for m in incumbents
    ]
    members = [*inc_streams, cand]  # candidate LAST (column -1)
    m_prime = len(members)

    # ---- Build session-ALIGNED joint OOS panels (§1/§3; audit QUANT-2-2) ----
    # Per (instrument, arm): member-aligned full-axis streams -> delta and
    # rung differentials on that instrument's own axis. Then the two
    # instruments' session axes are INNER-JOINED so each panel row is one
    # session date and columns are the registered (instrument x arm) order —
    # the session-axis joint bootstrap models serial, cross-arm AND
    # cross-instrument dependence; nothing is concatenated end-to-end.
    per_col: dict[str, dict] = {}
    for symbol in INSTRUMENTS:
        for f in KELLY_GRID:
            dates, mat = _align(members, symbol, f)
            g_aug = _ew(mat)
            g_inc = _ew(mat[:, :-1]) if m_prime > 1 else np.zeros(len(dates))
            b1_full, b3_full, fitted = _per_origin_benchmark_streams(dates, mat)
            per_col[f"{symbol}:k{f}"] = {
                "dates": dates,
                "delta": g_aug - g_inc,
                "g_aug": g_aug,
                "b1": b1_full,
                "b3": b3_full,
                "fitted": fitted,
            }
    axis = sorted(set.intersection(*(set(c["dates"]) for c in per_col.values())))
    oos_axis = _eval_session_filter(axis)
    fitted_axis = np.ones(len(axis), dtype=bool)
    for c in per_col.values():
        pos = {d: i for i, d in enumerate(c["dates"])}
        c["on_axis"] = np.array([pos[d] for d in axis], dtype=np.int64)
        fitted_axis &= c["fitted"][c["on_axis"]]
    # Row selection (audit CODE-2-3, intent stated directly): the per-origin
    # fitted mask binds only when benchmark rungs B1/B3 are tested; rows must
    # be fitted in BOTH instruments (declared in §3).
    sel = (oos_axis & fitted_axis) if m_prime > 1 else oos_axis

    def _col_panel(key: str) -> np.ndarray:
        cols = []
        for ck in COLUMN_KEYS:
            c = per_col[ck]
            v = c["on_axis"]
            if key == "delta":
                stream = c["delta"][v]
            elif key == "b4":
                stream = c["g_aug"][v]  # vs flat: g_aug − 0
            else:
                stream = c["g_aug"][v] - c[key][v]
            cols.append(stream[sel])
        return np.column_stack(cols)  # (n_selected_sessions, 8)

    delta_mat = _col_panel("delta")
    panels: dict[str, np.ndarray] = {"marginal": delta_mat}
    if m_prime > 1:
        panels["b1"] = _col_panel("b1")
        panels["b3"] = _col_panel("b3")
        panels["b4"] = _col_panel("b4")
    else:
        # |S| = 0: the flat rung EQUALS the marginal panel (computed once, §2).
        panels["b4"] = delta_mat

    # Per-instrument exhibits (all four arms REPORTED per instrument).
    per_instrument_exhibits = []
    for symbol in INSTRUMENTS:
        inst_ex: dict = {"instrument": symbol, "arms": {}}
        for f in KELLY_GRID:
            c = per_col[f"{symbol}:k{f}"]
            delta_sel = c["delta"][c["on_axis"]][sel]
            inst_ex["arms"][str(f)] = {
                "n_oos_sessions": int(sel.sum()),
                "delta_mean": (float(delta_sel.mean()) if delta_sel.size else float("nan")),
                "delta_sharpe": _sharpe(delta_sel),
            }
            if f == 1.0:
                pw = []
                dstream = c["delta"][c["on_axis"]]
                for w in h900_windows():
                    wsel = np.array([(w.origin <= d < w.eval_end) for d in axis]) & sel
                    vals = dstream[wsel]
                    pw.append(float(vals.mean()) if vals.size else float("nan"))
                inst_ex["per_window_delta_k1.0"] = pw
        per_instrument_exhibits.append(inst_ex)

    # ---- SPA + panel-StepM per panel (frozen estimators; §2.1) ----
    inference: dict = {}
    tested_panels = (
        ["marginal", "b1", "b3", "b4"] if m_prime > 1 else ["marginal"]
    )  # at |S|=0, b4 ≡ marginal (recorded once)
    # justify: block length = max over the two instruments' registered-unit
    # k1.0 delta columns of the frozen PW selector (protocol §10; the longer
    # block is conservative for both; deterministic).
    _bl_per_inst = [
        politis_white_block_length(
            per_col[f"{sym}:k1.0"]["delta"][per_col[f"{sym}:k1.0"]["on_axis"]][sel]
        ).block_length
        for sym in INSTRUMENTS
    ]
    bl = max(*_bl_per_inst, 1.0)
    for name in tested_panels:
        panel = panels[name]
        spa = hansen_spa(
            panel,
            block_length=bl,
            rng=np.random.default_rng(SEED_VERDICT),
            n_bootstrap=N_BOOTSTRAP,
        )
        stepm = romano_wolf_stepm_panel(
            panel,
            block_length=bl,
            rng=np.random.default_rng(SEED_VERDICT),
            n_bootstrap=N_BOOTSTRAP,
            alpha=level,
        )
        inference[name] = {
            "block_length": float(bl),
            "columns": list(COLUMN_KEYS),
            "spa_p_consistent": spa.p_value_consistent,
            "spa_p_lower": spa.p_value_lower,
            "spa_p_upper": spa.p_value_upper,
            "spa_statistic": spa.statistic,
            "stepm_adjusted_p": stepm.adjusted_pvalue.tolist(),
            "stepm_identified": stepm.rejected.tolist(),
            "column_means": panel.mean(axis=0).tolist(),
            "column_sharpes": [_sharpe(panel[:, j]) for j in range(panel.shape[1])],
        }
    if m_prime == 1:
        inference["b4"] = {**inference["marginal"], "note": "identical to marginal at |S|=0"}

    # ---- Rotor rung (frozen distributional rotor per column + Šidák; §2.1) ----
    # One rotor per (instrument, arm) column on that instrument's OWN OOS net
    # stream (the RC-H101/H103 per-instrument precedent — no cross-instrument
    # concatenation); union over all 8 columns priced by Šidák exponent 8.
    # Seeds SEED_VERDICT + 1 + idx, idx = registered column position (§10).
    rotor_by_column: dict[str, dict] = {}
    n_union = len(COLUMNS)
    for idx, (symbol, f) in enumerate(COLUMNS):
        dates_c = cand.by_instrument[symbol][f][0]
        net_c = cand.by_instrument[symbol][f][1]
        oos_c = _eval_session_filter(dates_c)
        series = net_c[oos_c]
        mask = series != 0.0
        rot = matched_turnover_rotor(
            series,
            mask,
            n_rotors=N_ROTORS,
            rng=np.random.default_rng(SEED_VERDICT + 1 + idx),
        )
        p_sidak = 1.0 - (1.0 - rot.p_value) ** n_union
        rotor_by_column[COLUMN_KEYS[idx]] = {
            "p_value": rot.p_value,
            "p_sidak_column_union": p_sidak,
            "expert_mean": rot.expert_mean,
            "expert_percentile": rot.expert_percentile,
            "entry_count": rot.entry_count,
        }

    # ---- DSR + PBO (§2.2 clause 4) ----
    # Protocol §6 branch enumeration on the 8-column (instrument x arm)
    # geometry: |U|=1 -> marginal-flat 8 + rotor 8 = 16; |U|>=2 -> marginal 8
    # + rungs b1/b3/b4 24 + rotor 8 = 40.
    current_surface = 16 if m_prime == 1 else 40
    n_trials = _cumulative_register_surface(paths, current_surface)
    # Matched dispersion surface (audit QUANT-2-3): EVERY Sharpe-bearing
    # trial of the current surface enters the dispersion pool — the marginal
    # panel's 8 column Sharpes plus, at |U|>=2, the 24 rung-differential
    # column Sharpes. Rotor trials are declaredly Sharpe-less (distributional
    # null; the h900 non-Sharpe-trial precedent) so the count and dispersion
    # surfaces differ ONLY by the declared rotor exception.
    column_delta_sharpes = [_sharpe(delta_mat[:, j]) for j in range(delta_mat.shape[1])]
    surface_sharpes = list(column_delta_sharpes)
    if m_prime > 1:
        for r in ("b1", "b3", "b4"):
            surface_sharpes.extend(inference[r]["column_sharpes"])
    sr_std = _dispersion_pool(paths, surface_sharpes)
    dsr_by_column: dict[str, dict] = {}
    for j, ck in enumerate(COLUMN_KEYS):
        v = delta_mat[:, j]
        v = v[np.isfinite(v)]
        if v.size < _MIN_N or not np.isfinite(sr_std) or sr_std <= _EPS:
            dsr_by_column[ck] = {"dsr": float("nan"), "reason": "degenerate"}
            continue
        vif = spine.hac_variance_inflation(v)
        n_eff = max(int(round(v.size / vif)), _MIN_N)
        sd = v.std()
        skew = float(((v - v.mean()) ** 3).mean() / (sd**3 + _EPS))
        kurt = float(((v - v.mean()) ** 4).mean() / (sd**4 + _EPS))
        d = deflated_sharpe_ratio(
            column_delta_sharpes[j], n_eff, n_trials, sr_std, skew=skew, kurtosis=kurt
        )
        dsr_by_column[ck] = {
            "dsr": float(d.dsr),
            "dsr_bound": 1.0 - level,
            "n_eff_hac": n_eff,
            "n_trials_gate": n_trials,
        }
    pbo_res = probability_of_backtest_overfitting(
        delta_mat, s_splits=PBO_SPLITS, score_fn=spine.member_only_sharpe
    )
    pbo = float(pbo_res.pbo)

    # ---- §2.2 admission conjunction (qualification unit = column) ----
    nondegenerate_rungs = ["b1", "b3", "b4"] if m_prime > 1 else ["b4"]
    iu_spa_p = max(inference[r]["spa_p_consistent"] for r in nondegenerate_rungs)
    rotor_min_sidak = min(r["p_sidak_column_union"] for r in rotor_by_column.values())
    marginal_pass = inference["marginal"]["spa_p_consistent"] < level
    iu_pass = (iu_spa_p < level) and (rotor_min_sidak < level)
    qualifying_columns = []
    for j, ck in enumerate(COLUMN_KEYS):
        ok = inference["marginal"]["stepm_identified"][j]
        for r in nondegenerate_rungs:
            ok = ok and inference[r]["stepm_identified"][j]
        ok = ok and (rotor_by_column[ck]["p_sidak_column_union"] < level)
        if ok:
            qualifying_columns.append(ck)
    best_column = None
    if qualifying_columns:
        # Best-QUALIFYING column = max marginal-panel Sharpe (the StepM
        # statistic is monotone in it at fixed n); REPORTED, never selected
        # (§5 — a column identifies an (instrument, arm) pair; no Kelly
        # fraction is selected by this report).
        stats = {
            ck: inference["marginal"]["column_sharpes"][COLUMN_KEYS.index(ck)]
            for ck in qualifying_columns
        }
        best_column = max(stats, key=stats.get)
    persistence_pass = False
    if best_column is not None:
        d = dsr_by_column[best_column]
        persistence_pass = (
            np.isfinite(d.get("dsr", float("nan"))) and d["dsr"] >= 1.0 - level and pbo <= level
        )
    admitted = bool(marginal_pass and iu_pass and qualifying_columns and persistence_pass)

    return {
        "protocol": PROTOCOL_RELPATH,
        "candidate": candidate,
        "expert_family": meta["family"],
        "hids": list(meta["hids"]),
        "incumbents_at_adjudication": incumbents,
        "set_size_augmented": m_prime,
        "screen_level_runtime": level,
        "seed": SEED_VERDICT,
        "n_bootstrap": N_BOOTSTRAP,
        "n_rotors": N_ROTORS,
        "current_trial_surface": current_surface,
        "n_trials_cumulative": n_trials,
        "sr_std_matched_surface": sr_std,
        "columns": list(COLUMN_KEYS),
        "n_aligned_sessions": int(len(axis)),
        "n_selected_sessions": int(sel.sum()),
        "inference": inference,
        "rotor_by_column": rotor_by_column,
        "dsr_by_column": dsr_by_column,
        "pbo": {"pbo": pbo, "bound": level, "s_splits": PBO_SPLITS},
        "identity_anchor_b2": "EW(U) is the §1 set functional (recorded, not tested)",
        "degenerate_rungs": [] if m_prime > 1 else ["b1", "b3"],
        "conjunction": {
            "marginal_spa_pass": bool(marginal_pass),
            "ladder_iu_spa_max_p": float(iu_spa_p),
            "ladder_iu_pass": bool(iu_pass),
            "rotor_min_sidak_p": float(rotor_min_sidak),
            "qualifying_columns": qualifying_columns,
            "best_qualifying_column_reported_not_selected": best_column,
            "persistence_pass": bool(persistence_pass),
            "admitted": admitted,
        },
        "per_instrument": per_instrument_exhibits,
        "per_window_delta_k1.0_by_instrument": "see per_instrument exhibits",
        "kelly_note": (
            "all four registered fractions computed and reported per "
            "instrument; the qualifying-column set is a REPORTED "
            "identification of (instrument, arm) pairs, not a selection "
            "(protocol §5; ADR-0013 D3)"
        ),
        "disposition": (
            "admitted-arsenal-member" if admitted else "pool-hold-reconsider (re-affirmed)"
        ),
    }


def main() -> int:
    # cp1252-console robustness (audit REPRODUCIBILITY-2-2): the module
    # docstring carries non-cp1252 glyphs; argparse help/usage and every
    # print must survive a Windows console out of the box.
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="VERDICT-1 adjudication harness (see module docstring)."
    )
    parser.add_argument("--candidate", required=True, choices=tuple(_REGISTRY))
    parser.add_argument("--out", default="reports/VERDICT-1")
    args = parser.parse_args()
    paths = ProjectPaths.discover()

    protocol = paths.root / PROTOCOL_RELPATH
    protocol_sha = hashlib.sha256(protocol.read_bytes()).hexdigest()
    manifest = json.loads((paths.data / "_manifest.json").read_text(encoding="utf-8"))
    checksums: dict[str, str] = {PROTOCOL_RELPATH: protocol_sha}
    checksums["config/multipletest_family.yaml"] = hashlib.sha256(
        (paths.config / "multipletest_family.yaml").read_bytes()
    ).hexdigest()
    # Ledger-partition binding (audit REPRODUCIBILITY-2-1): the candidate's
    # AND every incumbent's family partitions enter the ReproLog, per the
    # protocol §10 commitment — the adjudication consumes both sides.
    families = [_REGISTRY[args.candidate]["family"]] + [
        _REGISTRY[m]["family"] for m in _load_arsenal(paths)
    ]
    for fam in families:
        entries = {
            k: e["sha256"] for k, e in manifest["files"].items() if f"expert_id={fam}_k" in k
        }
        if not entries:
            raise RuntimeError(f"no ledger-partition checksums for family {fam}")
        checksums[f"shadow_ledger:{fam} ({len(entries)} parts)"] = hashlib.sha256(
            "".join(f"{k}:{v}\n" for k, v in sorted(entries.items())).encode()
        ).hexdigest()
    log = reproducibility.capture(
        phase=f"verdict-1-{args.candidate.lower()}",
        hypothesis_id="/".join(_REGISTRY[args.candidate]["hids"]),
        rng_seed=SEED_VERDICT,
        dataset_checksums=checksums,
        config_resolved_sha256=protocol_sha,
        paths=paths,
    )
    log_path = paths.logs_reproducibility / f"repro_log_{log.run_id}.json"
    log.write(log_path)
    print(f"ReproLog: {log_path.name} (protocol SHA {protocol_sha[:12]}...)", flush=True)

    result = run_adjudication(paths, args.candidate)
    result["repro_log"] = log_path.name
    result["protocol_sha256"] = protocol_sha
    out_dir = paths.root / args.out
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"verdict_{args.candidate.lower()}.json"
    out_path.write_text(
        json.dumps(
            spine.json_sanitize(result), indent=2, sort_keys=True, default=str, allow_nan=False
        ),
        encoding="utf-8",
    )
    c = result["conjunction"]
    print(
        f"[VERDICT-1/{args.candidate}] admitted={c['admitted']} | "
        f"marginal SPA p={result['inference']['marginal']['spa_p_consistent']:.4f} | "
        f"IU max p={c['ladder_iu_spa_max_p']:.4f} | rotor min Sidak p="
        f"{c['rotor_min_sidak_p']:.4f} | qualifying columns={c['qualifying_columns']} | "
        f"PBO={result['pbo']['pbo']:.3f}",
        flush=True,
    )
    print(f"Wrote {out_path}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
