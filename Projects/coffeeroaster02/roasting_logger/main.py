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