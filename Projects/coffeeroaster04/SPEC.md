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
- **Phase 9 (current)**: Roast intelligence & data tools. Surfaces calculated roast quality metrics that already had the underlying data, plus search/sort, CSV export, a live first-crack marking shortcut, and richer per-roast metadata (bean origin/variety/process, post-roast cupping notes).

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
The roast detail page's chart shall include a Rate of Rise (RoR) series — the °F-per-minute delta between consecutive whole-minute actual temperature readings — plotted against a second y-axis alongside the existing actual/target temperature lines.
`/roasts` shall offer a text search (matching bean name, profile name, or date) and click-to-sort table headers, applied client-side against the already-rendered table (no new server round-trip).
`/roasts` shall offer a CSV export of the current account's own roast records, using the same columns/order as `ROAST_TABLE_COLUMNS`.
The Add Roast live timer shall offer a "Mark first crack now" button that fills the first-crack field with the current elapsed time, as an alternative to typing it in after the fact.
The Add Roast form shall collect optional bean origin, variety, and process fields alongside bean name.
The roast detail page shall offer a form to record cupping notes (free text) and a cupping rating for a saved roast, submittable and re-editable independently of the roast record itself, since tasting happens after roasting is complete, not during the Add Roast submission.

### Constraints
No new external dependency: CSV export uses the standard-library `csv` module; search/sort is plain JS, no client-side library.
The `/roasts` list table's columns are unchanged — bean origin/variety/process and cupping notes/rating are shown on the roast detail page only, not added to `ROAST_TABLE_COLUMNS`.
Cupping notes/rating are optional and have no bearing on any existing calculation (weight loss, DTR, classification).

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
