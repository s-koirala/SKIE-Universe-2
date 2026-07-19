"""ADR-0015 verdict-precondition REPORTING check (operator-directed rule).

Evaluates the operator-directed, provisional verdict precondition recorded in
``config/pool_ledger_schema.yaml`` (``verdict_precondition`` block, ADR-0015
accepted 2026-07-18) against the live pool ledger
(``data/processed/pool_ledger/pool_ledger.jsonl``): the set-level VERDICT
(ADR-0014 Decision 2) is not scheduled until the pool holds at least
``min_distinct_disjoint_coverage`` distinct ``expert_hash`` values whose
coverage vectors (union of ``competence_window_cells`` per distinct
``expert_hash``) are pairwise non-overlapping.

**ADR-0017 (accepted 2026-07-19) extension:** the REALIZED-BAR basis — the
pairwise realized-bar/session Jaccards from the M1 machinery
(``scripts/run_m1_overlap_report.py``) — is reported ALONGSIDE the label
basis, read from the artifact the schema's ``realized_bar_input`` addendum
names. Both bases are reports; the exit code keys on the registered LABEL
rule exactly as before (no consumer's semantics change), and the checker
says plainly when the M1 artifact is absent rather than substituting.

REPORTING CHECK ONLY (ADR-0015 Decision 3): this script must NOT be wired
into pre-commit, CI, or any path that blocks a commit. A MET result does NOT
trigger a verdict — the lift action is explicit, dated operator authorization
of the first-admission VERDICT protocol; MET is reported to the operator and
nothing else happens.

The threshold is read at runtime from the registered config block (zero
magic numbers); the rule itself is an operator instruction, not a derived
threshold, and is labeled as such in the config.

Usage:
    uv run python scripts/audits/check_verdict_precondition.py \
        [--pool-ledger data/processed/pool_ledger/pool_ledger.jsonl] \
        [--schema config/pool_ledger_schema.yaml]

Exit codes: 0 = MET (reported, not acted on); 1 = BLOCKED; 2 = input error.
The exit code is the LABEL-rule verdict (ADR-0017 Decision 2).
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from itertools import combinations
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parents[2]
# justify: package = false (pyproject) -> skie_universe2 not installed; path needed.
sys.path.insert(0, str(_ROOT / "src"))

from skie_universe2.utils.paths import ProjectPaths  # noqa: E402

EXIT_MET = 0  # justify: structural exit-code convention (0 = condition met)
EXIT_BLOCKED = 1  # justify: structural exit-code convention (1 = blocked)
EXIT_ERROR = 2  # justify: structural exit-code convention (2 = unusable input)
# justify: exact-subset search bound — combinatorial guard only, far above any
# plausible pool size (n distinct expert hashes); beyond it the check refuses
# rather than silently approximating (S6 stop-rather-than-substitute).
_MAX_EXACT_HASHES = 20


@dataclass(frozen=True)
class PreconditionResult:
    """Outcome of the verdict-precondition evaluation."""

    status: str  # "MET" | "BLOCKED"
    reason: str
    distinct_expert_hash_count: int
    coverage_by_hash: dict[str, frozenset[str]]
    min_required: int


def _load_min_required(schema_path: Path) -> int:
    schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    if not isinstance(schema, dict):
        raise ValueError(
            f"{schema_path}: schema must parse to a mapping, got {type(schema).__name__}"
        )
    block = schema.get("verdict_precondition")
    if not isinstance(block, dict):
        raise ValueError(
            f"{schema_path}: no verdict_precondition block (ADR-0015); cannot evaluate."
        )
    raw = block.get("min_distinct_disjoint_coverage")
    if not isinstance(raw, int) or raw < 2:  # noqa: PLR2004 — 2 = smallest meaningful set size (structural: a 'pair' bound)
        raise ValueError(
            f"{schema_path}: min_distinct_disjoint_coverage must be an int >= 2 "
            f"(got {raw!r}); the registered operator instruction is malformed."
        )
    return raw


def _load_coverage_by_hash(pool_ledger_path: Path) -> dict[str, set[str]]:
    coverage: dict[str, set[str]] = {}
    with pool_ledger_path.open(encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{pool_ledger_path}:{line_no}: invalid JSON ({exc})") from exc
            if not isinstance(record, dict):
                raise ValueError(
                    f"{pool_ledger_path}:{line_no}: record must be a JSON object, "
                    f"got {type(record).__name__}"
                )
            provenance = record.get("provenance", {})
            if not isinstance(provenance, dict):
                raise ValueError(
                    f"{pool_ledger_path}:{line_no}: provenance must be an object, "
                    f"got {type(provenance).__name__}"
                )
            expert_hash = provenance.get("expert_hash")
            if not expert_hash:
                raise ValueError(
                    f"{pool_ledger_path}:{line_no}: record missing provenance.expert_hash"
                )
            competence = record.get("competence_structure")
            if not isinstance(competence, dict) or "competence_window_cells" not in competence:
                # Absent field = schema drift = unusable input (S6). An
                # explicitly EMPTY list stays valid (and is excluded later).
                raise ValueError(
                    f"{pool_ledger_path}:{line_no}: record missing "
                    "competence_structure.competence_window_cells"
                )
            cells = competence["competence_window_cells"]
            # Shape validation (round-2 audit QUANT-2-2): a str is an iterable
            # of characters and would silently decompose under set.update,
            # flipping the label verdict — refuse, never substitute (S6).
            if not isinstance(cells, list) or not all(isinstance(c, str) for c in cells):
                raise ValueError(
                    f"{pool_ledger_path}:{line_no}: competence_window_cells must be a list of str"
                )
            coverage.setdefault(expert_hash, set()).update(cells)
    return coverage


def _max_pairwise_disjoint(vectors: list[frozenset[str]]) -> int:
    """Size of the largest subset of pairwise-disjoint coverage vectors.

    Exact subset search; the pool's distinct-hash count is tiny by
    construction and the search is guarded by ``_MAX_EXACT_HASHES``. Empty
    coverage vectors are excluded upstream (they cover nothing and cannot
    count toward a coverage-based precondition).
    """
    if len(vectors) > _MAX_EXACT_HASHES:
        raise ValueError(
            f"{len(vectors)} distinct expert hashes exceeds the exact-search bound "
            f"{_MAX_EXACT_HASHES}; refusing to approximate (extend the checker instead)."
        )
    best = 1 if vectors else 0
    for size in range(len(vectors), 1, -1):
        if size <= best:
            break
        for combo in combinations(vectors, size):
            union: set[str] = set()
            total = 0
            for vec in combo:
                union.update(vec)
                total += len(vec)
            if len(union) == total:  # pairwise disjoint iff no element repeats
                best = size
                break
        if best >= size:
            break
    return best


def evaluate_precondition(pool_ledger_path: Path, schema_path: Path) -> PreconditionResult:
    """Evaluate the ADR-0015 verdict precondition. Pure; no side effects."""
    min_required = _load_min_required(schema_path)
    coverage_raw = _load_coverage_by_hash(pool_ledger_path)
    coverage = {h: frozenset(c) for h, c in coverage_raw.items()}
    n_distinct = len(coverage)

    if n_distinct < min_required:
        return PreconditionResult(
            status="BLOCKED",
            reason=f"distinct_expert_hash_count = {n_distinct}",
            distinct_expert_hash_count=n_distinct,
            coverage_by_hash=coverage,
            min_required=min_required,
        )

    nonempty = [vec for vec in coverage.values() if vec]
    n_empty = n_distinct - len(nonempty)
    if len(nonempty) < min_required:
        return PreconditionResult(
            status="BLOCKED",
            reason=(
                f"only {len(nonempty)} distinct expert_hash values carry a non-empty "
                f"coverage vector ({n_empty} empty); {min_required} required"
            ),
            distinct_expert_hash_count=n_distinct,
            coverage_by_hash=coverage,
            min_required=min_required,
        )

    n_disjoint = _max_pairwise_disjoint(nonempty)
    if n_disjoint >= min_required:
        return PreconditionResult(
            status="MET",
            reason=(
                f"{n_disjoint} pairwise-disjoint coverage vectors across "
                f"{n_distinct} distinct expert_hash values (>= {min_required} required). "
                "REPORTING ONLY: the VERDICT stays operator-gated (ADR-0015 lift_action)."
            ),
            distinct_expert_hash_count=n_distinct,
            coverage_by_hash=coverage,
            min_required=min_required,
        )
    return PreconditionResult(
        status="BLOCKED",
        reason=(
            f"no set of {min_required} pairwise-disjoint coverage vectors among "
            f"{n_distinct} distinct expert_hash values (max disjoint set size = {n_disjoint})"
        ),
        distinct_expert_hash_count=n_distinct,
        coverage_by_hash=coverage,
        min_required=min_required,
    )


def realized_bar_report_lines(schema_path: Path) -> list[str]:
    """ADR-0017 Decision 2: the realized-bar basis, reported alongside.

    Reads the artifact path from the schema's ``realized_bar_input`` addendum
    (never a hard-coded path) and renders the pairwise Jaccards. Pure
    reporting: returns printable lines; absence OR unreadability of the
    addendum/artifact is stated plainly, never substituted, and never
    propagated as an exception (round-1 audit CR-1-1: the label-keyed exit
    code must be unreachable by any realized-bar reporting failure). The
    artifact path is tried relative to the schema's parent-of-parent (the
    ``config/`` layout) then the schema's own directory (root layouts,
    round-1 audit CR-1-2); both tried paths are named on absence.
    """
    try:
        schema = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
    except (OSError, ValueError, yaml.YAMLError) as exc:
        return [
            f"  realized-bar basis (ADR-0017): schema unreadable for the addendum "
            f"({exc.__class__.__name__}); label basis only. No substitute is reported."
        ]
    parsed = schema if isinstance(schema, dict) else {}
    vp = parsed.get("verdict_precondition")
    block = vp.get("realized_bar_input") if isinstance(vp, dict) else None
    if not isinstance(block, dict) or not isinstance(block.get("artifact"), str):
        return [
            "  realized-bar basis (ADR-0017): schema carries no (well-formed) "
            "realized_bar_input addendum; label basis only."
        ]
    roots = (schema_path.resolve().parent.parent, schema_path.resolve().parent)
    candidates = [r / block["artifact"] for r in roots]
    artifact = next((p for p in candidates if p.is_file()), None)
    if artifact is None:
        tried = "; ".join(str(r / block["artifact"]) for r in roots)
        return [
            f"  realized-bar basis (ADR-0017): M1 artifact absent (tried {tried}); "
            f"run {block.get('machinery', 'scripts/run_m1_overlap_report.py')} first. "
            "No substitute is reported."
        ]
    try:
        blob = json.loads(artifact.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [
            f"  realized-bar basis (ADR-0017): M1 artifact unreadable "
            f"({exc.__class__.__name__}: {exc}); no substitute is reported."
        ]
    lines = [f"  realized-bar basis (ADR-0017; {block['artifact']}):"]
    pairs = blob.get("pairs") if isinstance(blob, dict) else None
    for pair in pairs if isinstance(pairs, list) else []:
        if not isinstance(pair, dict):
            lines.append("    (malformed pair entry skipped)")
            continue
        experts = pair.get("experts")
        a, b = (list(experts) + ["?", "?"])[:2] if isinstance(experts, list) else ("?", "?")
        pred = pair.get("pre_scan_prediction")
        pred = pred if isinstance(pred, dict) else {}
        lines.append(
            f"    {a} <-> {b}: J_bar={pair.get('bar_level_jaccard')} "
            f"J_session={pair.get('session_level_jaccard')} "
            f"(prediction: {pred.get('bar_level', 'n/a')})"
        )
    lines.append(
        "    (both bases are reports; the exit code keys on the label rule — "
        "ADR-0017 D2; neither basis gates mechanically)"
    )
    return lines


def main() -> int:
    # Robust console encoding: the M1 artifact carries non-cp1252 glyphs
    # (e.g. the approx sign in frozen prediction strings); a Windows console
    # must degrade to replacement characters, never crash the report — on
    # BOTH channels (stderr carries exception text; round-1 audit CR-1-4).
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pool-ledger", default=None, help="pool ledger JSONL path")
    parser.add_argument("--schema", default=None, help="pool ledger schema YAML path")
    args = parser.parse_args()

    try:
        if args.pool_ledger and args.schema:
            pool_ledger, schema = Path(args.pool_ledger), Path(args.schema)
        else:
            paths = ProjectPaths.discover()
            pool_ledger = (
                Path(args.pool_ledger)
                if args.pool_ledger
                else paths.data_processed / "pool_ledger" / "pool_ledger.jsonl"
            )
            schema = Path(args.schema) if args.schema else paths.config / "pool_ledger_schema.yaml"
        result = evaluate_precondition(pool_ledger, schema)
    except Exception as exc:  # noqa: BLE001 — deliberate contract guard: ANY label-path failure is an unusable-input condition, which is exactly what EXIT_ERROR exists for (round-2 audit QUANT-2-1: yaml.YAMLError and shape AttributeErrors are not ValueError subclasses and must not fall through to an OS exit 1 masquerading as BLOCKED)
        print(f"[verdict-precondition] ERROR: {exc}", file=sys.stderr, flush=True)
        return EXIT_ERROR

    print(f"[verdict-precondition] {result.status}: {result.reason}", flush=True)
    for expert_hash, cells in sorted(result.coverage_by_hash.items()):
        print(f"  {expert_hash}: coverage = {sorted(cells)}", flush=True)
    # Belt-and-braces (CR-1-1): the function is total by construction, but no
    # realized-bar reporting failure may ever reach the label-keyed exit code.
    try:
        for line in realized_bar_report_lines(schema):
            print(line, flush=True)
    except Exception as exc:  # noqa: BLE001 — deliberate contract guard, degraded to a report line
        print(
            f"  realized-bar basis (ADR-0017): reporting failed "
            f"({exc.__class__.__name__}); label basis only.",
            flush=True,
        )
    if result.status == "MET":
        print(
            "  NOTE: MET is a report to the operator, not a trigger; the "
            "first-admission VERDICT requires explicit dated operator "
            "authorization (ADR-0015 lift_action).",
            flush=True,
        )
        return EXIT_MET
    return EXIT_BLOCKED


if __name__ == "__main__":
    raise SystemExit(main())
