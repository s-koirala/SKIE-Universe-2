"""Roll-adjusted continuous-contract derivative of ``vendor_legacy_1min``.

Numerical-fidelity port of SKIE-Universe 1.0
``src/skie_ninja/data/ingest/vendor_legacy_1min_roll_adjusted.py``
(v0.4.0, sibling repo) per ADR-0011 Decision 2. The roll-adjustment
methodology — every algorithmic function from
:func:`detect_raw_front_month_by_day` through :func:`_adjust_one_symbol`
— is preserved numerically **verbatim**; adapted are imports, path
wiring, and provenance metadata, plus two round-1-audit additions that
do not alter any numerical output: (a) the ``pit_provisional`` metadata
column (see "Point-in-time flag" below) and (b) strict fail-closed
config loaders (:class:`RollConfigError` replaces the 1.0 silent
defaults). Cross-validated bit-exactly on all shared columns against
the 1.0 output registered as
``skie_universe_1_processed_roll_adjusted`` in
[config/data_sources.yaml](../../../../config/data_sources.yaml); see
docs/audits/benchmark_comparison_phaseC_ingest_2026-07-10.md — which
also documents the DEC_ROLL_LATE_COMMIT substrate defect SHARED with
the 1.0 reference (bit-exactness is a port-fidelity claim, not a
substrate-correctness claim).

Stitches successive front-month contracts into one continuous series
per root symbol. Method: **multiplicative ratio adjustment** — the
*relative* variant of the futures roll construction implemented in
mlfinlab ``get_futures_roll_series(method='relative')``. Roll-event
and anchor-bar definitions follow de Prado 2018 *Advances in Financial
Machine Learning* ch.2 §2.4.3 ("Single Future Roll"); note the AFML
text itself prescribes **additive** gap adjustment (Snippet 2.2,
``rollGaps``) — the multiplicative form used here is the mlfinlab
relative-method extension, chosen because it preserves *relative*
(log) returns across the roll boundary. Rolled on **volume-crossover
with persistence window** per
[config/instruments.yaml](../../../../config/instruments.yaml)
``roll_rule``.

(Not to be confused with AFML §2.4.1, "The ETF Trick", which is a
P&L-accumulation method for baskets/spreads/$1-invested series and
additionally handles dividends, bid-ask, and rebalance costs — a
different construction.)

Rationale
---------

Raw front-month concatenation (the ``vendor_legacy_1min`` output)
introduces price-level discontinuities at every roll boundary because
adjacent contracts trade at different prices (contango/backwardation).
Computing returns on the raw series contaminates the return at the
roll boundary with the contract-level price differential, violating
the "adjust for corporate actions before return calc" principle
(rules/quant-project.md §Time-series integrity). Multiplicative
back-adjustment preserves **return** magnitudes across the roll
boundary.

References
----------

  - **Primary (roll events + anchor bars):** de Prado 2018, *Advances
    in Financial Machine Learning* (Wiley, ISBN 978-1119482086), ch.2
    §2.4.3 ("Single Future Roll"). The AFML text prescribes
    **additive** gap adjustment (Snippet 2.2, ``rollGaps``); only the
    roll-event and anchor-bar definitions are taken from it.
  - **Primary (multiplicative/relative adjustment):** mlfinlab
    ``get_futures_roll_series(method='relative')`` — the ratio
    (cumulative gap-ratio product) variant of AFML's construction,
    which preserves log-returns across the roll boundary where the
    additive form preserves price differences.
  - **Supplementary:** Chan 2013, *Algorithmic Trading* (Wiley, ISBN
    978-1118460146), ch.2–3 on continuous-contract construction and
    the return-preservation argument.
  - **Supplementary:** Carver 2023, *Advanced Futures Trading
    Strategies* (Harriman House, ISBN 978-0857199683), on back-adjusted
    futures price series as the working substrate for systematic
    futures strategies.
  - **Operational convention (OHLC/volume extensions):** Uniform
    scalar adjustment of O/H/L/C and unadjusted per-contract volume
    follow the Norgate Data continuous-futures methodology
    (https://norgatedata.com/futures-data.php) and the CSI Unfair
    Advantage manual, "Back-Adjusted Contracts" section. Caveat: both
    vendors' *default* back-adjustment is difference-based (additive);
    only the uniform-scalar-OHLC-tuple + unadjusted-volume operational
    convention is borrowed here, not their default adjustment
    arithmetic. AFML §2.4.3 formalizes only the scalar close-price
    series; OHLC tuple extension is a documentation-only convention,
    not a de Prado result.
  - **Volume vs open-interest crossover:** no peer-reviewed empirical
    comparison of volume-crossover vs OI-crossover realized slippage
    for CME equity-index futures is known as of 2026-04-23 (Evidence
    Hierarchy tier 4 at best for this choice). Practitioner
    convention (CME rollover guidance, Databento default loader)
    uses volume-crossover. 1.0 follow-up ``P1-ROLL-METHOD`` (carried
    into the 2.0 backlog) will empirically compare the two.
  - **Rollover guidance:** CME rollover page retrieved 2026-04-15,
    https://www.cmegroup.com/trading/equity-index/rolldates.html
    (volume/OI migrates to back month ~8 calendar days before
    last-trade).

Algorithm (per root symbol)
---------------------------

**Step 1 — CME trading-day attribution.** Map each 1-minute UTC bar to
its CME trading-session date via the Sunday-17:00-CT boundary rule
(17:00 CT on calendar date D-1 is the start of session date D). This
matches the CME daily-settlement convention. Implementation uses a
polars native +7h shift from CME local time (Sunday 17:00 CT + 7h =
Monday 00:00 CT -> session date Monday). Holiday adjustment is not
required for front-month volume argmax because holidays have
near-zero volume and cannot change argmax outcomes.

**Step 2 — Rolling-window front-month detection (hysteresis).** For
each session date D, compute trailing-``window_days`` cumulative
volume per ``contract_symbol``. Front-month = argmax over contracts
of the windowed cumulative volume. Using a trailing window (not a
single-day argmax) suppresses one-day volume flips near roll
boundaries — the canonical failure mode that ``window_days`` in
the config exists to prevent. A contract only becomes front-month
when its cumulative ``window_days``-session volume leads.
Tie-breaking is deterministic: higher cumulative volume first, then
lexicographically-earliest contract_symbol.

**Step 3 — Roll event detection with persistence guard.** After
step 2, a raw transition at D is a session where front(D) !=
front(D-1). Raw transitions are committed as roll events only if
the new contract remains raw-winner for at least ``window_days``
consecutive sessions starting at D. This enforces the
``roll_rule.window_days`` hysteresis and rejects short oscillations
where volume briefly re-migrates to the older contract.

When persistence is confirmed, the guard **retroactively rewrites**
the effective-front-month label on every session since
``challenger_start`` (the first session the committed challenger
led by raw volume) to the challenger. Consequently, the
``roll_date`` surfaced by ``detect_roll_events`` is
``challenger_start`` — i.e., the first session the challenger
actually led, NOT the session at which the persistence threshold
was first met. The guard verifies persistence; it does not
relocate the boundary. This choice matches CME's own "roll occurs
~8 calendar days before last-trade as volume migrates" framing —
the transition moment is the first day of migration, not the day
the migration is retrospectively confirmed.

**Point-in-time flag (2.0 addition, round-1 audit QUANT-1-2; extended
round-2 QUANT-2-4).** The retroactive rewrite means the
effective-front-month label of every session inside a
pending-challenger window is only decidable using FUTURE information:
sessions in ``[challenger_start, commit)`` need up to
``window_days - 1`` future sessions, and the commit session itself
needs its own full-session volume (the label switches to the
challenger, not the causal incumbent-persists default, and is
decidable only at session close). Flagged span is therefore
``[challenger_start, commit]`` INCLUSIVE for committed rolls, plus
rejected-challenger windows. Those bars carry
``pit_provisional = True`` in the output. Walk-forward consumers and
the ADR-0008 PIT canary suite MUST exclude (or re-resolve causally)
flagged bars: their front-month attribution, and hence their
adjusted-price identity, is not knowable at bar time. The boundary
itself is unchanged (numerical output identical to 1.0); the flag is
metadata.

**Step 4 — Roll anchor per the AFML §2.4.3 roll-event definition.**
At each committed roll event ``(roll_date D, old, new)``, compute

    rho_k = new_open(t_first_new) / old_close(t_last_old)

where

    t_last_old = the last 1-minute bar of ``old`` on the last
                 session prior to D where ``old`` was front-month;
    t_first_new = the first 1-minute bar of ``new`` on session D
                  (its first session as front-month).

Anchor-bar selection matches AFML §2.4.3 / mlfinlab
``get_futures_roll_series``; the *ratio* formed from those anchors is
the mlfinlab relative-method extension (AFML's own Snippet 2.2 forms
the additive gap ``new_open - old_close`` instead). If either bar is
missing (source-data gap), the roll is declared a ``NoOverlapError``
and the user must
repair source coverage. **No post-roll or synchronous-overlap
fallback is used — those would leak future prices into the older
segment's adjustment factor.**

**Step 5 — Cumulative back-adjustment.** Walk backward from the
newest contract (factor 1.0). Each prior contract's cumulative
multiplicative factor = product of all rho_j for j >= k, where k is
the roll at which the contract rolled out of front-month. By the
anchor construction, adjusted_old_close(t_last_old) ==
new_open(t_first_new) — the adjusted old-contract close equals the
new-contract open at the roll boundary, so the first return into the
new contract is return-preserving. Chain-continuity
(``event_{k}.new == event_{k+1}.old``) is asserted.

**Step 6 — Front-month filter and output.** Filter bars so only the
effective-front-month at each session date survives — exactly one
front-month row per (symbol, ts_event) in the output. Emit
adjusted OHLC plus audit metadata (``front_contract_symbol``,
``adjustment_factor``, ``unadjusted_close``, ``roll_flag``,
``pit_provisional``).

Point-in-time caveat (important)
--------------------------------

The adjustment factors computed by this module use the **full sample**
roll history. As a consequence:

  - **Returns** (log-diffs of ``close``) on the adjusted series are
    point-in-time safe: a multiplicative scalar applied to both
    numerator and denominator cancels.
  - **Levels** (``open``, ``high``, ``low``, ``close`` on their own)
    are NOT point-in-time: the adjusted level of a 2021 bar is a
    retrospective rescaling that depends on later rolls. Refreshing
    the pipeline with new data *changes* the absolute adjusted levels
    of historical bars.

Consumers computing level-based features (moving-average distance,
Bollinger z-score, price percentile) in a walk-forward evaluation
MUST either (a) use return-based transforms only, or (b)
re-materialize this derivative within each training fold using
only rolls with roll_date <= fold_end. The provenance record
carries ``level_use_pit_safe: false`` as a machine-readable flag.
(1.0 follow-up ``P1-LEVEL-USE-POLICY``, carried into the 2.0
backlog; ADR-0008 Decision 1 PIT canaries gate any expert entering
the shadow ledger on this.)

Decade-wraparound disambiguation (contract_id_full)
---------------------------------------------------

CME equity-index futures contract symbols use a single-digit year
suffix (e.g., ``ESH5`` denotes March-2015 *or* March-2025; ``NQZ7``
denotes Dec-2017 *or* Dec-2027). On a substrate spanning >=10
calendar years, the naive use of ``contract_symbol`` as a
dictionary key collides between decades and silently destroys the
cumulative-back-adjust anchor (the newest contract's factor of 1.0
gets overwritten by the cumulative product of all rolls when the
loop traverses an older same-symbol contract).

This module disambiguates by appending the contract's 4-digit
**expiry year** to form ``contract_id_full``:

    contract_id_full = f"{contract_symbol}_{expiry_year:04d}"

where ``expiry_year`` is derived per bar from the code's trailing
year digits d and the bar's calendar year y as the smallest year
>= y congruent to d (mod 10^k) — see :func:`_expiry_year_expr`.

Round-2 audit history (QUANT-2-1, critical): the round-0/1 port
keyed on the BAR calendar year instead, inheriting the 1.0
convention. That splits any physical contract whose bars straddle
a calendar-year boundary (routine for monthly-roll MCL/MGC/SIL —
e.g. MCLG6 trades Dec-2025 through its Feb-2026 expiry — and for
ES/NQ once December-spanning raw data lands) into two synthetic
keys, fabricating a roll whose "ratio" is the contract's own
year-boundary overnight return and contaminating every
predecessor's cumulative factor. Expiry-year keying makes the key
a property of the physical contract, eliminating the failure mode;
``_assert_no_consecutive_year_collision`` now guards the
DERIVATION for all instruments (derived expiry years for one code
recur only every 10 years, so any closer pair flags a bug) and
cannot false-positive on legitimate year-spanning. On the current
ES/NQ per-year shards no contract straddles a year boundary, so
this change leaves the materialized output byte-identical
(re-verified against the 1.0 benchmark).

The original ``contract_symbol`` is preserved unchanged in the
output as ``front_contract_symbol`` for downstream display and
cross-referencing with vendor data; ``contract_id_full`` is an
internal pipeline key only.

Operational runbook for data gaps
---------------------------------

If ``NoOverlapError`` is raised on a real-data ingest:

  1. Re-fetch the raw 1-min CSV from Databento — the gap may be a
     pull-level corruption.
  2. If the gap is persistent, consult CME daily-settlement prices
     (CME Rule 813) for the two contracts on the last pre-roll
     session and substitute ``old_close`` with that settlement.
     This substitution is opt-in and NOT the default; it must be
     recorded in provenance ``ratio_anchor_override`` with a
     justification, and requires a fresh audit-remediate round.
  3. As a last resort, drop the problematic contract-pair from the
     universe for the affected calendar period and archive an
     incident report under ``docs/audits/``.

Conforms to ``IngestJob`` protocol in ``_registry.py``.
"""

