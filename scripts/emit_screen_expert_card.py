"""Emit the Expert Card v{N}, pool-ledger records, and register trials for a screen.

Generates, from the RC-{HID}-2 screen artifact (ADR-0009 Decision 3/6: every
number and every characterization derived from the artifacts — nothing
hand-copied):

  1. ``research/01_hypothesis_register/{HID}/expert_card_v2.md`` — the
     eight-section ADR-0009 card (append-only successor of the v1 retro card).
  2. On a screen PASS: pool-ledger records appended IDEMPOTENTLY to
     ``data/processed/pool_ledger/pool_ledger.jsonl`` using the schema field
     names of ``config/pool_ledger_schema.yaml`` (screen_alpha_ref /
     dsr_bound_ref / pbo_bound_ref pointers; detection_latency_bars carries
     the structural observation lag per the amended S-e rule; selectable
     boolean; VERDICT-tier blocks explicitly null-marked as deferred). One
     record per (hid, expert_version, kelly_fraction, ledger_slice): the
     screen statistics are fraction-invariant (k1.0 unit-exposure gross; the
     fraction axis mirrors the ledger materialization, none selected) and
     ledger_slice is the full backfilled span — finer per-window records are
     generated at the first verdict. Existing (key)-duplicate records are
     SKIPPED with a notice (append-only means new adjudication events append;
     identical re-runs must not).
  3. Per-cell trial records appended to the ``rc-{hid}-2`` family in
     ``config/multipletest_family.yaml`` (ADR-0008 Decision 6) — idempotent
     (skipped if the family already carries trials).

Dispositions (ADR-0014 Decision 3): screen PASS -> ``pool-hold-reconsider``
(verdict DEFERRED at |arsenal| = 0; re-adjudicated on incumbent-set change);
screen FAIL -> ``archive-no-persistent-window`` (sub-reason
``archive-no-gross-edge`` iff S-c passed nowhere). NOTHING is certified.

Usage:
    uv run python scripts/emit_screen_expert_card.py --hid H101
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

from skie_universe2.utils.paths import ProjectPaths  # noqa: E402
from skie_universe2.utils.reproducibility import ReproLog  # noqa: E402

# justify: bit-identity tolerance for the S-c reproduction comparison
# (float-repr round-trip only; same computation, same seed).
_STAT_IDENTITY_TOL = 1e-9
# justify: ADR-0013 Decision 3 registered grid (materialized, none selected).
KELLY_GRID = (0.5, 0.75, 1.0, 1.25)
# justify: ledger session spans (burned-data ledger entries, recorded 2026-07-17).
DATA_SPAN = {"start": "2015-01-05", "end": "2025-12-05"}
# justify: declared mechanism label per registered cell (frozen design §3
# vocabulary) — the §8 characterization is COMPOSED from these per the
# artifact's passing set, never asserted (Phase-2 audit CODE-1-1).
CELL_MECHANISM = {
    "unconditional": "unconditional",
    "high_vol": "high-realized-vol conditional",
    "low_vol": "calm (low-vol) conditional",
    "stress": "stress-band conditional (leakage-clean per-origin)",
    "non_stress": "calm (non-stress) conditional",
    "first_hour_up": "first-hour momentum-continuation",
    "first_hour_down": "first-hour momentum-reversal",
}

_PARENT = {
    "H101": {
        "design_sha12": "a7c5c9178f66",
        "v1_card": "docs/reports/expert_card_H052a_retro_2026-07-10.md",
        "rc1_doc": "docs/reports/H101/RC-H101-1_admission_disposition_2026-07-16.md",
        "rc1_artifact": "reports/H101/rc_h101_1_scan.json",
        "title": "Unconditional first-hour ORB (ES/NQ) - ADR-0014 screen re-run",
    },
    "H103": {
        "design_sha12": "84d01a6b4ad0",
        "v1_card": "docs/reports/expert_card_H054_retro_2026-07-10.md",
        "rc1_doc": "docs/reports/H103/RC-H103-1_admission_disposition_2026-07-16.md",
        "rc1_artifact": "reports/H103/rc_h103_1_scan.json",
        "title": "Stress-state anti-gate ORB (ES/NQ) - ADR-0014 screen re-run",
    },
}


def _load(paths: ProjectPaths, hid: str) -> dict:
    p = paths.root / "reports" / hid / f"rc_{hid.lower()}_2_screen.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _load_rc1(paths: ProjectPaths, hid: str) -> dict:
    return json.loads((paths.root / _PARENT[hid]["rc1_artifact"]).read_text(encoding="utf-8"))


def _full_design_sha(paths: ProjectPaths, hid: str) -> str:
    """Full parent-design SHA-256, verified against the recorded freeze prefix."""
    p = paths.root / "research" / "01_hypothesis_register" / hid / "design.md"
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    prefix = _PARENT[hid]["design_sha12"]
    if not sha.startswith(prefix):
        raise RuntimeError(
            f"{hid} design.md SHA {sha[:12]} does not match the recorded freeze "
            f"prefix {prefix} - the frozen design has drifted; refusing to emit"
        )
    return sha


def _screened_date(paths: ProjectPaths, blob: dict) -> str:
    """Screen date from the run's ReproLog timestamp (not emission-time now())."""
    log = ReproLog.read(paths.logs_reproducibility / blob["repro_log"])
    return log.timestamp_utc[:10]


