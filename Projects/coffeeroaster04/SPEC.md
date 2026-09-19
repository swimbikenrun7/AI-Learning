# Crackle Specification (Web UI)

## Purpose
Record coffee roasting sessions and calculate basic roast metrics in Python, presented through a browser-based UI instead of a terminal UI. This is an independent iteration of the coffeeroaster exercise (see coffeeroaster01-03); it carries forward the calculation and persistence logic from coffeeroaster03 and replaces only the UI layer.

## Implementation Phases
This SPEC describes the full target feature set, carried forward from coffeeroaster03. It is built in phases; only Phase 1 is in scope until a later phase is explicitly requested.

- **Phase 1**: View roasts (read-only table) and a roast detail page with a temperature chart. Uses data seeded from coffeeroaster03's existing JSON files.
- **Phase 2**: Add roast form.
- **Phase 3**: Roast profile management (add/view/edit).
- **Phase 4**: Delete roast records and delete roast profiles. This did not exist in coffeeroaster03 (which had no delete for either) — it is new scope for this mission, not something carried forward.
- **Phase 5**: Home page becomes a main menu (Add roast / View roasts / View and edit roast profiles as buttons), mirroring coffeeroaster03's `MainScreen`. The roast records table moves to its own `/roasts` route.
- **Phase 6**: Deploy to PythonAnywhere.
- **Phase 7**: User accounts. Each account has its own private roast records and profiles — the earlier "no authentication" decision applied while this was a purely local, single-user tool; it no longer holds once the app is reachable on the open internet.
- **Phase 8**: About page. Static project description plus a feedback form that emails the site owner directly — no user-visible email address, no new external service.
- **Phase 9**: Roast intelligence & data tools. Surfaces calculated roast quality metrics that already had the underlying data, plus search/sort, CSV export, a live first-crack marking shortcut, and richer per-roast metadata (bean origin/variety/process, post-roast cupping notes).
- **Phase 11 (current)**: Roaster selection. A reference list of home coffee roasters (`data/roasters.json`) and a roaster dropdown on the roast profile form, shown alongside the profile name wherever profiles are listed or used — groundwork for later customizing profiles and the Add Roast experience per roaster.
- **Phase 10**: Roast profile wizard. An opt-in helper on the Add roast profile page that recommends a starting Maillard-phase target-temperature curve plus target first-crack/development-time reference values, from bean characteristics, desired roast level, and the user's own observed first-crack temperature, which the user can then edit before saving. The target reference values also drive a live pull countdown timer on the Add Roast page once first crack is marked.

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
Page-specific JavaScript and CSS live as plain files under `static/` (served by Flask's built-in `/static/` route) rather than inline in templates; per-page data reaches them through a JSON data island in the template, not Jinja interpolated into script code. Still no build step.
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
A roast profile may also store a target first-crack time (MM:SS) and a target development time (MM:SS), both optional, fixed reference values shown in the Add Roast live panel, directly above the "First Crack Now!" button — not modeled as part of the temperature curve. **(Phase 10)**
Once a first-crack time is set on the Add Roast page (via "First Crack Now!" or by typing directly into the field) and the selected profile has a target development time, a pull countdown shall appear below the "First Crack Now!" button, live-updating as `first crack time + target development time − elapsed time` until it reaches zero, then holding at "Pull now!". Reaching zero triggers a quadruple flash (the existing per-whole-minute flash — see Phase 9 — is a double flash; this is visually distinct and reserved for the pull moment specifically). **(Phase 10)**
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
No new dependency and no server round-trip: the wizard is client-side JS on the profile form page, reading its own inputs and writing directly into the existing `temp_1`–`temp_12`, `target_first_crack`, and `target_development_time` fields; nothing about the wizard's inputs is persisted.
Per-tier development time ratio (DTR = development time ⁄ total time) targets were originally drawn from commonly published drum-roaster guidance, which turned out to run meaningfully slower than fluid-bed home roasters like the Fresh Roast machines this app targets — first-crack estimates around 8-9 minutes, versus the roughly 4-8 minute range reported for Fresh Roast machines by Sweet Maria's own SR540 tip sheet and corroborating sources. The DTR table was rescaled by a uniform factor off one real logged Fresh Roast result (medium density, washed: 6:15 first crack, 1:10 development time, landed at Full City, i.e. ~15.7% DTR versus the original table's 21%), preserving the table's original relative shape (darker roasts still carry a higher DTR) while anchoring the absolute scale to this machine.
Time to first crack (`MAILLARD_TIME_SECONDS`, `NATURAL_TIME_ADJUST_SECONDS` in `profile_form.html`) is a direct density/process-driven time target, not derived from the entered first-crack temperature. An earlier version computed time as (entered FC temp − a fixed start temp) ÷ a density-based pace, which conflated the FC temperature (which legitimately varies a lot by bean/instrument/altitude) with roast duration (which real-world use showed barely varies with density) — a high-altitude bean entered at a notably higher FC temp produced a wildly inflated multi-minute estimate, and because that estimate could exceed the temp grid's whole-minute cap while the displayed target first-crack field did not, the grid and the reference field could visibly disagree. The corrected model anchors medium/washed at 6:15 (the one real logged result) and applies the user's own rule of thumb for the deltas (high density ~30s later; natural process ~20s later); low density is treated as no different from medium, per the same source. The entered first-crack temperature is used only to set where the displayed Maillard curve ends, not to estimate its duration.
This is a rough first pass, not a validated model — only one real logged result exists, for one density/process combination, plus the user's own rule-of-thumb estimates for the others; the values should be revisited once more real roasts are logged across a range of density/process/roast-level combinations.

