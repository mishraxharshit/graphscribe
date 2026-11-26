from __future__ import annotations

import html
import os
import tempfile
import webbrowser
from typing import Any, Optional

import numpy as np

from . import teach
from .insights import Data, run_all
from .render.svg import render_line


def _in_notebook() -> bool:
    """True inside Jupyter, VS Code notebooks and Colab (not in a plain terminal)."""
    try:
        from IPython import get_ipython
    except ImportError:
        return False
    shell = get_ipython()
    return shell is not None and shell.__class__.__name__ == "ZMQInteractiveShell"


class Explanation(str):
    """A string that prints nicely in a terminal or notebook."""

    def __repr__(self) -> str:
        return str(self)


def _numbers(raw: Any, what: str) -> np.ndarray:
    arr = np.asarray(raw)
    if arr.dtype.kind in "iufb":
        return arr.astype(float, copy=False)
    try:
        return arr.astype(float)
    except (TypeError, ValueError):
        raise ValueError(f"{what} must be numbers. Text values are not supported in a line "
                         "chart.") from None


def _prepare(y: Any, x: Any, y_label: str, x_label: str):
    """Accept lists, arrays, pandas Series. Returns clean sorted float arrays."""
    if hasattr(y, "index") and hasattr(y, "values"):  # pandas Series
        if x is None and np.asarray(y.index).dtype.kind in "iufM":
            x = np.asarray(y.index)
        y_label = y_label or str(getattr(y, "name", "") or "")
        y = y.values
    yv = _numbers(y, "Values")
    if yv.ndim != 1:
        raise ValueError("A line chart needs one list of values (and optionally an x list).")
    is_time = False
    if x is None:
        xv = np.arange(yv.size, dtype=float)
    else:
        xa = np.asarray(x)
        if xa.dtype.kind == "M":
            nat = np.isnat(xa)
            xv = xa.astype("datetime64[s]").astype(np.int64).astype(float)
            xv[nat] = np.nan
            is_time = True
        elif xa.dtype.kind in "iuf":
            xv = xa.astype(float, copy=False)
        else:
            raise ValueError("x must be numbers or dates.")
        if xv.size != yv.size:
            raise ValueError(f"x has {xv.size} items but the values have {yv.size}.")
    ok = ~(np.isnan(yv) | np.isnan(xv))
    missing = int(ok.size - ok.sum())
    if missing:
        xv, yv = xv[ok], yv[ok]
    if yv.size == 0:
        raise ValueError("There is no usable data (everything is empty or NaN).")
    if yv.size > 1 and not bool(np.all(xv[1:] >= xv[:-1])):
        order = np.argsort(xv, kind="stable")
        xv, yv = xv[order], yv[order]
    return xv, yv, is_time, missing, y_label


