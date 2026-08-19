def get_user_input():
    coffee_name = input("Please enter the bean roasted: ")
    green_weight = float(input("Enter the green coffee weight in grams: "))
    finished_weight = float(input("Enter the finished coffee weight in grams: "))
    return coffee_name, green_weight, finished_weight

def calculate_weight_loss_percentage(green_weight, finished_weight):
    weight_loss = green_weight - finished_weight
    weight_loss_percentage = (weight_loss / green_weight) * 100
    return weight_loss_percentage

def classify_roast(weight_loss_percentage):
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

def print_results(coffee_name, green_weight, finished_weight, weight_loss_percentage, classification):
    print("Bean Roasted:", coffee_name)
    print("Green coffee weight: " + str(green_weight) + " grams")
    print("Finished coffee weight: " + str(finished_weight) + " grams")
    print("Roast weight loss percentage: " + str(round(weight_loss_percentage,2)) + "%")
    print("Roast classification: " + classification)

def main():
    coffee_name, green_weight, finished_weight = get_user_input()
    weight_loss_percentage = calculate_weight_loss_percentage(green_weight, finished_weight)
    classification = classify_roast(weight_loss_percentage)
    print_results(coffee_name, green_weight, finished_weight, weight_loss_percentage, classification)

if __name__ == "__main__":
    main()