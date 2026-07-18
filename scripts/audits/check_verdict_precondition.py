"""ADR-0015 verdict-precondition REPORTING check (operator-directed rule).

Evaluates the operator-directed, provisional verdict precondition recorded in
``config/pool_ledger_schema.yaml`` (``verdict_precondition`` block, ADR-0015
accepted 2026-07-18) against the live pool ledger
(``data/processed/pool_ledger/pool_ledger.jsonl``): the set-level VERDICT
(ADR-0014 Decision 2) is not scheduled until the pool holds at least
``min_distinct_disjoint_coverage`` distinct ``expert_hash`` values whose
coverage vectors (union of ``competence_window_cells`` per distinct
``expert_hash``) are pairwise non-overlapping.

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
            provenance = record.get("provenance", {})
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
            coverage.setdefault(expert_hash, set()).update(competence["competence_window_cells"])
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


def main() -> int:
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
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"[verdict-precondition] ERROR: {exc}", file=sys.stderr, flush=True)
        return EXIT_ERROR

    print(f"[verdict-precondition] {result.status}: {result.reason}", flush=True)
    for expert_hash, cells in sorted(result.coverage_by_hash.items()):
        print(f"  {expert_hash}: coverage = {sorted(cells)}", flush=True)
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
