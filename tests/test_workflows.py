from types import SimpleNamespace

import pandas as pd
import pytest

import tourism_forecasting.workflows as workflows


def test_backtest_workflow_enforces_monthly_continuity(monkeypatch: pytest.MonkeyPatch) -> None:
    gapped = pd.DataFrame(
        {
            "date": pd.to_datetime(["2020-01-01", "2020-03-01"]),
            "target_original_with_missing": [1.0, 2.0],
        }
    )
    monkeypatch.setattr(
        workflows,
        "load_core_data",
        lambda *_args, **_kwargs: (gapped, SimpleNamespace(sha256="synthetic")),
    )
    with pytest.raises(ValueError, match="Monthly continuity failure"):
        workflows.backtest_workflow(include_ml=False)
