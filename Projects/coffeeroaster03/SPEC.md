# Coffee Roast Logger Specification

## Purpose
Record coffee roasting sessions and calculate basic roast metrics in Python. The program requests the user inputs, performs calculations, then returns the user input data and calculation results as well as the roast classification according to weight loss percentage.

## Requirements
The code shall have a separate module for calculations.
The code shall have a separate module (or package) for the Textual interface, isolated from calculations.py and data_persistence.py.
calculations.py and data_persistence.py shall not import from or depend on the Textual UI module.
Each module shall have a pytest script written for validation testing.
Tests shall be stored in the tests/ folder in the parent directory.
Persistent data shall be written to a JSON file in the data/ folder in the parent directory.
Load existing roast records when the program starts.
If the data file does not yet exist, start with an empty dataset.
Save roast records when a new roast is added.
Preserve all existing roast records when adding a new record.
Convert dates appropriately between the Python internal representation and JSON storage.

## Constraints
JSON only; do not introduce a database.
Do not introduce external dependencies except the `textual` package (and its own required dependencies) for the UI layer.
The UI shall be built with Textual (a terminal UI, not a desktop/web GUI).
Do not change the existing calculation formulas.
Do not delete existing functionality.
Keep the architecture reasonably simple.
Add automated tests for persistence behavior.
Explain the proposed changes before implementing them.

## User Inputs

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
The main screen shall provide a "View and edit roast profiles" action leading to a submenu offering: add a new roast profile, and view/edit existing roast profiles.
A roast profile shall consist of a name and a target temperature (°F) for each whole-minute interval from 1:00 through 12:00 (12 data points).
Temperature entries within a profile are optional per minute.
Any minute interval left blank in a profile shall default to the most recently entered temperature at an earlier interval (carry-forward). An interval with no earlier entry has no default.
Selecting Add roast shall first require selecting an existing roast profile before the roast entry form is shown.
If no roast profiles exist, the user shall be directed to create one before a roast can be added.
The Add roast form shall present a table of time / actual temperature (°F) / target temperature (°F) for minutes 1:00 through 12:00, positioned after Green Weight and before Time of First Crack, which remains a standalone field.
The target temperature column shall be pre-populated and read-only, sourced from the selected profile with carry-forward applied.
The actual temperature column shall be manually entered by the user; entries are optional per minute.
At submission, if total roast time exceeds the last whole minute at which an actual temperature was entered, the latest entered actual temperature shall be used to populate the remaining whole-minute intervals up to total roast time.
Each saved roast record shall store the id of the selected roast profile and a snapshot of the resolved (carry-forward-applied) target temperatures as of the time the roast was saved.

### Constraints
Temperature values (profile targets and actual roast entries) must be numeric and between 60 and 500 °F when provided.
Editing a roast profile after a roast has been saved against it shall not alter the target temperatures already stored on that roast record (snapshot at save time, not a live reference).
Roast profile persistence shall use its own JSON file in the data/ folder, following the same load/corruption-check/save pattern as roast records.

### Domain rules
Roast profile intervals are defined in whole minutes only; there is no sub-minute granularity.
A profile's (or a roast's actual) temperature at any interval beyond the last explicitly entered value equals that last entered value, since a roast in progress, or a profile author, may only have data through a given point in time.

## Calculations

### Weight Loss
Weight loss percentage is calculated as:
(green weight - finished weight) / green weight × 100

### Development Time
Roast time after first crack calculated as:
(total roast time - time of first crack)

## Persistence
Roast records must persist between program executions.
The application will use JSON for initial persistent storage.
The stored representation of dates must be clearly defined and consistently converted to/from the internal Python date representation.
Existing roast records must not be silently discarded when a new roast is added.
Do not store calculated values in JSON.
Before querying user data, the program shall check the JSON file and if corrupted notify the user and exit the program.

## User Interface
When the application starts, after checking the JSON for corrupt data it shall load existing roast records and display the main screen.
The main screen shall provide the following actions:
1. Add roast
2. View roasts
3. View and edit roast profiles
4. Exit
Selecting Add roast shall first prompt the user to select a roast profile, then present a form to collect the required roast fields (including the profile's temperature table), validate them inline, and save the resulting record on submission.
Selecting View roasts shall display existing roast records in a table/data-grid widget.
Selecting View and edit roast profiles shall present a submenu to add a new roast profile or view/edit existing ones.
Selecting Exit shall terminate the application.
After completing Add roast or View roasts, the application shall return to the main screen.
Roast records table shall be rendered using the same fields/order as ROAST_TABLE_COLUMNS in the current implementation.

## Tables

### Roast Classification

weight loss percentage <    |   Roast classification
13.01                       |   City Roast
14.51                       |   City Plus
15.51                       |   Full City
16.51                       |   Full City Plus
18.01                       |   Vienna Roast

else: Italian Roast