"""Registered Kelly-fraction sweep grid (ADR-0013 Decision 3; ADR-0005 Layer 2).

The position-layer Kelly fraction is a **registered swept hyperparameter** over
``{0.5, 0.75, 1.0, 1.25}`` (ADR-0013 Decision 3, accepted 2026-07-12). Every fraction
is materialized as a distinct ``expert_id`` in the shadow ledger; the winner is
data-selected by best geometric (compounded / Kelly log-wealth) growth over the joint
(allocator-config × Kelly-fraction) space — but NO fraction is selected until the
BLOCKING ``P1-2.0-KELLY-GROWTH-CONCAVITY-RUIN-DERIVE`` memo is numerically instantiated
on the shadow ledger (CLAUDE.md governance).

This is the single source of truth for the grid, kept free of any signal/strategy
coupling so the ledger-backfill and admission-scan machinery can import the registered
constant without pulling in a specific expert prototype.
"""

from __future__ import annotations

# ADR-0013 Decision 3: registered Kelly fraction sweep grid. Selection on geometric
# growth is BLOCKED on the two Decision-9 Kelly calibration memos (CLAUDE.md).
KELLY_FRACTION_GRID: tuple[float, ...] = (0.5, 0.75, 1.0, 1.25)
