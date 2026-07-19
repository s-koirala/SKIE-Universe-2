"""Emit the append-only side effects of one VERDICT-1 adjudication.

Consumes the adjudication artifact written by ``scripts/run_verdict.py``
(``reports/VERDICT-1/verdict_{candidate}.json``) and materializes the
protocol §8 disposition as five append-only records (ADR-0008; nothing is
ever edited in place):

  1. Per-trial records appended to the ``first-admission-verdict`` family in
     ``config/multipletest_family.yaml`` (protocol §6 surface on the
     8-column [instrument x arm] geometry: 16 trials at |U| = 1, 40 at
     |U| >= 2; identifier
     ``VERDICT:{stem}:A{adjudication_index}:{instrument}:k{arm}:{object}`` —
     instrument keeps each column-trial unique, the adjudication index keeps
     re-adjudication appends unique, audit QUANT-1-6/QUANT-2-2). Idempotent
     per adjudication index.
  2. Pool-ledger records appended to
     ``data/processed/pool_ledger/pool_ledger.jsonl``: copy-forward of the
     latest record per (hid x kelly_fraction) with the verdict-updated
     ``disposition`` block (ADR-0014 D3 — value, reconsider_on_set_change,
     last_adjudicated_against) and provenance pointed at this adjudication.
  3. An appended Expert Card version per affected HID (ADR-0009/ADR-0014 D3
     append-only card bump) rendering the adjudication outcome — all 8
     (instrument x Kelly arm) columns REPORTED, none selected (ADR-0013 D9
     selection stays blocked).
  4. Per-eval-window burned spans appended to
     ``config/burned_data_ledger.yaml`` under ``purpose:
     admission-verdict`` (ADR-0008 D5 mirror; the spans are the SAME 15
     registered windows the screens consumed — protocol §3 span rule, the
     reuse is register-conserved, not hidden). Idempotent per adjudication.
  5. On ``admitted``: the member appended to ``config/arsenal.yaml``
     (created on first admission). ``kelly_fraction_selected`` is null by
     mandate.

Usage:
    uv run python scripts/emit_verdict_disposition.py --candidate H106 --date 2026-07-19
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.eval.windows import h900_windows  # noqa: E402
from skie_universe2.utils.paths import ProjectPaths  # noqa: E402
from skie_universe2.verdict.registry import KELLY_GRID, VERDICT_REGISTRY  # noqa: E402

# Candidate registry + Kelly grid — single source of truth shared with the
# adjudication harness (skie_universe2.verdict.registry; audit CODE-3-1).
_REGISTRY = VERDICT_REGISTRY
# VERDICT-1 protocol §7 substrate-grade labels, applied to every disposition
# artifact (card + pool record). The universal Tier-0 label binds all; H105
# carries the CONDITIONAL-GRADE Dec/Globex caveat + the registered
# DR-repaired re-adjudication; H106 carries the net-not-monetizable caveat.
_TIER0_LABEL = "Tier-0, constant-1-tick-slippage (ADR-0006 D2; not live-capital eligibility)"
_GRADE_NOTES = {
    "H105": (
        "CONDITIONAL-GRADE (§7): December/Globex blind spot inside the competence "
        "window (91 ES / 101 NQ excluded sessions; 69.0%/67.8% overnight-ETH). A "
        "confirmation-grade re-adjudication on the DR-1/DR-2-repaired ledger is a "
        "REGISTERED future-session event (fresh trial-register increment + appended "
        "card), never an automatic step."
    ),
    "H106": (
        "net-not-monetizable caveat (§7): the screened edge is pre-cost; at the "
        "Tier-0 constant-1-tick-per-side floor the 1-bar-hold net is deeply negative. "
        "Any admission is an allocator-unit marginal-contribution judgment (ADR-0001), "
        "not a tradable-standalone claim."
    ),
    "ORB": "standard Tier-0 grade (§7).",
}


def _grade_note(candidate: str) -> str:
    hid0 = _REGISTRY[candidate]["hids"][0]
    key = candidate if candidate in _GRADE_NOTES else hid0
    return _GRADE_NOTES.get(key, _GRADE_NOTES.get(candidate, "standard Tier-0 grade (§7)."))


_ANCHOR = "    # [VERDICT-1 trial-append anchor - do not remove]"
_EMPTY_TRIALS_LINE = (
    "    trials: []   # appended by the VERDICT-1 disposition emitter "
    "(every adjudication, admit or not)"
)


def _stem(candidate: str) -> str:
    return "+".join(_REGISTRY[candidate]["hids"])


def _incumbent_set_hash(incumbents: list[str]) -> str:
    return hashlib.sha256(",".join(sorted(incumbents)).encode()).hexdigest()[:16]


def _load_result(paths: ProjectPaths, candidate: str) -> dict:
    p = paths.root / "reports" / "VERDICT-1" / f"verdict_{candidate.lower()}.json"
    if not p.is_file():
        raise FileNotFoundError(f"adjudication artifact missing: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def _adjudication_index(cfg_text: str, stem: str) -> int:
    """Next A-index for this stem = 1 + max existing (append-only uniqueness)."""
    found = re.findall(rf"- hid: VERDICT:{re.escape(stem)}:A(\d+):", cfg_text)
    return (max(int(x) for x in found) + 1) if found else 1


def _fmt_sr(x: float | int | None) -> str:
    return f"{x:.6f}" if isinstance(x, int | float) and not math.isnan(x) else "null"


def append_register_trials(  # noqa: PLR0913 — record fields are the signature
    paths: ProjectPaths,
    candidate: str,
    result: dict,
    adj_index: int,
    date: str,
    artifact_rel: str,
) -> int:
    """Append the §6 branch-enumerated surface to first-admission-verdict."""
    cfg_path = paths.config / "multipletest_family.yaml"
    text = cfg_path.read_text(encoding="utf-8")
    if "family_id: first-admission-verdict" not in text:
        raise RuntimeError("first-admission-verdict family not registered")
    stem = _stem(candidate)
    if f"- hid: VERDICT:{stem}:A{adj_index}:" in text:
        print(f"  register trials already present for {stem} A{adj_index}, skipped")
        return 0
    meta = _REGISTRY[candidate]
    m_prime = int(result["set_size_augmented"])
    # Protocol §6 surface objects (branch-enumerated; marginal ≡ b4 at |U|=1).
    objects = (
        ["marginal-flat", "rotor"] if m_prime == 1 else ["marginal", "b1", "b3", "b4", "rotor"]
    )
    inference = result["inference"]
    columns = result["columns"]  # 8 registered (instrument x arm) keys
    lines: list[str] = []
    for obj in objects:
        for j, ck in enumerate(columns):
            symbol, karm = ck.split(":")  # "ES", "k1.0"
            f = karm[1:]
            if obj == "rotor":
                # Rotor trials are declaredly Sharpe-LESS (protocol §6).
                sr_txt = "null"
                ref = (
                    f"data/processed/shadow_ledger/expert_id={meta['family']}_k{f}"
                    f"@{meta['version']} asset={symbol} (OOS net rotor per " + artifact_rel + ")"
                )
            else:
                panel = "marginal" if obj == "marginal-flat" else obj
                sr_txt = _fmt_sr(inference[panel]["column_sharpes"][j])
                ref = (
                    f"data/processed/shadow_ledger/expert_id={meta['family']}_k{f}"
                    f"@{meta['version']} asset={symbol} (delta panel column per "
                    + artifact_rel
                    + ")"
                )
            lines += [
                f"      - hid: VERDICT:{stem}:A{adj_index}:{symbol}:k{f}:{obj}",
                f"        sharpe_estimate: {sr_txt}",
                f"        return_series_ref: {ref}",
                "        clustering:",
                f"          cluster_key: verdict-{stem.lower().replace('+', '-')}"
                "-column-object-overlap",
                "          notes: >-",
                "            8 (instrument x Kelly arm) columns of one candidate x nested",
                "            inference objects on one session-aligned OOS panel; N_eff via",
                "            the HAC-adjusted per-column counts in the adjudication artifact",
                f'        registered_at: "{date}"',
            ]
    if _EMPTY_TRIALS_LINE in text:
        block = (
            "    trials:   # per-trial records, VERDICT-1 adjudications (protocol §6)\n"
            + "\n".join(lines)
            + "\n"
            + _ANCHOR
        )
        text = text.replace(_EMPTY_TRIALS_LINE, block, 1)
    elif _ANCHOR in text:
        text = text.replace(_ANCHOR, "\n".join(lines) + "\n" + _ANCHOR, 1)
    else:
        raise RuntimeError(
            "neither the empty trials line nor the append anchor found in "
            "first-admission-verdict - register layout drifted; refusing to guess"
        )
    cfg_path.write_text(text, encoding="utf-8", newline="\n")
    return len(objects) * len(columns)


def append_pool_records(  # noqa: PLR0913
    paths: ProjectPaths,
    candidate: str,
    result: dict,
    adj_index: int,
    date: str,
    card_paths: dict[str, Path],
) -> int:
    """Copy-forward the latest (hid x fraction) records with verdict disposition."""
    ledger = paths.data_processed / "pool_ledger" / "pool_ledger.jsonl"
    records = [
        json.loads(line) for line in ledger.read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    admitted = bool(result["conjunction"]["admitted"])
    set_hash = _incumbent_set_hash(result["incumbents_at_adjudication"])
    trial_reg = f"first-admission-verdict:VERDICT:{_stem(candidate)}:A{adj_index}"
    out_lines = []
    for hid in _REGISTRY[candidate]["hids"]:
        for f in KELLY_GRID:
            latest = None
            for r in records:
                # `hid` is the top-level record key (schema record_key); the
                # provenance block carries expert_hash, not hid.
                if r.get("hid") == hid and r.get("kelly_fraction") == f:
                    latest = r  # last occurrence wins (append-only ledger)
            if latest is None:
                raise RuntimeError(f"no pool record to copy forward for {hid} k{f}")
            new = json.loads(json.dumps(latest))  # deep copy
            new["provenance"]["trial_register_id"] = trial_reg
            new["provenance"]["screened_at"] = date
            new["provenance"]["repro_log_path"] = f"logs/reproducibility/{result['repro_log']}"
            new["provenance"]["expert_card_path"] = (
                card_paths[hid].relative_to(paths.root).as_posix()
            )
            # ADR-0014 D3 disposition block (verdict-rendered).
            best = result["conjunction"]["best_qualifying_column_reported_not_selected"]
            new["disposition"] = {
                "value": ("arsenal-admit-conditional" if admitted else "pool-hold-reconsider"),
                "reconsider_on_set_change": not admitted,
                "last_adjudicated_against": set_hash,
                "substrate_grade": _grade_note(candidate),  # protocol §7 label
                "cost_label": _TIER0_LABEL,
                "adjudication": {
                    "protocol": result["protocol"],
                    "protocol_sha256": result["protocol_sha256"],
                    "adjudication_index": adj_index,
                    "candidate": candidate,
                    "admitted": admitted,
                    "best_qualifying_column_reported_not_selected": best,
                    "artifact": f"reports/VERDICT-1/verdict_{candidate.lower()}.json",
                },
            }
            out_lines.append(json.dumps(new, sort_keys=True))
    with ledger.open("a", encoding="utf-8", newline="\n") as fh:
        for line in out_lines:
            fh.write(line + "\n")
    return len(out_lines)


def _next_card_path(paths: ProjectPaths, hid: str) -> Path:
    reg = paths.root / "research" / "01_hypothesis_register" / hid
    versions = [
        int(m.group(1))
        for p in reg.glob("expert_card_v*.md")
        if (m := re.match(r"expert_card_v(\d+)\.md$", p.name))
    ]
    if not versions:
        raise RuntimeError(f"no existing expert card for {hid}; screen emitter must run first")
    return reg / f"expert_card_v{max(versions) + 1}.md"


def render_cards(
    paths: ProjectPaths, candidate: str, result: dict, adj_index: int, date: str
) -> dict[str, Path]:
    """Append-only card bump per affected HID with the adjudication outcome."""
    c = result["conjunction"]
    stem = _stem(candidate)
    marg = result["inference"]["marginal"]
    columns = result["columns"]
    rows = []
    for j, ck in enumerate(columns):
        rot = result["rotor_by_column"][ck]
        dsr = result["dsr_by_column"][ck]
        rows.append(
            f"| {ck} | {_fmt_sr(marg['column_sharpes'][j])} | "
            f"{_fmt_sr(marg['stepm_adjusted_p'][j])} | "
            f"{'yes' if marg['stepm_identified'][j] else 'no'} | "
            f"{_fmt_sr(rot['p_sidak_column_union'])} | "
            f"{_fmt_sr(dsr.get('dsr'))} |"
        )
    col_table = "\n".join(rows)
    disposition = result["disposition"]
    level = result["screen_level_runtime"]
    incumbents_txt = (
        ", ".join(result["incumbents_at_adjudication"]) or "EMPTY (degenerate first case, |S| = 0)"
    )
    clause1 = f"{_fmt_sr(result['inference']['marginal']['spa_p_consistent'])} — " + (
        "PASS" if c["marginal_spa_pass"] else "FAIL"
    )
    clause2 = (
        f"{_fmt_sr(c['ladder_iu_spa_max_p'])}; rotor min Šidák p "
        f"{_fmt_sr(c['rotor_min_sidak_p'])} — " + ("PASS" if c["ladder_iu_pass"] else "FAIL")
    )
    clause4 = (
        f"DSR bound {_fmt_sr(1.0 - level)}; PBO {_fmt_sr(result['pbo']['pbo'])} "
        f"(bound {_fmt_sr(result['pbo']['bound'])}) — "
        + ("PASS" if c["persistence_pass"] else "FAIL")
    )
    disp_txt = (
        "the member enters config/arsenal.yaml; first-admission triggers "
        "(Kelly re-instantiation, §A.8(1) level re-derivation, covariance "
        "anchor, pool-priority data point, held re-adjudication) fire before "
        "any subsequent queue adjudication."
        if c["admitted"]
        else "held in the provisional pool (ADR-0014 D3); "
        "reconsideration-eligible on the next incumbent-set change."
    )
    out: dict[str, Path] = {}
    for hid in _REGISTRY[candidate]["hids"]:
        path = _next_card_path(paths, hid)
        prior = sorted(path.parent.glob("expert_card_v*.md"))[-1].name
        vtag = path.stem.replace("expert_card_", "")
        body = f"""# {hid} Expert Card {vtag} — VERDICT-1 adjudication A{adj_index}

