def calculate_weight_loss(green_weight, finished_weight):
    return ((green_weight - finished_weight) / green_weight) * 100

def calculate_development_time(total_roast_time_str, time_of_first_crack_str):
    total_minutes = int(total_roast_time_str.split(':')[0]) * 60 + int(total_roast_time_str.split(':')[1])
    first_crack_minutes = int(time_of_first_crack_str.split(':')[0]) * 60 + int(time_of_first_crack_str.split(':')[1])
    development_seconds = total_minutes - first_crack_minutes
    return development_seconds

def format_development_time(seconds):
    minutes, seconds = divmod(seconds, 60)
    return f"{minutes:02}:{seconds:02}"

def get_roast_classification(weight_loss_percentage):
    if weight_loss_percentage < 13.01:
        return "City Roast"
    elif weight_loss_percentage < 14.51:
        return "City Plus"
    elif weight_loss_percentage < 15.51:
        return "Full City"
    elif weight_loss_percentage < 16.51:
        return "Full City Plus"
    elif weight_loss_percentage < 18.01:
        return "Vienna Roast"
    else:
        return "Italian Roast"