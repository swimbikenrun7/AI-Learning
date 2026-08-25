from calculations import calculate_weight_loss, calculate_development_time, format_development_time, get_roast_classification
import re
from datetime import datetime

def validate_date(date_str):
    date_format = "%m/%d/%Y"
    while True:
        try:
            return datetime.strptime(date_str, date_format)
        except ValueError:
            print("Invalid date format. Please enter a date in the format MM/DD/YYYY.")
            date_str = input("Enter the date (MM/DD/YYYY): ")

def validate_numeric_input(prompt, min_val=None, max_val=None):
    while True:
        try:
            value = float(input(prompt))
            if (min_val is None or value >= min_val) and (max_val is None or value <= max_val):
                return value
            else:
                print(f"Invalid input. Please enter a number between {min_val} and {max_val}.")
        except ValueError:
            print("Invalid input. Please enter a numeric value.")

def validate_time_input(prompt, min_val=None, max_val=None):
    while True:
        time_str = input(prompt)
        if re.match(r'^\d{2}:\d{2}$', time_str):
            hours, minutes = map(int, time_str.split(':'))
            total_minutes = hours * 60 + minutes
            if (min_val is None or total_minutes >= min_val) and (max_val is None or total_minutes <= max_val):
                return time_str
            else:
                print(f"Invalid input. Please enter a time in MM:SS format between {min_val} and {max_val}.")
        else:
            print("Invalid input. Please enter a time in MM:SS format.")

def main():
    date = validate_date(input("Enter the date (MM/DD/YYYY): "))
    green_weight = validate_numeric_input("Enter the green weight (in grams): ", 100, 300)
    finished_weight = validate_numeric_input("Enter the finished weight (in grams): ", 100, green_weight)
    total_roast_time = validate_time_input("Enter the total roast time (MM:SS): ", min_val=240, max_val=1200)  # 4 minutes to 20 minutes in minutes
    time_of_first_crack = validate_time_input(f"Enter the time of first crack (MM:SS), must be less than {total_roast_time}: ", max_val=int(total_roast_time.split(':')[0]) * 60 + int(total_roast_time.split(':')[1]))
    weight_loss_percentage = calculate_weight_loss(green_weight, finished_weight)
    development_seconds = calculate_development_time(total_roast_time, time_of_first_crack)
    roast_classification = get_roast_classification(weight_loss_percentage)

    print("\nRoast Session Details:")
    print(f"Date: {date.strftime('%m/%d/%Y')}")
    print(f"Green Weight: {green_weight} grams")
    print(f"Finished Weight: {finished_weight} grams")
    print(f"Weight Loss Percentage: {weight_loss_percentage:.2f}%")
    print(f"Development Time: {format_development_time(development_seconds)}")
    print(f"Roast Classification: {roast_classification}")

if __name__ == "__main__":
    main()