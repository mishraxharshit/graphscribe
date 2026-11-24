# Contributing to graphscribe

Thank you for helping. All skill levels are welcome.

## Setup

```bash
git clone https://github.com/YOUR_USERNAME/graphscribe
cd graphscribe
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest && ruff check .
python benchmarks/bench_line.py
```

## Add an insight rule (best first contribution)

1. Create `src/graphscribe/insights/your_rule.py`.
2. Write a function `(d: Data) -> Insight | None` and decorate it with `@register_insight`.
   `d.x` and `d.y` are clean, sorted NumPy arrays. Look at `insights/extremes.py` (the smallest).
3. Import it in `insights/__init__.py`.
4. Add a test in `tests/test_line.py`.

Write the text for a beginner. If you use a technical word, explain it in the same sentence.
Rules must work on 10 million points, so use NumPy, not Python loops over the data.

## Working on the renderer

graphscribe draws its own charts in `src/graphscribe/render/`. Do not add matplotlib or any other
plotting library. NumPy is the only dependency, and new dependencies need maintainer approval.
Always look at the output: render a chart and open the SVG.

## Pull requests

- Small and focused: one idea per pull request.
- `pytest` and `ruff check .` must pass.
- If you change anything that affects speed, show the `benchmarks/bench_line.py` numbers.
- By contributing, you agree your work is licensed under Apache-2.0.
- No `eval`, `exec` or `pickle` on user data. No network calls without discussion.

## Conduct

Be kind and respectful. See [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).
