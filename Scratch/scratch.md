Review the code below and diagnose why roast_records.json is being overwritten instead of appended when option 1 is selected in the menu. i've pasted all modules:

# calculations.py

def calculate_weight_loss(green_weight, finished_weight):
    if green_weight < 100 or green_weight > 300:
        raise ValueError(
            "Green weight must be greater than 100 and less than 300 grams."
        )
    return ((green_weight - finished_weight) / green_weight) * 100


def calculate_development_time(total_roast_time, time_of_first_crack):
    if total_roast_time < 240 or time_of_first_crack >= total_roast_time:
        raise ValueError("Total roast time must be between 04:00 and 20:00.")
    return total_roast_time - time_of_first_crack


def classify_roast(weight_loss):
    ROAST_CLASSIFICATION = {
        13.01: "City Roast",
        14.51: "City Plus",
        15.51: "Full City",
        16.51: "Full City Plus",
        18.01: "Vienna Roast"
    }
    for threshold, classification in ROAST_CLASSIFICATION.items():
        if weight_loss < threshold:
            return classification
    return "Italian Roast"

# data_persistence.py

import sys
import json
import os
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
ROAST_RECORDS_PATH = DATA_DIR / "roast_records.json"


def load_roast_records():
    if ROAST_RECORDS_PATH.exists():
        with open(ROAST_RECORDS_PATH, "r") as file:
            try:
                records = json.load(file)
                for date in records:
                    records[date]['date'] = datetime.strptime(
                        records[date]['date'], "%m/%d/%Y"
                    ).strftime("%m/%d/%Y")
                return records
            except json.JSONDecodeError:
                print(
                    "Failed to decode roast records file. Starting with an empty record set."
                )
    return {}


def save_roast_records(records):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ROAST_RECORDS_PATH, "w") as file:
        json.dump(records, file, indent=4)


def count_roasts():
       try:
           with open('data/roast_records.json', "r") as file:
               data = json.load(file)
               return len(data)
       except FileNotFoundError:
           return 0
       except json.JSONDecodeError:
           print("Error: The data file is corrupted. Exiting the program.")
           sys.exit(1)

# ui.py

import calculations as calc
from data_persistence import count_roasts, load_roast_records, save_roast_records
from user_input import (
    get_bean_name,
    get_date,
    get_finished_weight,
    get_green_weight,
    get_roast_time,
    get_time_of_first_crack,
)

ROAST_RECORDS = load_roast_records()


def display_menu():
    print("1. Add roast")
    print("2. View roasts")
    print("3. Count roasts")
    print("4. Exit")


def add_roast():
    date = get_date()
    bean_name = get_bean_name()
    green_weight = get_green_weight()
    finished_weight = get_finished_weight(green_weight)
    total_roast_time = get_roast_time()
    time_of_first_crack = get_time_of_first_crack(total_roast_time)

    weight_loss = calc.calculate_weight_loss(green_weight, finished_weight)
    development_time = calc.calculate_development_time(
        total_roast_time, time_of_first_crack
    )
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

    ROAST_RECORDS[date] = new_record
    save_roast_records(ROAST_RECORDS)
    print("Roast added successfully.")


def view_roasts():
    for date, record in ROAST_RECORDS.items():
        print(f"Date: {record['date']}")
        print(f"Bean Name: {record['bean_name']}")
        print(f"Green Weight: {record['green_weight']}g")
        print(f"Finished Weight: {record['finished_weight']}g")
        print(f"Total Roast Time: {record['total_roast_time']}s")
        print(f"Time of First Crack: {record['time_of_first_crack']}s")
        print(f"Weight Loss: {record['weight_loss']:.2f}%")
        print(f"Development Time: {record['development_time']}s")
        print(f"Roast Classification: {record['roast_classification']}")
        print("-" * 40)


def main():
    while True:
        display_menu()
        choice = input("Enter your choice (1/2/3/4): ")

        if choice == "1":
            add_roast()
        elif choice == "2":
            view_roasts()
        elif choice == "3":
            total_roasts = count_roasts()
            print(f"Total number of stored roasts: {total_roasts}")
        elif choice == "4":
            break
        else:
            print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()

# user_input.py

from datetime import datetime


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
            print(
                "Invalid input. Please enter a numeric value greater than 100 and less than 300."
            )


def get_finished_weight(green_weight):
    while True:
        try:
            finished_weight = float(input("Enter the finished weight (in grams): "))
            if finished_weight < 100 or finished_weight > green_weight:
                raise ValueError
            return finished_weight
        except ValueError:
            print(
                "Invalid input. Please enter a numeric value greater than 100 and less than the green weight."
            )


def get_roast_time():
    while True:
        time_str = input("Enter the total roast time (MM:SS): ")
        try:
            minutes, seconds = map(int, time_str.split(":"))
            total_seconds = minutes * 60 + seconds
            if total_seconds < 240 or total_seconds >= 1200:
                raise ValueError
            return total_seconds
        except ValueError:
            print("Invalid input. Please enter a value in MM:SS format.")


def get_time_of_first_crack(total_roast_time):
    while True:
        time_str = input("Enter the time of first crack (MM:SS): ")
        try:
            minutes, seconds = map(int, time_str.split(":"))
            total_seconds = minutes * 60 + seconds
            if total_seconds < 240 or total_seconds >= total_roast_time:
                raise ValueError
            return total_seconds
        except ValueError:
            print("Invalid input. Please enter a value in MM:SS format.")