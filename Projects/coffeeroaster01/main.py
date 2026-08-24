from calculations import calculate_weight_loss_percentage

def get_user_input():
    roast_date = input("Please enter the date of roast: ")
    coffee_name = input("Please enter the bean roasted: ")

    while True:
        green_weight_input = input("Enter the green coffee weight in grams: ")
        
        try:
            green_weight = float(green_weight_input)
            
            if green_weight > 100 and green_weight < 300:
                break  # Exit the loop if green_weight is valid
            else:
                print("Invalid input. The green coffee weight must be between 100 and 300 grams.")
        
        except ValueError:
            print("Invalid input. Please enter a numeric value for the green coffee weight.")

    while True:
            finished_weight_input = input("Enter the finished coffee weight in grams: ")
            
            try:
                finished_weight = float(finished_weight_input)
                
                if finished_weight > 100 and finished_weight < green_weight: 
                    break  # Exit the loop if green_weight is valid
                else:
                    print("Invalid input. The finished coffee weight must be less than green weight and greater than 100g.")
            
            except ValueError:
                print("Invalid input. Please enter a numeric value for the green coffee weight.")

    return roast_date, coffee_name, green_weight, finished_weight

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

def print_results(roast_date, coffee_name, green_weight, finished_weight, weight_loss_percentage, classification):
    print("Date Roasted:", roast_date)
    print("Bean Roasted:", coffee_name)
    print("Green coffee weight: " + str(green_weight) + " grams")
    print("Finished coffee weight: " + str(finished_weight) + " grams")
    print("Roast weight loss percentage: " + str(round(weight_loss_percentage,2)) + "%")
    print("Roast classification: " + classification)

def main():
    roast_date, coffee_name, green_weight, finished_weight = get_user_input()
    weight_loss_percentage = calculate_weight_loss_percentage(green_weight, finished_weight)
    classification = classify_roast(weight_loss_percentage)
    print_results(roast_date, coffee_name, green_weight, finished_weight, weight_loss_percentage, classification)

if __name__ == "__main__":
    main()