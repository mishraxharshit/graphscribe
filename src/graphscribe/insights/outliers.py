from __future__ import annotations

import numpy as np

from ._stats import fit_line
from .base import Data, Insight, Mark, fmt, register_insight


@register_insight
def outliers(d: Data):
    if d.y.size < 8:
        return None
    slope, intercept, _ = fit_line(d.x, d.y)
    score = d.y - (slope * d.x + intercept)  # distance from the trend, not from zero
    q1, q3 = np.percentile(score, [25, 75])
    iqr = q3 - q1
    if iqr == 0:
        return None
    mild = (score < q1 - 1.5 * iqr) | (score > q3 + 1.5 * iqr)
    far = (score < q1 - 3 * iqr) | (score > q3 + 3 * iqr)
    n_mild, n_far = int(mild.sum()), int(far.sum())
    if n_mild == 0:
        return Insight("outliers", "No unusual values (outliers) were found.", importance=4)

    idx = np.where(far if n_far else mild)[0]
    idx = idx[np.argsort(-np.abs(score[idx] - np.median(score)))][:5]
    where = (lambda i: f"{fmt(d.y[i])} on {d.fmt_x(float(d.x[i]))}") if d.x_is_time else (
        lambda i: f"{fmt(d.y[i])} at x = {d.fmt_x(float(d.x[i]))}")
    shown = ", ".join(where(i) for i in idx)

    if not n_far:
        word = "value is" if n_mild == 1 else "values are"
        return Insight(
            "outliers",
            f"{n_mild:,} {word} a little unusual, but none is extreme (for example {shown}). "
            "Some of this is normal in real data.", importance=5)

    word = "extreme value sits" if n_far == 1 else "extreme values sit"
    more = f" (showing the 5 biggest of {n_far:,})" if n_far > 5 else ""
    extra = f" {n_mild - n_far:,} more are mildly unusual." if n_mild > n_far else ""
    marks = tuple(Mark("point", float(d.x[i]), f"extreme: {fmt(d.y[i])}", float(d.y[i]))
                  for i in idx[:3])
    check = "it is a real event or a data error" if n_far == 1 else (
        "they are real events or data errors")
    return Insight(
        "outliers",
        f"{n_far:,} {word} far from the rest: {shown}{more}. Check whether {check}.{extra}",
        importance=8, headline=f"with {n_far:,} extreme value" + ("" if n_far == 1 else "s"),
        marks=marks)
