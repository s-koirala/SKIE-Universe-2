"""VERDICT-1 shared constants (single source of truth).

The candidate registry and the registered Kelly grid are imported by BOTH
the adjudication harness (`scripts/run_verdict.py`) and the disposition
emitter (`scripts/emit_verdict_disposition.py`) so the two cannot drift
(audit CODE-3-1): the family/version/hids drive the trial identifier
``VERDICT:{stem}:A{idx}:{instrument}:k{arm}:{object}`` and the ReproLog
ledger-partition binding in the harness, and the pool copy-forward /
register appends in the emitter — a version bump edited in one file only
would silently desynchronize them.
"""

from skie_universe2.verdict.registry import KELLY_GRID, VERDICT_REGISTRY

__all__ = ["KELLY_GRID", "VERDICT_REGISTRY"]
