from __future__ import annotations

import numpy as np

from .base import Data, Insight, Mark, fmt, register_insight


@register_insight
def extremes(d: Data):
    if d.y.size < 3:
        return None
    hi, lo = int(np.argmax(d.y)), int(np.argmin(d.y))
    text = (f"The highest value is {fmt(d.y[hi])} at {d.fmt_x(float(d.x[hi]))}. "
            f"The lowest is {fmt(d.y[lo])} at {d.fmt_x(float(d.x[lo]))}.")
    marks = ()
    if d.y.size > 12:  # with 12 or fewer points every value is already written on the chart
        marks = (Mark("dot", float(d.x[hi]), f"high: {fmt(d.y[hi])}", float(d.y[hi])),
                 Mark("dot", float(d.x[lo]), f"low: {fmt(d.y[lo])}", float(d.y[lo])))
    return Insight("extremes", text, importance=6, marks=marks)
