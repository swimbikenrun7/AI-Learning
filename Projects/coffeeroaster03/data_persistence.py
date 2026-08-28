import json
import os
from pathlib import Path
from datetime import datetime

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ROAST_RECORDS_PATH = DATA_DIR / "roast_records.json"

def load_roast_records():
    if ROAST_RECORDS_PATH.exists():
        with open(ROAST_RECORDS_PATH, 'r') as file:
            try:
                records = json.load(file)
                for date in records:
                    records[date]['date'] = datetime.strptime(records[date]['date'], 
"%m/%d/%Y").strftime("%m/%d/%Y")
                return records
            except json.JSONDecodeError:
                print("Failed to decode roast records file. Starting with an empty record set.")
    return {}

def save_roast_records(records):
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(ROAST_RECORDS_PATH, 'w') as file:
        json.dump(records, file, indent=4)