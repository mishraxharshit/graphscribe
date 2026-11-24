"""Insight registry. One insight rule = one small function = one file."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, List, Optional

import numpy as np

from ..render.ticks import fmt, format_time

__all__ = ["Data", "Insight", "Mark", "fmt", "register_insight", "run_all"]


@dataclass(frozen=True)
class Mark:
    """Something to point at ON the chart, in data coordinates."""

    kind: str  # "point" (ring + callout), "dot" (quiet marker), "trend" (dashed line)
    x: float
    label: str
    y: float = 0.0
    x2: float = 0.0
    y2: float = 0.0


@dataclass(frozen=True)
class Insight:
    kind: str
    text: str
    importance: int = 5  # 1 (minor) .. 10 (major): decides the order in explain()
    headline: str = ""  # a few words for the chart's title line
    marks: tuple = ()  # Mark objects drawn on the chart itself


@dataclass
class Data:
    """What a rule gets to look at. Arrays are clean (no NaN) and sorted by x."""

    x: np.ndarray
    y: np.ndarray
    x_is_time: bool = False
    x_name: str = ""
    y_name: str = ""

    def fmt_x(self, v: float) -> str:
        if self.x_is_time:
            return format_time(v, whole_days=(self.x[-1] - self.x[0]) >= 2 * 86400)
        return fmt(v)


Rule = Callable[[Data], Optional[Insight]]
_RULES: List[Rule] = []


def register_insight(func: Rule) -> Rule:
    """Decorator: add a rule so every chart runs it automatically."""
    _RULES.append(func)
    return func


def run_all(d: Data) -> List[Insight]:
    found = [r for r in (rule(d) for rule in _RULES) if r is not None]
    return sorted(found, key=lambda i: -i.importance)