from __future__ import annotations

import contextlib
import json
import logging
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

import numpy as np
import polars as pl
import yaml

from skie_universe2.data.ingest._registry import register
from skie_universe2.data.validation.schema import VendorLegacy1minRollAdjustedSchema
from skie_universe2.utils.hashing import file_sha256, frame_sha256
from skie_universe2.utils.paths import ProjectPaths, portable_key
from skie_universe2.utils.runcontext import RunContext
from skie_universe2.utils.sessions import CME_SESSION_SHIFT_HOURS, CME_TZ, cme_session_date_expr

_log = logging.getLogger(__name__)

_DATASET_NAME = "vendor_legacy_1min_roll_adjusted"
# 1.0 lineage version 0.4.0 (per-instrument monthly roll-code param, H060).
# The 2.0 port keeps the methodology version identical — the algorithm is
# unchanged — and records the port in provenance ``ported_from``.
_DATASET_VERSION = "0.4.0"

# Session-attribution constants moved to utils/sessions.py so the
# shadow-ledger writer shares the identical rule (QUANT-1-6); aliases
# preserved for port fidelity with the 1.0 module namespace.
_CME_TZ = CME_TZ
_CME_SESSION_SHIFT_HOURS = CME_SESSION_SHIFT_HOURS

# Vendor symbology (Databento GLBX.MDP3 raw_symbol, the legacy substrate
# convention) uses a single-digit calendar-year suffix in CME equity-
# index futures contract codes — 3-letter product root + 1-letter month
# code (CME Group, *Contract Month Codes*,
# https://www.cmegroup.com/month-codes.html) + 1-digit year (CME Group,
# *Understanding Contract Trading Codes*; Databento, *Symbology
# Standards*, https://databento.com/docs/standards-and-conventions/symbology).
# CME itself permits both 1-digit (ESZ5) and 4-digit (ESZ2025) forms; the
# 1-digit form is what the substrate carries. A 1-digit code recurs
# every 10 calendar years (ESH5 -> March-2015 OR March-2025). The
# disambiguator ``contract_id_full = contract_symbol + "_" + YYYY``
# is sound iff every contract's bars land within a single calendar
# year; bars whose ``contract_symbol`` years are <10y apart could
# legitimately be the same physical contract that crossed a year
# boundary, in which case the disambiguator would split it.
# 1.0 Phase O.8 amendment 2026-05-16: lowered from 10 -> 6. Empirical
# discovery on the expanded 2015-2026 substrate: CME ES + NQ contracts
# trade forward ~2-3 years before expiration (e.g., ESH7 March-2027
# contract trades from ~2024 onward), so the bar-calendar-year gap
# between two decade-wraparound instances of the same contract_symbol
# can be 7-9 years rather than strictly 10. The 6-year threshold still
# catches the consecutive-year-split bug (gap=1-5) that the assertion
# is designed to detect, while accepting legitimate decade-wraparound
# pairs whose forward-trading overlaps reduce the calendar-year gap.
# Verified empirically in 1.0: ESH7 with bars in {2017, 2026} (gap=9)
# is the canonical March-2017 contract + March-2027 contract pair, NOT
# a single-contract split.
_CME_CONTRACT_CODE_RECURRENCE_YEARS = 6

# CME month codes per CME Group "Contract Month Codes"
# (https://www.cmegroup.com/month-codes.html, retrieved 2026-05-12).
# Listed for documentation + use by ``_extract_month_code``.
_CME_MONTH_CODES: frozenset[str] = frozenset("FGHJKMNQUVXZ")

# Default roll-code set for callers that do not pass an explicit
# ``roll_codes_override`` and whose YAML entry omits ``roll_rule.codes``.
# Matches the quarterly equity-index convention (H/M/U/Z) preserved
# verbatim from the 1.0 v0.1.0-v0.3.0 implementation; metals/energy
# instruments (MCL/MGC/SIL) declare their own ``roll_rule.codes`` in
# config/instruments.yaml.
_DEFAULT_EQUITY_INDEX_ROLL_CODES: frozenset[str] = frozenset("HMUZ")

# Minimum length of a parseable CME contract symbol: 1-char root +
# 1-char month + 1-digit year (e.g. ``ZH5``). All real-world CME
# roots are >= 2 chars (ES, MES, MCL, etc.), so this is a lower bound
# rather than the practical minimum.
_MIN_CONTRACT_SYMBOL_LENGTH = 3

# Cap on the number of offending contract symbols enumerated in the
# ``_assert_roll_codes_subset`` ValueError message before truncating
# with a ``...`` ellipsis. Operational choice — surface enough names
# to diagnose without unbounded message length.
_ROLL_CODES_ERROR_MAX_EXAMPLES = 10


class NoOverlapError(ValueError):
    """Raised when a roll event has no valid AFML §2.4.3 anchor bars
    (either ``old`` has no bar on its last-as-front session, or
    ``new`` has no bar on its first-as-front session). Indicates
    upstream data gap; see module docstring 'Operational runbook for
    data gaps'."""


@dataclass(frozen=True)
class RollEvent:
    """One roll transition that has passed the persistence guard."""

    roll_date: date  # first session date where new_contract is front-month
    old_contract: str
    new_contract: str


@dataclass(frozen=True)
class RollRatio:
    """Computed ratio for a single roll event (AFML §2.4.3 anchor)."""

    event: RollEvent
    t_old_close_utc: datetime
    t_new_open_utc: datetime
    old_close: float
    new_open: float
    ratio: float  # = new_open / old_close


class RollConfigError(ValueError):
    """Raised when ``config/instruments.yaml`` is missing, malformed, or
    lacks the required ``roll_rule`` keys for a symbol in the production
    load path. Fail-closed by design (round-1 audit CODE-1-1/QUANT-1-4/
    REPRODUCIBILITY-1-4): a silently defaulted persistence window or
    roll-code set is a methodology change, not a fallback. Defaults are
    reachable ONLY through the explicit ``window_days_override`` /
    ``roll_codes_override`` constructor arguments (test/synthetic
    fixtures)."""


def _read_instruments_yaml(yaml_path: Path | None = None) -> dict[str, Any]:
    """Load and shape-check ``config/instruments.yaml`` (strict)."""
    if yaml_path is None:
        yaml_path = ProjectPaths.discover().root / "config" / "instruments.yaml"
    if not yaml_path.is_file():
        raise RollConfigError(
            f"instruments config not found at {yaml_path}; the roll-adjusted "
            f"ingest refuses to run without an explicit roll_rule per symbol."
        )
    try:
        cfg = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise RollConfigError(f"instruments config {yaml_path} is not valid YAML: {exc}") from exc
    if not isinstance(cfg, dict) or not isinstance(cfg.get("instruments"), dict):
        raise RollConfigError(
            f"instruments config {yaml_path} malformed: top-level 'instruments' "
            f"mapping required."
        )
    return cfg["instruments"]


def _load_roll_window_days(symbol: str, yaml_path: Path | None = None) -> int:
    """Read the ``window_days`` parameter from ``config/instruments.yaml``.

    Each contract's ``roll_rule.window_days`` is the persistence window
    required for a roll transition to commit. Matches the value that
    callers have already flagged ``# justify:`` in the yaml.

    Strict: raises :class:`RollConfigError` on missing file, YAML
    error, absent symbol, absent ``roll_rule``/``window_days`` key, or
    a non-positive/non-int value. There is NO silent default in this
    path — synthetic fixtures use ``window_days_override``.
    """
    instruments = _read_instruments_yaml(yaml_path)
    sym_cfg = instruments.get(symbol)
    if not isinstance(sym_cfg, dict):
        raise RollConfigError(
            f"Symbol {symbol!r} is not declared in config/instruments.yaml; "
            f"declared: {sorted(instruments)}."
        )
    roll_rule = sym_cfg.get("roll_rule")
    if not isinstance(roll_rule, dict):
        raise RollConfigError(f"Symbol {symbol!r} has no 'roll_rule' mapping in instruments.yaml.")
    w = roll_rule.get("window_days")
    if not isinstance(w, int) or isinstance(w, bool) or w < 1:
        raise RollConfigError(
            f"Symbol {symbol!r}: roll_rule.window_days must be a positive " f"integer; got {w!r}."
        )
    return int(w)


