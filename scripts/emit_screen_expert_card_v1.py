"""Emit the v1 Expert Card, pool records, register trials, and burned spans
for a FRESH forward expert's first screen (H105 / H106).

Counterpart of ``emit_screen_expert_card.py`` (the H101/H103 v2 emitter) for
first-cycle forward candidates: no predecessor card, no RC-1 reproduction
claim, the expert's OWN k1.0 ledger id as ``expert_hash`` (the quantity the
ADR-0015 verdict precondition counts), and the burned-data mirror written
per evaluation window (ADR-0008 D5 / ADR-0004 rolling regime) — the RC-*-2
emitters left that mirror hand-maintained; here it is scripted.

Generates, from ``reports/{HID}/rc_{hid}_1_screen.json`` (ADR-0009 D3:
every number derived from artifacts, nothing hand-copied):

  1. ``research/01_hypothesis_register/{HID}/expert_card_v1.md`` — the
     eight-section ADR-0009 card.
  2. On screen PASS: pool records appended IDEMPOTENTLY to
     ``data/processed/pool_ledger/pool_ledger.jsonl`` (schema field names of
     ``config/pool_ledger_schema.yaml``), one per Kelly fraction.
  3. Per-cell trial records appended to the ``rc-{hid}-1`` family in
     ``config/multipletest_family.yaml`` (idempotent).
  4. Per-eval-window burned spans appended to
     ``config/burned_data_ledger.yaml`` under the HID (idempotent: skipped
     when the HID already carries screen-purpose spans).

Usage:
    uv run python scripts/emit_screen_expert_card_v1.py --hid H105
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

import polars as pl  # noqa: E402

from skie_universe2.eval.windows import h900_windows  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402
from skie_universe2.utils.reproducibility import ReproLog  # noqa: E402

# justify: ADR-0013 Decision 3 registered grid (materialized, none selected).
KELLY_GRID = (0.5, 0.75, 1.0, 1.25)

_REGISTRY = {
    "H105": {
        "title": "Overnight/Globex session-drift expert (ES/NQ) - RC-H105-1 screen",
        "expert_hash": "overnight_session_drift_k1.0@1.0.0",
        "screen_script": "scripts/run_screen_h105.py",
        "mechanism": (
            "overnight risk premium (Boyarchenko-Larsen-Whelan 2023, "
            "10.1093/rfs/hhad020; Lou-Polk-Skouras 2019, "
            "10.1016/j.jfineco.2019.03.011) with the 2026 attenuation "
            "expectation pre-registered (design §1)"
        ),
        "coverage_claim": (
            "overnight-ETH accrual rows, bar-disjoint from the ORB pool's "
            "RTH rows BY CONSTRUCTION (design §12(c) identity; M1 measured "
            "at disposition)"
        ),
        "net_note": (
            "one round-trip per session (turnover-matched to the ORB "
            "cadence); Tier-0 net at constant 1-tick slippage is labeled "
            "'optimistic in thin ETH' per design §7"
        ),
    },
    "H106": {
        "title": "Variance-ratio range-state reversal expert (ES/NQ) - RC-H106-1 screen",
        "expert_hash": "vr_range_reversal_k1.0@1.0.0",
        "screen_script": "scripts/run_screen_h106.py",
        "mechanism": (
            "short-horizon reversal in the registered VR(2)<1 range state "
            "(Lo-MacKinlay 1988, 10.1093/rfs/1.1.41; Lo-MacKinlay 1990, "
            "10.1093/rfs/3.2.175); weekly-horizon transfer caveat declared "
            "(design §1)"
        ),
        "coverage_claim": (
            "whole-session accrual on range-state bars; bar-level overlap "
            "vs the ORB pool is PARTIAL by design (§12(c) predicted "
            "0.05-0.25) and CANNOT lift the ADR-0015 precondition against "
            "the ORB hash (M1 measured at disposition)"
        ),
        "net_note": (
            "1-bar-hold rule: per-session turnover one to two orders above "
            "the session-cadence experts; Tier-0 net at constant 1-tick "
            "slippage is expected strongly negative and is labeled "
            "'high-turnover regime - cost-model floor' per design §7"
        ),
    },
}


def _load(paths: ProjectPaths, hid: str) -> dict:
    p = paths.root / "reports" / hid / f"rc_{hid.lower()}_1_screen.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _screened_date(paths: ProjectPaths, blob: dict) -> str:
    log = ReproLog.read(paths.logs_reproducibility / blob["repro_log"])
    return log.timestamp_utc[:10]


def _passing_cells(blob: dict) -> list[tuple[str, dict]]:
    return [
        (inst["instrument"], c)
        for inst in blob["instruments"]
        for c in inst["cells"]
        if c.get("screen_pass")
    ]


def _fmt(x, spec: str = ".3f") -> str:
    if isinstance(x, int | float) and not isinstance(x, bool):
        return format(x, spec)
    return "n/a"


def _ledger_span(paths: ProjectPaths, expert_hash: str) -> dict:
    """Per-instrument ledger session span, derived from the partitions."""
    glob = str(
        paths.data_processed / "shadow_ledger" / f"expert_id={expert_hash}" / "**" / "*.parquet"
    )
    lf = pl.scan_parquet(glob).select("session_date")
    frame = lf.select(
        start=pl.col("session_date").min(), end=pl.col("session_date").max()
    ).collect()
    return {"start": str(frame["start"][0]), "end": str(frame["end"][0])}


def render_card(paths: ProjectPaths, hid: str, blob: dict) -> Path:  # noqa: PLR0915 — one linear card-rendering sequence
    """Render the eight-section v1 card from the artifacts (fully derived)."""
    meta = _REGISTRY[hid]
    design_sha = blob["design_md_sha256"]
    screened = _screened_date(paths, blob)
    passing = _passing_cells(blob)
    screen_pass = bool(passing)
    disposition = "pool-hold-reconsider" if screen_pass else "archive-no-persistent-window"
    any_sc = any(c["s_c_pass"] for i in blob["instruments"] for c in i["cells"])
    sub_note = "" if (screen_pass or any_sc) else "  # sub-reason: archive-no-gross-edge"
    level = blob["screen_level"]
    n_cells_total = sum(len(i["cells"]) for i in blob["instruments"])
    span = _ledger_span(paths, meta["expert_hash"])
    instruments_txt = ", ".join(i["instrument"] for i in blob["instruments"])
    n_gate = next(
        (
            c["s_d"]["n_trials_gate"]
            for i in blob["instruments"]
            for c in i["cells"]
            if c.get("s_d", {}).get("n_trials_gate")
        ),
        None,
    )
    if n_gate is None:
        raise RuntimeError(
            "no cell carries s_d.n_trials_gate (every cell degenerate?) — "
            "refusing to render a card from a malformed screen artifact"
        )

    yaml_lines = ["conditional_edges:"]
    table_rows = []
    for inst in blob["instruments"]:
        for c in inst["cells"]:
            cell_id = f"{inst['instrument']}:{c['cell']}"
            mg = c["mean_gross"]
            ge_line = (
                f"    gross_edge: {mg:.6e}" if isinstance(mg, float) else "    gross_edge: null"
            )
            yaml_lines += [
                f"  - cell: {cell_id}",
                ge_line,
                f"    rw_adj_pvalue: {c['rw_adj_pvalue']:.6f}",
                f"    significant_at_level: {str(bool(c['rw_adj_pvalue'] < level)).lower()}",
                f"    directional_positive: {str(bool(isinstance(mg, float) and mg > 0)).lower()}",
                f"    s_c_pass: {str(bool(c['s_c_pass'])).lower()}",
                f"    screen_pass_all_gates: {str(bool(c.get('screen_pass', False))).lower()}",
            ]
            sd = c.get("s_d", {})
            table_rows.append(
                f"| {cell_id} | {_fmt(mg, '.2e')} | n={c['n']} | "
                f"p={c['rw_adj_pvalue']:.3f} | DSR={_fmt(sd.get('dsr'))} | "
                f"PBO={_fmt(sd.get('pbo'))} | "
                f"{'PASS' if c.get('screen_pass') else 'no'} |"
            )

    stab_rows = []
    for inst in blob["instruments"]:
        for c in inst["cells"]:
            sd = c.get("s_d", {})
            pw = sd.get("per_window_growth")
            if pw:
                n_est = sum(1 for g in pw if isinstance(g, int | float))
                stab_rows.append(
                    f"| {inst['instrument']}:{c['cell']} | {n_est}/{len(pw)} windows "
                    f"estimable | positive-window fraction "
                    f"{_fmt(sd.get('positive_window_fraction'))} |"
                )

    passing_txt = "; ".join(f"{i}:{c['cell']}" for i, c in passing) if passing else "none"
    binding = (
        f"{len(passing)} cell(s) passed S-a..S-e at level {level} "
        f"({passing_txt}); VERDICT deferred (ADR-0015 ratified HOLD)"
        if screen_pass
        else f"no cell passed the S-a..S-e conjunction at level {level}"
    )
    pass_prose = (
        "Screen PASS: the expert enters the ADR-0014 provisional candidate "
        "pool as pool-hold-reconsider with the VERDICT DEFERRED under the "
        "ADR-0015 ratified operator HOLD. Re-adjudication triggers on any "
        "incumbent-set change. NOTHING is certified by this pass; pool entry "
        "is a queue position. The M1 realized-bar and session-level Jaccard "
        "vs the existing pool coverage are computed and REPORTED alongside "
        "this card (setup plan §2.3; the ADR-0015 label-based precondition "
        "governs; the lift is a named, dated operator action)."
        if screen_pass
        else "Screen FAIL: no persistent, ex-ante-selectable window at the "
        "enacted level; archived as archive-no-persistent-window. "
        "Reconsideration requires a fresh registered cycle."
    )

    card = f"""---
