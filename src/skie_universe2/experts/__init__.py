"""Expert layer — pluggable Layer-1 signal producers for the shadow-ledger backfill.

The :mod:`~skie_universe2.experts.base` contract (``Expert`` Protocol,
``BarWindow``, ``SignalSeries``, ``assert_prefix_invariant``) is the OD-1
interface every backfilled expert conforms to (ADR-0005 Layer 1).
"""

from __future__ import annotations
