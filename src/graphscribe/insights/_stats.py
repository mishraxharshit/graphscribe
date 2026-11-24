from __future__ import annotations

import numpy as np


def fit_line(x: np.ndarray, y: np.ndarray):
    """Least-squares straight line in one pass. Returns (slope, intercept, r_squared)."""
    xm, ym = float(x.mean()), float(y.mean())
    dx = x - xm
    sxx = float(np.dot(dx, dx))
    if sxx == 0:
        return 0.0, ym, 0.0
    dy = y - ym
    slope = float(np.dot(dx, dy)) / sxx
    intercept = ym - slope * xm
    ss_tot = float(np.dot(dy, dy))
    if ss_tot == 0:
        return slope, intercept, 0.0
    r2 = (float(np.dot(dx, dy)) ** 2) / (sxx * ss_tot)  # same as 1 - SSres/SStot for a line
    return slope, intercept, max(0.0, min(1.0, r2))
