# This line imports the sys module, which provides access to
# some variables used or maintained by the interpreter and to
# functions that interact strongly with the interpreter.
import sys

# This line prints a prompt asking the user to enter the name
# of a coffee roast.
print("Please enter the name of a coffee roast:")

# This line reads the input from the user. The input is read as
# a string, which is then stored in the variable 'xxx'.
coffee_name = input()
green_weight = float(input("Enter the green coffee weight in grams: "))
finished_weight = float(input("Enter the finished coffee weight in grams: "))

# Calculations for determining roast level
weight_loss = green_weight - finished_weight
weight_loss_percentage = (weight_loss / green_weight) * 100

# Classify the roast based on weight loss
if weight_loss_percentage < 13.01:
    classification = "City Roast"
elif weight_loss_percentage < 14.51:
    classification = "City Plus"
elif weight_loss_percentage < 15.51:
    classification = "Full City"
elif weight_loss_percentage < 16.51:
    classification = "Full City Plus"
elif weight_loss_percentage < 18.01:
    classification = "Vienna Roast"
else:
    classification = "Italian Roast"

# This line prints the information back to the screen,
# confirming that it has been received.
print("Bean Roasted:", coffee_name)
print("Green coffee weight: " + str(green_weight) + " grams")
print("Finished coffee weight: " + str(finished_weight) + " grams")
print("Roast weight loss percentage: " + str(round(weight_loss_percentage,2)) + "%")
print("Roast classification: " + classification)

# This line waits for the user to press Enter before the script
# exits. It's useful when running scripts from a command line
# or terminal, so you can see the output and then close the
# window.
sys.stdin.read(1)