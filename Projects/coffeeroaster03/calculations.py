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
