"""Ingest jobs (self-registering) + the global registry.

Importing this package loads the concrete job modules so they
self-register into ``INGEST_REGISTRY``.
"""

from __future__ import annotations

from skie_universe2.data.ingest import (  # noqa: F401  (self-registration imports)
    vendor_legacy_1min,
    vendor_legacy_1min_roll_adjusted,
)
from skie_universe2.data.ingest._registry import INGEST_REGISTRY, IngestJob, register

__all__ = ["INGEST_REGISTRY", "IngestJob", "register"]
