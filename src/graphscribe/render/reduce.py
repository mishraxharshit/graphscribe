"""Shrink huge data to what a screen can show, without hiding the shape.

A screen is about 1000 pixels wide, so drawing 10 million points is pointless. For every
pixel-wide slice of the data we keep its lowest and highest value. Spikes and dips survive.
"""

from __future__ import annotations

import numpy as np


def minmax_decimate(x: np.ndarray, y: np.ndarray, buckets: int):
    n = y.size
    if n <= buckets * 4:
        return x, y
    k = n // buckets
    body = y[: k * buckets].reshape(buckets, k)
    base = np.arange(buckets) * k
    pair = np.stack([base + body.argmin(axis=1), base + body.argmax(axis=1)], axis=1)
    idx = np.unique(np.concatenate([[0], pair.ravel(), [n - 1]]))
    return x[idx], y[idx]
