"""How fast is graphscribe's line chart from small to huge data?

    python benchmarks/bench_line.py            # 1 thousand .. 10 million points
    python benchmarks/bench_line.py --huge     # also 50 million (needs ~4 GB of free RAM)

Times are for the whole job: understand the data, work out the explanation, draw the SVG.
"""

import resource
import sys
import time

import numpy as np

import graphscribe as gs


def peak_mb() -> float:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # Linux reports KB


def run(n: int) -> None:
    rng = np.random.default_rng(0)
    y = np.cumsum(rng.normal(0.01, 1, n))
    y[n // 3] += 12 * float(y.std())  # one planted spike: it must always be found
    t0 = time.perf_counter()
    chart = gs.line(y)
    t1 = time.perf_counter()
    text = chart.explain()
    t2 = time.perf_counter()
    svg = chart.svg()
    t3 = time.perf_counter()
    found = "extreme" in text
    print(f"{n:>12,} | {t1 - t0:7.3f} | {t2 - t1:7.3f} | {t3 - t2:7.3f} | {t3 - t0:7.3f} | "
          f"{len(svg) / 1024:6.0f} KB | {peak_mb():7.0f} MB | {'yes' if found else 'NO'}")


if __name__ == "__main__":
    sizes = [10**3, 10**4, 10**5, 10**6, 10**7] + ([5 * 10**7] if "--huge" in sys.argv else [])
    print(f"{'points':>12} | {'load':>7} | {'explain':>7} | {'draw':>7} | {'total':>7} | "
          f"{'svg size':>9} | {'peak mem':>9} | spike found")
    print("-" * 92)
    for n in sizes:
        run(n)
