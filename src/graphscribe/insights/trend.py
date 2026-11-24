from __future__ import annotations

from ._stats import fit_line
from .base import Data, Insight, Mark, fmt, register_insight


@register_insight
def trend(d: Data):
    if d.y.size < 3:
        return None
    slope, intercept, r2 = fit_line(d.x, d.y)
    x0, x1 = float(d.x[0]), float(d.x[-1])
    start, end = slope * x0 + intercept, slope * x1 + intercept
    scale = abs(float(d.y.mean())) or 1.0
    if r2 < 0.1 or abs(end - start) / scale < 0.01:
        return Insight("trend", "There is no clear upward or downward trend. The values stay "
                       "around the same level.", importance=7, headline="Holding steady")
    up = slope > 0
    strength = "strong" if r2 >= 0.7 else "moderate" if r2 >= 0.4 else "weak"
    if r2 >= 0.4:
        head = "Rising steadily" if up else "Falling steadily"
    else:
        head = "Drifting " + ("up" if up else "down") + " slightly"
    return Insight(
        "trend",
        f"There is a {strength} {'upward' if up else 'downward'} trend. The overall line "
        f"{'rises' if up else 'falls'} from about {fmt(start)} to {fmt(end)}. A straight line "
        f"explains about {r2 * 100:.0f}% of the ups and downs (R-squared = {r2:.2f}).",
        importance=9, headline=head,
        marks=(Mark("trend", x0, f"overall trend: {'up' if up else 'down'}", start, x1, end),),
    )
