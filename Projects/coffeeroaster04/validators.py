import math
import re
from datetime import datetime

_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _mm_ss(total_seconds):
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes:02d}:{seconds:02d}"


def _max_time_label(max_seconds):
    # Whole-minute caps (a roaster's row count) are inclusive: 720 reads "12:00". The
    # original cap of 1199 means "under 20:00", so it reads "20:00".
    return _mm_ss(max_seconds + 1 if max_seconds % 60 == 59 else max_seconds)


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


def validate_green_weight(value_str, min_g=100, max_g=300):
    try:
        green_weight = float(value_str)
    except ValueError:
        green_weight = None
    if green_weight is None or green_weight < min_g or green_weight > max_g:
        raise ValueError(
            f"Invalid input. Please enter a numeric value between {min_g:g} and {max_g:g} grams."
        )
    return green_weight


def validate_finished_weight(value_str, green_weight, min_g=100):
    try:
        finished_weight = float(value_str)
    except ValueError:
        finished_weight = None
    if (
        finished_weight is None
        or finished_weight < min_g
        or finished_weight > green_weight
    ):
        raise ValueError(
            f"Invalid input. Please enter a numeric value between {min_g:g} and the green weight ({green_weight:g} g)."
        )
    return finished_weight


def _parse_mm_ss(time_str):
    try:
        minutes, seconds = map(int, time_str.split(":"))
        return minutes * 60 + seconds
    except ValueError:
        return None


def validate_roast_time(value_str, min_seconds=240, max_seconds=1199):
    total_seconds = _parse_mm_ss(value_str)
    if (
        total_seconds is None
        or total_seconds < min_seconds
        or total_seconds > max_seconds
    ):
        raise ValueError(
            "Invalid input. Please enter a value in MM:SS format, "
            f"between {_mm_ss(min_seconds)} and {_max_time_label(max_seconds)}."
        )
    return total_seconds


def validate_profile_name(name):
    if not name:
        raise ValueError("Profile name is required.")
    return name


def validate_roaster_id(value_str, roasters, required=False):
    if not value_str and not required:
        return None
    if value_str not in roasters:
        raise ValueError(
            "Choose a roaster from the list."
            if required
            else "Choose a roaster from the list, or leave blank."
        )
    return value_str


def validate_target_first_crack(value_str, max_seconds=1199):
    if not value_str:
        return None
    total_seconds = _parse_mm_ss(value_str)
    if total_seconds is None or total_seconds < 60 or total_seconds > max_seconds:
        raise ValueError(
            "Invalid input. Please enter a value in MM:SS format, "
            f"between 01:00 and {_max_time_label(max_seconds)}, or leave blank."
        )
    return total_seconds


def validate_target_development_time(value_str, max_seconds=1199):
    if not value_str:
        return None
    total_seconds = _parse_mm_ss(value_str)
    if total_seconds is None or total_seconds <= 0 or total_seconds > max_seconds:
        raise ValueError(
            "Invalid input. Please enter a value in MM:SS format, "
            f"between 00:01 and {_max_time_label(max_seconds)}, or leave blank."
        )
    return total_seconds


def validate_temperature(value_str, min_temp=60, max_temp=500):
    if not value_str:
        return None
    try:
        temperature = float(value_str)
    except ValueError:
        temperature = None
    if temperature is None or temperature < min_temp or temperature > max_temp:
        raise ValueError(
            f"Invalid input. Please enter a numeric value between {min_temp:g} and {max_temp:g}, or leave blank."
        )
    return temperature


START_CONDITIONS = ("cold", "warm", "preheated")


def validate_start_condition(value_str):
    if not value_str:
        return None
    if value_str not in START_CONDITIONS:
        raise ValueError("Choose a start condition from the list, or leave blank.")
    return value_str


def validate_ambient_temperature(value_str, min_temp, max_temp):
    if not value_str:
        return None
    try:
        temperature = float(value_str)
    except ValueError:
        temperature = None
    # float() accepts "nan" and "inf", which slip past a range check.
    if (
        temperature is None
        or not math.isfinite(temperature)
        or temperature < min_temp
        or temperature > max_temp
    ):
        raise ValueError(
            "Invalid input. Please enter the air temperature as a number between "
            f"{min_temp:g} and {max_temp:g}, or leave blank."
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


def validate_first_crack(value_str, total_roast_time, min_seconds=240):
    total_seconds = _parse_mm_ss(value_str)
    if (
        total_seconds is None
        or total_seconds < min_seconds
        or total_seconds >= total_roast_time
    ):
        raise ValueError(
            "Invalid input. Please enter a value in MM:SS format, "
            f"from {_mm_ss(min_seconds)} up to (not including) the total roast time."
        )
    return total_seconds
