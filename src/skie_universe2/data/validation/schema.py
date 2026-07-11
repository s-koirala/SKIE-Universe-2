"""Pandera schemas for ingested datasets.

Ported from SKIE-Universe 1.0 ``src/skie_ninja/data/validation/schema.py``
(sibling repo), restricted to the two vendor-legacy schemas the Phase C
substrate consumes. Constraints, docstrings, and dtype choices are
preserved verbatim (numerical-fidelity port; adapted imports only).
"""

from __future__ import annotations

import pandera.polars as pa
import polars as pl


class VendorLegacy1minSchema(pa.DataFrameModel):
    """Schema for ``data/processed/vendor_legacy_1min/`` (Databento-sourced
    ES/NQ/MCL/MGC/SIL 1-minute bars, materialized from the machine-level
    raw store registered as ``vendor_skie_ninja_legacy_raw_1min``).

    Matches the Databento ``ohlcv-1m`` schema plus a normalized symbol
    column. Constraints:
    - ``ts_event`` is UTC-tz-aware (Databento emits UTC)
    - ``low <= min(open, close)`` and ``high >= max(open, close)``
      (enforced by data-level check, not type-level)
    - ``volume >= 0``
    - unique ``(contract_symbol, ts_event)`` so there is exactly one bar
      per (contract, minute)
    """

    ts_event: pl.Datetime(time_zone="UTC") = pa.Field(nullable=False)
    rtype: pl.Int64 = pa.Field(nullable=False)
    publisher_id: pl.Int64 = pa.Field(nullable=False)
    instrument_id: pl.Int64 = pa.Field(nullable=False)
    # Note: prices can be NEGATIVE for commodity futures during stress
    # events. Canonical example: WTI Light Sweet Crude (CL/MCL) settled at
    # -$37.63 on 2020-04-20 due to physical-delivery supply imbalance +
    # Cushing storage capacity exhaustion. Validation must accept negative
    # prices to preserve this historically real signal; a `gt=0` rule would
    # be equity-index specific. The finite lower bound catches obvious data
    # corruption while allowing the documented commodity-negative-price
    # regime; -1000 USD is a generous lower bound vs the -$37.63 historical
    # extremum (lifted unchanged from 1.0).
    open: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    high: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    low: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    close: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    volume: pl.Int64 = pa.Field(nullable=False, ge=0)
    # Contract-specific symbol from Databento (e.g., ESH0, NQM3).
    contract_symbol: pl.Utf8 = pa.Field(nullable=False)
    # Normalized root symbol — product-root prefix of contract_symbol.
    symbol: pl.Utf8 = pa.Field(
        nullable=False,
        isin=["ES", "NQ", "MES", "MNQ", "MCL", "MGC", "SIL"],
    )

    class Config:
        """Uniqueness at the contract level: one bar per (contract, minute).

        ``(symbol, ts_event)`` intentionally *not* unique — during roll
        windows the same UTC minute can legitimately appear under two
        adjacent contract codes for the same root symbol.
        """

        unique = ["contract_symbol", "ts_event"]
        strict = True


class VendorLegacy1minRollAdjustedSchema(pa.DataFrameModel):
    """Schema for ``data/processed/vendor_legacy_1min_roll_adjusted/``.

    Continuous-contract derivative of ``vendor_legacy_1min``: successive
    front-month contracts stitched together with multiplicative ratio
    adjustment — the mlfinlab ``get_futures_roll_series(method='relative')``
    variant; roll-event/anchor-bar definitions per de Prado 2018
    *Advances in Financial Machine Learning* ch.2 **§2.4.3** ("Single
    Future Roll", whose own text prescribes ADDITIVE gaps — NOT §2.4.1
    "The ETF Trick") — rolled on volume-crossover with persistence per
    ``config/instruments.yaml`` ``roll_rule``. Log-returns on the adjusted
    series are preserved across roll boundaries.

    **Evidence-bar tier discrimination**: this table is evidence-bar
    eligible for *return-based* features only, and conditionally at that
    (see provenance ``evidence_bar_eligibility_conditions``: the
    DEC_ROLL_LATE_COMMIT substrate defect and ``pit_provisional`` bars).
    Level columns (``open``, ``high``, ``low``, ``close``) are
    retrospectively rescaled by the full-sample roll history and are NOT
    point-in-time safe for walk-forward use without per-fold
    re-materialization. See the ingest module docstring "Point-in-time
    caveat" section; the provenance JSON discriminates via
    ``evidence_bar_eligible_returns`` vs ``evidence_bar_eligible_levels``.
    """

    ts_event: pl.Datetime(time_zone="UTC") = pa.Field(nullable=False)
    # Allows commodity-stress negative prices per the WTI 2020-04-20
    # precedent (cf. VendorLegacy1minSchema). adjustment_factor remains
    # gt=0 since the multiplier is by construction positive; roll-adjusted
    # prices inherit the sign of the raw price.
    open: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    high: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    low: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    close: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    volume: pl.Int64 = pa.Field(nullable=False, ge=0)
    symbol: pl.Utf8 = pa.Field(
        nullable=False,
        isin=["ES", "NQ", "MES", "MNQ", "MCL", "MGC", "SIL"],
    )
    front_contract_symbol: pl.Utf8 = pa.Field(nullable=False)
    adjustment_factor: pl.Float64 = pa.Field(nullable=False, gt=0)
    unadjusted_close: pl.Float64 = pa.Field(nullable=False, ge=-1000.0)
    roll_flag: pl.Boolean = pa.Field(nullable=False)
    # 2.0 addition (round-1 audit QUANT-1-2): True on bars whose
    # front-month label was resolved by the persistence guard using
    # future sessions ([challenger_start, resolution) windows). PIT
    # consumers must exclude or causally re-resolve flagged bars.
    pit_provisional: pl.Boolean = pa.Field(nullable=False)

    class Config:
        """One front-month bar per (symbol, ts_event).

        Unlike ``VendorLegacy1minSchema`` (which allows concurrent
        contracts to coexist during roll windows), the roll-adjusted
        series is a single continuous front-month series per root
        symbol — so ``(symbol, ts_event)`` IS unique here.
        """

        unique = ["symbol", "ts_event"]
        strict = True
