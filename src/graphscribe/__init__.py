"""Importing a module here registers its rule. Add new rules as new files."""

from . import extremes, outliers, summary, trend  # noqa: F401
from .base import Data, Insight, Mark, fmt, register_insight, run_all

__all__ = ["Data", "Insight", "Mark", "fmt", "register_insight", "run_all"]