def _load_roll_codes(symbol: str, yaml_path: Path | None = None) -> frozenset[str]:
    """Read the ``roll_rule.codes`` set from ``config/instruments.yaml``.

    Each instrument's ``roll_rule.codes`` is the closed set of CME
    month codes (per CME *Contract Month Codes*,
    https://www.cmegroup.com/month-codes.html) whose contracts are
    expected to appear as front-month over the active trading
    calendar. The 1-letter codes correspond to:

      F-Jan G-Feb H-Mar J-Apr K-May M-Jun
      N-Jul Q-Aug U-Sep V-Oct X-Nov Z-Dec

    Conventional sets (verifiable from CME contract specs):

      - Equity-index quarterly (ES/NQ/MES/MNQ): H M U Z.
      - Energy monthly (CL/MCL): all 12 codes.
      - Gold metals (MGC, GC): G J M Q V Z (Feb/Apr/Jun/Aug/Oct/Dec).
      - Silver metals (SIL, SI): H K N U Z (Mar/May/Jul/Sep/Dec).

    Strict: raises :class:`RollConfigError` on missing file, YAML
    error, absent symbol, absent ``roll_rule``, or an absent/empty/
    invalid ``codes`` list (round-1 audit fail-closed remediation; the
    1.0 silent H/M/U/Z default is gone from the production path — every
    instrument in config/instruments.yaml now declares ``codes``
    explicitly, and synthetic fixtures use ``roll_codes_override``).

    The returned set is used defensively by
    ``_assert_roll_codes_subset`` to surface a controlled ``ValueError``
    if the input data contains a contract whose embedded month code is
    not in the configured set — i.e., either upstream data corruption
    or a mis-configuration of ``roll_rule.codes``. It does NOT alter
    the volume-driven front-month detection algorithm, which is
    code-agnostic by construction (it argmaxes over whatever contract
    symbols appear in the input).
    """
    instruments = _read_instruments_yaml(yaml_path)
    sym_cfg = instruments.get(symbol)
    if not isinstance(sym_cfg, dict):
        raise RollConfigError(
            f"Symbol {symbol!r} is not declared in config/instruments.yaml; "
            f"declared: {sorted(instruments)}."
        )
    roll_rule = sym_cfg.get("roll_rule")
    if not isinstance(roll_rule, dict):
        raise RollConfigError(f"Symbol {symbol!r} has no 'roll_rule' mapping in instruments.yaml.")
    codes = roll_rule.get("codes")
    if not isinstance(codes, list) or not codes:
        raise RollConfigError(
            f"Symbol {symbol!r}: roll_rule.codes must be a non-empty list of "
            f"CME month codes; got {codes!r}. Declare it explicitly in "
            f"config/instruments.yaml (fail-closed; no silent default)."
        )
    codeset = frozenset(str(c).upper() for c in codes)
    unknown = codeset - _CME_MONTH_CODES
    if unknown:
        raise RollConfigError(
            f"config/instruments.yaml: {symbol}.roll_rule.codes "
            f"contains non-CME month codes {sorted(unknown)}; "
            f"valid CME codes are {sorted(_CME_MONTH_CODES)}."
        )
    return codeset


