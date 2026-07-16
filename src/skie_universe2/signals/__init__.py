"""Signal layer (ADR-0005 Layer 1).

Pure signal generation: indicators, regime detection, crossover logic.
No position sizing, no order logic — those belong to the policy and
execution layers respectively.
"""

from __future__ import annotations
