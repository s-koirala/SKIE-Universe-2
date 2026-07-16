"""Position-policy layer (ADR-0005 Layer 2).

Maps signal-layer outputs to target positions. No indicator logic, no
order/fill mechanics — those belong to the signal and execution layers.
"""

from __future__ import annotations