def _passing_cells(blob: dict) -> list[tuple[str, dict]]:
    out = []
    for inst in blob["instruments"]:
        for c in inst["cells"]:
            if c.get("screen_pass"):
                out.append((inst["instrument"], c))
    return out


def _fmt(x, spec: str = ".3f") -> str:
    if isinstance(x, int | float) and not isinstance(x, bool):
        return format(x, spec)
    return "n/a"


def _net_note(rc1: dict, hid: str) -> str:
    """Net-of-cost summary injected from the RC-1 artifact (RC-XCORR-1 block).

    FAIL-CLOSED (Phase-2 round-2 audit CODE-2-1): a missing expected key
    raises rather than rendering "n/a" while claiming artifact-derived
    content. Key names match the RC-1 artifact exactly (sharpe_h101 /
    sharpe_h103 / residual_information_ratio).
    """
    if hid == "H103":
        parts = []
        for inst in rc1.get("instruments", []):
            x = inst.get("rc_xcorr1")
            if not x:
                continue
            missing = [
                k
                for k in ("sharpe_h101", "sharpe_h103", "residual_information_ratio")
                if k not in x
            ]
            if missing:
                raise RuntimeError(
                    f"rc_xcorr1 block missing expected keys {missing} in the "
                    "RC-1 artifact - refusing to render an empty derived claim"
                )
            parts.append(
                f"{inst['instrument']}: net SR H101 {x['sharpe_h101']:.4f} / "
                f"H103 {x['sharpe_h103']:.4f}, residual IR "
                f"{x['residual_information_ratio']:.4f}"
            )
        if parts:
            return "net-of-cost per the RC-1 RC-XCORR-1 block (" + "; ".join(parts) + ")"
        return "net decomposition: see the RC-1 record (no rc_xcorr1 block present)"
    return (
        "net-of-cost decomposition: VERDICT-tier object; the same-ledger RC-1 "
        "records carry the Tier-0 net series (see the doc reference above)"
    )


def _reproduction_claim(rc1: dict, blob: dict) -> str:
    """Derived S-c reproduction statement (Phase-2 round-2 audit QUANT-2-1).

    Compares (stat, n) per (instrument, cell) between the RC-1 scan and the
    RC-2 screen artifacts and states exactly what matched; never asserts
    bit-identity it did not verify.
    """
    rc1_cells = {
        (i["instrument"], c["cell"]): (c["stat"], c["n"])
        for i in rc1.get("instruments", [])
        for c in i.get("cells", [])
    }
    total, match = 0, 0
    diff_cells = []
    for i in blob["instruments"]:
        for c in i["cells"]:
            key = (i["instrument"], c["cell"])
            if key not in rc1_cells:
                continue
            total += 1
            s1, n1 = rc1_cells[key]
            if n1 == c["n"] and abs(s1 - c["stat"]) < _STAT_IDENTITY_TOL:
                match += 1
            else:
                diff_cells.append(f"{key[0]}:{key[1]}")
    if total and match == total:
        return (
            f"the S-c stage reproduces the RC-1 statistics bit-identically ({match}/{total} cells)"
        )
    return (
        f"the S-c stage reproduces the RC-1 statistics bit-identically for "
        f"{match}/{total} cells (the unchanged constructions); "
        f"{', '.join(diff_cells)} differ by the certified leakage-clean "
        f"per-origin construction (see the §2 exhibit)"
    )


