# To-Do — Crackle (coffeeroaster04)

A running list of planned feature updates and their detailed plans.

**How this file relates to the others**
- `SPEC.md` is the source of truth for *what the app must do* (requirements, constraints, domain rules). This file is *how and in what order* we get there. When an item is completed, its resulting requirements are written into `SPEC.md`, and the item here is collapsed to a short summary.
- Nothing here is implemented until its status says so. Human review of `git diff` before every commit is part of the process (see `CLAUDE.md`).

**Status tags**
`[PLANNED]` · `[IN PROGRESS]` · `[COMPLETE]` (with date and commit) · `[DEFERRED]` (considered, deliberately not scheduled)

**Item template** — each item has: Status · Depends on · Goal · Tasks (checkboxes) · Files touched · Tests · Done when. Tick a task's box as it lands; when every box is ticked and the suite passes, change the tag to `[COMPLETE]`, add the date and commit, and collapse the detail to a paragraph.

---

## Settled decisions (roaster-driven-profiles discussion, 2026-09-19)

These are fixed inputs to the plan below, not open questions.

1. **The roaster drives the profile.** The hierarchy is *roaster → profile → roast*. A profile belongs to exactly one roaster, and the profile's structure (grid length, limits, units, wizard behavior) comes from that roaster's data.
2. **No roaster override at Add Roast.** The roaster is implied by the selected profile, and targets are only valid for the roaster they were built for. The workflow is: define a profile for the roaster you use → select that profile → Add Roast.
3. **Limits live in the roaster data.** Weight and time ranges, temperature ranges, and units are per roaster, replacing the one-size-fits-all constants (green 100–300 g, roast time 4:00–20:00, finished ≥ 100 g, 12 rows).
4. **Grid length is per roaster** (`profile_grid_minutes`): one profile row per whole minute, sized to the longest reasonable roast plus a buffer. SR series: about 10 min → 12 rows. Every other roaster's row count comes from research, not from example numbers in conversation: figures like "15 min average, 17 longest, 20 rows" were only an illustration of the rule and are **not data**. Where a roaster's typical roast time can't be sourced, its row count is an inferred value, flagged as such in `notes`.
5. **Explicit values per roaster — no sharing or inheritance.** Every roaster entry carries its own full set of values. Two roasters may hold identical numbers when the research supports it, but each is written out on its own entry so any one can be tuned later without touching another.
6. **Only the Fresh Roast SR800 is calibrated** (the one machine with real logged roasts). Every other roaster's values are inferred from research, marked `calibrated: false`, and refined from user data and feedback.
7. **The roaster is locked once a profile exists.** It is chosen at creation and shown read-only on the edit form. To move a profile to another roaster, create a new profile (a "duplicate for another roaster" helper could come later). Changing it would silently invalidate the grid, targets, and units.
8. **Existing profiles are migrated to the SR800** (there are no other users' data yet). A one-time, idempotent startup migration assigns `fresh-roast-sr800` to any profile with no `roaster_id`, and to any roast record with none (from its profile when the profile still exists, otherwise SR800). Even so, the code keeps tolerating a roaster-less profile by falling back to today's constants: the existing tests build roaster-less profiles in memory and must stay untouched, and it is a safety net if a roaster id is ever removed from `roasters.json`.
9. **A roaster is required when creating a profile** (the wizard depends on it too).
10. **Roast records store their roaster** (`roaster_id`, plus the `temp_unit` in effect) alongside the existing `target_temps` snapshot, because profiles can be edited or deleted and records must stay self-describing. This reverses the Phase 11 note "records do not snapshot the roaster".
11. **The test changes for "roaster required" are approved** (the four tests listed under T-03).
12. **Temperature units: shared code, per-roaster data** (was U1; details below). Each roaster carries `temp_unit`; one code path reads a units table; no conversion, no C/F module forks. The main aim is that graphics scale correctly and the right unit appears in every axis label and readout.
13. **Maximum roast time = the roaster's row count** (was U2). The longest roast accepted without an input error is exactly as long as the profile grid generated for that roaster: 12 rows → 12:00 is accepted and 12:01 is rejected; a 20-row roaster accepts up to 20:00. (Roast time is stored in seconds, so in code this is `profile_grid_minutes × 60` — just minutes converted to seconds.) This guarantees a roast can never run past the rows that describe it. The roaster-less fallback (Settled #8) keeps today's 20:00 limit so existing tests are unaffected.

## Open decisions

None at the moment.

### Temperature units — how Settled #12 is implemented

**The goal:** each roaster carries C or F, graphics and formatting come out right for both, and conversion bugs can't show up.

- **Each roaster carries `temp_unit` (`"F"` or `"C"`).** Every temperature for that roaster's profiles and roasts — targets, actuals, wizard values, chart anchors — is stored and displayed in that unit and **never converted**. Because a profile and its records always belong to one roaster (decisions 1, 2, 10), units never mix, so there is no conversion code to get wrong.
- **Fork the data, not the code.** Rather than two versions of each downstream module, one code path takes a small `TEMP_UNITS` table chosen by the roaster's unit: symbol, label, rate-of-rise label, chart axis bounds, decimals, input hint text, and default sanity range. It lives in `roasters.py` and reaches the JavaScript through the page's JSON config block, so the JS contains no literal unit. The places where C and F genuinely differ are the table's rows.
- **Why not two module forks:** every chart, wizard, and formatting fix would have to be made twice, the copies drift, and the classic bug — "works for F, subtly wrong for C" — comes from the path someone forgot to update.
- **Guards that make the guarantee testable:**
  1. The same profile → roast → chart-config flow is run in parametrized tests against an F fixture roaster and a C fixture roaster.
  2. A test fails if `°F`, `&deg;F`, or a bare unit letter appears in templates or `static/` outside the units table (a small allowlist for prose).
  3. A schema test requires every roaster's `temp_unit` ∈ {F, C} and its `temp_min`/`temp_max` to be plausible for that unit.
  4. Profiles and records snapshot `temp_unit`, so a later edit to `roasters.json` can't reinterpret stored numbers.
  5. The wizard's constants and the chart anchors are already per-roaster data, written in the roaster's own unit.
- **Chart scaling:** the chart's y-axis bounds and step size, the axis title, tooltip/readout suffixes, and the rate-of-rise label all come from the units table row, so a °C roaster's chart is scaled for °C (not a °F chart with the wrong label).
- **Not covered here:** comparing roasts across roasters (which would need a display-only conversion). Nothing in the app does that today.

---

## T-00 [COMPLETE] Roaster selection (Phase 11)

Completed 2026-09-19 · commit `509a315` on branch `roaster-selection` (not yet merged to `main`).
Added `data/roasters.json` (47 roasters, each `{name, values: {}}`), an optional roaster dropdown on the profile form above the wizard, and a faint `.roaster-tag` beside profile names on the profiles list, Add Roast picker, and Add Roast heading. Documented as Phase 11 in `SPEC.md`. 173 tests passing.

---

## T-01 [COMPLETE] Repo cleanup / refactor

Completed 2026-09-19 · commits `3358ebc` (R1), `f0dd94e` (R2), `bd826e1` (R3) on branch `roaster-selection` (not yet merged to `main`). Each commit's suite was run in isolation: 173 passing.
Kept deliberately modest: the live WSGI file does `from app import app` and `data_persistence.py` derives `DATA_DIR` from its own location, so neither module moved.

- **R1 — tests into `tests/`.** `git mv` (pure renames; contents unchanged) plus `pythonpath`/`testpaths` under `[tool.pytest.ini_options]` in `pyproject.toml`. `pytest` from the project directory works exactly as before; a single test is now `pytest tests/test_app.py::Class::test`. `CLAUDE.md` needed no change — its commands don't reference this project.
- **R2 — inline JS/CSS moved to `static/`.** New files: `css/add_roast.css`, `js/add_roast_form.js`, `js/add_roast_layout.js`, `js/add_roast_live.js`, `js/profile_wizard.js`. `add_roast.html` went from 628 to 141 lines and `profile_form.html` from 243 to 127. The code moved verbatim except two Jinja lines, which became a `roast-config` JSON data island that `add_roast_live.js` reads — the pattern T-04/T-05 will extend. The stylesheet `<link>` stays at the original in-body position so the CSS cascade order is unchanged; `base.html` was not touched.
- **R3 — housekeeping.** Removed the unused `src/` "Hello" stub, `[build-system]`, and the `[project.scripts]` entry (which already failed with `ModuleNotFoundError: No module named 'app'`); wrote a real description and README. `uv.lock` changed by one line (`editable` → `virtual`).
- **Verified:** 173 tests pass unchanged via `pytest` and `uv run pytest`; each extracted file re-checked line-for-line against the original; a headless-Chromium click-through (chart data, timer, first-crack button, wizard output for two input sets, console errors) matched the pre-refactor baseline exactly; screenshots of four pages were pixel-identical; `uv sync` and `uv run python app.py` work.
- **Deploy note:** on PythonAnywhere this is `git pull` and Reload; `static/` needs no extra mapping (see `DEPLOY.md`).
- **Still deferred:** splitting `app.py` into Flask Blueprints (revisit once it passes roughly 900 lines after T-03), and moving the modules into a `coffeeroaster04/` package (needs a coordinated WSGI and `DATA_DIR` change).

---

## T-02 [PLANNED] Populate `data/roasters.json` with per-roaster values

**Depends on:** none (data + research only; can run alongside T-03 prep).
**Goal:** every one of the 47 entries carries a full, explicit set of values (Settled #5). Split into two passes so research effort follows need.

**Provenance rule.** Each entry has `calibrated` (true only where real logged roasts back it — SR800 only), `sources` (URLs), and `notes`. Prefer primary documents (manuals, Sweet Maria's tip-sheet PDFs, which download fine even though their web pages block fetching). Values taken from secondary sources are marked in `notes`. Where no source exists, leave the value `null`, never a guess; `null` falls back to the legacy default for that field. Identical numbers across roasters are fine, but don't make identical numbers look like measurements: use `notes` to say "same as X by design/assumption".

### T-02a — Tier 1 fields (needed by T-03)
- [ ] Define the schema in `SPEC.md` and add a data-validation test (below).
- [ ] Fill for all 47 entries:

| Field | Meaning |
|---|---|
| `type` | Descriptive label only (e.g. "fluid bed", "drum") — not used to inherit anything |
| `calibrated`, `sources`, `notes` | Provenance (above) |
| `green_weight_min_g`, `green_weight_max_g`, `green_weight_recommended_g` | Batch limits and hint |
| `roast_time_min_s` | Shortest plausible roast |
| `first_crack_min_s` | Earliest plausible first crack (today's global 240 s floor is wrong for fast roasters) |
| `profile_grid_minutes` | Number of profile rows, one per whole minute; also the maximum roast time in minutes (Settled #13). **Required, never null.** |
| `temp_unit` | `"F"` or `"C"` (Settled #12). **Required, never null.** |
| `temp_source` | `bean_probe` / `inlet_air` / `chamber_air` / `unspecified` / `none` |
| `has_temp_readout` | false → hide the temperature grid; the target first-crack and development-time fields are unaffected |
| `temp_min`, `temp_max` | Sanity range in the roaster's own unit (replaces the global 60–500 °F) |

Finished weight needs no per-roaster field: the domain rule is `0 < finished < green` (replacing the global ≥ 100 g floor, which rejects a full SR540 batch and any IKAWA roast).

### T-02b — Tier 2 fields (needed by T-04/T-05/T-06)
- [ ] Fill for all 47 entries:

| Field | Meaning |
|---|---|
| `start_model` | `ramp` / `preheat_charge` / `programmed` / `none` — what the live chart's opening looks like |
| `chart_start_temp`, `chart_inflection_min`, `chart_inflection_temp` | Live-chart anchors (SR: 145 °F, 0.5 min, 270 °F) |
| `preheat_temp`, `charge_temp` | Drum roasters; null otherwise |
| `controls` | List of `{name, min, max}` (e.g. Fan 1–9, Heat 1–9) |
| `cooling` | `internal` / `external_tray` / `manual` |
| `cooling_coast_seconds` | How much the roast keeps developing after cooling starts |
| `min_gap_between_roasts_min` | e.g. SR540 manual: 30 |
| `wizard` | `{time_to_first_crack_s: {low, medium, high}, natural_time_adjust_s, dtr_by_level: {six tiers}, profile_start_temp, default_first_crack_temp}` |

**SR800 — what is already known** (illustrative; each value is confirmed before it is written):

| Field | Value | Basis |
|---|---|---|
| `profile_grid_minutes` | 12 | Your statement (10 min longest roast + buffer) |
| `calibrated` | true | One real logged roast (medium/washed: 6:15 first crack, 1:10 development, Full City) |
| `temp_unit` | F | SR540 manual: display is °F; SR800 is the same family — confirm |
| `chart_*` | 145 / 0.5 / 270 | Existing `static/js/add_roast_live.js` constants |
| `wizard.time_to_first_crack_s` | 375 / 375 / 405 | Existing `static/js/profile_wizard.js` (`MAILLARD_TIME_SECONDS`) |
| `wizard.natural_time_adjust_s` | 20 | Existing `static/js/profile_wizard.js` |
| `wizard.dtr_by_level` | 0.12 / 0.13 / 0.16 / 0.18 / 0.20 / 0.23 | Existing `static/js/profile_wizard.js` (`ROAST_LEVEL_DTR`) |
| `wizard.profile_start_temp`, `default_first_crack_temp` | 315, 400 | Existing `static/js/profile_wizard.js` |
| `green_weight_max_g` | TBD | Retailer spec: 226 g (½ lb); your logged roasts: about 202 g |
| `roast_time_min_s`, `first_crack_min_s` | TBD | Legacy constants are 240 s; confirm from your own roasts |

**Files touched:** `data/roasters.json`, `SPEC.md`, a generator script kept out of the repo root if we use one.
**Tests (new):** every roaster has every required key; `green_weight_min_g < green_weight_max_g`; recommended lies within the min/max; `temp_min < temp_max`; `profile_grid_minutes >= 1`; `temp_unit` ∈ {F, C}; `calibrated` is false for everything except SR800; every `sources` entry is a URL. This is the guard against a typo silently breaking one roaster.
**Ops note:** `roasters.json` is loaded once at startup, so on PythonAnywhere an edit needs `git pull` and a web-app reload.
**Done when:** the 47 entries validate, provenance is recorded, and `null` is used wherever a value couldn't be sourced.

---

## T-03 [PLANNED] Roaster required and locked; limits, units, and grid driven by roaster data

**Depends on:** T-01 ✓ and T-02a.
**Goal:** the profile and Add Roast flows read their limits, units, and grid length from the profile's roaster, and no code path assumes 12 rows or °F.

**Tasks**
- [ ] **New `roasters.py`** (pure functions, no Flask): `settings_for(roaster_id)` returns that roaster's values with per-field fallback to today's constants when the id is unset, unknown, or a field is `null` (Settled #8). Also holds the `TEMP_UNITS` table (Settled #12).
- [ ] **`validators.py`:** add optional limit arguments to `validate_green_weight`, `validate_finished_weight`, `validate_roast_time`, `validate_first_crack`, `validate_temperature`, and the two target-time validators. Defaults equal today's constants, so every existing call and test is untouched. With limits supplied, finished weight uses `0 < finished < green`, and the roast-time maximum is the roaster's row count (Settled #13; inclusive, so 12 rows accepts 12:00). Error messages are built from the limits; the legacy wording is kept verbatim for the default path (no existing test asserts these strings — checked).
- [ ] **`calculations.py`:** `calculate_weight_loss` and `calculate_development_time` carry duplicate hard-coded guards (100–300 g; total ≥ 240 s). Give them optional limit arguments defaulting to the current values. Do not delete the guards: existing tests assert they raise. Formulas are unchanged (SPEC constraint).
- [ ] **`app.py`:** remove the eight hard-coded "12" sites (lines ~420–422 in `roast_detail`, ~494/495/503 in `add_roast`, ~614/615 in `add_edit_profile`). New profile or new roast → length from the roaster. Existing profile or record → length from its stored list, so old 12-entry data keeps rendering even if a roaster's grid is later retuned. When a roaster's grid is longer than a stored profile, pad with blanks and never truncate non-empty values.
- [ ] **Startup migration** (Settled #8): idempotent, saves only when something changed, unit-tested.
- [ ] **Profile form:** roaster required on create; on edit it renders as read-only text, not a select. Server side, reject any attempt to change it.
- [ ] **Add Roast:** show the allowed ranges as hints (e.g. "Recommended 226 g; allowed 100–226 g"); temperature column header and hints use the roaster's unit and probe type; hide the temperature grid when `has_temp_readout` is false.
- [ ] **Records:** snapshot `roaster_id` and `temp_unit`; `roast_detail` shows the roaster and what its temperature measures.
- [ ] **Units (Settled #12):** templates and the JS config take symbols, labels, and chart-axis settings from `TEMP_UNITS`; add the guard tests listed under "Temperature units — how Settled #12 is implemented".
- [ ] **JS:** the three hard-coded 12s in the live chart (`x <= 12`, axis `max: 12`, elapsed clamp) and the literal `°F` in the readouts of `static/js/add_roast_live.js` come from the config island.

**Files touched:** `roasters.py` (new), `validators.py`, `calculations.py`, `app.py`, `templates/profile_form.html`, `templates/add_roast.html`, `templates/roast_detail.html`, `static/js/add_roast_live.js`, `SPEC.md`.

**Existing tests changed by this item — approved 2026-09-19** (they encode "roaster optional", which Settled #1–3 and #9 reverse):
- `test_post_new_profile_creates_and_redirects` and `test_post_new_profile_defaults_to_not_favorite` — POST `/profiles/new` with no roaster; they gain a `roaster_id` in the form data.
- `test_form_lists_roasters_alphabetically_with_a_blank_default` and `test_post_new_profile_without_roaster_stores_none` (both added in Phase 11) — assert the blank "No roaster selected" default and `roaster_id: None`; they are replaced by "required" tests.
- `test_post_new_profile_invalid_shows_error_and_preserves_input` — posts an empty name with no roaster; it stays valid only if the name is still validated first, so the roaster check must come after it (keep that order). No edit expected.
- Not affected (verified by grep): the three edit-profile tests, all Add Roast tests, and all `test_units.py` validator/calculation tests, because the roaster-less fallback (Settled #8) and the default-argument design keep them valid.

**Tests (new):** per-roaster limits accepted/rejected (using synthetic fixture roasters — a 60 g batch, a 454 g batch, a 3:30 roast — not real roaster data); roast time exactly at the row count is accepted and one second over is rejected; a 20-row grid renders, saves, and displays; roaster locked on edit; record snapshots roaster and unit; records with 12 stored entries still render under a longer-grid roaster; migration assigns SR800 once and is a no-op the second time; the temperature-unit guards, with an F and a C fixture roaster.
**Done when:** the full suite passes; a profile for a synthetic fixture roaster with a 20-row grid can be created and roasted end to end; a °C roaster's pages show no °F anywhere.

---

## T-04 [PLANNED] Data-driven profile wizard

**Depends on:** T-02b, T-03.
**Goal:** the wizard's hard-coded constants (`MAILLARD_TIME_SECONDS`, `NATURAL_TIME_ADJUST_SECONDS`, `ROAST_LEVEL_DTR`, `PROFILE_START_TEMP`, default first-crack temp, the 12-row loop in `static/js/profile_wizard.js`) come from the roaster's `wizard` values and grid length.

**Tasks**
- [ ] Add a JSON config island to `profile_form.html`, modeled on Add Roast's `roast-config` (the wizard script had no Jinja, so it has none yet). The wizard reads the roaster's values from it: on load for a locked roaster, and on selection change for a new profile.
- [ ] `calibrated: false` → show a plain notice ("Estimated for this roaster — not calibrated; expect to adjust") rather than hiding the wizard (Settled #6: targets are inferred for now).
- [ ] Grid loops use the roaster's `profile_grid_minutes`; clamp the computed first-crack minute to it.
- [ ] Update the SPEC Profile Wizard text, which currently describes the Fresh-Roast-only constants.

**Tests:** no JS test harness exists in the repo (see T-09). Add server-side tests that the config island carries the right values per roaster, plus a browser check before commit.
**Done when:** the SR800 wizard output is identical to today's (the baseline values are recorded in the T-01 verification: default inputs → `315,343,366,383,394,400`, FC 6:15, dev 1:11), and a non-SR roaster produces values from its own entry with the notice shown.

---

## T-05 [PLANNED] Data-driven Add Roast live panel

**Depends on:** T-02b, T-03.
**Goal:** the live chart, timer, and pull countdown follow the roaster.

**Tasks**
- [ ] Chart anchors and opening shape follow `start_model` and the `chart_*` values (today's 145 °F / 270 °F-at-30 s ramp becomes the `ramp` case; `preheat_charge` starts at the charge temperature and dips to a turning point; `programmed` and `none` draw no synthetic ramp).
- [ ] Axis unit label, RoR unit, y-axis bounds/step, and x-axis length follow the roaster (via `TEMP_UNITS`, Settled #12).
- [ ] Pull countdown subtracts `cooling_coast_seconds`.
- [ ] Optional back-to-back warning from `min_gap_between_roasts_min` (informational only).

**Done when:** the SR800 panel behaves identically to today's; another roaster's panel reflects its own values.

---

## T-06 [PLANNED] New Add Roast fields, shown per roaster

**Depends on:** T-05. Schedule after real use of T-03–T-05 shows which of these earn their place.
**Candidates, roughly in value order:**
1. Start condition (cold / warm / preheated) and ambient temperature — the Gene Cafe tip sheet says warm starts, ambient, and line voltage each shift roast time by up to a minute.
2. Charge temperature and turning point (time, temperature) — for `preheat_charge` roasters.
3. Control changes: timestamped fan/heat/drum adjustments, using the roaster's `controls` list. On dial-driven machines the temperature curve is an outcome and the dial sequence is the repeatable part; a profile-side `control_plan` would mirror this.
4. Cooling start time.

Each gets its own SPEC entry and its own commit; fields not applicable to a roaster don't appear.

---

## T-07 [DEFERRED] Roaster-native profile structures and import/export

Program-driven roasters take profiles in their own shape — IKAWA (up to 6 inlet-temperature points and 3 airflow points over ≤ 12 min), Kaffelogic (temperature curve + fan curve + an end-of-roast "level"), Gene Cafe (multi-stage setpoints). Representing those natively, or importing/exporting Artisan/Kaffelogic/IKAWA files, is a large step and overlaps the existing Deferred Ideas in `SPEC.md`. Revisit only after T-03–T-05 have real users on more than one roaster.

## T-08 [PLANNED] Calibration feedback loop

**Depends on:** T-03 (records carry `roaster_id`), plus real data.
Add a read-only report script (not a web feature) that summarizes logged roasts per roaster — time to first crack, development ratio, weight loss, temperature at first crack — to compare against each roaster's stored values. When a roaster has enough consistent data, tune its entry and flip `calibrated` to true. This is how values for non-SR800 roasters get refined from user data (Settled #6).

## T-09 [PLANNED] Keep a browser regression check in the repo

**Depends on:** none; most useful before T-04/T-05, which change the JS's behavior.
There are no JS tests, and T-01's verification showed how much that matters: a headless-Chromium script (no new dependency beyond a Chromium binary and Node's built-in WebSocket) that loads Add Roast and the profile form, clicks Start / First Crack / Reset and the wizard, and records the resulting chart data, readouts, and console errors, then diffs the result against a stored baseline. A working prototype exists from T-01, but it lives in a scratch directory that is deleted with the session. Options: commit it under `tests/browser/` as an optional check that skips itself when Chromium isn't installed, or keep it out of the repo and rebuild it when needed. Your call.

---

## Suggested order

T-01 ✓ → T-02a (research) → T-03 → T-02b → T-09 (recommended before) → T-04 and T-05 → T-06 as warranted → T-08 once data exists. T-07 stays deferred.
