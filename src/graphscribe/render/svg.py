"""Draws a line chart as a clean, scalable SVG that explains itself."""

from __future__ import annotations

from xml.sax.saxutils import escape

import numpy as np

from .reduce import minmax_decimate
from .ticks import fmt, format_number, nice_ticks, time_ticks

INK, MUTED, GRID = "#1f2937", "#6b7280", "#ece9e1"
BLUE, ACCENT, PAPER = "#1d4ed8", "#ea580c", "#fbfaf7"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def _linmap(lo, hi, a, b):
    span = (hi - lo) or 1.0
    return lambda v: a + (np.asarray(v, dtype=float) - lo) / span * (b - a)


def _x_ticks(lo, hi, is_time):
    if is_time:
        return time_ticks(lo, hi)
    ticks, step = nice_ticks(lo, hi)
    return ticks, [format_number(t, step) for t in ticks]


def _text(x, y, s, size=12, fill=INK, anchor="start", weight=400, italic=False, halo=False):
    style = ' font-style="italic"' if italic else ""
    common = (f'x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" font-size="{size}" '
              f'font-weight="{weight}"{style}')
    main = f'<text {common} fill="{fill}">{escape(s)}</text>'
    if not halo:
        return main
    # an outline layer underneath keeps the label readable where it crosses the line
    under = (f'<text {common} fill="{PAPER}" stroke="{PAPER}" stroke-width="5" '
             f'stroke-linejoin="round">{escape(s)}</text>')
    return under + main


def _title_block(title, headline, left, pw):
    if headline:
        size = max(15, min(24, int(pw / (0.56 * len(headline)))))
        if title:
            return [_text(left, 26, title.upper(), 11, MUTED, weight=600),
                    _text(left, 58, headline, size, INK, weight=700)]
        return [_text(left, 40, headline, size, INK, weight=700)]
    return [_text(left, 28, title, 17, INK, weight=600)] if title else []


def _marks(marks, mx, my, left, top, pw):
    out, right = [], left + pw
    for m in marks:
        if m.kind == "trend":
            x1, y1, x2, y2 = float(mx(m.x)), float(my(m.y)), float(mx(m.x2)), float(my(m.y2))
            out.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                       f'stroke="{ACCENT}" stroke-width="1.6" stroke-dasharray="6 5"/>')
            w = 6.6 * len(m.label)  # a small legend, top right, so it never covers the data
            out.append(f'<line x1="{right - w - 36:.1f}" x2="{right - w - 10:.1f}" '
                       f'y1="{top - 14}" y2="{top - 14}" stroke="{ACCENT}" stroke-width="1.6" '
                       f'stroke-dasharray="6 5"/>')
            out.append(_text(right, top - 10, m.label, 12, ACCENT, "end", 600))
            continue
        px, py = float(mx(m.x)), float(my(m.y))
        ring = m.kind == "point"
        gap = 34 if ring else 14
        if px - left < 80:  # near the left edge: write the label to the right of the point
            lx, ly, anchor = px + (16 if ring else 10), py + 4, "start"
        elif right - px < 80:
            lx, ly, anchor = px - (16 if ring else 10), py + 4, "end"
        elif py - gap - 8 > top:
            lx, ly, anchor = px, py - gap, "middle"
        else:  # no room above: put it beside the point, not on top of the line
            lx, ly, anchor = px + (16 if ring else 10), py + 4, "start"
        if ring:
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="7" fill="none" '
                       f'stroke="{ACCENT}" stroke-width="2"/>')
            if anchor == "middle":
                out.append(f'<line x1="{px:.1f}" y1="{py - 8:.1f}" x2="{px:.1f}" '
                           f'y2="{ly + 4:.1f}" stroke="{ACCENT}"/>')
        else:  # "dot": a quiet marker for the highest / lowest point
            out.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" fill="{ACCENT}"/>')
        out.append(_text(lx, ly, m.label, 12, ACCENT, anchor, 600, halo=True))
    return out


def render_line(x, y, *, title="", x_label="", y_label="", x_is_time=False, headline="",
                marks=(), width=800, height=480, alt=""):
    """Return (svg_text, points_actually_drawn)."""
    left, right, bottom = 72, 28, 64
    top = (92 if title else 72) if headline else 48
    pw, ph = width - left - right, height - top - bottom
    xlo, xhi = float(x[0]), float(x[-1])
    ylo, yhi = float(y.min()), float(y.max())
    pad = (yhi - ylo) * 0.14 or 1.0
    ylo, yhi = ylo - pad, yhi + pad
    mx, my = _linmap(xlo, xhi, left, left + pw), _linmap(ylo, yhi, top + ph, top)

    body = []
    yt, ystep = nice_ticks(ylo, yhi, 5)
    for t in yt:
        py = float(my(t))
        body.append(f'<line x1="{left}" x2="{left + pw}" y1="{py:.1f}" y2="{py:.1f}" '
                    f'stroke="{GRID}"/>')
        body.append(_text(left - 10, py + 4, format_number(t, ystep), 12, MUTED, "end"))
    xt, xlabels = _x_ticks(xlo, xhi, x_is_time)
    for t, lab in zip(xt, xlabels, strict=True):
        body.append(_text(float(mx(t)), top + ph + 22, lab, 12, MUTED, "middle"))

    xs, ys = minmax_decimate(x, y, pw)
    px, py = mx(xs), my(ys)
    pts = " L".join(f"{a:.1f},{b:.1f}" for a, b in zip(px, py, strict=True))
    base = top + ph
    body.append(f'<path d="M{pts} L{px[-1]:.1f},{base} L{px[0]:.1f},{base} Z" '
                f'fill="{BLUE}" fill-opacity="0.07"/>')
    body.append(f'<path d="M{pts}" fill="none" stroke="{BLUE}" stroke-width="2" '
                f'stroke-linejoin="round" stroke-linecap="round"/>')
    if xs.size <= 60:
        for a, b in zip(px, py, strict=True):
            body.append(f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.2" fill="{BLUE}"/>')
    if xs.size <= 12:  # tiny data: write every value on the chart
        for a, b, v in zip(px, py, ys, strict=True):
            body.append(_text(a, b - 11, fmt(v), 12, INK, "middle", 600, halo=True))
    body.append(f'<line x1="{left}" x2="{left + pw}" y1="{base}" y2="{base}" '
                f'stroke="{INK}" stroke-width="1.4"/>')
    body += _marks(marks, mx, my, left, top, pw)
    body += _title_block(title, headline, left, pw)
    if x_label:
        body.append(_text(left + pw / 2, height - 14, x_label, 13, MUTED, "middle"))
    if y_label:
        body.append(f'<text transform="translate(16,{top + ph / 2}) rotate(-90)" '
                    f'text-anchor="middle" font-size="13" fill="{MUTED}">{escape(y_label)}</text>')
    label = escape(alt or headline or title or "line chart")
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
           f'width="{width}" height="{height}" role="img" aria-label="{label}" '
           f'font-family="{FONT}" data-drawn-points="{xs.size}">'
           f'<rect width="{width}" height="{height}" fill="{PAPER}"/>' + "".join(body) + "</svg>")
    return svg, int(xs.size)
