# Crackle Specification (Web UI)

## Purpose
Record coffee roasting sessions and calculate basic roast metrics in Python, presented through a browser-based UI instead of a terminal UI. This is an independent iteration of the coffeeroaster exercise (see coffeeroaster01-03); it carries forward the calculation and persistence logic from coffeeroaster03 and replaces only the UI layer.

## Implementation Phases
This SPEC describes the full feature set, carried forward from coffeeroaster03 and extended. It was built in phases, each requested explicitly; Phases 1 through 12 are built; Phase 13 (mobile optimization) is in progress and is the current one. `to-do.md` tracks what was built for Phases 11 to 13 and what is still open.

- **Phase 1**: View roasts (read-only table) and a roast detail page with a temperature chart. Uses data seeded from coffeeroaster03's existing JSON files.
- **Phase 2**: Add roast form.
- **Phase 3**: Roast profile management (add/view/edit).
- **Phase 4**: Delete roast records and delete roast profiles. This did not exist in coffeeroaster03 (which had no delete for either) — it is new scope for this mission, not something carried forward.
- **Phase 5**: Home page becomes a main menu (Add roast / View roasts / View and edit roast profiles as buttons), mirroring coffeeroaster03's `MainScreen`. The roast records table moves to its own `/roasts` route.
- **Phase 6**: Deploy to PythonAnywhere.
- **Phase 7**: User accounts. Each account has its own private roast records and profiles — the earlier "no authentication" decision applied while this was a purely local, single-user tool; it no longer holds once the app is reachable on the open internet.
- **Phase 8**: About page. Static project description plus a feedback form that emails the site owner directly — no user-visible email address, no new external service.
- **Phase 9**: Roast intelligence & data tools. Surfaces calculated roast quality metrics that already had the underlying data, plus search/sort, CSV export, a live first-crack marking shortcut, and richer per-roast metadata (bean origin/variety/process, post-roast cupping notes).
- **Phase 10**: Roast profile wizard. An opt-in helper on the Add roast profile page that recommends a starting Maillard-phase target-temperature curve plus target first-crack/development-time reference values, from bean characteristics, desired roast level, and the user's own observed first-crack temperature, which the user can then edit before saving. The target reference values also drive a live pull countdown timer on the Add Roast page once first crack is marked.
- **Phase 11**: Roaster selection. A reference list of home coffee roasters (`data/roasters.json`) and a roaster dropdown on the roast profile form, shown alongside the profile name wherever profiles are listed or used — groundwork for later customizing profiles and the Add Roast experience per roaster.
- **Phase 12**: Roaster-driven profiles. A profile belongs to one roaster, chosen first and locked afterward; that roaster's data supplies the profile's row count, the weight and time limits, and the temperature unit, and each saved roast records its roaster. Also part of this phase: an optional start condition and ambient temperature on each roast (see "Start condition and ambient temperature" under User Inputs), and a read-only calibration report that compares logged roasts with each roaster's stored values (see "Calibration report" under Roasters). See "Roaster-driven profiles" under Roasters.
- **Phase 13 (current)**: Mobile optimization. Every page is usable on a phone without zooming or scrolling the page sideways, and Add Roast puts the timer and First Crack button first. See "Phone-sized screens" under User Interface.