class VendorLegacy1minRollAdjustedIngestJob:
    """Ingest job: derive roll-adjusted continuous series from
    the already-processed raw ``vendor_legacy_1min`` partitions."""

    name: str = _DATASET_NAME
    version: str = _DATASET_VERSION

    # Track the per-symbol algorithmic detail (rolls, factors) so
    # emit_provenance can report it without re-running the pipeline.
    _last_run_summary: dict[str, dict[str, Any]]

    def __init__(
        self,
        source_dataset: str = "vendor_legacy_1min",
        symbols: tuple[str, ...] = ("ES", "NQ", "MCL", "MGC", "SIL"),
        window_days_override: int | None = None,
        roll_codes_override: dict[str, frozenset[str]] | None = None,
    ) -> None:
        self._source_dataset = source_dataset
        self._symbols = tuple(symbols)
        self._window_days_override = window_days_override
        # Per-symbol roll-code override map. Symbols absent from the map
        # resolve through ``_load_roll_codes(sym)`` (YAML, strict — see
        # RollConfigError). The override args are the ONLY sanctioned
        # bypass of the strict config path; tests use them to pass
        # synthetic parameters without touching instruments.yaml.
        self._roll_codes_override = dict(roll_codes_override) if roll_codes_override else None
        self._last_run_summary = {}

    # ------------------------------------------------------------------
    # fetch: list parquet files under data/processed/{source_dataset}/
    # ------------------------------------------------------------------

    def fetch(self, start: date, end: date, ctx: RunContext) -> list[Path]:
        src_root = ctx.paths.data_processed / self._source_dataset
        if not src_root.is_dir():
            raise FileNotFoundError(
                f"Source dataset root not found: {src_root}. "
                f"Run `scripts/ingest.py --dataset {self._source_dataset}` first."
            )

        out: list[Path] = []
        for parquet in sorted(src_root.rglob("part-*.parquet")):
            # Partition layout: symbol=XX/year=YYYY/part-NNNN.parquet
            year_part = parquet.parent.name  # "year=YYYY"
            sym_part = parquet.parent.parent.name  # "symbol=XX"
            if not year_part.startswith("year=") or not sym_part.startswith("symbol="):
                continue
            try:
                year_val = int(year_part.split("=", 1)[1])
            except ValueError:
                continue
            sym_val = sym_part.split("=", 1)[1]
            if sym_val not in self._symbols:
                continue
            if year_val < start.year or year_val > end.year:
                continue
            out.append(parquet)

        if not out:
            _log.warning(
                "No source parquets under %s for symbols=%s years=%s..%s",
                src_root,
                self._symbols,
                start.year,
                end.year,
            )
        else:
            _log.info(
                "Located %d source parquets (symbols=%s years=%s..%s)",
                len(out),
                self._symbols,
                start.year,
                end.year,
            )
        return out

    # ------------------------------------------------------------------
    # parse: load + concatenate + sort + adjust
    # ------------------------------------------------------------------

    def parse(self, raw_paths: list[Path], ctx: RunContext) -> pl.LazyFrame:
        del ctx
        if not raw_paths:
            return _empty_adjusted_frame().lazy()
        frames = [pl.scan_parquet(rp) for rp in raw_paths]
        source = pl.concat(frames, how="vertical").sort(["symbol", "contract_symbol", "ts_event"])
        return self.adjust(source)

    # ------------------------------------------------------------------
    # adjust: per-symbol dispatcher
    # ------------------------------------------------------------------

    def adjust(self, df: pl.LazyFrame) -> pl.LazyFrame:
        collected = df.collect()
        if collected.height == 0:
            return _empty_adjusted_frame().lazy()

        self._last_run_summary.clear()
        per_symbol: list[pl.DataFrame] = []
        for sym in sorted(collected["symbol"].unique(maintain_order=True).to_list()):
            sym_df = collected.filter(pl.col("symbol") == sym)
            if self._window_days_override is not None:
                # Explicit constructor override — the only sanctioned
                # bypass of the strict YAML path (WARNING per audit A).
                _log.warning(
                    "window_days for %s taken from explicit override (%d), "
                    "not config/instruments.yaml.",
                    sym,
                    self._window_days_override,
                )
                window_days = self._window_days_override
            else:
                window_days = _load_roll_window_days(sym)
            if self._roll_codes_override and sym in self._roll_codes_override:
                _log.warning(
                    "roll codes for %s taken from explicit override, "
                    "not config/instruments.yaml.",
                    sym,
                )
                roll_codes = frozenset(self._roll_codes_override[sym])
            else:
                roll_codes = _load_roll_codes(sym)
            adjusted, summary = _adjust_one_symbol(sym_df, sym, window_days, roll_codes=roll_codes)
            self._last_run_summary[sym] = summary
            per_symbol.append(adjusted)

        out = pl.concat(per_symbol, how="vertical").sort(["symbol", "ts_event"])
        return out.lazy()

    # ------------------------------------------------------------------
    # validate: schema + OHLC + monotonicity + cross-row invariants
    # ------------------------------------------------------------------

    def validate(self, df: pl.LazyFrame) -> None:
        collected = df.collect()
        VendorLegacy1minRollAdjustedSchema.validate(collected)

        # OHLC consistency on adjusted prices. Positive scalar
        # multiplication preserves ordering: low <= min(o, c) <= max(o, c) <= high.
        violations = collected.filter(
            (pl.col("low") > pl.col("open"))
            | (pl.col("low") > pl.col("close"))
            | (pl.col("low") > pl.col("high"))
            | (pl.col("high") < pl.col("open"))
            | (pl.col("high") < pl.col("close"))
        )
        if violations.height > 0:
            raise ValueError(
                f"Adjusted OHLC consistency violated on {violations.height} rows; "
                f"first: {violations.head(1).to_dicts()}"
            )

        # Monotonicity per symbol.
        sort_check = collected.sort(["symbol", "ts_event"])
        if not collected.equals(sort_check):
            raise ValueError("ts_event is not monotonically increasing within each symbol.")

        # Audit invariant: close == unadjusted_close * adjustment_factor,
        # with tolerance derived from float64 ULP and the longest
        # ratio-product chain length. IEEE-754 double has eps ~ 2.22e-16;
        # each multiplicative step in the cumulative factor contributes
        # at most ~eps relative rounding, so for an N-step chain the
        # bound is ~3 N eps (Higham 2002 §3.1). We use a generous
        # 10 N eps multiplied by the price magnitude for robustness.
        n_rolls = max(1, int(collected["roll_flag"].sum()))
        eps = float(np.finfo(np.float64).eps)
        max_px = float(collected["close"].abs().max() or 0.0)
        tol = 10.0 * n_rolls * eps * max_px
        recovered = collected.with_columns(
            (pl.col("unadjusted_close") * pl.col("adjustment_factor")).alias("_recovered")
        )
        bad = recovered.filter((pl.col("close") - pl.col("_recovered")).abs() > tol)
        if bad.height > 0:
            raise ValueError(
                f"Audit invariant violated: close != unadjusted_close * "
                f"adjustment_factor (tol={tol:.3e}) on {bad.height} rows; "
                f"first: {bad.head(1).to_dicts()}"
            )

        # Decade-disambiguated grouping key for cross-row invariants.
        # Two contracts whose 1-digit-year-suffix codes collide across
        # decades (e.g. ESH5 in 2015 and ESH5 in 2025) must NOT be
        # merged when checking factor uniqueness or first-session
        # roll_flag — they are physically distinct contracts. The
        # production pipeline keys on contract_id_full internally; the
        # validate step re-derives the SAME key from
        # (front_contract_symbol, expiry year) via _expiry_year_expr —
        # expiry-keyed since round-2 audit QUANT-2-1, so a contract
        # legitimately spanning a calendar-year boundary groups as one
        # family here exactly as it does in production.
        with_full = collected.with_columns(
            (
                pl.col("front_contract_symbol")
                + pl.lit("_")
                + _expiry_year_expr("front_contract_symbol").cast(pl.Utf8).str.zfill(4)
            ).alias("_front_contract_id_full")
        )

        # Cross-row invariant (a): exactly one contract per symbol with
        # adjustment_factor == 1.0. That's the anchor (newest) contract.
        # Use isclose rather than == to tolerate cumulative float error
        # (the newest contract itself never multiplies, but defensive).
        # Counts on contract_id_full so a 10-year wraparound that
        # produces the same 1-digit display code in two decades does
        # not falsely satisfy the invariant.
        for sym in sorted(with_full["symbol"].unique(maintain_order=True).to_list()):
            sym_rows = with_full.filter(pl.col("symbol") == sym)
            # 1e-12: anchor-detection tolerance, ~4.5e3 ULP of 1.0 —
            # generous vs the exact-1.0 anchor yet 4 orders below any
            # plausible roll ratio deviation (|rho - 1| >~ 1e-4 for CME
            # equity-index rolls). Lifted unchanged from 1.0.
            anchor_rows = sym_rows.filter(
                (pl.col("adjustment_factor") - 1.0).abs() < 1e-12  # noqa: PLR2004
            )
            n_anchor_contracts = anchor_rows["_front_contract_id_full"].n_unique()
            if n_anchor_contracts != 1:
                raise ValueError(
                    f"Symbol {sym}: expected exactly one contract with "
                    f"adjustment_factor==1.0 (the newest/anchor); got "
                    f"{n_anchor_contracts}."
                )

        # Cross-row invariant (b): adjustment_factor is constant within
        # each (symbol, contract_id_full) — i.e. distinct decades of the
        # same display contract_symbol get distinct factors and that's
        # OK; what must NOT vary is the factor inside one physical
        # contract.
        factor_variance = (
            with_full.group_by(["symbol", "_front_contract_id_full"])
            .agg(pl.col("adjustment_factor").n_unique().alias("_n"))
            .filter(pl.col("_n") > 1)
        )
        if factor_variance.height > 0:
            raise ValueError(
                f"adjustment_factor is not constant within some "
                f"(symbol, front_contract_symbol) group: "
                f"{factor_variance.to_dicts()}"
            )

        # Cross-row invariant (c): roll_flag True <=> first SESSION per
        # (symbol, contract_id_full). roll_flag marks every bar whose
        # session_date equals the minimum session_date for that contract
        # (all intraday bars on the roll-in session). Keyed on
        # contract_id_full (1.0 v0.3.0 decade-wraparound fix).
        with_session = with_full.with_columns(_session_date_expr().alias("_session_date"))
        per_contract_first_session = with_session.group_by(
            ["symbol", "_front_contract_id_full"], maintain_order=True
        ).agg(pl.col("_session_date").min().alias("_first_session"))
        marker = with_session.join(
            per_contract_first_session,
            on=["symbol", "_front_contract_id_full"],
            how="inner",
        ).with_columns(
            (pl.col("_session_date") == pl.col("_first_session")).alias("_expected_flag")
        )
        mismatch = marker.filter(pl.col("roll_flag") != pl.col("_expected_flag"))
        if mismatch.height > 0:
            raise ValueError(
                f"roll_flag is inconsistent with first-session-per-contract on "
                f"{mismatch.height} rows; first: {mismatch.head(1).to_dicts()}"
            )

        _log.info(
            "Roll-adjusted validation passed (rows=%d, symbols=%s, rolls=%d)",
            collected.height,
            sorted(collected["symbol"].unique().to_list()),
            n_rolls,
        )

    # ------------------------------------------------------------------
    # write_processed: partitioned parquet, two-phase commit with
    # staging swap
    # ------------------------------------------------------------------

    def write_processed(self, df: pl.LazyFrame, ctx: RunContext) -> Path:
        """Partitioned write: ``symbol={SYM}/year={YYYY}/part-0000.parquet``.

        Two-phase commit: stage to ``_staging`` -> re-validate every
        partition -> promote with a transactional guard that records
        every promoted path so partial failures can be rolled back.
        """
        paths = ctx.paths
        base_dir = paths.data_processed / _DATASET_NAME
        staging_dir = paths.data_processed / "_staging" / _DATASET_NAME
        paths.ensure(staging_dir)

        collected = df.collect().with_columns(pl.col("ts_event").dt.year().alias("_year"))

        staged: list[tuple[Path, Path]] = []
        for (symbol, year), part_df in collected.group_by(["symbol", "_year"], maintain_order=True):
            part_out = part_df.drop("_year")
            part_dir_final = base_dir / f"symbol={symbol}" / f"year={year}"
            part_dir_stage = staging_dir / f"symbol={symbol}" / f"year={year}"
            part_dir_stage.mkdir(parents=True, exist_ok=True)
            sp = part_dir_stage / "part-0000.parquet"
            fp = part_dir_final / "part-0000.parquet"
            part_out.write_parquet(sp)
            staged.append((sp, fp))

        # Re-validate every staged file before any promotion.
        for sp, _fp in staged:
            try:
                VendorLegacy1minRollAdjustedSchema.validate(pl.read_parquet(sp))
            except Exception:
                for bad_sp, _bfp in staged:
                    bad_sp.unlink(missing_ok=True)
                _rmtree_empty(staging_dir)
                raise

        # Snapshot pre-promotion state of targets for rollback.
        pre_existing: dict[Path, bytes | None] = {}
        for _sp, fp in staged:
            pre_existing[fp] = fp.read_bytes() if fp.is_file() else None

        promoted: list[tuple[Path, Path]] = []
        try:
            for sp, fp in staged:
                fp.parent.mkdir(parents=True, exist_ok=True)
                sp.replace(fp)
                promoted.append((sp, fp))
        except Exception:
            # Roll back every successfully promoted partition to its
            # pre-existing content.
            for _sp, fp in promoted:
                prev = pre_existing.get(fp)
                if prev is None:
                    fp.unlink(missing_ok=True)
                else:
                    fp.write_bytes(prev)
            _rmtree_empty(staging_dir)
            raise
        finally:
            _rmtree_empty(staging_dir)

        _log.info("Wrote %d adjusted partitions to %s", len(promoted), base_dir)
        return base_dir

    # ------------------------------------------------------------------
    # emit_provenance
    # ------------------------------------------------------------------

    def emit_provenance(
        self,
        ctx: RunContext,
        source_paths: list[Path],
        output_path: Path,
    ) -> Path:
        """Write atomic provenance JSON (tempfile + os.replace + fsync)
        with full roll-event / contract-factor audit detail and the
        point-in-time caveat flag for level-based use.
        """
        prov_dir = ctx.paths.data_processed / "_provenance"
        ctx.paths.ensure(prov_dir)

        # Keys match scripts/ingest.py::_source_unchanged contract.
        # portable_key: repo-relative / ~-relative — committed provenance
        # must not embed the OS username (identity hygiene, audit L).
        per_file_checksums = {
            portable_key(sp, ctx.paths.root): file_sha256(sp) for sp in source_paths if sp.is_file()
        }

        if source_paths:
            source_frame = (
                pl.concat([pl.scan_parquet(sp) for sp in source_paths], how="vertical")
                .sort(["symbol", "contract_symbol", "ts_event"])
                .collect()
            )
            source_frame_sha = frame_sha256(
                source_frame, sort_cols=["symbol", "contract_symbol", "ts_event"]
            )
        else:
            source_frame_sha = ""

        # Compute output-frame SHA (post-roll-adjustment parquet).
        # This is distinct from source_frame_sha (pre-adjustment input).
        # emit_provenance is called after the output parquet is written,
        # so output_path/*.parquet exists and is readable here. Failure
        # is recorded explicitly (audit B: CODE-1-2/QUANT-1-10a) — the
        # input hash is NEVER substituted for the output hash, and the
        # failure is a WARNING + machine-readable error field, not a
        # silent empty string.
        output_frame_sha = ""
        output_frame_sha_error: str | None = None
        try:
            output_frame = (
                pl.scan_parquet(str(output_path / "**" / "*.parquet"))
                .sort(["symbol", "ts_event"])
                .collect()
            )
            output_frame_sha = frame_sha256(output_frame, sort_cols=["symbol", "ts_event"])
        except (OSError, pl.exceptions.PolarsError) as exc:
            output_frame_sha_error = f"{type(exc).__name__}: {exc}"
            _log.warning(
                "Output-frame SHA256 could not be computed from %s: %s "
                "(provenance will carry output_frame_sha256_error; the "
                "input hash is NOT substituted).",
                output_path,
                output_frame_sha_error,
            )

        if hasattr(ctx, "add_dataset_checksum") and output_frame_sha:
            ctx.add_dataset_checksum(self.name, output_frame_sha)

        # Serialize the per-symbol run summary captured during adjust().
        summary_serializable: dict[str, dict[str, Any]] = {}
        for sym, summary in self._last_run_summary.items():
            summary_serializable[sym] = {
                "window_days": summary.get("window_days"),
                "roll_codes": summary.get("roll_codes", []),
                "rolls": [
                    {
                        "roll_date": rr.event.roll_date.isoformat(),
                        "old_contract": rr.event.old_contract,
                        "new_contract": rr.event.new_contract,
                        "t_old_close_utc": rr.t_old_close_utc.isoformat(),
                        "t_new_open_utc": rr.t_new_open_utc.isoformat(),
                        "old_close": rr.old_close,
                        "new_open": rr.new_open,
                        "ratio": rr.ratio,
                    }
                    for rr in summary.get("rolls", [])
                ],
                "contract_factors": summary.get("contract_factors", {}),
                "bars_dropped_non_front": summary.get("bars_dropped_non_front", 0),
                "rejected_oscillations": summary.get("rejected_oscillations", []),
                "final_front_contract_id_full": summary.get("final_front_contract_id_full"),
                "last_session_date": (
                    summary["last_session_date"].isoformat()
                    if summary.get("last_session_date")
                    else None
                ),
            }

        payload = {
            "dataset": self.name,
            "version": self.version,
            "ported_from": (
                "SKIE-Universe 1.0 src/skie_ninja/data/ingest/"
                "vendor_legacy_1min_roll_adjusted.py v0.4.0 (ADR-0011 "
                "Decision 2 re-materialization; benchmark cross-validation "
                "in docs/audits/)"
            ),
            "source_dataset": self._source_dataset,
            "source_dataset_frame_sha256": source_frame_sha,
            "method": "ratio_adjustment_volume_crossover_persistence",
            "method_reference": (
                "Roll events + anchor bars: de Prado 2018 AFML ch.2 §2.4.3 "
                "(Single Future Roll; AFML's own Snippet 2.2 rollGaps is "
                "ADDITIVE). Multiplicative/relative adjustment: mlfinlab "
                "get_futures_roll_series(method='relative'). Supplementary "
                "Chan 2013 ch.2-3; Carver 2023 'Advanced Futures Trading "
                "Strategies' (back-adjusted futures series). OHLC scalar "
                "extension + unadjusted volume follow the Norgate "
                "continuous-futures / CSI Unfair Advantage 'Back-Adjusted "
                "Contracts' operational convention (vendors' default "
                "arithmetic is difference-based; only the OHLC/volume "
                "convention is borrowed)."
            ),
            "tier": "evidence_bar",
            # Discriminate evidence-bar tier by feature kind (1.0 round-2
            # finding F-2-5): a single boolean was too permissive — a
            # consumer reading only `evidence_bar_eligible` could
            # silently use non-PIT levels in walk-forward CV.
            # Round-1 2.0 audit (QUANT-1-1 + QUANT-1-2): returns
            # eligibility is downgraded to CONDITIONAL — see
            # evidence_bar_eligibility_conditions.
            "evidence_bar_eligible_returns": "conditional",
            "evidence_bar_eligible_levels": False,
            # Legacy single-boolean key retained for backward
            # compatibility with any consumer written against the
            # 1.0 v0.1.0 provenance shape. Semantics = returns-only,
            # now conditional (see conditions).
            "evidence_bar_eligible": "conditional",
            "evidence_bar_eligibility_conditions": [
                {
                    "id": "DEC_ROLL_LATE_COMMIT",
                    "requirement": (
                        "Consumers must treat late-December/early-January "
                        "windows listed in coverage_gaps as carrying a "
                        "misattributed front-month (roll detected ~3 weeks "
                        "late due to per-year raw-file sharding). Evidence "
                        "over those windows is not confirmation-grade until "
                        "the re-pull follow-up "
                        "P1-2.0-DATABENTO-DEC-ROLL-REPULL lands (operator "
                        "authorization required for Databento spend)."
                    ),
                },
                {
                    "id": "PIT_PROVISIONAL_BARS",
                    "requirement": (
                        "Bars with pit_provisional=true carry a front-month "
                        "label decided with up to window_days-1 future "
                        "sessions (persistence-guard retroactive relabel). "
                        "The ADR-0008 PIT canary suite and all walk-forward "
                        "folds must exclude flagged bars or re-resolve them "
                        "causally."
                    ),
                },
            ],
            "level_use_pit_safe": False,
            "level_use_pit_safe_note": (
                "Adjusted level columns (open/high/low/close) are "
                "retrospectively rescaled by the full-sample roll "
                "history. Walk-forward consumers using level-based "
                "features must re-materialize this derivative within "
                "each training fold, or restrict to return-based "
                "transforms. Return-based features ARE PIT-safe on "
                "this derivative. Tracked as P1-LEVEL-USE-POLICY."
            ),
            "roll_adjustment": "multiplicative ratio (cumulative back-adjust)",
            "anchor_rule": (
                "Anchor bars per the AFML §2.4.3 roll-event definition; "
                "ratio rho = new_open(t_first_new) / old_close(t_last_old) "
                "per mlfinlab get_futures_roll_series(method='relative') — "
                "AFML's own text forms the additive gap instead. No "
                "synchronous-overlap or post-roll fallback."
            ),
            "persistence_window_source": "config/instruments.yaml roll_rule.window_days",
            "known_verification_gaps": {
                "volume_vs_oi_crossover": (
                    "No peer-reviewed empirical comparison of volume- vs "
                    "OI-crossover realized-slippage for CME equity-index "
                    "futures is known as of 2026-04-23. Practitioner "
                    "convention used. Follow-up P1-ROLL-METHOD."
                ),
                "anchor_sensitivity": (
                    "No empirical comparison of close-to-open vs "
                    "synchronous-overlap vs exchange-settlement anchor. "
                    "Follow-up P1-ROLL-ANCHOR."
                ),
            },
            # Machine-readable substrate-defect record (round-1 audit
            # QUANT-1-1, critical): December Z->H rolls commit ~3 weeks
            # late because per-year vendor raw files contain only
            # same-year-expiry contracts. Registered on the upstream
            # entry in config/data_sources.yaml (substrate_defects) and
            # detected here per run from the committed roll events.
            "coverage_gaps": _detect_dec_roll_coverage_gaps(summary_serializable),
            "pit_provisional_note": (
                "Output column pit_provisional=true marks bars whose "
                "effective front-month label was resolved by the "
                "persistence guard using up to window_days-1 FUTURE "
                "sessions (retroactive relabel over [challenger_start, "
                "resolution)). See module docstring 'Point-in-time flag'."
            ),
            "timestamp_utc": datetime.now(tz=UTC).isoformat(),
            "source_checksums": per_file_checksums,
            "output_path": portable_key(output_path, ctx.paths.root),
            "run_id": ctx.log.run_id if ctx.log else None,
            "repro_log": ctx.log.to_dict() if ctx.log else None,
            "run_summary": summary_serializable,
            "output_frame_sha256": output_frame_sha,
            "output_frame_sha256_error": output_frame_sha_error,
            "output_frame_sha256_note": (
                "SHA256 of roll-adjusted output parquet, computed via "
                "frame_sha256(sort_cols=[symbol,ts_event]) at provenance "
                "write time. Distinct from source_dataset_frame_sha256 "
                "(pre-roll-adjusted input hash). Empty string + non-null "
                "output_frame_sha256_error means the hash could not be "
                "computed; the input hash is never substituted."
            ),
        }

        date_str = datetime.now(tz=UTC).strftime("%Y%m%d")
        prov_path = prov_dir / f"{self.name}_{date_str}.json"
        _atomic_write_json(prov_path, payload)
        _log.info("Wrote provenance: %s", prov_path)
        return prov_path


