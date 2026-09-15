# Coffee Roast Logger Specification (Web UI)

## Purpose
Record coffee roasting sessions and calculate basic roast metrics in Python, presented through a browser-based UI instead of a terminal UI. This is an independent iteration of the coffeeroaster exercise (see coffeeroaster01-03); it carries forward the calculation and persistence logic from coffeeroaster03 and replaces only the UI layer.

## Implementation Phases
This SPEC describes the full target feature set, carried forward from coffeeroaster03. It is built in phases; only Phase 1 is in scope until a later phase is explicitly requested.

- **Phase 1**: View roasts (read-only table) and a roast detail page with a temperature chart. Uses data seeded from coffeeroaster03's existing JSON files.
- **Phase 2**: Add roast form.
- **Phase 3**: Roast profile management (add/view/edit).
- **Phase 4**: Delete roast records and delete roast profiles. This did not exist in coffeeroaster03 (which had no delete for either) — it is new scope for this mission, not something carried forward.
- **Phase 5 (current)**: Home page becomes a main menu (Add roast / View roasts / View and edit roast profiles as buttons), mirroring coffeeroaster03's `MainScreen`. The roast records table moves to its own `/roasts` route.

## Requirements
The code shall have a separate module for calculations (`calculations.py`, carried forward from coffeeroaster03 unchanged).
The code shall have a separate module for persistence (`data_persistence.py`, carried forward from coffeeroaster03, adapted only for this project's own `data/` path).
The code shall have a separate module/package for the web interface (Flask routes + Jinja2 templates), isolated from `calculations.py` and `data_persistence.py`.
`calculations.py` and `data_persistence.py` shall not import from or depend on the Flask/web module.
Each module shall have a pytest script written for validation testing.
Persistent data shall be written to a JSON file in the `data/` folder in the parent directory.
Load existing roast records when the application starts.
If the data file does not yet exist, start with an empty dataset.
Save roast records when a new roast is added (Phase 2).
Preserve all existing roast records when adding a new record.
Convert dates appropriately between the Python internal representation and JSON storage.

## Constraints
JSON only; do not introduce a database.
Do not introduce external Python dependencies except `flask` (and its own required dependencies, e.g. Jinja2, Werkzeug) for the web layer.
Charting is rendered client-side via Chart.js, loaded from a CDN `<script>` tag — this is not a Python package dependency and introduces no build tooling (no npm, no bundler, no SPA framework).
The UI shall be a server-rendered web application (Flask + Jinja2 templates), not a terminal UI and not a single-page JS application.
Do not change the existing calculation formulas.
Do not delete existing functionality once implemented in this mission.
Keep the architecture reasonably simple.
Explain the proposed changes before implementing them.

## User Inputs
*(These are domain/validation rules carried forward unchanged from coffeeroaster03. In Phase 1 they apply to the seeded records already on disk; there is no web form collecting them until Phase 2 — see Implementation Phases.)*

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

## Roast Profiles

### Requirements
The application shall provide a "View and edit roast profiles" area leading to add-a-new-profile and view/edit-existing-profiles pages. **(Phase 3)**
A roast profile shall consist of a name and a target temperature (°F) for each whole-minute interval from 1:00 through 12:00 (12 data points).
Temperature entries within a profile are optional per minute.
Any minute interval left blank in a profile shall default to the most recently entered temperature at an earlier interval (carry-forward). An interval with no earlier entry has no default.
Selecting Add roast shall first require selecting an existing roast profile before the roast entry form is shown. **(Phase 2)**
If no roast profiles exist, the user shall be directed to create one before a roast can be added. **(Phase 2/3)**
The Add roast form shall present a table of time / actual temperature (°F) / target temperature (°F) for minutes 1:00 through 12:00, positioned after Green Weight and before Time of First Crack, which remains a standalone field. **(Phase 2)**
The target temperature column shall be pre-populated and read-only, sourced from the selected profile with carry-forward applied.
The actual temperature column shall be manually entered by the user; entries are optional per minute.
At submission, if total roast time exceeds the last whole minute at which an actual temperature was entered, the latest entered actual temperature shall be used to populate the remaining whole-minute intervals up to total roast time.
Each saved roast record shall store the id of the selected roast profile and a snapshot of the resolved (carry-forward-applied) target temperatures as of the time the roast was saved.

### Constraints
Temperature values (profile targets and actual roast entries) must be numeric and between 60 and 500 °F when provided.
Editing a roast profile after a roast has been saved against it shall not alter the target temperatures already stored on that roast record (snapshot at save time, not a live reference).
Roast profile persistence shall use its own JSON file in the `data/` folder, following the same load/corruption-check/save pattern as roast records.

### Domain rules
Roast profile intervals are defined in whole minutes only; there is no sub-minute granularity.
A profile's (or a roast's actual) temperature at any interval beyond the last explicitly entered value equals that last entered value, since a roast in progress, or a profile author, may only have data through a given point in time.

### Delete **(Phase 4)**
A roast profile may be deleted, with a confirmation step first.
Deleting a profile that past roast records reference shall not alter those records' stored `target_temps` snapshot or any other field (they hold their own copy at save time, not a live reference — see Constraints above). Such records shall continue to display normally, showing no profile name for the now-missing reference (same behavior as a record whose profile was never set).

## Calculations

### Weight Loss
Weight loss percentage is calculated as:
(green weight - finished weight) / green weight × 100

### Development Time
Roast time after first crack calculated as:
(total roast time - time of first crack)

## Persistence
Roast records must persist between program executions.
The application will use JSON for storage, in this project's own `data/` folder (seeded from coffeeroaster03's existing `roast_records.json` and `roast_profiles.json` as starting data).
The stored representation of dates must be clearly defined and consistently converted to/from the internal Python date representation.
Existing roast records must not be silently discarded when a new roast is added.
Do not store calculated values in JSON.
Before serving any page, the application shall check the JSON files and if corrupted, notify the user and stop rather than serving stale or partial data.

## User Interface
On startup, after checking the JSON files for corruption, the application shall serve the following pages:

1. `/` — Home: a main menu offering Add roast, View roasts, and View and edit roast profiles as buttons, mirroring coffeeroaster03's `MainScreen` (minus Exit, which doesn't apply to a web application). **(Phase 5)**
2. `/roasts` — View roasts: displays existing roast records in an HTML table, including a Roast Profile column, using the same fields/order as `ROAST_TABLE_COLUMNS` in coffeeroaster03. **(Phase 1, moved off `/` in Phase 5)**
3. `/roasts/<id>` — Roast detail: displays that roast's full time/actual/target temperature table (1:00-12:00) and a line chart (x-axis: time in minutes, y-axis: temperature °F) plotting actual vs. target temperature, rendered client-side with Chart.js. **(Phase 1)**
4. Add roast — select a roast profile, then a form to collect roast fields (including the profile's temperature table), validate inline, and save. **(Phase 2)**
5. View and edit roast profiles — add a new profile, or view/edit existing ones. **(Phase 3)**
6. Delete a roast record, from its detail page, behind a confirmation step. **(Phase 4)**
7. Delete a roast profile, from its edit page, behind a confirmation step that notes how many roast records reference it. **(Phase 4)**

There is no "Exit" action for a web application; the process runs until the server is stopped.

## Tables

### Roast Classification

weight loss percentage <    |   Roast classification
13.01                       |   City Roast
14.51                       |   City Plus
15.51                       |   Full City
16.51                       |   Full City Plus
18.01                       |   Vienna Roast

else: Italian Roast
