"""Run this: python examples/quickstart.py   (writes 3 charts into docs/img/)"""

import os

import numpy as np

import graphscribe as gs

out = os.path.join(os.path.dirname(__file__), "..", "docs", "img")
os.makedirs(out, exist_ok=True)
rng = np.random.default_rng(3)

# 1) small: 12 months of sales. Every value is written on the chart.
months = np.arange("2025-01", "2026-01", dtype="datetime64[M]")
sales = [112, 118, 125, 123, 131, 140, 138, 150, 149, 162, 171, 168]
gs.line(sales, x=months, title="Monthly sales", y_label="sales").save(f"{out}/small.svg")

# 2) medium: two years of daily visitors with one strange day.
days = np.arange("2024-01-01", "2026-01-01", dtype="datetime64[D]")
visitors = 900 + np.arange(days.size) * 0.9 + rng.normal(0, 60, days.size)
visitors[410] += 1400
gs.line(visitors, x=days, title="Daily visitors", y_label="visitors").save(f"{out}/medium.svg")

# 3) big: 10 million sensor readings. Same code, same clean chart.
readings = np.cumsum(rng.normal(0.002, 1, 10_000_000))
readings[3_333_333] += 15_000
gs.line(readings, title="Sensor readings (10 million points)").save(f"{out}/big.svg")
print("done")
