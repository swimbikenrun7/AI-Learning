# Coffee Roast Logger 0.1

## Purpose

Write a command-line application that will record coffee roasting information and calculate weight loss (roast level)

## Planned features

- Enter roast information
- Calculate weight loss
- Save sessions
- View previous roasts
- Graph trends
- AI roast recommendations
- Notes about roast quality/preference

## Architecture

The application currently consists of:

- `main.py` — command-line user interface
- `calculations.py` — coffee-related calculations
- `test_calculations.py` — automated tests for calculations

## Input requirements

Date
    - must be in the format MM/DD/YYYY
    - YYYY must be less than or equal to today()
    - The program must continue requesting an input until the user provides a valid value.

Green weight
    - must be numeric
    - must be greater than 100 and less than 300
    - values less than 100 or more than 300 trigger a warning
    - The program must continue requesting an input until the user provides a valid value.

Finished weight
    - must be numeric
    - must be greater than 100 and less than 300
    - values less than 100 or more than 300 trigger a warning
    - must be less than green weight
    - The program must continue requesting an input until the user provides a valid value.