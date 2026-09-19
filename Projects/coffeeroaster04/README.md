# Crackle (coffeeroaster04)

A Flask web app for logging home coffee roasts and managing roast profiles. This is the fourth iteration of the coffee-roast-logger exercise in this repo; it carries the calculation and persistence logic forward from `coffeeroaster03` and replaces the UI with a browser-based one.

## Run it locally

```bash
uv sync                  # install dependencies into .venv
uv run python app.py     # serves on http://localhost:5000 (debug mode)
```

## Test and lint

```bash
uv run pytest            # tests live in tests/
SKIP_BROWSER_TESTS=1 uv run pytest   # same, without the browser check
uv run pytest tests/browser -rs      # just the browser check (shows why it skipped, if it did)
ruff check .             # static analysis
ruff format --check .    # preview formatting changes without applying them
```

## Layout

| Path | What it is |
|---|---|
| `app.py` | Flask routes and page wiring |
| `calculations.py`, `validators.py` | Pure calculation and input-validation functions (no I/O) |
| `data_persistence.py` | JSON load/save for records, profiles, users, and roasters |
| `roasters.py` | What comes from a roaster: temperature-unit table, per-roaster settings and limits, the live chart's opening, and the startup migration |
| `calibration_report.py` | Read-only report comparing logged roasts with each roaster's stored values (see below) |
| `email_sender.py` | Verification, password-reset, and feedback emails |
| `templates/`, `static/` | Jinja2 pages; extracted JS and CSS |
| `data/` | JSON data. `roasters.json` is tracked; the other files are live data and gitignored |
| `tests/` | pytest suite; `tests/browser/` drives the pages in headless Chromium (see below) |

## Project documents

- `SPEC.md` — what the app must do (requirements, constraints, domain rules)
- `to-do.md` — planned work and its detailed plans
- `DEPLOY.md` — deploying to PythonAnywhere

## Browser check

`tests/browser/` runs the real app on fixture data and drives its pages in headless Chromium: it loads Add Roast and the profile pages, clicks Start / First Crack Now! / Reset and the wizard, and checks the chart data, axis titles and units, readouts, and that the console stayed clean. It is the only check of the JavaScript, so run it after changing anything in `static/js/` or the page scripts.

It needs Chromium (or Chrome) and Node 22+ on your `PATH` and network access for the Chart.js CDN tag the pages use; if any is missing the tests are skipped with the reason. There is nothing to install for it (no npm packages), and it takes about ten seconds.

## Calibration report

`calibration_report.py` reads your logged roasts and shows, per roaster, how the time to first crack, weight loss, temperature at first crack, and development ratio compare with the values stored for that roaster in `data/roasters.json` — the way to decide when a roaster's numbers can be tuned and marked calibrated. It only reads: it writes nothing and does not start the app.

```bash
uv run python calibration_report.py                           # data/roast_records.json
uv run python calibration_report.py --records ~/roast_records.json   # e.g. a copy downloaded from PythonAnywhere
```

Your live roasts are not in the repository (`data/roast_records.json` is gitignored), so either run it where the real file is or download a copy and pass `--records`.
