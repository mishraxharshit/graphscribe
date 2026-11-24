from __future__ import annotations

import numpy as np

from .base import Data, Insight, fmt, register_insight


@register_insight
def summary(d: Data):
    n = d.y.size
    subject = f"{d.y_name} ranges" if d.y_name else "The values range"
    text = (f"There are {n:,} points. {subject} from {fmt(d.y.min())} to {fmt(d.y.max())}. "
            f"The average is {fmt(d.y.mean())} and the middle value (median) is "
            f"{fmt(np.median(d.y))}.")
    return Insight("summary", text, importance=3)