# Expert Card - machine-readable frontmatter (schema per ADR-0009 §3)
hid: {hid}
card_version: 1
predecessor_card: null   # first card of a fresh forward candidate
design_md_sha256: "{design_sha}"
repro_log_run_ids: [{blob["repro_log"].replace("repro_log_", "").replace(".json", "")}]
data_span: {{ start: {span["start"]}, end: {span["end"]} }}
instruments: [{instruments_txt}]
execution_tier: 0            # per ADR-0006
trial_register_increment: {n_cells_total}  # rc-{hid.lower()}-1 per-cell records
disposition: {disposition}{sub_note}
---

# Expert Card - {hid} v1: {meta["title"]}

## 1. Provenance header

| Field | Value |
|---|---|
| HID | {hid} |
| Scan | {blob["scan"]} (ADR-0014 SCREEN; first cycle of a fresh forward candidate) |
| design.md SHA-256 | {design_sha[:16]}… (full hash in frontmatter; frozen {screened} lineage) |
| ReproLog run_id | {blob["repro_log"]} |
| Screened (ReproLog UTC date) | {screened} |
| Data span | {span["start"]} → {span["end"]} (ledger session span, derived) |
| Instruments | {instruments_txt} |
| Execution tier | 0 (bar-close; ADR-0006 D2 forbidden-claims list binds per design §13) |
| Shadow-ledger partitions | expert_id={meta["expert_hash"]} (canonical; ADR-0003) |
| Trial-register increment | rc-{hid.lower()}-1 (+{n_cells_total} per-cell records) |
| Screening level | {level} (enacted; config/multipletest_family.yaml governs) |

