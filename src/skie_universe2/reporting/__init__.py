"""Reporting utilities for SKIE-Universe-2.

Canonical, hypothesis-agnostic performance reporting. :mod:`tearsheet` turns
per-session gross/net log-return streams (from the ADR-0003 shadow ledger) into
a platform-style backtest report (equity, drawdown, Monte Carlo, monthly
returns, metrics), rendered by ``scripts/build_tearsheet.py`` into the
``docs/templates/tearsheet_template.html`` shell.
"""