## Requirements
The code shall have a separate module for calculations (`calculations.py`, carried forward from coffeeroaster03 unchanged).
The code shall have a separate module for persistence (`data_persistence.py`, carried forward from coffeeroaster03, adapted only for this project's own `data/` path).
The code shall have a separate module/package for the web interface (Flask routes + Jinja2 templates), isolated from `calculations.py` and `data_persistence.py`.
`calculations.py` and `data_persistence.py` shall not import from or depend on the Flask/web module.
Each module shall have a pytest script written for validation testing.
Persistent data shall be written to JSON files in this project's own `data/` folder (see Persistence).
Load existing roast records when the application starts.
If the data file does not yet exist, start with an empty dataset.
Save roast records when a new roast is added (Phase 2).
Preserve all existing roast records when adding a new record.
Convert dates appropriately between the Python internal representation and JSON storage.

## Constraints
JSON only; do not introduce a database.
Do not introduce external Python dependencies except `flask` (and its own required dependencies, e.g. Jinja2, Werkzeug) for the web layer.
Charting is rendered client-side via Chart.js, loaded from a CDN `<script>` tag — this is not a Python package dependency and introduces no build tooling (no npm, no bundler, no SPA framework).
Page-specific JavaScript and CSS live as plain files under `static/` (served by Flask's built-in `/static/` route) rather than inline in templates; per-page data reaches them through a JSON data island in the template, not Jinja interpolated into script code. Still no build step.
A browser check (`tests/browser/`) drives the pages in headless Chromium through the DevTools protocol using Node's built-in WebSocket, against the real app on fixture data. It also loads the pages at phone (390 px) and tablet (768 px) widths as a touch device. It uses the system's Chromium and Node, so it adds no Python or npm dependency, and it skips itself (with the reason) when they or the network are unavailable.
The UI shall be a server-rendered web application (Flask + Jinja2 templates), not a terminal UI and not a single-page JS application.
Do not change the existing calculation formulas.
Do not delete existing functionality once implemented in this mission.
Keep the architecture reasonably simple.
Explain the proposed changes before implementing them.

## User Inputs
*(Phase 12: the numeric limits below (green/finished weight, roast time, first-crack time, temperature) are the limits for a profile with no roaster. For a profile with a roaster they come from that roaster's data — see "Roaster-driven profiles" under Roasters.)*

*(These are domain/validation rules carried forward from coffeeroaster03. The Add roast form (Phase 2) enforces them when a roast is entered.)*

### Date
Required.
Must be in the format MM/DD/YYYY.
Must represent a valid calendar date.
Must be ≤ today's date.
Future dates are rejected.
Display an explanatory error for invalid input.
The field shall remain editable and the record shall not be submitted until the value is valid.

### Bean
Required.
May contain any combination of alphanumeric characters.

### Green Weight
Required.
Input must be numeric.
Input must be greater than 100 and less than 300.
Invalid input must produce a helpful error.
The field shall remain editable after an invalid entry.
User is requested to input a number in grams.

### Finished Weight
Required.
Input must be numeric.
Input must be greater than 100.
Input must be less than green weight.
Invalid input must produce a helpful error.
The field shall remain editable after an invalid entry.
User is requested to input a number in grams.

### Total roast time
Required.
Must be entered in MM:SS format.
Must be ≥ 04:00.
Must be < 20:00.
Display an explanatory error for invalid input.
The error must display the values in MM:SS format.
The field shall remain editable and the record shall not be submitted until the value is valid.
Value must be stored as integer seconds.

### Time of first crack
Required.
Must be entered in MM:SS format.
Must be less than total roast time.
Display an explanatory error for invalid input.
The error must display values in MM:SS format.
The field shall remain editable and the record shall not be submitted until the value is valid.
Values must be stored as integer seconds.

### Roast temperature
See Roast Profiles below. Collected as part of Add roast via a selected roast profile, not as a standalone field.

### Start condition and ambient temperature **(Phase 12)**
Two optional facts about how the roast began, recorded because a cold room or a still-warm roaster changes how fast the same profile runs. Both are optional and independent, and a roast saved without them stores `null` for each.
- *Start condition*: one of `cold` (the roaster started at room temperature), `warm` (still warm from a recent roast) or `preheated` (deliberately warmed up first), shown as "Cold start" / "Warm start" / "Preheated". The same three choices are offered for every roaster: the app does not guess which apply to a machine, since `start_model` describes how the chart begins, not how the user started the roaster. Anything else is rejected.
- *Ambient temperature*: the room or outdoor air temperature, a number in the roaster's own temperature unit (never converted) within that unit's plausible range, kept in `roasters.TEMP_UNITS` (`ambient_min`–`ambient_max`: 0–120 °F, −18–49 °C; inclusive, negatives allowed). `nan` and `inf` are rejected. A roaster with no temperature unit (no readout) has no ambient field, and an ambient value posted to it is ignored.
Both appear on the roast detail page, on one line ("Warm start · Ambient 68°F") only when at least one was recorded, and are not added to the roast list or the CSV export. Records saved before these fields existed simply show no line.

## Roast Profiles

### Requirements
The application shall provide a "View and edit roast profiles" area leading to add-a-new-profile and view/edit-existing-profiles pages. **(Phase 3)**
A roast profile shall consist of a name and a target temperature for each whole-minute interval from 1:00 through its last row: 12 rows (°F) for a profile with no roaster; for a profile with a roaster, that roaster's row count and unit (Phase 12).
Temperature entries within a profile are optional per minute.
A profile may be marked as a favorite, toggled with a star on the Add roast profile picker, which lists favorites first in their own section. Every profile list shows favorites first, then the rest alphabetically by name. A new profile is not a favorite, and editing a profile keeps its favorite flag.
A roast profile may also store a target first-crack time (MM:SS) and a target development time (MM:SS), both optional, fixed reference values shown in the Add Roast live panel, directly above the "First Crack Now!" button — not modeled as part of the temperature curve. **(Phase 10)**
Once a first-crack time is set on the Add Roast page (via "First Crack Now!" or by typing directly into the field) and the selected profile has a target development time, a pull countdown shall appear below the "First Crack Now!" button, live-updating as `first crack time + target development time − the roaster's cooling coast time − elapsed time` (the coast time is 0 when the roaster's data has none) until it reaches zero, then holding at "Pull now!". Reaching zero triggers a quadruple flash (the existing per-whole-minute flash — see Phase 9 — is a double flash; this is visually distinct and reserved for the pull moment specifically). **(Phase 10)**
Any minute interval left blank in a profile shall default to the most recently entered temperature at an earlier interval (carry-forward). An interval with no earlier entry has no default.
Selecting Add roast shall first require selecting an existing roast profile before the roast entry form is shown. **(Phase 2)**
If no roast profiles exist, the user shall be directed to create one before a roast can be added. **(Phase 2/3)**
The Add roast form shall present a table of time / actual temperature / target temperature, one row per minute of the selected profile (1:00 through 12:00, in °F, for a profile with no roaster; the roaster's row count and unit otherwise, Phase 12), positioned after Green Weight and before Time of First Crack, which remains a standalone field. **(Phase 2)**
The target temperature column shall be pre-populated and read-only, sourced from the selected profile with carry-forward applied.
The actual temperature column shall be manually entered by the user; entries are optional per minute.
At submission, if total roast time exceeds the last whole minute at which an actual temperature was entered, the latest entered actual temperature shall be used to populate the remaining whole-minute intervals up to total roast time.
Each saved roast record shall store the id of the selected roast profile and a snapshot of the resolved (carry-forward-applied) target temperatures as of the time the roast was saved.

### Constraints
Temperature values (profile targets and actual roast entries) must be numeric and between 60 and 500 °F when provided (for a profile with a roaster, between that roaster's `temp_min` and `temp_max`, in its own unit).
Target first-crack time, when provided, must be MM:SS between 01:00 and 20:00. Target development time, when provided, must be MM:SS between 00:01 and 20:00. Neither is validated against the other or against the profile's temperature entries — they're independent reference values.
Editing a roast profile after a roast has been saved against it shall not alter the target temperatures already stored on that roast record (snapshot at save time, not a live reference).
Roast profile persistence shall use its own JSON file in the `data/` folder, following the same load/corruption-check/save pattern as roast records.

### Domain rules
Roast profile intervals are defined in whole minutes only; there is no sub-minute granularity.
A profile's (or a roast's actual) temperature at any interval beyond the last explicitly entered value equals that last entered value, since a roast in progress, or a profile author, may only have data through a given point in time.

### Delete **(Phase 4)**
A roast profile may be deleted, with a confirmation step first.
Deleting a profile that past roast records reference shall not alter those records' stored `target_temps` snapshot or any other field (they hold their own copy at save time, not a live reference — see Constraints above). Such records shall continue to display normally, showing no profile name for the now-missing reference (same behavior as a record whose profile was never set).

### Profile Wizard **(Phase 10)**
The Add roast profile page (new profiles only, not the edit form) shall offer an opt-in "Want some help?" wizard that, given bean density, process (washed/natural), desired roast level, and the user's own typically-observed first-crack temperature, fills the 12 target-temperature fields plus the target first-crack and target development-time fields with recommended starting values. The user may review and edit every generated value, or ignore the wizard entirely, before saving.
The wizard's roast-level options shall use the same six-tier vocabulary as `classify_roast` in `calculations.py` (City Roast through Italian Roast), so a recommended curve and the eventual weight-loss-based classification of a roast made from it speak the same language, even though they're computed from unrelated inputs (temperature curve vs. actual weight loss).
The wizard shall ask for the user's own first-crack temperature rather than assuming one, since it varies meaningfully by roaster model and probe placement.
The generated temperature curve models only the Maillard phase, minute 1 through first crack: the steep charge-to-drying ramp is already modeled outside the saved profile, by the live Add Roast graph's fixed 145°F start / 270°F-at-30s spline anchor (see `add_roast.html`), so a profile's own minute-1 value already starts just past drying, in early Maillard. The Maillard phase's minute-by-minute values shall decelerate (a larger share of that phase's temperature rise in its earlier minutes, a smaller share later) rather than rise linearly or spike, consistent with published guidance that a flat or rising rate of rise risks a "crash and flick" (baked or ashy flavor) — see Artisan's and Scott Rao's documented rate-of-rise guidance.
The wizard does not generate temperature values past first crack: development pace is roaster- and technique-dependent enough (e.g. a hold just above first-crack temperature, or a continued gradual rise, with cooling typically handled externally rather than as part of the heating profile) that pinning it to a specific temperature curve produced misleading results, including target temperatures that declined after first crack when a tier's fixed published drop-temperature fell below the user's own entered first-crack temperature. Instead, the wizard computes a target development *time* (MM:SS) from the tier's development-time-ratio (DTR) and the computed first-crack minute, and leaves the remaining temperature-grid minutes blank, relying on the existing carry-forward domain rule.

### Constraints
No new dependency and no server round-trip: the wizard is client-side JS on the profile form page, reading its own inputs and writing directly into the existing `temp_1`–`temp_N` (N = the roaster's row count), `target_first_crack`, and `target_development_time` fields; nothing about the wizard's inputs is persisted. Its roaster-specific numbers arrive in a JSON config block in the page (Phase 12), so generating a profile needs no server call either.
Per-tier development time ratio (DTR = development time ⁄ total time) targets were originally drawn from commonly published drum-roaster guidance, which turned out to run meaningfully slower than fluid-bed home roasters like the Fresh Roast machines this app targets — first-crack estimates around 8-9 minutes, versus the roughly 4-8 minute range reported for Fresh Roast machines by Sweet Maria's own SR540 tip sheet and corroborating sources. The DTR table was rescaled by a uniform factor off one real logged Fresh Roast result (medium density, washed: 6:15 first crack, 1:10 development time, landed at Full City, i.e. ~15.7% DTR versus the original table's 21%), preserving the table's original relative shape (darker roasts still carry a higher DTR) while anchoring the absolute scale to this machine.
Time to first crack (the roaster's `wizard.time_to_first_crack_s` and `wizard.natural_time_adjust_s`; for the SR800 these were the original `MAILLARD_TIME_SECONDS` and `NATURAL_TIME_ADJUST_SECONDS` constants) is a direct density/process-driven time target, not derived from the entered first-crack temperature. An earlier version computed time as (entered FC temp − a fixed start temp) ÷ a density-based pace, which conflated the FC temperature (which legitimately varies a lot by bean/instrument/altitude) with roast duration (which real-world use showed barely varies with density) — a high-altitude bean entered at a notably higher FC temp produced a wildly inflated multi-minute estimate, and because that estimate could exceed the temp grid's whole-minute cap while the displayed target first-crack field did not, the grid and the reference field could visibly disagree. The corrected model anchors medium/washed at 6:15 (the one real logged result) and applies the user's own rule of thumb for the deltas (high density ~30s later; natural process ~20s later); low density is treated as no different from medium, per the same source. The entered first-crack temperature is used only to set where the displayed Maillard curve ends, not to estimate its duration.
This is a rough first pass, not a validated model — only one real logged result exists, for one density/process combination, plus the user's own rule-of-thumb estimates for the others; the values should be revisited once more real roasts are logged across a range of density/process/roast-level combinations.

## Roasters **(Phase 11)**

### Requirements
`data/roasters.json` shall list known home coffee roasters, keyed by a stable slug id (e.g. `fresh-roast-sr800`), each with a display `name` and a `values` object holding that roaster's own data (see "Roaster data" below). Every roaster carries its own complete set of values — nothing is inherited or shared between roasters, so any one entry can be tuned later without touching another. Identical numbers across roasters are allowed where the research supports them, but each is written out on its own entry.
Adding a roast profile is two steps: first a page that asks which roaster the profile is for (an alphabetical dropdown, no default), then the profile form for that roaster. The choice is stored on the profile as `roaster_id`. **(Phase 12; Phase 11 put an optional dropdown on the form itself.)**
A roaster is required for a new profile. A profile with no `roaster_id` (or one no longer in `roasters.json`) keeps working with the original limits, 12 rows, and °F, but at startup any profile or record with no roaster is assigned the Fresh Roast SR800 (see below).
A profile's roaster name shall be displayed, in a faint italic style (`.roaster-tag`) so it reads as a different kind of data than the profile name, on: the View and edit roast profiles list, the Add Roast profile picker, and the Add Roast page heading (i.e. it propagates from the selected profile). It is omitted when the profile has no roaster.

### Constraints
`roasters.json` is read-only reference data loaded once at startup, following the same load/corruption-check pattern as the other JSON files. Unlike `roast_records.json`, `roast_profiles.json`, and `users.json`, it is **tracked in git** — it ships with the app rather than holding live user data.
A submitted `roaster_id` for a new profile must be a key of `roasters.json`; anything else, including blank, is rejected with a validation error (after the profile name is validated).
A profile stores only the roaster's id, not its name, so renaming a roaster in `roasters.json` is reflected everywhere. If a profile's roaster id is later removed from the file, the profile still works and simply shows no roaster.
Each saved roast record stores the profile's `roaster_id` and the `temp_unit` in effect (Phase 12), so a record stays self-describing if the profile is later edited or deleted or `roasters.json` changes.

### Roaster-driven profiles **(Phase 12)**
The roaster is chosen once, when a profile is created, and can never be changed afterward: its rows, limits, and units all come from that roaster, so a change would silently invalidate the profile's targets. The edit form shows the roaster read-only, and a submitted change is rejected (400). Add Roast has no roaster override either: the roaster is the selected profile's.
A profile has one temperature row per minute of its roaster's `profile_grid_minutes` (a saved profile is never truncated, and is padded with blank rows if its roaster's grid is now longer). The maximum roast time accepted equals the profile's row count in minutes (12 rows → 12:00 is accepted and 12:01 is not); target first-crack and development times obey the same maximum.
On Add Roast, green weight is limited to the roaster's `green_weight_min_g`–`green_weight_max_g` and finished weight need only be positive and no more than green (the original 100 g floor is not applied); the roast-time and first-crack floors and the temperature range are the roaster's own. The allowed ranges are shown as hints beside the fields.
Every temperature is stored and shown in the roaster's own unit and is never converted. Unit text (symbol and rate-of-rise label) comes only from `roasters.TEMP_UNITS`; no template, script, or module hard-codes a unit (enforced by a test), and the live chart's axis titles, tooltips, and readouts use the roaster's unit. A roaster with no temperature readout shows no temperature grid, temperature entry, chart, or temperature readout; its target first-crack and development times, timer, and first-crack button are unchanged.
The live chart's opening is decided by the roaster's data (Phase 12): a roaster with `chart_*` anchors (the SR540, SR700, and SR800) gets the synthetic ramp from its start temperature through the first inflection, in its own unit; a `preheat_charge` roaster with a stated `charge_temp` (else `preheat_temp`) starts the curve at that temperature and heads for the profile's first target; every other roaster's curve begins at the profile's first target (minute 1), with no invented ramp, lead-in, or turning point, since no source describes one. Before its curve begins the readout holds the first target and the rate of rise shows an en dash, because there is no slope yet; from its first sample the rate of rise is the curve's real slope.
On Add Roast, a stated `min_gap_between_roasts_min` greater than zero is shown as an informational reminder ("this roaster needs at least N minutes between roasts"); a gap that is only inferred is never shown, and a stated gap of zero (back-to-back is fine) shows nothing. A non-zero `cooling_coast_seconds` is stated beside the timer so the shortened pull countdown is explained. Nothing is enforced: the app records only the roast's date, not a time of day, so it cannot check the gap.
Saved records are never re-validated for display: weight loss and development time are calculated with the original guards opened, since a record was validated against its roaster's limits when it was saved.
The profile wizard is data-driven (Phase 12): it takes every number from the profile's roaster's `wizard` block (see "Roaster data (Tier 2)") and never from constants in the script — first-crack time by density, the natural-process adjustment (0 if unknown), the development-time ratios by roast level, and, for the curve, the start temperature, the default first-crack temperature, and the roaster's row count (the first-crack minute is kept within the rows). It is offered for every roaster that has wizard data (a temperature readout and a `wizard` block) and not offered otherwise; it is offered on the add form only, since the roaster is fixed by then.
Only the calibrated roaster (the SR800) is presented as calibrated. Any other roaster's wizard shows the notice "Estimated for this roaster — not calibrated; expect to adjust" and says it is a starting estimate from published guidance. For the SR800 the output is unchanged from before the wizard became data-driven.
A temperature curve is generated only when the roaster's data has both a start temperature and a default first-crack temperature (currently the SR family); the first-crack temperature field then appears, pre-filled, with the roaster's own temperature range. For every other roaster the wizard is times-only: it fills the target first-crack and development times, leaves the temperature grid untouched, and says so, rather than borrowing another machine's temperatures.
At startup, once, and idempotently: every profile with no roaster is assigned the Fresh Roast SR800; every record with no roaster takes its profile's roaster (the SR800 if the profile is gone) and every record without a `temp_unit` gets its roaster's unit. Files are rewritten only when something changed.

### Roaster data (Tier 1)
Each roaster's `values` object holds exactly these fields. They are the data the roaster-driven profile work (`to-do.md`, T-03) will read; nothing in the app reads them yet.

| Field | Meaning |
|---|---|
| `type` | Descriptive label only (e.g. "fluid bed", "drum") — never used to inherit anything |
| `calibrated` | `true` only where the owner's own logged roasts back the values (currently only `fresh-roast-sr800`) |
| `sources` | URLs of the documents each value was taken from (at least one) |
| `inferred` | Names of the data fields below whose value is **not directly stated by a source** — derived by the rules below or assumed. Any populated data field not listed here was stated by a source. |
| `notes` | Free text: source conflicts, confidence, model quirks |
| `green_weight_min_g`, `green_weight_max_g` | Accepted green batch weight range, whole grams |
| `green_weight_recommended_g` | The manufacturer's normal batch, used for hints; may be `null` |
| `roast_time_min_s`, `first_crack_min_s` | Shortest plausible total roast time / earliest plausible first crack, in seconds. `null` means "use today's 240 s" — set only for roasters whose normal roasts are shorter |
| `profile_grid_minutes` | Number of profile rows, one per whole minute; also the maximum roast time in minutes. Required |
| `temp_unit` | `"F"` or `"C"`: the unit the roaster reports and its profiles/roasts are stored in. `null` when there is no readout |
| `temp_source` | What the reading measures: `bean_probe`, `inlet_air`, `chamber_air` (a chamber, wall, exhaust, or thermostat sensor that does not touch the beans), `unspecified` (a reading exists but the sources do not say what it measures), or `none` |
| `has_temp_readout` | Whether the machine itself provides a temperature reading. When `false`, `temp_source` is `none` and `temp_unit`, `temp_min`, `temp_max` are `null` — no unit or range is invented, and the temperature grid is not shown |
| `temp_min`, `temp_max` | Sanity range for a temperature entry, in the roaster's own unit. Inlet-air roasters need a higher cap than bean-probe roasters (IKAWA inlet air can reach 290 °C) |
| `chart_start_temp`, `chart_inflection_min`, `chart_inflection_temp` | Opening of the live Add Roast chart, in the roaster's own unit: the start temperature, and the minute and temperature of the first inflection. All three set or all three `null`; `null` means no synthetic ramp is drawn. Set only for the Fresh Roast SR series (the app's original constants, tuned on the SR800) — pulled forward from Tier 2 so a °C roaster never gets a °F-numbered chart |

**Rules for values.** Values are stated by a source where one exists; otherwise they are inferred by these rules and listed in `inferred`:
- *Row count* (`profile_grid_minutes`) = the longest roast in the sources' normal range, rounded up to whole minutes, plus 2. Exception: the Fresh Roast SR series is 12 rows, per the owner's experience that about 10 minutes is the longest anyone roasts on it.
- *Minimum batch* = the stated minimum where a source gives one (e.g. SR800: 4 oz; Aillio: 200 g); otherwise the smallest official batch rounded down; otherwise about one third of the maximum, rounded to 5 g (the same ratio as the app's original 100/300 g limits).
- *Temperature range* defaults to 60–500 °F or 15–260 °C unless a source shows readings outside it.
- *Batch size conflicts* between sources take the larger figure, so a valid roast is never rejected; the conflict is recorded in `notes`.
- A roaster with no source at all for a value gets a low-confidence inferred value with that stated in `notes`; it is never presented as measured.

### Roaster data (Tier 2)
Also in each roaster's `values`. The profile wizard reads `wizard` (T-04), and the Add Roast live panel reads `start_model`, `preheat_temp`, `charge_temp`, `cooling_coast_seconds`, and `min_gap_between_roasts_min` (T-05, see "Roaster-driven profiles"). `controls` and `cooling` are not read yet.

| Field | Meaning |
|---|---|
| `start_model` | How a roast begins on the live chart: `ramp` (beans and roaster heat up together from cold — the SR machines), `preheat_charge` (the roaster is preheated, the beans are dropped in, and the bean temperature dips to a turning point), `programmed` (the machine follows a stored recipe from the first second), or `none` (no temperature readout, so no temperature curve). `none` exactly when `has_temp_readout` is false; chart anchors are set only for `ramp` |
| `preheat_temp`, `charge_temp` | Temperature the roaster is preheated to / the beans are charged at, in the roaster's own unit; `null` unless stated (`preheat_charge` roasters only) |
| `controls` | What the user can adjust: a list of `{name, min, max, unit}`. `min`/`max` are `null` where a control exists but its range isn't stated; `unit` is a short label (`level`, `%`, `min`, `A`, `preset`, `temp` = the roaster's own temperature unit, or `variable`/`null`). An empty list means a recipe-driven or fixed-heat machine with no dials |
| `cooling` | `internal` (the roaster cools the beans in its own chamber), `external_tray` (they are ejected or moved to a separate tray), or `manual` |
| `cooling_coast_seconds` | How long a roast keeps developing after cooling starts; `null` until a source gives a number (none has yet) |
| `min_gap_between_roasts_min` | The stated minimum time between roasts: `0` means back-to-back is fine; `null` means no stated requirement |
| `wizard` | `null` when there is no temperature readout, else `{time_to_first_crack_s: {low, medium, high}, natural_time_adjust_s, dtr_by_level, profile_start_temp, default_first_crack_temp}` |

**Wizard values.** `time_to_first_crack_s.medium` is the first-crack time for a medium-density washed coffee at about Full City. `low` equals `medium` and `high` is `medium` plus a density adjustment, which only the SR family has (+30 s, the owner's rule); everyone else has `high = medium` because no source describes an effect. `natural_time_adjust_s` is the change for a natural/honey process (SR: +20 s, the owner's rule; Gene Cafe: −30 s, from Sweet Maria's "up to a minute off"), `null` where no source says. `dtr_by_level` maps the six roast-level names used by `classify_roast` (City Roast … Italian Roast) to a development-time ratio. `profile_start_temp` (the temperature at minute 1) and `default_first_crack_temp` are in the roaster's unit and are `null` unless a source states them — no SR-machine number is ever borrowed for another roaster, so a wizard for such a roaster can offer times but not a temperature curve.

**Rules for Tier 2 values** (in addition to the Tier 1 rules; anything not directly stated by a source is listed in `inferred`, wizard sub-fields by dotted name such as `wizard.dtr_by_level`):
- *First-crack time* is stated where a source gives one (Kaffelogic's worked example, Hottop's worked example, Kaldi reviews, Sandbox, and the owner's SR800 result); otherwise it is the typical Full City roast time × (1 − 0.21), rounded to 5 s.
- *DTR table*: the SR family uses the table rescaled off the owner's SR800 result (12–23%); every other roaster uses the original published table the app started with (City 16%, City Plus 18%, Full City 21%, Full City Plus 24%, Vienna 27%, Italian 31%), which agrees with Kaffelogic's cited 20–25%.
- *`start_model`* is `none` without a readout; `preheat_charge` where a source describes preheating and charging; `programmed` for recipe-driven machines; otherwise `ramp`, inferred.
- Only the SR800 is calibrated; every other wizard value is an estimate to be refined from logged roasts.

**Not sourced from the retailer blog.** A retailer's "best home roasters" blog post (CoffeeRoast Co.) contradicted that retailer's own product pages (it described the Kaffa Wide POP as a 150 g electric air roaster; the product page says a 300 g gas drum roaster) and was not used as a source for any value. "Bohemia 250 (ceramic stovetop)" appeared only in that post, could not be found anywhere else, and was removed from the list (46 roasters).

## Calculations

### Weight Loss
Weight loss percentage is calculated as:
(green weight - finished weight) / green weight × 100

### Development Time
Roast time after first crack calculated as:
(total roast time - time of first crack)

### Calibration report **(T-08)**
A read-only script, `calibration_report.py`, compares logged roasts with each roaster's stored values so those values can be refined from real data (only the SR800 is calibrated so far). It is not part of the web app and imports none of it, so it can be pointed at a copy of the live data (`--records PATH`; default `data/roast_records.json`) without changing anything: it writes no file, and a missing file is an error while a corrupted one stops it with the loaders' message rather than reporting on partial data.
For each roaster with logged roasts (records with no roaster, or one no longer in `roasters.json`, are reported under their own headings without comparisons) it shows the roast count, whether the roaster is marked calibrated, and:
- *Time to first crack*, *total roast time* and *weight loss*: median and range; the first-crack time also against the roaster's stored `wizard.time_to_first_crack_s.medium` (which is for a medium-density washed coffee; records do not store density, so this comparison is rough).
- *Temperature at first crack*, in the roaster's own unit: the actual temperatures are once a minute, so it is the straight line between the two readings either side of first crack; a roast with a missing reading there, or in another unit than the roaster's, is left out. Compared with the stored `wizard.default_first_crack_temp`.
- *Development ratio by roast level*: development time as a share of total roast time, grouped by the roast level `classify_roast` gives the roast's weight loss, next to the stored `wizard.dtr_by_level` for that level.
- For a roaster not yet calibrated, whether it has enough consistent data to consider calibrating: at least 5 roasts whose first-crack times lie within 60 seconds of each other (starting points, not domain rules; the numbers are printed so the owner decides). Records from every owner in the file are combined and no bean names or owners appear.
Saved records are summarized with the original calculation guards opened, as when they are displayed. Editing a roaster's values or setting `calibrated` stays a manual edit of `data/roasters.json`.

## Persistence
Roast records must persist between program executions.
The application will use JSON for storage, in this project's own `data/` folder (seeded from coffeeroaster03's existing `roast_records.json` and `roast_profiles.json` as starting data).
The stored representation of dates must be clearly defined and consistently converted to/from the internal Python date representation.
Existing roast records must not be silently discarded when a new roast is added.
Do not store calculated values in JSON.
Before serving any page, the application shall check the JSON files and if corrupted, notify the user and stop rather than serving stale or partial data.

## Deployment **(Phase 6)**
Deployed to PythonAnywhere's free tier. See `DEPLOY.md` for the step-by-step guide.
`requirements.txt` is provided alongside `pyproject.toml` for PythonAnywhere's pip/virtualenv-based workflow, which does not consume `uv.lock` directly.
`data/` persists on PythonAnywhere's filesystem by default across web app reloads — no volume or database configuration is needed, which is the main reason this platform was chosen over one requiring an explicit persistent-volume mount.
The app's `debug=True` local dev-server flag (in `main()`) never runs in production: PythonAnywhere's WSGI config imports the `app` object directly and serves it through its own WSGI stack, bypassing `app.run()` entirely.
`FLASK_SECRET_KEY` must be set as a real, stable secret in the WSGI config on PythonAnywhere (see `DEPLOY.md`) so signed session cookies survive a reload; locally it falls back to a random key generated at process start, which is fine since that just means local dev-server restarts log everyone out.

## Authentication **(Phase 7)**

### Requirements
Every account is identified by its email address (used as both username and the storage key) and a password, hashed with `werkzeug.security` (already a Flask dependency — no new package).
Each roast record and roast profile has an `owner` (the creating account's email). Every route that reads or writes roast records/profiles requires being logged in, and filters/checks by the current account's ownership — not just in list views, but on every direct-by-ID route too (view, edit, delete), returning 404 rather than the data for another account's record.
Attempting any roast/profile action while logged out redirects to `/login?next=<original path>`, and successfully logging in or signing up redirects back to that original path.
The very first account ever created inherits ownership of any roast record/profile that predates accounts (the seed data) — a one-time migration, not a manual script.
On signup, the account is created and logged in immediately; email verification is *soft* — an unverified account can use every feature with no restriction. Verification only clears a "Verify your email" banner in the header; no route is gated on it, to avoid lockout risk if outbound email is temporarily unavailable.
A logged-in user can trigger a fresh verification email at any time (`POST /resend-verification`), which regenerates their verification token.
A user who forgets their password can request a reset link by email (`/forgot-password`) and set a new password through it (`/reset-password/<token>`), without needing to already be logged in.
Verification and password-reset tokens are single-use, random, and time-limited: a verification token is valid for 24 hours from signup/resend, a reset token for 1 hour from request — reset is the more sensitive action, so it gets the shorter window. Both are cleared (single-use) once acted on.
`/forgot-password` gives the exact same response whether or not the submitted email has an account, and only sends an email / issues a token for an email that does — this prevents the endpoint from being used to discover which emails are registered.

### Constraints
JSON only, same as everything else: accounts live in `data/users.json`, following the same load/corruption-check/save pattern as `roast_records.json`/`roast_profiles.json`.
No password-complexity rules beyond a minimum length — deliberately sparse for now, matching the rest of this app's scope.
Session state is Flask's built-in signed-cookie session — no server-side session store, no new dependency.
Verification/reset emails are sent via Gmail SMTP through the standard-library `smtplib` (`email_sender.py`) — no new Python dependency, and the one outbound SMTP host PythonAnywhere's free tier allowlists. If `GMAIL_ADDRESS`/`GMAIL_APP_PASSWORD` aren't configured in the environment, the email is printed to the server log instead of sent, so the flow stays usable in local development without real credentials.

## About / Feedback **(Phase 8)**

### Requirements
`/about` shall describe the project (currently: a vibe-coding passion project, presently intended for fresh-roast coffee roaster users) and offer a feedback form (message, plus an optional reply-to email).
Submitting the form shall email the site owner via the existing Gmail SMTP integration (`email_sender.py`) — the same account already configured for verification/reset emails.
No email address shall be displayed to users anywhere on the page or in the page source.
The message field is required; an empty submission shall redisplay the form with an explanatory error and the reply-to value preserved.
On success, redirect to `/about?sent=1` and show a confirmation in place of the form.
`/about` stays reachable while logged out, mirroring the home page.

### Constraints
No new external service or dependency — reuses the outbound SMTP path already built for Phase 7 email.

## Roast Intelligence & Data Tools **(Phase 9)**

### Requirements
The roast detail page shall display each roast's weight loss %, roast classification, development time, and development time ratio (DTR% = development time / total roast time × 100) — these were already calculated for the `/roasts` list view but not surfaced on the roast's own detail page.
The roast detail page shall include a Rate of Rise (RoR) chart — the °F-per-minute delta between consecutive whole-minute readings — as its own chart (not sharing an axis with the temperature chart above it), plotting both the target-derived and actual RoR so the two are directly comparable, mirroring the temperature chart's target-vs-actual comparison.
The Add Roast live timer shall display the target profile's current Rate of Rise (a numeric instantaneous derivative of the live target-temperature curve, not a delta between fixed points) below the live temperature/clock readouts, and the live chart shall plot the full target RoR curve against a second, right-hand y-axis alongside the existing temperature curve — a deliberate exception to one-axis-per-chart, since a roaster reads temperature and RoR together in real time off one instrument, matching the convention of dedicated roasting software (e.g. Artisan).
The Add Roast live panel (graph, timer, and readouts) shall stay in a fixed position, vertically centered, while only the form fields on the left scroll; this is a true split pane (the right pane never moves), not a sticky-while-scrolling effect. Mouse wheel scrolling anywhere on the page shall scroll the left form, regardless of which half the cursor is over — not a hover-dependent split-scroll.
The Add Roast live timer shall offer a prominent "First Crack Now!" button, styled as a primary action (not a subordinate inline control), positioned in the live panel below the timer/temperature readouts, that fills the first-crack field with the current elapsed time.
`/roasts` shall offer a text search (matching bean name, profile name, or date) and click-to-sort table headers, applied client-side against the already-rendered table (no new server round-trip).
`/roasts` shall offer a CSV export of the current account's own roast records, using the same columns/order as `ROAST_TABLE_COLUMNS`.
The Add Roast form shall collect optional bean origin, variety, and process fields alongside bean name.
The roast detail page shall offer a form to record cupping notes (free text) and a cupping rating for a saved roast, submittable and re-editable independently of the roast record itself, since tasting happens after roasting is complete, not during the Add Roast submission.

### Constraints
No new external dependency: CSV export uses the standard-library `csv` module; search/sort and the live RoR/split-pane behavior are plain JS, no client-side library.
The `/roasts` list table's columns are unchanged from Phase 1 except for one addition, **Roaster** (Phase 12, directly after Roast Profile, shown as "-" for a record with no roaster or one no longer in `roasters.json`), which the CSV export carries too. Bean origin/variety/process and cupping notes/rating are shown on the roast detail page only, not added to `ROAST_TABLE_COLUMNS`. The list's text search still matches bean name, profile name, or date only.
Cupping notes/rating are optional and have no bearing on any existing calculation (weight loss, DTR, classification).
The fixed-height split-pane and wheel-forwarding behavior on Add Roast is desktop-only; below the existing 640px breakpoint the layout falls back to normal stacked columns and whole-page scrolling.

## Deferred Ideas

These were considered and deliberately not scheduled — noted here so they aren't re-proposed as if new, and so a future decision to pursue one is a conscious choice rather than scope creep:

- **Live roast comparison/overlay** — plotting a past roast's actual curve as a background line behind the live Add Roast graph or the roast detail chart (Artisan's "background profile," in miniature). Deferred: real value, but adds meaningful chart/state complexity; revisit once Phase 9's per-roast metrics are in use and it's clear which past roasts are worth comparing against.
- **Live hardware/thermocouple integration** — reading actual temperature from a roasting machine instead of manual entry. Out of scope: this app is JSON + Flask on PythonAnywhere's free tier, with no path to a persistent serial/Bluetooth connection; this would be a different project.
- **Roast alerts/notifications** — e.g. an audio cue approaching a predicted first-crack window. Deferred: meaningfully more surface area (Web Audio/Notification APIs) and would need historical first-crack data per profile to predict from.
- **Photo attachments** on roast records (bean bag, roast color reference). Deferred: requires blob storage, which breaks the "JSON only" constraint below.

## User Interface
On startup, after checking the JSON files for corruption, the application shall serve the following pages:

1. `/` — Home: a main menu offering Add roast, View roasts, and View and edit roast profiles as buttons, mirroring coffeeroaster03's `MainScreen` (minus Exit, which doesn't apply to a web application). **(Phase 5)** Stays reachable while logged out; the buttons redirect through login if needed.
2. `/signup`, `/login` — create an account / authenticate; `/logout` (POST) ends the session. **(Phase 7)**
   `/verify-email/<token>` — confirms an account's email from the link sent at signup; `/resend-verification` (POST, requires login) re-sends it. `/forgot-password` — request a password-reset link by email; `/reset-password/<token>` — set a new password from that link. **(Phase 7)**
3. `/roasts` — View roasts: displays existing roast records in an HTML table, including a Roast Profile column (and, since Phase 12, a Roaster column after it), using the same fields/order as `ROAST_TABLE_COLUMNS` in coffeeroaster03 apart from that addition. **(Phase 1, moved off `/` in Phase 5, requires login and scoped to the current account as of Phase 7)**
4. `/roasts/<id>` — Roast detail: displays that roast's full time/actual/target temperature table and a line chart (x-axis: time in minutes, y-axis: temperature) plotting actual vs. target temperature, rendered client-side with Chart.js. The table has one row per minute of the record's own lists and the temperatures are in the record's own unit (°F and 12 rows for a record with no roaster, Phase 12); a roast from a roaster with no temperature readout shows no temperature table or charts. It also shows the roast's roaster and, if recorded, its start condition and ambient temperature. **(Phase 1, requires login and ownership as of Phase 7)**
5. Add roast — select a roast profile, then a form to collect roast fields (including the profile's temperature table), validate inline, and save. **(Phase 2, requires login as of Phase 7; saved records are owned by the current account)**
6. View and edit roast profiles — add a new profile, or view/edit existing ones. **(Phase 3, requires login and ownership as of Phase 7)**
7. Delete a roast record, from its detail page, behind a confirmation step. **(Phase 4, requires login and ownership as of Phase 7)**
8. Delete a roast profile, from its edit page, behind a confirmation step that notes how many roast records reference it. **(Phase 4, requires login and ownership as of Phase 7)**
9. `/about` — About: project description and a feedback form, linked from a footer on every page. **(Phase 8)** Stays reachable while logged out.
10. `/roasts/export` — CSV download of the current account's own roast records, same columns as the `/roasts` table. **(Phase 9, requires login and scoped to the current account)**
11. `/roasts/<id>/cupping` (POST) — save or update cupping notes/rating on an existing roast, from its detail page. **(Phase 9, requires login and ownership)**
12. `/profiles/<id>/favorite` (POST) — toggle a profile's favorite flag, from the Add roast profile picker. **(requires login and ownership)**

There is no "Exit" action for a web application; the process runs until the server is stopped.

### Phone-sized screens **(Phase 13)**
Every page shall be usable on a phone (about 360 to 430 px wide) without zooming and without the page scrolling sideways. A table too wide for the screen scrolls sideways inside its own container, with a hint ("Swipe sideways to see every column") shown on phones only.
- *Viewport:* every page inherits `<meta name="viewport" content="width=device-width, initial-scale=1">` from `base.html`; without it a phone lays a page out at 980 px and shrinks it, and no responsive rule applies. A test fails for any page template that does not extend `base.html`.
- *Phone rules* apply at 640 px wide and below: text fields and selects use 16 px text (smaller and iOS zooms the page when one is focused) and are at least 44 px tall; buttons, and the profile favorite stars, are at least 44 px tall; links get extra vertical tap area without moving any text; the header may wrap.
- *Keypads:* weights and temperatures (green and finished weight, the actual-temperature and profile-target grids) ask for a decimal keypad. Times (MM:SS) and the ambient temperature do not: iPhone number pads have no colon or minus sign, and ambient can be negative in °C.
- *Add Roast on a phone* is a single column with the live panel (Start/Reset, chart, temperature and clock readouts, First Crack Now!, pull countdown) above the form, because it is used during the roast and below the form it would be several screens down. The typed date and its calendar button share one row inside the card.
- *Charts* (the live chart and both detail-page charts) are 4:3 on a phone; on wider screens they keep Chart.js's default 2:1. Add Roast keeps its two-column split-pane layout above 640 px (tablets), where the typed date shrinks so the calendar button is never cut off.
- *Not part of this phase:* an installable app (web manifest), keeping the screen awake during a roast, and the splash animation, which is unchanged.

## Tables

### Roast Classification

weight loss percentage <    |   Roast classification
13.01                       |   City Roast
14.51                       |   City Plus
15.51                       |   Full City
16.51                       |   Full City Plus
18.01                       |   Vienna Roast

else: Italian Roast