*Appended {date} (ADR-0009/ADR-0014 D3 append-only card version; prior
version {prior} stands unedited). Rendered by
`scripts/emit_verdict_disposition.py` from
`reports/VERDICT-1/verdict_{candidate.lower()}.json` — never hand-copied.*

## Adjudication record

| Field | Value |
|---|---|
| Protocol | {result["protocol"]} (SHA `{result["protocol_sha256"][:12]}...`) |
| Candidate (queue) | {candidate} (stem {stem}) |
| Adjudication index | A{adj_index} |
| Incumbent set at adjudication | {incumbents_txt} |
| Level (runtime-read) | {level} (config/multipletest_family.yaml governs) |
| Trial surface (this adjudication) | {result["current_trial_surface"]} (§6 branch enumeration) |
| Cumulative register N (DSR) | {result["n_trials_cumulative"]} |
| Seed / bootstrap / rotors | {result["seed"]} / {result["n_bootstrap"]} / {result["n_rotors"]} |
| ReproLog | logs/reproducibility/{result["repro_log"]} |

## §2.2 conjunction

| Clause | Outcome |
|---|---|
| 1. Marginal SPA (consistent p) | {clause1} |
| 2. Ladder IU (max SPA p, non-degenerate rungs) | {clause2} |
| 3. Qualifying columns (StepM ∧ rotor) | {c["qualifying_columns"] or "none"} |
| 4. Persistence (best-qualifying column DSR/PBO) | {clause4} |
| **Admitted** | **{c["admitted"]}** |