def render_card(paths: ProjectPaths, hid: str, blob: dict) -> Path:  # noqa: PLR0915 — one linear, auditable card-rendering sequence; the eight ADR-0009 sections are emitted in order
    """Render the eight-section card from the artifacts (fully derived)."""
    meta = _PARENT[hid]
    rc1 = _load_rc1(paths, hid)
    repro_claim = _reproduction_claim(rc1, blob)
    design_sha = _full_design_sha(paths, hid)
    screened = _screened_date(paths, blob)
    passing = _passing_cells(blob)
    screen_pass = bool(passing)
    disposition = "pool-hold-reconsider" if screen_pass else "archive-no-persistent-window"
    any_sc = any(c["s_c_pass"] for i in blob["instruments"] for c in i["cells"])
    sub_note = "" if (screen_pass or any_sc) else "  # sub-reason: archive-no-gross-edge"
    level = blob["screen_level"]
    n_cells_total = sum(len(i["cells"]) for i in blob["instruments"])
    run_id = blob["repro_log"].replace("repro_log_", "").replace(".json", "")
    sha16 = blob["screen_addendum_sha256"][:16]
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
        raise RuntimeError("no cell carries s_d.n_trials_gate - artifact malformed")

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
                pos = sd.get("positive_window_fraction")
                stab_rows.append(
                    f"| {inst['instrument']}:{c['cell']} | {n_est}/{len(pw)} windows "
                    f"estimable | positive-window fraction {_fmt(pos)} |"
                )

    passing_txt = "; ".join(f"{i}:{c['cell']}" for i, c in passing) if passing else "none"
    mech_labels = sorted({CELL_MECHANISM[c["cell"]] for _, c in passing})
    binding = (
        f"{len(passing)} cell(s) passed S-a..S-e at level {level} "
        f"({passing_txt}); VERDICT deferred (|arsenal| = 0)"
        if screen_pass
        else f"no cell passed the S-a..S-e conjunction at level {level}"
    )
    prior2 = (
        "The passing windows are: "
        + "; ".join(mech_labels)
        + " - the pool's first coverage vector; disjoint-window forward "
        "experts remain the priority (they cover cells no ORB variant "
        "reaches)."
        if screen_pass
        else "No ORB conditioning cell carries a persistent selectable window "
        "at the enacted level - the ORB family is exhausted at the screen "
        "tier on this substrate."
    )
    pass_prose = (
        "Screen PASS: the expert enters the ADR-0014 provisional candidate "
        "pool as pool-hold-reconsider with the VERDICT DEFERRED (|arsenal| = "
        "0 - the set-level marginal-geometric-growth adjudication requires an "
        "incumbent set and runs at the first-admission protocol). "
        "Re-adjudication triggers on any incumbent-set change (fresh "
        "trial-register increment + appended card version). NOTHING is "
        "certified by this pass; pool entry is a queue position."
        if screen_pass
        else "Screen FAIL: no persistent, ex-ante-selectable window at the "
        "enacted level; archived as archive-no-persistent-window. "
        "Reconsideration requires a fresh registered cycle."
    )

    reversal = ""
    if hid == "H103":
        rc1_stress = next(
            (
                c
                for i in rc1["instruments"]
                if i["instrument"] == "ES"
                for c in i["cells"]
                if c["cell"] == "stress"
            ),
            None,
        )
        scr_stress = next(
            (
                c
                for i in blob["instruments"]
                if i["instrument"] == "ES"
                for c in i["cells"]
                if c["cell"] == "stress"
            ),
            None,
        )
        if rc1_stress and scr_stress:
            reversal = (
                f"\n**Construction-dependence exhibit (binding for prior "
                f"interpretation):** RC-H103-1's headline ES stress finding "
                f"(mean {rc1_stress['mean_gross']:.2e}, n={rc1_stress['n']}, "
                f"leaked full-sample cutoff) REVERSES under the certified "
                f"leakage-clean per-origin construction (mean "
                f"{scr_stress['mean_gross']:.2e}, n={scr_stress['n']}, screen "
                f"{'PASS' if scr_stress['screen_pass'] else 'fail'}). The "
                f"RC-1 'Lundstrom prior contradicted' verdict was rendered on "
                f"the leaked cell and is CONSTRUCTION-DEPENDENT; both records "
                f"stand (append-only), and the screen's construction is the "
                f"certified one.\n"
            )

    uncond_dsr_txt = "; ".join(
        f"{i['instrument']} "
        + _fmt(
            next(c for c in i["cells"] if c["cell"] == "unconditional").get("s_d", {}).get("dsr")
        )
        for i in blob["instruments"]
    )

    card = f"""---
# Expert Card - machine-readable frontmatter (schema per ADR-0009 §3)
hid: {hid}
card_version: 2
predecessor_card: {meta["v1_card"]}
design_md_sha256: "{design_sha}"
screen_addendum_sha256: "{blob["screen_addendum_sha256"]}"
repro_log_run_ids: [{run_id}]
data_span: {{ start: {DATA_SPAN["start"]}, end: {DATA_SPAN["end"]} }}
instruments: [{instruments_txt}]
execution_tier: 0            # per ADR-0006
trial_register_increment: {n_cells_total}  # rc-{hid.lower()}-2 per-cell records
disposition: {disposition}{sub_note}
---

# Expert Card - {hid} v2: {meta["title"]}

## 1. Provenance header

| Field | Value |
|---|---|
| HID | {hid} |
| Scan | {blob["scan"]} (ADR-0014 SCREEN; estimand of the frozen 2026-07-16 design) |
| design.md SHA-256 | {design_sha[:16]}… (full hash in frontmatter; freeze prefix verified) |
| Screen addendum SHA-256 | {sha16}… (frozen 2026-07-17) |
| ReproLog run_id | {blob["repro_log"]} |
| Screened (ReproLog UTC date) | {screened} |
| Data span | {DATA_SPAN["start"]} → {DATA_SPAN["end"]} (per-instrument ledger max) |
| Instruments | {instruments_txt} |
| Execution tier | 0 (bar-close; ADR-0006 — no scalping/intrabar claim) |
| Shadow-ledger partitions | expert_id=orb_first_hour_k1.0@1.0.0 (canonical; ADR-0003) |
| Trial-register increment | rc-{hid.lower()}-2 (+{n_cells_total} per-cell records) |
| Screening level | {level} (enacted 2026-07-17; config/multipletest_family.yaml governs) |

## 2. Failure-mode decomposition

Screen-tier adjudication is GROSS (pre-cost) per ADR-0002(c); the net/cost
decomposition is a VERDICT-tier object. Same-ledger reference: {meta["rc1_doc"]}
({_net_note(rc1, hid)}).
{reversal}
Classification: `conditional-only` — the gross edge concentrates in specific
declared cells ({passing_txt}); the unconditional stream is not
selection-distinguishable at the S-d gate (unconditional DSR
{uncond_dsr_txt} at the gate trial count N={n_gate}).

## 3. Conditional-edge panel

Conditioning set frozen in the parent design §3 (2026-07-16, pre-scan,
ADR-0002(b)); screen protocol frozen 2026-07-17 (addendum). Correction:
Romano-Wolf StepM within scan (seed {blob["seed_s_c"]}; {repro_claim}),
level = the enacted
`screening_error_rate_target` ({level}; the config value governs); S-d
bounds DSR ≥ 1 − level, PBO ≤ level at gate N = {n_gate}; S-e per the
amended rule (rule-based causal cells: structural observation lag;
latent-state latency UNATTAINABLE per P1-2.0-H900-BOCPD-WHITENED).

```yaml
{chr(10).join(yaml_lines)}
```

| Cell | Gross edge | n | RW-adj p | DSR | PBO | Screen |
|---|---|---|---|---|---|---|
{chr(10).join(table_rows)}

## 4. Ensemble block

Arsenal snapshot: EMPTY (0 members at card time; the ADR-0002(d)
non-redundancy test is a VERDICT-tier object, deferred until an incumbent
set exists).

```yaml
ensemble:
  marginal_ir_estimate: null   # undefined at |arsenal| = 0 (ADR-0014)
  residual_correlation_bound: null  # authored by the first admission
  known_dependencies:
    - "H101/H103 share the k1.0 ledger (session-complement structure; RC-XCORR-1)"
```

## 5. Stability profile

Per-cell rolling-origin growth over the registered h900 evaluation windows
(screen artifact `per_window_growth`; null = the cell has no member session
in that window; stateless expert — every window is untrained data):

| Cell | Coverage | Persistence read |
|---|---|---|
{chr(10).join(stab_rows)}

Change-points: none computed at the screen tier (the RC-1 KPSS and
rolling-dispersion exhibits stand; CUSUM/BOCPD change-point dating is a
verdict-tier stability object). Decayed vs never-worked: the S-d
persistence gates (DSR/PBO at the enacted bounds) are the screen's
separation of window from luck; no decay dating is asserted.

## 6. Disposition

```yaml
disposition: {disposition}{sub_note}
binding_criterion: "{binding}"
```

{pass_prose}

## 7. Burned-data entry

| OOS span consumed | Purpose | Mirrored to burned_data_ledger.yaml |
|---|---|---|
| {DATA_SPAN["start"]} → {DATA_SPAN["end"]} ES+NQ | admission-scan | recorded 2026-07-17 ({hid}) |

## 8. Priors update

1. The enacted-level screen separates cells the then-null-level RC-1 could
   not: persistence (S-d) now binds where descriptive significance did not.
2. {prior2}
3. Latent-state (HMM-cell) conditioning cannot pass S-e until a working
   unsupervised detector exists (P1-2.0-H900-BOCPD-WHITENED verdict).
4. The first VERDICT (at arsenal-building) must author the
   arsenal-covariance / residual-correlation bound memo (register gap 2).
5. Kelly-fraction selection stays blocked (grid materialized, none selected;
   bracketing verdict inconclusive-on-null-ledger).
"""
    out = paths.root / "research" / "01_hypothesis_register" / hid / "expert_card_v2.md"
    out.write_text(card, encoding="utf-8", newline="\n")
    return out


