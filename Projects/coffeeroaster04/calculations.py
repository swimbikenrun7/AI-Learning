from itertools import pairwise


def calculate_weight_loss(green_weight, finished_weight, min_g=100, max_g=300):
    if green_weight < min_g or green_weight > max_g:
        raise ValueError(f"Green weight must be between {min_g:g} and {max_g:g} grams.")
    return ((green_weight - finished_weight) / green_weight) * 100


def calculate_development_time(
    total_roast_time, time_of_first_crack, min_total_seconds=240
):
    if total_roast_time < min_total_seconds or time_of_first_crack >= total_roast_time:
        raise ValueError(
            "Total roast time must be at least "
            f"{min_total_seconds // 60:02d}:{min_total_seconds % 60:02d} "
            "and longer than the time of first crack."
        )
    return total_roast_time - time_of_first_crack


def fill_forward(values):
    filled = []
    last_value = None
    for value in values:
        if value is not None:
            last_value = value
        filled.append(last_value)
    return filled


def resolve_actual_temps(entered_temps, total_roast_time):
    total_minutes = total_roast_time // 60
    relevant_count = min(len(entered_temps), total_minutes)
    within_roast = fill_forward(entered_temps[:relevant_count])
    return within_roast + [None] * (len(entered_temps) - relevant_count)


def calculate_dtr(total_roast_time, development_time):
    return (development_time / total_roast_time) * 100


def calculate_rate_of_rise(temps):
    if not temps:
        return []
    rate_of_rise = [None]
    for previous, current in pairwise(temps):
        if previous is None or current is None:
            rate_of_rise.append(None)
        else:
            rate_of_rise.append(current - previous)
    return rate_of_rise


def classify_roast(weight_loss):
    ROAST_CLASSIFICATION = {
        13.01: "City Roast",
        14.51: "City Plus",
        15.51: "Full City",
        16.51: "Full City Plus",
        18.01: "Vienna Roast",
    }
    for threshold, classification in ROAST_CLASSIFICATION.items():
        if weight_loss < threshold:
            return classification
    return "Italian Roast"