## Per-column report — 8 (instrument × Kelly arm) columns; NO fraction selected (ADR-0013 D9)

| Column | Δ Sharpe (marginal) | StepM adj-p | Identified | Rotor Šidák p | DSR |
|---|---|---|---|---|---|
{col_table}

Best qualifying column (REPORTED (instrument, arm) pair, not a selection):
{c["best_qualifying_column_reported_not_selected"] or "none"}.

## Disposition

**{disposition}** — {disp_txt}

Degenerate rungs this adjudication: {result["degenerate_rungs"] or "none"};
B2 identity anchor: {result["identity_anchor_b2"]}.
Trial identifiers: `VERDICT:{stem}:A{adj_index}:{{instrument}}:k{{arm}}:{{object}}`
in the `first-admission-verdict` family.

## §7 substrate grade & labeling (binding)

- {_TIER0_LABEL}.
- {_grade_note(candidate)}
"""
        path.write_text(body, encoding="utf-8", newline="\n")
        out[hid] = path
    return out


def append_burned_spans(
    paths: ProjectPaths, candidate: str, adj_index: int, date: str, card_paths: dict[str, Path]
) -> int:
    """Mirror the verdict's consumed eval windows (ADR-0008 D5; §3 span rule)."""
    ledger_path = paths.config / "burned_data_ledger.yaml"
    text = ledger_path.read_text(encoding="utf-8")
    stem = _stem(candidate)
    marker = f"  # VERDICT-1 {stem} A{adj_index} adjudication windows"
    if marker in text:
        print(f"  burned spans already present for {stem} A{adj_index}, skipped")
        return 0
    first_hid = _REGISTRY[candidate]["hids"][0]
    card_rel = card_paths[first_hid].relative_to(paths.root).as_posix()
    lines = [marker + " (scripted mirror; register-conserved span reuse, protocol §3):"]
    n = 0
    for symbol in ("ES", "NQ"):
        for w in h900_windows():
            lines += [
                f"  - hid: {stem}",
                f"    instrument: {symbol}",
                f"    start: {w.origin}",
                f"    end: {w.eval_end}",
                f"    purpose: admission-verdict  # eval window {w.window_id}, A{adj_index}",
                f'    recorded_at: "{date}"',
                f"    expert_card_ref: {card_rel}",
            ]
            n += 1
    if not text.endswith("\n"):
        text += "\n"
    ledger_path.write_text(text + "\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    return n


def append_arsenal(
    paths: ProjectPaths, candidate: str, result: dict, adj_index: int, date: str
) -> bool:
    """On admission: append the member to config/arsenal.yaml (create on first)."""
    if not result["conjunction"]["admitted"]:
        return False
    p = paths.config / "arsenal.yaml"
    meta = _REGISTRY[candidate]
    header = (
        "# Arsenal register (ADR-0002 as amended by ADR-0014) - the admitted\n"
        "# incumbent set. APPEND-ONLY: members are appended on VERDICT-1\n"
        "# admission; removal (if ever) is a governance action with its own\n"
        "# dated record, never an edit. kelly_fraction_selected is null by\n"
        "# mandate until the Phase-4 champion action (ADR-0013 D9; all four\n"
        "# registered arms are computed and reported on every artifact).\n"
        "members:\n"
    )
    entry = (
        f"  - candidate: {candidate}\n"
        f"    expert_family: {meta['family']}\n"
        f'    expert_version: "{meta["version"]}"\n'
        f"    hids: [{', '.join(meta['hids'])}]\n"
        f'    admitted_at: "{date}"\n'
        f"    disposition: arsenal-admit-conditional\n"
        f"    adjudication_index: {adj_index}\n"
        f"    verdict_artifact: reports/VERDICT-1/verdict_{candidate.lower()}.json\n"
        f"    protocol_sha256: {result['protocol_sha256']}\n"
        f"    incumbent_set_at_admission: [{', '.join(result['incumbents_at_adjudication'])}]\n"
        f"    kelly_fraction_selected: null  # BLOCKED (ADR-0013 D9); reported-only sweep\n"
    )
    if p.is_file():
        text = p.read_text(encoding="utf-8")
        if f"- candidate: {candidate}\n" in text:
            print(f"  {candidate} already in arsenal.yaml, skipped")
            return False
        if not text.endswith("\n"):
            text += "\n"
        p.write_text(text + entry, encoding="utf-8", newline="\n")
    else:
        p.write_text(header + entry, encoding="utf-8", newline="\n")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, choices=tuple(_REGISTRY))
    parser.add_argument("--date", required=True, help="ISO adjudication date for the records")
    args = parser.parse_args()
    paths = ProjectPaths.discover()
    result = _load_result(paths, args.candidate)
    cfg_text = (paths.config / "multipletest_family.yaml").read_text(encoding="utf-8")
    adj_index = _adjudication_index(cfg_text, _stem(args.candidate))
    artifact_rel = f"reports/VERDICT-1/verdict_{args.candidate.lower()}.json"

    cards = render_cards(paths, args.candidate, result, adj_index, args.date)
    n_trials = append_register_trials(
        paths, args.candidate, result, adj_index, args.date, artifact_rel
    )
    n_pool = append_pool_records(paths, args.candidate, result, adj_index, args.date, cards)
    n_burn = append_burned_spans(paths, args.candidate, adj_index, args.date, cards)
    admitted = append_arsenal(paths, args.candidate, result, adj_index, args.date)

    for hid, cp in cards.items():
        print(f"card: {hid} -> {cp.relative_to(paths.root).as_posix()}")
    print(
        f"[A{adj_index}/{args.candidate}] trials: {n_trials}; pool records: {n_pool}; "
        f"burned spans: {n_burn}; arsenal append: {admitted}; "
        f"disposition: {result['disposition']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
