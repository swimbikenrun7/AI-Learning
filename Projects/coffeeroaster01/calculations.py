def calculate_weight_loss_percentage(green_weight, finished_weight):
    weight_loss = green_weight - finished_weight
    weight_loss_percentage = (weight_loss / green_weight) * 100
    return weight_loss_percentage