class LineChart:
    def __init__(self, y: Any, x: Any = None, *, title: str = "", x_label: str = "",
                 y_label: str = ""):
        self.x, self.y, self.is_time, self.missing, self.y_label = _prepare(
            y, x, y_label, x_label)
        self.title, self.x_label = title, x_label
        self._found = None
        self._drawn = None

    # ----- understanding the data -------------------------------------------------------
    def _insights(self):
        if self._found is None:  # computed once, reused by explain() and svg()
            self._found = run_all(Data(self.x, self.y, self.is_time, self.x_label, self.y_label))
        return self._found

    def headline(self) -> str:
        """One line that says what the chart shows, written by graphscribe."""
        found = self._insights()
        main = next((i.headline for i in found if i.headline and i.kind != "outliers"), "")
        extra = next((i.headline for i in found if i.kind == "outliers" and i.headline), "")
        return f"{main}, {extra}" if main and extra else (main or extra)

    def findings(self) -> list:
        lines = [i.text for i in self._insights()]
        if self.missing:
            lines.append(f"{self.missing:,} missing value(s) were skipped.")
        return lines

    def explain(self) -> Explanation:
        """Plain-English explanation of what the chart shows."""
        name = f" of '{self.y_label}'" if self.y_label else ""
        lines = ["WHAT YOU ARE LOOKING AT",
                 f"  A line chart{name} with {self.y.size:,} points. Your values come in order, "
                 "so a line shows how they change from one point to the next.",
                 "", "WHAT THE DATA SAYS"]
        lines += [f"  - {t}" for t in self.findings()]
        if self.y.size > 3200:
            lines += ["", "HOW IT WAS DRAWN",
                      f"  Your {self.y.size:,} points are more than a screen can show. For every "
                      "pixel-wide slice the highest and the lowest value are kept, so no spike or "
                      "dip is hidden. All statistics above use every single point."]
        return Explanation("\n".join(lines))

    def teach(self) -> Explanation:
        """A short lesson on how to read a line chart."""
        return Explanation(teach.LINE)

    # ----- drawing ----------------------------------------------------------------------
    def svg(self, width: int = 800, height: int = 480, annotate: bool = True) -> str:
        """Draw the chart. annotate=True adds a headline and points at what matters."""
        marks, headline = (), ""
        if annotate:
            headline = self.headline()
            marks = [m for i in self._insights() for m in i.marks]
            rings = {m.x for m in marks if m.kind == "point"}
            marks = tuple(m for m in marks if not (m.kind == "dot" and m.x in rings))
        svg, self._drawn = render_line(
            self.x, self.y, title=self.title, x_label=self.x_label, y_label=self.y_label,
            x_is_time=self.is_time, headline=headline, marks=marks, width=width, height=height,
            alt=f"line chart: {headline or self.title or self.y_label}")
        return svg

    def html(self) -> str:
        esc = html.escape
        pre = "white-space:pre-wrap;font:14px/1.6 system-ui,sans-serif"
        return ("<div style='font-family:system-ui,sans-serif;max-width:820px'>"
                f"<style>svg{{max-width:100%;height:auto}}</style>{self.svg()}"
                f"<pre style='{pre}'>{esc(str(self.explain()))}</pre>"
                "<details><summary style='cursor:pointer;font:600 14px system-ui'>"
                f"Teach me how to read this</summary><pre style='{pre}'>"
                f"{esc(str(self.teach()))}</pre></details></div>")

    def _repr_html_(self) -> str:  # Jupyter shows the chart and its explanation automatically
        return self.html()

    def __repr__(self) -> str:
        return (f"<graphscribe.LineChart {self.y.size:,} points>  "
                ".show() to view, .explain() to read, .save('chart.svg') to keep")

    def save(self, path: str) -> "LineChart":
        """Save as .svg (chart only) or .html (chart + explanation + lesson)."""
        ext = os.path.splitext(path)[1].lower()
        if ext == ".svg":
            text = self.svg()
        elif ext in (".html", ".htm"):
            text = f"<!doctype html><meta charset='utf-8'><title>graphscribe</title>{self.html()}"
        else:
            raise ValueError("Save as .svg or .html. PNG export is planned, not built yet.")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return self

    def show(self) -> "LineChart":
        """Display the chart with its explanation.

        In Jupyter it appears right below the cell. In a script it opens in your web browser.
        If no browser can be opened (a remote server, for example) the file is saved and its
        path is printed, so something always happens.
        """
        if _in_notebook():
            from IPython.display import HTML, display

            display(HTML(self.html()))
            return self
        fd, path = tempfile.mkstemp(suffix=".html", prefix="graphscribe_")
        os.close(fd)
        self.save(path)
        if not webbrowser.open("file://" + path):
            print(f"Could not open a browser here. The chart was saved to:\n  {path}\n"
                  "Open that file in any browser, or use .save('chart.svg') to choose the name.")
        return self


def line(y: Any, x: Optional[Any] = None, *, title: str = "", x_label: str = "",
         y_label: str = "") -> LineChart:
    """Draw a line chart that explains itself. Works from 5 points to 100 million."""
    return LineChart(y, x, title=title, x_label=x_label, y_label=y_label)
