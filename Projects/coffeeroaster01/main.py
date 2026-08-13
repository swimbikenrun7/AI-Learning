# This line imports the sys module, which provides access to
# some variables used or maintained by the interpreter and to
# functions that interact strongly with the interpreter.
import sys

# This line prints a prompt asking the user to enter the name
# of a coffee roast.
print("Please enter the name of a coffee roast:")

# This line reads the input from the user. The input is read as
# a string, which is then stored in the variable `coffee_name`.
coffee_name = input()

# This line prints the coffee name back to the screen,
# confirming that it has been received.
print("You entered:", coffee_name)

# This line waits for the user to press Enter before the script
# exits. It's useful when running scripts from a command line
# or terminal, so you can see the output and then close the
# window.
sys.stdin.read(1)