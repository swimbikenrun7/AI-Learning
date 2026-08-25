# Coffee Roast Logger Specification

## Purpose
Record coffee roasting sessions and calculate basic roast metrics in Python. The program requests the user inputs, performs calculations, then returns the user input data and calculation results as well as the roast classification according to weight loss percentage.

## Requirements
The code shall have a separate module for calculations.
Each module shall have a pytest script written for validation testing.

## User Inputs

### Date
Required.
Must be in the format MM/DD/YYYY.
Must represent a valid calendar date.
Must be ≤ today's date.
Future dates are rejected.
Display an explanatory error for invalid input.
Continue prompting until valid input is received.

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
Continue prompting until valid input is received.

### Time of first crack
Required.
Must be entered in MM:SS format.
Must be less than total roast time.
Display an explanatory error for invalid input.
Continue prompting until valid input is received.

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

## Tables

### Roast Classification

weight loss percentage <    |   Roast classification
13.01                       |   City Roast
14.51                       |   City Plus
15.51                       |   Full City
16.51                       |   Full City Plus
18.01                       |   Vienna Roast

else: Italian Roast