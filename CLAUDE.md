# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

This is Josh's personal learning journal for an "AI Software Engineering Apprenticeship" (see `README.md`). It is not a product codebase — it's a sequence of small Python exercises ("Missions", numbered 0.1, 0.2, ...) done under a structured curriculum, plus notes tracking what was learned along the way. Treat requests here as *tutoring/pairing on a specific exercise*, not as feature delivery on a shared system.

Each numbered mission tends to rebuild the same toy project (a coffee roast logger) with one new concept added — functions, then input validation, then persistence, then modules, then a CLI, then git branching, then linting. `Projects/coffeeroaster01/`, `02/`, `03/`, and `04/` are four successive, independent iterations of this exercise (not layers of one app) — each has its own `SPEC.md` describing its requirements/constraints for that stage. `coffeeroaster04/` ("Crackle") is the current one: a Flask web app that carries 03's calculation and persistence logic forward and has since grown well past the earlier exercises (accounts, roaster-driven profiles, deployment) — see its section below. Do not assume later files supersede or should be merged with earlier ones; check which mission/project is currently active before editing.

## Standing guardrails (from `Notes/guardrails.md`)

These are explicit, user-authored rules for how AI should behave in this repo. Follow them by default:

- **Minimal diffs**: solve the smallest problem that moves the current mission forward. No unrequested refactors, no added abstraction, no speculative generality.
- **No test tampering**: never modify or delete an existing test just to make it pass. If a test conflicts with the spec, explain the conflict instead of silently changing the test.
- **Spec-driven, not implementation-directed**: when a `SPEC.md` exists for the project you're touching, treat it as the source of truth for requirements/constraints, and prefer following/updating it over improvising behavior. Distinguish *requirement* (what it must do), *constraint* (what it must not do/introduce), *implementation* (how), and *domain rule* (a real-world fact, e.g. "finished weight < green weight") — these are deliberately kept separate in specs written in this repo.
- **Simplest architecture that fits the current stage** — do not propose splitting a small script into many modules/services/databases/frontends unless the mission is explicitly about that refactor. Josh has repeatedly rejected over-engineered proposals (e.g. 10-file architectures, full web stacks) for scripts of a few hundred lines.
- **Review-sized changes**: don't modify more code than a human can reasonably review line-by-line in one sitting.
- If stuck on one error for a while: read the full error message, explain it in plain terms, and state what was already tried before proposing further changes — don't thrash.
- **No Silent Auto-Fixes**: If a command fails or a linting error occurs, Claude must explain the failure in the chat before executing a secondary command to fix it. Do not chain commands blindly to force a pass.
- **Explain the "Why"**: Because this is a tutoring/pairing context, prioritize explaining the concept behind a code change over just delivering the patch.

## Working with the coffee roaster exercises

Each `coffeeroaster0N/` folder is self-contained. Typical module split within a given iteration: input handling / UI, calculations (pure functions, no I/O), persistence (JSON read/write), and tests. When adding validation or features, keep calculation functions free of `input()`/`print()` — this separation is intentional and repeatedly emphasized in the mission notes (`Notes/daily-log.md`).

### Running tests
Projects 01–03 have no dependency manifest, virtualenv, or pytest/ruff config file — dependencies (`pytest`, `ruff`) are expected to already be installed in the ambient environment. (Project 04 is the exception: it has a `pyproject.toml`, a `uv`-managed `.venv`, and pytest config.) Run tests from inside the relevant project directory, matching its own test layout:

```bash
# coffeeroaster01 (flat layout, unittest-style file names but run via pytest)
cd Projects/coffeeroaster01 && pytest

# coffeeroaster02 (package layout: roasting_logger/ + tests/)
cd Projects/coffeeroaster02 && pytest

# coffeeroaster03 (flat layout, unittest.TestCase-based)
cd Projects/coffeeroaster03 && pytest
# or, single-process unittest:
cd Projects/coffeeroaster03 && python -m unittest test_units.py test_integration.py

# coffeeroaster04 (Flask app; tests live in tests/, config in pyproject.toml)
cd Projects/coffeeroaster04 && uv run pytest
# the same, without the headless-Chromium browser check in tests/browser/
cd Projects/coffeeroaster04 && SKIP_BROWSER_TESTS=1 uv run pytest
```

