"""Console entry points."""

from __future__ import annotations

from tourism_forecasting.workflows import audit_workflow, backtest_workflow, reproduce_workflow


def audit() -> None:
    audit_workflow()


def backtest() -> None:
    backtest_workflow()


def reproduce() -> None:
    reproduce_workflow()
