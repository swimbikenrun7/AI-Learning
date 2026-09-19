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
ruff check .             # static analysis
ruff format --check .    # preview formatting changes without applying them
```

## Layout

| Path | What it is |
|---|---|
| `app.py` | Flask routes and page wiring |
| `calculations.py`, `validators.py` | Pure calculation and input-validation functions (no I/O) |
| `data_persistence.py` | JSON load/save for records, profiles, users, and roasters |
| `email_sender.py` | Verification, password-reset, and feedback emails |
| `templates/`, `static/` | Jinja2 pages; extracted JS and CSS |
| `data/` | JSON data. `roasters.json` is tracked; the other files are live data and gitignored |
| `tests/` | pytest suite |

## Project documents

- `SPEC.md` — what the app must do (requirements, constraints, domain rules)
- `to-do.md` — planned work and its detailed plans
- `DEPLOY.md` — deploying to PythonAnywhere