# ---------------------------------------------------------------------------
# Core algorithm helpers (module-level, unit-testable)
# ---------------------------------------------------------------------------


def _expiry_year_expr(sym_col: str, ts_col: str = "ts_event") -> pl.Expr:
    """Polars expression deriving a contract's 4-digit EXPIRY year from
    its code's trailing year digits + the bar's calendar year.

    Round-2 audit remediation (QUANT-2-1, critical): keying contracts by
    the BAR calendar year split any physical contract whose bars
    straddle a year boundary (e.g. MCLG6 trading Dec-2025 -> Jan-2026)
    into two synthetic keys, fabricating a roll whose "ratio" was the
    contract's own year-boundary overnight return. The expiry year is a
    property of the physical contract, so every bar of one contract
    maps to one key regardless of which calendar years it trades in.

    Derivation: let ``d`` be the trailing year digits of the code
    (1 digit for this substrate, e.g. ``ESH5`` -> 5; the expression is
    generic over k digits with modulus m = 10^k), and ``y`` the bar's
    calendar year. A contract's bars can never postdate its expiry
    year (trading stops at expiry) but may precede it by up to m-1
    years, so the expiry year is the SMALLEST year >= y congruent to
    d (mod m):

        expiry_year = y + ((d - y) mod m)

    Examples: MCLG6 bar in 2025 -> 2026; MCLG6 bar in 2026 -> 2026
    (one key); ESH5 bar in 2015 -> 2015 and ESH5 bar in 2025 -> 2025
    (decade wraparound still disambiguated); ESH7 bar in 2026 ->
    2027 (forward-traded March-2027 contract).
    """
    digits = pl.col(sym_col).str.extract(r"(\d+)$", 1)
    d = digits.cast(pl.Int64)
    # Modulus 10^k where k = number of trailing year digits (1 on this
    # substrate; generic for 2-digit codes like NQZ24).
    m = pl.lit(10, dtype=pl.Int64).pow(digits.str.len_chars().cast(pl.Int64)).cast(pl.Int64)
    y = pl.col(ts_col).dt.year().cast(pl.Int64)
    # Double-mod: polars integer % follows the dividend's sign, so a
    # single mod of the (usually negative) difference would be negative.
    return y + (((d - y) % m) + m) % m


def _contract_id_full_expr() -> pl.Expr:
    """Polars expression deriving ``contract_id_full`` from
    ``contract_symbol`` + the contract's EXPIRY year.

    Single-digit year suffixes in CME contract codes (``ESH5`` ->
    March-2015 OR March-2025) collide on substrates that span >=10
    calendar years; disambiguation appends the 4-digit expiry year
    (see :func:`_expiry_year_expr`). Keying by expiry year (round-2
    audit QUANT-2-1; previously bar calendar year) makes the key a
    property of the physical contract, so contracts legitimately
    trading across a calendar year boundary — routine for monthly-roll
    instruments (MCL/MGC/SIL) and for ES/NQ once December-spanning raw
    data lands via P1-2.0-DATABENTO-DEC-ROLL-REPULL — map to a single
    key instead of being split into a fabricated roll. The derivation
    is guarded by ``_assert_no_consecutive_year_collision`` for all
    instruments.
    """
    return (
        pl.col("contract_symbol")
        + pl.lit("_")
        + _expiry_year_expr("contract_symbol").cast(pl.Utf8).str.zfill(4)
    )


def _extract_month_code(contract_symbol: str) -> str | None:
    """Extract the 1-letter CME month code from a contract symbol.

    The CME convention is ``<root><month><year>`` where ``<month>`` is
    a 1-letter code from ``_CME_MONTH_CODES`` and ``<year>`` is one or
    more trailing digits. Examples:

      - ``ESH5`` -> ``H`` (root=ES, month=H Mar, year=5)
      - ``NQZ24`` -> ``Z`` (root=NQ, month=Z Dec, year=24)
      - ``MCLF5`` -> ``F`` (root=MCL, month=F Jan, year=5)
      - ``MGCG25`` -> ``G`` (root=MGC, month=G Feb, year=25)

    Returns the month-code letter, or ``None`` if the symbol does not
    match the canonical ``<root><month><year-digits>`` shape. We
    locate ``<month>`` as the rightmost alphabetic character whose
    immediate right context is one-or-more digits and whose left
    context is at least one alphabetic character (the root prefix).
    This is robust to variable-length roots (2-char ES/NQ; 3-char
    MES/MNQ/MCL/MGC/SIL) and to 1- vs 2-digit year suffixes.
    """
    s = contract_symbol.strip()
    if len(s) < _MIN_CONTRACT_SYMBOL_LENGTH:
        return None
    # Find the boundary between the trailing year-digits and the
    # preceding alphabetic prefix. The month code is the last
    # alphabetic char of that prefix.
    i = len(s)
    while i > 0 and s[i - 1].isdigit():
        i -= 1
    if i == len(s) or i == 0:
        # No trailing digits (i==len) or no leading alphabetic prefix
        # (i==0). Either way, not a recognizable contract code.
        return None
    code = s[i - 1]
    if code not in _CME_MONTH_CODES:
        return None
    # Require at least one alphabetic char before the month code (the
    # product root prefix). Otherwise ``H5`` alone would parse as
    # month=H year=5 without a root, which is not a vendor symbol.
    if i - 1 == 0:
        return None
    return code