## Roasters **(Phase 11)**

### Requirements
`data/roasters.json` shall list known home coffee roasters, keyed by a stable slug id (e.g. `fresh-roast-sr800`), each with a display `name` and a `values` object reserved for roaster-specific settings. `values` is intentionally empty for now — which settings matter (batch size, heat/fan ranges, typical first-crack temperature, etc.) will be decided later, once roaster-specific behavior is built on top of this.
The add/edit roast profile form shall offer a roaster dropdown (alphabetical, with a blank "No roaster selected" default), placed above the profile wizard so the wizard's inputs can later depend on it. The choice is stored on the profile as `roaster_id`.
Selecting a roaster is optional. Profiles created before this phase have no `roaster_id` and continue to work unchanged.
A profile's roaster name shall be displayed, in a faint italic style (`.roaster-tag`) so it reads as a different kind of data than the profile name, on: the View and edit roast profiles list, the Add Roast profile picker, and the Add Roast page heading (i.e. it propagates from the selected profile). It is omitted when the profile has no roaster.

### Constraints
`roasters.json` is read-only reference data loaded once at startup, following the same load/corruption-check pattern as the other JSON files. Unlike `roast_records.json`, `roast_profiles.json`, and `users.json`, it is **tracked in git** — it ships with the app rather than holding live user data.
A submitted `roaster_id` must be blank or a key of `roasters.json`; anything else is rejected with a validation error.
A profile stores only the roaster's id, not its name, so renaming a roaster in `roasters.json` is reflected everywhere. If a profile's roaster id is later removed from the file, the profile still works and simply shows no roaster.
Roast records do not snapshot the roaster (unlike `target_temps`): the Add Roast page reads it from the profile, and the roast detail page is unchanged.

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
The `/roasts` list table's columns are unchanged — bean origin/variety/process and cupping notes/rating are shown on the roast detail page only, not added to `ROAST_TABLE_COLUMNS`.
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
3. `/roasts` — View roasts: displays existing roast records in an HTML table, including a Roast Profile column, using the same fields/order as `ROAST_TABLE_COLUMNS` in coffeeroaster03. **(Phase 1, moved off `/` in Phase 5, requires login and scoped to the current account as of Phase 7)**
4. `/roasts/<id>` — Roast detail: displays that roast's full time/actual/target temperature table (1:00-12:00) and a line chart (x-axis: time in minutes, y-axis: temperature °F) plotting actual vs. target temperature, rendered client-side with Chart.js. **(Phase 1, requires login and ownership as of Phase 7)**
5. Add roast — select a roast profile, then a form to collect roast fields (including the profile's temperature table), validate inline, and save. **(Phase 2, requires login as of Phase 7; saved records are owned by the current account)**
6. View and edit roast profiles — add a new profile, or view/edit existing ones. **(Phase 3, requires login and ownership as of Phase 7)**
7. Delete a roast record, from its detail page, behind a confirmation step. **(Phase 4, requires login and ownership as of Phase 7)**
8. Delete a roast profile, from its edit page, behind a confirmation step that notes how many roast records reference it. **(Phase 4, requires login and ownership as of Phase 7)**
9. `/about` — About: project description and a feedback form, linked from a footer on every page. **(Phase 8)** Stays reachable while logged out.
10. `/roasts/export` — CSV download of the current account's own roast records, same columns as the `/roasts` table. **(Phase 9, requires login and scoped to the current account)**
11. `/roasts/<id>/cupping` (POST) — save or update cupping notes/rating on an existing roast, from its detail page. **(Phase 9, requires login and ownership)**

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
