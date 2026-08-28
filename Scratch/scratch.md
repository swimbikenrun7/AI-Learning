Review this coffee logger specification (Coffee Roast Logger Specification) and current code (main.py and calculations.py). Propose a simple architecture for implementing the command-line menu. Do not modify the code yet.

Identify the responsibilities that should remain separate, particularly:

loading/saving data
collecting user input
validation
calculations
displaying records
controlling the application menu

Keep the architecture as simple as reasonably possible for this project. Do not introduce classes, databases, frameworks, external dependencies, or additional modules unless you can explain why they are necessary.

# main.py
import os
import json
from pathlib import Path
from datetime import datetime
import calculations as calc

def validate_roast_records(records):
    if not records:
        raise ValueError("Roast records file is empty.")
    
    for record_id, record in records.items():
        if not isinstance(record_id, str) or not isinstance(record, dict):
            raise ValueError(f"Invalid record format at ID: {record_id}")
        
        required_fields = {"green_weight", "finished_weight", "total_roast_time", "time_of_first_crack"}
        if not required_fields.issubset(record):
            raise ValueError(f"Missing required fields in record ID: {record_id}")
        
def get_date():
    while True:
        date_str = input("Enter the date (MM/DD/YYYY): ")
        try:
            date_obj = datetime.strptime(date_str, "%m/%d/%Y")
            if date_obj > datetime.now():
                raise ValueError("Date cannot be in the future.")
            return date_obj.strftime("%m/%d/%Y")
        except ValueError as e:
            print(f"Invalid input: {e}")

def get_bean_name():
    return input("Enter the bean name: ")

def get_green_weight():
    while True:
        try:
            green_weight = float(input("Enter the green weight (in grams): "))
            if green_weight < 100 or green_weight > 300:
                raise ValueError
            return green_weight
        except ValueError:
            print("Invalid input. Please enter a numeric value greater than 100 and less than 300.")

def get_finished_weight(green_weight):
    while True:
        try:
            finished_weight = float(input("Enter the finished weight (in grams): "))
            if finished_weight < 100 or finished_weight > green_weight:
                raise ValueError
            return finished_weight
        except ValueError:
            print("Invalid input. Please enter a numeric value greater than 100 and less than the green weight.")

def get_roast_time():
    while True:
        time_str = input("Enter the total roast time (MM:SS): ")
        try:
            minutes, seconds = map(int, time_str.split(':'))
            total_seconds = minutes * 60 + seconds
            if total_seconds < 240 or total_seconds >= 1200:
                raise ValueError
            return total_seconds
        except ValueError:
            print("Invalid input. Please enter a value in MM:SS format between 04:00 and 20:00.")

def get_time_of_first_crack(total_roast_time):
    while True:
        time_str = input("Enter the time of first crack (MM:SS): ")
        try:
            minutes, seconds = map(int, time_str.split(':'))
            total_seconds = minutes * 60 + seconds
            if total_seconds >= total_roast_time:
                raise ValueError
            return total_seconds
        except ValueError:
            print("Invalid input. Please enter a value in MM:SS format less than the total roast time.")

def main():
    data_dir = Path(__file__).resolve().parent.parent / "data"
    roast_records_path = data_dir / "roast_records.json"

    try:
        records = calc.get_roast_records(roast_records_path)
        validate_roast_records(records)

    except FileNotFoundError:
        print("Roast records file not found. Starting with an empty record set.")
        records = {}

    except json.JSONDecodeError as e:
        print(f"Failed to decode roast records file: {e}")
        print("Starting with an empty record set.")
        records = {}
    
    except ValueError as e:
        print(f"Invalid roast records data: {e}")
        print("Exiting the program due to corrupted data.")
        return

    while True:
    
        date = get_date()
        bean_name = get_bean_name()
        green_weight = get_green_weight()
        finished_weight = get_finished_weight(green_weight)
        total_roast_time = get_roast_time()
        time_of_first_crack = get_time_of_first_crack(total_roast_time)
    
        weight_loss = calc.calculate_weight_loss(green_weight, finished_weight)
        development_time = calc.calculate_development_time(total_roast_time, time_of_first_crack)
        roast_classification = calc.classify_roast(weight_loss)
    
        new_record = {
            "date": date,
            "bean_name": bean_name,
            "green_weight": green_weight,
            "finished_weight": finished_weight,
            "total_roast_time": total_roast_time,
            "time_of_first_crack": time_of_first_crack,
            "weight_loss": weight_loss,
            "development_time": development_time,
            "roast_classification": roast_classification
    }
    
        records[date] = new_record
        calc.save_roast_records(records)
    
        print("Roast record saved successfully.")
        print(f"Date: {date}")
        print(f"Bean Name: {bean_name}")
        print(f"Green Weight: {green_weight}g")
        print(f"Finished Weight: {finished_weight}g")
        print(f"Weight Loss: {weight_loss:.2f}%")
        print(f"Total Roast Time: {total_roast_time // 60}:{total_roast_time % 60:02d}")
        print(f"Time of First Crack: {time_of_first_crack // 60}:{time_of_first_crack % 60:02d}")
        print(f"Development Time: {development_time // 60}:{development_time % 60:02d}")
        print(f"Roast Classification: {roast_classification}")

if __name__ == "__main__":
    main()

# calculations.py
import json
import os
from pathlib import Path

## Constants for roast classification
ROAST_CLASSIFICATION = {
    13.01: 'City Roast',
    14.51: 'City Plus',
    15.51: 'Full City',
    16.51: 'Full City Plus',
    18.01: 'Vienna Roast'
}

def calculate_weight_loss(green_weight, finished_weight):
    if green_weight < 100 or green_weight > 300:
        raise ValueError("Green weight must be greater than 100 and less than 300 grams.")
    return ((green_weight - finished_weight) / green_weight) * 100

def calculate_development_time(total_roast_time, time_of_first_crack):
    if total_roast_time < 240 or time_of_first_crack >= total_roast_time:
        raise ValueError("Total roast time must be between 04:00 and 20:00.")
    return total_roast_time - time_of_first_crack

def classify_roast(weight_loss):
    for threshold, classification in ROAST_CLASSIFICATION.items():
        if weight_loss < threshold:
            return classification
    return 'Italian Roast'

def get_roast_records(file_path='data/roast_records.json'):
    full_path = Path(__file__).resolve().parent.parent / "data" / "roast_records.json"
    
    if full_path.exists():
        with open(full_path, 'r') as file:
            try:
                records = json.load(file)
                return records
            except json.JSONDecodeError:
                pass
    return {}

def save_roast_records(records, file_path='data/roast_records.json'):
    full_path = Path(__file__).resolve().parent.parent / "data" / "roast_records.json"
    os.makedirs(full_path.parent, exist_ok=True)
    
    with open(full_path, 'w') as file:
        json.dump(records, file, indent=4)

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

## Command-Line Interface
When the application starts, after checking the json for corrupt data it shall load existing roast records and display a menu.
The menu shall provide the following options:
1. Add roast
2. View roasts
3. Exit
Selecting Add roast shall collect and validate the required roast fields and save the resulting record.
Selecting View roasts shall display existing roast records.
Selecting Exit shall terminate the application.
After completing Add roast or View roasts, the application shall return to the main menu.
An invalid menu selection shall display an appropriate message and return to the menu without terminating the application.

## Tables

### Roast Classification

weight loss percentage <    |   Roast classification
13.01                       |   City Roast
14.51                       |   City Plus
15.51                       |   Full City
16.51                       |   Full City Plus
18.01                       |   Vienna Roast

else: Italian Roast