def _assert_roll_codes_subset(df: pl.DataFrame, symbol: str, allowed_codes: frozenset[str]) -> None:
    """Verify every observed ``contract_symbol`` carries a month code
    that is a member of ``allowed_codes``.

    The volume-driven front-month detection algorithm is itself
    code-agnostic (it argmaxes over whatever ``contract_symbol`` keys
    appear in the data). This guard is *defensive*: it surfaces a
    controlled ``ValueError`` when the data contains a contract whose
    month code is not in the configured ``roll_rule.codes`` set. Two
    failure modes it catches:

      1. Upstream data corruption (e.g., a stray equity-index symbol
         leaking into an energy ingest partition).
      2. Mis-configuration of ``roll_rule.codes`` (e.g., MGC declares
         only the gold metals subset G/J/M/Q/V/Z but the substrate
         carries an odd-month code that should have been ingested as
         a separate instrument).

    A contract symbol whose shape does not match the canonical
    ``<root><month><year-digits>`` pattern is reported separately
    (parse failure) rather than silently skipped.
    """
    observed = df["contract_symbol"].unique().to_list()
    parse_failures: list[str] = []
    out_of_set: dict[str, str] = {}
    for sym in observed:
        if sym is None:
            continue
        code = _extract_month_code(sym)
        if code is None:
            parse_failures.append(sym)
            continue
        if code not in allowed_codes:
            out_of_set[sym] = code
    if parse_failures:
        cap = _ROLL_CODES_ERROR_MAX_EXAMPLES
        suffix = "..." if len(parse_failures) > cap else ""
        raise ValueError(
            f"Symbol {symbol}: {len(parse_failures)} contract_symbol "
            f"value(s) do not match the CME "
            f"<root><month-code><year-digits> pattern: "
            f"{parse_failures[:cap]}{suffix}."
        )
    if out_of_set:
        cap = _ROLL_CODES_ERROR_MAX_EXAMPLES
        raise ValueError(
            f"Symbol {symbol}: {len(out_of_set)} contract_symbol "
            f"value(s) carry a month code outside the configured "
            f"roll_rule.codes set {sorted(allowed_codes)}. Examples: "
            f"{list(out_of_set.items())[:cap]}."
        )


def _assert_no_consecutive_year_collision(df: pl.DataFrame, symbol: str) -> None:
    """Guard on the expiry-year derivation: for each ``contract_symbol``,
    all DERIVED expiry years must be >=
    ``_CME_CONTRACT_CODE_RECURRENCE_YEARS`` apart.

    Round-2 audit re-target (QUANT-2-1): the pre-remediation version
    asserted on BAR calendar years, which (a) false-positived on
    physical contracts legitimately straddling a year boundary and (b)
    was therefore skipped for the monthly-roll instruments — exactly
    where straddling occurs. With expiry-year keying
    (:func:`_expiry_year_expr`), a straddling contract's bars all map
    to ONE expiry year, so this guard never fires on legitimate
    spanning and now runs for ALL instruments. Two derived expiry
    years for the same 1-digit code differ by multiples of 10 by
    construction; any smaller gap therefore indicates a derivation
    bug or corrupted contract symbology and is surfaced as a
    controlled ``ValueError`` rather than being silently
    ratio-adjusted.
    """
    by_contract = (
        df.with_columns(_expiry_year_expr("contract_symbol").alias("_expiry_year"))
        .group_by("contract_symbol")
        .agg(pl.col("_expiry_year").unique().sort().alias("_expiry_years"))
    )
    offenders: list[dict[str, Any]] = []
    for row in by_contract.iter_rows(named=True):
        years = row["_expiry_years"]
        if not years:
            continue
        for prev_year, next_year in zip(years[:-1], years[1:], strict=True):
            if next_year - prev_year < _CME_CONTRACT_CODE_RECURRENCE_YEARS:
                offenders.append(
                    {
                        "contract_symbol": row["contract_symbol"],
                        "prev_expiry_year": prev_year,
                        "next_expiry_year": next_year,
                        "gap_years": next_year - prev_year,
                    }
                )
                break
    if offenders:
        raise ValueError(
            f"Symbol {symbol}: found {len(offenders)} contract_symbol "
            f"value(s) whose DERIVED expiry years are closer than "
            f"{_CME_CONTRACT_CODE_RECURRENCE_YEARS} years; expiry years "
            f"for one code recur only every 10 years, so this indicates a "
            f"derivation bug or corrupted symbology. "
            f"Offenders: {offenders[:5]}"
        )


def _session_date_expr() -> pl.Expr:
    """Polars expression mapping a UTC ``ts_event`` to CME session date.

    Delegates to :func:`skie_universe2.utils.sessions.cme_session_date_expr`
    (shared with the shadow-ledger writer per round-1 audit QUANT-1-6);
    see that module for the rule and its limitations. Name kept for
    port fidelity with the 1.0 module namespace.
    """
    return cme_session_date_expr("ts_event")


def detect_raw_front_month_by_day(df: pl.DataFrame, window_days: int) -> pl.DataFrame:
    """Per ``(symbol, session_date)``, identify the front-month contract
    as ``argmax_{contract_id_full}(trailing_window_days_cumulative_volume)``.

    Uses a trailing rolling sum of daily volume over ``window_days``
    sessions per ``contract_id_full``, then ``argmax`` across
    contract_id_full values per session. Ties broken deterministically
    (higher cumulative volume first, then lexicographically-earliest
    contract_id_full).

    Input must already carry ``contract_id_full`` (derived once in
    ``_adjust_one_symbol`` to avoid the decade-wraparound collision on
    1-digit year suffixes; see module docstring).

    Returns a frame with columns
    ``(symbol, session_date, front_contract_id_full, cumulative_volume)``.
    """
    if window_days < 1:
        raise ValueError(f"window_days must be >= 1, got {window_days}.")

    # Production path supplies contract_id_full pre-computed (decade-
    # disambiguated). Synthetic single-decade fixtures pass only
    # contract_symbol; preserve the legacy column-name contract for
    # those callers so existing tests remain meaningful.
    has_full = "contract_id_full" in df.columns
    key_in = "contract_id_full" if has_full else "contract_symbol"
    key_out = "front_contract_id_full" if has_full else "front_contract_symbol"

    daily = (
        df.with_columns(_session_date_expr().alias("session_date"))
        .group_by(["symbol", "session_date", key_in], maintain_order=True)
        .agg(pl.col("volume").sum().alias("daily_volume"))
        .sort(["symbol", key_in, "session_date"])
    )
    # Cumulative (trailing-window) volume per (symbol, key_in).
    cum = daily.with_columns(
        pl.col("daily_volume")
        # justify: min_samples=1 lets the trailing sum emit from a contract's
        # first session (short early history is real volume, not missingness);
        # verbatim from the 1.0 reference implementation.
        .rolling_sum(window_size=window_days, min_samples=1)
        .over(["symbol", key_in])
        .alias("cum_volume")
    )

    # argmax per (symbol, session_date) with explicit tie-break.
    winners = (
        cum.sort(
            ["symbol", "session_date", "cum_volume", key_in],
            descending=[False, False, True, False],
        )
        .group_by(["symbol", "session_date"], maintain_order=True)
        .agg(
            pl.col(key_in).first().alias(key_out),
            pl.col("cum_volume").first().alias("cumulative_volume"),
        )
    )
    return winners.sort(["symbol", "session_date"])