Run a single test: `pytest path/to/test_file.py::TestClass::test_name` (or `-k <substring>`).

### Linting/formatting
```bash
ruff check .            # static analysis
ruff format --check .   # preview formatting changes without applying them
```
Prefer `--check` first and let Josh review the diff before applying `ruff format .` — this project explicitly practices reviewing static-analysis suggestions rather than auto-applying them, and some Ruff findings have been deliberately rejected as inapplicable to this code's actual usage (e.g. timezone-naive `datetime` where wall-clock time isn't used).

### Data files
Iterations 01–03 persist to their own `data/roast_records.json` (git-tracked, not gitignored); for those only `__pycache__/` and `*.pyc` are gitignored (`.gitignore`). Project 04 is different: its live data (`data/roast_records.json`, `roast_profiles.json`, `users.json`) is **gitignored** because it is deployed with real accounts (see its `.gitignore` and `DEPLOY.md`), while `data/roasters.json` is tracked reference data. Don't delete or "fix" a corrupted JSON file by recreating it empty — the specs explicitly require detecting corruption and stopping rather than silently discarding existing records.

### coffeeroaster04 (Crackle)
- **Documents:** `SPEC.md` is the source of truth for what the app must do; `to-do.md` is the plan and current status (settled decisions, what each item built, its commit hash, what is still open) and should be kept accurate as work lands; `README.md` covers running and testing; `DEPLOY.md` covers PythonAnywhere. When behavior changes, update `SPEC.md` in the same change.
- **Layout:** `app.py` (Flask routes), `calculations.py` and `validators.py` (pure, no I/O), `data_persistence.py`, `roasters.py` (roaster-driven settings and units), `calibration_report.py` (a read-only script), `templates/`, `static/`, `tests/` (including `tests/browser/`).
- **Scripts must not `import app`:** its startup migration rewrites the live profile and record files. Use `data_persistence` and `calculations` directly, as `calibration_report.py` does.
- **Live data:** never `git checkout`, `git reset`, or recreate the gitignored data files; they are real users' data (see `DEPLOY.md`). Units are never converted: each roaster's temperatures stay in its own unit.
- **Branches:** `main` is what gets deployed. Feature work (e.g. the roaster-driven redesign on `roaster-selection`) happens on a branch and is merged into `main` when Josh asks.

## Git workflow

- New missions/features are typically done on a feature branch (e.g. `0.14.4_lab`, `mission-0.14.2-agent`), not directly on `main`.
- Commit at meaningful, known-good checkpoints (after tests pass) rather than too frequently or too rarely.
- Do not commit, merge, or push without being asked — per the mission notes, human review of `git diff` before commit/merge is a deliberate part of this apprenticeship, not a formality.
- Cloud Constraints: A .cloudignore file is active at the root. Do not suggest scripts or workflows that rely on uploading files or directories explicitly blocked by .cloudignore.

## Omarchy Environment Context
- **Operating System:** This repository is running inside Omarchy (an Arch Linux-based rolling distribution). 
- **Tooling Availability:** Shell commands should assume standard Linux/Arch utilities. Do not attempt to use `apt`, `brew`, or Windows-specific commands.
- **Terminal Editor:** The primary environment editor is Neovim (`nvim`). When suggesting manual file edits to Josh, reference `nvim` or standard terminal workflows.


## Other directories

- `Notes/` — `daily-log.md` (chronological mission log/journal — long, append-only, treat as historical record, not something to rewrite), `guardrails.md` (rules above), `command-cheatsheet.md` (reference commands for git/PowerShell/WSL/tmux/Ollama/Ruff), `vocabulary.md` (glossary built up as terms are introduced), `computer.md` (hardware/environment specs for Josh's two machines).
- `Prompts/` — `ai-prompts.md` and `debugging-prompts.md` are placeholders intended to collect reusable prompts; currently empty of content beyond a heading.
- `Scratch/` — throwaway files, not meaningful to the curriculum.
