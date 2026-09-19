import re
from datetime import datetime

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def validate_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%m/%d/%Y")
    except ValueError:
        raise ValueError("Enter a valid date in MM/DD/YYYY format.")
    if date_obj > datetime.now():
        raise ValueError("Date cannot be in the future.")
    return date_obj.strftime("%m/%d/%Y")


def validate_bean_name(name):
    if not name:
        raise ValueError("Bean name is required.")
    return name


def validate_green_weight(value_str):
    try:
        green_weight = float(value_str)
    except ValueError:
        green_weight = None
    if green_weight is None or green_weight < 100 or green_weight > 300:
        raise ValueError(
            "Invalid input. Please enter a numeric value greater than 100 and less than 300."
        )
    return green_weight


def validate_finished_weight(value_str, green_weight):
    try:
        finished_weight = float(value_str)
    except ValueError:
        finished_weight = None
    if (
        finished_weight is None
        or finished_weight < 100
        or finished_weight > green_weight
    ):
        raise ValueError(
            "Invalid input. Please enter a numeric value greater than 100 and less than the green weight."
        )
    return finished_weight


def _parse_mm_ss(time_str):
    try:
        minutes, seconds = map(int, time_str.split(":"))
        return minutes * 60 + seconds
    except ValueError:
        return None


def validate_roast_time(value_str):
    total_seconds = _parse_mm_ss(value_str)
    if total_seconds is None or total_seconds < 240 or total_seconds >= 1200:
        raise ValueError(
            "Invalid input. Please enter a value in MM:SS format, between 04:00 and 20:00."
        )
    return total_seconds


def validate_profile_name(name):
    if not name:
        raise ValueError("Profile name is required.")
    return name


def validate_roaster_id(value_str, roasters):
    if not value_str:
        return None
    if value_str not in roasters:
        raise ValueError("Choose a roaster from the list, or leave blank.")
    return value_str


def validate_target_first_crack(value_str):
    if not value_str:
        return None
    total_seconds = _parse_mm_ss(value_str)
    if total_seconds is None or total_seconds < 60 or total_seconds >= 1200:
        raise ValueError(
            "Invalid input. Please enter a value in MM:SS format, between 01:00 and 20:00, or leave blank."
        )
    return total_seconds


def validate_target_development_time(value_str):
    if not value_str:
        return None
    total_seconds = _parse_mm_ss(value_str)
    if total_seconds is None or total_seconds <= 0 or total_seconds >= 1200:
        raise ValueError(
            "Invalid input. Please enter a value in MM:SS format, between 00:01 and 20:00, or leave blank."
        )
    return total_seconds


def validate_temperature(value_str):
    if not value_str:
        return None
    try:
        temperature = float(value_str)
    except ValueError:
        temperature = None
    if temperature is None or temperature < 60 or temperature > 500:
        raise ValueError(
            "Invalid input. Please enter a numeric value between 60 and 500, or leave blank."
        )
    return temperature


def validate_email(value_str):
    email = (value_str or "").strip().lower()
    if not _EMAIL_PATTERN.match(email):
        raise ValueError("Enter a valid email address.")
    return email


def validate_password(value_str):
    if not value_str or len(value_str) < 8:
        raise ValueError("Password must be at least 8 characters.")
    return value_str


def validate_first_crack(value_str, total_roast_time):
    total_seconds = _parse_mm_ss(value_str)
    if (
        total_seconds is None
        or total_seconds < 240
        or total_seconds >= total_roast_time
    ):
        raise ValueError(
            "Invalid input. Please enter a value in MM:SS format, before the total roast time."
        )
    return total_seconds