## 2. Failure-mode decomposition

Screen-tier adjudication is GROSS (pre-cost) per ADR-0002(c)/ADR-0014 S-c;
no net claim is made at this tier. Cost posture (declared at freeze, design
§7): {meta["net_note"]}. Mechanism basis: {meta["mechanism"]}.
Coverage: {meta["coverage_claim"]}.

## 3. Conditional-edge panel

Conditioning set frozen in design §3 (pre-scan, ADR-0002(b)). Correction:
Romano-Wolf StepM within scan (seed {blob["seed_s_c"]}), level = the enacted
`screening_error_rate_target` ({level}; the config value governs); S-d
bounds DSR ≥ 1 − level, PBO ≤ level at gate N = {n_gate}; S-e per the
amended rule (all cells rule-based causal, observation lag 0; latent-state
latency UNATTAINABLE per P1-2.0-H900-BOCPD-WHITENED).

```yaml
{chr(10).join(yaml_lines)}
```

| Cell | Gross edge | n | RW-adj p | DSR | PBO | Screen |
|---|---|---|---|---|---|---|
{chr(10).join(table_rows)}

## 4. Ensemble block

Arsenal snapshot: EMPTY (0 members at card time; ADR-0002(d) non-redundancy
is a VERDICT-tier object under the ADR-0015 HOLD).

