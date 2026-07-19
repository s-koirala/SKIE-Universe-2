"""Frozen VERDICT-1 candidate registry + Kelly grid (single source of truth).

Queue names map to the shadow-ledger expert family, the expert version whose
partitions are adjudicated, and the HID(s) whose Expert Cards bump on
disposition. ``ORB`` adjudicates the held H101+H103 hash as ONE expert
implementation (ADR-0014 D3 re-adjudication; both cards bump). See the
package docstring for why this lives in one module (audit CODE-3-1).
"""

from __future__ import annotations

# justify: ADR-0013 D3 registered Kelly grid (materialized, none selected).
KELLY_GRID: tuple[float, ...] = (0.5, 0.75, 1.0, 1.25)

# Queue name -> {family, version, hids} (VERDICT-1 protocol §Queue).
VERDICT_REGISTRY: dict[str, dict] = {
    "H106": {"family": "vr_range_reversal", "version": "1.0.0", "hids": ("H106",)},
    "H105": {"family": "overnight_session_drift", "version": "1.0.0", "hids": ("H105",)},
    "ORB": {"family": "orb_first_hour", "version": "1.0.0", "hids": ("H101", "H103")},
}
