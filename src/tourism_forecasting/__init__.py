"""Leakage-aware tourism forecasting research package."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("tourism-forecasting")
except PackageNotFoundError:  # pragma: no cover - editable/source checkout
    __version__ = "0.1.0"

__all__ = ["__version__"]