```yaml
ensemble:
  marginal_ir_estimate: null   # undefined at |arsenal| = 0 (ADR-0014)
  residual_correlation_bound: null  # authored by the first admission
  known_dependencies:
    - "shares the ES/NQ roll-adjusted substrate with the ORB pool (H101/H103)"
    - "M1 realized-bar/session Jaccard vs pool coverage reported at disposition"
```

## 5. Stability profile

Per-cell rolling-origin growth over the registered h900 evaluation windows
(screen artifact `per_window_growth`; null = no member session in that
window; stateless expert - every window is untrained data):

| Cell | Coverage | Persistence read |
|---|---|---|
{chr(10).join(stab_rows)}

Change-points: none computed at the screen tier. Decayed vs never-worked:
the S-d persistence gates are the screen's separation of window from luck;
no decay dating is asserted.

## 6. Disposition

```yaml
disposition: {disposition}{sub_note}
binding_criterion: "{binding}"
```

{pass_prose}

## 7. Burned-data entry

The screen consumes the 15 registered h900 evaluation windows per
instrument; each window is mirrored to `config/burned_data_ledger.yaml`
under `hid: {hid}` with `purpose: admission-screen` (ADR-0008 D5, per
evaluation window - scripted by the emitter, not hand-maintained).

## 8. Priors update

1. {meta["coverage_claim"]}
2. The screen ran at the enacted level with S-d persistence binding from
   the first cycle (no descriptive-level predecessor exists for this HID).
3. Latent-state conditioning remains unable to pass S-e
   (P1-2.0-H900-BOCPD-WHITENED verdict); every cell here is rule-based
   causal at lag 0.
4. The first VERDICT (at arsenal-building) authors the arsenal-covariance /
   residual-correlation bound memo (register gap 2).
5. Kelly-fraction selection stays blocked (grid materialized, none
   selected; bracketing verdict inconclusive-on-null-ledger).
