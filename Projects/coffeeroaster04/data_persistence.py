import json
import os
import sys
from datetime import datetime
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
ROAST_RECORDS_PATH = DATA_DIR / "roast_records.json"
ROAST_PROFILES_PATH = DATA_DIR / "roast_profiles.json"
USERS_PATH = DATA_DIR / "users.json"


def load_roast_records():
    if ROAST_RECORDS_PATH.exists():
        with open(ROAST_RECORDS_PATH, "r") as file:
            try:
                records = json.load(file)
                for record_id in records:
                    records[record_id]["date"] = datetime.strptime(
                        records[record_id]["date"], "%m/%d/%Y"
                    ).strftime("%m/%d/%Y")
                return records
            except json.JSONDecodeError:
                print(
                    "Error: The roast records file is corrupted. Exiting the program."
                )
                sys.exit(1)
    return {}


def save_roast_records(records):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ROAST_RECORDS_PATH, "w") as file:
        json.dump(records, file, indent=4)


def load_roast_profiles():
    if ROAST_PROFILES_PATH.exists():
        with open(ROAST_PROFILES_PATH, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print(
                    "Error: The roast profiles file is corrupted. Exiting the program."
                )
                sys.exit(1)
    return {}


def save_roast_profiles(profiles):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ROAST_PROFILES_PATH, "w") as file:
        json.dump(profiles, file, indent=4)


def load_users():
    if USERS_PATH.exists():
        with open(USERS_PATH, "r") as file:
            try:
                return json.load(file)
            except json.JSONDecodeError:
                print("Error: The users file is corrupted. Exiting the program.")
                sys.exit(1)
    return {}


def save_users(users):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(USERS_PATH, "w") as file:
        json.dump(users, file, indent=4)


def count_roasts():
    try:
        with open(ROAST_RECORDS_PATH, "r") as file:
            data = json.load(file)
            return len(data)
    except FileNotFoundError:
        return 0
    except json.JSONDecodeError:
        print("Error: The data file is corrupted. Exiting the program.")
        sys.exit(1)
