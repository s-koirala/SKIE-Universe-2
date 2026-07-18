"""Exit-code contract tests for the discovery-alpha reproduction check.

Covers the audit CODE-1-1 remediation: a CRASH inside the check maps to
EXIT_ERROR (2), never to EXIT_MISMATCH (1) — a crashed check must not read
as a reproduction finding. The full re-run path is exercised by executing
``scripts/audits/check_discovery_alpha_reproduction.py`` itself (2026-07-18:
exit 0, REPRODUCED); these tests only pin the failure-mode mapping, which
must never depend on running the heavy calibration.
"""

from __future__ import annotations

import pytest
import scripts.audits.check_discovery_alpha_reproduction as check


def test_crash_maps_to_exit_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unexpected exception in the body returns EXIT_ERROR, not 1."""

    def _boom(scratch_rel: str) -> int:
        raise KeyError("rng_seed")

    monkeypatch.setattr(check, "_run", _boom)
    monkeypatch.setattr("sys.argv", ["check"])
    assert check.main() == check.EXIT_ERROR


def test_exit_codes_are_distinct() -> None:
    codes = {check.EXIT_REPRODUCED, check.EXIT_MISMATCH, check.EXIT_ERROR}
    assert codes == {0, 1, 2}
