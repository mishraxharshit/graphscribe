import time
import xml.etree.ElementTree as ET

import numpy as np
import pytest

import graphscribe as gs
from graphscribe.render.reduce import minmax_decimate

RNG = np.random.default_rng(0)


def valid(svg):
    ET.fromstring(svg)  # raises if the SVG is malformed
    return svg


# ---- reading the data -------------------------------------------------------------------
def test_upward_trend():
    assert "upward" in gs.line(np.arange(50) * 2.0 + RNG.normal(0, 1, 50)).explain()


def test_downward_trend():
    assert "downward" in gs.line([10, 9, 8, 7, 6, 5, 4, 3]).explain()


def test_flat_has_no_trend():
    c = gs.line([5, 5, 5, 5, 5, 5])
    assert "no clear" in c.explain() and c.headline() == "Holding steady"


def test_extreme_value_is_found_and_pointed_at():
    y = np.arange(60) * 1.0
    y[30] += 40
    c = gs.line(y)
    assert "extreme value" in c.explain() and "Rising" in c.headline()
    assert "extreme:" in valid(c.svg()) and "extreme:" not in valid(c.svg(annotate=False))


def test_normal_noise_has_no_extreme_headline():
    assert "extreme" not in gs.line(RNG.normal(0, 1, 2000)).headline()


def test_missing_values_are_skipped_and_reported():
    assert "2 missing" in gs.line([1, 2, np.nan, 4, 5, np.nan, 7, 8]).explain()


def test_unsorted_x_is_sorted():
    c = gs.line([3, 1, 2], x=[3, 1, 2])
    assert list(c.x) == [1, 2, 3] and list(c.y) == [1, 2, 3]


def test_dates_on_x_axis():
    days = np.arange("2026-01-01", "2026-04-01", dtype="datetime64[D]")
    c = gs.line(np.arange(days.size) * 1.0, x=days, y_label="sales")
    assert "Feb 2026" in valid(c.svg()) and "2026-" in c.explain()


def test_series_like_object_uses_its_index():
    class FakeSeries:
        name = "visitors"
        index = np.arange("2026-01-01", "2026-01-31", dtype="datetime64[D]")
        values = np.arange(30) * 1.0

    c = gs.line(FakeSeries())
    assert c.is_time and "visitors" in c.explain()


# ---- small data ---------------------------------------------------------------------------
def test_tiny_data_writes_every_value_on_the_chart():
    svg = valid(gs.line([10, 12, 13, 15, 14]).svg())
    for v in ("10", "12", "13", "15", "14"):
        assert f">{v}</text>" in svg


def test_single_point_does_not_crash():
    assert valid(gs.line([5]).svg()).startswith("<svg")


# ---- big data -----------------------------------------------------------------------------
def test_decimation_keeps_a_single_spike():
    y = RNG.normal(0, 1, 1_000_000)
    y[123_456] = 500.0
    xs, ys = minmax_decimate(np.arange(y.size, dtype=float), y, 700)
    assert ys.max() == 500.0 and ys.size < 3000


def test_big_data_draws_few_points_but_stats_use_all():
    y = np.cumsum(RNG.normal(0, 1, 2_000_000))
    c = gs.line(y)
    svg = c.svg()
    assert c._drawn < 3000 and "2,000,000 points" in c.explain()
    assert "HOW IT WAS DRAWN" in c.explain() and valid(svg)


def test_one_million_points_is_fast():
    y = np.cumsum(RNG.normal(0, 1, 1_000_000))
    t = time.perf_counter()
    c = gs.line(y)
    c.svg()
    c.explain()
    assert time.perf_counter() - t < 5


# ---- friendly errors and output ---------------------------------------------------------
def test_text_values_give_a_clear_error():
    with pytest.raises(ValueError, match="numbers"):
        gs.line(["a", "b", "c"])


def test_x_length_mismatch_gives_a_clear_error():
    with pytest.raises(ValueError, match="items"):
        gs.line([1, 2, 3], x=[1, 2])


def test_all_missing_gives_a_clear_error():
    with pytest.raises(ValueError, match="usable"):
        gs.line([np.nan, np.nan])


def test_save_svg_and_html(tmp_path):
    c = gs.line([1, 3, 2, 5, 4, 6, 8, 7])
    c.save(str(tmp_path / "a.svg"))
    c.save(str(tmp_path / "a.html"))
    assert "WHAT THE DATA SAYS" in (tmp_path / "a.html").read_text()
    with pytest.raises(ValueError, match="svg"):
        c.save(str(tmp_path / "a.png"))


def test_teach_explains_how_to_read_it():
    assert "HOW TO READ A LINE CHART" in gs.line([1, 2, 3]).teach()


# ---- show() must never fail silently ----------------------------------------------------
def test_show_prints_the_path_when_no_browser(monkeypatch, capsys):
    import webbrowser

    monkeypatch.setattr(webbrowser, "open", lambda url: False)
    gs.line([1, 2, 3, 5, 4]).show()
    out = capsys.readouterr().out
    assert "saved to" in out and ".html" in out


def test_show_opens_a_browser_quietly_when_possible(monkeypatch, capsys):
    import webbrowser

    opened = []
    monkeypatch.setattr(webbrowser, "open", lambda url: opened.append(url) or True)
    gs.line([1, 2, 3, 5, 4]).show()
    assert opened and opened[0].startswith("file://") and capsys.readouterr().out == ""


def test_show_displays_inline_in_a_notebook(monkeypatch):
    import sys
    import types

    shown = []
    fake = types.ModuleType("IPython.display")
    fake.HTML = lambda html: ("HTML", html)
    fake.display = lambda obj: shown.append(obj)
    monkeypatch.setitem(sys.modules, "IPython.display", fake)
    monkeypatch.setattr("graphscribe.core._in_notebook", lambda: True)
    gs.line([1, 2, 3, 5, 4]).show()
    assert shown and shown[0][0] == "HTML" and "<svg" in shown[0][1]


def test_repr_tells_a_beginner_what_to_do():
    assert ".show()" in repr(gs.line([1, 2, 3]))
