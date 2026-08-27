# Coffee Roast Logger Specification

## Purpose
Record coffee roasting sessions and calculate basic roast metrics in Python. The program requests the user inputs, performs calculations, then returns the user input data and calculation results as well as the roast classification according to weight loss percentage.

## Requirements
The code shall have a separate module for calculations.
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
Do not introduce external dependencies.
Do not add a GUI.
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
Continue prompting until valid input is received.

### Bean
Required.
May contain any combination of alphanumeric characters.

### Green Weight
Required.
Input must be numeric.
Input must be greater than 100 and less than 300.
Invalid input must produce a helpful error.
User must be allowed to retry.
User is requested to input a number in grams.

### Finished Weight
Required.
Input must be numeric.
Input must be greater than 100.
Input must be less than green weight.
Invalid input must produce a helpful error.
User must be allowed to retry.
User is requested to input a number in grams.

### Total roast time
Required.
Must be entered in MM:SS format.
Must be ≥ 04:00.
Must be < 20:00.
Display an explanatory error for invalid input.
The error must display the values in MM:SS format.
Continue prompting until valid input is received.
Value must be stored as integer seconds.

### Time of first crack
Required.
Must be entered in MM:SS format.
Must be less than total roast time.
Display an explanatory error for invalid input.
The error must display values in MM:SS format.
Continue prompting until valid input is received.
Values must be stored as integer seconds.

### Roast temperature
Not included in the current version.
Future functionality may allow temperature logging at each minute mark against a selected roast profile.

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

## Tables

### Roast Classification

weight loss percentage <    |   Roast classification
13.01                       |   City Roast
14.51                       |   City Plus
15.51                       |   Full City
16.51                       |   Full City Plus
18.01                       |   Vienna Roast

else: Italian Roast