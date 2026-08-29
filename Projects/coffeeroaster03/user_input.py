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