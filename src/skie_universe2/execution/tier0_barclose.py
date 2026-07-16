"""Tier-0 bar-close execution + counterfactual return (ADR-0006 Decision 1).

The shadow-ledger backfill default execution tier: positions set at bar close
fill at bar close, and the counterfactual return the ledger stores is the
position-weighted next-bar log return, less a bar-level turnover cost
(ADR-0006 D4: the cost model applies at *every* tier). Owns the steps §2.4–§2.5
of the backfill plan so they are unit-testable in isolation.

**Exact levered log return (not the linear approximation).** The per-bar gross
counterfactual is ``log(1 + pos·(exp(r) − 1)) = log1p(pos·expm1(r))`` — the log
return of a position ``pos`` in an asset whose 1-bar log return is ``r``. This is
exact for shorts and for leverage ``|pos| > 1`` (the Kelly sweep reaches 1.25),
where the linear form ``pos·r`` is only a first-order approximation and, worse,
**cannot represent ruin**: when ``1 + pos·(exp(r) − 1) ≤ 0`` the levered position
is wiped out and log-wealth is ``−inf``. This module surfaces that as ``-inf`` so
the geometric-growth / P(ruin) analysis (ADR-0013; the frozen ``kelly_growth``
ruin memo this feeds) sees the tail correctly rather than a finite ``pos·r``.

**PIT alignment (load-bearing).** A target position decided at ``close(t)``
accrues the return realized over ``(t, t+1]`` — i.e. ``r_{t+1} =
log(close_{t+1}/close_t)``. This module keys each counterfactual on the **accrual
bar** ``t+1`` (matching `ShadowLedgerWriter` semantics: "the bar the counterfactual
return accrues over"). Bar ``t``'s row uses the position from bar ``t-1``; there
is no look-ahead — the position earning bar ``t``'s return was decided at ``t-1``.

**Boundary conventions (documented).** (a) ``start_position`` is held before bar 0
but earns no bar-0 return (there is no prior bar to accrue over); its entry
turnover is charged on accrual bar 1. (b) The turnover of the trade that
establishes the FINAL bar's position is never charged — there is no accrual bar
``n`` to attribute it to; negligible over a long backfill. (c) The turnover cost
is linear in ``|Δposition|`` (the standard matched-turnover convention): the
per-unit drag is ``switch_drag_notional / 2`` (one-way), so scaling by turnover
is a deliberate linear-in-contracts cost model, not the round-trip nonlinearity.

**Turnover cost convention.** ``per_unit_turnover_cost`` is the log-return drag of
**one unit of |Δposition|** (one-way). A full round trip (flat→±1→flat) has total
turnover 2, so it incurs ``2 · per_unit_turnover_cost`` = one round-trip drag. The
driver therefore passes ``per_unit_turnover_cost = switch_drag_notional / 2``,
where ``switch_drag_notional`` (`FuturesRtV1CostModel`) is the round-trip drag.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Tier0Result:
    """Per-accrual-bar counterfactual returns (all same length as the input).

    Index ``t`` is the accrual bar: ``ret_gross[t]`` is the pre-cost return the
    position (decided at ``t-1``) earns over ``(t-1, t]``; ``turnover[t]`` is the
    ``|Δposition|`` of the trade that established that position; ``ret_net[t]`` is
    ``ret_gross[t]`` minus ``turnover[t] · per_unit_turnover_cost``. Bar 0 is
    ``0.0`` (no prior position or return).
    """

    ret_gross: NDArray[np.float64]
    ret_net: NDArray[np.float64]
    turnover: NDArray[np.float64]


def tier0_counterfactual(
    target_position: NDArray[np.float64],
    log_return: NDArray[np.float64],
    *,
    per_unit_turnover_cost: float,
    start_position: float = 0.0,
) -> Tier0Result:
    """Bar-close counterfactual gross/net returns for a position path (ADR-0006 T0).

    Parameters
    ----------
    target_position : 1-D float array
        Signed position decided at each bar's close (``target_position[t]``
        established at ``close(t)``). Same length as *log_return*.
    log_return : 1-D float array
        Per-bar close-to-close log return; ``log_return[t] = log(close_t /
        close_{t-1})`` is realized over ``(t-1, t]``. ``log_return[0]`` is unused
        (no prior close) and may be NaN.
    per_unit_turnover_cost : float
        Non-negative log-return drag per unit of ``|Δposition|`` (one-way; a round
        trip costs ``2×`` this). ``0`` disables costs.
    start_position : float
        Position held before bar 0 (default flat). The bar-0 entry turnover is
        ``|target_position[0] − start_position|`` and is charged on accrual bar 1.

    Returns
    -------
    Tier0Result
        Gross/net counterfactual returns and turnover, keyed on the accrual bar.
    """
    if per_unit_turnover_cost < 0.0:
        raise ValueError(f"per_unit_turnover_cost must be >= 0, got {per_unit_turnover_cost}")
    pos = np.asarray(target_position, dtype=np.float64)
    r = np.asarray(log_return, dtype=np.float64)
    if pos.ndim != 1 or r.ndim != 1:
        raise ValueError("target_position and log_return must be 1-D")
    if pos.shape != r.shape:
        raise ValueError(f"shape mismatch: position {pos.shape} vs return {r.shape}")
    n = pos.size

    ret_gross = np.zeros(n, dtype=np.float64)
    ret_net = np.zeros(n, dtype=np.float64)
    turnover = np.zeros(n, dtype=np.float64)
    if n < 2:
        return Tier0Result(ret_gross=ret_gross, ret_net=ret_net, turnover=turnover)

    # Position earning the return over (t-1, t] is the one decided at t-1.
    # Exact levered log return log1p(pos·expm1(r)); ruin (arg <= -1, i.e.
    # 1 + pos·(exp(r)-1) <= 0) surfaces as -inf log-wealth (not a finite pos·r).
    pos_prev = pos[:-1]  # decision bars 0 .. n-2, earning accrual bars 1 .. n-1
    arg = pos_prev * np.expm1(r[1:])
    with np.errstate(divide="ignore", invalid="ignore"):
        lev = np.log1p(arg)
    ret_gross[1:] = np.where(arg <= -1.0, -np.inf, lev)  # wipeout-or-worse -> ruin
    # Turnover of the trade that established pos_prev: |pos[t-1] - pos[t-2]|,
    # with pos[-1] = start_position.
    pos_before = np.concatenate([[start_position], pos[:-2]])  # pos[-1] := start_position
    turnover[1:] = np.abs(pos_prev - pos_before)
    ret_net[1:] = ret_gross[1:] - turnover[1:] * per_unit_turnover_cost
    return Tier0Result(ret_gross=ret_gross, ret_net=ret_net, turnover=turnover)
