"""Execution layer (ADR-0005 Layer 3).

Order placement, fill simulation, slippage estimation. No signal logic,
no position sizing — those belong to the signal and policy layers.
"""

from __future__ import annotations
