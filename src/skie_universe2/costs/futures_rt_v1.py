"""``futures_rt_v1`` cost model — round-trip log-return drag (H900 §7).

Registered by research/01_hypothesis_register/H900/design.md §7:
bar-level round-trip log-return drag ``log(1 - cost_rt / notional)``,
notional basis (formula-consistent basis per the Phase B round-2
finding QUANT-2-2; the account-dollar basis is reported as a
sensitivity column). Commission + spread schedule: the CME retail
schedule registered in config/instruments.yaml (ported from 1.0 with
CME-cited fees).

Numerical-fidelity adaptation of the 1.0 cost model
``SKIE-Universe@ce018515:src/skie_ninja/backtest/costs/futures_orb_v1.py``
(same per-side decomposition commission + exchange + NFA + 1-tick
slippage prior; same ``log1p(-cost/notional)`` drag formula), with two
registered differences:

- id ``futures_rt_v1`` and round-trip semantics = one allocator switch
  (exit incumbent position + enter successor position = 2 sides = one
  round trip), per H900 §7 c_switch definition;
- the fee schedule is read fail-closed from config/instruments.yaml
  (no hard-coded fee table), consistent with the Phase C config-loader
  convention (round-1 audit CODE-1-1: no silent defaults).

Cross-check: at the QUANT-2-2 reference prices the notional-basis
round-trip drags reproduce the design §7 bracket values (ES ~1.21e-4 at
price 4800, NQ ~4.15e-5 at price 17000) — asserted in
tests/test_futures_rt_v1.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import ClassVar

import numpy as np
import yaml

# Sides per allocator switch: exit incumbent (1) + enter successor (1).
# Definitional to the H900 §7 c_switch ("one round-trip drag"), not
# tunable.
_SIDES_PER_SWITCH = 2  # justify: H900 design.md §7 (exit + enter = one round trip)

# Account-dollar sensitivity basis: the 1.0 KPI convention reports
# terminal wealth on a $10,000 account (e.g. expert_card_H052a_retro
# "$10K"); carried as the registered sensitivity denominator.
ACCOUNT_EQUITY_USD = 10_000.0  # justify: 1.0 KPI $10K account convention (H052a/H054 cards)

_REQUIRED_FIELDS = (
    "commission_per_side_usd",
    "exchange_fee_usd",
    "nfa_fee_usd",
    "tick_value",
    "multiplier",
    "slippage_ticks_per_side",
)


@dataclass(frozen=True)
class InstrumentCostSpec:
    """Per-instrument fee/contract parameters (from config/instruments.yaml)."""

    symbol: str
    commission_per_side_usd: float
    exchange_fee_usd: float
    nfa_fee_usd: float
    tick_value: float
    multiplier: float
    slippage_ticks_per_side: float

    @property
    def fixed_per_side_usd(self) -> float:
        return self.commission_per_side_usd + self.exchange_fee_usd + self.nfa_fee_usd

    @property
    def slippage_per_side_usd(self) -> float:
        return self.slippage_ticks_per_side * self.tick_value


@dataclass(frozen=True)
class FuturesRtV1CostModel:
    """H900 §7 registered cost model (see module docstring)."""

    cost_model_id: ClassVar[str] = "futures_rt_v1"

    specs: dict[str, InstrumentCostSpec]

    @classmethod
    def from_config(cls, config_path: Path) -> FuturesRtV1CostModel:
        """Load fail-closed from config/instruments.yaml.

        Raises KeyError if any required field is missing (no silent
        defaults; CODE-1-1 convention).
        """
        payload = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
        specs: dict[str, InstrumentCostSpec] = {}
        for symbol, block in payload["instruments"].items():
            present = [f for f in _REQUIRED_FIELDS if f in block]
            if not present:
                # No fee schedule registered at all (roll_rule-only
                # instruments, e.g. MCL/MGC/SIL): legitimately skipped.
                continue
            missing = [f for f in _REQUIRED_FIELDS if f not in block]
            if missing:
                # Round-1 audit CODE-1-2: a PARTIAL block is a config
                # defect (typo'd/omitted field), not an unregistered
                # instrument — silently skipping it would contradict the
                # fail-closed contract. Raise, listing what is missing.
                raise KeyError(
                    f"instrument '{symbol}' has a partial futures_rt_v1 fee "
                    f"schedule in {config_path}: present {sorted(present)}, "
                    f"missing {sorted(missing)}. Register all of "
                    f"{sorted(_REQUIRED_FIELDS)} or remove the block's fee "
                    "fields entirely."
                )
            specs[symbol] = InstrumentCostSpec(
                symbol=symbol,
                commission_per_side_usd=float(block["commission_per_side_usd"]),
                exchange_fee_usd=float(block["exchange_fee_usd"]),
                nfa_fee_usd=float(block["nfa_fee_usd"]),
                tick_value=float(block["tick_value"]),
                multiplier=float(block["multiplier"]),
                slippage_ticks_per_side=float(block["slippage_ticks_per_side"]),
            )
        return cls(specs=specs)

    def _spec(self, symbol: str) -> InstrumentCostSpec:
        sym = symbol.upper()
        if sym not in self.specs:
            raise KeyError(
                f"Symbol '{symbol}' has no registered futures_rt_v1 fee schedule "
                f"in config/instruments.yaml. Registered: {sorted(self.specs)}"
            )
        return self.specs[sym]

    def switch_cost_usd(self, symbol: str, n_contracts: int = 1) -> float:
        """USD cost of one allocator switch (= one round trip, 2 sides)."""
        if n_contracts <= 0:
            raise ValueError(f"n_contracts must be positive; got {n_contracts}.")
        spec = self._spec(symbol)
        per_side = spec.fixed_per_side_usd + spec.slippage_per_side_usd
        return _SIDES_PER_SWITCH * n_contracts * per_side

    def switch_drag_notional(
        self, symbol: str, *, reference_price: float, n_contracts: int = 1
    ) -> float:
        """c_switch on the notional basis (H900 §7 primary basis).

        Positive magnitude of the log-return drag
        ``-log(1 - cost / notional)`` with
        notional = reference_price x multiplier x n_contracts.
        """
        if reference_price <= 0:
            raise ValueError(f"reference_price must be > 0; got {reference_price}.")
        spec = self._spec(symbol)
        notional = reference_price * spec.multiplier * n_contracts
        cost = self.switch_cost_usd(symbol, n_contracts)
        ratio = cost / notional
        if ratio >= 1.0:
            raise ValueError(f"cost/notional {ratio} >= 1; reference_price too small.")
        return float(-np.log1p(-ratio))

    def switch_drag_account_dollar(self, symbol: str, *, n_contracts: int = 1) -> float:
        """c_switch on the account-dollar basis (H900 §7 sensitivity column).

        Drag of one switch against the 1.0 $10K account convention:
        ``-log(1 - cost / ACCOUNT_EQUITY_USD)``.
        """
        cost = self.switch_cost_usd(symbol, n_contracts)
        ratio = cost / ACCOUNT_EQUITY_USD
        if ratio >= 1.0:
            raise ValueError(f"cost/account {ratio} >= 1.")
        return float(-np.log1p(-ratio))


def break_even_dwell_bars(
    *, detection_latency_bars: float, c_switch: float, mu_per_bar: float
) -> float:
    """Registered break-even formula (H900 §7): D_be = L_detect + c_switch / mu."""
    if mu_per_bar <= 0:
        raise ValueError(f"mu_per_bar must be > 0; got {mu_per_bar}.")
    if c_switch < 0 or detection_latency_bars < 0:
        raise ValueError("c_switch and detection_latency_bars must be >= 0.")
    return detection_latency_bars + c_switch / mu_per_bar


# Registered mu scenario grid, per 5-minute bar (H900 design.md §7,
# basis-labelled, from the Phase B retro-card record); central scenario
# for the §1/§10 decision is MU_CENTRAL.
MU_GRID: tuple[float, ...] = (1e-5, 4e-5, 1.2e-4, 2.7e-4)  # justify: H900 design.md §7
MU_CENTRAL = 1.2e-4  # justify: H900 design.md §7 central scenario