def apply_persistence_guard(  # noqa: PLR0912 — verbatim 1.0 port; restructuring the state machine would risk numerical-fidelity drift
    raw_front: pl.DataFrame, window_days: int
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    """Require a new front-month candidate to lead for ``window_days``
    consecutive sessions before committing the roll.

    Returns ``(effective_front_month, rejected_oscillations)`` where
    ``effective_front_month`` carries the committed per-session front
    contract and ``rejected_oscillations`` lists transitions that did
    not persist (for provenance).

    The effective frame also carries ``pit_provisional`` (bool, 2.0
    addition per round-1 audit QUANT-1-2, extended per round-2 audit
    QUANT-2-4): True for every session inside a challenger window —
    ``[challenger_start, commit]`` INCLUSIVE for committed rolls (the
    commit-session label uses that session's own full-session volume,
    so it is decidable only at session close), and
    ``[challenger_start, rejection)`` for rejected oscillations. The
    label values themselves are unchanged from the 1.0 algorithm; the
    flag is metadata for downstream PIT enforcement (ADR-0008
    Decision 1).

    Implementation: iterate per symbol in chronological order; track
    the incumbent and a pending challenger. A challenger becomes
    incumbent only after leading for ``window_days`` consecutive
    sessions.
    """
    if window_days < 1:
        raise ValueError(f"window_days must be >= 1, got {window_days}.")

    records: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    # Auto-detect the front-month column for back-compat with synthetic
    # raw_front frames that pass ``front_contract_symbol`` directly
    # (the disambiguation only matters when collisions are possible —
    # synthetic test fixtures with one decade are isomorphic).
    front_col = (
        "front_contract_id_full"
        if "front_contract_id_full" in raw_front.columns
        else "front_contract_symbol"
    )
    eff_col = (
        "effective_front_contract_id_full"
        if front_col == "front_contract_id_full"
        else "effective_front_contract_symbol"
    )
    raw_eff_col = (
        "raw_front_contract_id_full"
        if front_col == "front_contract_id_full"
        else "raw_front_contract_symbol"
    )

    for sym in sorted(raw_front["symbol"].unique(maintain_order=True).to_list()):
        sym_rows = raw_front.filter(pl.col("symbol") == sym).sort("session_date")
        incumbent: str | None = None
        challenger: str | None = None
        challenger_streak = 0
        challenger_start: date | None = None

        for row in sym_rows.iter_rows(named=True):
            raw = row[front_col]
            committed_now = False

            if incumbent is None:
                # Seed: the first session's raw winner is the incumbent
                # without needing persistence (there is no prior
                # contract to have been persisting).
                incumbent = raw
            elif raw == incumbent:
                # Challenger resets if the incumbent re-takes.
                if challenger is not None:
                    rejected.append(
                        {
                            "symbol": sym,
                            "start_date": challenger_start.isoformat()
                            if challenger_start
                            else None,
                            "end_date": row["session_date"].isoformat(),
                            "challenger": challenger,
                            "incumbent": incumbent,
                            "streak_reached": challenger_streak,
                            "window_required": window_days,
                        }
                    )
                challenger = None
                challenger_streak = 0
                challenger_start = None
            else:
                # raw != incumbent
                if raw != challenger:
                    # Reset challenger.
                    if challenger is not None:
                        rejected.append(
                            {
                                "symbol": sym,
                                "start_date": challenger_start.isoformat()
                                if challenger_start
                                else None,
                                "end_date": row["session_date"].isoformat(),
                                "challenger": challenger,
                                "incumbent": incumbent,
                                "streak_reached": challenger_streak,
                                "window_required": window_days,
                            }
                        )
                    challenger = raw
                    challenger_streak = 1
                    challenger_start = row["session_date"]
                else:
                    challenger_streak += 1

                if challenger_streak >= window_days:
                    # Commit the roll: the challenger becomes the
                    # incumbent effective at challenger_start (first
                    # session the challenger led).
                    # Rewrite prior sessions since challenger_start.
                    assert challenger_start is not None  # narrows type
                    for rec in records[::-1]:
                        if rec["symbol"] != sym:
                            continue
                        if rec["session_date"] < challenger_start:
                            break
                        rec[eff_col] = challenger
                    incumbent = challenger
                    challenger = None
                    challenger_streak = 0
                    challenger_start = None
                    committed_now = True

            records.append(
                {
                    "symbol": sym,
                    "session_date": row["session_date"],
                    eff_col: incumbent,
                    raw_eff_col: raw,
                    # PIT flag (QUANT-1-2; commit-session extension per
                    # round-2 audit QUANT-2-4): True over
                    # [challenger_start, commit] INCLUSIVE plus rejected
                    # challenger windows. A live challenger means this
                    # session's effective label is pending resolution by
                    # future sessions; the COMMIT session's label
                    # (challenger, not the causal incumbent-persists
                    # default) is itself decided using the commit
                    # session's own full-session volume — decidable only
                    # at session close, not at any bar within it — so it
                    # is flagged too. Records rewritten at commit time
                    # were appended while the challenger was live and
                    # already carry True.
                    "pit_provisional": (challenger is not None) or committed_now,
                }
            )

    if not records:
        effective = pl.DataFrame(
            schema={
                "symbol": pl.Utf8,
                "session_date": pl.Date,
                eff_col: pl.Utf8,
                raw_eff_col: pl.Utf8,
                "pit_provisional": pl.Boolean,
            }
        )
    else:
        effective = pl.DataFrame(records).sort(["symbol", "session_date"])

    return effective, rejected


def detect_roll_events(effective_front: pl.DataFrame) -> list[RollEvent]:
    """Identify committed roll events from the effective (post-persistence)
    front-month series.

    Auto-detects the effective-front column: prefers the disambiguated
    ``effective_front_contract_id_full`` (the production path through
    ``_adjust_one_symbol``) and falls back to
    ``effective_front_contract_symbol`` for synthetic test fixtures.
    The returned ``RollEvent.old_contract`` / ``new_contract`` carry
    the same key family as the input (i.e. ``contract_id_full`` for
    production, raw ``contract_symbol`` for tests).
    """
    events: list[RollEvent] = []
    if effective_front.height == 0:
        return events
    eff_col = (
        "effective_front_contract_id_full"
        if "effective_front_contract_id_full" in effective_front.columns
        else "effective_front_contract_symbol"
    )
    for sym in sorted(effective_front["symbol"].unique(maintain_order=True).to_list()):
        sym_rows = effective_front.filter(pl.col("symbol") == sym).sort("session_date")
        prev_contract: str | None = None
        for row in sym_rows.iter_rows(named=True):
            current = row[eff_col]
            if prev_contract is not None and current != prev_contract:
                events.append(
                    RollEvent(
                        roll_date=row["session_date"],
                        old_contract=prev_contract,
                        new_contract=current,
                    )
                )
            prev_contract = current
    return events


def compute_roll_ratio_afml(
    df: pl.DataFrame,
    event: RollEvent,
    symbol: str,
    effective_front: pl.DataFrame,
) -> RollRatio:
    """AFML §2.4.3 anchor: rho = new_open(t_first_new) / old_close(t_last_old).

    ``t_last_old`` = last 1-min bar of ``old`` on its last session as
    effective front-month (= session immediately before ``event.roll_date``).
    ``t_first_new`` = first 1-min bar of ``new`` on its first session as
    effective front-month (= ``event.roll_date``).

    Auto-detects whether ``effective_front`` and ``df`` carry the
    disambiguated ``contract_id_full`` (production path) or the raw
    ``contract_symbol`` (legacy/synthetic). The ``RollEvent`` keys
    must agree with the input's key family.

    Raises ``NoOverlapError`` if either anchor bar is missing.
    """
    has_full = (
        "effective_front_contract_id_full" in effective_front.columns
        and "contract_id_full" in df.columns
    )
    eff_col = "effective_front_contract_id_full" if has_full else "effective_front_contract_symbol"
    df_key_col = "contract_id_full" if has_full else "contract_symbol"

    # Find the old contract's last-as-effective-front session date.
    old_sessions = effective_front.filter(
        (pl.col("symbol") == symbol) & (pl.col(eff_col) == event.old_contract)
    )["session_date"].sort()
    if old_sessions.len() == 0:
        raise NoOverlapError(
            f"Roll {symbol} {event.old_contract}->{event.new_contract}: "
            f"old contract never held effective-front status."
        )
    old_last_session = old_sessions.to_list()[-1]

    old_bars = df.filter(
        (pl.col("symbol") == symbol)
        & (pl.col(df_key_col) == event.old_contract)
        & (_session_date_expr() == old_last_session)
    ).sort("ts_event")
    if old_bars.height == 0:
        raise NoOverlapError(
            f"Roll {symbol} {event.old_contract}->{event.new_contract} "
            f"on {event.roll_date}: no bar for old contract on "
            f"{old_last_session} (its last-as-front session)."
        )
    old_last = old_bars.tail(1).to_dicts()[0]

    new_bars = df.filter(
        (pl.col("symbol") == symbol)
        & (pl.col(df_key_col) == event.new_contract)
        & (_session_date_expr() == event.roll_date)
    ).sort("ts_event")
    if new_bars.height == 0:
        raise NoOverlapError(
            f"Roll {symbol} {event.old_contract}->{event.new_contract} "
            f"on {event.roll_date}: no bar for new contract on its "
            f"first-as-front session."
        )
    new_first = new_bars.head(1).to_dicts()[0]

    old_close = float(old_last["close"])
    new_open = float(new_first["open"])
    ratio = new_open / old_close

    return RollRatio(
        event=event,
        t_old_close_utc=old_last["ts_event"],
        t_new_open_utc=new_first["ts_event"],
        old_close=old_close,
        new_open=new_open,
        ratio=ratio,
    )


def _adjust_one_symbol(  # noqa: PLR0912 — verbatim 1.0 port; see apply_persistence_guard
    sym_df: pl.DataFrame,
    symbol: str,
    window_days: int,
    roll_codes: frozenset[str] | None = None,
) -> tuple[pl.DataFrame, dict[str, Any]]:
    """Full roll-adjustment pipeline for one root symbol.

    ``roll_codes`` is the per-instrument set of expected CME month
    codes (see ``_load_roll_codes``). When ``None``, defaults to the
    equity-index quarterly set H/M/U/Z, preserving backward
    compatibility for the 1.0 v0.1.0-v0.3.0 ES/NQ/MES/MNQ callers that
    pre-date this parameterization. Used only by
    ``_assert_roll_codes_subset`` as a defensive validation; the
    volume-driven front-month detection itself is code-agnostic.

    Returns ``(adjusted_frame, summary_dict)`` where ``summary_dict``
    carries rolls / contract-factors / rejected-oscillations / bars
    dropped — consumed by ``emit_provenance`` for audit traceability.
    """
    if roll_codes is None:
        roll_codes = _DEFAULT_EQUITY_INDEX_ROLL_CODES
    summary: dict[str, Any] = {
        "window_days": window_days,
        "roll_codes": sorted(roll_codes),
        "rolls": [],
        "contract_factors": {},
        "bars_dropped_non_front": 0,
        "rejected_oscillations": [],
    }
    if sym_df.height == 0:
        return _empty_adjusted_frame(), summary

    # Defensive: every observed contract_symbol's month code must lie
    # in the configured roll_codes set. Catches upstream data
    # corruption and roll_rule.codes mis-configuration.
    _assert_roll_codes_subset(sym_df, symbol, roll_codes)

    # Decade-wraparound disambiguation: derive contract_id_full once
    # and propagate it as the pipeline key so two contracts that share
    # a 1-digit-year-suffix code across decades (e.g. ESH5 March-2015
    # vs ESH5 March-2025) cannot collide in any downstream dictionary
    # or groupby. The raw contract_symbol is preserved for output as
    # front_contract_symbol. Round-2 audit QUANT-2-1 (critical): the
    # key appends the contract's EXPIRY year (_expiry_year_expr), NOT
    # the bar calendar year — a physical contract legitimately trading
    # across a year boundary (routine for monthly-roll MCL/MGC/SIL,
    # e.g. MCLG6 trading Dec-2025 -> Jan-2026, and for ES/NQ once the
    # December re-pull P1-2.0-DATABENTO-DEC-ROLL-REPULL lands) maps to
    # ONE key. Bar-year keying split such a contract in two and
    # fabricated a roll whose ratio equaled the contract's own
    # year-boundary overnight return. The derivation guard runs for
    # ALL instruments (it cannot false-positive on legitimate
    # spanning; see _assert_no_consecutive_year_collision).
    _assert_no_consecutive_year_collision(sym_df, symbol)
    sym_df = sym_df.with_columns(_contract_id_full_expr().alias("contract_id_full"))

    raw_front = detect_raw_front_month_by_day(sym_df, window_days)
    effective_front, rejected = apply_persistence_guard(raw_front, window_days)
    summary["rejected_oscillations"] = rejected

    events = detect_roll_events(effective_front)
    ratios: list[RollRatio] = [
        compute_roll_ratio_afml(sym_df, ev, symbol, effective_front) for ev in events
    ]
    summary["rolls"] = ratios

    # Chain-continuity assertion: event_{k}.new == event_{k+1}.old.
    for k in range(len(ratios) - 1):
        nk = ratios[k].event.new_contract
        ok = ratios[k + 1].event.old_contract
        if nk != ok:
            raise ValueError(
                f"Roll-chain discontinuity for symbol {symbol} at "
                f"event index {k}: event[{k}].new={nk!r} != "
                f"event[{k+1}].old={ok!r}."
            )

    # Derive newest contract_id_full from the effective front-month
    # series (the last session's effective front). Assert consistency
    # with the last roll event (if any).
    last_effective = effective_front.filter(pl.col("symbol") == symbol).sort("session_date").tail(1)
    if last_effective.height == 0:
        # No effective front-month data (single-contract with no rolls
        # and empty guard output). Fall back to raw-front's last session.
        last_row = raw_front.filter(pl.col("symbol") == symbol).tail(1)
        newest = last_row["front_contract_id_full"][0] if last_row.height else None
    else:
        newest = last_effective["effective_front_contract_id_full"][0]
    if ratios and newest is not None and newest != ratios[-1].event.new_contract:
        raise ValueError(
            f"Newest-contract inconsistency for symbol {symbol}: "
            f"effective-front last session = {newest!r}, "
            f"but ratios[-1].new_contract = {ratios[-1].event.new_contract!r}."
        )

    # Terminal-coverage audit inputs (round-2 audit QUANT-2-2a): the
    # coverage-gap detector needs the final front-month and the last
    # session in sample to flag a Z contract still front at
    # end-of-sample with no successor roll.
    summary["final_front_contract_id_full"] = newest
    summary["last_session_date"] = (
        last_effective["session_date"][0] if last_effective.height else None
    )

    # Cumulative multiplicative factors keyed by contract_id_full
    # (decade-disambiguated). The newest contract_id_full anchors at
    # 1.0 (back-adjustment convention: the current contract trades at
    # its raw price); older contracts walk backward through the
    # ordered roll chain accumulating rho_k. With the disambiguated
    # key, no older contract can overwrite the anchor entry even when
    # its raw contract_symbol (1-digit year) collides with the
    # anchor's raw contract_symbol from another decade.
    contract_factor: dict[str, float] = {}
    if not ratios:
        only_contracts = (
            effective_front.filter(pl.col("symbol") == symbol)["effective_front_contract_id_full"]
            .unique(maintain_order=True)
            .to_list()
        )
        for c in only_contracts:
            contract_factor[c] = 1.0
    else:
        if newest is not None:
            contract_factor[newest] = 1.0
        cum = 1.0
        for rr in reversed(ratios):
            cum *= rr.ratio
            contract_factor[rr.event.old_contract] = cum
    summary["contract_factors"] = dict(contract_factor)

    # Front-month filter + factor attach + OHLC adjust. Join key is
    # contract_id_full (decade-disambiguated); the display
    # front_contract_symbol is the raw contract_symbol carried
    # through from sym_df.
    front_map = effective_front.filter(pl.col("symbol") == symbol).select(
        pl.col("session_date"),
        pl.col("effective_front_contract_id_full").alias("contract_id_full"),
        pl.col("pit_provisional"),
    )
    sym_with_date = sym_df.with_columns(_session_date_expr().alias("_session_date"))
    total_raw = sym_with_date.height
    front_only = sym_with_date.join(
        front_map,
        left_on=["_session_date", "contract_id_full"],
        right_on=["session_date", "contract_id_full"],
        how="inner",
    )
    summary["bars_dropped_non_front"] = total_raw - front_only.height

    factor_rows = pl.DataFrame(
        {
            "contract_id_full": list(contract_factor.keys()),
            "adjustment_factor": list(contract_factor.values()),
        }
    )
    enriched = front_only.join(factor_rows, on="contract_id_full", how="inner")

    first_session = enriched.group_by("contract_id_full", maintain_order=True).agg(
        pl.col("_session_date").min().alias("_first_session")
    )
    enriched = enriched.join(first_session, on="contract_id_full", how="inner")

    adjusted = enriched.with_columns(
        (pl.col("open") * pl.col("adjustment_factor")).alias("_open_adj"),
        (pl.col("high") * pl.col("adjustment_factor")).alias("_high_adj"),
        (pl.col("low") * pl.col("adjustment_factor")).alias("_low_adj"),
        (pl.col("close") * pl.col("adjustment_factor")).alias("_close_adj"),
        pl.col("close").alias("unadjusted_close"),
        (pl.col("_session_date") == pl.col("_first_session")).alias("roll_flag"),
        pl.col("contract_symbol").alias("front_contract_symbol"),
    ).select(
        pl.col("ts_event"),
        pl.col("_open_adj").alias("open"),
        pl.col("_high_adj").alias("high"),
        pl.col("_low_adj").alias("low"),
        pl.col("_close_adj").alias("close"),
        pl.col("volume"),
        pl.col("symbol"),
        pl.col("front_contract_symbol"),
        pl.col("adjustment_factor"),
        pl.col("unadjusted_close"),
        pl.col("roll_flag"),
        pl.col("pit_provisional"),
    )

    return adjusted.sort(["symbol", "ts_event"]), summary


def _detect_dec_roll_coverage_gaps(
    summary_serializable: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect the DEC_ROLL_LATE_COMMIT substrate defect per run.

    Round-1 audit QUANT-1-1 (critical): the per-year vendor raw files
    contain only same-year-expiry contracts, so the December
    volume-crossover into the next year's H (March) contract is
    invisible until the next year's file begins — the Z->H roll commits
    at the first January session, ~3 weeks late. Empirically confirmed
    on this substrate: every ES/NQ Z->H roll 2016-2025 committed on the
    first trading session of January.

    Repair requires re-pulling December-spanning raw data from
    Databento — operator-authorized spend, follow-up
    ``P1-2.0-DATABENTO-DEC-ROLL-REPULL`` (see config/data_sources.yaml
    substrate_defects). Do not silently re-adjust in code: the defect
    is in the raw substrate, and the 1.0 reference output shares it
    (bit-exactness != correctness).

    Round-2 audit rework (QUANT-2-2): (a) the committed-roll rule
    compares CONTRACT EXPIRY YEARS (from the ``contract_id_full``
    suffix, i.e. the QUANT-2-1 derivation) instead of the old
    ``code == 'H' and January`` heuristic — any roll into a
    later-expiry-year contract that only commits on or after Jan 01 of
    the new expiry year is late, regardless of month codes (robust to
    monthly-roll instruments); (b) a TERMINAL gap is emitted when the
    final in-sample front-month is a December-expiry (Z) contract and
    the sample extends into its expiry month with no successor roll —
    the successor's volume takeover is unobservable under the per-year
    sharding, so end-of-sample front-month attribution beyond the
    expected crossover is unverifiable. The Dec-01 terminal threshold
    is the start of the expiry month: the CME crossover lands ~8
    calendar days before the third-Friday LTD (~Dec 08-12), and a
    sample truncated anywhere inside the expiry month cannot confirm
    the takeover was captured, so the whole month is flagged
    conservatively.
    """
    gaps: list[dict[str, Any]] = []
    for sym, summary in summary_serializable.items():
        for roll in summary.get("rolls", []):
            old_expiry = _expiry_year_from_contract_id(str(roll["old_contract"]))
            new_expiry = _expiry_year_from_contract_id(str(roll["new_contract"]))
            if old_expiry is None or new_expiry is None:
                continue  # synthetic ids without an expiry suffix
            roll_year = int(str(roll["roll_date"])[:4])
            if new_expiry > old_expiry and roll_year >= new_expiry:
                gaps.append(
                    {
                        "defect_id": "DEC_ROLL_LATE_COMMIT",
                        "kind": "late_committed_roll",
                        "symbol": sym,
                        "old_contract": roll["old_contract"],
                        "new_contract": roll["new_contract"],
                        "committed_roll_date": roll["roll_date"],
                        "expected_crossover_window": (f"{old_expiry}-12-08 .. {roll['roll_date']}"),
                        "cause": (
                            "per-year raw files carry only same-year-expiry "
                            "contracts; the later-expiry-year contract is "
                            "absent until its first calendar year's file "
                            "begins"
                        ),
                        "repair_follow_up": "P1-2.0-DATABENTO-DEC-ROLL-REPULL",
                    }
                )
        # Terminal window (QUANT-2-2a): final front-month is a Z
        # (December-expiry) contract and the sample runs into its
        # expiry month with no successor roll recorded.
        final_front = summary.get("final_front_contract_id_full")
        last_sd = summary.get("last_session_date")
        if final_front and last_sd:
            last_sd_str = str(last_sd)
            display = str(final_front).split("_", 1)[0]
            code = _extract_month_code(display)
            expiry = _expiry_year_from_contract_id(str(final_front))
            if code == "Z" and expiry is not None and last_sd_str >= f"{expiry}-12-01":
                gaps.append(
                    {
                        "defect_id": "DEC_ROLL_LATE_COMMIT",
                        "kind": "terminal_window",
                        "symbol": sym,
                        "old_contract": final_front,
                        "new_contract": None,
                        "committed_roll_date": None,
                        "expected_crossover_window": (
                            f"{expiry}-12-08 .. (successor takeover unobserved; "
                            f"sample ends {last_sd_str})"
                        ),
                        "cause": (
                            "sample ends inside the final Z contract's expiry "
                            "month with no successor roll; the successor's "
                            "volume takeover is unobservable under per-year "
                            "raw sharding, so end-of-sample front-month "
                            "attribution past the expected crossover is "
                            "unverifiable"
                        ),
                        "repair_follow_up": "P1-2.0-DATABENTO-DEC-ROLL-REPULL",
                    }
                )
    return gaps


# Width of the zero-padded expiry-year suffix in contract_id_full
# ("{code}_{YYYY}"): 4 digits by the str.zfill(4) in
# _contract_id_full_expr — a format constant, not a tunable.
_CONTRACT_ID_YEAR_WIDTH = 4


def _expiry_year_from_contract_id(contract_id: str) -> int | None:
    """Parse the 4-digit expiry year from a ``contract_id_full``
    (``{code}_{YYYY}``); None for ids without the suffix (synthetic
    test fixtures that key on raw contract_symbol)."""
    _, sep, suffix = contract_id.partition("_")
    if sep and len(suffix) == _CONTRACT_ID_YEAR_WIDTH and suffix.isdigit():
        return int(suffix)
    return None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _empty_adjusted_frame() -> pl.DataFrame:
    return pl.DataFrame(
        schema={
            "ts_event": pl.Datetime("us", "UTC"),
            "open": pl.Float64,
            "high": pl.Float64,
            "low": pl.Float64,
            "close": pl.Float64,
            "volume": pl.Int64,
            "symbol": pl.Utf8,
            "front_contract_symbol": pl.Utf8,
            "adjustment_factor": pl.Float64,
            "unadjusted_close": pl.Float64,
            "roll_flag": pl.Boolean,
            "pit_provisional": pl.Boolean,
        }
    )


def _rmtree_empty(path: Path) -> None:
    if not path.is_dir():
        return
    for child in path.iterdir():
        if child.is_dir():
            _rmtree_empty(child)
    with contextlib.suppress(OSError):
        path.rmdir()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    """Atomic JSON write: tempfile in the same directory, fsync, os.replace."""
    payload_bytes = (
        json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n"
    ).encode("utf-8")
    with tempfile.NamedTemporaryFile(
        mode="wb",
        dir=str(path.parent),
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as tmp:
        tmp.write(payload_bytes)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_name = tmp.name
    os.replace(tmp_name, path)


def _json_default(obj: Any) -> Any:
    """json.dumps default: dataclass -> dict; date/datetime -> isoformat."""
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if hasattr(obj, "__dataclass_fields__"):
        return asdict(obj)
    raise TypeError(f"Not JSON-serializable: {type(obj).__name__}")


# Self-register at import time.
register(VendorLegacy1minRollAdjustedIngestJob())
