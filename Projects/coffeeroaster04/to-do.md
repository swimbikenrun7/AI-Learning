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

## T-02 [COMPLETE] Populate `data/roasters.json` with per-roaster values

**Depends on:** none (data + research only; can run alongside T-03 prep).
**Goal:** every one of the 46 entries carries a full, explicit set of values (Settled #5). Split into two passes so research effort follows need.

**Provenance rule.** Each entry has `calibrated` (true only where real logged roasts back it — SR800 only), `sources` (URLs), `inferred` (the fields whose value is not directly stated by a source), and `notes`. Prefer primary documents (manuals, manufacturer and Sweet Maria's tip-sheet PDFs, which download fine even though their web pages block fetching); read the raw text, not a page summarizer's paraphrase, which invented details more than once. Where a value cannot be sourced it is inferred by the rules in `SPEC.md` ("Roaster data") and listed in `inferred`, never presented as measured; a value that is optional and has no basis (e.g. the roast-time floor) stays `null` and falls back to today's constant. Identical numbers across roasters are fine, but don't make identical numbers look like measurements: use `notes` to say so.

### T-02a — Tier 1 fields (needed by T-03) — [COMPLETE]

Completed 2026-09-19 · commit `b9fbb58` on branch `roaster-selection`.
- [x] Schema defined in `SPEC.md` ("Roaster data (Tier 1)", including the rules for values).
- [x] All 46 entries filled, each with its own explicit values, source URLs, an `inferred` list, and notes.
- [x] `tests/test_roasters_data.py` (11 tests): required keys, batch ranges, row counts, time floors, unit/readout consistency, provenance, only-SR800-calibrated, SR series = 12 rows. Each guard was checked against deliberately broken copies of the data. Suite: 184 passing.

| Field | Meaning |
|---|---|
| `type` | Descriptive label only (e.g. "fluid bed", "drum") — not used to inherit anything |
| `calibrated`, `sources`, `inferred`, `notes` | Provenance (above) |
| `green_weight_min_g`, `green_weight_max_g`, `green_weight_recommended_g` | Batch limits and hint (recommended may be `null`) |
| `roast_time_min_s`, `first_crack_min_s` | Shortest plausible roast / earliest plausible first crack; `null` = today's 240 s. Set only for IKAWA Pro and the Roest L200 Ultra, whose normal roasts are shorter |
| `profile_grid_minutes` | Number of profile rows, one per whole minute; also the maximum roast time in minutes (Settled #13). Required |
| `temp_unit` | `"F"` or `"C"` (Settled #12); `null` when there is no readout |
| `temp_source` | `bean_probe` / `inlet_air` / `chamber_air` / `unspecified` / `none` |
| `has_temp_readout` | false → `temp_source` is `none`, unit and range are `null`, and the temperature grid is hidden; the target first-crack and development-time fields are unaffected |
| `temp_min`, `temp_max` | Sanity range in the roaster's own unit (IKAWA's is higher: inlet air reaches 290 °C) |

**Result.** Manuals, manufacturer pages, or tip sheets back the batch sizes and temperature behavior of the Fresh Roast SR series, Gene Cafe, Behmor, Hottop, Quest, Aillio R1/R1 V2, IKAWA, Kaffelogic, Sandbox, and Roest. Retailer listings and reviews back Kaleido, Kaldi, Nesco, Huky, the poppers, the Whirley-Pop, and the ceramic roasters. Row counts are inferred for every roaster except the SR series (your rule), from the longest normal roast the sources describe: Gene Cafe 25, Behmor 28, Hottop 24–27, Quest 24, Kaldi/Kaleido/Huky 17, Sandbox 18–22, IKAWA 14, Kaffelogic/Roest/poppers/ceramics 12, Nesco 32.
Low-confidence entries are flagged in their `notes`: Huky 500T, Presto PopLite, Zenroast (little or no model-specific source); Aillio R2 and R2 Pro (copied from the R1 V2 page); Behmor 2000AB Plus (copied from the 1600AB Plus manual).

**For you to confirm**
1. **SR800 limits:** minimum 113 g (the retailer's stated 4 oz) and maximum 227 g (8 oz washed; naturals are 170 g, and the natural limit is not enforced separately). Your logged roasts (about 202 g) fit.
2. **SR800 rows:** the retailer text says total roast 8–18 min and a timer up to 20 min. I kept your 12 rows; this is the one place a source contradicts your rule.
3. **SR300/SR340/SR500 have no temperature readout** in their sources, so after T-03 their profile form hides the temperature grid (target first crack and development time remain). If people use an external probe on these, that needs a decision (an override).
4. **Removed "Bohemia 250 (ceramic stovetop)"** (list is now 46): it appeared only in a retailer blog post that contradicted that retailer's own product pages, and no other source exists. If you have a real product in mind, give me the actual name.
5. **Kaffa is the export brand of the same Seoul maker as Kaldi** (Kaldi Wide400 = Kaffa Wide400, 400 g; Wide POP, 300 g). The list has only Kaldi Mini and Kaldi Wide; adding the Wide400 and Wide POP is optional and not done.


Finished weight needs no per-roaster field: the domain rule is `0 < finished < green` (replacing the global ≥ 100 g floor, which rejects a full SR540 batch and any IKAWA roast).

### T-02b — Tier 2 fields (needed by T-04/T-05/T-06) — [COMPLETE]

Completed 2026-09-19 · **not yet committed** — awaiting your review. Suite: 293 passing (was 284).
- [x] Schema and rules written into `SPEC.md` ("Roaster data (Tier 2)").
- [x] All 46 entries filled: `start_model`, `preheat_temp`, `charge_temp`, `controls`, `cooling`, `cooling_coast_seconds`, `min_gap_between_roasts_min`, `wizard` (the three chart-anchor fields were done in T-03). Wizard sub-fields are listed in `inferred` by dotted name (e.g. `wizard.dtr_by_level`).
- [x] Tier 2 tests added to `tests/test_roasters_data.py` (start model vs readout and anchors, preheat/charge within range, control shape, cooling, gap, wizard shape and consistency, SR-only table, and a drift guard that fails if the SR800's wizard data differs from the constants actually in `profile_wizard.js`). Each guard was checked against 14 deliberately broken copies of the data.

**What is stated and what is inferred**
- **SR800:** fully stated (the owner's calibrated wizard values; retailer controls and cooling). Its only inferred fields are the temperature range and the 30-minute gap.
- **Stated by a source:** cooling and controls for the Fresh Roast SR series, Gene Cafe (setpoint and time ranges), Behmor (1-hour gap, P1–P5 power), Hottop (167 °F preheat beep, ranges, cooling tray), Quest (150 °C preheat, back-to-back, 205 °C first crack), Aillio (power/fan/drum 0–9, preheat 230 °C, 1–2 min between batches), Kaffelogic (roast level 0.1–5.9, no gap, 205 °C first crack, the 7:30 example), Sandbox (percent controls), and the SR540's 30-minute gap. First-crack *times* are stated for Kaffelogic, Hottop, Kaldi, and Sandbox R1.
- **Inferred (flagged):** all other first-crack times (typical Full City time × 0.79), the published DTR table for every non-SR roaster, the start model for Gene Cafe and Behmor, and everything for Kaleido, Roest, and Huky beyond their cooling trays.
- **Left `null` on purpose:** `cooling_coast_seconds` for all 46 (no source gives a number); `wizard.profile_start_temp` for everyone but the SR family; `default_first_crack_temp` except where stated (SR family, Hottop B-2K/P-2K, Kaffelogic, Quest, Sandbox); `preheat_temp`/`charge_temp` unless stated. The 12 no-readout roasters have `wizard: null` and `start_model: "none"`.

**Decision for T-04.** For every roaster except the SR family, the wizard has first-crack and development-time estimates but **no start or first-crack temperature**, so it cannot draw a temperature curve without borrowing numbers from another machine. T-04 should offer those roasters a times-only wizard (target first crack and development time) with the "estimated, not calibrated" notice, and the temperature curve only where the data supports it. Say if you'd rather I infer temperatures too.

**Files touched:** `data/roasters.json`, `SPEC.md`, `tests/test_roasters_data.py`.
**Ops note:** `roasters.json` is loaded once at startup, so on PythonAnywhere an edit needs `git pull` and a web-app reload.
**Done when:** met — 46 entries validate, provenance is recorded, and `null` is used wherever no source gives a value.

---

## T-03 [COMPLETE] Roaster required and locked; limits, units, and grid driven by roaster data

Completed 2026-09-19 · commit `e01d917` on branch `roaster-selection` (not yet merged to `main`). 273 tests passing (was 184 at the start of T-03), verified on the commit in isolation.

**What now works**
- **Choose the roaster first.** `/profiles/new` asks which roaster (an alphabetical dropdown, no default); the profile form for that roaster follows. The roaster is then shown read-only and is locked: an edit that tries to change it gets a 400. Add Roast has no roaster override.
- **Rows, limits, and units come from the roaster.** A profile has one row per minute of its roaster's grid (never truncated; padded if the grid grew). Max roast time = the profile's row count (12 rows → 12:00 accepted, 12:01 rejected); target first-crack/development times obey the same cap. Green weight, finished weight (now just `> 0` and `≤ green`), roast-time and first-crack floors, and the temperature range are the roaster's own, with the allowed ranges shown as hints on Add Roast.
- **Units.** Every temperature is stored and shown in the roaster's own unit, never converted. All unit text comes from `roasters.TEMP_UNITS`; the live chart's axis titles, tooltips, and readouts, the roast detail charts, and every table header use it. A guard test (`tests/test_no_hardcoded_units.py`) fails if a unit literal appears in any template, script, or module; run against the pre-T-03 code it finds all 17.
- **No-readout roasters** show no temperature grid, temperature entry, chart, or temperature readout; the target times, timer, First Crack button, and pull countdown work as before.
- **Records snapshot the roaster.** Each saved roast stores `roaster_id` and `temp_unit`; the detail page shows the roaster and uses the record's own unit and row count. Saved records are never re-validated for display (a 60 g or 3:30 roast would otherwise trip the original guards).
- **Startup migration** (Settled #8): profiles and records with no roaster get the SR800 (records take their profile's roaster first) and a `temp_unit`; idempotent, rewrites only when something changed. Verified end to end on old-format data files, including a second start that changed nothing (`DEPLOY.md` notes it).
- **Original limits still apply** to a profile with no roaster (or an unknown roaster id), so the earlier tests and any stray legacy profile behave exactly as before.

**Decisions made while building (all in `SPEC.md`, "Roaster-driven profiles")**
1. **Two-step profile creation.** Because the row count depends on the roaster, the roaster is picked on its own page first instead of a dropdown on the form. This changed three existing Phase 11 tests beyond the four you approved; you approved those three separately (see below).
2. **Chart anchors pulled forward from T-02b.** The live chart's opening (145 / 0.5 min / 270) is °F-specific, so it is now per-roaster data in the roaster's own unit: set for SR540, SR700, SR800; `null` for everyone else, which means no synthetic ramp (the curve starts flat at the first target). SR300/340/500 have no readout, so no chart at all. Without this a °C roaster would have been drawn on a °F-numbered ramp.
3. **The wizard is offered only for a `calibrated` roaster** (the SR800), since its constants are °F and calibrated for that machine. T-04 makes it data-driven.
4. **Max roast time uses the profile's own row count** rather than the roaster's current grid, so a roast can never run past the rows that describe it even if a roaster's grid is later retuned.
5. **Error messages are built from the limits** ("between 113 and 227 grams", "between 04:00 and 12:00"); the wording changed slightly from "greater than X and less than Y". No test depended on the old text.

**Existing tests changed** (all approved): the four listed earlier (`test_post_new_profile_creates_and_redirects` and `..._defaults_to_not_favorite` gained a `roaster_id`; the blank-default and stores-None tests were replaced by "asks for a roaster first" and "a roaster is required"), plus three approved on 2026-09-19 because they asserted what Settled #7 reverses: `test_edit_form_preselects_the_saved_roaster` → shows the roaster read-only; `test_post_edit_can_change_the_roaster` → an attempt is rejected (400); `test_roaster_dropdown_sits_above_the_wizard_and_is_tied_to_the_form` → the chosen roaster is carried into the form with no dropdown. No other existing test changed.

**Verified in a real browser** (headless Chromium, before/after): the SR800 Add Roast, timer, First Crack, wizard (two input sets), and profile pages match the pre-T-03 baseline on every recorded value with no console errors. A °C roaster shows `°C` on both axes and readouts and starts flat; a 25-row Gene Cafe profile gets 25 rows and a 25-minute axis; a no-readout roaster hides the chart but its timer and First Crack button work.

**Known interim limits (by design; later items fix them)**
- Non-SR roasters have no chart opening, so a curve starts flat and its rate-of-rise line spikes when it first climbs; T-05 gives each roaster a proper `start_model`.
- The wizard is SR800-only (T-04).
- SR300/340/500, the poppers, Nesco, Whirley-Pop, and the ceramic roasters have no temperature grid at all (they have no readout); if people use external probes there, that needs an override.
- Roasters do not yet appear on the `/roasts` list or CSV export.

**Files:** `roasters.py` (new), `validators.py`, `calculations.py`, `app.py`, `templates/{choose_roaster,profile_form,add_roast,roast_detail}.html`, `static/js/{add_roast_live,profile_wizard}.js`, `data/roasters.json` (chart anchors), `SPEC.md`, `DEPLOY.md`; tests: `test_roasters.py`, `test_limits.py`, `test_roaster_profiles.py`, `test_roaster_roasts.py`, `test_no_hardcoded_units.py` (new) and the seven edits above.

---

## T-04 [PLANNED] Data-driven profile wizard

**Depends on:** T-02b ✓, T-03 ✓. **Starting point after T-02b:** every readout roaster has a `wizard` block; only the SR family has start and first-crack temperatures (see the T-02b decision above). **Starting point after T-03:** the wizard is offered only for a `calibrated` roaster (the SR800); this item removes that gate.
**Goal:** the wizard's hard-coded constants (`MAILLARD_TIME_SECONDS`, `NATURAL_TIME_ADJUST_SECONDS`, `ROAST_LEVEL_DTR`, `PROFILE_START_TEMP`, default first-crack temp, the 12-row loop in `static/js/profile_wizard.js`) come from the roaster's `wizard` values and grid length.

**Tasks**
- [ ] Add a JSON config island to `profile_form.html`, modeled on Add Roast's `roast-config` (the wizard script had no Jinja, so it has none yet). The wizard reads the roaster's values from it: on load for a locked roaster, and on selection change for a new profile.
- [ ] `calibrated: false` → show a plain notice ("Estimated for this roaster — not calibrated; expect to adjust") rather than hiding the wizard (Settled #6: targets are inferred for now).
- [ ] Grid loops use the roaster's `profile_grid_minutes`; clamp the computed first-crack minute to it.
- [ ] Update the SPEC Profile Wizard text, which currently describes the Fresh-Roast-only constants.

**Tests:** server-side tests that the config island carries the right values per roaster, and the browser check (`tests/browser/`, T-09) extended for whatever the wizard now does; it currently pins the SR800 wizard's output, so a deliberate change to those numbers means updating its expected values.
**Done when:** the SR800 wizard output is identical to today's (the baseline values are recorded in the T-01 verification: default inputs → `315,343,366,383,394,400`, FC 6:15, dev 1:11), and a non-SR roaster produces values from its own entry with the notice shown.

---

## T-05 [PLANNED] Data-driven Add Roast live panel

**Depends on:** T-02b ✓, T-03 ✓. **Starting point after T-02b:** `start_model` is set for every roaster (`ramp` only for the SR machines and the Gene Cafe/Behmor guesses; `preheat_charge` and `programmed` elsewhere), `preheat_temp`/`charge_temp` exist only where stated, and `cooling_coast_seconds` is `null` everywhere, so the pull countdown should treat `null` as zero.
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

## T-09 [COMPLETE] Keep a browser regression check in the repo

Completed 2026-09-19 · commit `22976f0` on branch `roaster-selection`. Suite: 284 passing (11 of them the browser check), about 8.5 s in all.
The scratch prototype from T-01/T-03 became `tests/browser/`, committed as an automatic check that skips itself when it can't run.

- **How it works.** `test_browser.py` writes fixture profiles and records, starts the real app on them (`serve.py`, with a session injected and the project's real data untouched), launches headless Chromium, and runs `driver.mjs` (Node's built-in WebSocket; no npm packages, no build step). The driver only observes; the Python test asserts, so a failure says what is wrong and there is no golden file to go stale. No pixel screenshots (they differ across machines).
- **What it covers.** Add Roast for the SR800, a °C roaster, a 25-row roaster, and a no-readout roaster: chart data and opening, axis titles, units, row counts, hints, timer, First Crack button, pull countdown, date field, reset, and a clean console. The SR800 wizard's output for two input sets; the edit page (locked roaster, no wizard); the choose-a-roaster-first flow; and the roast detail charts and tables in each record's unit. Three of these were never browser-checked before: the pull countdown, the chooser, and the detail page's charts.
- **When it runs.** Automatically with `pytest` when Chromium/Chrome, Node 22+, and the Chart.js CDN are all reachable; otherwise skipped with the reason (`-rs` shows it). `SKIP_BROWSER_TESTS=1` skips it on purpose. About six seconds.
- **Checked against breakage.** Seven deliberate regressions in a scratch copy were each caught by the intended test: a hard-coded °F in the readout, an x-axis stuck at 12, the chart opening ignored, a changed countdown text, a changed wizard constant, a hard-coded °F title on the detail page, and a script error on load.
- **Bugs found while building it (all in the check itself):** the first chooser test clicked the header's Log out button because it matched the first submit button on the page; a stale-frame race that made my earlier check read the pull countdown too early (it now waits for it).
- **Files:** `tests/browser/{test_browser.py,serve.py,driver.mjs}`, `README.md` (a "Browser check" section), `SPEC.md` (one constraint).
- **Limits:** it needs a system Chromium and Node, so a machine without them (or offline) silently skips it; a browser-version change could in principle move a chart value, so numeric checks use tolerances.

---

## Suggested order

T-01 ✓ → T-02a ✓ → T-03 ✓ → T-02b ✓ → T-09 ✓ → T-04 and T-05 → T-06 as warranted → T-08 once data exists. T-07 stays deferred.