"""
    out = paths.root / "research" / "01_hypothesis_register" / hid / "expert_card_v1.md"
    out.write_text(card, encoding="utf-8", newline="\n")
    return out


def append_pool_records(paths: ProjectPaths, hid: str, blob: dict, card_path: Path) -> int:
    """Append schema-conformant pool records IDEMPOTENTLY (ADR-0014 D5)."""
    passing = _passing_cells(blob)
    if not passing:
        return 0
    meta = _REGISTRY[hid]
    span = _ledger_span(paths, meta["expert_hash"])
    ledger_slice = f"ES+NQ:full-backfill-{span['start'][:4]}-{span['end'][:4]}"
    ledger = paths.data_processed / "pool_ledger" / "pool_ledger.jsonl"
    existing_keys: set[tuple] = set()
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            existing_keys.add(
                (
                    r.get("hid"),
                    r.get("expert_version"),
                    r.get("kelly_fraction"),
                    r.get("ledger_slice"),
                )
            )
    card_rel = card_path.relative_to(paths.root).as_posix()
    screened = _screened_date(paths, blob)
    head_inst, head = max(passing, key=lambda t: t[1]["s_d"]["dsr"])
    n_written = 0
    with ledger.open("a", encoding="utf-8", newline="\n") as fh:
        for frac in KELLY_GRID:
            key = (hid, "v1", frac, ledger_slice)
            if key in existing_keys:
                print(f"  pool record exists, skipped: {key}")
                continue
            rec = {
                "hid": hid,
                "expert_version": "v1",
                "kelly_fraction": frac,
                "ledger_slice": ledger_slice,
                "provenance": {
                    "expert_hash": meta["expert_hash"],
                    "design_md_sha256": blob["design_md_sha256"],
                    "expert_card_path": card_rel,
                    "cost_model_id": "futures_rt_v1",
                    "execution_tier": 0,
                    "repro_log_path": f"logs/reproducibility/{blob['repro_log']}",
                    "trial_register_id": f"rc-{hid.lower()}-1",
                    "screened_at": screened,
                },
                "screen": {
                    "screen_pass": True,
                    "conditional_edge_cell": "; ".join(f"{i}:{c['cell']}" for i, c in passing),
                    "rw_adj_p": head["rw_adj_pvalue"],
                    "screen_alpha_ref": (
                        "config/multipletest_family.yaml:screening_error_rate_target"
                    ),
                    "dsr": head["s_d"]["dsr"],
                    "dsr_bound_ref": (
                        "1 - screening_error_rate_target (config/multipletest_family.yaml)"
                    ),
                    "pbo": head["s_d"]["pbo"],
                    "pbo_bound_ref": (
                        "screening_error_rate_target (config/multipletest_family.yaml)"
                    ),
                    "cell_dwell_bars": head["s_e"]["cell_dwell_bars"],
                    "detection_latency_bars": head["s_e"]["observation_lag_bars"],
                    "detection_latency_semantics": (
                        "structural observation lag of the rule-based causal "
                        "cell (amended S-e rule; latent-state latency "
                        "UNATTAINABLE -> null for latent-state cells)"
                    ),
                    "selectable": bool(head["s_e"]["pass"]),
                    "headline_cell": f"{head_inst}:{head['cell']}",
                    "passing_cells_detail": [
                        {
                            "instrument": i,
                            "cell": c["cell"],
                            "rw_adj_p": c["rw_adj_pvalue"],
                            "dsr": c["s_d"]["dsr"],
                            "pbo": c["s_d"]["pbo"],
                            "cell_dwell_bars": c["s_e"]["cell_dwell_bars"],
                            "detection_latency_bars": c["s_e"]["observation_lag_bars"],
                            "selectable": bool(c["s_e"]["pass"]),
                        }
                        for i, c in passing
                    ],
                },
                "competence_structure": {
                    "per_cell_oos_growth": {
                        f"{i}:{c['cell']}": [
                            g if isinstance(g, int | float) else None
                            for g in c["s_d"]["per_window_growth"]
                        ]
                        for i, c in passing
                    },
                    "competence_window_cells": [f"{i}:{c['cell']}" for i, c in passing],
                },
                "complementarity": {
                    "marginal_growth_delta": None,  # undefined at |arsenal| = 0 (schema)
                    "covers_uncovered_cell": True,  # cold-start: all cells uncovered
                    "edge_corr_vs_incumbents": None,  # deferred: no incumbents
                    # label-cell Jaccard deferred; the M1 report carries the
                    # realized-bar statistic (setup plan §2.3)
                    "window_overlap_jaccard": None,
                },
                "ruin_leverage": {
                    "geom_growth_at_fraction": None,  # VERDICT-tier (selection blocked)
                    "ruin_prob_contribution": None,  # VERDICT-tier
                },
                "disposition": {
                    "value": "pool-hold-reconsider",
                    "reconsider_on_set_change": True,
                    "last_adjudicated_against": "arsenal:EMPTY (verdict deferred)",
                },
                "note": (
                    "fraction-invariant screen statistics (k1.0 unit-exposure "
                    "gross); kelly_fraction mirrors the ledger materialization, "
                    "none selected; null growth entries = cell has no member "
                    "session in that window; finer per-window records at the "
                    "first verdict"
                ),
            }
            fh.write(json.dumps(rec, sort_keys=True) + "\n")
            n_written += 1
    return n_written


def append_register_trials(paths: ProjectPaths, hid: str, blob: dict) -> bool:
    """Append per-cell trial records to the rc-{hid}-1 family (ADR-0008 D6)."""
    cfg_path = paths.config / "multipletest_family.yaml"
    text = cfg_path.read_text(encoding="utf-8")
    marker = f"family_id: rc-{hid.lower()}-1"
    if marker not in text:
        raise RuntimeError(
            f"register family rc-{hid.lower()}-1 not found - pre-registration missing"
        )
    idx = text.index(marker)
    old_line = f"    trials: []   # appended by RC-{hid}-1 at scan time (pass or fail, every cell)"
    try:
        pos = text.index(old_line, idx)
    except ValueError:
        print(f"  register trials already present for rc-{hid.lower()}-1, skipped")
        return False
    meta = _REGISTRY[hid]
    artifact_rel = f"reports/{hid}/rc_{hid.lower()}_1_screen.json"
    screened = _screened_date(paths, blob)
    lines = [f"    trials:   # per-cell records, RC-{hid}-1 screen (ADR-0008 D6)"]
    for inst in blob["instruments"]:
        for c in inst["cells"]:
            sr = c.get("sharpe")
            sr_txt = f"{sr:.6f}" if isinstance(sr, int | float) else "null"
            lines += [
                f"      - hid: {hid}:{inst['instrument']}:{c['cell']}",
                f"        sharpe_estimate: {sr_txt}",
                (
                    "        return_series_ref: data/processed/shadow_ledger/"
                    f"expert_id={meta['expert_hash']} (cell mask per " + artifact_rel + ")"
                ),
                "        clustering:",
                f"          cluster_key: {hid.lower()}-ledger-"
                + inst["instrument"].lower()
                + "-cell-overlap",
                "          notes: >-",
                "            nested/overlapping conditioning cells of one ledger stream;",
                "            N_eff via the pairwise-complete cell correlations recorded",
                "            in the screen artifact (cell_dependence)",
                f'        registered_at: "{screened}"',
            ]
    new_block = "\n".join(lines)
    text = text[:pos] + new_block + text[pos + len(old_line) :]
    cfg_path.write_text(text, encoding="utf-8", newline="\n")
    return True


def append_burned_spans(paths: ProjectPaths, hid: str, blob: dict, card_path: Path) -> int:
    """Mirror the screen's consumed OOS windows per evaluation window (ADR-0008 D5)."""
    ledger_path = paths.config / "burned_data_ledger.yaml"
    text = ledger_path.read_text(encoding="utf-8")
    purpose = "admission-screen"
    if f"# RC-{hid}-1 screen windows" in text:
        print(f"  burned spans already present for {hid}, skipped")
        return 0
    screened = _screened_date(paths, blob)
    card_rel = card_path.relative_to(paths.root).as_posix()
    lines = [f"  # RC-{hid}-1 screen windows (scripted mirror; ADR-0004 rolling regime):"]
    for symbol in ("ES", "NQ"):
        for w in h900_windows():
            lines += [
                f"  - hid: {hid}",
                f"    instrument: {symbol}",
                f"    start: {w.origin}",
                f"    end: {w.eval_end}",
                f"    purpose: {purpose}  # eval window {w.window_id} (rolling-origin, design §6)",
                f'    recorded_at: "{screened}"',
                f"    expert_card_ref: {card_rel}",
            ]
    if not text.endswith("\n"):
        text += "\n"
    text += "\n".join(lines) + "\n"
    ledger_path.write_text(text, encoding="utf-8", newline="\n")
    return 2 * len(h900_windows())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hid", required=True, choices=tuple(_REGISTRY))
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    blob = _load(paths, args.hid)
    card = render_card(paths, args.hid, blob)
    n_pool = append_pool_records(paths, args.hid, blob, card)
    reg = append_register_trials(paths, args.hid, blob)
    n_burn = append_burned_spans(paths, args.hid, blob, card)
    sha = hashlib.sha256(card.read_bytes()).hexdigest()
    print(f"card: {card} (sha {sha[:12]}...)")
    print(f"pool records: {n_pool}; register trials: {reg}; burned spans: {n_burn}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