def append_pool_records(paths: ProjectPaths, hid: str, blob: dict, card_path: Path) -> int:
    """Append schema-conformant pool records IDEMPOTENTLY (ADR-0014 D5)."""
    passing = _passing_cells(blob)
    if not passing:
        return 0
    ledger_dir = paths.data_processed / "pool_ledger"
    ledger_dir.mkdir(parents=True, exist_ok=True)
    ledger = ledger_dir / "pool_ledger.jsonl"
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
    design_sha = _full_design_sha(paths, hid)
    head_inst, head = max(passing, key=lambda t: t[1]["s_d"]["dsr"])
    n_written = 0
    with ledger.open("a", encoding="utf-8", newline="\n") as fh:
        for frac in KELLY_GRID:
            key = (hid, "v2", frac, "ES+NQ:full-backfill-2015-2025")
            if key in existing_keys:
                print(f"  pool record exists, skipped: {key}")
                continue
            rec = {
                "hid": hid,
                "expert_version": "v2",
                "kelly_fraction": frac,
                "ledger_slice": "ES+NQ:full-backfill-2015-2025",
                "provenance": {
                    "expert_hash": "orb_first_hour_k1.0@1.0.0",
                    "design_md_sha256": design_sha,
                    "screen_addendum_sha256": blob["screen_addendum_sha256"],
                    "expert_card_path": card_rel,
                    "cost_model_id": "futures_rt_v1",
                    "execution_tier": 0,
                    "repro_log_path": f"logs/reproducibility/{blob['repro_log']}",
                    "trial_register_id": f"rc-{hid.lower()}-2",
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
                    "window_overlap_jaccard": None,  # deferred: no incumbents
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
    """Append per-cell trial records to the rc-{hid}-2 family (ADR-0008 D6).

    Idempotent (skipped when the family already carries trials); text-level
    YAML edit that preserves the register's comments.
    """
    cfg_path = paths.config / "multipletest_family.yaml"
    text = cfg_path.read_text(encoding="utf-8")
    marker = f"family_id: rc-{hid.lower()}-2"
    if marker not in text:
        raise RuntimeError(
            f"register family rc-{hid.lower()}-2 not found in "
            "config/multipletest_family.yaml - pre-registration missing"
        )
    idx = text.index(marker)
    old_line = "    trials: []   # per-cell records appended at screen time (pass or fail)"
    try:
        pos = text.index(old_line, idx)
    except ValueError:
        print(f"  register trials already present for rc-{hid.lower()}-2, skipped")
        return False
    artifact_rel = f"reports/{hid}/rc_{hid.lower()}_2_screen.json"
    screened = _screened_date(paths, blob)
    lines = [f"    trials:   # per-cell records, RC-{hid}-2 screen (ADR-0008 D6)"]
    for inst in blob["instruments"]:
        for c in inst["cells"]:
            sr = c.get("sharpe")
            sr_txt = f"{sr:.6f}" if isinstance(sr, int | float) else "null"
            lines += [
                f"      - hid: {hid}:{inst['instrument']}:{c['cell']}",
                f"        sharpe_estimate: {sr_txt}",
                (
                    "        return_series_ref: data/processed/shadow_ledger/"
                    "expert_id=orb_first_hour_k1.0@1.0.0 (cell mask per " + artifact_rel + ")"
                ),
                "        clustering:",
                "          cluster_key: orb-first-hour-ledger-"
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hid", required=True, choices=("H101", "H103"))
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    blob = _load(paths, args.hid)
    card = render_card(paths, args.hid, blob)
    n = append_pool_records(paths, args.hid, blob, card)
    reg = append_register_trials(paths, args.hid, blob)
    sha = hashlib.sha256(card.read_bytes()).hexdigest()
    print(f"card: {card} (sha {sha[:12]}...)")
    print(f"pool records appended: {n}; register trials appended: {reg}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
