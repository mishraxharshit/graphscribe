"""Pick clean axis tick values and format them for people."""

from __future__ import annotations

import math

import numpy as np


def nice_ticks(lo: float, hi: float, target: int = 6):
    """Return (tick_values, step) with round numbers like 0, 20, 40 or 0.25, 0.5."""
    if not (math.isfinite(lo) and math.isfinite(hi)):
        return np.array([0.0, 1.0]), 1.0
    if lo == hi:
        pad = abs(lo) * 0.5 or 1.0
        lo, hi = lo - pad, hi + pad
    raw = (hi - lo) / target
    mag = 10 ** math.floor(math.log10(raw))
    step = mag * 10
    for m in (1, 2, 2.5, 5, 10):
        if raw <= m * mag:
            step = m * mag
            break
    first = math.ceil(lo / step - 1e-9)
    last = math.floor(hi / step + 1e-9)
    return np.arange(first, last + 1) * step, step


def format_number(v: float, step: float) -> str:
    a = abs(v)
    if a >= 1e9:
        return f"{v / 1e9:g}B"
    if a >= 1e6:
        return f"{v / 1e6:g}M"
    d = 0
    while d < 8 and abs(round(step, d) - step) > 1e-9 * max(step, 1e-12):
        d += 1
    if a >= 1e4 and d == 0:
        return f"{v:,.0f}"
    return f"{v:.{d}f}"


def format_time(seconds: float, whole_days: bool) -> str:
    stamp = str(np.datetime64(int(round(seconds)), "s"))
    return stamp[:10] if whole_days else stamp[:16].replace("T", " ")


def fmt(v: float) -> str:
    """Numbers for people: 11,590 not 1.159e+04, and no pointless decimals."""
    v = float(v)
    a = abs(v)
    if a >= 1e4:
        return f"{v:,.0f}"
    if a >= 100:
        return f"{v:,.1f}".rstrip("0").rstrip(".")
    return f"{v:.4g}"


_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def time_ticks(lo: float, hi: float, target: int = 6):
    """Calendar-aware ticks for a time axis (seconds since 1970): month and year starts, not
    random days. Returns (tick_seconds, labels)."""
    days = (hi - lo) / 86400
    lo_dt, hi_dt = np.datetime64(int(lo), "s"), np.datetime64(int(hi), "s")

    def keep(secs):
        secs = np.asarray(secs, dtype=float)
        return secs[(secs >= lo - 1e-6) & (secs <= hi + 1e-6)]

    if days < 2:  # hours and minutes
        ticks, _ = nice_ticks(lo, hi, target)
        return ticks, [format_time(t, False) for t in ticks]
    if days <= 45:  # whole days
        step = next((s for s in (1, 2, 3, 7, 14) if days / s <= target), 14)
        d0 = int(np.ceil(lo / 86400 / step)) * step
        secs = keep(np.arange(d0, int(hi // 86400) + 1, step) * 86400.0)
        labels = []
        for s in secs:
            d = np.datetime64(int(s), "s").astype("datetime64[D]")
            labels.append(f"{_MONTHS[int(str(d)[5:7]) - 1]} {int(str(d)[8:10]):02d}")
        return secs, labels
    months = days / 30.44
    step = next((s for s in (1, 2, 3, 6) if months / s <= target), None)
    if step is not None:  # month starts
        m_lo = int(lo_dt.astype("datetime64[M]").astype(int))
        m_hi = int(hi_dt.astype("datetime64[M]").astype(int))
        ms = np.arange(-(-m_lo // step) * step, m_hi + 1, step)
        stamps = ms.astype("datetime64[M]").astype("datetime64[s]").astype(np.int64)
        secs = keep(stamps)
        labels = []
        for s in secs:
            m = np.datetime64(int(s), "s").astype("datetime64[M]")
            labels.append(f"{_MONTHS[int(str(m)[5:7]) - 1]} {str(m)[:4]}")
        return secs, labels
    years = months / 12  # year starts
    step = next((s for s in (1, 2, 5, 10, 20, 25, 50, 100) if years / s <= target), 100)
    y_lo = int(lo_dt.astype("datetime64[Y]").astype(int)) + 1970
    y_hi = int(hi_dt.astype("datetime64[Y]").astype(int)) + 1970
    ys = np.arange(-(-y_lo // step) * step, y_hi + 1, step)
    stamps = (ys - 1970).astype("datetime64[Y]").astype("datetime64[s]").astype(np.int64)
    secs = keep(stamps)
    return secs, [str(int(y)) for y, s in zip(ys, stamps) if lo - 1e-6 <= s <= hi + 1e-6]
