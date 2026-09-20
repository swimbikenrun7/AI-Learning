# To-Do — Crackle (coffeeroaster04)

A running list of planned feature updates and their detailed plans.

**How this file relates to the others**
- `SPEC.md` is the source of truth for *what the app must do* (requirements, constraints, domain rules). This file is *how and in what order* we get there. When an item is completed, its resulting requirements are written into `SPEC.md`, and the item here is collapsed to a short summary.
- Nothing here is implemented until its status says so. Human review of `git diff` before every commit is part of the process (see `CLAUDE.md`).

**Status tags**
`[PLANNED]` · `[IN PROGRESS]` · `[PARTLY COMPLETE]` (an item with several parts, some built) · `[COMPLETE]` (with date and commit) · `[DEFERRED]` (considered, deliberately not scheduled)

**Item template** — each item has: Status · Depends on · Goal · Tasks (checkboxes) · Files touched · Tests · Done when. Tick a task's box as it lands; when every box is ticked and the suite passes, change the tag to `[COMPLETE]`, add the date and commit, and collapse the detail to a paragraph.

---

## Current status (as of 2026-09-19)

- **Branches.** `roaster-selection` was merged into `main` by fast-forward (no merge commit, matching `main`'s linear history) and pushed. Since then `origin/main` is at `ab0316b` (docs), and local `main` is one commit ahead (`1d0638d`, the T-11 to T-14 queue). T-11 is committed on `mobile-optimization` (`2ff59ad`, `64a1b3d`) and T-12 is committed on `versioning` (`b18b677`), cut from it (so it includes T-11); T-13 is built on `espresso-style`, cut from `versioning`; none of the three is merged to `main`. The old `roaster-selection` branch still exists locally and can be deleted (`git branch -d roaster-selection`). Whether PythonAnywhere has pulled and reloaded this is not recorded here; before its first reload, back up `data/` (the startup migration rewrites the profile and record files once; see `DEPLOY.md`).
- **Tests.** 398 passing on `main`, 409 on `mobile-optimization`, 432 on `versioning`, 483 on `espresso-style`, including the browser check (22, 30, 31, and 34 tests; about 10 s; it skips itself without Chromium, Node 22, or the CDN). `ruff check`/`ruff format --check` are clean on every file added in this work; the 18 remaining `ruff check` findings (naive `datetime` calls and unused unpacked variables) and the unformatted `app.py` and `tests/test_app.py` were there before it started and are left for you to review.
- **Done:** T-00 through T-06 (1: start condition + ambient temperature), T-08 (calibration report), T-09 (browser check), T-10 (review follow-ups). Commit hashes are in each item.
- **Not yet done or decided:**
  - The calibration report has only run on synthetic records; run it on your real SR800 roasts (see T-08) before trusting the thresholds.
  - `validate_green_weight("nan")` and `validate_temperature("nan")` accept NaN (found during T-06, not fixed; see Open decisions).
  - **T-11 mobile optimization is built and committed** (`2ff59ad`) on `mobile-optimization`; it still needs a test on your phone. **T-12 version and release notes is built and committed** (`b18b677`) on `versioning`. **T-13 espresso style is built** on `espresso-style` (uncommitted, awaiting your review and, ideally, your own espresso numbers). **Queued, not started:** T-14 how-to/tutorial.
  - Unscheduled: T-06 candidates 2–4 (charge/turning point, control-change log, cooling start) and T-07 (native profile formats, deferred).
  - `app.py` is 879 lines, so the Blueprint split (T-01, "revisit once it passes roughly 900 lines") is still not due.

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
14. **The SR800's 30-minute gap between roasts is confirmed by the owner** (2026-09-19 review), so it is stated data: Add Roast shows the reminder "this roaster needs at least 30 minutes between roasts". The other SR models' 30 minutes stay assumed and unshown, except the SR540, whose manual states it.
15. **Roasters with no temperature readout stay grid-less until someone needs otherwise** (SR300/340/500, the poppers, Whirley-Pop, Nesco, the ceramics). An opt-in "I use an external probe" per profile (with a unit choice) was considered and deferred; revisit only when a real user with a probe on one of these appears.
16. **Roast records show their roaster in the `/roasts` list and the CSV export** (a Roaster column right after Roast Profile; done 2026-09-19).
17. **Next, in this order: T-06 start condition + ambient temperature, then T-08 (calibration report).** Both are done. Not selected: the T-06 control-change log. Afterwards `roaster-selection` was merged into `main` and pushed (2026-09-19).

## Open decisions

Nothing is blocking. These are the defaults I'm assuming from the 2026-09-19 review — say if you object to any and I'll reverse it:

- **The wizard is times-only for every roaster without start and first-crack temperatures** (all but the SR family), rather than inferring temperatures (the T-02b/T-04 decision).
- **The SR800 keeps 12 rows** even though its retailer says roasts run 8–18 minutes (your rule: about 10 minutes is the longest anyone roasts).
- **The SR800's 170 g cap for natural coffees is not enforced** (only its 113–227 g range is); the app can't tell which coffees are naturals reliably, since process is optional free text.
- **"Bohemia 250" stays removed** and **the Kaldi Wide400 / Wide POP (Kaffa) are not added** to the list.
- **The `/roasts` search still matches only bean, profile, and date**, not the new roaster column.
- **The rate-of-rise dot at exactly t = 0 keeps showing half the true slope** on ramp and charge curves (how the SR800 has always behaved) rather than changing the SR800's initial readout.
- **T-06's three choices stand** (details in T-06): ambient is entered in the roaster's own unit; all three start options are offered for every roaster; the two fields show on the roast detail page only, not the list or CSV.
- **T-08's "enough consistent data" thresholds are mine** — at least 5 roasts with first-crack times within 60 s of each other (two constants at the top of `calibration_report.py`) — to be adjusted once you have seen real output.
- **`validate_green_weight` and `validate_temperature` still accept `nan`** (T-06 found it; only the new ambient validator rejects it). A NaN weight or temperature could be saved, and a NaN weight loss classifies as an Italian Roast. A small fix with tests; not done because it is outside T-06's scope and changes original validators.
- **The roaster-less fallback stays in the code** (the original limits for a profile with no roaster): removing it would mean rewriting the tests that build roaster-less profiles, for no user-visible gain now that every stored profile is migrated.

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

Completed 2026-09-19 · commit `509a315` on branch `roaster-selection` (since merged to `main`).
Added `data/roasters.json` (47 roasters at the time; 46 after T-02 removed "Bohemia 250", each `{name, values: {}}`), an optional roaster dropdown on the profile form above the wizard, and a faint `.roaster-tag` beside profile names on the profiles list, Add Roast picker, and Add Roast heading. Documented as Phase 11 in `SPEC.md`. 173 tests passing.

---

## T-01 [COMPLETE] Repo cleanup / refactor

Completed 2026-09-19 · commits `3358ebc` (R1), `f0dd94e` (R2), `bd826e1` (R3) on branch `roaster-selection` (since merged to `main`). Each commit's suite was run in isolation: 173 passing.
Kept deliberately modest: the live WSGI file does `from app import app` and `data_persistence.py` derives `DATA_DIR` from its own location, so neither module moved.

- **R1 — tests into `tests/`.** `git mv` (pure renames; contents unchanged) plus `pythonpath`/`testpaths` under `[tool.pytest.ini_options]` in `pyproject.toml`. `pytest` from the project directory works exactly as before; a single test is now `pytest tests/test_app.py::Class::test`. `CLAUDE.md` needed no change — its commands don't reference this project.
- **R2 — inline JS/CSS moved to `static/`.** New files: `css/add_roast.css`, `js/add_roast_form.js`, `js/add_roast_layout.js`, `js/add_roast_live.js`, `js/profile_wizard.js`. `add_roast.html` went from 628 to 141 lines and `profile_form.html` from 243 to 127. The code moved verbatim except two Jinja lines, which became a `roast-config` JSON data island that `add_roast_live.js` reads — the pattern T-04/T-05 will extend. The stylesheet `<link>` stays at the original in-body position so the CSS cascade order is unchanged; `base.html` was not touched.
- **R3 — housekeeping.** Removed the unused `src/` "Hello" stub, `[build-system]`, and the `[project.scripts]` entry (which already failed with `ModuleNotFoundError: No module named 'app'`); wrote a real description and README. `uv.lock` changed by one line (`editable` → `virtual`).
- **Verified:** 173 tests pass unchanged via `pytest` and `uv run pytest`; each extracted file re-checked line-for-line against the original; a headless-Chromium click-through (chart data, timer, first-crack button, wizard output for two input sets, console errors) matched the pre-refactor baseline exactly; screenshots of four pages were pixel-identical; `uv sync` and `uv run python app.py` work.
- **Deploy note:** on PythonAnywhere this is `git pull` and Reload; `static/` needs no extra mapping (see `DEPLOY.md`).
- **Still deferred:** splitting `app.py` into Flask Blueprints (revisit once it passes roughly 900 lines after T-03; it was 879 lines on 2026-09-19, so not yet), and moving the modules into a `coffeeroaster04/` package (needs a coordinated WSGI and `DATA_DIR` change).

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

**Resolved in the 2026-09-19 review:** 1–2 stand (SR800 limits and 12 rows; see Open decisions); 3 became Settled #15 (leave as is); 4 and 5 stay as they are (see Open decisions).


Finished weight needs no per-roaster field: the domain rule is `0 < finished < green` (replacing the global ≥ 100 g floor, which rejects a full SR540 batch and any IKAWA roast).

### T-02b — Tier 2 fields (needed by T-04/T-05/T-06) — [COMPLETE]

Completed 2026-09-19 · commit `0c93e16` on branch `roaster-selection`. Suite: 293 passing (was 284).
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

Completed 2026-09-19 · commit `e01d917` on branch `roaster-selection` (since merged to `main`). 273 tests passing (was 184 at the start of T-03), verified on the commit in isolation.

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
- ~~Non-SR roasters have no chart opening, so a curve starts flat and its rate-of-rise line spikes when it first climbs~~ — **resolved by T-05.**
- ~~The wizard is SR800-only~~ — **resolved by T-04.**
- SR300/340/500, the poppers, Nesco, Whirley-Pop, and the ceramic roasters have no temperature grid at all (they have no readout) — **decided: leave as is (Settled #15).**
- ~~Roasters do not yet appear on the `/roasts` list or CSV export~~ — **done (Settled #16).**

**Files:** `roasters.py` (new), `validators.py`, `calculations.py`, `app.py`, `templates/{choose_roaster,profile_form,add_roast,roast_detail}.html`, `static/js/{add_roast_live,profile_wizard}.js`, `data/roasters.json` (chart anchors), `SPEC.md`, `DEPLOY.md`; tests: `test_roasters.py`, `test_limits.py`, `test_roaster_profiles.py`, `test_roaster_roasts.py`, `test_no_hardcoded_units.py` (new) and the seven edits above.

---

## T-04 [COMPLETE] Data-driven profile wizard

Completed 2026-09-19 · commit `c6a279b` on branch `roaster-selection`. Suite: 310 passing (was 293).

**What now works**
- **No constants in the script.** `static/js/profile_wizard.js` reads a JSON config island (`#wizard-config`) built from the profile's roaster's `wizard` data: first-crack time by density, the natural-process adjustment (0 if unknown), the DTR by roast level, the start and default first-crack temperatures, and the roaster's row count. The curve loop, array length, and first-crack-minute clamp all use the roaster's rows instead of 12.
- **The SR800's output is unchanged.** The browser check's SR800 wizard assertions (two input sets) passed untouched after the switch, so the data-driven wizard produces exactly the same numbers as the old constants.
- **The `calibrated` gate is gone.** The wizard is offered for every roaster that has wizard data (a readout and a `wizard` block). A roaster that isn't calibrated gets the notice "Estimated for this roaster — not calibrated; expect to adjust" plus a line saying only the SR800 is calibrated.
- **Times-only mode (the T-02b decision).** A temperature curve needs both a start and a default first-crack temperature, which only the SR family has. For every other roaster the wizard fills the target first-crack and development times, leaves the temperature grid untouched, hides the first-crack-temperature field, and says why. Verified: Kaffelogic 7:30 / 2:00; Gene Cafe (25 rows) 15:00 / 3:59, and 14:30 / 3:51 for a natural coffee (its −30 s adjustment); the SR540 gets the SR800's curve plus the notice.
- **The first-crack temperature field** is pre-filled from the roaster's data and its min/max come from the roaster's own temperature range (it was a hard-coded 300–480, a Fahrenheit assumption).
- **The plan's "on selection change" item is moot:** since T-03 the roaster is chosen on its own page before the form, so the wizard reads its data once, on load.

**Existing tests changed** (both mine, both anticipated by this item's plan): T-03's `test_wizard_is_offered_only_for_a_calibrated_roaster` asserted the `calibrated` gate that this item removes, and is replaced by tests that the wizard follows the roaster's data (offered, the notice, times-only vs curve, the config's numbers, no wizard on the edit page, and the real data for the SR800, SR540/SR700, Kaffelogic/Hottop/Quest/Gene Cafe, and the no-readout roasters). T-02b's drift guard, which compared the data to constants in the script, is replaced by a guard that the constants don't come back.

**Verified:** 6 deliberate breakages of the wizard (natural adjustment ignored, curve always drawn, stuck at 12 rows, notice removed, temperature field shown without a curve, server sending 0 for the adjustment) were each caught. I also looked at the open panel for the SR800 and for Kaffelogic.

**Known gap:** no roaster in the real data has both a temperature curve and a grid other than 12 rows, so the "curve uses the roaster's row count" path is covered only by a static guard and unit tests of the config, not by a browser run.

**Files:** `static/js/profile_wizard.js`, `templates/profile_form.html`, `app.py` (`wizard_config_for`), `roasters.py`, `SPEC.md` (Profile Wizard text), `tests/test_roaster_profiles.py`, `tests/test_roasters.py`, `tests/test_roasters_data.py`, `tests/browser/{driver.mjs,test_browser.py}`.

---

## T-05 [COMPLETE] Data-driven Add Roast live panel

Completed 2026-09-19 · commit `24ea855` on branch `roaster-selection`. Suite: 334 passing (was 310); the browser check is now 18 tests (was 15).

**What now works**
- **Chart opening follows the roaster's data** (`roasters.chart_opening`, sent to the page as `anchors`): the SR540/700/800 keep today's synthetic ramp (145 / 0.5 min / 270); a `preheat_charge` roaster with a stated `charge_temp` (else `preheat_temp`) starts the curve at that temperature and heads for the first target — Hottop 167, Aillio R1 160 / R1 V2 230, Quest 150, Sandbox 200; every other roaster's curve begins at the profile's first target, with no invented ramp, lead-in, or turning point (no source describes one). The T-03 flat lead-in, which caused a rate-of-rise spike, is gone.
- **Rate of rise** shows an en dash before a curve that begins later than minute 0 has a slope, and its first samples use the curve's real slope (my first version halved them; a browser assertion now guards it). The SR800's numbers are unchanged.
- **Pull countdown** subtracts the roaster's `cooling_coast_seconds` (unknown counts as 0). No roaster has coast data yet, so today it changes nothing; the page states the allowance when one is set.
- **Back-to-back reminder**, informational only: "this roaster needs at least N minutes between roasts", shown only for a *stated* gap greater than zero (SR540 30, Behmor 60, Aillio R1 V2 2, and — after the 2026-09-19 review confirmed it — SR800 30). The other SR models' 30 minutes are only assumed, so they show nothing. The app stores only a roast's date, not a time, so it could not enforce a gap anyway.
- **Axis units, y-axis and x-axis length:** already done in T-03 — labels and readouts come from the roaster's unit, the x-axis runs to its row count, and the y-axes auto-scale to whatever unit the data is in, so no separate bounds are needed.

**Tests.** 24 new unit and browser tests (opening for every kind of roaster and the real data, charge vs preheat, only stated gaps, coast reaching the page and the countdown, the notes). Six deliberate breakages (opening unused, preheat preferred to charge, curve always from minute 0, coast ignored, an inferred gap shown, the server sending coast 0) and the reverted rate-of-rise fix were each caught. **Existing tests changed** (both mine, from T-09, both pinning the behavior this item replaces): the Celsius test's "starts flat" is now "starts at its first target", and the 25-row curve has 240 points, not 250, because it begins at minute 1. I also looked at the Kaffelogic and Hottop charts.

**Known limits**
- No turning point: the data has none, so a charge-then-dip curve is approximated by heading from the charge temperature to the profile's first target.
- `cooling_coast_seconds` is `null` for all 46 roasters, so the coast allowance is untested against real data (the browser check gives the Quest an in-memory value to exercise it).
- The rate-of-rise *dot* at exactly t = 0 shows half the true slope on ramp and charge curves because the slope estimate reaches back before 0. That is how the SR800 has always behaved, so I left it to keep the SR800 identical; the fix is one line if you want it.
- `controls` and `cooling` are still unread (the control-change log, a T-06 candidate, would read them).

**Files:** `roasters.py` (`chart_opening`, more settings), `app.py`, `static/js/add_roast_live.js`, `static/css/add_roast.css`, `templates/add_roast.html`, `SPEC.md`, `tests/test_roasters.py`, `tests/test_roaster_roasts.py`, `tests/browser/{driver.mjs,serve.py,test_browser.py}`.

---

## T-06 [PARTLY COMPLETE] New Add Roast fields, shown per roaster

**Depends on:** T-05 ✓. **Done (Settled #17): start condition + ambient temperature** — details below. The rest stay candidates, not scheduled.

**Candidates, not scheduled:**
2. Charge temperature and turning point (time, temperature) — for `preheat_charge` roasters.
3. Control changes: timestamped fan/heat/drum adjustments, using the roaster's `controls` list. On dial-driven machines the dial sequence is the repeatable part of a roast; a profile-side `control_plan` would mirror this. *(Considered on 2026-09-19 and not selected for now.)*
4. Cooling start time.

Each gets its own SPEC entry and its own commit; fields not applicable to a roaster don't appear.

### T-06 (1) Start condition and ambient temperature — [COMPLETE]

Completed 2026-09-19 · commit `1916067` on branch `roaster-selection`. Suite: 365 passing (was 338); the browser check is 22 tests (was 19). Why: the Gene Cafe tip sheet says warm starts, ambient temperature, and line voltage each shift roast time by up to a minute, and the SR540 manual's 30-minute gap is about the same effect. Two optional facts on each roast, saved on the record and shown on the roast detail page.

**The three open design points, and what I chose** (each is a small change to reverse):
- **Ambient is entered in the roaster's own unit**, like every other temperature (Settled #12) — never converted. Its plausible range is per unit in `roasters.TEMP_UNITS` (0–120 °F, −18–49 °C), so it stays with the other unit text. A roaster with no temperature readout has no unit, so it gets no ambient field (and a posted value is ignored).
- **The same three start options for every roaster** (cold / warm / preheated), not only `preheat_charge` roasters. `start_model` says how the *chart* begins, not how the user started the roaster: a Fresh Roast owner can still start from a warm machine, which is exactly the SR540 gap. Hiding "preheated" for some roasters would be a guess the data doesn't support.
- **Detail page only — not the list or CSV.** The list is already wide, and nothing needs to sort or search on these yet. Adding them later is one column each.

**What it does.** Add Roast has a "Start condition (optional)" select and, for roasters with a unit, an "Ambient temperature, °F/°C (optional)" box, both after the bean fields. Both are stored as `start_condition` (`cold`/`warm`/`preheated`/`null`) and `ambient_temp` (number/`null`). The detail page shows one line ("Warm start · Ambient 68°F") only when at least one was recorded; older records show nothing. Rejected input re-shows the form with what was typed.

**Details worth knowing**
- `validate_ambient_temperature` rejects `nan` and `inf`. `float()` accepts both, and every comparison with NaN is false, so a plain range check lets them through.
- The page's chart script config now gets only `{symbol, ror}` of the units row, since the row also holds the server-side ambient limits (two T-03 tests correctly caught the leak — I fixed the code, not the tests).
- **No existing test changed.**

**Tests.** 27 new: validators and the units table (`tests/test_limits.py`, `tests/test_roasters.py`), Add Roast and detail behavior (`tests/test_roaster_roasts.py`), and the browser check (the options and label per roaster, the detail line with the record's unit, and a real form round trip — a wrong-unit ambient is rejected with the typed values kept, then the corrected form saves and shows the line). Thirteen deliberate breakages in a scratch copy were each caught (NaN/inf allowed, both bounds made exclusive, start condition unchecked, Fahrenheit bounds hard-coded, no-unit roaster still validated, units row leaked to the page, raw text saved, zero ambient hidden ×2, selection not kept, ambient field shown without a unit, the separator dropped). One first slipped through (the dot between the two facts, which led to a tighter assertion); the bounds check first matched the older temperature validator's identical wording, so it was re-aimed at the ambient validator.

**Files:** `roasters.py` (`TEMP_UNITS` ambient limits), `validators.py`, `app.py`, `templates/{add_roast,roast_detail}.html`, `SPEC.md` (a "Start condition and ambient temperature" input section), `tests/{test_limits,test_roasters,test_roaster_roasts}.py`, `tests/browser/{driver.mjs,test_browser.py}`.

**Found but not fixed (out of scope):** `validate_green_weight("nan")` and `validate_temperature("nan")` return NaN (the same reason as above), so a form could save a NaN weight or temperature. Worth a small separate fix with tests if you want it.

---

## T-07 [DEFERRED] Roaster-native profile structures and import/export

Program-driven roasters take profiles in their own shape — IKAWA (up to 6 inlet-temperature points and 3 airflow points over ≤ 12 min), Kaffelogic (temperature curve + fan curve + an end-of-roast "level"), Gene Cafe (multi-stage setpoints). Representing those natively, or importing/exporting Artisan/Kaffelogic/IKAWA files, is a large step and overlaps the existing Deferred Ideas in `SPEC.md`. Revisit only after T-03–T-05 have real users on more than one roaster.

## T-08 [COMPLETE] Calibration feedback loop

**Depends on:** T-03 (records carry `roaster_id`), plus real data. Completed 2026-09-19 · commit `34155db` on branch `roaster-selection` (Settled #17: the item after T-06). Suite: 398 passing (was 365); browser check unchanged (22 tests).

**What it is.** `calibration_report.py`, a read-only script (not a web feature): `python calibration_report.py [--records PATH]` prints, for each roaster with logged roasts, the roast count, whether it is marked calibrated, and the median and range of time to first crack, total roast time, and weight loss; the temperature at first crack; and the development ratio by roast level — each set beside that roaster's stored value (`wizard.time_to_first_crack_s.medium`, `wizard.default_first_crack_temp`, `wizard.dtr_by_level`) with the difference. A roaster not yet calibrated also gets a plain "enough consistent data to consider calibrating?" line. Tuning a roaster and flipping `calibrated` stays a manual edit of `data/roasters.json` (Settled #6) — the report changes nothing.

**Design choices** (each easy to change):
- **Read-only and standalone.** It reuses the existing loaders and `calculations.py` (so roast levels and ratios are exactly the app's) but never imports `app.py`, whose startup migration would write to the data files. A missing records file is an error, a corrupted one stops with the loaders' message (never an empty or partial report).
- **The data isn't in the repo.** `data/roast_records.json` is gitignored and this checkout has none, so the report takes `--records PATH`: run it where the real file is, or download a copy.
- **Temperature at first crack** is interpolated between the two once-a-minute readings either side of first crack (a missing reading, or a different unit than the roaster's, leaves that roast out; the line says "n of N with readings").
- **Development ratio is grouped by roast level** (from weight loss, via `classify_roast`), because the stored table is per level: "Full City roasts averaged 16.7% against a stored 16.0%" is a like-for-like comparison, whereas one overall average would not be.
- **Readiness thresholds are my defaults, not domain rules:** at least 5 roasts whose first-crack times lie within 60 s of each other (`MIN_ROASTS`, `MAX_FIRST_CRACK_SPREAD_S` at the top of the file). The numbers are printed so you decide; change the two constants if they feel wrong.
- **Rough first-crack comparison:** the stored first-crack time is for a medium-density washed coffee, and records don't store density, so the difference is a guide, not a verdict (the report says so beside the number).
- **Records from every owner are combined** and no bean names or owners are printed. With no other users yet this is moot; if that changes and calibration should use only your roasts, an `--owner` filter is a few lines.
- **Not included** (not asked for): breaking results down by start condition or ambient temperature, the point of T-06's fields. It would be a small addition once there are enough roasts with those recorded.

**Tests.** 33 new in `tests/test_calibration_report.py`: the interpolation (whole minutes, between readings, missing neighbours, before/after the grid), the numbers gathered per roaster (including a small-batch roast outside the original guards), every comparison line and its sign, units, readiness at each boundary, roasters with no readout / no roaster / unknown roaster, ordering, no names leaked, and the command line (reads the named file with the real roaster data, writes nothing and leaves the data path as it was, missing and corrupted files, empty file). Sixteen deliberate breakages in a scratch copy were each caught, after two fixes to the tests (see below) (wrong interpolation slope, unit filter removed, original guards left on, ratio against the wrong denominator, roast level ignored, three flipped/unscaled differences, both readiness boundaries, path not restored, missing-file check removed, ordering, calibrated branch, unit symbol dropped, wrong column). **No existing test changed.** Problems in my own new tests, all fixed before this was finished: four wrong expectations (roast-level thresholds and where the readings fall; the report was right each time); a boundary test whose data was impossible (first crack after the end of the roast), which made an early mutation run meaningless because it was the failing test each time — so every mutation was re-run against the clean file; and that re-run found two real gaps (the first-crack difference's sign, and the total-roast-time line, were untested), now covered.

**Not yet exercised on real roasts:** it ran on synthetic records only, since none are available here. Run it on your SR800 roasts and see whether the numbers read sensibly.

**Files:** `calibration_report.py` (new), `tests/test_calibration_report.py` (new), `README.md` (a section and a layout row), `SPEC.md` ("Calibration report").

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

## T-10 [COMPLETE] Review follow-ups: the SR800's stated gap and the Roaster column

Completed 2026-09-19 · commit `0652029` on branch `roaster-selection`. Suite: 338 passing (was 334); the browser check is 19 tests (was 18). These are the two concrete decisions from the open-questions review (Settled #14 and #16).

- **SR800 gap.** `data/roasters.json`: the SR800's 30-minute gap is now stated (removed from its `inferred` list; the note records the owner's confirmation). Add Roast therefore shows "Reminder: this roaster needs at least 30 minutes between roasts." for the SR800. The other SR models' 30 minutes stay assumed and unshown.
- **Roaster column.** `ROAST_TABLE_COLUMNS` gains "Roaster" directly after "Roast Profile", in the `/roasts` list and the CSV export (a record with no roaster, or one no longer in the list, shows "-"). The list's client-side sort and search were unaffected; a new browser scenario checks the headers, sorting by the new column both ways, and search. `SPEC.md` describes both.
- **Existing tests changed** (both mine, from T-05, both asserting the SR800's gap is *not* shown — the opposite of Settled #14): `test_only_stated_gaps_are_reminders` now expects the SR800 stated (the SR700 is the assumed example), and the browser check's SR800 page test now expects the reminder. The one original test on the CSV header only checks a substring, which still holds, so no original test changed.
- **Verified:** the new column tests failed when the cell or the CSV value was removed (the misaligned-cell breakage failed 3 tests, the missing CSV value 2); the gap tests failed the moment the data changed and passed once updated.
- **Files:** `data/roasters.json`, `app.py`, `templates/roasts.html`, `SPEC.md`, `tests/test_roasters.py`, `tests/test_roaster_roasts.py`, `tests/browser/{driver.mjs,test_browser.py}`.

---

## T-11 [COMPLETE, phone test pending] Mobile optimization

Built and committed 2026-09-19 · commit `2ff59ad` on branch `mobile-optimization` (branched from `main` at `1d0638d`; not yet merged to `main`). Suite: 409 passing (was 398); the browser check is 30 tests (was 22). Queued the same day; nothing needed a decision from you to start, so the open points below were settled with defaults you can reverse.

**The finding.** No template had a `<meta name="viewport">` tag, so a phone laid every page out at 980 px and shrank it (measured in headless Chromium as a 390 px touch device: every page had a 980 px layout). The two existing `@media (max-width: 640px)` rules never fired. One line fixed that; the rest is what a real phone width then showed.

**What changed**
- **Viewport tag** in `base.html`, so every page has it. A test fails for any page template that does not extend the base.
- **Phone rules** (640 px and below, `base.html`): text fields and selects 16 px and at least 44 px tall (under 16 px, iOS zooms the page when a field is focused); buttons and the favorite stars at least 44 px; extra vertical tap area on links (padding on an inline link moves no text); the header may wrap; the search box and menu use the full width.
- **Keypads:** `inputmode="decimal"` on green and finished weight and the actual-temperature and profile-target grids. Not on MM:SS times (iPhone number pads have no colon) or on ambient (no minus sign, and it can be negative in °C).
- **Add Roast on a phone:** one column with the live panel (Start/Reset, chart, readouts, First Crack Now!, pull countdown) **above** the form; before, it was about four screens down. Start/Reset are large half-width buttons. The typed date and calendar button share one row inside the card.
- **Charts:** the live chart and both detail charts were held at Chart.js's default 2:1 shape (a thin strip on a phone, with empty space under it). They are 4:3 on a phone; wider screens are unchanged (still 2:1).
- **`/roasts`:** the table already scrolled sideways inside its own box; it now says so ("Swipe sideways to see every column", phones only).
- **Tablet (641–~800 px)** keeps the two-column layout; there the typed date now shrinks so the calendar button isn't cut off (a flaw that existed before this).

**Decisions I made** (each easy to reverse)
- `/roasts` stays a scrolling table with a hint, not cards: it keeps sort and search as they are and adds no second layout.
- **Screen wake lock: not built.** It cannot be verified in headless Chromium and needs your phone. It is a small addition (ask for the lock on Start, release it on Stop/Reset, re-ask when the tab returns to the front). I recommend adding it once you have tried the layout on your phone; say the word.
- **The timer is not sticky.** On a phone the live panel is at the top, but typing temperatures into the table below scrolls it out of view. A slim always-visible bar (clock, temperature, First Crack, Start/Stop) would fix that; it needs the panel restructured, so I left it as a follow-up decision (do you type temperatures during the roast on your phone?).
- Not touched: the splash animation (it plays on every page load, and its own comment plans a settings toggle), the profile-list Favorite column width, and the desktop layout.

**Tests.** 11 new: `tests/test_mobile.py` (3: the tag is in the base, every page extends it, served pages carry it) and 8 in the browser check, which now also loads the pages as a 390 px touch device and a 768 px one. It checks: 980 vs 390 px layout and no sideways scroll on ten pages; fields at least 16 px and controls at least 44 px on every one; the live panel and First Crack button above the form on three Add Roast pages (including a 25-row profile and one with no temperature readout); chart shapes (4:3 phone, 2:1 desktop, both detail charts); the date row fitting on phone and tablet; the scroll hint (shown on phone, hidden on desktop). Fourteen deliberate breakages in a scratch copy were each caught, plus the tablet date fix; the clean suite was confirmed passing before each mutation run. **No existing test changed.**

**Files:** `templates/base.html`, `templates/{add_roast,profile_form,roast_detail,roasts}.html`, `static/css/add_roast.css`, `static/js/add_roast_live.js`, `SPEC.md` (Phase 13 and "Phone-sized screens"), `tests/test_mobile.py` (new), `tests/browser/{driver.mjs,test_browser.py}`.

**Still to do for "done":** you try Add Roast, Roasts, and a profile on your own phone (real fonts, real keyboard, real thumb) and tell me what feels wrong.

---

## T-12 [COMPLETE] App version and in-app release notes

Completed 2026-09-19 · commit `b18b677` on branch `versioning` (cut from `mobile-optimization` at `64a1b3d`, so it includes T-11; not yet merged to `main`). Suite: 432 passing (was 409); the browser check is 31 tests (was 30). Queued the same day.

**What it is.** The app now has a version, shown in every page's footer ("About · v1.2.0 · What's new"), and a public `/whats-new` page listing every release newest first: version, title, date written out, and a few plain-language changes, with the newest marked "current version". Everything comes from one tracked file, `data/release_notes.json` (a list, newest first, of `{version, date, title, changes}`), and **the app's version is the newest entry's version**, so the number and the notes cannot drift apart. `pyproject.toml` and `uv.lock` carry the same version (`uv lock --check` passes).

**Decisions I made** (each easy to change; you did not answer the open points, so these are defaults)
- **Where counting starts.** The first entries were written afterward from the git history (Sept 14–19, real dates): 0.1.0 the first version, 0.2.0 accounts and the live timer, 0.3.0 Crackle with roast insights and the wizard, 0.4.0 the pull countdown, **1.0.0 "Choose your roaster"** (the roaster-driven redesign, the point where the app stopped being tied to one machine), 1.1.0 mobile, and **1.2.0 this feature**. So the current version is 1.2.0. Say if you would draw the 1.0 line elsewhere or want fewer, coarser entries; it is one JSON file.
- **Numbering:** MINOR for a user-visible feature, PATCH for a fix, MAJOR when existing data or behavior changes.
- **Style:** plain language, each line at most 220 characters and no HTML, so it stays a summary and not the developer log (which stays here and in git). A test enforces the length and the no-markup rule.
- **No git tags.** Tagging (`git tag v1.2.0`) is optional and nothing does it; it is one command if you want to see what was deployed when.
- **The habit is written down** (SPEC, README "Releasing", CLAUDE.md): a change users can see adds an entry at the top and bumps `pyproject.toml` in the same commit. A test cannot tell whether a change is user-visible, so this part is a convention, not a check.
- **`tomllib` is not used** to read `pyproject.toml`: PythonAnywhere is set up on Python 3.10, which lacks it, so the sync test reads the file as plain text.
- `date.fromisoformat` rather than `strptime` for the dates (no naive-datetime lint findings added).

**Files:** `data/release_notes.json` (new), `data_persistence.py` (`load_release_notes`), `app.py` (`/whats-new`, the version in every template, the date formatter), `templates/whats_new.html` (new), `templates/base.html` (footer), `pyproject.toml` and `uv.lock` (version), `SPEC.md` ("Versions and release notes", Phase 14), `README.md` (Releasing), `DEPLOY.md` (the new tracked data file), `CLAUDE.md` (a Releases bullet), `tests/test_release_notes.py` (new), `tests/browser/{driver.mjs,test_browser.py}`.

**Tests.** 23 new. `tests/test_release_notes.py` (22): the data file (fields, version form, strictly rising versions, real dates in order, short plain changes, and the `pyproject.toml` sync), the loader (missing file, valid, corrupted stops and leaves the file alone), the page (public, order, dates, only the newest marked current, text escaped, the empty state), and the footer (newest version, follows the newest entry, shown to logged-in users, absent with no releases). The browser check (1 new, plus the page in the phone-width set): the page's headings and footer match the real data file without hard-coding a version, and it loads with a clean console. Twenty-five deliberate breakages in a scratch copy were each caught, including bad edits to the data file itself (versions out of order or duplicated, an impossible date, a stale date, an empty or essay-length change, markup, an extra field, an empty title). **No existing test changed.**

**For you:** read the seven entries in `data/release_notes.json` (they are your project's voice, and I wrote them from the commit history) and correct anything that overstates or misses.

---

## T-13 [BUILT, awaiting your review and your numbers] Espresso profile style

Built 2026-09-19 on branch `espresso-style` (cut from `versioning` at `fcdbf69`, so it includes T-11 and T-12; uncommitted). Suite: 483 passing (was 432); the browser check is 34 tests (was 31). Released as version **1.3.0** ("Espresso profiles") in `data/release_notes.json`. Queued the same day; you started it without answering the five design points, so I used my leans, listed below.

**What it does.** A profile now has a **style**, Drip (what every profile was) or Espresso, chosen on the page where you choose the roaster and **locked afterward** (read-only on the edit form; a change is rejected with a 400). The wizard reads the roaster's new `wizard.espresso` values for an espresso profile, and always says they are estimates, the SR800 included. The style shows as a faint tag beside the roaster's tag in the profile lists, the Add Roast picker and the Add Roast heading, and as a "Style:" line on the profile form and the roast detail page. Each roast records its profile's style, and at startup every existing profile and roast becomes Drip (idempotent, like the roaster migration: back up `data/` first, per `DEPLOY.md`). The calibration report now groups by roaster **and** style, compares espresso with the espresso values, and never calls espresso calibrated, so espresso roasts are never averaged into the drip comparison.

**What "espresso-shaped" honestly is, so far (please read).** The research supports one claim only: **espresso develops longer than filter.** The sources I could read: ICT Coffee (a retailer's article) puts filter development at 20–25% of the roast and espresso at "often 25 to 30 percent or more", finished "medium to medium-dark"; Scott Rao's 20–25% is "for most roast levels" and does not mention espresso; Kaffelogic's profile page has no espresso guidance; Sweet Maria's air-roaster page (blocked to me; two search summaries agree it says a slow rate of rise and lots of development after first crack) has no numbers I could verify. So the espresso values are: each roaster's own drip development ratios **× 1.2** (rounded, written out per roaster: SR800 Full City 16% → 19%), and time to first crack and the natural adjustment **copied from drip** (no source gives a figure). All are marked `inferred` (`wizard.espresso`) with the ICT source. Because the wizard's temperature curve ends at first crack and that time is unchanged, **the espresso curve is the same as drip's and the only visible difference is a longer target development time** (SR800 medium/washed/Full City: 1:28 against 1:11). That is not yet a different curve *shape*. If you roast espresso, your own SR800 numbers (first-crack time, development time, roast level for espresso roasts) are worth more than any of these sources; with them I can set a real espresso time to first crack and ratios, and the curve will change with them.

**Decisions I made** (each easy to reverse; the numbers are the part you should check)
1. **Numbers live per roaster** (option A: `wizard.espresso` on each of the 34 roasters with a wizard, explicit values, consistent with Settled #5), not as one shared multiplier applied at run time.
2. **Locked at creation**, like the roaster.
3. **Records snapshot the style** (`profile_style`), like `roaster_id`.
4. **No Style column in the roast list or CSV** (you asked for it in the menus, like the roaster's tag); one column each if you want it.
5. **Names:** "Drip" and "Espresso". The style tag is a separate element from the roaster tag (existing tests pin the roaster tag's exact markup and count).
6. **A missing style in a link or form means Drip**, so older links and posts keep working; an unknown style is rejected.

**Existing tests changed** (three, all mine from earlier items, none of your originals; each follows the spec change, and all other tests are untouched)
- `test_roasters_data.py::test_wizard_values_are_consistent` asserted the wizard's keys were exactly the drip fields; they now also include `espresso`.
- `test_roasters_data.py::test_inferred_lists_only_populated_data_fields` accepts the new dotted name `wizard.espresso`.
- `tests/browser/test_browser.py::test_choosing_a_roaster_first_then_the_form_for_it` expected the chooser to send `?roaster=…`; it now also sends `&style=drip`.

**Tests.** 51 new: `tests/test_profile_styles.py` (41: the helpers, the migration incl. idempotence, the validator, choosing and saving a style, the lock on edit, the wizard's values and notices per style, the tags, records and the detail page, and the report's grouping), 7 in `test_roasters_data.py` (each espresso block's shape, first-crack times, ratios rising, **longer than drip at every level**, natural adjustment, marked inferred with its source), and 3 in the browser check (the real espresso wizard output, the full choose-fill-save round trip and tag, and the style on the detail page). Thirty-seven deliberate breakages in a scratch copy were each caught (one of my first mutations deleted a loop body and caused a syntax error that only looked like a catch; I redid it as two valid ones).

**Files:** `roasters.py` (`PROFILE_STYLES`, `profile_style`, `wizard_for_style`, `migrate_profile_styles`), `validators.py`, `app.py`, `calibration_report.py`, `data/roasters.json` (espresso blocks), `data/release_notes.json`, `pyproject.toml`, `uv.lock`, `templates/{choose_roaster,profile_form,add_roast,select_profile,_profile_table,roast_detail,base}.html`, `SPEC.md` ("Profile styles", Phase 15, Tier 2), `DEPLOY.md`, `tests/test_profile_styles.py` (new), `tests/test_roasters_data.py`, `tests/browser/{driver.mjs,test_browser.py}`.

**For you:** (1) tell me if you have espresso numbers from your own roasts; (2) check the four release-note lines in 1.3.0; (3) try creating an espresso profile on the SR800 and look at the wizard's development time.

---

## T-14 [PLANNED] How-to / tutorial

**Depends on:** none, but best written **after T-11 and T-13** so it describes the final screens and the phone layout. Queued 2026-09-19.
**Goal:** a new user can learn the app's flow without asking. It is not obvious today: choose your roaster → create a profile (optionally with the wizard) → Add Roast → run the live timer and mark first crack → save → read the result. The only help now is the About page.

**Options**
- (a) A `/help` page: one readable page with sections and anchors, linked from the header or footer. Plain HTML in a template; cheap and easy to keep accurate.
- (b) A first-run walkthrough or tooltips over the real pages. More engaging; more code and more to keep in sync with the UI.
- (c) Both, with small "?" links from key pages (the wizard, the live panel) to the matching help section.
- **Screenshots** are not proposed at first: they go stale with every UI change (the browser check could generate them later if you want them).
I lean to (a), with (c)'s contextual links added once the page exists.

**Proposed contents:** 1. Getting started (roaster → profile → first roast). 2. Making a profile and using the wizard. 3. Logging a roast: the timer, First Crack Now!, the pull countdown, entering temperatures, start condition and ambient. 4. Reading a roast: weight loss, roast level, development ratio and time, cupping notes, CSV export. 5. Favorites. 6. A short glossary (first crack, development, DTR, rate of rise, profile). If T-13 happens: drip vs espresso.

**Tasks**
- [ ] Write the content (plain language; ask you to check it, since it is your app's voice).
- [ ] The `/help` route and template; a header or footer link; public like `/about`.
- [ ] Contextual links from the key pages to their sections (if (c)).
- [ ] `SPEC.md`: the page and its links.

**One constraint to know:** `tests/test_no_hardcoded_units.py` fails if a template contains a hard-coded temperature unit, so the help page has to say "your roaster's unit" (or draw the symbol from the units table), not "°F".
**Tests:** the page renders logged in and out; every in-page anchor and every "?" link points at a section that exists; the unit guard still passes.
**Done when:** the page covers the flow above and you can follow it cold from a fresh account.

---

## Suggested order

T-01 ✓ → T-02a ✓ → T-03 ✓ → T-02b ✓ → T-09 ✓ → T-04 ✓ → T-05 ✓ → T-10 ✓ → T-06 (start condition + ambient) ✓ → T-08 ✓ → merged to `main` and pushed. The other T-06 candidates and T-07 stay unscheduled.

**Queued 2026-09-19 (order not yet decided; T-11, T-12 and T-13 have since been built):** T-11 mobile optimization, T-12 app version and release notes, T-13 espresso profile style, T-14 how-to. A suggestion, not a decision: T-11 first (the missing viewport tag is a one-line fix that helps every page), T-12 next (small, and gives later items somewhere to be announced), then T-13, and T-14 last because it documents the final screens.
